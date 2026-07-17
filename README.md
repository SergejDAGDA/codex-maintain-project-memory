# Maintain Project Memory

[Русская версия](README.ru.md)

A portable Codex skill for initializing, updating, auditing, and handing off durable project memory. It keeps stable project guidance, current state, decisions, chronological history, and unfinished-work context in separate files.

## What it does

- bootstraps project memory from a document package and repository evidence;
- updates the current snapshot after meaningful verified stages;
- records consequential decisions without silently approving proposals;
- prepares a compact handoff for another session or agent;
- audits required files, headings, placeholders, dates, and guidance size;
- distinguishes the original baseline from later approved project evolution;
- uses code-graph tools when available and falls back to focused search when they are not.

The core workflow has no required MCP server, connector, external service, or companion skill.

## Repository layout

```text
skills/
└── maintain-project-memory/
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── assets/templates/
    ├── references/update-policy.md
    └── scripts/
```

Only `skills/maintain-project-memory/` is the installable skill. The repository-level README files are human documentation and are intentionally kept outside the skill package.

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

Explicit invocation is useful when you want to guarantee that this workflow is selected. It is not required for every later task: the project's `AGENTS.md` memory protocol carries the ongoing read/update rules.

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

Do not pass `--overwrite` unless the existing memory files have been reviewed and replacing them is intentional.

## Typical bootstrap prompt

```text
Use $maintain-project-memory to bootstrap this existing project.

Source documents are in docs/context. Inspect the repository and current Git
state, use focused code discovery, and create only missing memory files. Keep
facts separate from assumptions. Do not replace AGENTS.md; propose a merge.
Use the approve-decisions policy and stop for material conflicts.
```

## Memory model

| File | Purpose |
|---|---|
| `AGENTS.md` | Stable operating rules and memory protocol |
| `PROJECT.md` | Stable project model and source map |
| `STATUS.md` | Short current snapshot |
| `DECISIONS.md` | Proposed, approved, rejected, and superseded decisions |
| `SESSION_LOG.md` | Append-only factual checkpoints |
| `HANDOFF.md` | Replaceable context for substantial unfinished work |

## Update policies

- `notify`: update verified durable information automatically and report changes.
- `approve-decisions`: update facts automatically, but request approval for consequential decisions. This is the default.
- `strict`: show a proposed diff before every memory-file change.

See `references/update-policy.md` inside the skill for the exact boundaries.

## Audit

```powershell
python ~/.codex/skills/maintain-project-memory/scripts/audit_project_memory.py C:\path\to\project
```

The audit is structural. A clean result does not prove that the documented facts are true; Codex must still compare them with current project evidence.

## Optional capabilities

A code knowledge graph can reduce broad repository reads by returning architecture, relationships, and focused snippets. The skill uses one when it is already available. If it is absent, the workflow continues with bounded file and text search. Optional tooling must never become a failure point.

## Inspiration

The memory model was inspired by Sergey Pimenov's articles [AGENTS.md / SESSION_NOTES — project memory for coding agents](https://pimenov.ai/knowledge/agents-md-session-notes-proektnaya-pamyat/) and [Keep the agent memo fresh](https://pimenov.ai/blog/derzhite-pamyatku-agenta-svezhey/). This repository is an independent Codex-skill implementation with original workflows, templates, validation rules, and scripts.

## License and publishing

Released under the MIT License. Keep secrets, project-specific documents, generated memory, and private repository data out of this reusable repository.
