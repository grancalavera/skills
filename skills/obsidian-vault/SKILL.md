---
name: obsidian-vault
description: Use the `obsidian` CLI to work with an Obsidian vault through the running app instead of poking at the markdown files directly. Reach for this whenever the user mentions their vault, their notes, Obsidian, wikilinks, backlinks, a daily note, tags or tasks across notes, `.base` files, or asks to move, rename or delete a note — and especially phrases like "rename this note", "move X into Y folder", "what links here", "what does my daily note say", "add this to my notes", "find the note about...", "which notes are orphaned", "what am I looking at in Obsidian". Also use it when a session in some unrelated code repo needs to write something into the user's notes, since the CLI reaches the vault from any working directory. Renaming or moving a note with `mv` silently breaks every inbound link, so consult this skill before touching vault files with shell commands.
compatibility: Requires the `obsidian` CLI on PATH and the Obsidian desktop app running with the target vault open.
---

# Obsidian Vault

The `obsidian` CLI talks to the *running app*, not to the directory, so it answers from
Obsidian's live index: which links resolve, what's on screen, what a `.base` query returns.
It also reaches the vault from any working directory, which is what makes it useful from
inside an unrelated code repo.

**Start with `obsidian help`** — the command surface is self-documenting, and
`obsidian help <command>` gives exact option names for any of them. Guessing option names
is a bad idea here for reasons the next section explains.

This skill covers only what `help` gets *wrong* or leaves out. Those gaps all fail silently,
which is the problem: the commands look like they worked.

## Failures do not set an exit code

Every error still exits 0 — a missing file, a bad option, even a command that doesn't exist:

```
$ obsidian file file="No Such Note"   ->  Error: File "No Such Note" not found.    exit 0
$ obsidian notacommand                ->  Error: Command "notacommand" not found.  exit 0
```

So `cmd && next`, `set -e`, and "it succeeded because it didn't fail" are all unsound.
**Read the output.** A command worked if it printed what you expected. When scripting
several steps, check stdout for a leading `Error:`, and compare strings rather than
branching on exit status:

```bash
[ "$(obsidian vault info=name)" = "Expected Vault" ] || exit 1
```

## `vault=` does not select a vault

`obsidian help` documents a global option — `vault=<name>  Target a specific vault by name`.
It does not work. Naming a vault that exists but isn't open returns the **active** vault's
answer, exit 0, no warning; a name that doesn't exist at all behaves identically. Every
command hits whatever vault the app currently has open, and `delete permanent` is in the
command list.

There is also no "default vault" to look up. Obsidian's registry
(`~/Library/Application Support/obsidian/obsidian.json`) marks *every* vault `open: true`
and its `ts` field can point at a vault that isn't the live one, because the file is written
lazily and lags the running app. Nothing on disk encodes which vault was *meant*.

So:

1. **Ask the app which vault is live** — this is the only authoritative answer:

   ```bash
   obsidian vault info=name     # the vault every other command will actually hit
   obsidian vaults verbose      # known vaults and paths (does NOT mark the active one)
   ```

2. **Know which vault is intended.** If the user has more than one and either could be meant,
   ask. Once you have a *confirmed* answer, record it where a later session will find it —
   what the user actually told you, not a guess you made because one vault happened to be
   open, and preferably somewhere private rather than a checked-in repo file.

3. **Verify before the first write, and stop on mismatch.** Don't switch vaults yourself and
   don't proceed because it's probably fine — ask the user to open the right one. Never offer
   `vault=<name>` as the fix; it will quietly write to the wrong vault.

Reads are free, so check once before writing rather than before every command.

## `rename` and `move` only update links if the vault is configured for it

