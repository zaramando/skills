# Troubleshooting

One branch per `error_type` in the receipt. Find the branch, act, and stop.

## `MissingDependency`

The receipt's `missing` array names exactly which tools are absent.

```bash
brew install yt-dlp ffmpeg     # macOS; ffprobe ships inside ffmpeg
sudo apt install ffmpeg && pipx install yt-dlp    # Debian/Ubuntu
```

## ffmpeg is installed but will not run

Not an `error_type` — the receipt says the tool exists, and then every frame fails. Run `ffmpeg
-version` directly. A dyld error naming a missing `.dylib` means ffmpeg was linked against a
library version that a later upgrade replaced:

```
dyld: Library not loaded: /opt/homebrew/opt/x265/lib/libx265.215.dylib
```

The installed x265 now ships a different soname (`libx265.216.dylib`), so ffmpeg must be rebuilt
against it:

```bash
brew upgrade ffmpeg
```

Upgrade the ONE broken formula. A bare `brew upgrade` rebuilds everything outdated on the machine,
which is a far larger change than the problem calls for.

## `ResolveFailed`

yt-dlp could not turn the video into a stream url. The `detail` field carries yt-dlp's own last
line, which is usually specific. Common causes, in order of likelihood:

1. **yt-dlp is out of date.** YouTube changes its player often and yt-dlp ships fixes constantly. A
   version more than a few weeks old is the first suspect: `brew upgrade yt-dlp`.
2. **Private, deleted, or members-only.** Nothing works around this. Report and stop.
3. **Age-restricted or sign-in required.** yt-dlp can use browser cookies for this, but that means
   handling the user's YouTube session — do not. Report that the video requires sign-in.
4. **Geo-blocked.** Unavailable from this machine's region.
5. **Rate limiting / bot check.** Wait rather than retrying in a loop.

Unlike the transcript API, yt-dlp is generally NOT blocked by the same IP bans — a machine that
cannot fetch transcripts may still resolve streams fine. Do not assume one failure implies the other.

## `TimestampPastEnd`

The receipt reports `video_duration` and the offending values. Almost always a typo, or the wrong
video. Confirm with the user rather than clamping to the end — a frame from the last second is not
what they asked for.

## `BadTimestamp`

Accepted: `SS`, `MM:SS`, `HH:MM:SS`, with minutes and seconds under 60. `7:99` is rejected on
purpose. If the user meant 7 minutes 99 seconds, that is `8:39`; confirm rather than converting
silently.

## `BadTarget`

Not a YouTube URL or an 11-character id. Playlists and channels are not supported — ask for one
video.

## `status: partial` — individual frames failed

The `detail` on each failed frame is ffmpeg's last stderr line, truncated. If `detail` is a bare
`ffmpeg failed`, ffmpeg exited without a message, which in practice means the seek found no frame:

- The timestamp is inside the video but past its last frame (a duration rounded down).
- The stream url expired mid-run. These are signed and short-lived; a run interrupted for a long
  time then resumed will fail. Re-run — the cached frames are kept, so only the missing ones cost
  anything.

## Frames come back near-black

Not an error: the receipt flags it as a `warning` with `mean_luma` under 8. The timestamp landed on
a cut, a fade, or a transition. Retry one or two seconds later. Values around 20-50 are normal for a
dark slide or a dim room and are NOT blank.
