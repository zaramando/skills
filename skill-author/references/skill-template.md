# The skeleton, and a worked extraction

## Skeleton — stateless skill

````markdown
---
name: <kebab-case, matches the directory>
description: >
  <What it does, what it emits, when it applies. For model-invoked skills this IS the trigger.
  For user-invoked skills, state the invocation: /name <argument>.>
license: Apache-2.0
metadata:
  author: <you>
  version: "1.0"
allowed-tools: <narrowest set that lets the procedure run>
disable-model-invocation: true   # omit ONLY if model-invocation was a deliberate choice
---

# <name>

<One paragraph: what this does and what it explicitly does not do. Name the sibling skill
that covers the adjacent case.>

## Input contract

<How the target arrives. Wrap runtime data in XML tags: <target_file>, <user_query>, <docs>.
Say what to do when the input is missing — ask, or stop.>

## Leading words

- **<term>** — <one-line definition, reused verbatim later in this file>

## Procedure

1. <Atomic action with an observable result>
2. <...>
3. <Branch step: "Read `references/x.md` and ..." — with the condition stated>

## Output format

```markdown
<The exact shape. Design it so it cannot be filled in without doing the work.>
```

## References

- `references/<file>.md` — <what it holds AND the condition under which to read it>

## CRITICAL REMINDERS

- <The handful of rules that carry real risk. MUST / NEVER / ALWAYS. Nothing else.>
````

## Skeleton — stateful skill

Same shape, with three additions:

````markdown
## Workspace

```
mission.md      # WHY the user is doing this. Consulted every run
notes.md        # agent-private observations: preferences, watch-outs
records/        # outcomes: what was tried, what happened
<units>/        # the numbered deliverables
```

## Procedure

1. **Re-hydrate.** Read `mission.md`, `notes.md`, and the latest entries in `records/`.
   If the workspace does not exist, go to Bootstrap.
2. **Diagnose position.** What is done, what is next, what stalled.
3. ... <the work> ...
N. **Write state back.** Append the outcome to `records/`, update `notes.md` if a preference or
   watch-out surfaced. NEVER end a run without this step.

## Bootstrap (first run only)

1. Ask the user for their mission — why this, and what "done" looks like. Write `mission.md`.
2. Gather primary sources into `resources.md`.
3. Create the workspace tree, then continue from step 2 of the procedure.

## Exit condition

<What "done" looks like, and where the user goes afterwards.>
````

---

## Worked extraction — 340 lines to 90 plus three references

**Before.** One file, `SKILL.md`, 340 lines, in this order:

```
frontmatter (model-invoked, trigger: "when the user works on database migrations")
When to use                                12 lines
Background: how our migration tool works   48 lines
The 10 rules of safe migrations            35 lines
Postgres-specific notes                    40 lines
MySQL-specific notes                       38 lines
Rollback procedures                        30 lines
Checklist (restates the 10 rules)          25 lines
Three worked examples                     104 lines
```

**Diagnosis.**

- *Trigger:* ambient — "when the user works on migrations" fires on file events, not intent. But
  writing a migration is exactly the moment a user does NOT know they need the safety rules → this
  one genuinely is model-invoked. Rewrite the description around the intent, keep the mode.
- *State:* stateless. Each migration is judged on its own; remembering the last one would not change
  the next. No workspace.
- *Structure:* the Postgres and MySQL sections are mutually exclusive branches — a Postgres project
  pays 38 lines for MySQL on every load. Rollback is a branch too: it only matters when something
  failed. The examples are reference.
- *Steering:* the 10 rules exist twice, as prose and as a checklist. No leading words: the file says
  "a migration that cannot be reverted without downtime" in four different phrasings.
- *Pruning:* the checklist is a second copy of the rules and has already drifted — rule 7 changed in
  the prose and not in the checklist.

**After.**

```
SKILL.md                          90 lines
  frontmatter (model-invoked, intent-based description)
  Leading words: "expand-contract", "irreversible cut", "long lock"
  The 10 rules — one table, serving as the checklist. Single source of truth
  Procedure: 6 ordered steps, step 3 branches by engine
  Output format
  References (3 pointers, each with its condition)
  CRITICAL REMINDERS

references/postgres.md    read at step 3 when the target database is Postgres
references/mysql.md       read at step 3 when the target database is MySQL
references/rollback.md    read only when a migration has already failed in an environment
```

The three worked examples were cut to one, inlined at 14 lines, covering the edge case the other two
did not — the happy-path examples were teaching nothing the rules did not already say.

Net effect: a Postgres migration now loads 90 lines instead of 340, the rules exist in one place so
they cannot drift, and "expand-contract" does the work that four paragraphs of prose were doing.
