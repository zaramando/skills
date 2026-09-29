# Big Picture moves — what to ask in each etapa and how it lands in the YAML

Read in full at step 3 of every run. The loop, the question kinds, the detectors, anti-completado,
"no sé" and the status rules are in `<storm-start>/references/socratic-protocol.md`; this file only
adds what is specific to Big Picture. Examples use the "biblioteca" domain of
`<storm-start>/assets/fixtures/biblioteca.eventstorm.yaml`.

## Etapa `exploración`

Goal: as many events as the stakeholder can name, in any order. Order comes later.

- **Opening.** Ask for a case, not a list: "Piensa en el último libro que salió, de punta a punta.
  ¿Qué pasó?" Each fact in the answer is a candidate event.
- **Several facts in one answer.** The protocol's block devolución: one numbered list, one recast
  per line, each item written as `propuesto` with that answer as `provenance.answer`. The
  stakeholder confirms or corrects each number; a "no" removes the item, a correction gets its own
  devolución. No new question until every number is answered.
- **Stall (tablero vacío).** Never offer a candidate. Anchor on an event already on the board:
  "¿Qué pasa justo antes de <evento>?", "¿Y justo después?", "¿Hay algo que pase aunque nadie haga
  nada?", "¿Qué pasa cuando esto sale mal?". With no event yet, re-ask the opening with another case.
- **"Dame varias".** Only when the stakeholder asks for it (the protocol defines the escape); the
  devolución is the same block as above.
