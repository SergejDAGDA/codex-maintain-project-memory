#!/usr/bin/env python3
"""Run structural and optional adoption/freshness checks on project-memory files."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from datetime import date, datetime
from pathlib import Path


REQUIRED_HEADINGS = {
    "PROJECT.md": ("# Project", "## Purpose", "## Sources of truth"),
    "STATUS.md": ("# Status", "## Current outcome", "## Next safe step", "## Verification"),
    "DECISIONS.md": ("# Decisions",),
    "SESSION_LOG.md": ("# Session log",),
    "HANDOFF.md": ("# Handoff",),
}
PLACEHOLDERS = ("TBD", "YYYY-MM-DD")
PREDICTED_CHECK_SUCCESS = (
    r"\bpasses\s+after\b",
    r"\bwill\s+pass\b",
    r"\bбудет\s+успеш(?:ен|на|но)\b",
)
REVIEW_ANNOTATIONS = (
    r"^\s*No change\.?\s*$",
    r"^\s*Keep (?:the file )?as-is\.?\s*$",
)
VAGUE_VERIFICATION = (r"\baudit\s+used\b", r"\bused\s+during\s+.*audit\s+cycle\b")
DECISION_STATUSES = {"Proposed", "Unverified", "Approved", "Superseded", "Rejected"}
PROVENANCE_VALUES = {"user-approved", "source-attributed", "agent-generated/unverified"}
CLAIM_KEY_PATTERN = r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)+"
EXPECTED_PROTOCOL = "maintain-project-memory/v2"
EXPECTED_SCHEMA = "project-memory/v1"
EXPECTED_MEMORY_ROOT = "docs/project-memory"
SKIP_SCAN_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "vendor",
    "target",
    ".cache",
}


def _marker_values(text: str, label: str) -> list[str]:
    return re.findall(
        rf"^{re.escape(label)}:\s*`([^`]+)`\.?\s*$",
        text,
        re.MULTILINE,
    )


def _git_identity(project_root: Path) -> dict[str, str]:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    try:
        top = run("rev-parse", "--show-toplevel")
    except OSError:
        return {"status": "unavailable"}
    if top.returncode != 0:
        return {"status": "unavailable"}

    head = run("rev-parse", "HEAD")
    branch = run("branch", "--show-current")
    dirty = run("status", "--porcelain")
    return {
        "status": "git",
        "root": top.stdout.strip(),
        "branch": branch.stdout.strip() or "detached",
        "head": head.stdout.strip() if head.returncode == 0 else "unborn",
        "dirty": "yes" if dirty.stdout.strip() else "no",
    }


def _nested_memory_roots(project_root: Path) -> list[Path]:
    project_root = project_root.resolve()
    canonical = (project_root / EXPECTED_MEMORY_ROOT).resolve()
    found: list[Path] = []
    for root, dirs, _files in os.walk(project_root):
        dirs[:] = [name for name in dirs if name not in SKIP_SCAN_DIRS]
        path = Path(root)
        if path.name == "project-memory" and path.parent.name == "docs":
            resolved = path.resolve()
            if resolved != canonical:
                found.append(resolved)
            dirs[:] = []
    return sorted(set(found))


def _is_semantically_empty_handoff(text: str) -> bool:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines and lines[0].casefold() == "# handoff":
        lines = lines[1:]
    return not lines or lines == ["No active handoff."]


def adoption_report(project_root: Path) -> list[str]:
    project_root = project_root.resolve()
    agents = project_root / "AGENTS.md"
    agents_text = agents.read_text(encoding="utf-8") if agents.exists() else ""

    protocol_values = _marker_values(agents_text, "Project memory protocol")
    schema_values = _marker_values(agents_text, "Project memory schema")
    root_values = _marker_values(agents_text, "Canonical project-memory root")

    protocol = protocol_values[0] if len(protocol_values) == 1 else "legacy/unversioned"
    schema = schema_values[0] if len(schema_values) == 1 else "legacy/unversioned"
    memory_root = root_values[0] if len(root_values) == 1 else EXPECTED_MEMORY_ROOT

    handoff = project_root / EXPECTED_MEMORY_ROOT / "HANDOFF.md"
    if not handoff.exists():
        handoff_state = "missing"
    else:
        text = handoff.read_text(encoding="utf-8")
        handoff_state = (
            "empty"
            if _is_semantically_empty_handoff(text)
            else "active-or-legacy"
        )

    git = _git_identity(project_root)
    if git["status"] == "git":
        vcs = f"git branch={git['branch']} head={git['head']} dirty={git['dirty']}"
    else:
        vcs = "unavailable"

    nested = _nested_memory_roots(project_root)
    lines = [
        f"ADOPTION protocol={protocol}",
        f"ADOPTION schema={schema}",
        f"ADOPTION canonical_root={memory_root}",
        f"ADOPTION vcs={vcs}",
        f"ADOPTION handoff={handoff_state}",
        f"ADOPTION nested_memory_roots={len(nested)}",
    ]
    lines.extend(f"ADOPTION nested_memory_root={path}" for path in nested)
    return lines


def audit(project_root: Path, stale_days: int, adoption: bool = False) -> list[str]:
    project_root = project_root.resolve()
    memory_root = project_root / "docs" / "project-memory"
    findings: list[str] = []

    for filename, headings in REQUIRED_HEADINGS.items():
        path = memory_root / filename
        if not path.exists():
            findings.append(f"ERROR missing {path}")
            continue

        text = path.read_text(encoding="utf-8")
        for heading in headings:
            if heading not in text:
                findings.append(f"ERROR {filename}: missing heading {heading!r}")
        for marker in PLACEHOLDERS:
            if marker in text:
                findings.append(f"WARN {filename}: unresolved placeholder {marker!r}")
        for pattern in REVIEW_ANNOTATIONS:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                findings.append(
                    f"ERROR {filename}: review annotation was written as durable memory"
                )
                break

        dated_sections = re.findall(r"^##\s+\d{4}-\d{2}-\d{2}\b", text, re.MULTILINE)
        if filename in {"STATUS.md", "HANDOFF.md"} and dated_sections:
            findings.append(
                f"WARN {filename}: contains {len(dated_sections)} dated section(s); "
                "keep current/active state replaceable and move history to SESSION_LOG.md"
            )

        if filename == "STATUS.md":
            for pattern in PREDICTED_CHECK_SUCCESS:
                if re.search(pattern, text, re.IGNORECASE):
                    findings.append(
                        "ERROR STATUS.md: verification success is predicted before the check ran"
                    )
                    break
            for pattern in VAGUE_VERIFICATION:
                if re.search(pattern, text, re.IGNORECASE):
                    findings.append(
                        "ERROR STATUS.md: verification wording does not state the observed result"
                    )
                    break
            match = re.search(r"^Last verified:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
            if match:
                try:
                    verified = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                    age = (date.today() - verified).days
                    if age > stale_days:
                        findings.append(f"WARN STATUS.md: last verified {age} days ago")
                except ValueError:
                    findings.append("ERROR STATUS.md: invalid Last verified date")
            elif "YYYY-MM-DD" not in text:
                findings.append("ERROR STATUS.md: missing Last verified date")

        if filename == "DECISIONS.md" and re.search(
            r"^##\s+Provenance\s*$", text, re.IGNORECASE | re.MULTILINE
        ):
            findings.append(
                "ERROR DECISIONS.md: detached provenance map; keep provenance with each decision"
            )
        if filename == "DECISIONS.md":
            for match in re.finditer(r"^-\s*Status:\s*(.+?)\s*$", text, re.MULTILINE):
                value = match.group(1).strip().strip("`")
                if value not in DECISION_STATUSES:
                    findings.append(f"ERROR DECISIONS.md: non-canonical status {value!r}")
            for match in re.finditer(
                r"^-\s*Approval provenance:\s*(.+?)\s*$", text, re.MULTILINE
            ):
                value = match.group(1).strip().strip("`")
                if value not in PROVENANCE_VALUES:
                    findings.append(
                        f"ERROR DECISIONS.md: non-canonical approval provenance {value!r}"
                    )
            decision_sections = re.findall(
                r"^##\s+.+?$\n(.*?)(?=^##\s+|\Z)",
                text,
                re.MULTILINE | re.DOTALL,
            )
            seen_keys: set[str] = set()
            for body in decision_sections:
                if not re.search(r"^-\s*Status:", body, re.MULTILINE):
                    continue
                keys = re.findall(r"^-\s*Claim key:\s*(.+?)\s*$", body, re.MULTILINE)
                if len(keys) != 1:
                    findings.append(
                        "ERROR DECISIONS.md: every structured decision needs exactly one Claim key"
                    )
                    continue
                key = keys[0].strip().strip("`")
                if not re.fullmatch(CLAIM_KEY_PATTERN, key):
                    findings.append(f"ERROR DECISIONS.md: invalid Claim key {key!r}")
                if key in seen_keys:
                    findings.append(f"ERROR DECISIONS.md: duplicate Claim key {key!r}")
                seen_keys.add(key)

    agents = project_root / "AGENTS.md"
    if agents.exists():
        agents_text = agents.read_text(encoding="utf-8")
        if agents.stat().st_size > 32 * 1024:
            findings.append("WARN AGENTS.md: larger than 32 KiB; keep durable guidance concise")
        policies = re.findall(
            r"^Memory update policy:\s*`(notify|approve-decisions|strict)`\.?\s*$",
            agents_text,
            re.MULTILINE,
        )
        if not policies:
            findings.append("ERROR AGENTS.md: missing canonical Memory update policy")
        elif len(policies) > 1:
            findings.append("ERROR AGENTS.md: multiple Memory update policies")

        protocols = _marker_values(agents_text, "Project memory protocol")
        if not protocols:
            findings.append(
                f"WARN AGENTS.md: missing project-memory protocol marker; expected {EXPECTED_PROTOCOL!r}"
            )
        elif len(protocols) > 1:
            findings.append("ERROR AGENTS.md: multiple project-memory protocol markers")
        elif protocols[0] != EXPECTED_PROTOCOL:
            findings.append(
                f"WARN AGENTS.md: protocol {protocols[0]!r} differs from current {EXPECTED_PROTOCOL!r}"
            )

        schemas = _marker_values(agents_text, "Project memory schema")
        if not schemas:
            findings.append(
                f"WARN AGENTS.md: missing project-memory schema marker; expected {EXPECTED_SCHEMA!r}"
            )
        elif len(schemas) > 1:
            findings.append("ERROR AGENTS.md: multiple project-memory schema markers")
        elif schemas[0] != EXPECTED_SCHEMA:
            findings.append(
                f"WARN AGENTS.md: schema {schemas[0]!r} differs from current {EXPECTED_SCHEMA!r}"
            )

        roots = _marker_values(agents_text, "Canonical project-memory root")
        if not roots:
            findings.append(
                f"WARN AGENTS.md: missing canonical memory-root marker; expected {EXPECTED_MEMORY_ROOT!r}"
            )
        elif len(roots) > 1:
            findings.append("ERROR AGENTS.md: multiple canonical memory-root markers")
        elif roots[0] != EXPECTED_MEMORY_ROOT:
            findings.append(
                f"WARN AGENTS.md: canonical memory root {roots[0]!r} differs from expected {EXPECTED_MEMORY_ROOT!r}"
            )
    else:
        findings.append("WARN AGENTS.md: missing project-local memory protocol")

    if adoption:
        for nested in _nested_memory_roots(project_root):
            findings.append(
                f"WARN nested project-memory root detected: {nested}; classify it as separate or non-canonical"
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--stale-days", type=int, default=30)
    parser.add_argument(
        "--adoption",
        action="store_true",
        help="Print read-only protocol/VCS/canonical-root adoption information and scan for nested memory roots.",
    )
    args = parser.parse_args()

    if not args.project_root.exists() or not args.project_root.is_dir():
        parser.error("project_root must be an existing directory")
    if args.stale_days < 0:
        parser.error("--stale-days must be non-negative")

    if args.adoption:
        print("\n".join(adoption_report(args.project_root)))

    findings = audit(args.project_root, args.stale_days, adoption=args.adoption)
    if findings:
        print("\n".join(findings))
        print(f"SUMMARY findings={len(findings)}")
        return 1 if any(item.startswith("ERROR") for item in findings) else 0

    print("OK project memory passed structural checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
