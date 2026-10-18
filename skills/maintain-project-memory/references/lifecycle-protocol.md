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
- If the project is already on the current protocol, run the session-start preflight below before material work. Before substantial **write-capable** work, also verify that its *actual project-local* `AGENTS.md` routes unfinished WIP through Minimum Continuity Record (MCR), not merely that a newer skill is installed.
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

## Minimum WIP continuity

### Activation in existing projects

Before **ordinary coding** in an existing memory-enabled project, read its
actual `AGENTS.md` and run a read-only `audit_project_memory.py
<project-root> --adoption` when MCR routing has not already been established.
This reports `ADOPTION wip_continuity_routing=declared` or
`missing-review-required` based on the project-local instruction text;
`declared` is **not proof of runtime agent compliance**. Protocol/schema
markers alone and installation of a new skill do not upgrade existing
project-local instructions.

When routing is absent/incomplete, propose the smallest project-local
`AGENTS.md` amendment adding a short pointer to the installed current MCR
lifecycle, **preserving existing memory policy and unrelated guidance**.
Obtain the appropriate explicit approval before writing operating rules.
Do not silently rewrite the old fragment or change protocol/schema markers.
**Stop ordinary substantial write-capable implementation until the agreed
project-local adoption is completed**; a read-only assessment may continue.
When an installed skill is explicitly invoked, it can apply MCR under the
current project's existing valid permission policy for that bounded task, but
this does **not** make subsequent ordinary coding sessions adopted or
guaranteed. A user-approved project-local routing rule is the durable trigger.

#### Ambiguous user deferral: classify before edits

A request such as "continue coding, update project memory only when finished,
and ask me before doing so" is **ambiguous**, not permission to write MCR.
Treat "don't update memory", "don't touch STATUS/SESSION_LOG/HANDOFF", "do not
change tracking files until I approve", and broad equivalents as a
**no-tracking-write instruction or unresolved prohibition**. Before any
substantial write-capable step, state that the work requires a minimal factual
WIP record and ask whether that specific record is permitted. Until clarified,
**stop rather than silently writing MCR or accumulating unfinished code**.
When the user explicitly says "defer only the final checkpoint", "do not
approve or change DECISIONS yet", or "postpone the finished documentation,
but keep factual WIP status", MCR can proceed subject to the normal
`notify`/`approve-decisions`/`strict` policy. Explicit read-only or strict
approval gates still override automatic recording. A no-commit instruction
is not a prohibition on approved factual status updates.

This is a **factual in-progress sub-step** of the existing Checkpoint/Handoff
lifecycle, not a fifth operation and **not** a completion checkpoint. Its
purpose is to let the next session recover unfinished substantial write-capable
work from durable files rather than chat history alone. Use the existing
canonical `docs/project-memory/STATUS.md` first; do not introduce a second WIP
ledger, automatic commits, a background service or a new schema marker.

### Required boundaries

1. **Before the first material write:** finish read-only preflight; capture
   project root, branch and exact HEAD (or VCS unavailable), existing
   staged/unstaged/untracked paths and their ownership, intended bounded slice
   and the next action. Revalidate and write the initial factual MCR before
   beginning substantial edits, where the update policy permits it. This
   baseline must not falsely claim an implementation has already happened.
2. **After a meaningful implementation slice:** refresh `STATUS.md` from the
   current diff, completed work and check results, including what remains WIP.
   Do not write after every small edit or tool call.
3. **On material blocker / cross-component contract mismatch:** record the
   two observed sides, relevant paths and impact, what is verified versus
   unresolved, and the next safe action. Do not silently choose or approve
   a new product/architecture/security contract.
4. **Before pause, context transfer, or a final report with material WIP:**
   refresh MCR before handing off, even when a final verified Checkpoint and
   Git commit are not safe. Use `HANDOFF.md` only when a real unfinished
   workstream will transfer to another session/agent.

### Minimum record and ownership

Maintain a concise WIP note inside existing `STATUS.md` sections:
`In progress`, `Blockers and risks`, `Next safe step`, and `Verification`.

- bounded task scope and observed implemented-vs-planned state;
- branch and exact observed HEAD, explicitly labelled **pre-commit**, or
  `VCS unavailable`;
- affected file paths and staged/unstaged/untracked state, distinguishing
  pre-existing or unrelated changes from task-owned changes; do not stage,
  clean or overwrite other work;
- checks actually run/results, unverified areas and known blockers/conflicts;
- next safe action, and `commit readiness: NOT READY` until the separate
  verified Git-completion gates are actually satisfied.

Keep `STATUS.md` a replaceable present-state summary. When a material
boundary adds durable history, append a **short factual** event to
`SESSION_LOG.md` without editing earlier entries. Do not append a new
log entry for each minor change or duplicate the whole status snapshot.
`DECISIONS.md` remains approval-gated; current code is evidence of
implementation, **never** proof of approved intent. Exclude secrets,
credentials and raw environment values.

### Permission and failure boundaries

- `notify` / `approve-decisions`: factual MCR updates are allowed by the
  existing memory policy. **Only an explicitly limited deferral** of final
  semantic documentation/checkpoint leaves MCR permitted. Broad deferrals
  of "project memory" are ambiguous/no-write until clarified (see above).
  Tell the user what was recorded; never override a no-tracking-write request.
- `strict`: show the exact proposed memory diff and obtain approval **before**
  the first MCR write, as required for every memory write. If approval is not
  available, pause substantial write-capable work instead of proceeding with
  a potentially unrecoverable dirty tree.
- Explicit `read-only`: no writes and no MCR mutation; reporting findings
  in the response is allowed. Explicit `no-commit` does **not** block a
  policy-permitted factual MCR update.
- Explicit prohibition of any tracking-file writes, conflicting user
  instructions, missing canonical memory, or unexpected branch/HEAD or
  memory changes during optimistic revalidation: **stop before further
  substantial write-capable changes**, report the constraint and ask for a
  compatible recording plan. Do not evade it by writing a hidden/out-of-tree
  log, committing incomplete work, or claiming memory is current.
- Before **every** MCR write, use the same optimistic revalidation as
  Checkpoint/Handoff. If policy/permissions block writes, a response-only
  summary is useful evidence for the user but **does not satisfy** durable
  continuity.

WIP recording never implies that source changes are committed, tests passed,
a decision was approved or anything was released/deployed. When the bounded
slice is finished and verified, follow the existing Checkpoint and separate
native Git completion procedure; replace WIP status with the actual outcome.

## Local Git completion routing

After a verified, substantial write-capable change, route source/product
documentation maintenance to its existing owner, then perform the memory
Checkpoint and finally the bounded native local Git commit **only** when
`Local Git commit policy` authorizes it. Read
`references/local-git-checkpoints.md` and use the guards there. This
completion rule is distinct from `Memory update policy`. No commit for
read-only tasks, unfinished work, or explicit no-commit instructions. If
Git or user authorization is absent, document the skipped commit without
turning the memory lifecycle into a failure. Do not turn local Git history
into release, deployment or runtime authority.

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