- **Something going wrong.** When a fact is about something failing ("si no lo devuelve…", "se
  rechaza"), ask whether that is what happens when something goes wrong; on yes, write the event
  with `failure: true`. Which flow it breaks is NOT asked here and NOT assumed: it waits for
  `recorrido`.
- **Relevance.** When an answer is purely technical ("se guarda en la tabla"), ask: "¿Qué cambia
  para el negocio cuando pasa eso?" No business change → it is not an event; write nothing.
- **Scope edge.** An event outside `domain.scope.includes` → ask an `exclusión` question before
  writing it.
- **End of the etapa.** Ask: "¿Queda algo que pase en <alcance> y que no hayamos puesto?" A "no",
  "no por ahora" or "no sé" ends the etapa; set `session.stage: línea`.

### Recast to pasado de negocio

Keep the stakeholder's noun and verb; change only tense and voice — never add a word they did not
say. Confirm the recast in the devolución like any sticky.

| Heard | Problem | Move |
|-------|---------|------|
| "Se lo presto al socio" | present tense | → "Libro prestado", only if they said "libro"; otherwise "Prestado" and ask what |
| "Renovar el préstamo" | infinitive: an intention, not a fact | → "Préstamo renovado"; the original stays in `provenance.answer`, where Process finds the command |
| "Cada libro que vuelve queda registrado" | fine as is | → "Libro registrado", in their verb; NOT "Libro devuelto" unless they say "devuelto" |
| "El socio está suspendido" | a state, not a fact | Ask "¿Qué pasó para que quede suspendido?" — the event is in their answer, not in your guess |
| "Se cobra y se anota" | two verbs | Two events, two lines of the block devolución |

Never swap their word for a synonym you prefer ("copia" stays "copia"); a second word for the same
thing is the protocol's `sinónimo` detector.

## Etapa `línea`

Goal: every confirmed event placed on a timeline (`flows`). Events with `failure: true` are not
placed here: they wait for the camino de falla in `recorrido`.

- **One story, one flow.** Ask which events belong to the same story: "¿Prestar y devolver son la
  misma historia o dos?" Then, as its own `nombre-flujo` question, its name in their words.
  `kind: principal`; `steps` are ids in the order they gave.
- **Enforce the timeline.** For each unplaced event, ask a `secuencia` question against a placed
  one: "¿Esto pasa antes, después o al mismo tiempo que <evento>?"
- **"No sé" to a secuencia question.** Do not create a one-event flow to park it. Open a hotspot
  `desconocido`, `level: big-picture`, whose `refs` hold the event; it leaves the línea condition.
- **Only after a failure.** When the voice places an event only right after a `failure: true`
  event ("Pago vuelto a cobrar" after "Pago rebotado"), it cannot go in a principal flow. Ask the
  placement question of "Failure events" (recorrido) for that failure event now, and put both in
  the same camino de falla.
- **Gaps.** "¿Pasa algo entre <A> y <B>?" A gap is a question, never a sticky you fill in.
- **Lanes.** When after an event the story splits by area or by voice ("después, catálogo hace lo
  suyo"), each branch is its own `principal` flow with `lane: <área>` in their words, whose first
  step is the shared event.
- Every devolución here plays back the whole flow (timeline playback in SKILL.md).
- When no event is left for this etapa, set `session.stage: participantes`.

## Etapa `participantes`

Goal: who takes part and where information comes from. Triggers ("¿quién hace que pase?") are NOT
asked here: they belong to `storm-process`.

- **Actor.** "¿Quién se entera de esto?" / "¿A quién le importa que esto pasó?" → `actors`, named
  as they name the role. Place its id in `steps` just before the first event where it takes part.
- **External system.** "¿De dónde viene esta información?" If the answer is outside
  `domain.scope.includes` → `external_systems` (e.g. "Catálogo de la red de bibliotecas"), placed
  just before the event it feeds. If it is unclear whether it is inside, ask an `exclusión` question.
- **Actor kind.** Ask it; do not infer it: "¿Es una persona de acá, alguien de afuera, o un sistema
  que lo hace solo?" → `persona`, `externo` or `sistema`.
- Once every event of the flow was asked about, set `session.stage: recorrido`.

## Etapa `recorrido`

Goal: the flow survives being read in both directions, and its failure is on the board.

- **Backwards.** From the last event: "¿Qué tuvo que pasar antes para que esto pase?" A new event
  sends you back to `línea`.
- **Forwards.** From the first event: "¿Y después?" until the stakeholder says where it ends.
- **Pivot.** "¿Qué evento, cuando pasa, cambia todo lo que viene después?" Set `pivotal: true` on
  the event the voice names. If they say there is none, write their words in
  `none_said.pivot: {words, speaker}` on the flow.
- **Camino de falla.** The flow's **evento clave** is its pivotal event; with `none_said.pivot`, its
  last event. Ask: "¿Qué pasa cuando <evento clave> no llega a pasar, o sale mal?" Build the answer
  as a flow of its own, `kind: falla`, `failure_of: <the principal flow's id>`, with the same moves.
  Its name is asked like a principal flow's, as its own `nombre-flujo` question, and so is the name
  of every camino de falla another move creates; `kind` marks it as a failure, never a prefix in
  the name (the protocol's anti-completado, names). If the voice says there is no failure, write
  `none_said.failure`; if nobody knows, open a hotspot `desconocido`, `level: big-picture`, whose
  `refs` hold the flow.
- **Failure events.** For each `failure: true` event in no flow and no open hotspot — whether or not
  the evento clave question found it — ask, one event per question: "¿<evento> pasa cuando se rompe
  <flow name>, en otra historia, o no lo sabes?" A named flow → the event joins that flow's camino
  de falla (created if missing), followed by the events that only happen after it ("Pago vuelto a
  cobrar"), each confirmed in the timeline playback. "No sé" → a hotspot `desconocido`, `level:
  big-picture`, whose `refs` hold the event and its followers. Never attach one yourself.
- **Pain and opportunity.** Once per flow: "¿Qué parte de esta historia les cuesta más hoy?" Their
  answer is an `opportunities` entry in their words, with `refs` to the events it touches.
- **Walked.** When the moves above are asked for this flow, set its `walked.big-picture: true` and
  `session.stage: participantes`; step 4 moves on to the next principal flow not yet walked.

## Frontera candidata

Big Picture is where one word in two areas usually first appears, because two voices tell two
stories. Canonical case: Rosa (circulación) says "libro" for the copy a socio takes home; Tomás
(catálogo) says "libro" for the title, and "ejemplar" for each copy.

1. Apply the protocol's detector: two glossary entries (`context: circulación`,
   `context: catálogo`) and one hotspot `frontera-candidata`, `level: design`, `refs` to both entries.
2. Ask the `frontera` question with a case that separates them: "Si llega una segunda copia de un
   título que ya tienen, ¿es un libro más?" Write each voice's verdict in its own entry's
   `edge_cases`, with the same `case` text.
3. Do not ask whether it blocks: the protocol's "Severity" sets it (here, opposite verdicts →
   `bloqueante`). Tell the stakeholder it stays open for the design level.
4. Bounded contexts are NOT created here, and the frontera is not decided here: that is `storm-design`.
