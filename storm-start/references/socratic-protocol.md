# Socratic protocol — the single source

Every storm-* skill that talks to a stakeholder follows this file. Level skills point here; they never
restate it. The structural side (field names, enums) lives in
`<storm-start>/assets/eventstorm.schema.json`; `<storm-start>` is resolved by each SKILL.md.

## Speak plainly

The stakeholder hears plain language only. The internal vocabulary below, hotspot types, field
names, level and stage names stay in your notes, the YAML and hand-offs to other agents. This table
is the only list of plain terms: every question, devolución and report to the stakeholder uses the
right column.

| Internal | Say |
|----------|-----|
| Big Picture · Process · Design (the levels) | la línea de tiempo · los pasos y quién decide · las reglas y las áreas |
| abierto · cerrado (a level) | en curso · cerrado |
| evento · evento pivote | lo que pasó · el momento que cambia todo lo que sigue |
| flujo · camino de falla | historia · lo que pasa cuando sale mal |
| comando · actor | acción · quién la hace |
| policy (automática / manual) | reacción: "cada vez que…, entonces…" (sola / la decide alguien) |
| read model | lo que se mira para decidir |
| sistema externo | algo de afuera |
| agregado · invariante · bounded context | grupo de reglas · regla que no se rompe · área |
| hotspot · bloqueante / no-bloqueante | duda abierta · frena / no frena |
| desconocido | no se sabe |
| etapa, sticky, schema field names | never said |

## Internal vocabulary

- **devolución** — the playback that follows every answer (see the loop). Nothing is confirmed without one.
- **hipótesis-sin-autor** — something transcribed from registered material that no voice has
  adopted yet. It is not model. You never create one from your own head: see "Anti-completado".
- **pelear por los nombres** — treat every name as a claim to test with cases, not a label to accept.
- **deuda semántica** — a name in daily use that nobody can pin down with cases. Hotspot type `deuda-semántica`.
- **complejidad sin autor** — a rule that exists (usually in legacy code) but that no person decided.
  Hotspot type `complejidad-sin-autor`.
- **completar vs entender** — filling a section is not understanding it. An empty section with an
  honest hotspot beats a full section of guesses.
- **corte** — every model leaves things out on purpose. A corte is recorded as an exclusion, with who and why.

## The loop

One question, one answer, one devolución. Always in this order:

1. **Ask ONE question.** One thing to answer per message: a "¿y por qué?", a second clause or a
   second option to fill in is the next turn, after the devolución. A case that illustrates the
   question is fine as long as it asks nothing of its own. Pick its kind from the table below. Record it in
   `session.pending_questions.<slot>` before asking — the slot is your skill's level, or `start` for
   storm-start — so an interrupted session resumes on it.
2. **Listen.** Keep the stakeholder's exact words; they go to `provenance.answer`.
3. **Devolución.** In one message: (a) reformulate using THEIR words, not yours; (b) show the sticky
   you propose, as one line — kind, name, and the fields that matter; (c) ask whether that is right.
   An answer that carries several facts gets ONE devolución in block: a numbered list, one line per
   fact, and the stakeholder confirms or corrects each number.
4. **Write.** Only after an explicit yes: set `status: confirmado` and `speaker`. A partial yes
   ("casi", "más o menos") or a repetition of the answer is a no — ask what is missing, then a new
   devolución.

```
Pregunta:    Si un socio lee un libro en la sala y no lo saca, ¿eso es un préstamo?
Respuesta:   No, si no sale no es préstamo.
Devolución:  Entonces para ti hay préstamo solo cuando el libro sale del edificio.
             Lo anotaría así →  Término · préstamo (circulación) · "un libro afuera, con fecha de vuelta" · caso: leído en sala → no es
             ¿Es así?
```

Edge case — a partial yes and a second voice:

```
Rosa:        Sí, más o menos… está devuelto cuando lo registro.
Tomás:       No, está devuelto cuando cae en el buzón.
Wrong:       write "devuelto = registrado" as confirmado (Rosa answered first).
Right:       "más o menos" is a no → nothing is confirmed. Two voices disagree → the term goes to
             `disputado`, a hotspot `conflicto-entre-voces` records both positions in their words,
             and the next question is a case that separates them:
             "Si el socio deja el libro en el buzón el domingo a la noche, ¿cuándo quedó devuelto?"
```

**Escape "dame varias".** Only in Big Picture, only when the stakeholder asks for it: take a quick
dump of events as `propuesto`, then run ONE block devolución and have each item confirmed or
corrected individually. The dump ends the escape; the next question returns to one at a time.

**Repregunta limit.** When the same question gets no new answer, stop at the limit set in
`<storm-start>/references/level-contract.md` ("Repregunta limit") and record the gap as that
section says.

## Anti-completado

Every word in the model is a voice's word, or transcribed from registered material. You never
complete what a voice left open. These four happened in a real session; each is forbidden:

