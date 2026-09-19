---
name: random-excerpt
description: Pulls a random passage out of a text file (or a random file in a directory) and drops it into the conversation as a starting point for open-ended thinking. Use this whenever the user wants to wander through their own notes, journals, drafts, or codebase without a destination — phrases like "show me something random from", "surprise me with", "open my notes anywhere", "pick a random bit of", "let's see what's in there", "I want to explore my vault", "pull up a random daily note", or any request to be prompted by their own writing — including when they want the draw confined to one folder rather than a whole tree. Also use it when the user is stuck, wants a creative jolt, or asks for a conversation starter and has a file or folder of their own material to draw from.
compatibility: Requires Python 3.9+. No external dependencies.
allowed-tools: Bash(python3 scripts/:*)
---

# Random Excerpt

Seeks to a random byte in a text file and prints the readable passage around it. The
point is serendipity: to surface something the user forgot they wrote and see what it
sparks, rather than to answer a question.

## Usage

```bash
python3 scripts/random_excerpt.py <path> [--size 2000] [--count 1] [--depth N] [--seed N] [--weight-by-size]
```

`<path>` is either a file, or a directory — in which case a random text file under it
is chosen first (recursively; hidden files, `.git`, `node_modules` and similar noise are
skipped), then a random byte inside that file.

- `--size` — approximate excerpt size in bytes. The default of ~2000 is a few paragraphs:
  enough to be *about* something without crowding the conversation. Raise it when the
  user wants more to chew on, lower it for a quick jolt.
- `--count` — draw several passages at once, useful when the user asks for a few options
  or wants to look for connections between unrelated fragments.
- `--depth` — how many directory levels to descend. `--depth 1` draws only from files
  sitting directly in the named directory; `--depth 2` also takes its immediate
  subdirectories. No limit by default. See "Choosing the scope" below.
- `--seed` — reproduce an earlier draw. Only needed if the user wants the same passage back.
- `--weight-by-size` — in a directory, favour longer files. Off by default because equal
  weighting visits more distinct documents, which is usually what exploration wants.

The excerpt is trimmed outward-in to clean boundaries: paragraph breaks where the file
has them, line breaks otherwise, so code and unbroken prose still read sensibly. Each
excerpt is printed under a header giving the path and how far into the file it landed.

Binary files are refused when named directly and skipped when walking a directory.

## Agent instructions

### Getting a passage

Run the script and read what came back before saying anything. If the user named a file
or folder, use it; if they gently gestured at "my notes" without a path, ask which
directory rather than guessing, since a wrong folder wastes the surprise.

If the command fails, say what went wrong in plain terms — the wrong path, a binary file,
an empty directory — and ask what to try instead. Don't silently substitute a different
file or fall back to reading the whole thing.

### Choosing the scope

A directory the user names is often a container of unlike things rather than one
collection. The common case is an Obsidian vault whose top level holds the daily notes
while its subfolders hold projects, clippings, and archives: a recursive draw there
mostly returns things that aren't daily notes, which quietly defeats the request.

Recursion stays the default, because for a codebase or a folder of drafts the whole tree
usually *is* the collection. Reach for `--depth 1` when the user's words point at the
files in one folder rather than at everything beneath it:

- they name a kind of note — "my daily notes", "the journal", "this week's entries"
- they say "in this folder", "at the top level", "just what's in ~/vault"
- they've already seen a draw come back from a subfolder and steered away from it

Use the whole tree when they gesture at the collection itself — "my vault", "anywhere in
my notes", "somewhere in the repo" — or when the directory is flat anyway.

You can settle it by looking: `ls` the directory, or run the draw and see what path comes
back. If it's genuinely ambiguous and the folder does have subdirectories, one short
question beats a wasted draw — but don't interrogate someone who just said "surprise me".

When you narrowed the scope yourself, name it in a few words as you show the passage
("from the top level of the vault"). That's not throat-clearing: it tells the user what
the draw was sampling from, so if you guessed wrong they can widen it in three words
instead of wondering why their project notes never come up.

### What to do with it

Show the excerpt, then say **one** genuine thing about it, then stop and let the user
steer. That shape matters: the user came here to think out loud, and a wall of analysis
puts them in the position of responding to you instead of following their own thread.

A good opening reaction is specific to what's actually in the passage — an observation
about a tension in it, a question you'd genuinely want the answer to, a connection to
something else in the conversation. It is not a summary of what the passage says (the
user can read), and not a compliment about it.

**Example**

Excerpt (from a journal): *"...kept the meeting short because nobody had done the reading.
Third time. I think I'm the only one who believes this project is happening."*

Weak opening: "This is a journal entry about a meeting where the team was unprepared,
and it sounds like you were frustrated about the project's momentum."

Better opening: "Third time' is doing a lot of work in that sentence — you were counting.
Did that project end up happening?"

### When the passage is a dud

Sometimes the random landing is boilerplate, a config block, half a table, or a fragment
too thin to say anything about. Don't manufacture depth from nothing. Say it looks like a
dud and offer to draw again — the cheapness of another draw is the whole advantage of
this approach.

If the passage is code rather than prose, the same rules apply: react to what's
interesting about it — a decision baked into it, something that looks like it was hard to
get right — rather than reviewing it for defects, unless the user asks for that.

### Following the thread

Once the user picks up the thread, the excerpt has done its job. Follow where they go.
Reach for the wider file only when the conversation actually needs it — reading the
surrounding pages or the whole document is fine and often useful, just don't do it
pre-emptively to "understand the context" before reacting, since that turns a spark into
a research task.

When the user wants to keep wandering, draw again rather than mining the same passage.
Repeated draws from the same folder work well as a rhythm: read, react, move on.
