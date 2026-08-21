# Step 2 — the trigger decision

Every skill is invoked one of two ways. The default is model-invoked, which means most skills have
this decided *for* them. Decide it.

## The two modes

**Model-invoked.** The skill's `description` is injected into the agent's context on every request.
The agent reads it, decides whether it applies, and if so pulls `SKILL.md` into context. The
description is a **context pointer**: it does not do the work, it advertises that the work exists.

**User-invoked.** `disable-model-invocation: true`. Nothing enters the agent's context until the
human names the skill. The skill sits on disk, invisible, until invoked.

## The costs are symmetric

| Mode | Cost |
|------|------|
| Model-invoked | **Context load.** Every description is permanent context, on every request. Fifty model-invoked skills is fifty descriptions competing for attention before the user has said anything. Plus **unpredictability**: the agent may decline to follow a perfect pointer, and you will not know it happened |
| User-invoked | **Cognitive load.** The human pilot has to know the skill exists and remember to invoke it. A user-invoked skill nobody remembers is a skill that never runs |

Neither is better. They serve different situations, and a repo can hold both.

## The decision rule

Ask: **at the moment this skill should run, does the user already know they want it?**

- **Yes → user-invoked.** Auditing, releasing, creating, migrating, scaffolding. These are deliberate
  acts with an obvious moment. Paying context load forever to detect a moment the user can announce
  in two words is a bad trade — and it removes the whole class of "why didn't it fire" problems.
- **No → model-invoked.** Domain conventions the user does not know to ask for; safety rules that
  must apply whether or not anyone remembers them; project gotchas a newcomer cannot anticipate.
  Here the agent knowing is the entire value.

Load-bearing correctness pushes toward user-invoked even when the trigger is detectable: if a missed
invocation produces a silently wrong result, do not stake it on the agent choosing to follow a pointer.

## Ambient triggers are the main failure

An ambient trigger fires on a passive condition instead of an intent:

```
BAD   Trigger: user edits CLAUDE.md/SKILL.md, or opens a file under src/prompts/
GOOD  Trigger: user asks to audit, review or score an existing prompt
```

The bad version loads the skill every time a file is touched, for a task the user did not ask for.
Triggers describe **intents**, never file events.

## Writing a description that works as a pointer

For model-invoked skills the description is the only thing the agent sees before deciding. It must
answer: what does this do, what does it produce, and when does it apply.

```
BAD
description: Helps with code quality and best practices.

GOOD
description: >
  Adds a bidirectional sync event between the cloud app and the edge device without
  reintroducing the five known production bugs. Use when adding a new entity event type
  to the sync pipeline — covers the outbox, the event handler and the pull job.
```

Rules:

- Name the artifact it emits. "Produces X" beats "helps with X".
- Include the vocabulary a user would actually type. The agent matches on those words.
- State the boundary. A description that says when NOT to use the skill prevents more misfires than
  one that only says when to use it.
- Never write "use this skill when appropriate". That is a no-op.
- Never add a `Keywords` section to the body. Matching happens on the frontmatter
  `description`; keywords buried in the body are read only after the skill has already been
  loaded, which is too late to influence the decision.

For user-invoked skills the description is documentation for a human browsing a list. Same rules,
lower stakes — and it should state the invocation explicitly: `/skill-name <argument>`.
