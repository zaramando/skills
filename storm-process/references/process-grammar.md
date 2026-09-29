# Process grammar — what to ask at each sticky, and how to write it

Read at storm-process's "Load the grammar" step, in every run. The loop, the question kinds, the
status rules, anti-completado, "no sé" and the detectors are in
`<storm-start>/references/socratic-protocol.md`; field names and id prefixes are in
`<storm-start>/assets/eventstorm.schema.json`. This file only maps Brandolini's Process Level
grammar onto both.

## The grammar

```
actor ─(mira)→ read model ─→ comando ─→ [sistema] ─→ evento ─→ policy ─→ comando siguiente
                                  └─ camino de falla ─→ evento de falla ─→ …
```

Walk it event by event along the chosen flow's `steps`. Each sticky below is one question, one
answer, one devolución. The "sistema" box is not written at this level: an aggregate belongs to
`storm-design`, and a sistema externo is an `external_systems` entry already found in Big Picture.

## Question per sticky

| Sticky | Ask (a case, never a definition) — one message per row | `kind` |
|--------|---------------------------------------------------------|--------|
| Trigger of an event | "¿Quién o qué hace que <evento> pase?" | `disparador` |
| Actor of a command | "¿Quién da esa orden? ¿Una persona o un sistema?" | `disparador` |
| Read model | "Justo antes de <comando>, ¿qué necesitas ver en pantalla o saber para decidirlo?" | `lectura` |
| Camino de falla · rechazo | "¿Qué pasa si <comando> se rechaza?" | `caso-límite` |
| Camino de falla · error | "¿Y si al <comando> algo falla?" | `caso-límite` |
| Camino de falla · demora | "¿Y si <comando> llega tarde?" | `caso-límite` |
| Policy | "Cada vez que <evento>, ¿qué tiene que pasar sí o sí?" | `secuencia` |
| Policy kind | "¿Eso lo hace el sistema solo, o una persona decide si se hace?" | `disparador` |
| "Siempre" in any answer | "¿Hubo alguna vez en que <evento> pasó y <reacción> no?" | `caso-límite` |
| Next command | "Después de <evento>, ¿qué pasa justo después?" | `secuencia` |

When the answer to one failure question describes a different way of failing ("si rebota en el
banco…" to the `rechazo` question), do not file it yourself: ask which one it is, in their terms —
the protocol's anti-completado. "No sé" to that question → "Known failure, unknown way" below.

## How each answer is written

Every element carries `status`, `speaker` and `provenance` per the protocol's status rules. The
fields specific to this level:

- **Command** — `commands[]`, id `cmd-`, name in the imperative ("Prestar libro"). `actor` points
  to an `actors` id; `results_in` lists the success event AND every failure event.
- **Evento de falla** — its own `events[]` entry, past tense ("Préstamo rechazado"), added to the
  command's `results_in` and set as `failure_paths.<rechazo|error|demora>`. A failure is never a
  note on the success event.
- **Known failure, unknown way** — the voice knows the failure event ("el pago rebota") but not
  whether it is a rechazo, an error or a demora. The event stays in the camino de falla with its
  trigger, and gets `failure_mode: {desconocido: <hs-id>}`. It is NOT set as any
  `failure_paths.<way>`: each of the three ways is still asked on its own.
- **No failure path** — if the voice answers that the command cannot be rejected, fail or arrive
  late, ask once for a case that would break it. If the answer holds, write
  `failure_paths.<way>: {no_aplica: true, words: "<their words>", speaker: <sp-id>}`.
- **Unknown** — "no sé" to any of these (actor, read model, a failure mode, a trigger, the policy's
  command or its mode): the protocol's "'No sé' is an answer", grouping included. The rest of the
  rule is written as the voice said it.
- **triggered_by** — every event in the scope gets one: the `cmd-` whose `results_in` contains it,
  the `ext-` that emits it on its own, `{time: "<when, in their words>"}` for what happens because
  time passes, or `{desconocido: <hs-id>}`. NEVER a `pol-`: a policy issues its `then` command, and
  that command produces the event. What happens because an order was never given ("si no lo
  devuelve a los 14 días") is a `time` trigger, not a `demora` of the command.
- **Policy** — `policies[]`, id `pol-`. `when` = the events, `then` = ONE command. Name it as the
  voice says it. `mode: automática` or `mode: manual`; a manual policy's `then` command has the
  deciding person as `actor`. When the voice says how long after the event it happens ("al día
  siguiente"), write `delay: {words, speaker}` in their words; it is not a `time` trigger.
- **System actor** — an automatic policy's `then` command still needs an `actor`. Ask who or what
  runs it; a system enters `actors` with `kind: sistema`, named as the voice names it. Nobody
  knows → `actor: {desconocido: <hs-id>}`.
- **Read model** — `read_models[]`, id `rm-`. `informs` = the command it supports; `built_from` =
  the events its data comes from, asked as a follow-up ("¿De dónde sale ese dato?"). "No sé" →
  `commands[].informed_by: {desconocido: <hs-id>}`. When the command's actor is unknown, do not
  ask: nobody present can say what that actor looks at, and the voice's guess would be attributed
  to someone else. Write `informed_by` pointing to the actor's hotspot.
- **Flow** — extend the chosen flow's `steps` in timeline order: `act-`, `rm-`, `cmd-`, `ev-`,
  `pol-`, next `cmd-`… Failure events and their follow-ups go in the flow's camino de falla
  (`kind: falla`, `failure_of` the chosen flow), created now if Big Picture left none. Do not add
  `agg-` ids at this level.
- **Flow walked** — once every event in a chosen flow and in its caminos de falla has
  `triggered_by`, and every command in them has its three `failure_paths`, set `walked.process:
  true` on the flow and on those caminos de falla.

## Example — the shape, on the "biblioteca" fixture

`<storm-start>/assets/fixtures/biblioteca.eventstorm.yaml`, flow `fl-prestamo` and its camino de
falla `fl-prestamo-rechazado`.

```
Pregunta:    ¿Qué pasa si prestar el libro se rechaza?
Respuesta:   (Rosa) Si tiene una multa sin pagar, el préstamo se rechaza y se va sin el libro.
Devolución:  Entonces cuando no se puede prestar, eso es algo que pasó: "préstamo rechazado",
             y el socio se va sin el libro.
             Lo anotaría así →  Evento · Préstamo rechazado · resultado de "Prestar libro" si se rechaza
             ¿Es así?
Write:       events += ev-prestamo-rechazado (confirmado, sp-rosa, triggered_by: [cmd-prestar-libro])
             cmd-prestar-libro.results_in += ev-prestamo-rechazado
             cmd-prestar-libro.failure_paths.rechazo: ev-prestamo-rechazado
             fl-prestamo-rechazado (kind: falla, failure_of: fl-prestamo).steps: cmd-prestar-libro, ev-prestamo-rechazado
```

The same command's `demora` is a `no_aplica` in Rosa's words, and its `error` is
`{desconocido: hs-prestamo-error}` ("No sé; nunca pasó"). `cmd-generar-multa` shows the system
actor: `pol-multar-vencido` (`mode: automática`) issues it, and its actor is
`act-sistema-circulacion` (`kind: sistema`), named by Rosa. `cmd-avisar-socio` shows a rule given
whole with its actor unknown: `actor: {desconocido: hs-quien-avisa}`, with `informed_by` and its
`error` pointing to the same hotspot. `pol-avisar-reserva` shows a `delay` ("ese mismo día") and
one hotspot, `hs-aviso-reserva`, holding its `then`, its `mode` and a trigger.
