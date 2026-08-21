#!/usr/bin/env python3
"""Capture one or more frames from a YouTube video, without downloading it.

Resolves the stream URL ONCE with yt-dlp (~6s), then seeks each timestamp with
ffmpeg (~4s each) against that single URL. Resolving per frame would more than
double the cost of every frame after the first.

Prints a JSON receipt. Never prints image data.

Exit codes:
  0  every requested frame is on disk
  1  usage / bad input
  2  some frames failed (partial success)
  3  could not resolve the video (blocked, private, geo/age restricted)
  5  missing dependency (yt-dlp or ffmpeg)
"""

from __future__ import annotations  # PEP 604 syntax on Python 3.9

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_ID = r"[0-9A-Za-z_-]{11}"
URL_PATTERNS = [
    rf"(?:youtube\.com/watch\?(?:.*&)?v=)({VIDEO_ID})",
    rf"(?:youtu\.be/)({VIDEO_ID})",
    rf"(?:youtube\.com/(?:embed|shorts|live|v)/)({VIDEO_ID})",
]
BLACK_THRESHOLD = 8.0  # mean luma below this is an effectively black frame


def receipt(**kwargs) -> None:
    print(json.dumps(kwargs, ensure_ascii=False, indent=2))


def extract_video_id(raw: str) -> str | None:
    raw = raw.strip()
    for pattern in URL_PATTERNS:
        match = re.search(pattern, raw)
        if match:
            return match.group(1)
    return raw if re.fullmatch(VIDEO_ID, raw) else None


def parse_timestamp(raw: str) -> int | None:
    """Accepts 90, 90s, 1:30, 01:30, 1:01:30. Returns seconds."""
    raw = raw.strip().lower().rstrip("s")
    if raw.isdigit():
        return int(raw)
    parts = raw.split(":")
    if not all(p.isdigit() for p in parts) or not 2 <= len(parts) <= 3:
        return None
    parts = [int(p) for p in parts]
    if len(parts) == 2:
        minutes, seconds = parts
        hours = 0
    else:
        hours, minutes, seconds = parts
    if minutes > 59 or seconds > 59:
        return None
    return hours * 3600 + minutes * 60 + seconds


def as_clock(total: int) -> str:
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def as_slug(total: int) -> str:
    return as_clock(total).replace(":", "-")