This is the reason to use the CLI at all: `mv note.md folder/` leaves every `[[note]]`
pointing at nothing and reports no error, while `obsidian move` and `obsidian rename` go
through the app, which *can* rewrite inbound links. (`obsidian delete` likewise lands the
file in Obsidian's trash; plain `delete` is recoverable, `delete permanent` is not.)

"Can" is load-bearing. Link rewriting depends on the vault's **"Automatically update
internal links"** setting, and Obsidian's default is **off**. With it off:

- the file is renamed on disk straight away;
- the app raises a modal — *"Do you want to update internal links that link to this file?"*
  with buttons **Always update / Just once / Do not update**;
- the CLI command blocks on that dialog and never returns, because nobody is at the keyboard;
- meanwhile every inbound link is broken.

Measured both ways on a note with five inbound links: setting on, `rename` printed
`Renamed: old.md -> new.md` in under a second and all five links were rewritten with their
shapes intact. Setting off, the command hung and `unresolved` reported all five dead.

**Check before renaming**, and ask the app rather than the disk — `.obsidian/app.json` omits
the key at its default and lags the live setting:

```bash
obsidian eval code="app.vault.getConfig('alwaysUpdateLinks')"   # => true or false
```

If it's `false`, say so before renaming rather than firing and hoping. The user can enable
*Settings → Files and links → Automatically update internal links*, or answer the dialog with
**Always update**, which completes the rename and sets the preference. Repairing links by
hand is a last resort — it means reproducing every link shape yourself when the app will do
it correctly.

**If a `move` or `rename` doesn't return within a few seconds, don't retry it.** The rename
has almost certainly already happened and a dialog is waiting; retrying acts on a vault
that's already half-changed. Say so and ask the user to answer the prompt.

Afterwards, verify instead of assuming — it's one command and it catches the whole failure
class:

```bash
obsidian unresolved                        # expect no new dead links
obsidian backlinks file="New Name" total   # expect the count you saw before
```

## Ask the graph about links, not grep

`backlinks`, `links`, `orphans`, `unresolved` and `deadends` read the graph Obsidian has
*resolved*, which is not the set of strings in the files. Against a note with five genuine
inbound links, grepping for the literal `[[Name]]` found two, missed three, and returned a
file that wasn't a link at all:

| Inbound reference       | In the file           | `backlinks`       | naive grep     |
| ----------------------- | --------------------- | ----------------- | -------------- |
| plain                   | `[[Name]]`            | found             | found          |
| display text            | `[[Name\|shorthand]]` | found             | missed         |
| different case          | `[[name]]`            | found             | missed         |
| heading ref             | `[[Name#Section]]`    | found             | missed         |
| embed                   | `![[Name]]`           | found             | found          |
| example in a code fence | ` ``` ` block         | correctly ignored | false positive |

Block refs (`^block-id`) are another shape. A grep pattern chasing all of them grows long and
still misses some, and the failure is a confident wrong answer rather than an obvious error.
Grep remains the right tool for finding *text*.

**An alias is not a link target.** If a note has the alias `FN`, a bare `[[FN]]` does not
resolve — it lands in `unresolved`. Obsidian's autocomplete writes `[[Real Name|FN]]`, which
is why alias links normally work. So when `unresolved` lists something matching an existing
note's alias, the fix is that one link, not the index.

## `search:context` repeats lines

It streams, and the same line comes back more than once — in one run, a single line of a
single file appeared four times. Deduplicate before counting anything, or use
`search query="..." total` for counts and keep `search:context` for reading matches.

## There is no in-place edit

The only write primitives are `create`, `append` and `prepend`. Editing existing note text —
fixing a typo, rewriting a section — is a job for ordinary file tools against the file:

```bash
obsidian vault info=path           # absolute vault root
obsidian file file="Some Note"     # prints `path  Folder/Some Note.md`, vault-relative
```

Join those and edit directly; Obsidian picks up external changes. Don't rebuild a note with
`create ... overwrite` to change one word. Editing content in place is safe — it's renames,
moves and deletes that must go through the app, because those change the link graph.

For content passed *to* the CLI, `\n` and `\t` work inside a shell argument, which is fine
for a one-liner (`obsidian daily:append content="- Shipped the parser fix"`). For anything
with code fences, quotes or backticks, write the file with normal tools instead of fighting
the quoting.

`eval` runs arbitrary JavaScript in the user's app. The read-only config check above is a
reasonable use; reaching for it to do what a real command already does is not.

## Describing the vault honestly

Report what the commands return *now*. Counts, tag lists, which notes were orphaned, how the
vault is organised — all of it goes stale the moment the user edits something, and stating it
as a standing fact is how this skill's predecessor went wrong. Run the command again; if
you're carrying something over from earlier in the conversation, say when you looked.

`orphans` and `unresolved` answer questions — they are not a to-do list. Offering to sweep
them unprompted turns someone's notes into a maintenance project they didn't ask for. The
vault is someone's thinking, not a database to be normalised.
