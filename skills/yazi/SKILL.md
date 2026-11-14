---
name: yazi
description: Opens yazi, the terminal file manager, in a Ghostty split to the right of the current terminal, at the file or folder the conversation is about, so the user can browse it. Use when the user says "yazi", alone or with a target ("yazi", "yazi this", "yazi the skill").
compatibility: macOS with Ghostty 1.3+, yazi, and the ghostty skill installed beside this one.
---

# Yazi

## 1. Resolve the path

Take the first that applies:

1. The target the user named ("yazi the README").
2. The file or folder the conversation most recently discussed, created or edited. When several files changed together, use their deepest common parent directory.
3. The worktree of the task or PR under discussion.
4. This session's working directory.

Done when you hold one absolute path.

## 2. Open yazi

Run the script beside this file:

```bash
scripts/open-yazi.sh <absolute-path>
```

It calls the `ghostty` skill's `open-split.sh` to open a new split on the right running yazi. A file opens its parent directory with the file hovered; a directory opens itself. Every trigger opens a new split; the user closes it with `q`.

Done when the script exits 0. Reply in one line with the path.

## Exit codes

- `3`: not inside Ghostty. Tell the user and give the manual command: `yazi '<path>'`.
- `4`: the path doesn't exist. Report it and offer its nearest existing parent.
- `5`: yazi isn't installed. Point the user to the `install-yazi` skill.
- `6`: the `ghostty` skill isn't installed beside this one. Report it.
- Anything else: report the error and give the manual command.

## Testing

`scripts/open-yazi.sh --dry-run <path>` prints the split it would open and opens nothing. Use it whenever you test.
