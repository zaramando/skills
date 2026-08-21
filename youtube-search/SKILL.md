---
name: youtube-search
description: >
  Searches YouTube from several phrasings of one need and returns a ranked table of CANDIDATE
  videos with id, duration, channel and view count. Its deliverable is the list — it never picks a
  video or acts on one. Feeds youtube-transcript and youtube-screenshot. Invoke explicitly:
  /youtube-search <what you are looking for>.
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Bash
disable-model-invocation: true
---

# youtube-search

Produces a shortlist for a human to choose from. It does NOT fetch, capture, summarise, or decide.
Sibling skills consume the id you choose: `youtube-transcript` for the words, `youtube-screenshot`
for frames.

## Input contract

A description of what the user is looking for, in prose. Extract the need before searching:

```
<need>an app demo showing how merchant credit works in Peru</need>
```

If the need is ambiguous in a way that changes the search, ASK before running anything — see
`references/query-craft.md` for the ambiguities that matter. "Credit for merchants" alone is the
canonical example: lending TO the merchant and the merchant's own book of customer debt are
different products, different vocabulary, and non-overlapping results.

## State

**Stateless, deliberately** — unlike its siblings, which both cache.

A transcript and a frame are immutable: the same video at the same timestamp yields the same bytes
forever, so caching them is free correctness. A search result is not. Ranking shifts, new videos
appear, channels are deleted. A cached shortlist would age into a confident lie, and the staleness
would be invisible in the output.

So every run searches live. Do NOT add a cache here by analogy with `youtube-transcript` or
`youtube-screenshot`. If a shortlist is worth keeping, the user saves the ids — the skill does not
decide that for them.

## Tone

Factual. Report what the table says. Never describe a video you have not opened, never assert that a
candidate contains what the user wants, and when nothing matches say so plainly instead of
presenting the least-bad row as an answer.

## Leading words

- **candidate** — a search hit. The word carries "unverified": a title and a channel are evidence
  about a video, never proof of its contents. Use this word in the report, never "match".
- **query spread** — several phrasings of one need, run together and merged by video id. A video
  surfaced by three different phrasings is a stronger signal than one ranked first by a single query.
- **noise floor** — the share of results that are generic or off-topic. A high noise floor means the
  QUERY is wrong, not that the video does not exist.

## Procedure

1. **Write the query spread.** Pull the need out of the prose into `<need>` first, per the input
   contract, then write two to four phrasings of THAT — varying vocabulary, not word order. Never
   one query: a single phrasing cannot tell a good hit from a lucky ranking. Read
   `references/query-craft.md` when the need involves a language other than English, a country, an
   industry term, or a product category that could mean two things.
2. **Run all of them in one invocation:**
   ```bash
   python3 scripts/search_youtube.py "phrasing one" "phrasing two" "phrasing three" --min-seconds 60
   ```
   Flags: `--limit N` (per query, default 8), `--min-seconds` (60-120 filters out ad spots),
   `--max-seconds`, `--full` (slower: real upload dates and untranslated titles).
3. **Read the receipt.** On success:
   ```json
   {
     "status": "success",
     "mode": "flat",
     "count": 16,
     "dropped_by_filter": 7,
     "candidates": [
       {"id": "QqDu_AehAJQ", "title": "...", "channel": "...", "duration": "9:20",
        "views": 206659, "uploaded": null, "found_by_count": 2, "best_rank": 1}
     ],
     "hint": "These are CANDIDATES, not matches..."
   }
   ```
   When nothing survives:
   ```json
   {"status": "empty", "queries": ["..."], "dropped_by_filter": 7,
    "hint": "<the script's own remedy — rephrase, do not conclude the video is absent>"}
   ```
   And when yt-dlp itself fails: `{"status": "error", "error_type": "SearchFailed", "failures": [...]}`
   → read `references/troubleshooting.md`.
4. **Assess the candidates.** Read `references/assessing-candidates.md`. Say for each plausible row
   WHY it is plausible and what is unverified. Name the noise floor out loud: if ten of sixteen rows
   are generic, the query was wrong and step 1 should be repeated with better vocabulary.
5. **Present and STOP.** Show the table, state your reading, and hand the choice to the user. This
   is the end of the skill.

## Output format

```markdown
16 candidatos de 3 formulaciones (7 descartados por duración).

| ✓ | id | dur | views | canal | título |
|---|----|-----|-------|-------|--------|
| 2 | QqDu_AehAJQ | 9:20 | 206k | Ivon Reyes | Cómo funciona TREINTA APP... |

**Plausibles:** <row> — <why, and what is still unverified>
**Ruido:** <n> de <total> son <what kind of noise>, lo que sugiere <what to change>

¿Cuál querés? Con el id te saco la transcripción o los frames.
```

The `✓` column is `found_by_count`: how many phrasings surfaced that video.

## First run

```bash
brew install yt-dlp
```

## References

- `references/query-craft.md` — read at step 1 whenever the need involves a non-English language, a
  country, an industry term, or a category that could mean two different products.
- `references/assessing-candidates.md` — read at step 4. What title, channel, duration and view
  count can and cannot tell you, and the flat-mode caveats.
- `references/troubleshooting.md` — read when the receipt is `error` or unexpectedly `empty`.

## CRITICAL REMINDERS

- The list IS the deliverable. NEVER pick a candidate and hand it to another skill yourself. The
  agent that can see the screenshot will grab row one without checking, and the user gets a valid
  image of the wrong video with nothing to reveal the substitution.
- NEVER call them matches. They are candidates until a human or an opened file says otherwise.
- NEVER run a single query. One phrasing cannot distinguish a good hit from a lucky ranking.
- An empty result means REPHRASE. It is not evidence that no such video exists, and must never be
  reported as if it were.
- In flat mode titles arrive auto-translated by YouTube, so a Spanish video may show an English
  title. Quote the title as returned, and use `--full` when the exact wording matters.
