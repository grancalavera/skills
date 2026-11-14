#!/bin/sh
# Opens yazi at a path in a new Ghostty split to the right, via the ghostty skill's script.
# A file opens its parent directory with the file hovered; a directory opens itself.
# Usage: open-yazi.sh [--dry-run] [path]   (default path: current directory)
# Exit codes: 2 bad usage, 3 not inside Ghostty, 4 path missing, 5 yazi missing,
# 6 ghostty skill missing, other = osascript error. --dry-run opens nothing.
set -eu

dry_run=""
if [ "${1:-}" = "--dry-run" ]; then dry_run="--dry-run"; shift; fi
[ $# -le 1 ] || { echo "usage: $0 [--dry-run] [path]" >&2; exit 2; }
target="${1:-.}"

split="$(cd "$(dirname "$0")/../.." && pwd)/ghostty/scripts/open-split.sh"
[ -x "$split" ] || { echo "ghostty skill not found at $split" >&2; exit 6; }

if [ -d "$target" ]; then
  target="$(cd "$target" && pwd)"
  directory="$target"
elif [ -e "$target" ]; then
  directory="$(cd "$(dirname "$target")" && pwd)"
  target="$directory/$(basename "$target")"
else
  echo "path not found: $target" >&2
  exit 4
fi

command -v yazi >/dev/null 2>&1 || { echo "yazi not installed" >&2; exit 5; }

quoted="'$(printf '%s' "$target" | sed "s/'/'\\\\''/g")'"
exec "$split" $dry_run right "$directory" "yazi $quoted"
