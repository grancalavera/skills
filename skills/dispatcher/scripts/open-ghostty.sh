#!/bin/sh
# Opens a new Ghostty window, or a split next to the focused terminal, and starts the dispatcher in it.
# DISPATCHER_SESSION=1 marks the new session as the dispatcher; the skill checks it.
# Usage: open-ghostty.sh [window|left|right|up|down|top|bottom] [directory]
# Defaults: window, current directory. Needs Ghostty 1.3+ on macOS (AppleScript).
set -eu

case "${1:-window}" in
  window|left|right|up|down) target="${1:-window}" ;;
  top) target=up ;;
  bottom) target=down ;;
  *) echo "usage: $0 [window|left|right|up|down|top|bottom] [directory]" >&2; exit 2 ;;
esac
directory="$(cd "${2:-.}" && pwd)"

if [ "${TERM_PROGRAM:-}" != "ghostty" ]; then
  echo "not running inside Ghostty" >&2
  exit 3
fi

osascript - "$target" "$directory" <<'APPLESCRIPT'
on run argv
  set target to item 1 of argv
  set workDir to item 2 of argv
  tell application "Ghostty"
    set cfg to new surface configuration
    set initial working directory of cfg to workDir
    set initial input of cfg to "DISPATCHER_SESSION=1 claude -n dispatcher 'be the dispatcher'" & linefeed
    if target is "window" then
      new window with configuration cfg
    else
      set currentTerm to focused terminal of selected tab of front window
      if target is "left" then
        split currentTerm direction left with configuration cfg
      else if target is "right" then
        split currentTerm direction right with configuration cfg
      else if target is "up" then
        split currentTerm direction up with configuration cfg
      else
        split currentTerm direction down with configuration cfg
      end if
    end if
  end tell
end run
APPLESCRIPT
