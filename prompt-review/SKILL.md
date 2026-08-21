---
name: prompt-review
description: >
  Audits an existing prompt (system prompt, CLAUDE.md, SKILL.md, sub-agent prompt, or a prompt
  embedded in a Claude API call) against Anthropic's 10-part framework, and — when the target is a
  SKILL.md — also against the five-checkpoint skill checklist: trigger, state model, structure, steering, pruning.
  Reports a scored gap analysis with concrete fixes. Detects "ski accident" risk: confident
  hallucination caused by missing domain context. Invoke explicitly: /prompt-review <path>.
license: Apache-2.0
metadata:
  author: zaramando
  version: "2.0"
allowed-tools: Read, Grep, Glob
disable-model-invocation: true
---

# prompt-review

Audits what ALREADY EXISTS. To write a new prompt from scratch use `skill-author` (for skills) or
draft directly.

## Input contract

The target arrives in one of two forms:

- **File path**, wrapped as `<target_file>/absolute/path/to/file.md</target_file>` → read it in full first.
- **Inline prompt**, wrapped as `<prompt_to_audit>...</prompt_to_audit>` → use directly.

If neither wrapper is present, treat the last file the user mentioned as the target. If there is no
target at all, ask for one and stop.

## Two passes

| Pass | Judges | Runs when |
|------|--------|-----------|
| **A — the 10 parts** | The prompt content: does it carry what the model needs to answer correctly? | Always |
| **B — the skill checklist** | The artifact: trigger, state model, structure, steering, pruning | Only when the target is a `SKILL.md` |

Pass B lives in `references/skill-checklist.md`. Read it at step 3 of the procedure, not before.

## Leading words

Use these exact terms in the report. They compress the diagnosis into something the reader acts on.

- **ski accident** — the prompt omits domain context, so the model reinterprets ambiguous input in
  the wrong domain and answers confidently. Origin: `references/canonical-case.md`.
- **dilution** — a critical rule sits near the top of a long prompt, where attention is lowest.
- **raw injection** — external or user-supplied data is concatenated into instructions with no
  delimiting tag, so the model cannot tell instruction from data.

Pass B adds its own vocabulary — context load, re-hydration, sediment, no-op, legwork — defined in
its reference.

## Pass A — the 10 parts

Single source of truth. This table IS the checklist; there is no second list anywhere in this skill.

| # | Part | Mark `[v]` only if | Usually lives in |
|---|------|--------------------|------------------|
| 1 | Task Context | An explicit assistant role AND a concrete end goal (not "be helpful") | Frontmatter `description` + "When to use" |
| 2 | Tone Context | A stated register (factual / cautious / concise) AND at least one "do NOT" (don't guess, don't judge) | Tone section |
| 3 | Background Data | Domain vocabulary, structures, valid enums, format quirks. **If the domain is niche and this is absent → ski accident** | "Background Data" / "Critical Patterns" |
| 4 | Dynamic Content | The variable input is a runtime slot, not hardcoded, and is clearly marked as the thing being processed | Interpolated variable / user turn |
| 5 | Detailed Instructions | Ordered steps, each atomic (never "do X and also Y and consider Z") | Numbered procedure |
| 6 | Examples (few-shot) | At least one input→output pair, covering an edge case and not only the happy path | "Examples" section |
| 7 | Critical Reminders | The strongest rules are at the END of the file and use MUST / NEVER / ALWAYS | Last section |
| 8 | XML tags | Data is wrapped (`<user_query>`, `<docs>`, `<ticket>`) and separated from instructions | Throughout |
| 9 | Pre-filling | The assistant turn is pre-started with `{` or `<verdict>`. **N/A outside API calls** | API call, not the prompt string |
| 10 | Reasoning order | An explicit "first analyze X, then Y, then emit the verdict", with the verdict in its own tag | Procedure section |

**Why placement matters:** attention concentrates at the start and end of a prompt. That is the whole
reason part 7 belongs at the end — it is not a stylistic preference.

