## Project memory

Project memory protocol: `maintain-project-memory/v2`
Project memory schema: `project-memory/v1`
Canonical project-memory root: `docs/project-memory`
Memory update policy: `approve-decisions`
Local Git commit policy: `auto`

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
- report every memory file changed;
- when this verified stage changed project files and the declared Local Git commit policy permits it, synchronize affected product docs (use `project-documentation` if installed and relevant; otherwise update the maintained docs directly) and memory first, then make one narrowly scoped **local-only** Git commit via native Git. Never stage unrelated changes. See the installed `maintain-project-memory` skill's `references/local-git-checkpoints.md`.

When this project has an approved **separate deployment** workflow:
- on "prepare for deployment", use the installed documentation/release workflow as appropriate, then a memory Handoff to freeze the approved source revision/build, preserve explicit data-protection gates, and give a bounded deployment prompt; do not mark the release as deployed;
- after deployment, when an authorized shared project checkout and a factual deployment receipt are available, use a memory Checkpoint to record the actual deployed identity, verification provenance and pending actions and close the Handoff. Call the documentation owner only if maintained technical docs really changed;
- on resuming development, compare the project status and deployed-revision evidence before continuing. If a different deployment chat cannot write this canonical root, report synchronization pending; do not invent success from its chat transcript.

Before any Checkpoint or Handoff write, re-read the target memory files and re-check repository identity. If canonical project-memory or repository HEAD changed unexpectedly outside the changes made by this session, load and reconcile the newer state instead of overwriting it from a stale base.

Do not commit after a read-only task, an explicit no-commit instruction, or when
pre-existing staged files, unresolved material failures or unclear scope
make staging unsafe. Never perform push, PR/merge, tag, release or deployment
as part of a local checkpoint. If Git is unavailable, report the skipped
commit; Git remains optional.

Never store secrets, hidden reasoning, or duplicated machine-readable configuration in project memory.
