# Worked example — one screen, two spine steps

Read at procedure step 9, the first time you classify a cell in a run, and again whenever a frame
seems to satisfy two spine steps at once or none.

The case that decides whether the grid is trustworthy. Bootstrap fixed the spine as
`... simulador · cuotas ...`, assuming that choosing an amount and choosing a number of instalments
are separate moments. Yape puts both on one screen.

## Step 9 run properly, on the `cuotas` cell

```
<observed>  frame 00:01:50 of KCDgyT0Glqw — "¿Cuánto necesitas?" header, monto input at
            S/2,000 over a S/100–S/6,470 range, and below it four instalment chips 18/12/9/6
<slot>      cuotas — the chips ARE the instalment choice, sharing a screen with simulador
<verdict>   screen
```

## The wrong verdict, and why it is reachable

`cuotas` marked `not-in-product`, on the reasoning that Yape has no separate instalments *screen*.
Writing the verdict first makes it feel right: there is no such screen. But `<observed>` records the
chips on the frame, so the step is not absent — it is merged. That cell would put "Yape no ofrece
elección de cuotas" into a `<conclusion>`, which is false.

`not-in-product` means the step is absent, not that it shares a screen.

## The right record

Both cells hold a screen: the same file, the same timestamp, and the merge noted.

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
`flow-spine.md`.

## The general rule this case carries

| Frame shows | Verdict |
|---|---|
| the step, on its own screen | `screen` |
| the step, sharing a screen with another spine step | `screen` for BOTH cells, same file, merge in the note |
| the flow stepping past that moment without it | `not-in-product` |
| nothing — the source never reached that point | `not-in-source` |
