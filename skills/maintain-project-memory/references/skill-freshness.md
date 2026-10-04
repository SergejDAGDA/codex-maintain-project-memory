# Canonical skill freshness

This reference defines how `maintain-project-memory` verifies that the installed skill payload matches the current canonical implementation before relying on current-contract behavior.

## Canonical source

Canonical repository:

- `https://github.com/SergejDAGDA/codex-maintain-project-memory`
- branch: `main`

The canonical repository commit identifies the current skill implementation. This is separate from the project-local protocol marker (`maintain-project-memory/v2`) and from the project-memory schema marker (`project-memory/v1`). A project may be on protocol v2 while the installed skill implementation is stale.

## Freshness check

Before an Audit, adoption/migration review, Bootstrap, Checkpoint, or Handoff that claims to use the current canonical skill contract, resolve the installed skill directory and run the checker with the available Python interpreter:

```text
python <skill-directory>/scripts/check_skill_freshness.py
```

On systems where the interpreter command is `python3`, use that instead.

The primary path compares the complete installed `skills/maintain-project-memory` payload with the skill subtree at canonical GitHub `main` using Git blob identities. It does not rely on a local `.git` directory, installer metadata, or protocol markers.

Run the check once near the start of a substantial session. Re-run only when the canonical branch may have changed during a long-running task or before a write when freshness is otherwise uncertain.

## Network-restricted environments

Some Codex environments block direct network access from local Python even though the skill was installed from GitHub through an installer or another trusted workflow. Do not treat that transport restriction as proof that the installed skill is stale.

Immediately after a user-authorized install/update whose canonical commit was established by a trusted source, record a local install-provenance receipt:

```text
python <skill-directory>/scripts/record_skill_provenance.py --canonical-commit <40-character-sha>
```

The receipt is stored outside the installed skill payload at `~/.codex/skill-provenance/maintain-project-memory.json` by default. It records the canonical repository/branch/commit supplied by the install workflow plus a SHA-256 fingerprint of the complete installed skill payload.

The recorder does **not** contact GitHub and does not prove that the supplied commit is current. Only record provenance when the commit was independently established during the install/update workflow. Recording a guessed SHA defeats the freshness control.

When direct GitHub access is unavailable, run the checker with the trusted commit supplied by the current task or user:

```text
python <skill-directory>/scripts/check_skill_freshness.py --expected-commit <40-character-sha>
```

If the current payload still matches the recorded receipt and the expected commit matches the recorded install commit, the checker returns `verified-local` and marks the operation write-eligible. This proves the installed payload is unchanged since the confirmed installation and corresponds to the supplied expected commit. It does **not** independently prove that GitHub `main` has not advanced since that commit.

Without `--expected-commit`, a valid receipt may still return `verified-local`, but write eligibility remains false because current canonical-main freshness was not established.

## Status semantics

The checker returns one of four statuses:

- `current`: the installed skill payload exactly matches canonical GitHub `main` through a live online comparison.
- `verified-local`: GitHub could not be reached, but the installed payload exactly matches a recorded user-confirmed installation receipt.
- `different`: the installed payload differs from live canonical `main`, differs from its recorded receipt, or the supplied expected commit does not match the recorded install commit.
- `unverified`: neither live canonical state nor a usable local install receipt could establish the installed payload.

`verified-local` is intentionally narrower than `current`: it verifies local install integrity and a known commit, not present-time remote branch state.

## Stop rules

- On `current`, continue normally.
- On `verified-local` with `WRITE_ELIGIBLE yes`, current-contract writes may continue because the payload fingerprint and trusted expected commit both match the recorded installation. Report that canonical currentness is offline/unverified.
- On `verified-local` with `WRITE_ELIGIBLE no`, read-only Audit may continue, but Bootstrap, migration writes, Checkpoint, and Handoff require either a trusted expected commit or explicit user acceptance of the last-known install boundary.
- On `different`, stop before any project-memory mutation. Report the mismatch and update/reinstall or re-establish provenance before continuing.
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

`record_skill_provenance.py` is a separate, explicit post-install action. It writes only the external provenance receipt and does not change the installed skill or any user project.

Updating the installed skill remains a separate user-authorized installation action.

## Reporting

When canonical freshness materially affects the task, report:

- canonical repository and branch;
- canonical commit when established;
- freshness: `current`, `verified-local`, `different`, or `unverified`;
- verification scope: live `canonical-main`, offline `recorded-install`, or none;
- canonical currentness: verified online or unverified offline;
- write eligibility;
- for `different`, the relevant payload/commit mismatch;
- whether the task was allowed to continue under the stop rules above.

Do not substitute the project protocol marker for this check. The layers are distinct:

```text
canonical skill freshness / recorded install integrity
        ↓
project-local protocol generation
        ↓
project-memory freshness
        ↓
current code/config/runtime evidence
```
