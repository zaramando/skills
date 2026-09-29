# Bounded contexts — step 7

Read before the first `frontera` question of a run. The `frontera` question kind, the homonym
detector, severity and the conflict rules are in `<storm-start>/references/socratic-protocol.md`;
this file adds only how a candidate boundary becomes a decided one.

## Where boundaries come from

Big Picture leaves `frontera-candidata` hotspots: one word used in two areas, with a glossary entry
per `context`. Design turns each into a decision. The test is the juego de lenguaje: not whether
the word is the same, but whether the rules it follows are. Compare the `invariants` and
`edge_cases` of both glossary entries (step 6 fills them); if a case gets `es` in one area and
`no-es` in the other, they are two juegos de lenguaje.

## Per open candidate boundary

1. `frontera` — "Cuando <voz A> dice <palabra> y <voz B> dice <palabra>, ¿hablan de lo mismo?"
   Bring a case that the two entries decide differently.
2. Ask the decision itself: separate (each area keeps its own term) or unify (one term with one set
   of rules for both). Unify is valid only under the protocol's "Unifying needs one verdict per
   case" (section "Voices"): re-ask every separating case to each voice first. If a case keeps
   opposite verdicts, unify cannot be written, however sure the voices are that "es lo mismo".
3. Ask who decides. The authors are voices in `speakers`, never you and never "el equipo". If nobody
   present can decide, the hotspot stays open with the severity the protocol's "Severity" sets; do
   not ask whether it blocks.
4. Write the decision: `statement`, `speakers` as authors, `why` in their words, `outcome:
   unificar` or `separar`, `alternatives_rejected` (the option not taken, with its `why_not`, asked
   as an `alternativas` question), `refs` to both glossary entries and the hotspot, `level: design`.
   Set the hotspot `resolution: resuelto` with `resolved_by`, and `decision` on both glossary
   entries. `verify.py` checks the outcome against the verdicts (`unified-verdicts`).
5. Continue with "Per decided boundary".

## Per decided boundary

The hotspot already has `resolved_by`: separate or unify is settled, so do NOT ask it again. Only:

1. Ask the name of each context in their words (kind `nombre`: "¿Cómo le llaman ustedes a esta
   área?"). No name → the context is not written; the question stays in `pending_questions.design`.
2. In its own turn, ask its purpose ("¿Qué parte de esto es solo tuya?").
3. Write `bounded_contexts` and set `glossary[].bounded_context` on every term of that area.

Keeping two glossary entries for one word across two contexts requires the `frontera-candidata`
hotspot to stay in the YAML, resolved: `verify.py` checks it (`homonym-boundary`).

## The single-context case

If no boundary appears, the domain still needs one bounded context (the design gate checks it):
every aggregate references one or an open design doubt about its area (see
`invariants-and-aggregates.md`, "Grouping", point 3). Ask the stakeholder to name the area, as in
"Per decided boundary", and record why no split was needed as a decision only if someone proposed one.

## Edge case — a conflict disguised as a boundary

In the fixture, before it was decided, Rosa said a book dropped in the night box is returned when
she registers it and Tomás said when it falls in the box (`hs-devolucion-buzon`). Both speak about
the same devolución, inside Circulación.

```
Wrong:  create "Devolución en mostrador" and "Devolución en buzón" as two contexts so both are right.
Right:  it stays one conflicto-entre-voces, `bloqueante` by rule, with both positions in their
        words. The next question is a separating case: "Si el socio deja el libro en el buzón el
        domingo a la noche, ¿cuándo quedó devuelto?" Only a decision whose authors both accept
        resolves it (`dec-devolucion-buzon`, `speakers: [sp-rosa, sp-tomas]`).
```

A boundary separates areas that already follow different rules. It is never a way to avoid a
decision inside one area.
