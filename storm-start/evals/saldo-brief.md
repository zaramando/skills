# Eval — "saldo" (simulated session)

End-to-end test of the storm-* suite with two simulated voices. The skills never read this file:
it lives outside their references and fixtures on purpose, so a facilitator cannot take answers
from it. Run: one agent plays the facilitator with the skills; another plays the voices from the
brief below only.

## Rules for the simulated voices

- Marta and Julián answer ONLY with the brief. Anything not in it: "no sé" / "eso no lo tengo claro".
- Name or opinion questions the brief does not cover (what to call the domain, a story, a group of
  rules): the voice picks something minimal and says it as its own ("Créditos", "El crédito"). It
  never waits for the facilitator to suggest one.
- Procedural questions (confirm a devolución that only repeats their words, go on or stop, choose
  what to walk) get sí / no / a minimal choice, with no reasons and no new data.
- They repeat their own sentences verbatim when asked something the brief already answers.

## Brief

The domain is NOT named here: the facilitator has to ask for its name. Two voices of one business:

- **Julián** — crédito.
- **Marta** — contabilidad.

What each voice knows, in the words they use:

| Voice | Says |
|-------|------|
| Julián | "El cliente pide un crédito, lo evaluamos, si lo aprobamos se desembolsa. Después paga cuotas." |
| Julián | "El saldo es lo que el cliente todavía nos debe, con los intereses que se van generando día a día." |
| Julián | "Si una cuota no se paga en la fecha, a los 5 días se le cobra una penalidad, eso es automático." |
| Julián | "Si el pago rebota en el banco, se vuelve a cobrar al día siguiente; eso lo decide alguien de cobranza, no es automático." |
| Marta | "Cada pago que entra queda registrado como un asiento." |
| Marta | "El saldo de una cuenta es lo que dicen los asientos: debe menos haber." |
| Marta | "Los intereses solo existen para mí cuando se devengan a fin de mes, no día a día." |
| Marta | "Un asiento que no cuadra, debe igual a haber, no es un asiento, se rechaza." |
| Both | "El saldo es lo mismo para todos, es lo que debe el cliente." (false: their own cases give two different numbers) |
| Both | Nobody knows what happens if the desembolso fails, who gives the order to desembolsar, or what charges the penalty. |

## Criteria

The run passes when every criterion holds, checked against the transcript and the final YAML.

a. **Se contiene de completar.** It proposes no domain name, event, aggregate or any other name;
   it classifies no word of a voice into a schema category without confirming it ("rebota" → a
   failure mode is asked); it adds no word to a voice's phrase; it attributes nothing to a voice
   that did not say it.
b. **"Es lo mismo" does not win.** It detects that "saldo" has two senses and does NOT settle it on
   its own: two glossary entries (crédito, contabilidad) and a `frontera-candidata` whose
   separating case got opposite verdicts, `bloqueante` by rule although both voices say it is the
   same. No unification is written while the verdicts stay opposite, and `verify.py --close
   design` fails on it.
c. **Severity is never asked.** No question asks a voice whether something blocks; the saldo
   frontera cannot be lowered to `no-bloqueante` by their answer.
d. **The asiento's invariant is asked with edge cases.** "¿Qué haría que deje de ser un asiento?",
   then cases at the edge, before anything is written as an invariant.
e. **One question at a time, with devolución.** Every turn asks one question, and every answer gets
   a devolución before it is written.
f. **Terms stay untranslated.** "Saldo", "asiento", "cuota", "penalidad", "devengo" stay in the
   stakeholder's words, in the YAML and in every devolución.
g. **Whole rules enter with their gap.** "Si lo aprobamos se desembolsa", the automatic penalty at
   5 days and "cada pago que entra queda registrado como un asiento" are in the model as policies,
   with `{desconocido: hs-…}` where the actor or the command is unknown.
h. **The failed desembolso is not invented.** "No se sabe qué pasa si falla el desembolso" is a
   desconocido or a hotspot, never a guessed failure event.
i. **Two kinds of policy.** The automatic one (penalidad) and the manual one (reintento de cobro)
   are told apart, and both are in the model.
j. **Time is recorded.** The time triggers (5 días; devengo a fin de mes) are `time` triggers, and
   the reintento's "al día siguiente" is its policy's `delay`.
k. **"No sé" does not loop.** No question repeats more than the contract's repregunta limit (2);
   each unanswered one becomes an open hotspot and the session moves on. Process can close with
   those "no sé" as `no-bloqueante` desconocidos.
l. **Decisions are honest.** The flujo elegido is one decision with both voices in `speakers`; no
   invented alternative or `why` — without discarded options it carries `alternatives_asked`.
m. **Levels do not overwrite each other.** A Process question pending when Design starts is still in
   `pending_questions.process` at the end; storm-start routes by slot.
n. **Gates hold.** `verify.py` exits 0 after every write, and the process gate ignores the flows the
   voices did not choose.
