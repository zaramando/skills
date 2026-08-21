# Step 9 — pruning

The final pass. Everything the skill is better without.

## The deletion test

For every line: remove it, and ask whether the output would degrade. If it would not, the line is a
**no-op** — it costs tokens and dilutes the lines that matter.

No-ops are almost always instructions that describe default behavior:

```
"Read the file carefully before answering."
"Think step by step about the user's request."
"Be thorough and consider edge cases."
"Write a detailed and descriptive commit message."
"Use your best judgment."
```

The model already does these, or cannot be made to do them by being told. Replace with an
instruction that has an observable consequence:

```
BEFORE  "Read the file carefully."
AFTER   "Write one evidence line per part, each with a line number, before producing a score."
```

The rewrite is testable: you can look at the output and see whether it happened.

## DRY — one source of truth per concept

Any list, table, rule or template with two homes will drift, and the drift is silent. The classic
shape is a concept table near the top and a checklist of the same concepts further down: the two
start identical, someone edits one, and now the skill contradicts itself in a way nobody notices
because both halves still look right in isolation.

Merge them. If a table needs to serve as a checklist, give it a column that makes it one.

The one legitimate repetition is a critical rule stated in place AND in the closing reminders. That
is deliberate steering, not duplication — but keep it to the handful of rules that earn it.

## Sediment

Text that accumulated across edits and no longer applies to any branch the skill takes. It appears
wherever several people edit a shared skill and nobody feels entitled to delete.

Symptoms:

- Instructions for a tool, path or workflow the skill no longer uses
- A branch condition that can no longer occur
- A `references/` file no pointer mentions, or a pointer to a file that does not exist
- Two sections whose headings promise different things and whose bodies say the same thing

Sediment is the reason branch-specific material belongs in `references/` rather than inline: when a
branch dies, you delete one file instead of hunting fragments through a 400-line document.

## Size as a symptom

A `SKILL.md` over ~150 lines is usually not a complex skill — it is a skill that never had branch
analysis done. Before adding anything, ask whether the run that does NOT need this material should
have to load it.

## Pruning checklist

```
[ ] Every line survives the deletion test
[ ] No concept has two homes (except deliberate closing reminders)
[ ] No instruction refers to a branch, tool or path the skill no longer has
[ ] Every references/ file is named by exactly one context pointer
[ ] Every context pointer names a file that exists AND the condition to read it
[ ] SKILL.md is under ~150 lines, or you can say precisely why not
```
