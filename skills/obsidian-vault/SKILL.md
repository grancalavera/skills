---
name: obsidian-vault
description: Use the `obsidian` CLI to work with an Obsidian vault through the running app instead of editing markdown files directly. Use whenever the user mentions their vault, notes, Obsidian, wikilinks, backlinks, daily note, tags or tasks across notes, `.base` files, or asks to find, add to, move, rename or delete a note — including from an unrelated code repo, since the CLI reaches the vault from any directory. Renaming or moving vault files with `mv` silently breaks inbound links.
compatibility: Requires the `obsidian` CLI on PATH and the Obsidian desktop app running with the target vault open.
---

# Obsidian Vault

Run `obsidian help` first, and `obsidian help <command>` for exact option names. Don't guess options.
If even `help` prints `Vault not found.`, no vault is open in the app: ask the user to open one.
Don't fall back to editing the files directly.

The rules below cover where `help` is wrong or silent. Every one of these fails without an error.

## Errors exit 0
Every failure exits 0, including unknown commands and bad options. Don't chain with `&&` or rely
on `set -e`. Read the output, and treat a leading `Error:` as failure.

## `vault=` is ignored
`help` documents `vault=<name>`, but it doesn't work. Every command hits the vault that's active
in the app, even if you name another one. Nothing on disk reliably says which vault is active,
so ask the app:
- `obsidian vault info=name` shows the vault that writes will hit.
- Your memory holds the name of the user's main vault. If it doesn't, ask the user and save
  the answer to memory.
- Before the first write in a session, check that the active vault is that one, unless the user
  named another. If it isn't, stop and ask them to switch. Never offer `vault=` as a fix, and
  don't switch vaults yourself.

## Rename and move
Use `obsidian rename` / `obsidian move`, never `mv`. They rewrite inbound links only if the app
setting is on, and Obsidian's default is off:
- Before renaming, check `obsidian eval code="app.vault.getConfig('alwaysUpdateLinks')"`.
  Ask the app, not `.obsidian/app.json`.
- If it's `false`, tell the user before renaming. Otherwise the file is renamed, a modal appears,
  the CLI hangs, and every inbound link breaks. The fix is *Settings → Files and links →
  Automatically update internal links*, or clicking **Always update** in the dialog.
- If a rename or move hasn't returned after a few seconds, don't retry it. The rename has
  already happened and a dialog is waiting. Tell the user.
- Afterwards, check that `obsidian unresolved` shows no new dead links and that
  `backlinks file="<new>" total` matches the count from before.
`delete` sends the note to Obsidian's trash. `delete permanent` can't be undone.

## Links: ask the graph, not grep
For link questions, use `backlinks`, `links`, `orphans`, `unresolved` and `deadends`. Grep misses
piped, case-variant, heading and block links, and it matches code fences. Use grep for text only.
A bare `[[Alias]]` doesn't resolve: aliases aren't link targets.

## Smaller gotchas
- `search:context` returns duplicate lines. Deduplicate them, or use `search ... total` for counts.
- There's no in-place edit. To change note text, use ordinary file tools on
  `$(obsidian vault info=path)/<path from obsidian file>`. Editing content directly is fine;
  renames, moves and deletes must go through the app.
- `eval` runs arbitrary JS in the user's app. Use it only for read-only checks like the one above.

## Manners
Report what commands return now, and re-run them rather than reusing old counts. `orphans` and
`unresolved` answer questions; they aren't a to-do list. Don't offer cleanup the user didn't ask for.
