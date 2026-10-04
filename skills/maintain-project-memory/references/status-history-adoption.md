# STATUS history during adoption

`STATUS.md` is a replaceable current-state snapshot. It must not become an append-only checkpoint ledger. Historical checkpoints, audits, corrections, and superseded state belong in `SESSION_LOG.md`.

During adoption, `audit_project_memory.py --adoption` reports `ADOPTION status_history=likely-accumulation` only when it finds strong evidence of historical accumulation, such as explicit date-headed sections or multiple dated trailing `Latest ...` / checkpoint / audit / correction sections after the current snapshot. Ordinary dates inside current verification facts are not enough.

A likely-accumulation signal means the project requires at least a small lifecycle review and must not be treated as marker-only. Compare the candidate STATUS history with `SESSION_LOG.md`. `session_log_date_overlap=full` or `partial` is only a review hint; matching dates do not prove semantic duplication.

The audit is read-only. Do not automatically move or delete history. If equivalent history already exists in `SESSION_LOG.md`, remove only the duplicate historical blocks from `STATUS.md` after contextual review. If equivalent history is absent or ambiguous, preserve it until the correct historical record can be established safely.

This guidance does not change `maintain-project-memory/v2` or `project-memory/v1`.