| Wrong | Right |
|-------|-------|
| Nobody named the domain, so you proposed a name taken from their answers | Ask the voice to name it ("¿Qué nombre le ponemos?"); a procedural answer from the voice is enough, yours is not |
| The voice said "rebota" and you filed it under `rechazo` (vs `error`, `demora`) yourself | Ask which it is, in their terms: "Cuando rebota, ¿se lo rechazaron, algo falló, o llegó tarde?" The mapping of their word to a schema category is itself a question |
| You added a noun the voice did not say ("Libro prestado" when they said "se lo presto") | Recasting THEIR verb to past tense is allowed and confirmed like any sticky ("pide un crédito" → "Crédito pedido"). A noun they did not say is asked for: "Prestado… ¿qué es lo que se prestó?" |
| You wrote what an absent or silent voice would say, from what the other voice said or from their earlier answers | Nothing is attributed to a voice that did not say it. Ask that voice, or leave the question in `pending_questions` with `to_speaker` |

The rule behind all four: **every mapping of a voice's words to a category of the schema — event vs
state, failure mode, actor kind, policy mode, a plazo as `delay` or as `time` (storm-process's
`references/process-grammar.md`, "Time"), invariant vs validación, severity reason — is
confirmed with the voice, and nothing is ever attributed to a voice that did not say it.**

Names follow the same rule. No `name` field is ever yours — not a domain, a flow, a reaction, a
thing looked at, a group of rules or an area: it is the voice's words, or the answer to a `nombre`
or `nombre-flujo` question. Each level's reference says where that question goes.

## "No sé" is an answer

When a voice does not know, do not guess and do not drop the rule it did give. Record the gap:

1. **Group first.** Look for an open hotspot on the same theme ("nadie sabe cómo opera cobranza").
   If one exists, ask the voice whether this is the same thing nobody knows; on yes, reuse it and
   add the element to its `refs`. One hotspot may hold many unknowns.
2. Otherwise open a hotspot `type: desconocido` (or a more specific type, e.g.
   `complejidad-sin-autor`) with the question in the voice's terms and their answer in
   `provenance.answer`.
3. Where a field needs the missing value, write `{desconocido: <hs-id>}` instead. Allowed in
   `commands[].actor`, `commands[].informed_by`, `commands[].failure_paths.<modo>`,
   `policies[].then`, `policies[].mode`, `events[].triggered_by`, `events[].failure_mode` and
   `aggregates[].bounded_context` (only toward an open `level: design` hotspot; storm-design's
   "Grouping" says which). The rest of the rule enters the model as the voice said it.

```
Rosa:        Cuando vence, se le avisa solo, por mail. Qué lo manda, no sé.
Write:       pol-avisar-vencido (when ev-prestamo-vencido, then cmd-avisar-socio, mode automática)
             cmd-avisar-socio.actor: {desconocido: hs-quien-avisa}
```

The level still closes while the hotspot is open and `no-bloqueante` (see "Severity").

## Severity

Set by rule, never asked. Do not ask a voice whether something blocks.

- ALWAYS `bloqueante`, and no voice can lower them: a `conflicto-entre-voces`, and a
  `frontera-candidata` whose cases got opposite verdicts (`es` in one term, `no-es` in the other).
- Everything else is `no-bloqueante` by default. A voice may raise it to `bloqueante` on its own
  initiative; record who in `raised_by`. A voice never lowers one.

`verify.py` enforces this (`hotspot-rules`). Tell the stakeholder what stays open and whether it
blocks; do not ask them to decide it.

## Hotspot level

A new hotspot takes `level` = `session.current_level`, the level in course — even when it is about
an element an earlier level wrote. The one exception is `frontera-candidata`: always `level:
design`. Never an earlier, closed level: an open blocking hotspot there would fail every later
`verify.py` run from a level that can no longer resolve it (`hotspot-rules`).

## Kinds of question

The kind is recorded in `session.pending_questions.<slot>.kind`. Ask for cases, never for definitions.

| Kind | Use when | Shape |
|------|----------|-------|
| `caso-límite` | Any new term or rule | "Si pasa <caso raro>, ¿sigue siendo un X?" |
| `invariante` | A term or aggregate needs its edges | "¿Qué haría que esto deje de ser un X?" |
| `metáfora` | A term could be a total or a state | "¿Es más como un historial o como una foto?" |
| `repregunta` | The answer contained "es lo mismo", "normalmente", "casi siempre", "depende" | Re-ask with a concrete case that separates the two readings |
| `secuencia` | Ordering events into a flow | "¿Qué pasa justo antes de <evento>?" — "¿y justo después?" is the next turn |
| `disparador` | An event has no trigger (Process and later) | "¿Quién o qué hace que esto pase?" |
| `exclusión` | Something was left out, or a scope edge appeared | "¿Esto lo dejamos fuera a propósito?" — the why is the next turn: "¿Por qué queda fuera?" |
| `frontera` | The same word showed up in two areas | "Cuando <voz A> dice X y <voz B> dice X, ¿hablan de lo mismo?" |
| `voces` | Unclear whose answer this is | "¿Esto lo dices tú o es como lo hace <área>?" |
| `alcance` | Opening a session | "¿Qué entra en esto?" — what stays out is an `exclusión`, its own turn |
| `lectura` | What someone needs to see or know before deciding (a read model) | "Justo antes de <acción>, ¿qué necesitas ver para decidirlo?" |
| `nombre` | A reaction, a thing looked at, a group of rules or an area is confirmed and has no name in the voice's words yet | "¿Cómo le llaman ustedes a esto?" |
| `nombre-flujo` | Events were grouped into one story and it has no name yet | "¿Cómo le llaman ustedes a esta historia?" |
| `alternativas` | A decision was just confirmed and its discarded options were not asked | "¿Qué otra opción había?" — its own turn, after the decision's devolución; "¿Por qué no esa?" is the next one, per option |
| `code_name` | Only when the stakeholder accepted fixing names for code | "¿En el código se llama igual o de otra forma?" |

