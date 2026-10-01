## Project memory

Project memory protocol: `maintain-project-memory/v2`
Project memory schema: `project-memory/v1`
Canonical project-memory root: `docs/project-memory`
Memory update policy: `approve-decisions`

At the start of substantial work, read:

1. `docs/project-memory/PROJECT.md`
2. `docs/project-memory/STATUS.md`
3. `docs/project-memory/DECISIONS.md`
4. `docs/project-memory/HANDOFF.md` when it contains active work

Then perform a lightweight freshness check before relying on the loaded memory:

- verify the actual project root and current version-control identity when available;
- compare the current `STATUS.md` and active `HANDOFF.md` with task-relevant repository/runtime evidence;
- if the protocol marker is missing/older, or memory is materially stale or conflicting, treat stale memory as context rather than authority and run a bounded read-only Audit before material work;
- Git is optional: when no valid repository exists, say that VCS freshness is unavailable and use current task-relevant filesystem/runtime evidence instead of inventing a revision.

Load only task-relevant source documents and code. Prefer available code-graph tools for architecture, symbol discovery, call paths, and focused snippets; otherwise use focused search and bounded reads. Optional tools must never block the task.

Treat initial specifications as a baseline. When current code or maintained documents differ, identify whether the difference is approved evolution, undocumented implementation, unresolved conflict, or regression. Do not silently force the project back to its initial plan.

Do not infer approval from implementation alone. Keep machine-specific source paths out of this shared file; record them as non-portable sources in `PROJECT.md`.

Project-memory ownership:

- `docs/project-memory/*` and this memory protocol are maintained through the `maintain-project-memory` lifecycle;
- other workflows may read them as evidence and report staleness, but should not opportunistically rewrite them;
- staging, deployment, mirror, or backup copies are non-canonical unless they are explicitly declared as a separate project root.

After a meaningful verified stage:

- run a Checkpoint: replace the current snapshot in `STATUS.md` rather than appending history;
- append factual outcomes and checks to `SESSION_LOG.md`;
- record consequential decisions in `DECISIONS.md`, using `Proposed` or `Unverified` until approval is established;
- update `HANDOFF.md` only for substantial unfinished work and reset it when that workstream finishes;
- report every memory file changed.

Before any Checkpoint or Handoff write, re-read the target memory files and re-check repository identity. If project-memory or repository HEAD changed since this session loaded its context, reconcile the newer state instead of overwriting it from a stale base.

Never store secrets, hidden reasoning, or duplicated machine-readable configuration in project memory.
