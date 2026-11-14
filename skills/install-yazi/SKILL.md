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
5. **Show hidden files.** The script configures yazi to show hidden files by default. It
   keeps the user's existing yazi settings intact, and leaves the config untouched when
   hidden files are already shown.
6. **Add a key to maximize the preview pane.** yazi has no built-in key for this, so the
   script installs the official `toggle-pane` plugin with
   `ya pkg add yazi-rs/plugins:toggle-pane`. It skips the install if the plugin is
   already there. It then binds `e` ("expand") in `~/.config/yazi/keymap.toml`; `e` is
   free in yazi's default keymap and needs no Shift:

   ```toml
   [[mgr.prepend_keymap]]
   on   = "e"
   run  = "plugin toggle-pane max-preview"
   desc = "Maximize or restore the preview pane"
   ```

   The script checks for a `toggle-pane max-preview` binding on any key, and keeps the
   rest of the keymap intact:
   - **None**: add the `e` entry.
   - **On `T`** (from an earlier version of this script): change its `on` to `"e"` and
     report the migration.
   - **On `e` or any other key**: leave it alone and report it as already done.

   Homebrew installs the current yazi, so target the current `ya pkg` command and
   `[[mgr.prepend_keymap]]` table, not the older `ya pack -a` and
   `[[manager.prepend_keymap]]` forms. In the follow-ups, tell the user that `e` (or the
   key they already had) toggles the preview between full screen and normal, and that
   `max-current` or `max-parent` maximize the other panes instead.
7. **Add the `y` shell wrapper.** Take yazi's documented `y` wrapper (it changes the
   shell's directory to yazi's on exit) from the docs, and add one change: yazi starts
   with a client ID derived from the terminal's tty, so the `yazi` skill can find and
   reuse it:

   ```sh
   yazi "$@" --client-id "9000$(tty | tr -cd '0-9')" --cwd-file="$tmp"
   ```

   The ID is `9000` followed by the tty name's digits (`/dev/ttys004` → `9000004`). Keep
   it identical to the `yazi` skill's Client ID scheme. Write the wrapper to the user's
   shell rc file (`~/.zshrc` for zsh, `~/.bashrc` for bash) between
   `# >>> yazi y wrapper >>>` and `# <<< yazi y wrapper <<<` marker lines. Skip it when
   the markers already exist. When the rc file already defines `y` outside the markers,
   leave it alone and tell the user to add the `--client-id` flag themselves. In the
   follow-ups, tell the user to open a new shell or `source` the rc file, then start
   yazi with `y`.
8. **Verify and point out follow-ups.** The script ends by confirming yazi runs and
   reporting its version. It then tells the user about any setup the docs recommend that
   the script can't do for them.
9. **Hand over the script.** When the script is written, show the user the command to
   open it in `bat`, and copy that command to the clipboard.

## Invariant

The skill stays idempotent. Any requirement added to this skill must keep the script
safe to rerun: a second run installs, upgrades, and writes nothing new, duplicates no
config entries, and reports each step as already done. If a new requirement would break
this, change the requirement, not the invariant.

## Rules for the script

Every step that changes the system checks the current state first and acts only if
needed, so a second run changes nothing and reports each step as already done.

The script installs any tool it relies on before first using it.

## Done when

- The script exists at a temporary path and covers every dependency the docs currently
  list.
- Run on its own, the script leaves yazi and every dependency installed and up to date,
  confirms yazi runs, reports its version, and lists any manual follow-ups.
- yazi shows hidden files by default, and the user's other yazi settings are unchanged.
- The `toggle-pane` plugin is installed, and `e` (or the key the user already had)
  maximizes or restores the preview pane through exactly one keymap entry.
- The shell rc file holds exactly one `y` wrapper block, starting yazi with the
  tty-derived client ID, unless the user already had their own `y`.
- Run a second time, it changes nothing and reports each step as already done.
- The user has seen the `bat` command for the script, and that command is on their
  clipboard.
