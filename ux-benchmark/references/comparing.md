# Reading the grid

Read at step 6, before writing anything into `findings.md`.

## Compare through the sheet, not the screens

`sheet --step <name>` tiles every competitor's screen for one step into a single image, left to
right in spec order. Open that. Opening each screen separately costs a look per competitor and gives
you no alignment — the whole point is seeing the same moment across products at once.

## The three cell states say different things

| Cell | Means | Belongs in a conclusion |
|------|-------|-------------------------|
| screen | you have evidence | yes |
| `not-in-product` | the product has no such step | **yes — this is the finding** |
| `not-in-source` | your video did not show it | no. It is a to-do |
| open | nobody looked | no. It is not even a to-do yet |

Most of the value in a benchmark sits in the `not-in-product` cells: they are where products
genuinely diverge. A competitor that picks a monthly payment day instead of a number of instalments
has made a different product decision, and the grid is what surfaced it.

Never let a `not-in-source` or an open cell drift into a sentence like "X doesn't have Y".

## What a screen can and cannot support

Can: what is on screen — labels, amounts, field types, controls, the number of inputs, the presence
of a simulator, what is disclosed before confirming.

Cannot: how long the step took, how many taps preceded it, what an error state looks like, whether
the flow felt hard, whether the screen is current. A screen from a 2023 walkthrough is evidence
about 2023.

When a claim rests on a screen, cite the competitor, the step, and the source id and timestamp. The
grid stores all three — use them.

## Comparable things to note per step

- **Input model** — keypad, chips, free text, dropdown, slider
- **Disclosure** — what cost, rate or total is visible before confirming, and what is behind a link
- **Choice offered** — amount, instalments, dates, or nothing
- **Field count** — how much the user must supply at this step
- **Confirmation weight** — a single tap, a code, a signature

Record these per step in `findings.md`, not per competitor. The step is the unit of comparison.

## Coverage before conclusions

Report coverage first, always: how many cells hold screens, how many are gaps of each kind, how many
are still open. A benchmark at 9 of 18 cells is a useful partial result and a misleading complete
one — the difference is entirely in whether you said so.
