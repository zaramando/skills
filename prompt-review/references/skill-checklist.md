# Pass B — is this skill well built?

Run this pass ONLY when the target is a `SKILL.md`. It is orthogonal to the 10 parts: the 10 parts
judge the *prompt content*, this pass judges the *skill as an artifact* — how it is triggered, what
it remembers, how it is laid out, how it steers, and what dead weight it carries.

Sources: "The Missing Manual: How to Write Great Skills" and "Learn anything with the /teach skill",
Matt Pocock.

Five checkpoints. Each gets a verdict: **PASS** / **WEAK** / **FAIL**. Do not invent a numeric score
here — the 10-part score already carries the numbers, and a second one is noise.

## Leading words for this pass

- **context load** — every model-invoked skill puts its `description` into the agent's context on
  every single request. Twenty such skills is twenty descriptions competing for attention forever.
- **cognitive load** — the mirror cost of user-invoked skills: the human pilot has to know the skill
  exists and remember to invoke it.
- **re-hydration** — a stateful skill reading its workspace back from disk at the start of a run.
  Every run lands in a fresh context; disk is the only continuity there is.
- **sediment** — instructions that accumulated over successive edits and no longer apply to any
  branch the skill actually takes. Dead text nobody dares delete.
- **no-op** — an instruction that describes the model's default behavior. Removing it changes
  nothing except the token count.
- **legwork** — the preliminary work a skill needs done properly (discovery, questions, evidence)
  before it reaches its deliverable. Agents rush legwork when they can already see the deliverable.

---

## 1. Trigger

The invocation contract. This is the checkpoint most skills get wrong by default, because the
default is "model-invoked" and nobody chose it.

| Check | Fails when |
|-------|-----------|
| Is the invocation mode a deliberate choice? | Frontmatter has no `disable-model-invocation` and the body never says how the skill is meant to be reached — the mode was inherited, not decided |
| Does the mode match the task? | The skill performs a **deliberate** act (audit, release, migrate, create) but is model-invoked — the user always knows when they want it, so the context load buys nothing |
| Is the `description` a real context pointer? | Model-invoked, but the description is vague ("helps with code quality"), so the agent cannot tell when to follow the pointer |
| Is the trigger ambient? | The description fires on a passive condition — "when the user edits X", "when working on Y" — rather than on an intent. Ambient triggers load the skill constantly and are the main source of context load |
| Is the unpredictability affordable? | Model-invoked skills may simply not fire even when they are the perfect match. If the skill is load-bearing for correctness, that miss is a silent failure |

**Verdict FAIL if:** the skill is model-invoked with an ambient trigger, or model-invoked with a
description that does not describe an intent.

**Fix text:** *"This skill performs a deliberate action. Set `disable-model-invocation: true` and
invoke it by name; drop the ambient trigger from the description."*

---

## 2. State model

Whether the skill carries anything across runs, and whether that choice was made rather than
inherited. Most skills are legitimately stateless — the failure is a skill whose value depends on
continuity that it never actually stores.

| Check | Fails when |
|-------|-----------|
| Is the state model stated at all? | Nothing in the skill says whether it remembers previous runs. The reader cannot tell, and neither can the agent |
| Should it be stateful? | The right next action depends on what already happened — teaching, onboarding, a long migration, anything with a learner or a project position — but every run starts from zero |
| Is the workspace shape declared? | Stateful, but the skill never lays out the file tree, so each run invents a different layout and the workspace becomes unreadable |
| Does it re-hydrate first? | Stateful, but the procedure does not begin by reading the workspace. A fresh context remembers nothing — a run that does not read disk is stateless in practice |
| Does it write state back? | Stateful, but persisting the outcome lives in a reminder rather than a numbered step, so it gets skipped. The workspace goes stale and silently stops being trusted |
| Is there a stated WHY? | Stateful with no `mission.md` equivalent. Every run then optimizes for a goal the agent guessed |
| Is there an exit condition? | The skill accumulates a relationship with its user and never says what "done" looks like or where the user goes afterwards |
| Is the artifact format chosen on richness? | The deliverable is visual, diagrammatic or interactive but is emitted as Markdown out of habit, when a self-contained HTML file would carry it |

**Verdict FAIL if:** the skill's value depends on continuity and it stores none, or it declares a
workspace it never reads back.

**Fix text:** *"This skill is stateful. Declare the workspace tree in `SKILL.md`, make re-hydration
step 1 of the procedure, and make writing state back the final numbered step."*

---

## 3. Structure

