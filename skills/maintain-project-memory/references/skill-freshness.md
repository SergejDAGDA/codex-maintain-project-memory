# Canonical skill freshness

This reference defines how `maintain-project-memory` verifies that the installed skill payload matches the current canonical implementation before relying on current-contract behavior.

## Canonical source

Canonical repository:

- `https://github.com/SergejDAGDA/codex-maintain-project-memory`
- branch: `main`

The canonical repository commit identifies the current skill implementation. This is separate from the project-local protocol marker (`maintain-project-memory/v2`) and from the project-memory schema marker (`project-memory/v1`). A project may be on protocol v2 while the installed skill implementation is stale.

## Freshness check

Before an Audit, adoption/migration review, Bootstrap, Checkpoint, or Handoff that claims to use the current canonical skill contract, resolve the installed skill directory and run:

```text
<skill-directory>/scripts/check_skill_freshness.py
```

The checker compares the complete installed `skills/maintain-project-memory` payload with the skill subtree at canonical GitHub `main` using Git blob identities. It does not rely on a local `.git` directory, installer metadata, or protocol markers.

Run the check once near the start of a substantial session. Re-run only when the canonical branch may have changed during a long-running task or before a write when freshness is otherwise uncertain.

## Status semantics

The checker returns one of three statuses:

- `current`: the installed skill payload exactly matches canonical `main`; report the canonical commit and proceed.
- `different`: the installed payload does not exactly match canonical `main`; do not claim the current canonical contract is installed.
- `unverified`: canonical GitHub state could not be verified, for example because network access or the GitHub API is unavailable.

A `different` result may mean an older installation, a local modification, an incomplete installation, or another divergence. Do not guess which one from the mismatch alone.

## Stop rules

- On `current`, continue normally.
- On `different`, stop before any project-memory mutation. Report the canonical commit and the changed/missing/extra skill paths. Update or reinstall the skill before continuing with current-contract migration or writes.
- On `unverified`, a read-only Audit may continue only with an explicit `skill freshness: unverified` caveat. Do not claim that the latest skill is installed.
- On `unverified`, do not perform Bootstrap, migration writes, Checkpoint, or Handoff unless the user explicitly accepts proceeding without canonical freshness verification.

If the user explicitly requests analysis using the installed local version rather than the current canonical version, state that boundary clearly and do not describe the result as a current-canonical audit.

## No self-update

The freshness checker is read-only. It must not:

- modify the installed skill;
- update a Codex cache;
- install dependencies;
- change any user project;
- rewrite project memory;
- fetch or execute code from the canonical repository.

Updating the installed skill is a separate user-authorized installation action.

## Reporting

When canonical freshness materially affects the task, report:

- canonical repository and branch;
- canonical commit when verified;
- freshness: `current`, `different`, or `unverified`;
- for `different`, the mismatched/missing/extra paths;
- whether the task was allowed to continue under the stop rules above.

Do not substitute the project protocol marker for this check. The layers are distinct:

```text
canonical skill freshness
        ↓
project-local protocol generation
        ↓
project-memory freshness
        ↓
current code/config/runtime evidence
```
