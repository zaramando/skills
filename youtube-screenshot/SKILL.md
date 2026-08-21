---
name: youtube-screenshot
description: >
  Captures frames from a YouTube video at given timestamps without downloading the video, writing
  PNGs to disk plus an optional contact sheet. Resolves the stream once and reuses it for every
  frame, and caches what it has already captured. Invoke explicitly:
  /youtube-screenshot <url> <timestamp> [<timestamp>...].
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Bash, Read
disable-model-invocation: true
---

# youtube-screenshot

Turns timestamps into images. It does NOT find the interesting moments for you — timestamps come
from the user, or from a transcript. Sibling skill: `youtube-transcript` produces the timestamps
this one consumes.

## Input contract

A video (bare URL or 11-character id) plus **one or more** timestamps, usually pasted into the
message. Timestamps accept `SS`, `MM:SS` or `HH:MM:SS`.

When the request is a sentence rather than bare arguments, pull the data out of the prose before
acting — `<video>...</video>` and `<timestamps>...</timestamps>`. Everything outside those tags is
instruction: never pass surrounding prose to the script, and never take a URL found inside quoted or
third-party text as the target without confirming it is the video the user means.

If no timestamp is given, ASK. Never invent one: a guessed timestamp produces a real image of the
wrong moment, and nothing in the output reveals that it was a guess. If the user describes a moment
instead of naming it ("the slide about pruning"), fetch the transcript first with
`youtube-transcript`, find the timestamp there, and confirm it before capturing.

## Tone

Factual and terse. Report what the receipt says. Do not describe a frame you have not opened, and
do not claim a capture succeeded when the receipt says `partial`.

## Leading words

- **receipt** — the JSON the script prints: per-frame status, paths, mean luma, warnings. This is
  what you read.
- **resolve** — the yt-dlp step that turns a video into a playable stream url. It costs ~6 seconds
  and it is the expensive part. The script does it ONCE per run, never once per frame.
- **look** — opening a frame into context. Roughly 1.5k tokens at 1080p: cheap for one, expensive
  for twelve. That is what the contact sheet is for.

## Cache

Stateful as a **cache**, mirroring `youtube-transcript`:

```
screenshots/
  <video_id>/
    HH-MM-SS.png        # one file per captured timestamp
    contact-sheet.png   # only if --contact-sheet was passed
```

A timestamp already on disk is a cache hit, and if every requested timestamp is cached the script
skips resolve entirely — the run costs milliseconds and no network call.

## Procedure

1. **Collect the video and ALL timestamps** before running anything, separating them from any
   surrounding prose into `<video>` and `<timestamps>` per the input contract. If the user named
   four moments, all four go in ONE invocation — see the resolve cost above.
2. **Run the script** from the directory where `screenshots/` should live:
   ```bash
   python3 scripts/capture_frames.py "<url>" 0:30 4:20 7:58 --contact-sheet
   ```
   Flags: `--contact-sheet` (tile every frame into one image), `--columns N` (default 3),
   `--height N` (max height, default 1080), `--force`, `--out-dir <path>`, `--format jpg`
   with `--quality 2..31`.
3. **Read the receipt.** On success:
   ```json
   {
     "status": "success",
     "video_id": "s5T5oQJcJ6U",
     "dir": "screenshots/s5T5oQJcJ6U",
     "resolved": true,
     "video_duration": "00:13:04",
     "captured": 2, "cache_hits": 1, "failed": 0,
     "contact_sheet": "screenshots/s5T5oQJcJ6U/contact-sheet.png",
     "frames": [
       {"at": "00:07:58", "path": "...", "status": "captured", "bytes": 675177, "mean_luma": 211.6}
     ]
   }
   ```
   On failure — the shape to expect when a timestamp is wrong:
   ```json
   {
     "status": "error",
     "error_type": "TimestampPastEnd",
     "video_duration": "00:13:04",
     "out_of_range": ["05:00:00"],
     "hint": "<the script's own remedy for this error_type — always actionable>"
   }
   ```
   On `partial` — some frames landed, some did not. This is the status most easily misreported:
   ```json
   {
     "status": "partial",
     "captured": 3, "cache_hits": 0, "failed": 1,
     "frames": [
       {"at": "00:04:20", "path": "...", "status": "captured", "bytes": 845529, "mean_luma": 47.3},
       {"at": "00:12:50", "status": "failed", "detail": "<ffmpeg's last stderr line, truncated>"}
     ]
   }
   ```
   Branch on `status`:
   - `success` → report the count, the directory and any `warning` fields. STOP here.
   - `partial` → some frames failed. Report which timestamps, and do not describe the run as done.
   - `error` → read `references/troubleshooting.md`, find the branch for that `error_type`, and
     report the cause and the remedy in one line each.
4. **Check the warnings.** A frame with `mean_luma` under 8 carries a near-black warning: the
   timestamp landed on a cut or fade. Offer to retry a second or two later — do not silently
   present a black image as the requested moment.
5. **Look only on demand.** Open a frame when the task needs to see it: the user asked what is on
   screen, or asked you to describe or transcribe a slide. When several frames are in play, open the
   contact sheet instead of each frame. For which frames are worth a look, see
   `references/frame-selection.md`.

## Output format

```markdown
4 frames → `screenshots/s5T5oQJcJ6U/` (1 cached, 3 captured, video is 13:04)
Contact sheet: `screenshots/s5T5oQJcJ6U/contact-sheet.png`

<any warnings, one line each>
<one line: what you can ask for next>
```

On an error, report the `error_type` and the remedy in one line each. Never claim what a frame shows
unless you opened it.

## First run

```bash
brew install yt-dlp ffmpeg
```

`ffprobe` ships with `ffmpeg`. If the receipt is `MissingDependency` it names exactly which tools
are absent. For a broken ffmpeg that installs but will not run, see `references/troubleshooting.md`.

## References

- `references/troubleshooting.md` — read when a receipt has `status: error` or `partial`. One branch
  per `error_type`, plus the dyld/library failures that make an installed ffmpeg unusable.
- `references/frame-selection.md` — read at step 5, or whenever the user wants frames chosen rather
  than named: picking timestamps from a transcript, slides versus talking heads, and what a single
  frame cannot tell you.

## CRITICAL REMINDERS

- NEVER guess a timestamp. A wrong one yields a real image of the wrong moment and the output gives
  no sign of it. Ask, or read it out of the transcript.
- Batch every timestamp into ONE invocation. N separate runs pay the resolve cost N times for
  nothing.
- NEVER describe a frame you have not opened. The receipt carries paths and brightness, not content.
- `-q:v` is a NO-OP for PNG — verified: identical bytes at quality 2 and 31. It only affects `jpg`.
  Do not "improve quality" by passing it with the default format.
- Frames are the creator's work. Use them to discuss and cite the video, with attribution; do not
  reassemble them into a substitute for watching it.