A skill is made of two kinds of material: **steps** (the procedure the agent walks) and
**reference** (supporting material that helps execute a step — templates, glossaries, worked
examples, background). They do not belong in the same file.

| Check | Fails when |
|-------|-----------|
| Is `SKILL.md` as small as it can be? | Over ~150 lines with no `references/` directory — reference material is inlined and paid for on every load |
| Was branch analysis done? | Material that is only needed on a conditional branch ("if the target is a Rails app…", "if the user wants a migration…") sits in the main file instead of behind a context pointer |
| Are context pointers explicit? | The skill has a `references/` directory but the body never says *when* to read each file, so the agent reads all of them or none |
| Are steps actually steps? | The "procedure" is prose paragraphs rather than an ordered, atomic sequence |
| Is there exactly one source of truth per concept? | The same list, table or rule appears twice in different shapes. This is the failure that silently drifts out of sync |

**Verdict FAIL if:** a single file over ~250 lines carries steps, reference and examples together,
or two copies of the same list have already diverged.

**Fix text:** *"Move `<section>` (lines N-M) to `references/<name>.md` and replace it with a one-line
pointer stating the condition under which it should be read."*

---

## 4. Steering

Whether the skill actually changes what the agent does, versus merely describing what it should do.

| Check | Fails when |
|-------|-----------|
| Are there leading words? | The skill explains a concept in a paragraph every time instead of naming it once with a compact term the agent can pick up and repeat ("vertical slice", "ski accident", "sediment") |
| Are the leading words used consistently? | A term is defined and then never used again in the procedure or the output format — a definition with no uptake steers nothing |
| Is legwork protected? | The skill puts discovery and its deliverable in the same run with nothing forcing completion — the agent sees the deliverable and rushes the questions. Fix by making the preliminary output a required artifact, or by splitting the phase into its own skill |
| Does the output format enforce the process? | The report shape can be filled in without having done the work. A format that requires per-item evidence forces the pass; a format that only asks for conclusions does not |
| Is strong language used where it matters? | MUST / NEVER / ALWAYS are absent from the rules that actually carry risk — or so overused that everything is critical and nothing is |

**Verdict WEAK if:** the concepts are right but unnamed. **FAIL if:** the skill is a description of
good behavior with no mechanism that produces it.

**Fix text:** *"Name `<concept>` as a leading word, define it once in a Leading Words section, and
use that exact term in the procedure and the output template."*

---

## 5. Pruning

Everything the skill would be better without.

| Check | Fails when |
|-------|-----------|
| DRY | Any concept, list or template with two homes. Cite both line ranges |
| Sediment | Instructions referring to a branch, tool, path or workflow the skill no longer has. Common in shared team skills with several editors |
| No-ops | Lines that describe default behavior: "read the file carefully", "think step by step", "be thorough", "write a detailed commit message". Apply the **deletion test** — remove it and ask whether the output degrades. If not, delete it |
| Redundant restatement | The same rule stated in the intro, the procedure and the reminders. One deliberate repetition at the end is steering; three is noise |
| Dead references | A `references/` file that no pointer in the body ever mentions, or a pointer to a file that does not exist |

**Verdict FAIL if:** more than a quarter of the file survives the deletion test as removable.

**Fix text:** *"Delete lines N-M — they describe default model behavior and pass the deletion test."*

---

## Report section

Append this block to the standard audit report when Pass B ran:

```markdown
### Skill checklist (Pass B)

- **Trigger — FAIL.** Model-invoked with an ambient trigger ("user edits CLAUDE.md", line 7). The
  skill audits on demand; it should be user-invoked. → context load on every request for a
  deliberate action.
- **Structure — FAIL.** 420 lines, no `references/`. The canonical case (63-88), failure patterns
  (155-216) and worked examples (258-399) are reference material inlined into the steps.
- **Pruning — FAIL.** The 10 parts exist twice (45-56 and 113-151) and the two copies have already
  drifted — Dynamic Content is missing from the second, so the score can never total 10.
- **Steering — PASS.** "ski accident" is a working leading word: defined once, reused in the
  checklist, the patterns and the output template.
- **State — PASS.** Stateless, correctly: an audit of a file is judged on that file, and
  remembering previous audits would not change the verdict.
```

Order the five checkpoints worst-first. If Pass B produces a FAIL, the Main risk line comes from
Pass B, not from the 10 parts — a skill that never fires, whose lists disagree with each other, or
whose workspace is never read back, is broken in a way no amount of prompt content fixes.
