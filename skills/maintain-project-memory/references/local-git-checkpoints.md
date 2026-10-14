# Local Git checkpoints

## Goal and ownership

At a substantial **verified** completion boundary, preserve approved code,
project documentation, and the factual project-memory checkpoint in a single
local Git commit when the project has authorized it. This is **not** a separate
Agent Skill, a custom Git implementation, a release process, or GitHub
publication. Use native Git; no mandatory helper is needed.

The coding/documentation task owns its source and product-documentation diff.
`maintain-project-memory` owns only project-memory semantics and the
completion coordination. The current task agent stages and commits the
reviewed result after all applicable owners have finished.

## Policy (independent from memory update policy)

The optional `AGENTS.md` declaration has exactly one value:

- ``Local Git commit policy: `auto` ``: for **verified, finished, write-capable**
  stages, perform a narrow local commit without a repeated confirmation,
  subject to all safety gates below.
- ``Local Git commit policy: `ask` ``: list exact candidate paths and request
  approval before creating each local commit.
- ``Local Git commit policy: `off` ``: never create a local commit through this
  lifecycle.

A new project that explicitly adopts the bundled project-memory template
uses `auto` by default. If an existing project's declaration is absent,
conflicting, or unrecognized, the **effective mode is `ask`**; do not infer
consent from a memory update policy or silently change an existing project's
operating rules. During adoption, propose any policy change separately and
preserve existing stricter instructions. An explicit current-task instruction
such as "read-only", "do not commit", or "wait for approval" overrides `auto`.

`auto` authorizes **local commits only**; it does not authorize `git init`,
`push`, `pull`, fetching third-party material, opening/merging PRs, tagging,
publishing a release, or deploying. `git init` requires explicit approval
even when the policy is `auto`. Git is optional: without a valid repository,
record `SKIPPED — no Git repository` and continue the memory operation.

## When

Use this step once after a meaningful completed feature, bug fix, reviewed
documentation integration, or other approved durable project change.
Complete the code/product documentation checks and, when appropriate, the
project-memory Checkpoint **before** staging. This includes project-local
`docs/project-knowledge/` and `docs/project-memory/` when they were
intentionally changed; exclude external-only exports and runtime artifacts.

Never make an automatic commit after read-only discovery, audit, incomplete
tests, unresolved material blockers, an unapproved change, a refused
strict-mode memory diff, or an intermediate/unfinished operation. No-op if
there is no task-owned diff. A user-requested standalone checkpoint can
remain uncommitted when no safe Git boundary exists.

## Native Git safety procedure

1. Resolve `git rev-parse --show-toplevel` and verify it is the intended
   project root; capture branch, HEAD and `git status --porcelain=v1`.
   Never assume a repository exists from a `.git` folder or create one.
2. Compare the current status to the start-of-task state and identify
   **explicit individual relative file paths** produced or intentionally
   updated by this completed task. Preserve pre-existing user changes and
   all unrelated untracked files. Do not stage a directory recursively unless
   its exact contents were inventoried and approved. Treat symlinks,
   submodules, secrets and runtime/data/backups as review-required.
3. Inspect `git diff`, newly created file contents, affected tests and
   documentation links; stop for unresolved failures. Check `git status`
   and confirm branch/HEAD are unchanged from the verified work base.
4. Check the pre-existing index with `git diff --cached --quiet`.
   If any staged change is already present (including changes to unrelated
   paths), **do not** run the automatic commit or disturb the index. Report
   `SKIPPED — staged changes need review`. Never use `git add -A`,
   `git add .`, `git commit -a`, `--amend`, `reset --hard`, or
   other broad/destructive commands.
5. Stage only the explicit reviewed paths with `git add -- <file1> ...`.
   Inspect `git diff --cached --name-only` and `git diff --cached`.
   Require that every staged path belongs to the approved task scope, the
   patch has no secret or unrelated user data, and `git diff --cached --check`
   succeeds. If the exact staged scope cannot be established, do not commit;
   remove only staging added by the current task when safe and report.
6. Recheck repository HEAD and index scope immediately before committing.
   Make **one** descriptive native `git commit -m "<stage summary>"`.
   If Git identity is missing or a hook prevents the commit, report the
   limitation instead of changing global Git config or bypassing hooks.
7. Verify `git rev-parse HEAD`, `git show --stat --oneline HEAD`, and
   `git status --porcelain=v1`. The commit must contain only intended paths.
   Report new local HEAD, committed files, any unrelated dirty work left
   intact, and whether project-memory status was written against the
   pre-commit HEAD.

If staging or the commit fails, do not claim success. Preserve user work,
never perform destructive cleanup, and report what remains staged so it can
be recovered without guessing. Do not re-run the task or repeatedly retry
commits to hide the failure.

## Revision semantics

Record pre-commit HEAD as such in memory when relevant; it is **not** proof
that the later commit is deployed or tested in runtime. Post-commit SHA is
verified and reported after the commit. Avoid a recursive loop of updating
`STATUS.md` with the new SHA and immediately making another commit.
Normal later checkpoints can incorporate the new repository identity.

## Scope and guarantees

This procedure provides a reproducible narrow **policy**, not atomic Git
transactions or automatic invocation in environments that ignore
`AGENTS.md`. Codex must actually read the project instructions and obey
the active policy. External installers and deployment agents use their own
authorization boundaries; this skill does not silently change them.
