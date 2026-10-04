# Lifecycle protocol

This reference defines the project-local lifecycle contract for `maintain-project-memory` protocol v2. It supplements the file semantics in `SKILL.md`; it does not add a fifth durable operation.

## Canonical skill freshness gate

Before relying on current-canonical `maintain-project-memory` behavior, read `references/skill-freshness.md` and verify the installed skill payload with `scripts/check_skill_freshness.py`.

This check is separate from project protocol/schema markers. A project can correctly declare `maintain-project-memory/v2` while the installed skill implementation is older or locally modified.

- `current`: proceed; live GitHub comparison established that the installed payload matches canonical `main`.
- `verified-local` with `WRITE_ELIGIBLE yes`: proceed under the narrower offline boundary; the installed payload matches a recorded user-confirmed installation and the trusted expected commit supplied by the current task/user, but present-time GitHub `main` currentness remains unverified offline.
- `verified-local` with `WRITE_ELIGIBLE no`: read-only work may continue, but current-contract writes require a trusted expected commit or explicit user acceptance of the last-known install boundary.
- `different`: stop before project-memory mutation and update/reinstall or re-establish install provenance before continuing.
- `unverified`: a read-only Audit may continue only with an explicit freshness caveat; Bootstrap, migration writes, Checkpoint, and Handoff require either successful verification or explicit user acceptance of the unverified state.

In a network-restricted environment, a user-confirmed install may record an external provenance receipt with `scripts/record_skill_provenance.py --canonical-commit <sha>`. The receipt is not a substitute for live GitHub currentness; it proves only that the installed payload is unchanged since that confirmed installation and associates it with the trusted commit supplied at recording time.

Do not auto-update the installed skill or edit a Codex cache as part of this lifecycle. Skill installation/update is a separate user-authorized action.

## Protocol markers

Canonical project-local guidance uses these markers:

- `Project memory protocol: maintain-project-memory/v2`
- `Project memory schema: project-memory/v1`
- `Canonical project-memory root: docs/project-memory`

The protocol marker tracks lifecycle/routing behavior independently of the installed skill version. The schema marker tracks the durable file model independently of protocol changes.

Protocol v2 supports exactly one canonical project-memory root per project, at `docs/project-memory`. A project that intentionally needs a different durable layout requires explicit future protocol/tooling support; do not claim protocol v2 is current merely by changing the marker value.

A missing or older marker is an adoption signal, not proof that the memory is wrong. Do not rewrite a project automatically merely because the installed skill is newer.

## Project-start routing

Use project memory as an early coordination layer for substantial software projects rather than as a rescue mechanism added only after drift appears.

- If a substantial new project has no project-memory protocol yet, route through Bootstrap before or alongside the first material implementation stage unless the user explicitly opts out.
- If an existing project already has project-memory files or memory guidance but lacks current protocol markers, treat it as adoption/migration: perform the read-only adoption review before relying on the old memory as current authority.
- If the project is already on the current protocol, run the session-start preflight below before material work.
- Do not Bootstrap trivial experiments, throwaway snippets, or repositories where durable cross-session coordination is not useful.

The goal is not to force every task through a memory write. The goal is to establish one shared durable project model early enough that later chats and agents do not independently reconstruct project state.

## Session-start preflight

Before substantial work in a project that uses project memory:

1. Complete the canonical skill freshness gate above when the task claims current-canonical behavior.
2. Read `AGENTS.md`, `PROJECT.md`, `STATUS.md`, `DECISIONS.md`, and active `HANDOFF.md`.
3. Verify the actual project root. Treat `.git` as evidence only after a real VCS command confirms a repository.
4. Capture current repository identity when available: branch, HEAD, and whether the working tree is dirty. Git is optional.
5. Compare `STATUS.md` and active `HANDOFF.md` with task-relevant implementation/runtime evidence.
6. Check protocol/schema markers and the declared canonical project-memory root.
7. If current memory is materially stale, conflicting, or from an older/unmarked protocol, treat it as context rather than current authority and run a bounded read-only Audit before relying on it.

