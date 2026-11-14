#!/bin/sh
# Opens a Ghostty split next to the focused terminal and starts the dispatcher in it.
# DISPATCHER_SESSION=1 marks the new session as the dispatcher; the skill checks it.
# Usage: open-ghostty-split.sh [left|right|up|down|top|bottom] [directory]
# Defaults: down, current directory. Needs Ghostty 1.3+ on macOS (AppleScript).
set -eu

case "${1:-down}" in
  left|right|up|down) direction="${1:-down}" ;;
  top) direction=up ;;
  bottom) direction=down ;;
  *) echo "usage: $0 [left|right|up|down|top|bottom] [directory]" >&2; exit 2 ;;
esac
directory="$(cd "${2:-.}" && pwd)"

if [ "${TERM_PROGRAM:-}" != "ghostty" ]; then
  echo "not running inside Ghostty" >&2
  exit 3
fi

osascript - "$direction" "$directory" <<'APPLESCRIPT'
on run argv
  set splitDirection to item 1 of argv
  set workDir to item 2 of argv
  tell application "Ghostty"
    set cfg to new surface configuration
    set initial working directory of cfg to workDir
    set initial input of cfg to "DISPATCHER_SESSION=1 claude -n dispatcher 'be the dispatcher'" & linefeed
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
