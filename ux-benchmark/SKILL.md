---
name: ux-benchmark
description: >
  Builds a UX benchmark of one product flow across competitors, using screens captured from public
  YouTube walkthroughs. Maintains a workspace on disk — a coverage grid of competitors x flow steps,
  plus side-by-side comparison sheets per step. Accumulates across sessions. Invoke explicitly:
  /ux-benchmark <the flow you want to compare>.
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# ux-benchmark

Turns scattered screenshots into a comparison. It does NOT judge which product is better — it
assembles the evidence and makes the holes in that evidence visible.

Orchestrates three sibling skills: `youtube-search` finds a source, `youtube-screenshot` captures
frames, and this one assigns each frame to a step and keeps the grid.

## Input contract

The flow to compare and the competitors in scope:

```
<flow>solicitar un crédito de capital de trabajo</flow>
<competitors>Yape, Mibanco, Caja Arequipa</competitors>
```

On a first run, both are usually missing — go to Bootstrap and ask. On later runs they come from
the workspace, not from the message.

## Tone

Factual. Describe what a screen shows, never what the product does beyond it. Report coverage
honestly — an incomplete grid presented as a finished benchmark is the only real failure mode here.

## Leading words

- **flow spine** — the ordered list of steps every competitor is measured against. It is the
  benchmark's backbone: screens without a spine slot are not evidence, they are a pile.
- **gap** — a spine cell with no screen. It has two causes that must NEVER be merged:
  `not-in-product` (the product has no such step — a finding about the product) and
  `not-in-source` (the video did not show it — a finding about your evidence).
- **spot** — a source that is advertising: brand film, testimonial, animated explainer. It proves
  nothing about the screens. Its opposite is a **walkthrough**, which shows the real interface.

## Workspace

Stateful. Every run reads this back before doing anything; a fresh context remembers nothing.

```
benchmark/
  benchmark.json   # the state. Machine-owned
  mission.md       # the flow, WHY it matters, what "done" looks like. Human-owned
  coverage.md      # generated grid. NEVER hand-edit — regenerated on every write
  sources.md       # generated: one row per competitor, what its source actually shows
  findings.md      # observations per step, accumulated across runs. Human-owned
  notes.md         # rejected sources, gotchas, things to re-check
  screens/<competitor>/NN-step.png
  compare-NN-step.png   # side-by-side sheets, generated on demand
```

## Procedure

1. **Re-hydrate.** `python3 scripts/benchmark.py --dir <ws> status`. Read `mission.md` and
   `notes.md`. If the receipt is `NoWorkspace`, go to Bootstrap.
2. **Pick the next open cell.** The status receipt lists `open_cells` and `unsourced` competitors.
   Work one competitor at a time — a competitor half-sourced across three sessions is how grids rot.
3. **Source it.** Use `youtube-search` with BRAND queries, never category queries. Judge each
   candidate walkthrough-vs-spot before capturing anything — see `references/sourcing.md`. Record
   the verdict:
   ```bash
   python3 scripts/benchmark.py --dir <ws> source --competitor yape --id T4QIfNC8xgM \
     --kind walkthrough --shows "flujo in-app completo"
   ```
4. **Locate the steps.** Capture a survey with `youtube-screenshot --contact-sheet`, look at the
   sheet ONCE, and map frames to spine steps. Re-capture at precise timestamps only for the steps
   you actually identified.
5. **Record every cell.** A screen, or a gap with its cause. Never leave a cell open after looking:
   ```bash
   python3 scripts/benchmark.py --dir <ws> add --competitor yape --step simulador \
     --file screenshots/T4QIfNC8xgM/00-03-00.png --source T4QIfNC8xgM --at 00:03:00
   python3 scripts/benchmark.py --dir <ws> gap --competitor mibanco --step cuotas \
     --cause not-in-product --note "elige día de pago mensual, no número de cuotas"
   ```
6. **Compare.** `sheet --step <name>` or `--all` tiles the competitors for a step into one image.
   Open the SHEET, not the individual screens. Append what you see to `findings.md`.
7. **Report the grid and stop.** Coverage first, findings second. Say what is still open.

## Bootstrap (first run only)

1. Ask for the flow, the competitors, and WHY — what decision this feeds. Pull the answers out of
   the prose into `<flow>` and `<competitors>` per the input contract before using them; everything
   outside those tags is context, not data. Without the why, every later run optimises for a goal
   that was guessed.
2. Draft the flow spine and get it confirmed before capturing anything. See
   `references/flow-spine.md`. Changing the spine later invalidates the grid.
3. ```bash
   python3 scripts/benchmark.py --dir <ws> init --flow "..." \
     --steps "entrada,oferta,simulador,cuotas,confirmacion,desembolso" \
     --competitors "yape,mibanco,caja-arequipa"
   ```
4. Write the WHY into `mission.md`, then continue from step 2 of the procedure.

## Receipts

Success carries the grid:
```json
{"status": "success", "action": "status", "captured": 9, "gaps": 9, "open": 0, "total": 18,
 "grid": {"yape": {"simulador": "screen", "entrada": "not-in-source"}},
 "unsourced": [], "hint": "Open cells are unexamined, NOT absent features..."}
```
`status: empty` from `sheet` means no screens exist for that step yet — capture, do not conclude.

Errors carry an `error_type` and a remedy:
```json
{"status": "error", "error_type": "UnknownStep", "value": "resumen",
 "known": ["entrada", "oferta", "simulador", "cuotas", "confirmacion", "desembolso"],
 "hint": "<the script's own remedy — always actionable>"}
```
The full set: `NoWorkspace`, `UnknownStep`, `UnknownCompetitor`, `UnknownCell`,
`AlreadyInitialised`, `BadSpec`, `FileNotFound`, `MissingDependency`.

## Output format

```markdown
**<flow>** — 9/18 celdas con captura, 9 gaps, 0 sin examinar

| step | yape | mibanco | caja-arequipa |
|------|------|---------|---------------|
| simulador | ✓ | ✓ | ? sin fuente |
| cuotas | ✓ | ✗ n/a | ? sin fuente |

**Diferencia de producto:** <what a `not-in-product` cell reveals>
**Hueco de evidencia:** <what `not-in-source` cells still need>
**Abierto:** <cells nobody has looked at>
```

Always separate the two kinds of gap in the report. Collapsing them is the mistake this whole skill
exists to prevent.

## References

- `references/flow-spine.md` — read at Bootstrap step 2, or whenever a step name does not fit.
- `references/sourcing.md` — read at procedure step 3, every time. Brand-not-category, and
  walkthrough-vs-spot.
- `references/comparing.md` — read at step 6, before writing anything into `findings.md`.

## CRITICAL REMINDERS

- NEVER save a screen without a spine slot. A folder of unlabelled frames is not a benchmark, and
  turning one into a benchmark afterwards costs more than doing it right.
- NEVER merge `not-in-product` with `not-in-source`. One is a finding about the competitor, the
  other about your own evidence, and only the first belongs in a conclusion.
- An open cell means NOBODY LOOKED. It is not an absent feature and must never be reported as one.
- NEVER hand-edit `coverage.md` or `sources.md`. They are regenerated on every write.
- Official brand channels publish spots; third-party tutorial channels publish walkthroughs. For
  screens, prefer the tutorial — verified the hard way, and the opposite of what channel authority
  suggests.
- A frame is one instant. It cannot tell you what the flow felt like, how long it took, or what
  happened between two screens. Report screens, not experiences.
