#!/usr/bin/env python3
"""Run structural checks on project-memory files."""

from __future__ import annotations

import argparse
import re
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


def audit(project_root: Path, stale_days: int) -> list[str]:
    memory_root = project_root.resolve() / "docs" / "project-memory"
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

    agents = project_root.resolve() / "AGENTS.md"
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

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--stale-days", type=int, default=30)
    args = parser.parse_args()

    if not args.project_root.exists() or not args.project_root.is_dir():
        parser.error("project_root must be an existing directory")
    if args.stale_days < 0:
        parser.error("--stale-days must be non-negative")

    findings = audit(args.project_root, args.stale_days)
    if findings:
        print("\n".join(findings))
        print(f"SUMMARY findings={len(findings)}")
        return 1 if any(item.startswith("ERROR") for item in findings) else 0

    print("OK project memory passed structural checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
