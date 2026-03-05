#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="${1:-$HOME/.codex/skills/project-memory-rules}"
MEMORY_SCRIPT="$SKILL_ROOT/scripts/memory_manager.py"
RC_FILE="${BASHRC_PATH:-$HOME/.bashrc}"

if [[ ! -f "$MEMORY_SCRIPT" ]]; then
  echo "memory_manager.py not found: $MEMORY_SCRIPT" >&2
  exit 1
fi

START_MARKER="# >>> project-memory-rules >>>"
END_MARKER="# <<< project-memory-rules <<<"

SNIPPET=$(cat <<'EOF'
__START_MARKER__
export PROJECT_MEMORY_RULES_SCRIPT="__MEMORY_SCRIPT__"

mem() {
  local cmd="${1:-}"
  shift || true
  local project_path="${PWD}"
  if [[ -n "${1:-}" && "$1" == "--project-path" ]]; then
    project_path="${2:-$PWD}"
    shift 2 || true
  fi

  if [[ -z "$cmd" ]]; then
    python "$PROJECT_MEMORY_RULES_SCRIPT" menu --project-path "$project_path"
    return
  fi

  case "${cmd,,}" in
    1|/load|load)
      python "$PROJECT_MEMORY_RULES_SCRIPT" context --project-path "$project_path" --skip-init --print-summary
      ;;
    2|4|/save|save|/advanced|advanced)
      python "$PROJECT_MEMORY_RULES_SCRIPT" menu --project-path "$project_path"
      ;;
    3|/pick|pick)
      python "$PROJECT_MEMORY_RULES_SCRIPT" menu --project-path "$project_path"
      ;;
    *)
      python "$PROJECT_MEMORY_RULES_SCRIPT" slash "$cmd" --project-path "$project_path" "$@"
      ;;
  esac
}

codex() {
  local known_subcommands="exec review login logout mcp mcp-server app-server completion sandbox debug apply resume fork cloud features help"
  local project_path="$PWD"
  local summary prompt merged
  summary="$(python "$PROJECT_MEMORY_RULES_SCRIPT" context --project-path "$project_path" --skip-init --print-summary 2>/dev/null || true)"
  [[ -n "$summary" ]] && printf '%s\n' "$summary"
  prompt="$(python "$PROJECT_MEMORY_RULES_SCRIPT" context --project-path "$project_path" --skip-init --print-prompt 2>/dev/null || true)"

  if [[ $# -eq 0 && -n "$prompt" ]]; then
    command codex "$prompt"
    return
  fi

  if [[ $# -gt 0 ]]; then
    local first="${1,,}"
    for sub in $known_subcommands; do
      if [[ "$first" == "$sub" ]]; then
        command codex "$@"
        return
      fi
    done
    if [[ "${first:0:1}" != "-" && -n "$prompt" ]]; then
      merged="${prompt}"$'\n\n''[USER REQUEST]'$'\n'"$*"
      command codex "$merged"
      return
    fi
  fi

  command codex "$@"
}
__END_MARKER__
EOF
)

SNIPPET="${SNIPPET/__START_MARKER__/$START_MARKER}"
SNIPPET="${SNIPPET/__END_MARKER__/$END_MARKER}"
SNIPPET="${SNIPPET/__MEMORY_SCRIPT__/$MEMORY_SCRIPT}"

touch "$RC_FILE"
EXISTING="$(cat "$RC_FILE")"
CLEANED="$(perl -0777 -pe "s/\Q$START_MARKER\E.*?\Q$END_MARKER\E//sg" <<< "$EXISTING" | sed 's/[[:space:]]*$//')"

{
  [[ -n "$CLEANED" ]] && printf '%s\n\n' "$CLEANED"
  printf '%s\n' "$SNIPPET"
} > "$RC_FILE"

echo "Installed project-memory-rules hooks into: $RC_FILE"
echo "Reload shell: source \"$RC_FILE\""
