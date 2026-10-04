#!/usr/bin/env python3
"""Verify the installed maintain-project-memory payload against canonical GitHub main."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple


CANONICAL_REPOSITORY = "SergejDAGDA/codex-maintain-project-memory"
CANONICAL_BRANCH = "main"
SKILL_PREFIX = "skills/maintain-project-memory/"
API_BASE = f"https://api.github.com/repos/{CANONICAL_REPOSITORY}"
USER_AGENT = "maintain-project-memory-skill-freshness/2"
PROVENANCE_SCHEMA = "maintain-project-memory/install-provenance-v1"
DEFAULT_PROVENANCE_FILE = (
    Path.home() / ".codex" / "skill-provenance" / "maintain-project-memory.json"
)
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _ignored(relative: str) -> bool:
    parts = Path(relative).parts
    return (
        "__pycache__" in parts
        or relative.endswith(".pyc")
        or relative.endswith(".pyo")
        or relative.endswith(".DS_Store")
    )


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def local_blob_map(skill_root: Path) -> Dict[str, str]:
    skill_root = skill_root.resolve()
    result: Dict[str, str] = {}
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root).as_posix()
        if _ignored(relative):
            continue
        result[relative] = git_blob_sha(path.read_bytes())
    return result


def payload_digest(blob_map: Dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, blob_sha in sorted(blob_map.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob_sha.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def compare_blob_maps(
    local: Dict[str, str], remote: Dict[str, str]
) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
    local_keys = set(local)
    remote_keys = set(remote)
    missing_local = tuple(sorted(remote_keys - local_keys))
    extra_local = tuple(sorted(local_keys - remote_keys))
    mismatched = tuple(
        sorted(path for path in local_keys & remote_keys if local[path] != remote[path])
    )
    return missing_local, extra_local, mismatched


def _request_json(url: str, timeout: float) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def canonical_blob_map(timeout: float) -> Tuple[str, Dict[str, str]]:
    branch = _request_json(f"{API_BASE}/branches/{CANONICAL_BRANCH}", timeout)
    commit_sha = branch["commit"]["sha"]
    tree_sha = branch["commit"]["commit"]["tree"]["sha"]
    tree = _request_json(f"{API_BASE}/git/trees/{tree_sha}?recursive=1", timeout)
    if tree.get("truncated"):
        raise RuntimeError("canonical repository tree response was truncated")

    result: Dict[str, str] = {}
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or not path.startswith(SKILL_PREFIX):
            continue
        relative = path[len(SKILL_PREFIX) :]
        if not relative or _ignored(relative):
            continue
        result[relative] = entry["sha"]
    if not result:
        raise RuntimeError("canonical skill payload was not found in repository tree")
    return commit_sha, result


def online_result(skill_root: Path, timeout: float) -> dict:
    local = local_blob_map(skill_root)
    commit_sha, remote = canonical_blob_map(timeout)
    missing_local, extra_local, mismatched = compare_blob_maps(local, remote)
    status = "current" if not (missing_local or extra_local or mismatched) else "different"
    return {
        "status": status,
        "verification_scope": "canonical-main",
        "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
        "canonical_branch": CANONICAL_BRANCH,
        "canonical_commit": commit_sha,
        "canonical_currentness": "verified-online",
        "skill_root": str(skill_root.resolve()),
        "local_file_count": len(local),
        "canonical_file_count": len(remote),
        "local_payload_digest": payload_digest(local),
        "missing_local": list(missing_local),
        "extra_local": list(extra_local),
        "mismatched": list(mismatched),
        "write_eligible": status == "current",
    }


def load_provenance(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != PROVENANCE_SCHEMA:
        raise ValueError("unsupported provenance schema")
    if data.get("canonical_repository") != f"https://github.com/{CANONICAL_REPOSITORY}":
        raise ValueError("provenance repository does not match canonical repository")
    if data.get("canonical_branch") != CANONICAL_BRANCH:
        raise ValueError("provenance branch does not match canonical branch")
    commit = data.get("canonical_commit")
    if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
        raise ValueError("provenance canonical_commit must be a 40-character Git SHA")
    digest = data.get("payload_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("provenance payload_digest must be a SHA-256 hex digest")
    return data


def local_provenance_result(
    skill_root: Path,
    provenance_file: Path,
    expected_commit: Optional[str],
    online_error: Exception,
) -> dict:
    local = local_blob_map(skill_root)
    local_digest = payload_digest(local)
    provenance = load_provenance(provenance_file)
    recorded_digest = provenance["payload_digest"].lower()
    recorded_commit = provenance["canonical_commit"].lower()
    expected = expected_commit.lower() if expected_commit else None

    payload_matches = local_digest == recorded_digest
    expected_matches = None if expected is None else expected == recorded_commit

    if not payload_matches or expected_matches is False:
        status = "different"
    else:
        status = "verified-local"

    return {
        "status": status,
        "verification_scope": "recorded-install",
        "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
        "canonical_branch": CANONICAL_BRANCH,
        "canonical_commit": recorded_commit,
        "canonical_currentness": "unverified-offline",
        "expected_commit": expected,
        "expected_commit_match": expected_matches,
        "skill_root": str(skill_root.resolve()),
        "local_file_count": len(local),
        "local_payload_digest": local_digest,
        "provenance_file": str(provenance_file.resolve()),
        "provenance_recorded_at": provenance.get("recorded_at_utc"),
        "provenance_payload_match": payload_matches,
        "write_eligible": status == "verified-local" and expected_matches is True,
        "online_error": f"{type(online_error).__name__}: {online_error}",
    }


def result_payload(
    skill_root: Path,
    timeout: float,
    provenance_file: Path,
    expected_commit: Optional[str],
) -> dict:
    if expected_commit and not COMMIT_RE.fullmatch(expected_commit):
        raise ValueError("expected commit must be a 40-character Git SHA")

    try:
        payload = online_result(skill_root, timeout)
        if expected_commit:
            expected = expected_commit.lower()
            actual = payload["canonical_commit"].lower()
            payload["expected_commit"] = expected
            payload["expected_commit_match"] = expected == actual
            if expected != actual:
                payload["status"] = "different"
                payload["write_eligible"] = False
        return payload
    except (OSError, RuntimeError, KeyError, ValueError, urllib.error.URLError) as online_exc:
        if provenance_file.exists():
            try:
                return local_provenance_result(
                    skill_root,
                    provenance_file,
                    expected_commit,
                    online_exc,
                )
            except (OSError, KeyError, ValueError, json.JSONDecodeError) as provenance_exc:
                return {
                    "status": "unverified",
                    "verification_scope": "none",
                    "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
                    "canonical_branch": CANONICAL_BRANCH,
                    "canonical_commit": None,
                    "canonical_currentness": "unverified-offline",
                    "expected_commit": expected_commit.lower() if expected_commit else None,
                    "skill_root": str(skill_root.resolve()),
                    "provenance_file": str(provenance_file.resolve()),
                    "write_eligible": False,
                    "online_error": f"{type(online_exc).__name__}: {online_exc}",
                    "provenance_error": f"{type(provenance_exc).__name__}: {provenance_exc}",
                }
        return {
            "status": "unverified",
            "verification_scope": "none",
            "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
            "canonical_branch": CANONICAL_BRANCH,
            "canonical_commit": None,
            "canonical_currentness": "unverified-offline",
            "expected_commit": expected_commit.lower() if expected_commit else None,
            "skill_root": str(skill_root.resolve()),
            "provenance_file": str(provenance_file.resolve()),
            "write_eligible": False,
            "online_error": f"{type(online_exc).__name__}: {online_exc}",
        }


def _print_text(payload: dict) -> None:
    print(f"SKILL_FRESHNESS {payload['status']}")
    print(f"VERIFICATION_SCOPE {payload.get('verification_scope', 'none')}")
    print(f"CANONICAL_REPOSITORY {payload['canonical_repository']}")
    print(f"CANONICAL_BRANCH {payload['canonical_branch']}")
    if payload.get("canonical_commit"):
        print(f"CANONICAL_COMMIT {payload['canonical_commit']}")
    print(f"CANONICAL_CURRENTNESS {payload.get('canonical_currentness', 'unknown')}")
    if payload.get("expected_commit"):
        print(f"EXPECTED_COMMIT {payload['expected_commit']}")
    if payload.get("expected_commit_match") is not None:
        print(f"EXPECTED_COMMIT_MATCH {'yes' if payload['expected_commit_match'] else 'no'}")
    print(f"SKILL_ROOT {payload['skill_root']}")
    print(f"WRITE_ELIGIBLE {'yes' if payload.get('write_eligible') else 'no'}")
    if "local_file_count" in payload:
        print(f"LOCAL_FILE_COUNT {payload['local_file_count']}")
    if "canonical_file_count" in payload:
        print(f"CANONICAL_FILE_COUNT {payload['canonical_file_count']}")
    if payload.get("provenance_file"):
        print(f"PROVENANCE_FILE {payload['provenance_file']}")
    if payload.get("provenance_payload_match") is not None:
        print(
            f"PROVENANCE_PAYLOAD_MATCH "
            f"{'yes' if payload['provenance_payload_match'] else 'no'}"
        )
    for label in ("missing_local", "extra_local", "mismatched"):
        for path in payload.get(label, []):
            print(f"{label.upper()} {path}")
    for label in ("online_error", "provenance_error"):
        if payload.get(label):
            print(f"{label.upper()} {payload[label]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Installed skill root. Defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Per-request timeout in seconds for the canonical GitHub check.",
    )
    parser.add_argument(
        "--provenance-file",
        type=Path,
        default=DEFAULT_PROVENANCE_FILE,
        help="Local install-provenance receipt used only when canonical GitHub is unreachable.",
    )
    parser.add_argument(
        "--expected-commit",
        help="Trusted canonical commit supplied by the current task/user for offline comparison.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if not args.skill_root.exists() or not args.skill_root.is_dir():
        parser.error("skill root must be an existing directory")

    try:
        payload = result_payload(
            args.skill_root,
            args.timeout,
            args.provenance_file,
            args.expected_commit,
        )
    except ValueError as exc:
        parser.error(str(exc))

    status = payload["status"]
    if status == "current" or (status == "verified-local" and payload.get("write_eligible")):
        exit_code = 0
    elif status == "different":
        exit_code = 2
    elif status == "unverified":
        exit_code = 3
    else:
        exit_code = 4

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
