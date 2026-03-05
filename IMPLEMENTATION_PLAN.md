# Project Memory Rules v0.1 Execution Plan

## Objective
- Publish-ready skill with:
- `/mem` as primary command (menu + shortcuts)
- startup context injection into Codex initial prompt
- docs-based project memory (`docs/memory.md`, `docs/tasks/index.md`, `docs/tasks/<id>.md`)
- install/uninstall scripts and release assets for GitHub

## Execution Steps
1. Stabilize core engine (`scripts/memory_manager.py`)
2. Upgrade PowerShell installer (`scripts/install_powershell_hooks.ps1`)
3. Add uninstall scripts (PowerShell + bash/zsh)
4. Add Linux/mac experimental installers (bash + zsh)
5. Add templates and align SKILL.md
6. Add README (CN/EN), LICENSE, CI workflow
7. Smoke test core flows and install hooks
8. Sync final skill to `~/.codex/skills/project-memory-rules`

## Core Behavioral Contracts
- Top menu: `1 Fast Read`, `2 Fast Save`, `3 Pick Task Manually`, `4 Advanced`
- Pick task must always set status to `in_progress` (including reopening `done`)
- Codex wrapper must:
- print terminal summary
- inject prompt payload for interactive/prompt-start sessions
- leave subcommand invocations (`--help`, `exec`, `review`, etc.) unchanged

## Recovery Rules (Context Reset)
- Always read `IMPLEMENTATION_PROGRESS.md` first in any new session/window.
- Resume from the first step whose status is not `done`.
- Append only factual completion notes with timestamp.
