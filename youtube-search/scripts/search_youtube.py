#!/usr/bin/env python3
"""Search YouTube and return CANDIDATES. Never picks one.

Runs several query formulations in a single invocation and merges them by video
id, because the number of distinct queries that surfaced a video is a better
signal than any single query's ranking.

Exit codes:
  0  candidates found
  1  usage / bad input
  2  no results for any query
  3  search failed (blocked, yt-dlp error)
  5  missing dependency
"""

from __future__ import annotations  # PEP 604 syntax on Python 3.9

import argparse
import json
import shutil
import subprocess
import sys

FIELDS = ["id", "duration", "channel", "view_count", "upload_date", "title"]
SEPARATOR = "\x1f"  # unit separator: cannot occur in a title


def receipt(**kwargs) -> None:
    print(json.dumps(kwargs, ensure_ascii=False, indent=2))


def as_clock(total) -> str:
    try:
        total = int(total)
    except (TypeError, ValueError):
        return "?"
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:d}:{seconds:02d}"


def run_query(query: str, limit: int, flat: bool) -> tuple[list[dict], str]:
    command = ["yt-dlp", f"ytsearch{limit}:{query}", "--no-warnings",
               "--print", SEPARATOR.join(f"%({field})s" for field in FIELDS)]
    if flat:
        command.append("--flat-playlist")
    else:
        command.append("--skip-download")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return [], "yt-dlp timed out after 180s"
    if result.returncode != 0:
        return [], (result.stderr.strip().splitlines() or ["yt-dlp failed"])[-1][:300]

    found = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(SEPARATOR)
        if len(parts) != len(FIELDS):
            continue
        row = dict(zip(FIELDS, parts))
        if len(row["id"]) != 11:
            continue
        found.append(row)
    return found, ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search YouTube for candidate videos. Returns a list; never picks one.")
    parser.add_argument("queries", nargs="+",
                        help="two or more phrasings of the same need, quoted separately")
    parser.add_argument("--limit", type=int, default=8, help="results per query; default 8")
    parser.add_argument("--min-seconds", type=int, default=0,
                        help="drop anything shorter; 120 filters out ad spots")
    parser.add_argument("--max-seconds", type=int, default=0, help="drop anything longer; 0 = no cap")
    parser.add_argument("--full", action="store_true",
                        help="slower per-video extraction: real upload dates and untranslated titles")
    args = parser.parse_args()

    if not shutil.which("yt-dlp"):
        receipt(status="error", error_type="MissingDependency",
                hint="macOS: brew install yt-dlp")
        return 5

    merged: dict[str, dict] = {}
    errors = []
    for query in args.queries:
        rows, error = run_query(query, args.limit, not args.full)
        if error:
            errors.append({"query": query, "detail": error})
            continue
        for rank, row in enumerate(rows, start=1):
            entry = merged.setdefault(row["id"], {
                "id": row["id"],
                "title": row["title"],
                "channel": row["channel"],
                "duration": as_clock(row["duration"]),
                "seconds": int(row["duration"]) if row["duration"].isdigit() else 0,
                "views": int(row["view_count"]) if row["view_count"].isdigit() else None,
                "uploaded": None if row["upload_date"] in ("NA", "") else row["upload_date"],
                "found_by": [],
                "best_rank": rank,
            })
            entry["found_by"].append(query)
            entry["best_rank"] = min(entry["best_rank"], rank)

    if errors and not merged:
        receipt(status="error", error_type="SearchFailed", failures=errors,
                hint="Every query failed. See references/troubleshooting in the skill.")
        return 3

    candidates = list(merged.values())
    dropped = 0
    if args.min_seconds or args.max_seconds:
        kept = [c for c in candidates
                if c["seconds"] >= args.min_seconds
                and (not args.max_seconds or c["seconds"] <= args.max_seconds)]
        dropped = len(candidates) - len(kept)
        candidates = kept

    # More queries agreeing beats any single query's ranking.
    candidates.sort(key=lambda c: (-len(c["found_by"]), c["best_rank"]))
    for candidate in candidates:
        candidate["found_by_count"] = len(candidate["found_by"])

    if not candidates:
        receipt(status="empty", queries=args.queries, dropped_by_filter=dropped,
                hint="No candidates survived. Rephrase — a high noise floor means the query is "
                     "wrong, not that the video does not exist.")
        return 2

    receipt(status="success", queries=args.queries, mode="full" if args.full else "flat",
            candidates=candidates, count=len(candidates), dropped_by_filter=dropped,
            partial_failures=errors or None,
            hint="These are CANDIDATES, not matches. Present them to the user and STOP. "
                 "Never pick one and act on it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
