## Project memory

At the start of substantial work, read:

1. `docs/project-memory/PROJECT.md`
2. `docs/project-memory/STATUS.md`
3. `docs/project-memory/DECISIONS.md`
4. `docs/project-memory/HANDOFF.md` when it contains active work

Load only task-relevant source documents and code. Prefer available code-graph tools for architecture, symbol discovery, call paths, and focused snippets; otherwise use focused search and bounded reads. Optional tools must never block the task.

Treat initial specifications as a baseline. When current code or maintained documents differ, identify whether the difference is approved evolution, undocumented implementation, unresolved conflict, or regression. Do not silently force the project back to its initial plan.

Do not infer approval from implementation alone. Keep machine-specific source paths out of this shared file; record them as non-portable sources in `PROJECT.md`.

Memory update policy: `approve-decisions`.

After a meaningful verified stage:

- update the current snapshot in `STATUS.md`;
- append factual outcomes and checks to `SESSION_LOG.md`;
- record consequential decisions in `DECISIONS.md`, using `Proposed` until approved;
- update `HANDOFF.md` only for substantial unfinished work;
- report every memory file changed.

Never store secrets, hidden reasoning, or duplicated machine-readable configuration in project memory.
