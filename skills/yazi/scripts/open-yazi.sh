#!/bin/sh
# Shows a path in yazi to the right of the current terminal.
# Reuses this terminal's yazi pane when one is still running (ya emit-to);
# otherwise opens a new Ghostty split via the ghostty skill's script.
# A file is revealed (hovered) in its parent directory; a directory is opened.
# Usage: open-yazi.sh [--dry-run] [path]   (default path: current directory)
# Exit codes: 2 bad usage, 3 not inside Ghostty, 4 path missing, 5 yazi missing,
# 6 ghostty skill missing, other = osascript error.
# --dry-run prints what it would do and changes nothing (no pane, no emit, no state).
# State: one file per controlling terminal under $YAZI_SKILL_STATE_DIR
# (default ~/.local/state/yazi-skill), holding the yazi client ID.
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
  action=cd
elif [ -e "$target" ]; then
  directory="$(cd "$(dirname "$target")" && pwd)"
  target="$directory/$(basename "$target")"
  action=reveal
else
  echo "path not found: $target" >&2
  exit 4
fi

command -v yazi >/dev/null 2>&1 || { echo "yazi not installed" >&2; exit 5; }

# Key the state by the first controlling terminal up the process tree.
key=default
pid=$$
while [ "${pid:-1}" -gt 1 ]; do
  tty="$(ps -o tty= -p "$pid" | tr -d ' ')"
  case "$tty" in
    ""|"??"|"?") pid="$(ps -o ppid= -p "$pid" | tr -d ' ')" ;;
    *) key="$tty"; break ;;
  esac
done
state_dir="${YAZI_SKILL_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/yazi-skill}"
state="$state_dir/$key"

# Reuse: ya emit-to fails when no yazi with that client ID is running.
if [ -s "$state" ] && command -v ya >/dev/null 2>&1; then
  id="$(cat "$state")"
  if [ -n "$dry_run" ]; then
    echo "reuse: ya emit-to $id $action '$target' (if live; else the split below)"
  elif ya emit-to "$id" "$action" "$target" 2>/dev/null; then
    echo "reused yazi $id"
    exit 0
  else
    rm -f "$state"
  fi
fi

id="$(date +%s)$$"
quoted="'$(printf '%s' "$target" | sed "s/'/'\\\\''/g")'"
"$split" $dry_run right "$directory" "yazi --client-id $id $quoted"
if [ -z "$dry_run" ]; then
  mkdir -p "$state_dir"
  printf '%s\n' "$id" > "$state"
fi
