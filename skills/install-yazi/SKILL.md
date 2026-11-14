---
name: install-yazi
description: Writes an idempotent install-or-upgrade script for yazi, the terminal file manager, on macOS using Homebrew. It includes every optional dependency yazi uses to preview different file types, taken from yazi's current online docs. Use this whenever the user wants to install, set up, upgrade, or reinstall yazi on a Mac, asks for a yazi install script, or wants yazi's preview/rendering dependencies installed through brew, even if they don't say "script".
compatibility: macOS with Homebrew. Needs web access to read yazi's installation documentation.
---

# Install yazi

Write a shell script that installs yazi and all of its file-preview dependencies with
Homebrew.

## Requirements

1. **Write the script to a temporary path.** Make it executable. Don't run it unless
   the user asks you to.
2. **Read the docs when you run, not from memory.** Open yazi's online installation
   documentation. Take from it the current full list of dependencies yazi uses to preview
   or render different file types, plus the Homebrew install steps it recommends.
3. **Check and update Homebrew.** Before changing anything, the script stops with a clear
   message if Homebrew isn't installed. It updates Homebrew before installing anything.
4. **Install what's missing, upgrade what's outdated.** For yazi and for each dependency,
   check its state. Install it if it's missing, upgrade it if it's outdated, and leave it
   alone if it's current. Say which case applied. Upgrade only these packages, not
   everything else the user has installed.
5. **Verify and point out follow-ups.** The script ends by confirming yazi runs and
   reporting its version. It then tells the user about any setup the docs recommend that
   the script can't do for them.
6. **Hand over the script.** When the script is written, show the user the command to
   open it in `bat`, and copy that command to the clipboard.

## Rules for the script

Every step that changes the system checks the current state first and acts only if
needed, so a second run changes nothing and reports each step as already done.

The script installs any tool it relies on before first using it.

## Done when

- The script exists at a temporary path and covers every dependency the docs currently
  list.
- Run on its own, the script leaves yazi and every dependency installed and up to date,
  confirms yazi runs, reports its version, and lists any manual follow-ups.
- Run a second time, it changes nothing and reports each step as already done.
- The user has seen the `bat` command for the script, and that command is on their
  clipboard.
