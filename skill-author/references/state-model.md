# Step 3 — the state model

Source: "Learn anything with the /teach skill", Matt Pocock.

A skill is either **stateless** or **stateful**, and the choice shapes everything downstream — the
file layout, the first step of the procedure, and whether the skill improves with use.

## Stateless

Retains nothing between runs. Every invocation starts from zero, does the work, emits the
deliverable, forgets. Auditors, reviewers, formatters, generators, one-shot analyses.

The tell: **the deliverable is the entire output**, and a second run on the same input should give
the same answer. If remembering the previous run would not change the next one, the skill is
stateless — do not add a workspace it will never read.

## Stateful

Writes to disk (or to an MCP memory server) and reads that state back on the next run. Teaching,
onboarding, long migrations, anything with a *learner* or a *project* that has a position.

The tell: **the value comes from continuity.** The right next action depends on what already
happened. A teacher who forgets what you learned last week is not a teacher.

The mistake is defaulting to stateless because it is simpler. Ask what the skill would do if it
remembered — if the answer is materially better, it is stateful.

## Designing a stateful workspace

Declare the workspace shape **in the skill**, explicitly, as a file tree. The agent must be able to
walk into a directory it has never seen and know what everything is. Example from `teach`:

```
mission.md          # WHY the user is doing this. Written once, consulted every run
resources.md        # high-trust primary sources, accumulated over time
glossary.md         # terms defined once so later artifacts can stay compact
notes.md            # the agent's own notes: preferences, watch-outs, dead ends
lessons/            # the numbered deliverables, one file per unit
records/            # what actually happened: what worked, what did not
cards/              # compact reference sheets distilled from the lessons
```

The taxonomy generalizes past teaching:

| Artifact | Role | Generalizes to |
|----------|------|----------------|
| `mission.md` | the WHY, stated by the user | the goal any long-running skill is serving |
| `resources.md` | trusted external sources | the citations the work rests on |
| `glossary.md` | terms defined once | shared vocabulary that keeps later artifacts short |
| `notes.md` | agent-private observations | preferences and gotchas not worth a deliverable |
| `<unit>/` | the numbered deliverables | lessons, migrations, chapters, phases |
| `records/` | outcomes, not intentions | what was tried and what happened |

`mission.md` is the one most often skipped and the one that matters most: without a stated WHY,
every run optimizes for a goal the agent guessed.

## Re-hydration is step one

A stateful skill's procedure MUST begin by reading its workspace. Every run lands in a fresh context
that remembers nothing — disk is the only continuity there is.

```markdown
## Procedure

1. Read the workspace: `mission.md`, `notes.md`, and the most recent entries in `records/`.
   If the workspace does not exist, this is a first run — go to "Bootstrap" instead.
2. Diagnose the current position: what is done, what is next, what stalled.
3. ...
```

And it must close by writing state back. A stateful skill that reads but never writes degrades into
a stateless one with extra steps. Name the write explicitly as a numbered step — if it lives only in
a reminder, it gets skipped.

## Choose the artifact format on richness, not habit

Markdown is the default, not the requirement. When the deliverable benefits from diagrams, layout,
callouts, or interaction, a self-contained HTML file is far richer — and an agent writes it as
easily as prose. `teach` emits HTML lessons with diagrams, quizzes and interactive widgets precisely
because Markdown could not carry them.

Pick the format the deliverable needs: HTML for anything visual or interactive, Markdown for text
that will be diffed and reviewed, JSON for anything another program consumes.

## The exit posture

A stateful skill accumulates a relationship with its user, which creates a temptation to make itself
permanent. Resist it. `teach` answers what it can from its sources, then deliberately hands the user
off to real practitioner communities — knowledge and skills it can build, wisdom it cannot.

State the exit condition in the skill: what "done" looks like, and where the user goes afterwards.
A skill with no exit is a skill designed to keep being needed.
