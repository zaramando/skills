# Step 4 — reading the table

Every row is a **candidate**. The receipt carries metadata about a video, never its contents.

## What each field is worth

| Field | Tells you | Does NOT tell you |
|-------|-----------|-------------------|
| `title` | the uploader's own framing — the strongest single signal | that the content matches it. Titles overstate |
| `channel` | a lot. An official product channel, a conference channel, or a named reviewer each carry different reliability | that this specific video is on-topic |
| `found_by_count` | how many independent phrasings surfaced it. High agreement is the best signal in the table | relevance. Three phrasings can agree on the wrong thing when they share a word |
| `duration` | genre. Under a minute is an ad; 5-15 minutes is a walkthrough; 40+ is a talk or a stream | whether the useful part is in it |
| `views` | reach, and weakly, usefulness | correctness or recency |
| `uploaded` | recency — but only in `--full` mode; it is `null` in flat mode | whether the product still looks like that |
| `best_rank` | YouTube's own ranking for its best query | much. Rank one is frequently generic |

## Agreement beats ranking, but is not proof

The table is sorted by `found_by_count` first. That ordering is a heuristic about *search
behaviour*, not about content: when three phrasings share a term, they can all surface the same
irrelevant video. Read the top row as "most consistently surfaced", never as "most likely correct".

## Report the noise floor out loud

Count the rows that are plainly off-topic and say the number. It is the most actionable thing in the
report: ten of sixteen generic rows means step 1 needs different vocabulary, and the user needs to
know that before choosing anything.

Never present the least-bad row as an answer. "None of these match, and here is what the noise
suggests" is a complete, useful result.

## Flat mode caveats

The default is `--flat-playlist`: about six times faster, and enough for a shortlist. Two costs:

- **`uploaded` is null.** No recency judgement is possible. Use `--full` when the product's age
  matters.
- **Titles arrive auto-translated.** YouTube localises titles in flat listings, so a Spanish video
  may appear with an English title. Quote it as returned rather than "correcting" it, and use
  `--full` when the exact original wording matters.

## What only opening the video can settle

Metadata cannot establish that a person appears, that a feature is demonstrated, or that a claim is
made. Those need `youtube-transcript` for the words or `youtube-screenshot` for the screen — and
even then, on-screen evidence the video itself declares (a caption, a nameplate, a UI label) is
worth far more than an inference from a face or a thumbnail.

Hand the id to the sibling skill only after the USER has chosen it.
