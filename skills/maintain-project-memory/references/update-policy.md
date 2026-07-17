# Update policy

Choose one policy per project and record it in the memory protocol section of `AGENTS.md`.

## `notify`

Automatically update verified facts, current status, logs, stable project descriptions, and approved decisions. Report every changed memory file at the end of the task.

Use only when the user has explicitly delegated broad documentation maintenance.

## `approve-decisions` (default)

Automatically update:

- verified completed work;
- checks and observed results;
- current status and an already-agreed next step;
- factual session-log entries;
- resolved handoff items.

Request approval before:

- changing goals, scope, constraints, or ownership;
- recording an architecture, product, security, data, or operational decision as approved;
- changing boundaries or permissions in `AGENTS.md`;
- replacing a documented source of truth;
- deleting or rewriting decision history.

When work should continue without waiting, record the item as `Proposed` and keep existing approved behavior authoritative.

## `strict`

Prepare and show a proposed diff before changing any memory file. Use for regulated, high-risk, or multi-owner projects.

## Universal rules

- Never store secrets, credentials, tokens, or raw `.env` content.
- Prefer links to canonical code/config over copied versions or values.
- Preserve unrelated user edits.
- Do not turn hypotheses into facts.
- Do not infer approval from implementation alone.
- Update existing decision entries instead of duplicating them.
- Keep machine-specific source paths in the project source map, not shared operating guidance.
- Ensure `Next safe step` remains pending after the current memory update completes.
- Preserve approved decision history unless an explicit reviewed change supersedes or removes an entry.
- Write final status as post-operation state, not as a proposal that still awaits the operation being recorded.
- Do not create a handoff for work that will finish in the current interaction.
- Keep `STATUS.md` current and short; keep history in `SESSION_LOG.md`.
- Notify the user after every automatic durable-memory update.
