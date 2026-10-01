from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "maintain-project-memory"


class SkillContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (SKILL_ROOT / relative).read_text(encoding="utf-8")

    def test_agents_template_declares_protocol_markers(self) -> None:
        text = self.read("assets/templates/AGENTS.memory.fragment.md")
        self.assertIn("Project memory protocol: `maintain-project-memory/v2`", text)
        self.assertIn("Project memory schema: `project-memory/v1`", text)
        self.assertIn("Canonical project-memory root: `docs/project-memory`", text)

    def test_session_start_freshness_is_protocol_not_new_operation(self) -> None:
        skill = self.read("SKILL.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("Session-start freshness is a read-only protocol, not a fifth operation", skill)
        self.assertIn("## Session-start preflight", lifecycle)
        self.assertIn("## Pre-write optimistic revalidation", lifecycle)

    def test_existing_project_adoption_is_read_only_before_migration(self) -> None:
        skill = self.read("SKILL.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("--adoption", skill)
        self.assertIn("Do not overwrite them with templates", lifecycle)
        self.assertIn("Preserve the existing update policy", lifecycle)

    def test_current_file_semantics_remain_separate(self) -> None:
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        session_log = self.read("assets/templates/SESSION_LOG.md")
        handoff = self.read("assets/templates/HANDOFF.md")
        self.assertIn("replace the current snapshot in `STATUS.md` rather than appending history", agents)
        self.assertIn("Append factual checkpoints; do not use this file as the current project status", session_log)
        self.assertIn("No active handoff.", handoff)

    def test_temporal_identity_and_external_provenance_are_explicit(self) -> None:
        skill = self.read("SKILL.md")
        status = self.read("assets/templates/STATUS.md")
        self.assertIn("implementation/source baseline", skill)
        self.assertIn("documentation/project-memory revision", skill)
        self.assertIn("External evidence provenance", status)

    def test_ownership_routes_memory_updates_through_memory_lifecycle(self) -> None:
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        self.assertIn("other workflows may read them as evidence and report staleness", agents)
        self.assertIn("should not opportunistically rewrite them", agents)

    def test_git_is_optional_and_locking_is_not_required(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("Git is optional", lifecycle)
        self.assertIn("This is optimistic revalidation, not locking", lifecycle)
        self.assertIn("Do not introduce a lock service", lifecycle)


if __name__ == "__main__":
    unittest.main()
