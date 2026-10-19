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

    def test_project_template_keeps_source_roles_stable(self) -> None:
        template = self.read("assets/templates/PROJECT.md")
        skill = self.read("SKILL.md")
        self.assertIn("stable evidence roles", template)
        self.assertIn("not the project's transient current results", template)
        self.assertIn("Do not", template)
        self.assertIn("passing test results", template)
        self.assertIn("Leave the `Approved intent` source", template)
        self.assertIn("unless a concrete user approval", template)
        self.assertIn("point to STATUS.md", template)
        self.assertIn("not a second current-state snapshot", skill)
        self.assertIn("Leave the `Approved intent` source as `TBD`", skill)
        self.assertIn("route current work status to `STATUS.md`", skill)

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

    def test_substantial_task_closeout_requires_permitted_checkpoint(self) -> None:
        skill = self.read("SKILL.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        interface = self.read("agents/openai.yaml")
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        for text in (skill, lifecycle, interface, agents):
            self.assertIn("Checkpoint: PENDING", text)
            self.assertIn("closeout", text)
            self.assertIn("STATUS.md", text)
            self.assertIn("SESSION_LOG.md", text)
        self.assertIn("Completion Checkpoint procedure:", agents)
        self.assertIn("task-wide read-only", agents)
        self.assertIn("read-only target/server/runtime", agents)
        self.assertIn("Local Git commit policy is independent", lifecycle)
        self.assertNotIn("Read-only work never writes memory", agents)

    def test_checkpoint_requires_cross_file_semantic_closeout(self) -> None:
        skill = self.read("SKILL.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        interface = self.read("agents/openai.yaml")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for text in (skill, lifecycle, agents, interface):
            self.assertIn("PROJECT.md", text)
            self.assertIn("STATUS.md", text)
            self.assertIn("DECISIONS.md", text)
            self.assertIn("SESSION_LOG.md", text)
            self.assertIn("Checkpoint: PENDING", text)
        for text in (skill, lifecycle, agents, readme):
            self.assertIn("historical", text)
            self.assertIn("RED", text)
            self.assertIn("approval", text.lower())
        self.assertIn("bounded semantic reconciliation", skill)
        self.assertIn("Checkpoint: COMPLETE", agents)
        self.assertIn("structural audit PASS", lifecycle)
        self.assertIn("append-only", lifecycle)
        self.assertIn("Do not require edits to unchanged files", skill)

    def test_adoption_diagnostic_distinguishes_wip_and_completion(self) -> None:
        audit = self.read("scripts/audit_project_memory.py")
        self.assertIn("def _checkpoint_routing(", audit)
        self.assertIn("ADOPTION checkpoint_routing=", audit)
        self.assertIn("Completion Checkpoint routing absent or incomplete", audit)

    def test_local_git_checkpoint_policy_is_project_scoped_and_safe(self) -> None:
        guide = self.read("references/local-git-checkpoints.md")
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        skill = self.read("SKILL.md")
        lifecycle = self.read("references/lifecycle-protocol.md")
        policy = self.read("references/update-policy.md")
        self.assertIn("Local Git commit policy: `auto`", agents)
        for mode in ("auto", "ask", "off"):
            self.assertIn(f"`{mode}`", guide)
        for phrase in (
            "pre-existing index", "git diff --cached --quiet",
            "git add -- <file1> ...", "git diff --cached --check",
            "git rev-parse HEAD", "git show --stat --oneline HEAD",
            "git init", "push", "read-only",
        ):
            self.assertIn(phrase, guide)
        self.assertIn("effective mode is `ask`", guide)
        self.assertIn("references/local-git-checkpoints.md", skill)
        self.assertIn("references/local-git-checkpoints.md", lifecycle)
        self.assertIn("independent", policy)
        self.assertEqual("0.1.6", self.read("VERSION").strip())

    def test_minimum_wip_continuity_boundaries_and_no_new_operation(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        skill = self.read("SKILL.md")
        status = self.read("assets/templates/STATUS.md")
        session_log = self.read("assets/templates/SESSION_LOG.md")
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        self.assertIn("## Minimum WIP continuity", lifecycle)
        self.assertIn("not a fifth operation", lifecycle)
        self.assertIn("Before the first material edit", skill)
        for trigger in (
            "Before the first material write",
            "After a meaningful implementation slice",
            "On material blocker / cross-component contract mismatch",
            "Before pause, context transfer, or a final report with material WIP",
        ):
            self.assertIn(trigger, lifecycle)
        for record_field in (
            "exact observed HEAD",
            "staged/unstaged/untracked",
            "unverified areas",
            "next safe action",
            "commit readiness: NOT READY",
        ):
            self.assertIn(record_field, lifecycle)
        self.assertIn("Minimum Continuity Record", status)
        self.assertIn("meaningful WIP boundary", session_log)
        self.assertIn("strict", agents)
        self.assertIn("No commit", agents)

    def test_deferred_memory_permissions_and_failure_boundaries(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        policy = self.read("references/update-policy.md")
        skill = self.read("SKILL.md")
        for phrase in (
            "notify",
            "approve-decisions",
            "strict",
            "Explicit `read-only`",
            "Explicit `no-commit`",
            "Explicit prohibition of any tracking-file writes",
            "optimistic revalidation",
            "DECISIONS.md",
            "SESSION_LOG.md",
        ):
            self.assertIn(phrase, lifecycle)
        self.assertIn("obtain approval", lifecycle)
        self.assertIn("pause substantial write-capable work", lifecycle)
        self.assertIn("A chat summary is not a durable project-file record", policy)
        self.assertIn("defer **full semantic", skill)
        self.assertIn("A read-only task never writes MCR", skill)
        self.assertIn("WIP recording never authorizes a Git", skill)

    def test_legacy_project_activation_and_broad_deferral_are_fail_closed(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        policy = self.read("references/update-policy.md")
        skill = self.read("SKILL.md")
        agents = self.read("assets/templates/AGENTS.memory.fragment.md")
        audit = self.read("scripts/audit_project_memory.py")
        self.assertIn("### Activation in existing projects", lifecycle)
        self.assertIn("## Minimum WIP continuity", lifecycle)
        self.assertIn("wip_continuity_routing=declared", lifecycle)
        self.assertIn("missing-review-required", lifecycle)
        self.assertIn("Stop ordinary substantial write-capable implementation", lifecycle)
        self.assertIn("Ambiguous user deferral: classify before edits", lifecycle)
        self.assertIn("update project memory only when finished", lifecycle)
        self.assertIn("ask whether that specific record is permitted", lifecycle)
        self.assertIn("Broad statements", policy)
        self.assertIn("broad defer-memory requests as ambiguous", self.read("agents/openai.yaml"))
        self.assertIn("first verify project-local MCR routing", skill)
        self.assertIn("an old/missing rule requires separately approved", skill)
        self.assertIn("clarify whether the minimal factual WIP update is allowed", agents)
        self.assertIn("def _wip_continuity_routing(", audit)
        self.assertIn("ADOPTION wip_continuity_routing=", audit)

    def test_git_is_optional_and_locking_is_not_required(self) -> None:
        lifecycle = self.read("references/lifecycle-protocol.md")
        self.assertIn("Git is optional", lifecycle)
        self.assertIn("This is optimistic revalidation, not locking", lifecycle)
        self.assertIn("Do not introduce a lock service", lifecycle)


if __name__ == "__main__":
    unittest.main()
