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

    def test_project_start_routing_is_explicit(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        interface = self.read("agents/openai.yaml")
        self.assertIn("## Project-start routing", lifecycle)
        self.assertIn("route through Bootstrap before or alongside the first material implementation stage", lifecycle)
        self.assertIn("start or resumption of substantial project work", interface)

    def test_protocol_v2_has_one_supported_canonical_root(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("supports exactly one canonical project-memory root per project", lifecycle)
        self.assertIn("at `docs/project-memory`", lifecycle)
        self.assertIn("do not claim protocol v2 is current merely by changing the marker value", lifecycle)

    def test_canonical_skill_freshness_gate_is_explicit(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        freshness = self.read("references/skill-freshness.md")
        interface = self.read("agents/openai.yaml")
        self.assertIn("## Canonical skill freshness gate", lifecycle)
        self.assertIn("scripts/check_skill_freshness.py", lifecycle)
        self.assertIn("canonical GitHub `main`", freshness)
        self.assertIn("`current`", freshness)
        self.assertIn("`verified-local`", freshness)
        self.assertIn("`different`", freshness)
        self.assertIn("`unverified`", freshness)
        self.assertIn("verify installed skill freshness against canonical main", interface)

    def test_offline_fallback_requires_external_receipt_and_expected_commit(self) -> None:
        freshness = self.read("references/skill-freshness.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("scripts/record_skill_provenance.py --canonical-commit", freshness)
        self.assertIn("~/.codex/skill-provenance/maintain-project-memory.json", freshness)
        self.assertIn("--expected-commit", freshness)
        self.assertIn("WRITE_ELIGIBLE yes", freshness)
        self.assertIn("does **not** independently prove that GitHub `main` has not advanced", freshness)
        self.assertIn("user-confirmed install", lifecycle)

    def test_skill_freshness_is_distinct_from_project_protocol(self) -> None:
        freshness = self.read("references/skill-freshness.md")
        self.assertIn("separate from the project-local protocol marker", freshness)
        self.assertIn("Do not substitute the project protocol marker for this check", freshness)

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
