#!/usr/bin/env python3
"""Record a user-confirmed maintain-project-memory install for offline freshness checks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from check_skill_freshness import (
    CANONICAL_BRANCH,
    CANONICAL_REPOSITORY,
    COMMIT_RE,
    DEFAULT_PROVENANCE_FILE,
    PROVENANCE_SCHEMA,
    local_blob_map,
    payload_digest,
)


def build_receipt(skill_root: Path, canonical_commit: str) -> dict:
    blobs = local_blob_map(skill_root)
    if not blobs:
        raise ValueError("skill root contains no files")
    return {
        "schema": PROVENANCE_SCHEMA,
        "skill_name": "maintain-project-memory",
        "canonical_repository": f"https://github.com/{CANONICAL_REPOSITORY}",
        "canonical_branch": CANONICAL_BRANCH,
        "canonical_commit": canonical_commit.lower(),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "recorded_from": "user-confirmed-install",
        "skill_root_at_recording": str(skill_root.resolve()),
        "payload_file_count": len(blobs),
        "payload_digest": payload_digest(blobs),
    }


def write_receipt(path: Path, receipt: dict) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Installed skill root. Defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--canonical-commit",
        required=True,
        help="Trusted 40-character canonical commit established by the install/update workflow.",
    )
    parser.add_argument(
        "--provenance-file",
        type=Path,
        default=DEFAULT_PROVENANCE_FILE,
        help="Receipt path outside the installed skill payload.",
    )
    args = parser.parse_args()

    if not args.skill_root.exists() or not args.skill_root.is_dir():
        parser.error("skill root must be an existing directory")
    if not COMMIT_RE.fullmatch(args.canonical_commit):
        parser.error("canonical commit must be a 40-character Git SHA")

    receipt = build_receipt(args.skill_root, args.canonical_commit)
    write_receipt(args.provenance_file, receipt)

    print("PROVENANCE_RECORDED user-confirmed-install")
    print(f"CANONICAL_REPOSITORY {receipt['canonical_repository']}")
    print(f"CANONICAL_BRANCH {receipt['canonical_branch']}")
    print(f"CANONICAL_COMMIT {receipt['canonical_commit']}")
    print(f"PAYLOAD_DIGEST {receipt['payload_digest']}")
    print(f"PAYLOAD_FILE_COUNT {receipt['payload_file_count']}")
    print(f"PROVENANCE_FILE {args.provenance_file.expanduser().resolve()}")
    print("NOTE This receipt proves the local payload is unchanged since recording; it does not prove GitHub main has not advanced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
