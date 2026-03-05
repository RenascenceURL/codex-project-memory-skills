# Project Memory Rules

`project-memory-rules` is a Codex skill for repeatable memory workflows:
- global engineering rules (`~/.codex/GLOBAL_ENGINEERING_RULES.md`)
- project memory (`docs/memory.md`)
- project tasks (`docs/tasks/index.md` + `docs/tasks/<task-id>.md`)

## Features
- `/mem` interactive menu:
- `1` Fast Read
- `2` Fast Save
- `3` Pick Task Manually
- `4` Init
- `5` Advanced
- Manual pick always sets selected task to `in_progress` (including reopening `done`)
- Codex startup context:
- print summary in terminal
- inject context payload into initial prompt for interactive/prompt-start sessions

## 功能概览（中文）
- 全局规则统一在 `~/.codex/GLOBAL_ENGINEERING_RULES.md`
- 项目记忆统一在 `docs/memory.md`
- 任务索引与详情统一在 `docs/tasks/`
- `/mem` 主命令菜单支持快速读取、快速存储、手动切任务和高级操作

## Install

### Windows (stable)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_powershell_hooks.ps1
```

### Linux / macOS (experimental)
```bash
bash scripts/install_bash_hooks.sh
bash scripts/install_zsh_hooks.sh
```

Reload shell after install.

## Usage

### Primary command
```powershell
/mem
```

### Windows fallback command (no leading slash)
```powershell
mem
```

### Codex dialog limitation
- `/init` and similar slash commands are built into Codex itself.
- `/mem` is a shell function installed into PowerShell/Bash/Zsh, not a Codex built-in slash command.
- So `/mem` cannot be registered as a native Codex chat slash command from this repo.
- In Codex chat, use normal text to ask the agent to run memory commands, or run `mem`/`/mem` in your terminal.

### Direct commands
```powershell
python scripts/memory_manager.py init --project-path .
python scripts/memory_manager.py context --project-path . --print-summary
python scripts/memory_manager.py context --project-path . --ensure-init --print-summary
python scripts/memory_manager.py save --project-path . --mode task --title "combat-parry"
python scripts/memory_manager.py list-tasks --project-path .
python scripts/memory_manager.py activate-task --project-path . --task-id combat-parry
```

Notes:
- `context` is read-only by default and does not create files.
- To create missing memory files, run `init` (recommended) or pass `--ensure-init`.

### Compatibility slash mode
```powershell
python scripts/memory_manager.py slash /load --project-path .
python scripts/memory_manager.py slash /save --project-path . --title "fix-input" --next "add tests"
```

## File Layout
- `docs/memory.md`
- `docs/tasks/index.md`
- `docs/tasks/<task-id>.md`
- `docs/tasks/archive/` (advanced archive)
- `docs/reports/weekly-YYYY-WW.md` (advanced weekly report)

## Uninstall

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File scripts/uninstall_hooks.ps1
```

### Linux / macOS
```bash
bash scripts/uninstall_hooks.sh ~/.bashrc
bash scripts/uninstall_hooks.sh ~/.zshrc
```

## Privacy
- This skill reads and writes local files only.
- No telemetry and no automatic network upload.

## License
MIT
