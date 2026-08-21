---
name: youtube-transcript
description: >
  Fetches the transcript of a YouTube video to disk as a timestamped Markdown file, and keeps a
  local cache so the same video is never fetched twice. The transcript never passes through the
  agent's context unless a task actually needs the words. Invoke explicitly:
  /youtube-transcript <url or video id>.
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# youtube-transcript

Gets the words out of a video and onto disk. It does NOT summarise, translate or analyse by
default — those are separate requests, and each one costs a cold read.

## Input contract

The target is usually a bare URL pasted into the message. It may also arrive wrapped as
`<target>...</target>` when passed programmatically — treat both identically.

Accepted shapes: `watch?v=`, `youtu.be/`, `/embed/`, `/shorts/`, `/live/`, or a bare 11-character
id. Playlist and channel URLs are NOT supported; ask which video. If the message contains more than
one video URL, ask which one — never fetch several on a guess. If none is present, ask and stop:
never guess a video id, and never fetch a video the user did not name.

## Tone

Factual and terse. Report what the receipt says and stop. Do not speculate about a video's content
before it has been read, do not soften an error into "it might have worked", and do not pad a
one-line result into a paragraph.

## Leading words

- **receipt** — the small JSON the script prints: status, path, language, duration, counts. This is
  what you read. It is a few hundred bytes regardless of how long the video is.
- **cache hit** — the transcript is already on disk, so no network call happens. The receipt says
  `cache_hit` and the run is free.
- **cold read** — opening the transcript file itself. A one-hour video is roughly 50k characters;
  a cold read spends all of it. Deliberate, never reflexive.

## Cache

Stateful as a **cache**, not as a workspace: it stores results, it does not track a goal.

```
transcripts/
  index.md          # rebuilt from the files present on every run. Never hand-edit
  <video_id>.md     # YAML front matter + the transcript, one paragraph per 30s
```

Re-hydration is automatic — the script checks for `<video_id>.md` before touching the network, so
re-running on the same video is a cache hit. Nothing else re-hydrates; there is no mission or
history to restore.

## Procedure

1. **Resolve the target.** Extract the URL or id from the user's message. If absent, ask and stop.
2. **Run the script.** From the directory where the `transcripts/` cache should live:
   ```bash
   python3 scripts/fetch_transcript.py "<target>"
   ```
   Useful flags: `--languages pt,en` (preference order, default `es,en`), `--force` (refetch over a
   cache hit), `--list-only` (report available languages, fetch nothing), `--out-dir <path>`,
   `--group-seconds N` (paragraph window, default 30).
3. **Read the receipt, not the file.** On success:
   ```json
   {
     "status": "success",
     "video_id": "UNzCG3lw6O0",
     "path": "transcripts/UNzCG3lw6O0.md",
     "title": "Building Great Agent Skills: The Missing Manual",
     "channel": "AI Engineer",
     "index": "transcripts/index.md",
     "language": "English (en)",
     "generated": true,
     "metadata_ok": true,
     "snippets": 412,
     "duration_seconds": 1274,
     "characters": 21840,
     "proxy": "none",
     "hint": "Transcript written to disk. Read the file only if the task needs the words."
   }
   ```
   On failure — this is the shape you will see most often:
   ```json
   {
     "status": "error",
     "error_type": "IpBlocked",
     "video_id": "UNzCG3lw6O0",
     "youtube_reachable": true,
     "caption_endpoint_only": true,
     "hint": "<the script's own remedy for this error_type — always actionable>"
   }
   ```
   Branch on `status`:
   - `success` / `cache_hit` → report it in the shape below. STOP here. If `metadata_ok` is false
     the transcript is intact but title and channel are empty — say so, do not present a nameless
     file as complete.
   - `error` → read `references/troubleshooting.md`, find the branch for that `error_type`, and
     report the cause and the remedy in one line each. NEVER retry in a loop. On a blocked fetch,
     read `caption_endpoint_only` first: when true, only captions are refused and
     `youtube-screenshot` still works on that video.
4. **Cold read only on demand.** If — and only if — the user asked for something that needs the
   words (a summary, a quote, an answer about the content), read the file now. For what to do with
   it, see `references/downstream.md`.

## Output format

Report the receipt in prose, one block, then stop:

```markdown
`transcripts/UNzCG3lw6O0.md` — "Building Great Agent Skills: The Missing Manual"
English (en, auto-generated) · 21m 14s · 412 snippets · fetched just now

<one line: what you can ask for next>
```

On a cache hit say so explicitly — the user should know no network call happened. On an error:

```markdown
No transcript — `IpBlocked`. YouTube refused the request from this machine's IP.
Fix: run it from a residential connection, or set a proxy (see troubleshooting.md). Not a retry.
```

Never paste transcript content into the report, and never report a fetch as successful when the
receipt says otherwise.

## First run

The script needs one dependency:

```bash
python3 -m pip install --user youtube-transcript-api
```

If the receipt is `MissingDependency`, run that and retry once. If pip refuses with
`externally-managed-environment`, see `references/troubleshooting.md`.

## References

- `references/troubleshooting.md` — read when a receipt has `status: error`. One branch per
  `error_type`, including the IP-ban workaround, which is the most common failure by far.
- `references/downstream.md` — read only at step 4, when the user asked for something that needs the
  transcript's content.

## CRITICAL REMINDERS

- NEVER pass `--stdout`, and never `cat` the transcript, to "check that it worked". The receipt is
  the check. That flag exists for piping into another program, not for reading.
- A cold read is a deliberate act with a real cost. NEVER do one in the same turn as the fetch
  unless the user asked for the content.
- `TranscriptsDisabled` and `AgeRestricted` are permanent states. NEVER retry them.
- `IpBlocked` and `RequestBlocked` report 429, but do NOT promise the user it will clear: measured
  here, it survived 80 minutes of spaced retries. Offer at most one or two bounded attempts, then
  point at a different network or a proxy. NEVER a tight loop.
- Check `caption_endpoint_only` first: when true, `youtube-screenshot` still works on that video and
  the user should be told so.
- `index.md` is generated. Edits to it are erased on the next run.
- Transcripts are the creator's work. Summarise and quote briefly with attribution; never reproduce
  a full transcript into chat, a document, or anywhere it would substitute for the video.
