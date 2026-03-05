#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BASH="$SCRIPT_DIR/install_bash_hooks.sh"
SKILL_ROOT="${1:-$HOME/.codex/skills/project-memory-rules}"

if [[ ! -f "$INSTALL_BASH" ]]; then
  echo "install_bash_hooks.sh not found in $SCRIPT_DIR" >&2
  exit 1
fi

BASHRC_PATH="$HOME/.zshrc" "$INSTALL_BASH" "$SKILL_ROOT"
echo "Installed using zsh profile: $HOME/.zshrc"
