# Maintain Project Memory

[Русская версия](README.ru.md)

A portable Codex skill for initializing, updating, auditing, adopting, and handing off durable project memory. It keeps stable project guidance, current state, decisions, chronological history, and unfinished-work context in separate files.

## What it does

- bootstraps project memory from a document package and repository evidence;
- adopts the current memory protocol in existing projects without overwriting history;
- performs a lightweight session-start freshness check before substantial work;
- updates the current snapshot after meaningful verified stages;
- records consequential decisions without silently approving proposals;
- prepares a compact handoff for another session or agent;
- audits required files, headings, placeholders, dates, protocol markers, and common lifecycle drift;
- distinguishes the original baseline from later approved project evolution;
- detects legacy/unversioned project-memory protocols and nested memory copies;
- uses optimistic revalidation before Checkpoint/Handoff writes to avoid stale-base overwrites;
- uses code-graph tools when available and falls back to focused search when they are not.

The core workflow has no required MCP server, connector, external service, or companion skill.

## Protocol v2

Project-local memory guidance now carries independent protocol/schema markers:

```text
Project memory protocol: `maintain-project-memory/v2`
Project memory schema: `project-memory/v1`
Canonical project-memory root: `docs/project-memory`
```

The protocol version describes lifecycle/routing behavior and is intentionally independent of the installed skill version. The schema version describes the durable file model. A missing or older marker is an adoption signal, not permission to rewrite existing memory automatically.

Protocol v2 adds:

- bounded session-start freshness checks;
- read-only adoption reporting for existing projects;
- explicit canonical-memory ownership;
- Checkpoint/Handoff pre-write revalidation;
- separation of repository HEAD, implementation/deployed identities, and documentation/project-memory revision when they differ;
- explicit provenance for material external/runtime evidence when verification source matters.

It does **not** change the core semantics: `STATUS.md` stays a replaceable current snapshot, `SESSION_LOG.md` stays append-only history, and `HANDOFF.md` stays active unfinished-work context only.

## Repository layout

```text
skills/
└── maintain-project-memory/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/templates/
    ├── references/
    │   ├── lifecycle-protocol.md
    │   └── update-policy.md
    └── scripts/
        ├── audit_memory_proposal.py
        ├── audit_project_memory.py
        ├── init_project_memory.py
        └── memory_snapshot.py
```

Only `skills/maintain-project-memory/` is the installable skill. The repository-level README files and tests are human/project documentation and are intentionally kept outside the skill package.

## Requirements

- Codex with local skill support;
- Python 3.9 or newer for the bundled deterministic scripts;
- Git is recommended for repository-state evidence but is not required;
- no MCP server, connector, external service, or companion skill is required.

## Installation

Install from GitHub with Codex's skill installer by providing the repository URL and the path `skills/maintain-project-memory`.

For a manual installation, copy that directory to:

```text
~/.codex/skills/maintain-project-memory
```

Restart Codex or start a new task if the newly installed skill does not appear in the current session.

## Activation

Explicit invocation is the most predictable first run:

```text
Use $maintain-project-memory to initialize project memory from docs/context.
```

Once installed, Codex can also invoke the skill implicitly when a request matches its description, for example:

- “Initialize project memory from these documents.”
- “Update the project checkpoint after this stage.”
- “Prepare a handoff for a new task.”
- “Audit our project instructions for stale information.”
- “Check whether this old project-memory protocol needs adoption.”

Explicit invocation is useful when you want to guarantee that this workflow is selected. It is not required for every later task: the project's `AGENTS.md` memory protocol carries the ongoing read/update rules.

## Session start

For substantial work in an initialized project, the repository-local `AGENTS.md` protocol should make every new chat/agent converge on the same current context. It requires reading `PROJECT.md`, `STATUS.md`, `DECISIONS.md`, and active `HANDOFF.md`, then comparing that coordination state with current task-relevant repository/runtime evidence.

This is a lightweight preflight, not a full audit and not a fifth operation. `SESSION_LOG.md` is read only when history is needed to explain current state.

If Git is unavailable or invalid, the workflow continues. It must report VCS freshness as unavailable rather than fabricating a revision.

## Starting in an existing project

The initializer is safe by default:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/init_project_memory.py C:\path\to\project
```

On macOS or Linux:

```bash
python3 ~/.codex/skills/maintain-project-memory/scripts/init_project_memory.py /path/to/project
```

It creates only missing files under `docs/project-memory/` and skips existing files. It does not modify `AGENTS.md` automatically. Ask Codex to merge `assets/templates/AGENTS.memory.fragment.md` into the existing project guidance after reviewing local rules.

When project memory already exists, treat the work as adoption/migration instead of a fresh Bootstrap. First run the read-only adoption report:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project --adoption
```

The report identifies protocol/schema markers, VCS availability, handoff state, and nested `docs/project-memory` copies. It does not migrate files automatically. Preserve the project's existing update policy unless the user explicitly changes it.

Do not pass `--overwrite` unless the existing memory files have been reviewed and replacing them is intentional.

## Optimistic revalidation

