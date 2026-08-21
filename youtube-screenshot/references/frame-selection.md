# Choosing which frames to capture, and which to look at

Read at step 5, or whenever the user wants frames chosen rather than named.

## Timestamps come from the transcript, not from intuition

When the user describes a moment instead of naming one — "the slide about pruning", "where they
show the workspace" — do not guess. The sibling skill produces exactly what is needed:

1. `/youtube-transcript <url>` writes `transcripts/<video_id>.md`, one paragraph per 30 seconds,
   each stamped.
2. Search that file for the topic. The stamp on the matching paragraph is the timestamp.
3. Add 5-15 seconds. A speaker names a thing before the visual for it is fully on screen, and the
   paragraph stamp marks where the paragraph *started*.
4. Confirm the timestamp with the user before capturing if the video is long or the topic recurs.

This costs one cold read of the transcript and turns a guess into a citation.

## Capture more than you think, look at less

Capturing is cheap after resolve: roughly four seconds per frame, and frames are cached forever.
Looking is what costs — about 1.5k tokens per frame at 1080p.

So: capture a spread, then review them through the contact sheet rather than one by one.

```bash
python3 scripts/capture_frames.py "<url>" 4:10 4:25 4:40 4:55 --contact-sheet --columns 2
```

One look at the sheet tells you which single frame is worth opening at full size. Four frames
reviewed for the price of one.

## Bracket when the exact moment is uncertain

A slide transition, an animation, a terminal filling with output — one timestamp may land between
states. Capture three at ±10 seconds and pick from the contact sheet. Cheaper than three separate
runs, because they share one resolve.

## What kind of video is it

| Content | Approach |
|---------|----------|
| Slides / conference talk | One frame per slide change. The transcript's topic shifts are good proxies for those changes |
| Screencast / live coding | Bracket tightly — the screen changes constantly and a 30s paragraph stamp is far too coarse |
| Talking head, no visuals | Frames add little. Say so and suggest the transcript instead of capturing |
| Diagrams, whiteboard | Capture after the drawing is complete, not when it is first mentioned — often a minute later |

## What a single frame cannot tell you

A frame is one instant with no before or after. When reading one:

- Text mid-animation may be partially rendered. If a line looks truncated, it may not be.
- You cannot tell a still slide from one frame of a moving sequence.
- Nothing in the image says whether it is representative of the section around it.

When a claim rests on a frame, say which timestamp it came from, so the user can check it against
the video. Describe what is visible; do not infer what happened before or after it.
