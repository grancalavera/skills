#!/bin/sh
# Shows a path in yazi to the right of the current terminal.
# Reuses a running yazi when one answers on its tty-derived client ID (ya emit-to);
# otherwise opens a new Ghostty split via the ghostty skill's script.
# A file is revealed (hovered) in its parent directory; a directory is opened.
#
# Client ID scheme (shared with the install-yazi skill's `y` wrapper):
#   "9000" followed by the digits of the yazi pane's tty name, e.g. /dev/ttys004 -> 9000004
#   shell: yazi --client-id "9000$(tty | tr -cd '0-9')"
# A yazi started without that ID can't be found, so it isn't reused.
#
# Usage: open-yazi.sh [--dry-run] [--new] [path]   (default path: current directory)
# --new skips reuse and always opens a new split.
# --dry-run prints what it would do and changes nothing (no pane, no ya emit-to).
# Exit codes: 2 bad usage, 3 not inside Ghostty, 4 path missing, 5 yazi missing,
# 6 ghostty skill missing, other = osascript error.
set -eu

dry_run=""
new=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run="--dry-run"; shift ;;
    --new) new=1; shift ;;
    *) break ;;
  esac
done
[ $# -le 1 ] || { echo "usage: $0 [--dry-run] [--new] [path]" >&2; exit 2; }
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

# Reuse: try this user's running yazi processes, newest first. ya emit-to fails
# when no yazi answers on that ID; any failure falls through to a new split.
if [ -z "$new" ] && command -v ya >/dev/null 2>&1; then
  ttys="$(ps -x -o etime=,tty=,comm= | awk '
    $3 ~ /(^|\/)yazi$/ && $2 != "??" {
      n = split($1, p, /[-:]/); s = 0
      if (n == 4) s = ((p[1] * 24 + p[2]) * 60 + p[3]) * 60 + p[4]
      else if (n == 3) s = (p[1] * 60 + p[2]) * 60 + p[3]
      else s = p[1] * 60 + p[2]
      print s, $2
    }' | sort -n | awk '{ print $2 }')"
  for tty in $ttys; do
    id="9000$(printf '%s' "$tty" | tr -cd '0-9')"
    if [ -n "$dry_run" ]; then
      echo "reuse: ya emit-to $id $action '$target' (yazi on $tty, if it answers)"
    elif ya emit-to "$id" "$action" "$target" 2>/dev/null; then
      echo "reused yazi $id on $tty"
      exit 0
    fi
  done
fi

quoted="'$(printf '%s' "$target" | sed "s/'/'\\\\''/g")'"
exec "$split" $dry_run right "$directory" "yazi --client-id \"9000\$(tty | tr -cd '0-9')\" $quoted"
