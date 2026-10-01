#!/usr/bin/env python3
"""Print a read-only project-memory and VCS fingerprint for optimistic revalidation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Optional


MEMORY_FILES = (
    "AGENTS.md",
    "docs/project-memory/PROJECT.md",
    "docs/project-memory/STATUS.md",
    "docs/project-memory/DECISIONS.md",
    "docs/project-memory/SESSION_LOG.md",
    "docs/project-memory/HANDOFF.md",
)


def _sha256(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_identity(project_root: Path) -> dict[str, object]:
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
        return {"available": False}
    if top.returncode != 0:
        return {"available": False}

    head = run("rev-parse", "HEAD")
    branch = run("branch", "--show-current")
    dirty = run("status", "--porcelain")
    return {
        "available": True,
        "root": top.stdout.strip(),
        "branch": branch.stdout.strip() or "detached",
        "head": head.stdout.strip() if head.returncode == 0 else "unborn",
        "dirty": bool(dirty.stdout.strip()),
    }


def snapshot(project_root: Path) -> dict[str, object]:
    project_root = project_root.resolve()
    files = {
        relative: _sha256(project_root / relative)
        for relative in MEMORY_FILES
    }
    return {
        "project_root": str(project_root),
        "vcs": _git_identity(project_root),
        "memory_files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()

    if not args.project_root.exists() or not args.project_root.is_dir():
        parser.error("project_root must be an existing directory")

    print(json.dumps(snapshot(args.project_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