def mean_luma(path: Path) -> float | None:
    """Mean brightness via signalstats, to catch black or blank frames."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-f", "lavfi",
             "-i", f"movie={path},signalstats",
             "-show_entries", "frame_tags=lavfi.signalstats.YAVG",
             "-of", "csv=p=0"],
            capture_output=True, text=True, timeout=30,
        )
        first = result.stdout.strip().splitlines()
        return float(first[0]) if first else None
    except Exception:
        return None


def resolve_stream(video_url: str, height: int) -> tuple[str | None, int | None, str]:
    """One yt-dlp call for both the stream url and the duration.

    The duration is what lets a timestamp past the end of the video be rejected
    up front, instead of surfacing as a bare "ffmpeg failed" four seconds later.
    """
    selector = (
        f"bestvideo[ext=mp4][height<={height}]"
        f"/bestvideo[height<={height}]"
        f"/best[ext=mp4]/best"
    )
    try:
        result = subprocess.run(
            ["yt-dlp", "-f", selector, "--print", "duration", "--print", "urls",
             "--no-warnings", video_url],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return None, None, "yt-dlp timed out after 120s"
    if result.returncode != 0:
        return None, None, (result.stderr.strip().splitlines() or ["yt-dlp failed"])[-1][:300]

    duration, stream = None, None
    for line in result.stdout.strip().splitlines():
        if line.startswith("http") and stream is None:
            stream = line
        elif duration is None:
            try:
                duration = int(float(line))
            except ValueError:
                pass
    if stream is None:
        return None, None, "yt-dlp returned no stream url"
    return stream, duration, ""


def grab(stream_url: str, seconds: int, out_path: Path, quality: int) -> str:
    """Seek and write one frame. -ss before -i is frame-accurate and avoids
    fetching the whole file: ffmpeg range-requests from near the timestamp."""
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error",
               "-ss", as_clock(seconds), "-i", stream_url, "-frames:v", "1"]
    if out_path.suffix.lower() in {".jpg", ".jpeg"}:
        # -q:v only affects lossy encoders. It is a NO-OP for png.
        command += ["-q:v", str(quality)]
    command += ["-y", str(out_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return "ffmpeg timed out after 180s"
    if result.returncode != 0 or not out_path.exists():
        return (result.stderr.strip().splitlines() or ["ffmpeg failed"])[-1][:200]
    return ""


def build_contact_sheet(paths: list[Path], out_path: Path, columns: int) -> str:
    """Tile every frame into one image, so N frames cost one look, not N."""
    if not paths:
        return "no frames to tile"
    rows = (len(paths) + columns - 1) // columns
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    for path in paths:
        command += ["-i", str(path)]
    streams = "".join(f"[{i}:v]" for i in range(len(paths)))
    command += [
        "-filter_complex",
        f"{streams}concat=n={len(paths)}:v=1:a=0[c];"
        f"[c]scale=480:-1,tile={columns}x{rows}:padding=6:color=white[out]",
        "-map", "[out]", "-frames:v", "1", "-y", str(out_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    if result.returncode != 0 or not out_path.exists():
        return (result.stderr.strip().splitlines() or ["tile failed"])[-1][:200]
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture frames from a YouTube video.")
    parser.add_argument("target", nargs="?", help="YouTube URL or 11-character video id")
    parser.add_argument("timestamps", nargs="+", help="e.g. 7:58 1:04:20 480")
    parser.add_argument("--out-dir", default="screenshots")
    parser.add_argument("--height", type=int, default=1080, help="max frame height; default 1080")
    parser.add_argument("--format", choices=["png", "jpg"], default="png")
    parser.add_argument("--quality", type=int, default=2, help="jpg only, 2=best. Ignored for png")
    parser.add_argument("--force", action="store_true", help="recapture frames already on disk")
    parser.add_argument("--contact-sheet", action="store_true",
                        help="also tile every frame into one image")
    parser.add_argument("--columns", type=int, default=3, help="contact sheet columns; default 3")
    # YouTube ids use the base64url alphabet, so a legal id can start with "-".
    # argparse would parse it as flags, so lift it out of argv first.
    argv = list(sys.argv[1:])
    leading = None
    if argv and argv[0].startswith("-") and re.fullmatch(VIDEO_ID, argv[0]):
        leading = argv.pop(0)
    args = parser.parse_args(argv)
    if leading:
        args.target = leading
    if not args.target:
        receipt(status="error", error_type="BadTarget", target=None,
                hint="No video given. Pass a YouTube URL or an 11-character video id.")
        return 1

    missing = [tool for tool in ("yt-dlp", "ffmpeg", "ffprobe") if not shutil.which(tool)]
    if missing:
        receipt(status="error", error_type="MissingDependency", missing=missing,
                hint="macOS: brew install yt-dlp ffmpeg — ffprobe ships with ffmpeg.")
        return 5

    video_id = extract_video_id(args.target)
    if not video_id:
        receipt(status="error", error_type="BadTarget", target=args.target,
                hint="Not a recognisable YouTube URL or 11-character video id.")
        return 1

    wanted: list[int] = []
    for raw in args.timestamps:
        seconds = parse_timestamp(raw)
        if seconds is None:
            receipt(status="error", error_type="BadTimestamp", value=raw,
                    hint="Use SS, MM:SS or HH:MM:SS (minutes and seconds under 60).")
            return 1
        if seconds not in wanted:
            wanted.append(seconds)

    out_dir = Path(args.out_dir) / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    pending = [s for s in wanted
               if args.force or not (out_dir / f"{as_slug(s)}.{args.format}").exists()]

    stream_url, duration = None, None
    if pending:
        stream_url, duration, error = resolve_stream(
            f"https://www.youtube.com/watch?v={video_id}", args.height
        )
        if stream_url is None:
            receipt(status="error", error_type="ResolveFailed", video_id=video_id, detail=error,
                    hint="yt-dlp could not get a stream url. See references/troubleshooting.md — "
                         "usually private, geo-blocked, age-restricted, or yt-dlp is out of date.")
            return 3

        if duration is not None:
            past_end = [as_clock(s) for s in pending if s >= duration]
            if past_end:
                receipt(status="error", error_type="TimestampPastEnd", video_id=video_id,
                        video_duration=as_clock(duration), out_of_range=past_end,
                        hint=f"The video is {as_clock(duration)} long. Those timestamps are past "
                             f"the end — check for a typo, or that the right video was given.")
                return 1

    frames, failures = [], 0
    for seconds in wanted:
        path = out_dir / f"{as_slug(seconds)}.{args.format}"
        if seconds not in pending:
            frames.append({"at": as_clock(seconds), "path": str(path), "status": "cache_hit"})
            continue
        error = grab(stream_url, seconds, path, args.quality)
        if error:
            failures += 1
            frames.append({"at": as_clock(seconds), "status": "failed", "detail": error})
            continue
        entry = {"at": as_clock(seconds), "path": str(path), "status": "captured",
                 "bytes": path.stat().st_size}
        luma = mean_luma(path)
        if luma is not None:
            entry["mean_luma"] = round(luma, 1)
            if luma < BLACK_THRESHOLD:
                entry["warning"] = "near-black frame — likely a cut or fade, try a second later"
        frames.append(entry)

    sheet = None
    if args.contact_sheet:
        good = [Path(f["path"]) for f in frames if f.get("path") and f["status"] != "failed"]
        sheet_path = out_dir / f"contact-sheet.{args.format}"
        error = build_contact_sheet(good, sheet_path, args.columns)
        sheet = str(sheet_path) if not error else None
        if error:
            frames.append({"at": "contact-sheet", "status": "failed", "detail": error})

    captured = sum(1 for f in frames if f["status"] == "captured")
    cached = sum(1 for f in frames if f["status"] == "cache_hit")
    receipt(status="success" if not failures else "partial",
            video_id=video_id, dir=str(out_dir), resolved=stream_url is not None,
            video_duration=as_clock(duration) if duration is not None else None,
            captured=captured, cache_hits=cached, failed=failures,
            contact_sheet=sheet, frames=frames,
            hint="Frames are on disk. Open one only if the task needs to see it."
                 + (" Use the contact sheet to review many at once." if sheet else ""))
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
