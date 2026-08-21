# Steps 6 and 7 — steering

Steering is the gap between a skill that *describes* good behavior and a skill that *produces* it.
Most weak skills are perfectly correct documents that change nothing about what the agent does.

## Leading words

A leading word is a compact term carrying a whole concept. Instead of explaining in a paragraph
every time, you name it once and then use the name.

The mechanism is real and observable: when a skill contains a strong term, the agent adopts it,
repeats it in its own reasoning, and aligns its behavior to it. Say "vertical slice" and the agent
stops writing layer-by-layer. Say "ski accident" and it starts hunting for missing domain context.
Three words replace three paragraphs, and they survive summarization.

Rules for coining one:

- **Concrete and unusual.** "Ski accident" sticks; "context insufficiency" does not.
- **Defined exactly once**, in a `## Leading words` section near the top.
- **Reused in the procedure and the output format.** A term defined and never used again steers
  nothing — either wire it in or delete it.
- **Two to six per skill.** Past that they stop being landmarks.

## Protecting the legwork

Agents rush preliminary work as soon as the deliverable is visible. Give an agent a skill that says
"first ask clarifying questions, then write the plan" and it will ask two questions and write the
plan, because the plan is what it is being measured on.

Three fixes, strongest first:

**1. Split the phase into its own skill.** The most reliable one. If discovery lives in
`grill-with-docs` and generation lives in `to-prd`, the discovery agent cannot see the deliverable,
so it spends all its effort on discovery. Hiding the next step is what forces the current one.

**2. Make the preliminary output a required artifact.** If step 2 must emit ten evidence lines with
line numbers before step 5 may produce a score, the work cannot be skipped without the omission
being visible in the output.

**3. Add an explicit gate.** "Do NOT produce the report until the evidence pass is complete." Weakest
of the three — on its own it is close to a no-op, because the agent already believes it is complying.
Use it to reinforce 1 or 2, never alone.

## Formats that enforce their own process

The output format is a steering device, not a cosmetic choice. Design it so it cannot be filled in
without doing the work.

```
WEAK      ### Summary
          <a paragraph about how the code looks>

STRONG    ### Evidence
          - [v] 1. Task Context — role + goal (line 4)
          - [x] 3. Background Data — no enum of valid categories (absent)
          ...ten lines, one per part, each carrying a line number
```

The second version is unfillable without walking all ten parts. The first is fillable from a glance.

The same applies to reasoning order: "first list the checkboxes, record them as verified facts, THEN
read the sketch" produces different results than "analyze the form and the sketch", because it forces
the ambiguous input to be interpreted against established facts instead of generating its own.

## Strong language, used sparingly

MUST / NEVER / ALWAYS work because they are rare. A skill where every rule is critical has no
critical rules. Reserve them for the handful that carry real risk, and put those at the END of the
file — attention concentrates at the start and the end, and the end is nearest to generation.
