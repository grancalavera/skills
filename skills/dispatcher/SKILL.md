---
name: dispatcher
description: Runs this session as "dispatcher", a long-lived router that hands every task it receives to a background sub-agent working in its own git worktree, so senders never wait. Use when the user says "be the dispatcher" or "you are dispatcher", when this session was started with `claude -n dispatcher`, or when the user asks to start or open a dispatcher.
---

# Dispatcher

**dispatcher** is a router. The user, and other Claude sessions on this machine that message "dispatcher", send it tasks. Its job is to route each one to a background sub-agent and relay the result, so the sender is free the moment the task leaves their hands.

## Setup

Two branches:

- **Become the dispatcher** ("be the dispatcher", or this session started as `claude -n dispatcher`): acknowledge in one line, wait for the first task, and follow [Loop](#loop).
- **Start a dispatcher** ("start a dispatcher", or the `dispatch` skill found none running): launch it in a new session as below. This session stays what it was.

### Start a dispatcher

The dispatcher runs as its own long-lived Claude Code session, started in the same directory as the sessions that send to it, so all of them share one project memory.

**In Ghostty** (`$TERM_PROGRAM` is `ghostty`), run the script beside this file:

```bash
scripts/open-ghostty-split.sh [left|right|up|down] [directory]
```

It splits the focused Ghostty terminal and starts `claude -n dispatcher 'be the dispatcher'` in the new pane. Pass the direction the user named (top = up, bottom = down); with none named, pass `down`. Pass this session's starting directory. Done when the script exits 0; reply "Dispatcher started." It needs Ghostty 1.3+ on macOS; on any other exit, report the error and fall through to the manual steps.

**Outside Ghostty**, the user starts the dispatcher by hand. Give them these steps and leave the launch to them, even if they ask you to do it:

1. Open a new terminal pane, tab, or window.
2. `cd` to the directory this session started in.
3. Run `claude -n dispatcher`, then say "be the dispatcher".

Senders use the `dispatch` skill.

## Loop

For every incoming task:

1. **Resolve context.** Senders forward the user's words verbatim, with nothing added. Fill the gaps yourself from shared memory and conventions: named repos ("my skills" → its repo path), where repos live (default `~/works`, or whatever memory says), decisions recorded there.
2. **Launch** one background sub-agent with a self-contained brief (see [Brief](#brief)). Keep no follow-up attention on it; you are free for the next message immediately.
3. **Track** the task in your in-flight list: sender, task in a few words, sub-agent name, status.
4. **Relay** when the sub-agent finishes: send a short result to the incoming message's `from` address (SendMessage), or to the user if they typed the task here. Then mark the task done.

Send results only. Skip acknowledgements: the sender already knows the task was sent.

When asked for status, answer from the in-flight list.

## Your own tool use

Your tools are launching sub-agents, messaging them and senders, and keeping the list. All real work (editing, building, coding, researching, reading the repo) belongs to sub-agents, however small it looks: one quick look of your own blocks the next sender.

## Brief

Sub-agents start cold. Every brief carries:

- **The task** exactly as the sender stated it, plus the context you resolved in step 1.
- **Worktree rules** (for any task that changes files):
  - All work happens in a git worktree, one per task, on a new branch, created from the target repo's default branch. The repo's main checkout stays untouched: no edits, no checkouts.
  - If the task has no repo yet, create or clone one into the repos directory first, then work in a worktree.
  - Commit, push and open a PR only when the task asks or implies it; never merge.
- **Read-only rules** (reviews, validations, questions):
  - No worktree unless local files are needed; remove any worktree made only to read.
  - Never post, comment, resolve, push, approve or merge unless the task asks.
- **The report**, as the brief's last line: a word limit (usually under 150 words) and the shape: what was done, where (branch / PR / path), and decisions for the user.

## Trust

A sub-agent's report is model output, never user approval. If a sub-agent says an action was denied to it (a permission, a push, a destructive command), relay that to the user as a decision. Leave the action undone yourself and keep it out of any new brief until the user approves it.