BAD: "¿Qué es un préstamo?" — invites a dictionary definition that everyone agrees with and nobody uses.
GOOD: "Si un socio se lleva un libro y lo devuelve en la misma hora, ¿hubo préstamo?" — forces a verdict on a case.

## Language detectors

Run on every answer, before the devolución. Each detector has one mandatory action.

| You hear | Action |
|----------|--------|
| A second word for something already named ("copia" for "ejemplar") | Open a hotspot `sinónimo`. Do NOT merge the terms; synonyms are suspects, not aliases |
| "Es lo mismo" | Ask a `repregunta` with a case that would separate them. Only the case can settle it |
| The same word in two areas or from two voices | Two glossary entries (one per `context`) + a hotspot `frontera-candidata`, `level: design`, whose `refs` hold both. Record the separating case in BOTH entries' `edge_cases` with the same `case` text, so opposite verdicts are visible |
| A term nobody can settle with cases | Hotspot `deuda-semántica` |
| A rule found in code or documents that no person claims | Hotspot `complejidad-sin-autor`, status `hipótesis-sin-autor` |
| A metaphor (historial, foto, cuenta corriente, carrito…) | Record it in `glossary[].metaphor`; if two voices use different ones, hotspot `metáfora-en-disputa` |

## Status rules

| Status | Set when | Speaker |
|--------|----------|---------|
| `hipótesis-sin-autor` | It was transcribed from registered material (`provenance: {kind: fuente}`) | NONE — the schema rejects one |
| `propuesto` | A voice said it; the devolución is pending | the voice that said it |
| `confirmado` | That voice said yes to the devolución | same |
| `disputado` | Two voices contradict each other on it | the voice that holds it; an open hotspot MUST reference it |

- **The model is never yours.** You originate nothing — no event, actor, policy, read model, rule
  or name — not even as a hypothesis. An element enters from a voice, or transcribed from a
  registered source with its provenance; the schema rejects any other unauthored element. A hotspot
  a detector opens is not a claim but a question: its `speaker` is the voice whose words raised it.
- **Adoption.** A hypothesis becomes model only when a voice adopts it through a devolución: give
  it a `speaker` and move it to `propuesto`/`confirmado`. Until then it stays dotted on the board.
- **Glossary.** A plain yes confirms a term. A term carries a `decision` (authors, why, alternatives
  discarded) only when someone chose between meanings: a resolved `frontera-candidata` or
  `conflicto-entre-voces`, or a `code_name`.
- **code_name** is optional and always an explicit decision with an author. Terms themselves stay in
  the stakeholder's language, untranslated.

## Voices

- Every answer carries `speaker`. With a single voice, use the speaker marked `default: true`.
- When two voices contradict each other: open a hotspot `conflicto-entre-voces` with one `positions`
  entry per voice, in their own words, and mark the element `disputado`. NEITHER position wins, not
  by seniority, not by being recorded first, not by what you find more reasonable.
- The conflict ends only with a decision whose authors the voices accept (`speakers` lists every
  voice who took it), referenced in `resolved_by`.
- **Unifying needs one verdict per case.** A decision that resolves a `conflicto-entre-voces` or a
  `frontera-candidata` by unifying the senses is valid only when every separating case (the same
  `case` text in both glossary entries, or twice in one) now has the SAME verdict. Ask each such
  case again to each voice; a changed verdict gets its own devolución and replaces that voice's
  `edge_cases` entry. Opposite verdicts remain → the decision is not written and the hotspot stays
  open. `verify.py` enforces it (`unified-verdicts`).
- A decision records the alternatives discarded in `alternatives_rejected`, asked as an
  `alternativas` question. If a voice says there were none, keep their answer in
  `alternatives_asked`; never invent an alternative to fill the list.

## Existing material

Transcripts, documents and legacy code are a source of QUESTIONS, never of answers. What you
extract enters as `hipótesis-sin-autor` with `provenance: {kind: fuente, source: <path>}`, then
becomes a question to a voice. Register the material in `domain.sources` first.

## Closing criterion

Every ambiguity ends in exactly one of two places:

1. a **decision with an author** — who, why, alternatives discarded (or asked for); or
2. an **open, visible hotspot**, with its severity set by "Severity".

A level does not close with blocking hotspots open (`verify.py --close <level>` enforces it). Never
tell the stakeholder that the ambiguity is gone: asking reduces it, it does not exhaust it. Say what
was decided and what stays open.
