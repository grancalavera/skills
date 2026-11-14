---
name: install-yazi
description: Writes an idempotent install script for yazi, the terminal file manager, on macOS using Homebrew. It includes every optional dependency yazi uses to preview different file types, taken from yazi's current online docs. Use this whenever the user wants to install, set up, or reinstall yazi on a Mac, asks for a yazi install script, or wants yazi's preview/rendering dependencies installed through brew, even if they don't say "script".
compatibility: macOS with Homebrew. Needs web access to read yazi's installation documentation.
---

# Install yazi

Write a shell script that installs yazi and all of its file-preview dependencies with
Homebrew. You write the script yourself, based on the requirements below and on what
yazi's documentation says right now.

## Requirements

1. **Write the script to a temporary path.** Make it executable. Don't run it unless
   the user asks you to.
2. **Read the docs when you run, not from memory.** Open yazi's online installation
   documentation. Take from it the current full list of dependencies yazi uses to preview
   or render different file types, plus the Homebrew install steps it recommends. The
   list changes over time, so treat what the docs say today as the source of truth.
3. **Update Homebrew first.** This is the script's first action. If Homebrew isn't
   installed, stop at once with a clear message.
4. **Install only what's missing.** For yazi and for each dependency, check whether it's
   already installed. Install it only if it isn't, and say which case applied.
5. **Hand over the script.** When the script is written, show the user the command to
   open it in `bat`, and copy that command to the clipboard (on macOS, through the system
   clipboard utility).

## Rules for the script

**Make every step that changes the system safe to re-run.** Installs are not the only
such steps. Any step the docs prescribe after installing (configuring, linking,
activating, overwriting, and so on) also needs a check first: is it already in the
desired state? Act only if it isn't. Never run a step that forces or overwrites
something without a check, because a second run would undo changes the user may have
made on purpose. On a second run, each step should report "already done" instead of
repeating itself or printing noisy warnings.

**Keep the script's own tools separate from the software's dependencies.** The software's
dependencies are what yazi needs. The script's tools are what the script itself uses to
do its work, such as parsing output or running checks. Check for the script's tools and
install them at the start, before anything uses them. Don't count on one of them being
installed along the way because it happens to be on yazi's dependency list: the order of
the steps or the docs' list could change. To decide what state something is in, use the
package manager's documented, stable commands rather than reading its internal files.

## Done when

- The script exists at a temporary path and covers every dependency the docs currently
  list.
- Running it a second time changes nothing and reports each step as already done.
- The user has seen the `bat` command for the script, and that command is on their
  clipboard.
