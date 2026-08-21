---
name: skill-author
description: >
  Creates a new agent skill, or rebuilds an existing one, applying the five-checkpoint discipline —
  trigger, state model, structure, steering, pruning — on top of Anthropic's 10-part prompt
  framework. Produces a minimal SKILL.md plus a references/ tree, then self-audits it with
  prompt-review. Invoke explicitly: /skill-author <what the skill should do>.
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Read, Write, Edit, Grep, Glob
disable-model-invocation: true
---

# skill-author

A skill is a **procedure an agent executes**, not a document about a topic. If what you have is
knowledge rather than a procedure, it belongs in a `CLAUDE.md` or a reference file — not in a skill.
To judge a skill that already exists rather than build one, use `prompt-review`.

## Before anything: does this warrant a skill?

Answer these three before writing a line. If any answer is "no", say so and stop.

1. **Is it repeatable?** A one-off task does not need a skill. A procedure you will run again, on
   different inputs, does.
2. **Does the agent get it wrong without instruction?** If the default behavior is already correct,
   the skill would be one large no-op. Apply the deletion test to the whole idea.
3. **Is there a deliverable?** A skill that produces nothing inspectable cannot be verified or
   improved. Name the artifact it emits.

## Leading words

The vocabulary this skill both uses and teaches. A skill you author should end up with leading words
of its own — compact terms that carry a whole concept, that the agent picks up and repeats.

- **steps vs reference** — steps are the procedure the agent walks; reference is supporting material
  that helps execute a step. They never share a file.
- **context pointer** — a one-line instruction naming a file AND the condition under which to read
  it. Without the condition it is not a pointer, it is a pile.
- **context load** — the permanent cost of a model-invoked skill: its description occupies the
  agent's context on every request, forever.
- **stateful / stateless** — whether the skill carries anything across runs. Stateful skills own a
  workspace on disk and re-hydrate from it; stateless skills start from zero every time.
- **legwork** — the preliminary work (discovery, questions, evidence) an agent rushes as soon as it
  can see the deliverable.
- **deletion test** — remove a line and ask whether the output degrades. If not, the line is a no-op.
- **sediment** — text that accumulated across edits and no longer applies to any branch the skill takes.

## Procedure

Follow in order. Do NOT open a file for writing before step 5 — a skill drafted while typing becomes
a skill shaped by typing.

1. **Scope it.** State in one sentence what the skill does, what it emits, and who invokes it. Get
   this confirmed by the user before continuing. If the user's request is vague, ask; do not guess
   the deliverable.
2. **Decide the trigger.** Read `references/trigger-decision.md` and pick user-invoked or
   model-invoked deliberately. Write down the reason — it goes in the commit message, not the file.
3. **Decide the state model.** Read `references/state-model.md`. Ask what the skill would do if it
   remembered the previous run; if the answer is materially better, it is stateful — design the
   workspace tree now, before the steps, because re-hydration becomes step one of its procedure.
4. **Draft the steps, and only the steps.** Ordered, atomic, each one an action with an observable
   result. No background, no examples, no templates yet. If a step contains "and also", split it.
5. **Branch analysis.** Go through everything you were tempted to include. Anything needed only on a
   condition — a specific stack, a specific input shape, a failure mode — moves to
   `references/<name>.md` behind a context pointer. What remains in `SKILL.md` is what EVERY run
   needs. Target: under 150 lines.
6. **Name the leading words.** For each concept the skill explains in more than two sentences, coin
   a term, define it once, and then use that exact term in the procedure and the output format.
   A term defined and never reused steers nothing — delete it or use it.
7. **Protect the legwork.** Read `references/steering.md`. If the skill has a discovery phase and a
   deliverable phase, make the discovery output a required artifact, or split it into a separate
   skill. Design the output format so it cannot be filled in without doing the work.
8. **Content pass.** Walk the 10 parts (role, tone, background, dynamic content, instructions,
   examples, critical reminders, XML tags, pre-filling, reasoning order) over the draft. Put the
   critical rules at the END, in a `## CRITICAL REMINDERS` section.
9. **Prune.** Read `references/pruning.md` and run the deletion test on every line. Kill duplicated
   lists — one source of truth per concept, always.
10. **Self-audit.** Run `prompt-review` on the file you just wrote. Fix everything it reports before
    handing the skill over. A skill-authoring skill that ships an unaudited skill has failed.

## File layout

```
<skill-name>/
  SKILL.md            # steps only. Under ~150 lines
  references/         # reference material, one file per branch
  scripts/            # executable helpers, if any
  assets/             # templates, fixtures, images
```

| Directory | Holds | Rule |
|-----------|-------|------|
| `references/` | Prose the agent reads to execute a step: branch material, glossaries, worked examples | Local paths only. NEVER a web URL — a reference the agent may fail to fetch is not a reference |
| `assets/` | Artefacts the agent copies or fills in: templates, schemas, fixtures | If the agent reads it to decide, it is a reference; if it copies it, it is an asset |
| `scripts/` | Executables the procedure invokes | The skill must say which step runs them and what they return |

Naming:

| Kind | Pattern | Examples |
|------|---------|----------|
| Generic capability | `<technology>` | `pytest`, `playwright`, `typescript` |
| Project-specific | `<project>-<component>` | `myapp-api`, `myapp-ui` |
| Workflow / action | `<verb>-<target>` | `skill-author`, `prompt-review` |

A stateful skill additionally declares its **workspace** — the tree it creates in the user's working
directory — inside `SKILL.md`. The workspace is not part of the skill package; it is what the skill
writes. Never conflate the two.

`SKILL.md` frontmatter:

| Field | Rule |
|-------|------|
| `name` | kebab-case, matches the directory name exactly |
| `description` | For model-invoked skills this IS the trigger — see `references/trigger-decision.md`. For user-invoked skills it is documentation for the human |
| `allowed-tools` | The narrowest set that lets the procedure run. An audit skill that writes files is a design error |
| `disable-model-invocation` | `true` for deliberate actions. Its absence must be a decision, not a default |
| `metadata.version` | Bump on every structural change |

## References

- `references/trigger-decision.md` — step 2. User-invoked vs model-invoked, and how to write a
  description that works as a context pointer.
- `references/state-model.md` — step 3. Stateful vs stateless, workspace design, re-hydration,
  artifact formats, and the exit posture. Read in full when the skill turns out to be stateful.
- `references/steering.md` — steps 6 and 7. Leading words, legwork protection, and formats that
  enforce their own process.
- `references/pruning.md` — step 9. DRY, sediment, no-ops, the deletion test.
- `references/skill-template.md` — the skeletons (stateless and stateful) to start from, plus a
  worked before/after reducing a 340-line single file to 90 lines and three references.

## CRITICAL REMINDERS

- Steps and reference NEVER share a file. If you cannot tell which one a paragraph is, it is reference.
- A context pointer without a condition is not a pointer. Always write *when* to read the file.
- NEVER leave the invocation mode to the default. Choose it, and be able to say why.
- A stateful skill MUST re-hydrate as its first step and write state back as its last. One without
  the other is a workspace that rots.
- One source of truth per concept. Two copies of the same list WILL drift, and the drift is silent.
- The deletion test is not optional. If removing a line changes nothing, the line costs tokens and
  dilutes the lines that matter.
- Do not hand over a skill you have not run `prompt-review` against.
