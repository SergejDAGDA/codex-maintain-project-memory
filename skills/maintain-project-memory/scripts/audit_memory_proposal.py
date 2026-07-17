#!/usr/bin/env python3
"""Check a strict project-memory proposal for deterministic failure patterns."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


REQUIRED_SECTIONS = (
    "Evidence summary",
    "Baseline divergences",
    "Current-state facts",
    "Unresolved decisions",
    "Memory defects",
    "Approval effect",
    "Full proposed diff",
)
CLASSIFICATIONS = {
    "Consistent with baseline",
    "Approved evolution",
    "Implemented, approval unverified",
    "Unresolved conflict",
    "Regression",
}
DECISION_STATUSES = {"Proposed", "Unverified", "Approved", "Superseded", "Rejected"}
PROVENANCE_VALUES = {"user-approved", "source-attributed", "agent-generated/unverified"}
EXPECTED_DIVERGENCE_HEADER = (
    "Claim key",
    "Baseline claim",
    "Current claim",
    "Applicability",
    "Classification",
    "Evidence",
)
CLAIM_KEY_PATTERN = r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)+"
FORBIDDEN_PATTERNS = {
    r"\bNo change proposed\b": "omit unchanged files instead of listing them",
    r"^\+.*\bawaiting approval\b": "post-operation content still awaits approval",
    r"^\+.*\bpending (?:this|the) correction\b": "post-operation content still describes the correction as pending",
    r"\baudit\s+used\b": "verification wording does not state an observed result",
    r"^\+##\s+Provenance\s*$": "detached provenance map",
}


def section(text: str, name: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(name)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else None


def audit(text: str) -> list[str]:
    findings: list[str] = []

    for name in REQUIRED_SECTIONS:
        if section(text, name) is None:
            findings.append(f"ERROR missing required section: ## {name}")

    for pattern, message in FORBIDDEN_PATTERNS.items():
        if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
            findings.append(f"ERROR {message}")

    divergences = section(text, "Baseline divergences")
    if divergences is not None:
        if "Current-state fact — not a baseline divergence" in divergences:
            findings.append("ERROR current-state fact placed in baseline divergences")
        rows = re.findall(r"^\|.*\|\s*$", divergences, re.MULTILINE)
        if rows:
            header = tuple(cell.strip() for cell in rows[0].strip().strip("|").split("|"))
            if header != EXPECTED_DIVERGENCE_HEADER:
                findings.append("ERROR Baseline divergences has a non-canonical table header")
        for row in rows:
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if all(re.fullmatch(r"[-:]+", cell) for cell in cells) or tuple(cells) == EXPECTED_DIVERGENCE_HEADER:
                continue
            if len(cells) != 6:
                findings.append("ERROR baseline-divergence row must have exactly six columns: " + row.strip())
                continue
            if not re.fullmatch(CLAIM_KEY_PATTERN, cells[0]):
                findings.append("ERROR invalid atomic Claim key: " + cells[0])
            if not cells[1] or not cells[2]:
                findings.append("ERROR baseline and current claims must both be explicit: " + row.strip())
            applicability = cells[3].strip("`")
            if applicability not in {"Active", "Unresolved"}:
                findings.append("ERROR Applicability must be Active or Unresolved: " + row.strip())
            labels = re.findall(r"`([^`]+)`", row)
            classification_labels = [label for label in labels if label in CLASSIFICATIONS]
            if len(classification_labels) != 1:
                findings.append(
                    "ERROR every baseline-divergence row must contain exactly one closed classification: "
                    + row.strip()
                )
            if "Regression" in classification_labels and applicability != "Active":
                findings.append("ERROR Regression requires Active applicability: " + row.strip())

    unresolved_keys: set[str] = set()
    unresolved = section(text, "Unresolved decisions")
    if unresolved is not None:
        for line in (item.strip() for item in unresolved.splitlines() if item.strip()):
            if line == "- None.":
                continue
            match = re.fullmatch(rf"-\s+`({CLAIM_KEY_PATTERN})`:\s+.+", line)
            if not match:
                findings.append(
                    "ERROR unresolved decision must be one atomic claim-key bullet: " + line
                )
            else:
                unresolved_keys.add(match.group(1))

    for match in re.finditer(r"^\+\s*-\s*Status:\s*(.+?)\s*$", text, re.MULTILINE):
        value = match.group(1).strip().strip("`")
        if value not in DECISION_STATUSES:
            findings.append(f"ERROR non-canonical decision status: {value}")

    for match in re.finditer(
        r"^\+\s*-\s*Approval provenance:\s*(.+?)\s*$", text, re.MULTILINE
    ):
        value = match.group(1).strip().strip("`")
        if value not in PROVENANCE_VALUES:
            findings.append(f"ERROR non-canonical approval provenance: {value}")

    for match in re.finditer(r"^\+\s*-\s*Decision:\s*`?(.+?)`?\s*$", text, re.MULTILINE):
        if re.match(r"(?:Decide|Determine|Select|Confirm|Consider)\b", match.group(1), re.IGNORECASE):
            findings.append("ERROR Decision must be declarative, not an audit workflow instruction")

    effect = section(text, "Approval effect")
    if effect is not None:
        for label in (
            "Files changed",
            "Approved claim keys",
            "Unverified claim keys",
            "Proposed claim keys",
            "Superseded claim keys",
            "Rejected claim keys",
            "Policy changes",
        ):
            if not re.search(rf"^-\s*{re.escape(label)}\s*:", effect, re.MULTILINE):
                findings.append(f"ERROR approval effect missing field: {label}")

    proposed_diff = section(text, "Full proposed diff")
    if proposed_diff is not None:
        fenced = re.search(r"```diff\s*(.*?)```", proposed_diff, re.DOTALL | re.IGNORECASE)
        if not fenced:
            findings.append("ERROR Full proposed diff must contain one diff code fence")
        elif not re.search(r"^(?:diff --git|\*\*\* Update File:)", fenced.group(1), re.MULTILINE):
            findings.append("ERROR diff fence does not contain an actual patch")
        elif re.search(r"^\+##\s+Sources of truth\s*$", fenced.group(1), re.MULTILINE):
            source_match = re.search(
                r"^\+##\s+Sources of truth\s*$\n(.*?)(?=^\+##\s+|^\*\*\* Update File:|^diff --git|\Z)",
                fenced.group(1),
                re.MULTILINE | re.DOTALL,
            )
            source_added = "\n".join(
                line[1:] for line in source_match.group(1).splitlines() if line.startswith("+")
            ) if source_match else ""
            role_patterns = {
                "Approved intent": r"Approved intent",
                "Implemented state": r"Implemented state",
                "Current coordination state": r"Current coordination state[^\n]*STATUS\.md",
                "Decision index": r"Decision index[^\n]*DECISIONS\.md",
                "Historical checkpoints": r"Historical checkpoints[^\n]*SESSION_LOG\.md",
            }
            for role, pattern in role_patterns.items():
                if not re.search(pattern, source_added, re.IGNORECASE):
                    findings.append(f"ERROR Sources of truth has invalid or missing role mapping: {role}")

        if fenced:
            session_chunks = re.findall(
                r"(?:^\*\*\* Update File:.*SESSION_LOG\.md\s*$|^diff --git a/.*SESSION_LOG\.md.*$)"
                r"(.*?)(?=^\*\*\* Update File:|^diff --git a/|\Z)",
                fenced.group(1),
                re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )
            for chunk in session_chunks:
                deleted = [
                    line for line in chunk.splitlines()
                    if line.startswith("-")
                    and not line.startswith("---")
                    and line != "-# Session Log"
                ]
                if deleted:
                    findings.append(
                        "ERROR SESSION_LOG.md is append-only; preserve old checkpoints and append a correction"
                    )
                chunk_lines = chunk.splitlines()
                for index, line in enumerate(chunk_lines):
                    if not re.match(r"^\+##\s+", line):
                        continue
                    before = chunk_lines[index - 1] if index > 0 else ""
                    after = chunk_lines[index + 1] if index + 1 < len(chunk_lines) else ""
                    if before not in {"+", " "}:
                        findings.append(
                            "ERROR appended SESSION_LOG heading needs a preserved or added blank line before it"
                        )
                    if after not in {"+", " "}:
                        findings.append(
                            "ERROR appended SESSION_LOG heading needs a blank line before its first entry"
                        )

            decision_chunks = re.findall(
                r"(?:^\*\*\* Update File:.*DECISIONS\.md\s*$|^diff --git a/.*DECISIONS\.md.*$)"
                r"(.*?)(?=^\*\*\* Update File:|^diff --git a/|\Z)",
                fenced.group(1),
                re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )
            all_decision_statuses: dict[str, str] = {}
            replaces_legacy_index = False
            for chunk in decision_chunks:
                if re.search(r"^-##\s+(?:Approved|Proposed)\s*$", chunk, re.MULTILINE):
                    replaces_legacy_index = True
                headings = re.findall(r"^\+##\s+.+$", chunk, re.MULTILINE)
                keys = re.findall(r"^\+\s*-\s*Claim key:\s*(.+?)\s*$", chunk, re.MULTILINE)
                if headings and len(keys) != len(headings):
                    findings.append(
                        "ERROR every added decision entry must contain exactly one Claim key"
                    )
                normalized: list[str] = []
                for key in keys:
                    value = key.strip().strip("`")
                    normalized.append(value)
                    if not re.fullmatch(CLAIM_KEY_PATTERN, value):
                        findings.append(f"ERROR invalid decision Claim key: {value}")
                if len(normalized) != len(set(normalized)):
                    findings.append("ERROR duplicate decision Claim key in proposed migration")
                added_text = "\n".join(
                    line[1:] for line in chunk.splitlines() if line.startswith("+")
                )
                for body in re.findall(
                    r"^##\s+.+?$\n(.*?)(?=^##\s+|\Z)",
                    added_text,
                    re.MULTILINE | re.DOTALL,
                ):
                    key_match = re.search(r"^-\s*Claim key:\s*`?([^`\s]+)`?\s*$", body, re.MULTILINE)
                    status_match = re.search(r"^-\s*Status:\s*`?([^`\n]+)`?\s*$", body, re.MULTILINE)
                    if key_match and status_match:
                        all_decision_statuses[key_match.group(1)] = status_match.group(1).strip()
            if replaces_legacy_index:
                for key in sorted(unresolved_keys):
                    status = all_decision_statuses.get(key)
                    if status not in {"Unverified", "Proposed"}:
                        findings.append(
                            f"ERROR unresolved Claim key missing from migrated decision index or has wrong status: {key}"
                        )
                if effect is not None:
                    for status in DECISION_STATUSES:
                        label = f"{status} claim keys"
                        match = re.search(rf"^-\s*{re.escape(label)}\s*:\s*(.+?)\s*$", effect, re.MULTILINE)
                        if not match:
                            continue
                        raw = match.group(1).strip()
                        declared = set() if raw.lower() == "none" else set(re.findall(r"`([^`]+)`", raw))
                        actual = {key for key, value in all_decision_statuses.items() if value == status}
                        if declared != actual:
                            findings.append(
                                f"ERROR Approval effect {label} does not match migrated decision index"
                            )

            if effect is not None:
                file_match = re.search(r"^-\s*Files changed\s*:\s*(.+?)\s*$", effect, re.MULTILINE)
                if file_match:
                    raw = file_match.group(1).strip()
                    declared_files = set() if raw.lower() == "none" else {
                        item.replace("\\", "/") for item in re.findall(r"`([^`]+)`", raw)
                    }
                    actual_files = {
                        item.replace("\\", "/")
                        for item in re.findall(r"^\*\*\* Update File:\s*(.+?)\s*$", fenced.group(1), re.MULTILINE)
                    }
                    actual_files.update(
                        item.replace("\\", "/")
                        for item in re.findall(r"^diff --git a/(.+?) b/", fenced.group(1), re.MULTILINE)
                    )
                    if declared_files != actual_files:
                        findings.append("ERROR Approval effect Files changed does not match diff paths")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    if not args.draft.is_file():
        parser.error("draft must be an existing text file")

    raw = args.draft.read_bytes()
    findings = audit(raw.decode("utf-8"))
    if findings:
        print("\n".join(findings))
        print(f"SUMMARY findings={len(findings)}")
        return 1
    print("OK strict memory proposal passed deterministic checks")
    print(f"SHA256 {hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
