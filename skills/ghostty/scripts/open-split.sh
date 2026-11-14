#!/bin/sh
# Opens a Ghostty split next to the focused terminal, optionally running a command in it.
# Usage: open-split.sh [--dry-run] <left|right|up|down|top|bottom> [directory] [command]
# Defaults: current directory, no command (a plain shell). Needs Ghostty 1.3+ on macOS (AppleScript).
# --dry-run prints what it would open and exits 0 without touching Ghostty.
# Exit codes: 2 bad usage, 3 not inside Ghostty, 4 directory missing, other = osascript error.
set -eu

usage() { echo "usage: $0 [--dry-run] <left|right|up|down|top|bottom> [directory] [command]" >&2; exit 2; }

dry_run=0
if [ "${1:-}" = "--dry-run" ]; then dry_run=1; shift; fi
[ $# -ge 1 ] || usage

case "$1" in
  left|right|up|down) direction="$1" ;;
  top) direction=up ;;
  bottom) direction=down ;;
  *) usage ;;
esac

if [ ! -d "${2:-.}" ]; then
  echo "directory not found: ${2:-.}" >&2
  exit 4
fi
directory="$(cd "${2:-.}" && pwd)"
command="${3:-}"

if [ "$dry_run" -eq 1 ]; then
  printf 'direction: %s\ndirectory: %s\ncommand: %s\n' "$direction" "$directory" "$command"
  exit 0
fi

if [ "${TERM_PROGRAM:-}" != "ghostty" ]; then
  echo "not running inside Ghostty" >&2
  exit 3
fi

osascript - "$direction" "$directory" "$command" <<'APPLESCRIPT'
on run argv
  set splitDirection to item 1 of argv
  set workDir to item 2 of argv
  set startCommand to item 3 of argv
  tell application "Ghostty"
    set cfg to new surface configuration
    set initial working directory of cfg to workDir
    if startCommand is not "" then set initial input of cfg to startCommand & linefeed
    set currentTerm to focused terminal of selected tab of front window
    if splitDirection is "left" then
      split currentTerm direction left with configuration cfg
    else if splitDirection is "right" then
      split currentTerm direction right with configuration cfg
    else if splitDirection is "up" then
      split currentTerm direction up with configuration cfg
    else
      split currentTerm direction down with configuration cfg
    end if
  end tell
end run
APPLESCRIPT
