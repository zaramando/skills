# Canonical case — Swedish car insurance (V1 → V4)

Source: "Prompting 101", Hannah Moran & Christian Ryan, Anthropic. Code w/ Claude, San Francisco,
May 22 2025.

The task never changed across the four versions: *given a Swedish accident report form and a
hand-drawn collision sketch, determine which driver is at fault*. Only the prompt changed.

## V1 — total failure

A minimal zero-shot prompt: "analyze this report and say who is at fault", plus the raw documents.

The model concluded it was a **skiing accident on a Swedish street**. With no domain framing, it
resolved ambiguous Swedish terms toward winter sports. The answer was fluent, confident and
completely wrong — the failure mode this skill calls a **ski accident**.

Missing parts: 1, 2, 3, 5, 6, 7, 8, 10.

## V2 — role and tone

Added a system prompt: *you assist a claims adjuster on vehicular accidents, the reports are in
Swedish, stay factual, do not guess if the evidence is insufficient.*

The hallucination stopped immediately. The model correctly identified the document as a car accident
form and extracted checkbox marks — but it still could not say what any given checkbox *meant*, so
it would not assign fault.

Parts added: 1, 2.

## V3 — background data

Added the static structure of the form to the system prompt: the 17 numbered rows and the fixed
meaning of each (Row 1 "Parked / leaving parking", Row 12 "Turning right", and so on), for both
Vehicle A and Vehicle B. Plus a note on how humans actually fill these in: circles, scribbles,
smudges, stray marks — not clean X's.

The model started reading the checkboxes correctly. Because this metadata is identical on every
request, it also became the natural prompt-caching boundary.

Parts added: 3.

## V4 — reasoning order and parseable output

Forced the inspection sequence explicitly:

1. List the checkboxes marked by each driver, from the structured form.
2. Record those as verified facts.
3. Analyze the hand-drawn sketch.
4. Cross-check the sketch against the recorded facts and surface any contradiction.
5. Emit the determination wrapped in `<final_verdict>...</final_verdict>`.

Reading the structured form *before* the ambiguous sketch is what produced zero-shot accuracy —
the sketch gets interpreted against established facts instead of generating its own. The wrapper tag
let downstream code parse the verdict while ignoring the reasoning above it.

Parts added: 10, plus 9 (pre-filling the assistant turn with `<final_verdict>`).

## Why this case is the backbone of the skill

Each version added exactly one missing part and fixed exactly one class of failure. Nothing about
the model changed between V1 and V4. That is the claim the audit rests on: a bad output is a
gap in the prompt, and gaps are enumerable.
