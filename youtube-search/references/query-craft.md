# Step 1 — writing the query spread

A search is only as good as the vocabulary it uses. Most failed searches are not missing videos;
they are the wrong words, producing a high **noise floor**.

## Vary vocabulary, not word order

Rearranging the same words returns the same results. A spread must change the *terms*:

```
WEAK   "credito comercios peru app"
       "app credito comercios peru"
       "peru credito app comercios"        <- one query wearing three hats

STRONG "credito comercios peru app"
       "prestamo bodega peru aplicacion"   <- bodega, prestamo
       "financiamiento negocios peru app movil"  <- financiamiento, negocios, movil
```

Each phrasing should reach for a different word a real uploader might have typed in their title.

## Disambiguate BEFORE searching

Some needs split into two products that share a phrase. Searching the phrase returns a blend of both
and looks like a bad result set. Ask first.

| Ambiguous phrase | Reading A | Reading B |
|------------------|-----------|-----------|
| "credit for merchants" | lending TO the merchant: working capital, sales advance | the merchant's own book of customer debt — *fiado*, store credit |
| "delivery app" | the courier's app | the restaurant's order-management side |
| "billing system" | invoicing the customer | reconciling supplier bills |
| "school platform" | for teachers | for parents |

The tell: two readings have almost no shared vocabulary, so one spread cannot serve both.

## Search in the language the uploader used

Video titles are written in the creator's language, not the searcher's. A Peruvian bodega app demo
is titled in Spanish. Searching in English finds English-language explainers *about* the topic,
which is a different genre.

For a country-specific need, include the local term rather than the international one:

| International | Peru |
|---------------|------|
| small shop | bodega |
| ID number | DNI, RUC |
| loan | préstamo, crédito |
| municipal savings bank | caja municipal |

The same word can also mark the WRONG country. *Cédula* is Colombian or Venezuelan, not Peruvian;
a demo showing a Cédula field is not a Peruvian product no matter what the query asked for.

## For a product category, search BRANDS — not the category

The biggest single source of noise. Uploaders title videos with the product's NAME; almost nobody
titles a video with its category. Searching the category matches the generic business-content
cluster instead — dashboards, KPI explainers, ERP comparisons.

```
CATEGORY  "capital de trabajo para bodegas peru app"     -> ~13 of 16 rows generic noise
BRAND     "Prestamype como funciona prestamo"
          "Mibanco app prestamo negocio peru"
          "Yape negocios prestamo como solicitar"        -> ~5 of 18, with official channels
```

So when the need is a product category, spend one step naming the brands in that market first, and
build the spread from those names. If the brands are unknown, say so and ask — guessing a brand
list and searching it silently presents one vendor's ecosystem as if it were the market.

Watch for the **side of the transaction**. A brand can serve two audiences, and its videos will mix
them: Prestamype searches return mostly "how to INVEST in factoring", which is the lender's side,
not the merchant receiving the money. Group candidates by side before reporting them.

## Add the genre word

The need usually implies a video genre. Naming it cuts the noise floor sharply:

- `demo`, `tutorial`, `cómo funciona`, `paso a paso` → product walkthroughs
- `review`, `opinión`, `vale la pena` → evaluations
- `charla`, `conferencia`, `keynote` → talks
- `caso de éxito`, `testimonio` → customer stories

## Filter by duration instead of by reading titles

`--min-seconds 60` removes ad spots and shorts, which dominate commercial queries. `--min-seconds
300` keeps only substantial walkthroughs. This is cheaper and more reliable than judging length from
a title.

## When the spread returns noise

A high noise floor is a signal about the query, never a conclusion about the world:

1. The generic rows will show which broader category YouTube matched. Move away from those words.
2. Add the genre word.
3. Add the local term.
4. If the noise is a different country's product, add the country's own vocabulary rather than the
   country name — uploaders rarely put the country in the title, but they always use its words.

Report the rephrasing to the user. Silently re-searching hides that the first attempt failed.
