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

Drives two sibling skills' scripts and keeps the grid: `youtube-search` finds a source,
`youtube-screenshot` captures frames, and this one assigns each frame to a step.

Call those scripts with **Bash, never the `Skill` tool**. Both siblings set
`disable-model-invocation: true`, so invoking them by name from inside this procedure fails with
`Unknown skill` — the flag exists to keep them out of ambient context, and it blocks programmatic
invocation too. Paths are relative to this skill's directory:

```
../youtube-search/scripts/search_youtube.py       # queries -> ranked candidates, picks nothing
../youtube-screenshot/scripts/capture_frames.py   # id + timestamps -> PNGs, optional contact sheet
```

Their judgment lives HERE, not there: `references/sourcing.md` carries brand-not-category and
walkthrough-vs-spot for this skill's purposes, so you do not need the siblings' own references.

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

`<ws>` belongs to the investigation, NOT to this skill — put it in the user's own project and pass
`--dir <ws>` explicitly on every call. The script defaults to `./benchmark`, which silently picks up
whatever workspace happens to sit in the current directory; naming it is how two investigations stay
apart.

```
<ws>/
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
3. **Search.** Read `references/sourcing.md` first, every time. Two or more BRAND phrasings, never
   a category query. `--min-seconds 120` drops the ad spots:
   ```bash
   python3 ../youtube-search/scripts/search_youtube.py --min-seconds 120 \
     "Yape negocios prestamo como solicitar" "Yape credito paso a paso 2025"
   ```
4. **Judge the candidates — tells first, verdict last.** The script ranks but never picks. For each
   candidate you seriously consider, emit these three in order and never the reverse:
   `<tells>` what the title, channel and duration indicate · `<audience>` which side of the
   transaction and which country · `<kind>` exactly one of `walkthrough` / `spot` / `mixed`.
   The tells in `references/sourcing.md` decide the kind. A kind chosen first and justified
   afterwards is how a brand spot enters the grid as evidence.
5. **Record the source verdict**, including what it does NOT show:
   ```bash
   python3 scripts/benchmark.py --dir <ws> source --competitor yape --id T4QIfNC8xgM \
     --kind walkthrough --shows "flujo in-app completo"
   ```
6. **Capture a survey.** Coarse timestamps across the whole video, tiled into one sheet:
   ```bash
   python3 ../youtube-screenshot/scripts/capture_frames.py T4QIfNC8xgM \
     --contact-sheet --out-dir <ws>/screenshots/T4QIfNC8xgM 0:10 0:30 1:00 1:30 2:00 2:30 3:00
   ```
7. **Map frames to spine steps.** Open the contact sheet ONCE. Decide which spine step each frame
   belongs to, and which steps no frame covers.
8. **Re-capture precisely** — only at the timestamps you actually identified in step 7, never on
   spec.
9. **Classify every cell — observe, place, then rule.** This is where the skill's whole distinction
   is won or lost, so the order is fixed. For each cell you looked at, emit:
   - `<observed>` what is actually on the frame — labels, amounts, field types, controls. When no
     frame covers the cell, what the source showed at that point in the flow instead.
   - `<slot>` the spine step it satisfies, or none.
   - `<verdict>` exactly one of `screen` · `not-in-product` · `not-in-source`.

   The order IS the safeguard. `not-in-product` is only available when `<observed>` records the
   surrounding flow stepping past that moment without it. If the source simply never got there,
   the verdict is `not-in-source`. A verdict written before its observation is a guess wearing a
   finding's clothes. Then record it — never leave a cell open after looking:
   ```bash
   python3 scripts/benchmark.py --dir <ws> add --competitor yape --step simulador \
     --file <ws>/screenshots/T4QIfNC8xgM/00-03-00.png --source T4QIfNC8xgM --at 00:03:00
   python3 scripts/benchmark.py --dir <ws> gap --competitor mibanco --step cuotas \
     --cause not-in-product --note "elige día de pago mensual, no número de cuotas"
   ```
10. **Compare.** `sheet --step <name>` or `--all` tiles the competitors for a step into one image.
    Open the SHEET, not the individual screens. Append what you see to `findings.md` — read
    `references/comparing.md` before writing.
11. **Report the grid and stop.** Re-read `status` before writing a single conclusion, so the
    coverage you report is the grid's, not your memory of it. Then, in order: the counts, the
    grid, and only last the `<conclusion>` — which may rest on `screen` and `not-in-product`
    cells and on nothing else. Stop there; do not propose a redesign.

## Worked example — one screen, two spine steps

The case that decides whether the grid is trustworthy. Bootstrap fixed the spine as
`... simulador · cuotas ...`, assuming that choosing an amount and choosing a number of instalments
are separate moments. Yape puts both on one screen.

Step 9 run properly, on the `cuotas` cell:

```
<observed>  frame 00:01:50 of KCDgyT0Glqw — "¿Cuánto necesitas?" header, monto input at
            S/2,000 over a S/100–S/6,470 range, and below it four instalment chips 18/12/9/6
