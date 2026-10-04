#!/usr/bin/env python3
"""Verify the installed maintain-project-memory payload against canonical GitHub main."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Tuple


CANONICAL_REPOSITORY = "SergejDAGDA/codex-maintain-project-memory"
CANONICAL_BRANCH = "main"
SKILL_PREFIX = "skills/maintain-project-memory/"
API_BASE = f"https://api.github.com/repos/{CANONICAL_REPOSITORY}"
USER_AGENT = "maintain-project-memory-skill-freshness/1"


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


def result_payload(skill_root: Path, timeout: float) -> dict:
    local = local_blob_map(skill_root)
    commit_sha, remote = canonical_blob_map(timeout)
    missing_local, extra_local, mismatched = compare_blob_maps(local, remote)
    status = "current" if not (missing_local or extra_local or mismatched) else "different"
    return {
        "status": status,
        "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
        "canonical_branch": CANONICAL_BRANCH,
        "canonical_commit": commit_sha,
        "skill_root": str(skill_root.resolve()),
        "local_file_count": len(local),
        "canonical_file_count": len(remote),
        "missing_local": list(missing_local),
        "extra_local": list(extra_local),
        "mismatched": list(mismatched),
    }


def _print_text(payload: dict) -> None:
    print(f"SKILL_FRESHNESS {payload['status']}")
    print(f"CANONICAL_REPOSITORY {payload['canonical_repository']}")
    print(f"CANONICAL_BRANCH {payload['canonical_branch']}")
    if payload.get("canonical_commit"):
        print(f"CANONICAL_COMMIT {payload['canonical_commit']}")
    print(f"SKILL_ROOT {payload['skill_root']}")
    if "local_file_count" in payload:
        print(f"LOCAL_FILE_COUNT {payload['local_file_count']}")
    if "canonical_file_count" in payload:
        print(f"CANONICAL_FILE_COUNT {payload['canonical_file_count']}")
    for label in ("missing_local", "extra_local", "mismatched"):
        for path in payload.get(label, []):
            print(f"{label.upper()} {path}")
    if payload.get("error"):
        print(f"ERROR {payload['error']}")


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
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    if not args.skill_root.exists() or not args.skill_root.is_dir():
        parser.error("skill root must be an existing directory")

    try:
        payload = result_payload(args.skill_root, args.timeout)
        exit_code = 0 if payload["status"] == "current" else 2
    except (OSError, RuntimeError, KeyError, ValueError, urllib.error.URLError) as exc:
        payload = {
            "status": "unverified",
            "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
            "canonical_branch": CANONICAL_BRANCH,
            "canonical_commit": None,
            "skill_root": str(args.skill_root.resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }
        exit_code = 3

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
