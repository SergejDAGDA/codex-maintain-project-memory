from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "maintain-project-memory"
TEMPLATES = SKILL_ROOT / "assets" / "templates"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load_module(
    "audit_project_memory",
    SKILL_ROOT / "scripts" / "audit_project_memory.py",
)
SNAPSHOT = load_module(
    "memory_snapshot",
    SKILL_ROOT / "scripts" / "memory_snapshot.py",
)


class AuditProjectMemoryTests(unittest.TestCase):
    def make_project(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="memory-audit-"))
        memory = root / "docs" / "project-memory"
        memory.mkdir(parents=True)
        for name in ("PROJECT.md", "STATUS.md", "DECISIONS.md", "SESSION_LOG.md", "HANDOFF.md"):
            shutil.copyfile(TEMPLATES / name, memory / name)
        shutil.copyfile(TEMPLATES / "AGENTS.memory.fragment.md", root / "AGENTS.md")
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def test_current_protocol_markers_do_not_warn_as_missing(self) -> None:
        root = self.make_project()
        findings = AUDIT.audit(root, stale_days=99999)
        joined = "\n".join(findings)
        self.assertNotIn("missing project-memory protocol marker", joined)
        self.assertNotIn("missing project-memory schema marker", joined)
        self.assertNotIn("missing canonical memory-root marker", joined)

    def test_unversioned_agents_is_reported_as_adoption_signal(self) -> None:
        root = self.make_project()
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        text = "\n".join(
            line
            for line in text.splitlines()
            if not line.startswith("Project memory protocol:")
            and not line.startswith("Project memory schema:")
            and not line.startswith("Canonical project-memory root:")
        )
        agents.write_text(text + "\n", encoding="utf-8")

        findings = AUDIT.audit(root, stale_days=99999)
        joined = "\n".join(findings)
        self.assertIn("missing project-memory protocol marker", joined)
        self.assertIn("missing project-memory schema marker", joined)
        self.assertIn("missing canonical memory-root marker", joined)
        self.assertFalse(any(item.startswith("ERROR AGENTS.md: missing project-memory") for item in findings))

    def test_conflicting_protocol_markers_are_errors(self) -> None:
        root = self.make_project()
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        agents.write_text(
            text + "\nProject memory protocol: `maintain-project-memory/v1`\n",
            encoding="utf-8",
        )
        findings = AUDIT.audit(root, stale_days=99999)
        self.assertIn(
            "ERROR AGENTS.md: multiple project-memory protocol markers",
            findings,
        )

    def test_noncanonical_memory_root_is_reported(self) -> None:
        root = self.make_project()
        agents = root / "AGENTS.md"
        text = agents.read_text(encoding="utf-8").replace(
            "Canonical project-memory root: `docs/project-memory`",
            "Canonical project-memory root: `memory`",
        )
        agents.write_text(text, encoding="utf-8")
        findings = AUDIT.audit(root, stale_days=99999)
        self.assertTrue(
            any("canonical memory root 'memory' differs" in item for item in findings)
        )

    def test_dated_sections_in_status_and_handoff_are_flagged(self) -> None:
        root = self.make_project()
        status = root / "docs" / "project-memory" / "STATUS.md"
        handoff = root / "docs" / "project-memory" / "HANDOFF.md"
        status.write_text(status.read_text(encoding="utf-8") + "\n## 2026-01-01 old state\n", encoding="utf-8")
        handoff.write_text(handoff.read_text(encoding="utf-8") + "\n## 2026-01-02 old handoff\n", encoding="utf-8")

        findings = AUDIT.audit(root, stale_days=99999)
        joined = "\n".join(findings)
        self.assertIn("WARN STATUS.md: contains 1 dated section", joined)
        self.assertIn("WARN HANDOFF.md: contains 1 dated section", joined)

    def test_adoption_report_handles_project_without_git(self) -> None:
        root = self.make_project()
        report = AUDIT.adoption_report(root)
        joined = "\n".join(report)
        self.assertIn("ADOPTION protocol=maintain-project-memory/v2", joined)
        self.assertIn("ADOPTION schema=project-memory/v1", joined)
        self.assertIn("ADOPTION vcs=unavailable", joined)
        self.assertIn("ADOPTION handoff=empty", joined)

    def test_adoption_scan_finds_nested_memory_root(self) -> None:
        root = self.make_project()
        nested = root / "staging" / "docs" / "project-memory"
        nested.mkdir(parents=True)
        findings = AUDIT.audit(root, stale_days=99999, adoption=True)
        self.assertTrue(any("nested project-memory root detected" in item for item in findings))

    def test_memory_snapshot_changes_when_memory_changes(self) -> None:
        root = self.make_project()
        before = SNAPSHOT.snapshot(root)
        status = root / "docs" / "project-memory" / "STATUS.md"
        status.write_text(status.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        after = SNAPSHOT.snapshot(root)
        key = "docs/project-memory/STATUS.md"
        self.assertNotEqual(before["memory_files"][key], after["memory_files"][key])
        self.assertFalse(before["vcs"]["available"])


if __name__ == "__main__":
    unittest.main()
