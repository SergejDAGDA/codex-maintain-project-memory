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
        self.assertIn("WARN STATUS.md: likely historical accumulation in 1 section", joined)
        self.assertIn("WARN HANDOFF.md: contains 1 dated section", joined)

    def test_current_status_dates_do_not_trigger_history_warning(self) -> None:
        root = self.make_project()
        status = root / "docs" / "project-memory" / "STATUS.md"
        text = status.read_text(encoding="utf-8").replace("YYYY-MM-DD", "2026-10-04", 1)
        text = text.replace(
            "- Runtime: Not verified.",
            "- Runtime: verified on 2026-10-04.\n- Previous production observation: 2026-10-03.",
        )
        status.write_text(text, encoding="utf-8")

        findings = AUDIT.audit(root, stale_days=99999)
        self.assertFalse(any("historical accumulation" in item for item in findings))
        report = AUDIT.adoption_report(root)
        self.assertIn(
            "ADOPTION status_history=clean count=0 session_log_date_overlap=none",
            report,
        )

    def test_single_dated_latest_section_is_not_enough_for_accumulation_signal(self) -> None:
        root = self.make_project()
        status = root / "docs" / "project-memory" / "STATUS.md"
        status.write_text(
            status.read_text(encoding="utf-8")
            + "\n## Latest verification note\n\nObserved: 2026-09-23\n",
            encoding="utf-8",
        )

        findings = AUDIT.audit(root, stale_days=99999)
        self.assertFalse(any("historical accumulation" in item for item in findings))

    def test_repeated_latest_historical_sections_are_detected(self) -> None:
        root = self.make_project()
        status = root / "docs" / "project-memory" / "STATUS.md"
        status.write_text(
            status.read_text(encoding="utf-8")
            + "\n## Latest checkpoint\n\nDate: 2026-09-10\nOld state A.\n"
            + "\n## Latest audit\n\nDate: 2026-09-11\nOld state B.\n"
            + "\n## Latest correction\n\nDate: 2026-09-12\nOld state C.\n",
            encoding="utf-8",
        )

        findings = AUDIT.audit(root, stale_days=99999)
        joined = "\n".join(findings)
        self.assertIn("likely historical accumulation in 3 section(s)", joined)
        self.assertIn("session-log date overlap=none", joined)
        report = AUDIT.adoption_report(root)
        self.assertIn(
            "ADOPTION status_history=likely-accumulation count=3 session_log_date_overlap=none",
            report,
        )

    def test_repeated_latest_history_reports_full_session_log_date_overlap(self) -> None:
        root = self.make_project()
        memory = root / "docs" / "project-memory"
        status = memory / "STATUS.md"
        session_log = memory / "SESSION_LOG.md"
        status.write_text(
            status.read_text(encoding="utf-8")
            + "\n## Latest checkpoint\n\nDate: 2026-09-10\nOld state A.\n"
            + "\n## Latest audit\n\nDate: 2026-09-11\nOld state B.\n",
            encoding="utf-8",
        )
        session_log.write_text(
            session_log.read_text(encoding="utf-8")
            + "\n## 2026-09-10 checkpoint\n\n- Old state A.\n"
            + "\n## 2026-09-11 audit\n\n- Old state B.\n",
            encoding="utf-8",
        )

        findings = AUDIT.audit(root, stale_days=99999)
        joined = "\n".join(findings)
        self.assertIn("session-log date overlap=full", joined)
        self.assertIn("review for duplicate ownership", joined)
        report = AUDIT.adoption_report(root)
        self.assertIn(
            "ADOPTION status_history=likely-accumulation count=2 session_log_date_overlap=full",
            report,
        )

    def test_adoption_report_handles_project_without_git(self) -> None:
        root = self.make_project()
        report = AUDIT.adoption_report(root)
        joined = "\n".join(report)
        self.assertIn("ADOPTION protocol=maintain-project-memory/v2", joined)
        self.assertIn("ADOPTION schema=project-memory/v1", joined)
        self.assertIn("ADOPTION vcs=unavailable", joined)
        self.assertIn("ADOPTION handoff=empty", joined)
        self.assertIn("ADOPTION status_history=clean count=0", joined)

    def assert_handoff_state(self, content: str, expected: str) -> None:
        root = self.make_project()
        handoff = root / "docs" / "project-memory" / "HANDOFF.md"
        handoff.write_text(content, encoding="utf-8")

        report = AUDIT.adoption_report(root)

        self.assertIn(f"ADOPTION handoff={expected}", report)

    def test_heading_only_handoff_is_empty(self) -> None:
        self.assert_handoff_state("# Handoff\n", "empty")

    def test_heading_and_blank_lines_handoff_is_empty(self) -> None:
        self.assert_handoff_state("# Handoff\n\n  \n\t\n", "empty")

    def test_explicit_no_active_handoff_is_empty(self) -> None:
        self.assert_handoff_state("# Handoff\n\nNo active handoff.\n", "empty")

    def test_comment_only_handoff_is_empty(self) -> None:
        self.assert_handoff_state("# Handoff\n\n<!-- template note -->\n", "empty")

    def test_substantive_unfinished_handoff_is_active_or_legacy(self) -> None:
        self.assert_handoff_state(
            "# Handoff\n\n## Next step\nFinish the adoption audit.\n",
            "active-or-legacy",
        )

    def test_legacy_handoff_with_real_content_is_active_or_legacy(self) -> None:
        self.assert_handoff_state(
            "# Handoff\n\nContinue from the unresolved ownership decision.\n",
            "active-or-legacy",
        )

    def test_no_active_phrase_inside_real_content_is_active_or_legacy(self) -> None:
        self.assert_handoff_state(
            "# Handoff\n\nThe phrase No active handoff. appears in this note.\n",
            "active-or-legacy",
        )

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