For long or multi-chat workstreams, capture a read-only memory/VCS fingerprint at session start:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/memory_snapshot.py C:\path\to\project
```

Run it again immediately before Checkpoint or Handoff writes. If canonical project-memory files or repository HEAD changed unexpectedly, load the newer state and reconcile it instead of overwriting from the stale session base. This is intentionally lightweight optimistic revalidation, not a locking system.

## Common prompts

Use these prompts as starting points. Replace placeholder paths with real locations when documentation is outside the repository. The project root usually does not need to be supplied when the task is opened in the project folder: Codex should detect it with `git rev-parse --show-toplevel` and otherwise use the current task directory.

### New project with source documents

```text
Use $maintain-project-memory.

This is a new project. Bootstrap project memory from the supplied source
documents and repository evidence.

Source documents / baseline:
<DOCS_PATH_OR_LIST>

Detect the project root yourself: use git rev-parse --show-toplevel when
available; otherwise use the current task directory.

Create or update only:
- AGENTS.md
- docs/project-memory/PROJECT.md
- docs/project-memory/STATUS.md
- docs/project-memory/DECISIONS.md
- docs/project-memory/SESSION_LOG.md
- docs/project-memory/HANDOFF.md

Keep AGENTS.md as operating guidance and source routing, not as the full product
specification. Put product facts in PROJECT.md and consequential choices in
DECISIONS.md.

If documentation is outside the repository, record it as an external/non-portable
baseline source.

Update policy: notify.
Run audit_project_memory.py when available.
```

### Existing project

```text
Use $maintain-project-memory.

This is an existing project. First run a read-only adoption/freshness audit.
Do not migrate or overwrite existing project-memory merely because the current
skill is newer.

Synchronize project memory with the current repository state only after current
protocol, canonical memory root, stale current-state files, and unresolved
legacy decisions have been identified.

Additional documentation / baseline, if any:
<DOCS_PATH_OR_LIST_OR_EMPTY>

Detect the project root yourself. Read AGENTS.md, README, task-relevant docs and
existing docs/project-memory/* when present.

Compare baseline documents with current repository evidence. Classify
divergences as Consistent with baseline, Approved evolution, Implemented,
approval unverified, Unresolved conflict, or Regression.

Allowed files after review:
- AGENTS.md
- docs/project-memory/*

Preserve the existing update policy unless explicitly changed.
Run audit_project_memory.py --adoption before proposing migration.
Report sources read, files changed, divergences, unresolved decisions, protocol
state, and audit result.
```

### Start from current repo and chat only

```text
Use $maintain-project-memory.

No separate source package is available. Initialize or update project memory from
the current repository, current chat, and completed work.

Treat current chat as supporting context, not automatic approval. Put unsupported
requirements in Proposed, Unverified, or Assumption.

Read focused repository evidence instead of reading the entire repo.
Do not change code, configuration, or product documents.
Update policy: notify.
```

### Checkpoint after concept change

```text
Use $maintain-project-memory.

The project concept has changed:
<SHORT_DESCRIPTION_OF_NEW_DIRECTION>

Record this as Approved evolution only if this message is explicit approval or
another concrete approval source exists.

Before writing, re-read canonical project memory and re-check repository identity.
If it advanced since this session started, reconcile the newer state first.

Update DECISIONS.md, PROJECT.md, STATUS.md, and SESSION_LOG.md.
Update AGENTS.md only if agent operating rules, source routing, memory policy, or
memory protocol changed.

Do not let older MVP/baseline documents override the approved new direction.
Do not change code.
Update policy: notify.
```

### Updating this skill later

```text
Use $maintain-project-memory and skill-creator.

Update the maintain-project-memory skill itself. Keep SKILL.md enforceable; put
long user-facing usage examples in README.md and README.ru.md.

After editing, run repository tests, inspect the diff, and use a reviewed PR.
```

## Memory model

| File | Purpose |
|---|---|
| `AGENTS.md` | Stable operating rules, lifecycle protocol, protocol/schema markers, and canonical memory root |
| `PROJECT.md` | Stable project model and source/authority map |
| `STATUS.md` | Short replaceable current snapshot |
| `DECISIONS.md` | Proposed, unverified, approved, rejected, and superseded consequential decisions |
| `SESSION_LOG.md` | Append-only factual checkpoints |
| `HANDOFF.md` | Replaceable context for substantial unfinished work only |

## Update policies

- `notify`: update verified durable information automatically and report changes.
- `approve-decisions`: update facts automatically, but request approval for consequential decisions. This is the default.
- `strict`: show a proposed diff before every memory-file change.

Protocol adoption does not automatically change the update policy.

See `references/update-policy.md` inside the skill for the exact boundaries.

## Audit

Structural audit:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project
```

Read-only adoption/freshness report:

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project --adoption
```

The deterministic audit does not prove that documented facts are true. Codex must still compare task-relevant memory with current implementation/runtime evidence.

## Optional capabilities

A code knowledge graph can reduce broad repository reads by returning architecture, relationships, and focused snippets. The skill uses one when it is already available. If it is absent, the workflow continues with bounded file and text search. Optional tooling must never become a failure point.

## Inspiration

The memory model was inspired by Sergey Pimenov's articles [AGENTS.md / SESSION_NOTES — project memory for coding agents](https://pimenov.ai/knowledge/agents-md-session-notes-proektnaya-pamyat/) and [Keep the agent memo fresh](https://pimenov.ai/blog/derzhite-pamyatku-agenta-svezhey/). This repository is an independent Codex-skill implementation with original workflows, templates, validation rules, and scripts.

## License and publishing

Released under the MIT License. Keep secrets, project-specific documents, generated memory, and private repository data out of this reusable repository.
