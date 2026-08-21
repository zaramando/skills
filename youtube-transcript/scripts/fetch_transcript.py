#!/usr/bin/env python3
"""Fetch a YouTube transcript to disk.

Prints a small JSON receipt to stdout. NEVER prints the transcript itself unless
--stdout is passed explicitly: the whole point is that the words land on disk
without passing through an agent's context window.

Exit codes:
  0  success (fetched or cache hit)
  1  usage / bad input
  2  no transcript available for this video
  3  blocked by YouTube (IP ban, age restriction, PO token required)
  4  video unavailable / invalid id
  5  missing dependency
"""

from __future__ import annotations  # PEP 604 syntax on Python 3.9

import argparse
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VIDEO_ID = r"[0-9A-Za-z_-]{11}"
URL_PATTERNS = [
    rf"(?:youtube\.com/watch\?(?:.*&)?v=)({VIDEO_ID})",
    rf"(?:youtu\.be/)({VIDEO_ID})",
    rf"(?:youtube\.com/(?:embed|shorts|live|v)/)({VIDEO_ID})",
]


def receipt(**kwargs) -> None:
    print(json.dumps(kwargs, ensure_ascii=False, indent=2))


def extract_video_id(raw: str) -> str | None:
    raw = raw.strip()
    for pattern in URL_PATTERNS:
        match = re.search(pattern, raw)
        if match:
            return match.group(1)
    if re.fullmatch(VIDEO_ID, raw):
        return raw
    return None


