#!/usr/bin/env bash
set -euo pipefail

RC_FILE="${1:-$HOME/.bashrc}"
START_MARKER="# >>> project-memory-rules >>>"
END_MARKER="# <<< project-memory-rules <<<"

if [[ ! -f "$RC_FILE" ]]; then
  echo "Profile not found: $RC_FILE"
  exit 0
fi

EXISTING="$(cat "$RC_FILE")"
CLEANED="$(perl -0777 -pe "s/\Q$START_MARKER\E.*?\Q$END_MARKER\E//sg" <<< "$EXISTING" | sed 's/[[:space:]]*$//')"
printf '%s\n' "$CLEANED" > "$RC_FILE"

echo "Removed project-memory-rules hooks from: $RC_FILE"
