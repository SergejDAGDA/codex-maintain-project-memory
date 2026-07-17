#!/usr/bin/env python3
"""Initialize portable project-memory files without overwriting user work."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


TEMPLATE_MAP = {
    "PROJECT.md": Path("docs/project-memory/PROJECT.md"),
    "STATUS.md": Path("docs/project-memory/STATUS.md"),
    "DECISIONS.md": Path("docs/project-memory/DECISIONS.md"),
    "SESSION_LOG.md": Path("docs/project-memory/SESSION_LOG.md"),
    "HANDOFF.md": Path("docs/project-memory/HANDOFF.md"),
}


def initialize(project_root: Path, overwrite: bool = False) -> tuple[list[Path], list[Path]]:
    templates = Path(__file__).resolve().parent.parent / "assets" / "templates"
    project_root = project_root.resolve()
    created: list[Path] = []
    skipped: list[Path] = []

    for source_name, relative_target in TEMPLATE_MAP.items():
        source = templates / source_name
        target = project_root / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            skipped.append(target)
            continue
        shutil.copyfile(source, target)
        created.append(target)

    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing project-memory files. Review user changes first.",
    )
    args = parser.parse_args()

    if not args.project_root.exists() or not args.project_root.is_dir():
        parser.error("project_root must be an existing directory")

    created, skipped = initialize(args.project_root, args.overwrite)
    for path in created:
        print(f"CREATED {path}")
    for path in skipped:
        print(f"SKIPPED {path}")
    print(f"SUMMARY created={len(created)} skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
