---
name: project-memory-rules
description: Persist and reuse engineering context across projects with one global rules file and docs-based project memory. Use when starting/resuming development, loading task context, saving handoffs, manually switching active tasks, or enforcing personal cross-project rules without rewriting them per repository.
---

# Project Memory Rules

## Overview

Use this skill to standardize memory operations in two scopes:

- Global scope: `~/.codex/GLOBAL_ENGINEERING_RULES.md`
- Project scope: `docs/memory.md`, `docs/tasks/index.md`, `docs/tasks/<task-id>.md`

## Startup Behavior

When shell hooks are installed, starting `codex` does two things:

1. Print context summary in terminal.
2. Inject merged prompt payload into Codex initial prompt for interactive/prompt-start sessions.

Use this command directly when needed:

```powershell
python <skill-dir>/scripts/memory_manager.py context --project-path <project-root> --print-summary
```

`context` is read-only by default (no file creation).  
Use `init` (preferred) or `context --ensure-init` when you explicitly want to create missing files.

## `/mem` Menu Workflow

Primary command is `/mem`.

Top-level menu:
- `1` Fast Read
- `2` Fast Save
- `3` Pick Task Manually
- `4` Init
- `5` Advanced

Rules:
- Pick Task manually must set selected task status to `in_progress`, including reopening `done`.
- Fast Save mode `1` updates only `docs/tasks/index.md`.
- Fast Save mode `2` updates task file and syncs `docs/memory.md`.

## Commands

- Initialize files:
  - `python <skill-dir>/scripts/memory_manager.py init --project-path <project-root>`
- Build startup payload:
  - `python <skill-dir>/scripts/memory_manager.py context --project-path <project-root> --json`
- Build startup payload and force initialization:
  - `python <skill-dir>/scripts/memory_manager.py context --project-path <project-root> --ensure-init --json`
- Save updates:
  - `python <skill-dir>/scripts/memory_manager.py save --project-path <project-root> --mode task --title "task-name"`
- List tasks:
  - `python <skill-dir>/scripts/memory_manager.py list-tasks --project-path <project-root>`
- Activate task:
  - `python <skill-dir>/scripts/memory_manager.py activate-task --project-path <project-root> --task-id <id>`
- Advanced:
  - `archive-done`, `stats`, `weekly-report`

Slash compatibility remains:
- `/init`, `/load`, `/summary`, `/save`, `/menu`

## Installers

- Windows:
  - `powershell -ExecutionPolicy Bypass -File <skill-dir>/scripts/install_powershell_hooks.ps1`
- Linux/mac (experimental):
  - `bash <skill-dir>/scripts/install_bash_hooks.sh`
  - `bash <skill-dir>/scripts/install_zsh_hooks.sh`
- Uninstall:
  - `powershell -ExecutionPolicy Bypass -File <skill-dir>/scripts/uninstall_hooks.ps1`
  - `bash <skill-dir>/scripts/uninstall_hooks.sh ~/.bashrc`
  - `bash <skill-dir>/scripts/uninstall_hooks.sh ~/.zshrc`

## Templates

Reusable templates are under `templates/`:

- `templates/docs-memory.md`
- `templates/tasks-index.md`
- `templates/task-item.md`

## Behavior Rules for This Skill

- Keep entries factual and concise.
- Prefer updates over duplicate files.
- Preserve user-authored task content when appending logs.
- If user instruction conflicts with stored rule, follow explicit user instruction and note the conflict.

## References

- Rule categories and starter content: `references/global-rules-guide.md`
