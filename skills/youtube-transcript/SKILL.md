---
name: youtube-transcript
description: Fetches a verbatim YouTube transcript and video metadata (title, channel, published date) as JSON. The agent MUST invoke this skill before creating any note, summary, or artefact from a YouTube URL. Single video URLs only.
compatibility: Requires Python 3.9+. No external dependencies.
allowed-tools: Bash(python3 scripts/:*)
---

# YouTube Transcript

Extracts a verbatim transcript and basic metadata from a YouTube video URL and returns structured JSON.

## Usage

```bash
python3 scripts/youtube_transcript.py '<youtube_url>'
```

**Important:**
- **Always single-quote the URL.** YouTube URLs contain `?` and `=` which the shell will interpret as glob or assignment characters if unquoted. Wrap the URL in single quotes to prevent this.
- Do NOT redirect stderr. Do NOT append `2>/dev/null` or `2>&1` to the command. All skill output is printed to stdout as JSON.

The script **always** prints a single JSON object to stdout, even on failure.

## Agent Instructions

### Failure handling — THIS IS CRITICAL

**On ANY failure, STOP IMMEDIATELY.**

A failure is any of the following:
- The command exits with a non-zero exit code
- The output is empty or not valid JSON
- The JSON output contains an `error` field instead of a `transcript` field

When the skill fails, you MUST do exactly two things and nothing else:
1. Explain to the user **in plain language** what went wrong based on the error output
2. Ask the user what they want to do

**You MUST NOT do any of the following:**
- Retry the command
- Try alternative approaches or workarounds (e.g. web search, web_fetch, scraping)
- Suggest ways to get the information through other means
- Offer to create a note or summary from other sources
- Attempt to create any artefact without a successful transcript response

Your response must end with a question to the user. Do not suggest options. The user knows their environment and will tell you what to do.

### On success

1. **Always fetch before writing.** Never create a note or summary from a YouTube video without first running the script and receiving a successful JSON response (one that contains a `transcript` field, not an `error` field).

2. **Language warning.** If `is_english` is `false`, tell the user before proceeding: "The transcript is in `{language}` — no English transcript was available. Do you want me to continue?"

3. **The transcript is the source of truth.** All note content must be derived from the `transcript` field. Do not supplement with information from web searches or prior knowledge unless the user explicitly asks.

4. **Metadata is available.** Use `title`, `channel`, and `published_date` from the JSON when writing note headers, filenames, or frontmatter. Do not guess or infer these values.
