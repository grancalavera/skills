---
name: ghostty
description: Opens a Ghostty split next to the focused terminal, in a chosen direction and directory, optionally running a command in it. Use when the user asks to open something in a Ghostty pane or split ("open the skills repo in a Ghostty pane to the right"), or when another skill needs a Ghostty split.
compatibility: macOS with Ghostty 1.3+ (uses Ghostty's AppleScript API).
---

# Ghostty

Run the script beside this file:

```bash
scripts/open-split.sh [--dry-run] <left|right|up|down|top|bottom> [directory] [command]
```

1. **Direction**: the one the user or calling skill named (top = up, bottom = down). With none named, use `right`.
2. **Directory**: an absolute path. With none named, use this session's working directory.
3. **Command**: one shell string, typed into the new pane's shell and run. Shell-quote any paths inside it. Omit it for a plain shell.

Done when the script exits 0. Reply in one line naming what opened and where.

## Exit codes

- `2`: bad usage. Fix the arguments and retry.
- `3`: not inside Ghostty (`$TERM_PROGRAM` isn't `ghostty`). Tell the user, and give them the manual steps: open a pane, `cd` to the directory, run the command.
- `4`: the directory doesn't exist. Report it.
- Anything else: `osascript` failed, often because Ghostty is older than 1.3. Report the error and give the manual steps.

## Testing

`--dry-run` prints the resolved direction, directory and command, and opens nothing. Use it whenever you test the script or a skill that calls it, so the user's terminal stays untouched.