def _ssl_context():
    """Framework Pythons on macOS ship without a usable CA store, so the system
    default fails on ALL https. certifi arrives with requests, which
    youtube-transcript-api already requires — no new dependency."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def oembed(video_id):
    """Title/channel metadata. Returns None when the call itself failed."""
    query = urllib.parse.urlencode(
        {"url": "https://www.youtube.com/watch?v=" + video_id, "format": "json"}
    )
    try:
        with urllib.request.urlopen(
            "https://www.youtube.com/oembed?" + query, timeout=10, context=_ssl_context()
        ) as response:
            return json.load(response)
    except Exception:
        return None


def fetch_metadata(video_id: str) -> dict:
    """Best effort, but the failure is REPORTED. Silently returning empty strings
    hid a completely broken call for an entire release."""
    data = oembed(video_id)
    if data is None:
        return {"title": "", "channel": "", "ok": False}
    return {"title": data.get("title", ""), "channel": data.get("author_name", ""), "ok": True}


def group_snippets(snippets, window: int) -> list[tuple[int, str]]:
    """Merge snippets into paragraphs of `window` seconds, keyed by start time."""
    groups: list[tuple[int, list[str]]] = []
    for snippet in snippets:
        text = snippet.text.replace("\n", " ").strip()
        if not text:
            continue
        bucket = int(snippet.start // window) * window
        if groups and groups[-1][0] == bucket:
            groups[-1][1].append(text)
        else:
            groups.append((bucket, [text]))
    return [(bucket, " ".join(parts)) for bucket, parts in groups]


def stamp(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes:02d}:{secs:02d}]"


def render(video_id: str, transcript, meta: dict, window: int) -> str:
    groups = group_snippets(transcript.snippets, window)
    last = transcript.snippets[-1]
    total = int(last.start + last.duration)
    kind = "auto-generated" if transcript.is_generated else "manual"

    header = [
        "---",
        f"video_id: {video_id}",
        f"url: https://www.youtube.com/watch?v={video_id}",
        f"title: {json.dumps(meta['title'], ensure_ascii=False)}",
        f"channel: {json.dumps(meta['channel'], ensure_ascii=False)}",
        f"language: {transcript.language} ({transcript.language_code}, {kind})",
        f"duration_seconds: {total}",
        f"snippets: {len(transcript.snippets)}",
        f"group_seconds: {window}",
        f"fetched_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "---",
        "",
        f"# {meta['title'] or video_id}",
        "",
    ]
    body = [f"{stamp(bucket)} {text}" for bucket, text in groups]
    return "\n".join(header + body) + "\n"


def read_front_matter(path: Path) -> dict:
    fields: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        if handle.readline().strip() != "---":
            return fields
        for line in handle:
            if line.strip() == "---":
                break
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def rebuild_index(out_dir: Path) -> Path:
    """Rewrite index.md from the files present. Idempotent — no drift."""
    rows = []
    for path in sorted(out_dir.glob("*.md")):
        if path.name == "index.md":
            continue
        fields = read_front_matter(path)
        rows.append(
            "| {id} | {title} | {channel} | {lang} | {fetched} |".format(
                id=f"[{fields.get('video_id', path.stem)}]({path.name})",
                title=fields.get("title", "") or "—",
                channel=fields.get("channel", "") or "—",
                lang=fields.get("language", "") or "—",
                fetched=fields.get("fetched_at", "")[:10] or "—",
            )
        )
    index = out_dir / "index.md"
    index.write_text(
        "# Transcripts\n\n"
        "| Video | Title | Channel | Language | Fetched |\n"
        "| ----- | ----- | ------- | -------- | ------- |\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return index


def build_proxy_config():
    """Proxy settings come from the environment, never from argv.

    Credentials passed as flags leak into shell history and process listings.
    Set one of:
      YTT_PROXY_HTTP / YTT_PROXY_HTTPS   any HTTP(S) proxy url
      YTT_WEBSHARE_USER / YTT_WEBSHARE_PASS   a Webshare residential account
    """
    webshare_user = os.environ.get("YTT_WEBSHARE_USER")
    webshare_pass = os.environ.get("YTT_WEBSHARE_PASS")
    http_url = os.environ.get("YTT_PROXY_HTTP")
    https_url = os.environ.get("YTT_PROXY_HTTPS")

    if webshare_user or webshare_pass:
        if not (webshare_user and webshare_pass):
            raise ValueError("Set BOTH YTT_WEBSHARE_USER and YTT_WEBSHARE_PASS, or neither.")
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return WebshareProxyConfig(proxy_username=webshare_user, proxy_password=webshare_pass)

    if http_url or https_url:
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(http_url=http_url, https_url=https_url)

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch a YouTube transcript to disk.")
    parser.add_argument("target", nargs="?", help="YouTube URL or 11-character video id")
    parser.add_argument("--out-dir", default="transcripts", help="default: ./transcripts")
    parser.add_argument("--languages", default="es,en", help="comma-separated, in preference order")
    parser.add_argument("--group-seconds", type=int, default=30, help="paragraph window; default 30")
    parser.add_argument("--force", action="store_true", help="refetch even on a cache hit")
    parser.add_argument("--list-only", action="store_true", help="report available languages, fetch nothing")
    parser.add_argument("--stdout", action="store_true", help="also print the transcript (expensive)")
    # A legal YouTube id can start with "-"; argparse would read it as flags.
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

    video_id = extract_video_id(args.target)
    if not video_id:
        receipt(status="error", error_type="BadTarget",
                hint="Not a recognisable YouTube URL or 11-character video id.",
                target=args.target)
        return 1

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        import youtube_transcript_api as yta
    except ImportError:
        receipt(status="error", error_type="MissingDependency",
                hint="Run: python3 -m pip install --user youtube-transcript-api")
        return 5

    out_dir = Path(args.out_dir)
    target_path = out_dir / f"{video_id}.md"

    if target_path.exists() and not args.force and not args.list_only:
        fields = read_front_matter(target_path)
        receipt(status="cache_hit", video_id=video_id, path=str(target_path),
                title=fields.get("title", ""), language=fields.get("language", ""),
                snippets=int(fields.get("snippets", 0) or 0),
                duration_seconds=int(fields.get("duration_seconds", 0) or 0),
                fetched_at=fields.get("fetched_at", ""),
                hint="Already on disk. Pass --force to refetch.")
        return 0

    try:
        proxy_config = build_proxy_config()
    except ValueError as error:
        receipt(status="error", error_type="BadProxyConfig", hint=str(error))
        return 1
    api = YouTubeTranscriptApi(proxy_config=proxy_config)

    if args.list_only:
        try:
            available = [
                {"code": t.language_code, "name": t.language,
                 "generated": t.is_generated, "translatable": t.is_translatable}
                for t in api.list(video_id)
            ]
        except Exception as error:
            return report_failure(error, yta, video_id)
        receipt(status="listed", video_id=video_id, available=available)
        return 0

    try:
        transcript = api.fetch(
            video_id, languages=[code.strip() for code in args.languages.split(",") if code.strip()]
        )
    except Exception as error:
        return report_failure(error, yta, video_id, api=api)

    out_dir.mkdir(parents=True, exist_ok=True)
    meta = fetch_metadata(video_id)
    document = render(video_id, transcript, meta, args.group_seconds)
    target_path.write_text(document, encoding="utf-8")
    index_path = rebuild_index(out_dir)

    last = transcript.snippets[-1]
    receipt(status="success", video_id=video_id, path=str(target_path),
            index=str(index_path), title=meta["title"], channel=meta["channel"],
            language=f"{transcript.language} ({transcript.language_code})",
            generated=transcript.is_generated, snippets=len(transcript.snippets),
            duration_seconds=int(last.start + last.duration),
            characters=len(document), metadata_ok=meta["ok"],
            proxy="webshare" if os.environ.get("YTT_WEBSHARE_USER") else
                  "generic" if (os.environ.get("YTT_PROXY_HTTP") or os.environ.get("YTT_PROXY_HTTPS"))
                  else "none",
            hint="Transcript written to disk. Read the file only if the task needs the words.")

    if args.stdout:
        print(document)
    return 0


def youtube_reachable(video_id: str) -> bool:
    """Is YouTube itself reachable, or only the caption endpoint blocked?

    oEmbed is a plain metadata endpoint, unrelated to timedtext. If it answers
    while the transcript fetch is refused, the block is caption-specific and
    everything else about this video still works from here.
    """
    return oembed(video_id) is not None


def report_failure(error: Exception, yta, video_id: str, api=None) -> int:
    """Map a library exception to an actionable receipt and an exit code."""
    name = type(error).__name__

    blocked = (yta.RequestBlocked, yta.IpBlocked, yta.AgeRestricted, yta.PoTokenRequired)
    unavailable = (yta.VideoUnavailable, yta.InvalidVideoId, yta.VideoUnplayable)

    if isinstance(error, blocked):
        reachable = youtube_reachable(video_id)
        if reachable:
            hint = ("Only the CAPTION endpoint is blocked for this IP — YouTube itself answers "
                    "fine, so youtube-screenshot still works on this video. Usually rate limiting "
                    "that clears on its own. Wait, switch network, or set a proxy. Do not retry in "
                    "a loop. See references/troubleshooting.md.")
        else:
            hint = ("YouTube is not reachable at all from here, not just captions. Check the "
                    "network or VPN before blaming the skill. See references/troubleshooting.md.")
        receipt(status="error", error_type=name, video_id=video_id,
                youtube_reachable=reachable, caption_endpoint_only=reachable, hint=hint)
        return 3

    if isinstance(error, yta.NoTranscriptFound):
        available = []
        if api is not None:
            try:
                available = [
                    {"code": t.language_code, "generated": t.is_generated}
                    for t in api.list(video_id)
                ]
            except Exception:
                pass
        receipt(status="error", error_type=name, video_id=video_id, available=available,
                hint="None of the requested languages exist for this video. Retry with "
                     "--languages set to one of the codes in `available`.")
        return 2

    if isinstance(error, yta.TranscriptsDisabled):
        receipt(status="error", error_type=name, video_id=video_id,
                hint="The uploader disabled subtitles. There is nothing to fetch — do not retry.")
        return 2

    if isinstance(error, unavailable):
        receipt(status="error", error_type=name, video_id=video_id,
                hint="Video is private, deleted, or the id is wrong. Verify the URL.")
        return 4

    if "Proxy" in name or "SSL" in name:
        receipt(status="error", error_type=name, video_id=video_id,
                detail=str(error).splitlines()[0],
                hint="The proxy itself failed, before YouTube was reached. Check YTT_PROXY_HTTPS / "
                     "YTT_WEBSHARE_* — the transcript request never went out.")
        return 3

    receipt(status="error", error_type=name, video_id=video_id, detail=str(error).splitlines()[0],
            hint="Unexpected failure. See references/troubleshooting.md.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