## Procedure

Do NOT produce a score, a verdict, or the report until the evidence pass is complete. The evidence
pass is the work; the report is just its summary.

1. Read the target in full, start to end.
2. **Evidence pass A.** Walk parts 1→10 in order. For each part write one line: the number, the mark
   (`[v]` / `[!]` / `[x]` / `N/A`), and the proof — a line number and a short quote if present, or
   the specific thing that is absent if not. Ten lines. No part skipped, no part merged.
3. **Evidence pass B** — only if the target is a `SKILL.md`. Read `references/skill-checklist.md`
   and produce one verdict line per checkpoint (trigger, state, structure, steering, pruning) with the same
   evidence discipline: line numbers, not impressions.
4. Determine the denominator for pass A: 10 if the target is an API call, otherwise 9 (part 9 is N/A).
5. Score: one point per `[v]`. `[!]` and `[x]` score zero. Verify that
   `[v] + [!] + [x] + N/A` equals 10 before writing the score — if it does not, the evidence pass
   is wrong, redo it. Pass B has no numeric score.
6. Pick the single worst gap for the Main risk line, naming it with a leading word where one fits.
   If pass B produced a FAIL, the Main risk comes from pass B.
7. Emit the report.

## Output format

```markdown
## Audit: <path or "inline prompt">

### Score: X/N parts present

### Present
- [v] 1. Task Context — role + goal (line 4)
- [v] 5. Detailed Instructions — 4 ordered steps (lines 22-29)

### Weak / Missing
- [!] 7. Critical Reminders — at line 3 instead of the end → dilution
- [x] 3. Background Data — no enum of valid categories → ski accident
- [x] 8. XML tags — user text concatenated at line 12 → raw injection

### N/A
- 9. Pre-filling — not an API call

### Skill checklist (Pass B)     <!-- only when auditing a SKILL.md -->
- **Trigger — FAIL.** <verdict with evidence and consequence>
- **Structure — WEAK.** ...
- **Pruning — WEAK.** ...
- **Steering — PASS.** ...
- **State — PASS.** ...

### Proposed fixes
1. Move the CRITICAL RULES block (lines 3-12) to the end of the file.
2. Add a `<domain>` block listing the 5 valid categories with one line of meaning each.
3. Wrap the user text at line 12 in `<user_query>...</user_query>`.

### Main risk
<main_risk>One line naming the worst gap and its consequence.</main_risk>
```

Conventions: `[v]` present · `[!]` present but weak or misplaced · `[x]` absent. Always cite a line
number. Always propose the concrete replacement text, never "add more context". No praise, no
softening, no summary paragraph after the report.

## References

Read these only when the branch calls for it — not on every audit.

- `references/skill-checklist.md` — Pass B. Read when, and only when, the target is a `SKILL.md`.
- `references/canonical-case.md` — the Swedish insurance V1→V4 case. Read when the user asks *why*
  the framework is shaped this way, or when you need to justify a finding with precedent.
- `references/failure-patterns.md` — the five recurring bad-prompt shapes and their fixes. Read when
  a target exhibits a gap and you need the standard remediation text.
- `references/example-audits.md` — two full worked audits, one API prompt and one CLAUDE.md. Read
  when you are unsure how much evidence a report line should carry.

## CRITICAL REMINDERS

- The model does not fail — the context fails. Every gap you find is a missing part, not a bad model.
- Critical reminders go AT THE END. A rule at the top of a long prompt is a rule that gets diluted.
- Missing background data in a niche domain is a guaranteed ski accident. Say so by name.
- Pre-filling is API-only. NEVER mark it `[x]` on a CLAUDE.md or SKILL.md — mark it N/A.
- When the target is a SKILL.md, pass B is MANDATORY. A skill can score 9/9 on content and still be
  broken because it never fires, because two of its lists disagree, or because it declares a
  workspace it never reads back.
- Never emit a score without the ten evidence lines behind it. The arithmetic MUST close on 10.