<slot>      cuotas — the chips ARE the instalment choice, sharing a screen with simulador
<verdict>   screen
```

**The wrong verdict, and why it is reachable** — `cuotas` marked `not-in-product`, on the reasoning
that Yape has no separate instalments *screen*. Writing the verdict first makes it feel right: there
is no such screen. But `<observed>` records the chips on the frame, so the step is not absent —
it is merged. That cell would put "Yape no ofrece elección de cuotas" into a `<conclusion>`, which
is false. `not-in-product` means the step is absent, not that it shares a screen.

**The right record** — both cells hold a screen: the same file, the same timestamp, and the merge
noted.

```bash
python3 scripts/benchmark.py --dir <ws> add --competitor yape --step simulador \
  --file <ws>/screenshots/KCDgyT0Glqw/00-01-50.png --source KCDgyT0Glqw --at 00:01:50 \
  --note "¿Cuánto necesitas? monto S/2,000, rango S/100-S/6,470"
python3 scripts/benchmark.py --dir <ws> add --competitor yape --step cuotas \
  --file <ws>/screenshots/KCDgyT0Glqw/00-01-50.png --source KCDgyT0Glqw --at 00:01:50 \
  --note "Mismo screen que simulador: cuotas 18/12/9/6, sin navegación intermedia"
```

The merge is the finding, and it belongs in `findings.md` — Yape collapses two spine steps into one
screen, which is a real product difference and only became visible because the spine kept the steps
apart. A product that merges or reorders steps is a finding, never a reason to edit the spine; see
`references/flow-spine.md`.

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
`error_type: SheetFailed` is the opposite and must never be confused with it: the screens ARE on
disk and ffmpeg failed to render them. That is a broken tool, not missing evidence — never record a
gap for it.

Errors carry an `error_type` and a remedy:
```json
{"status": "error", "error_type": "UnknownStep", "value": "resumen",
 "known": ["entrada", "oferta", "simulador", "cuotas", "confirmacion", "desembolso"],
 "hint": "<the script's own remedy — always actionable>"}
```
The full set: `NoWorkspace`, `UnknownStep`, `UnknownCompetitor`, `UnknownCell`,
`AlreadyInitialised`, `BadSpec`, `FileNotFound`, `MissingDependency`, `SheetFailed`.

## Output format

```markdown
**<flow>** — 9/18 celdas con captura, 9 gaps, 0 sin examinar

| step | yape | mibanco | caja-arequipa |
|------|------|---------|---------------|
| simulador | ✓ | ✓ | ? sin fuente |
| cuotas | ✓ | ✗ n/a | ? sin fuente |

<conclusion>
**Diferencia de producto:** <what a `not-in-product` cell reveals, cited by competitor,
step, source id and timestamp>
</conclusion>

Pendiente — NO concluible:
**Hueco de evidencia:** <what `not-in-source` cells still need>
**Abierto:** <cells nobody has looked at>
```

The tag is not decoration: only `screen` and `not-in-product` cells may appear inside
`<conclusion>`. Everything a `not-in-source` or an open cell supports is pending work, and lives
outside it. Always separate the two kinds of gap. Collapsing them is the mistake this whole skill
exists to prevent.

## References

- `references/flow-spine.md` — read at Bootstrap step 2, or whenever a step name does not fit.
- `references/sourcing.md` — read at procedure step 3, every time, before searching.
  Brand-not-category, and walkthrough-vs-spot.
- `references/comparing.md` — read at procedure step 10, before writing anything into `findings.md`.

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