Do not require `SESSION_LOG.md` on every start. Read recent relevant checkpoints when the current snapshot, decision index, or handoff is insufficient to explain the present state.

When Git is unavailable, do not fabricate a revision or treat the project as defective. State that VCS freshness is unavailable and use current task-relevant filesystem/config/runtime evidence instead.

## Canonical ownership

Each project root has one canonical project-memory root: `docs/project-memory` under protocol v2.

- `maintain-project-memory` owns lifecycle semantics for `AGENTS.md` memory protocol and canonical project-memory files.
- Other workflows may read project memory as evidence and report stale or conflicting content, but should route corrections through this lifecycle instead of opportunistically rewriting it.
- Deployment handoffs, server-operation ledgers, mirrors, staging trees, backups, and copied project-memory directories are non-canonical unless explicitly declared as a separate project root.
- A multi-project server workspace may maintain server-wide memory, but that memory must not silently replace application-level memory for independent projects.

## Adoption and migration

When Bootstrap enters an existing project that already has some or all project-memory files:

1. Do not overwrite them with templates.
2. Run a read-only adoption/freshness audit.
3. Classify the local protocol as current, legacy/unversioned, newer/unknown, or conflicting.
4. Compare the local AGENTS memory block with the canonical protocol markers and required lifecycle rules.
5. Identify stale or mixed-role `STATUS.md`/`HANDOFF.md`, legacy decision structure, and nested memory copies.
6. Preserve the existing update policy (`notify`, `approve-decisions`, or `strict`) unless the user explicitly changes it.
7. Propose the smallest migration needed; do not rewrite chronological history automatically.
8. Add current protocol/schema markers only as part of a reviewed adoption/migration update.

Use Audit as the read-only adoption report. A separate migration operation is not required.

## Checkpoint triggers

A Checkpoint is appropriate after a meaningful verified boundary, including:

- a completed feature or bug-fix stage;
- an investigation conclusion that materially changes project understanding;
- an architecture, schema, security, product, data, or operational decision;
- a release, deployment, or migration boundary;
- an approved change of direction;
- a materially changed next safe action;
- closure of an active handoff;
- a durable conflict or risk that must survive the current session.

Do not create a Checkpoint for trivial formatting, ordinary reading, a transient debugging attempt, or an intermediate experiment that does not change durable project understanding.

## Pre-write optimistic revalidation

At session start, capture the current project-memory file fingerprints and repository identity when available. Immediately before writing a Checkpoint or Handoff:

1. Re-read the target memory files.
2. Re-check repository HEAD/branch when a valid repository exists.
3. Compare project-memory fingerprints with the state loaded earlier in the session.
4. Distinguish expected changes made by the current task from unexpected changes produced elsewhere.
5. If canonical memory or repository HEAD advanced unexpectedly, stop the write, load the newer state, and reconcile instead of overwriting from a stale base.

This is optimistic revalidation, not locking. Do not introduce a lock service, database, or background coordinator without independent evidence that such machinery is necessary.

## Temporal identity

When identity differences affect truth, keep these concepts separate:

- repository HEAD;
- implementation/source baseline;
- released or deployed source revision;
- artifact/build identity;
- runtime identity;
- documentation/project-memory revision.

A documentation-only or project-memory commit may advance repository HEAD without changing the implementation or deployed source baseline. Do not collapse materially different identities into one unqualified `current revision`.

## External evidence provenance

For material external/runtime claims, record enough provenance to avoid implying verification that did not occur. Distinguish when relevant between:

- independently checked in the current task;
- supplied by the user;
- inherited from a prior verified checkpoint/coordination record;
- copied from historical or otherwise unverified coordination material.

Do not require this label on every ordinary repository-derived fact. Make provenance explicit when its absence would change how strongly the current claim can be trusted.

## Fail-safe behavior

If project memory conflicts materially with current code, configuration, current user instruction, or verified runtime evidence:

- do not silently restore the project to the stale memory state;
- preserve stale records as historical evidence until corrected through the normal lifecycle;
- mark current coordination state as stale/unresolved when appropriate;
- run a bounded Audit before material work that depends on the conflict;
- create a corrective Checkpoint only after current evidence is established.
