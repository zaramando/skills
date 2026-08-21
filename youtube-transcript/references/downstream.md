# After a cold read

Read this only at step 4 — when the user asked for something the receipt cannot answer, so the
transcript file has to come into context.

## Before you open the file

A one-hour talk is roughly 50k characters. Check the receipt's `duration_seconds` and `characters`
first, and pick the narrowest read that answers the question:

| The user wants | Read |
|----------------|------|
| A specific moment ("what did they say about X around 12 minutes") | The file, then work from the `[12:00]`-ish paragraphs. The timestamps are the index |
| A quote to cite | The file, locate the passage, quote briefly with its timestamp |
| A summary of the whole thing | The whole file. There is no shortcut — say so rather than skimming and guessing |
| Something about the video that is not its words (length, language, channel) | Nothing. It is already in the receipt |

Never skim a transcript and present the result as a full summary. An auto-generated transcript has
no speaker labels and no paragraph structure; a partial read produces confident, wrong claims about
what was said — and the user cannot tell from the output that you only read a third of it.

## Auto-generated transcripts are lossy

The receipt's `generated: true` means these words came from speech recognition, not a human. Expect:

- No speaker labels. In an interview or a panel, attribution is inference, not fact — say so when it
  matters, and never invent who said what.
- Proper nouns, library names and acronyms mangled. Names of people, products and APIs are the least
  reliable tokens in the file. Verify a name before repeating it as fact.
- No punctuation structure. Sentence boundaries in the grouped paragraphs are approximate.
- Timestamps mark when a phrase *started*, so a quote spanning a boundary carries the earlier stamp.

When a claim from the transcript is load-bearing, mark it as "the transcript says", not as "the
speaker said".

## Summarising

If the user asked for a summary, work from the structure the timestamps already give you:

1. Read the whole file.
2. Segment by topic shift, not by fixed time. Note the timestamp where each segment starts.
3. Write the summary as segments with their timestamps, so the user can jump to the source.
4. Keep quotes short and attributed to their timestamp. Summarise in your own words — do not stitch
   the transcript back together as a paraphrase of itself.

## Attribution

The transcript is the creator's work. Summarise it, quote briefly, and point at the video. Do not
reproduce it in full into chat, a document, or an artifact — the file on disk is for the user's own
reference, not a redistribution format.
