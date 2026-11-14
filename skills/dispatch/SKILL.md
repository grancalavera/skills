---
name: dispatch
description: Sends a task to the long-running "dispatcher" session so this session stays free. Use when the user says "dispatch <task>", "send this to the dispatcher", or asks whether the dispatcher is running.
---

# Dispatch

"Dispatch <task>" means: hand the task to the session named **dispatcher**, which routes it to a background sub-agent. Speed on this side is the point; aim for a round trip of a couple of seconds.

1. Send the user's words **verbatim** with SendMessage `to: "dispatcher"`. Forward them as typed: the dispatcher shares this project's memory and resolves context itself, so enriching, looking things up or checking first only adds delay.
2. Reply to the user in one short line at most ("Dispatched.").

If the send fails or `dispatcher` is missing from ListAgents, it isn't running. Say so in one line and offer to start it: a new session in this same directory, `claude -n dispatcher`, then "be the dispatcher" (the `dispatcher` skill).

Results arrive later as a message from dispatcher. Relay them to the user as they come, briefly.
