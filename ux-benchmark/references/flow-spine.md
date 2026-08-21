# Defining the flow spine

The spine is the ordered list of steps every competitor is measured against. It is decided once, at
Bootstrap, and changing it later invalidates every cell already recorded — so spend the time.

## Steps are user intentions, not screens

A step must be nameable without reference to any one product. If a step name only makes sense for
one competitor, it is a screen, not a step.

```
BAD    "pantalla morada de Yape"     -> one product's implementation
BAD    "tap en Créditos"             -> one product's navigation
GOOD   "entrada"                     -> how the user reaches the flow
GOOD   "simulador"                   -> where the user chooses an amount
```

The test: could a competitor satisfy this step with a completely different interface? If not,
rename it.

## Granularity

Six to ten steps is the usable range.

- **Too coarse** (3 steps) and every cell holds several screens, so nothing lines up for comparison.
- **Too fine** (20 steps) and the grid fills with `not-in-product`, which stops being informative
  because it only reflects your own over-splitting.

When unsure, start coarser. Splitting a step later is cheap if no cell for it is filled yet;
merging two steps means re-deciding every screen already assigned.

## Common spines

| Flow | Spine |
|------|-------|
| Requesting credit | entrada · oferta · simulador · cuotas · confirmacion · desembolso |
| Onboarding | descarga · registro · verificacion-identidad · datos · primer-uso |
| Checkout | carrito · direccion · pago · confirmacion · seguimiento |
| Money transfer | destinatario · monto · revision · autenticacion · comprobante |
| Support | acceso-ayuda · busqueda · articulo · escalamiento · contacto |

Adapt the names to the domain's own vocabulary, in the language the products use.

## Order matters, and is not always linear

The spine is ordered because the grid reads top to bottom as a journey. When a product reorders
steps — asking for identity before the amount, say — that is a **finding**, not a spine problem.
Keep the spine and note the reordering in `findings.md`.

Only rebuild the spine when a step turns out not to exist in any product at all.

## Naming

Lower case, no accents, hyphens instead of spaces — the script slugs names anyway, and the slug
becomes the filename. Keep names short: they are column headers in the grid.
