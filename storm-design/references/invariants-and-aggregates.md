# Invariants and aggregates — steps 6 and 8

Read before the first invariant question of a run. The question loop, the question kinds and the
status rules are in `<storm-start>/references/socratic-protocol.md`; this file adds only what is
specific to invariants and to grouping them.

## The stance

The invariant does not validate the concept; it defines it. "Un ejemplar sin código no es un
ejemplar" — it is not an invalid ejemplar, it is something else (a book nobody catalogued). That is
why the question is never "¿qué reglas tiene un X?", which invites a list of validaciones, but
"¿qué haría que esto deje de ser un X?", which forces a verdict on the concept's edge.

| | Invariante definitorio | Validación |
|---|---|---|
| Kind of truth | Necessary: without it there is no X | Contingent: the data could be otherwise |
| When it breaks | The thing is something else ("un error", "un libro sin catalogar") | The thing is an X badly entered |
| Where it goes | Its own `invariants` entry (`inv-`), referenced by id from `glossary[].invariants` and later `aggregates[].invariants` | `glossary[].validations` (`words`, `speaker`), never an invariant |
| Example | "Un libro prestado no se presta de nuevo hasta que vuelve" | "El número de carnet tiene ocho dígitos" |

The stakeholder's answer tells you which one it is: "entonces no es un X" is definitorio;
"entonces hay que corregirlo" is usually a validación. When it is unclear, ask the separating case
from the design detectors before writing; the classification is the voice's, not yours.

## Question ladder (step 6)

One question per turn, each followed by a devolución.

1. `invariante` — "¿Qué haría que esto deje de ser un <X>?"
2. `caso-límite` — take the answer to its edge with a concrete case from THEIR domain: "Si un libro
   se lee en la sala y no sale, ¿es un préstamo?" Record the verdict (`es`, `no-es`, `depende`)
   with `why` and `speaker` in `glossary[].edge_cases`.
3. A `depende` verdict is not an answer yet: ask a `repregunta` with a case that separates the two
   readings, per the protocol.
4. Stop when a new case no longer changes the rule. Say what the rule is, in their words, and ask
   for the yes.

## Grouping into aggregates (step 8)

An aggregate is a frontera de consistencia: the rules that must be true together at the same
instant, and the commands that must respect them. Start from either end:

- **From a command without an aggregate.** Ask which of the confirmed rules it can break: "Cuando
  alguien <comando>, ¿qué regla no puede quedar rota ni un segundo?"
- **From a rule no aggregate lists.** Ask which actions can break it: "¿Qué tendría que pasar para
  que <regla> se rompa?" A rule with no command yet (Process left its actor unknown) can still form
  a group: `handles` stays empty until the command exists.

Then:

1. For each pair of rules touched by the same command or the same action, ask the consistency
   question (kind `invariante`): "¿Esto tiene que ser verdad al mismo tiempo que aquello, o puede
   ponerse al día después?" "Al mismo tiempo" puts them inside the same frontera; "después" leaves
   one outside.
2. Show the group as a plain list of rules plus the commands that touch them. Do not propose a name
   (the protocol's anti-completado, names). Ask: "¿Cómo le llaman ustedes a esto?" (kind `nombre`).
   If they have no name, the group is not written; the question stays in `pending_questions.design`.
3. On a name and a yes, write the aggregate: `invariants` (the ids of the rules), `handles` (the
   commands), `emits` (the `results_in` of those commands), `provenance` with the naming question
   and answer, and `bounded_context`, which the voice places — never you:
   - A confirmed context the voice names → its `bc-` id. No context exists yet → do step 7 first.
   - The voice says the area waits on an open `frontera-candidata` → `{desconocido: <that hotspot>}`
     (`agg-ejemplar` in the fixture).
   - The voice does not know → ask about each open `frontera-candidata`, one per turn: "¿El área de
     <grupo> depende de cómo se decida <palabra>?" A yes → that hotspot. No yes → the protocol's
     "'No sé' is an answer": group first with an open `level: design` doubt of the same theme, or
     open a `desconocido`, `level: design`: "¿A qué área pertenece <grupo>?" Write
     `{desconocido: <that hotspot>}`.
   A frontera nobody tied to the group is never picked because it looks closest.

A derived number is a signal, not an aggregate rule: if a value "sale de" other records, it is
built from events (a read model already listed by Process) and sits outside the frontera.

## Worked example — préstamo (fixture `biblioteca`)

```
Pregunta:    ¿Qué haría que esto deje de ser un préstamo?
Rosa:        Que el libro esté prestado a dos a la vez; eso ya es un error.
Devolución:  Para ti, un libro que ya está afuera no se puede prestar otra vez hasta que vuelve.
             Lo anotaría así → Regla de "préstamo" · un libro prestado no se presta de nuevo · si no, "es un error"
             ¿Es así?
Rosa:        Sí.
Pregunta:    Y la ficha del socio, ¿tiene que cambiar en el mismo instante que se presta, o puede
             ponerse al día después?
Rosa:        Puede salir después; la ficha sale de los préstamos.
```

Result: "un libro prestado no se presta de nuevo hasta que vuelve" (`inv-prestado-no-se-presta`) is
the frontera de consistencia of `Préstamo`, named by Rosa, handling `cmd-prestar-libro` and
`cmd-registrar-devolucion`. `gl-prestamo` references the same id: each rule is written once. The
ficha del socio is outside it: it is derived (`rm-ficha-socio`), not guarded.

Edge case — a validación offered as an invariant:

```
Rosa:        Tampoco puede tener el carnet con siete dígitos.
Wrong:       add "el carnet tiene ocho dígitos" to the invariants of Préstamo.
Right:       ask "Si llega un socio con un carnet de siete dígitos, ¿deja de ser un socio o es un
             socio mal cargado?" — "mal cargado" → gl-socio.validations, in her words.
```
