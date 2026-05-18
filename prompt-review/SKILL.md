---
name: prompt-review
description: >
  Audits prompts (system prompts, CLAUDE.md, SKILL.md, sub-agent prompts, Claude API calls)
  against Anthropic's 10-part framework. Detects hallucination risk when domain
  context is missing.
  Trigger: user edits CLAUDE.md/SKILL.md/system prompt, or explicitly asks "review this prompt",
  "audit this", "what's missing from this prompt".
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.0"
allowed-tools: Read, Grep, Glob
---

## When to Use

Load this skill when:

- A `CLAUDE.md` file is being edited (global `~/.claude/CLAUDE.md` or project-level)
- A `SKILL.md` is being edited or created (any `~/.claude/skills/*/SKILL.md` or `.claude/skills/*/SKILL.md`)
- A sub-agent / orchestrator system prompt is being edited
- A prompt is being written in code that calls the Claude API (e.g. `.rb` files with `Anthropic::Client`,
  strings with `system:` or `messages:`; Python files with the `anthropic` SDK)
- The user explicitly says: "review this prompt", "audit this", "what's missing from this prompt",
  "is this well written?", "how would you improve this?"

**Do NOT load** when the user asks to WRITE a new prompt from scratch — use `skill-creator`
(if it's a skill) or draft directly. This skill audits what ALREADY EXISTS.

---

## Tone

Direct and diagnostic. No softening, no praise. Report exactly what is missing and why it matters.
Use the output conventions strictly: `[v]` present, `[x]` absent, `[!]` present but weak or misplaced.

---

## The 10-Part Framework (Anthropic, Code w/ Claude SF, May 2025)

An effective prompt covers these 10 parts. Missing one doesn't break the prompt, but accumulating
gaps causes hallucination, inconsistent output, and lower zero-shot accuracy.

| # | Part | What it is | Where it lives in a SKILL.md / CLAUDE.md |
|---|------|------------|------------------------------------------|
| 1 | Task Context | Assistant role + end goal | Frontmatter `description` + "When to Use" |
| 2 | Tone Context | Factual / professional / concise / cautious | Explicit tone section or instructions |
| 3 | Background Data (static) | Manuals, structures, domain vocabulary | "Critical Patterns" / "Background Data" |
| 4 | Dynamic Content | Specific user query | Runtime variable (not hardcoded) |
| 5 | Detailed Instructions | Logical steps in order | "How to Use" / numbered steps |
| 6 | Examples (Few-shot) | Input/output for complex cases | "Examples" section with `<example>` tags |
| 7 | Critical Reminders | Key rules AT THE END of the message | Last section of the file |
| 8 | XML tags | Separate instructions from data | `<docs>`, `<task>`, `<example>`, `<user_input>` |
| 9 | Pre-filling | Force structured output | Start response with `{` or `<json>` (API only) |
| 10 | Reasoning order | Force thinking before verdict | "First analyze X, then Y, return `<final_verdict>`" |

**Why order matters:** the model pays more attention to the START and END of the prompt. Critical
reminders buried in the middle get diluted. That's why (7) goes at the end, not the beginning.

---

## The V1 to V4 Iteration Method (canonical Swedish insurance case)

Real workshop case. Same task: "analyze this Swedish car insurance form and say who's at fault".
Four iterations:

**V1 (total failure):** minimal prompt, no context. The model hallucinated a "ski accident"
because without domain context it interpreted generic Swedish terms as winter sports.
Result: confident and completely wrong response.

**V2:** added a system prompt with an explicit role: "you're a car insurance expert, the reports
are in Swedish, be factual, don't judge if you're not sure". The model stopped inventing but still
couldn't understand the form.

**V3:** added background data — the form structure has 17 rows with fixed meaning
(Row 1: "Parked/Leaving parking", Row 12: "Turning right", etc.).
Added warning: humans mark with circles, scribbles, stains — not perfect Xs. The model
started reading the checkboxes correctly.

**V4 (zero-shot accuracy):** forced explicit reasoning order:
1. List checkboxes marked by each driver
2. Analyze the accident diagram
3. Cross-check checkboxes vs. diagram (detect inconsistencies)
4. Return verdict wrapped in `<final_verdict>...</final_verdict>` for automated parsing

**Lesson:** the model didn't fail in V1 — the context failed. Each V didn't add "magic", it added
one of the 10 missing parts. Applying this skill = doing that diagnosis systematically.

---

## Audit Procedure (execute in this order)

**Input:** the prompt to audit arrives in one of two forms:

- **File path** (via ARGUMENTS): wrapped as `<target_file>/absolute/path/to/file.md</target_file>`. Read the file at that path in full before proceeding.
- **Inline**: the prompt content is wrapped in `<prompt_to_audit>...</prompt_to_audit>`. Use it directly.

1. Read the full file from start to end before making any marks.
2. Go through parts 1–10 in the checklist below, one by one.
3. Count the score: one point per `[v]` out of 10. Pre-filling is N/A for SKILL.md and CLAUDE.md — max achievable score for non-API prompts is 9/10.
4. Identify the single worst smell for the Main Risk line.
5. Produce the output using the exact format from the Output Format section.

Never skip to the output before completing all 10 checks.

---

## Audit Checklist

When reviewing a prompt, validate each item. Mark present / weak / absent.

```
Task Context
[ ] Is there an explicit assistant role?
[ ] Is there a clear end goal (not just "be helpful")?

Tone Context
[ ] Is a tone specified (factual / conversational / cautious)?
[ ] Are there instructions for what NOT to do (not judgmental, don't invent, etc.)?

Background Data
[ ] Is there domain vocabulary / structure / format?
[ ] If the domain is niche (legal, medical, parking, insurance) — is there a glossary or reference?
[ ] SKI ACCIDENT RISK: if this is missing and the domain is ambiguous, it will hallucinate.

Detailed Instructions
[ ] Are there numbered or ordered steps?
[ ] Is each step atomic (not "do X and also Y and consider Z")?

Few-shot Examples
[ ] If the task produces structured output, is there at least 1 input/output example?
[ ] Do the examples cover edge cases, not just the happy path?

Critical Reminders
[ ] Are CRITICAL rules at the END of the file, not the beginning?
[ ] Do the rules use strong language (MUST, NEVER, ALWAYS) where applicable?

XML tags
[ ] Is user data wrapped in `<user_input>` / `<query>` / `<docs>`?
[ ] Are instructions separated from data?

Pre-filling (API only)
[ ] If JSON is expected, does the assistant response start with `{`?
[ ] If a tag is expected, does it start with `<final_verdict>`?
> Note: pre-filling is only relevant for API call prompts. Mark N/A for CLAUDE.md and SKILL.md audits.

Reasoning order
[ ] Is there an instruction to "first think X, then respond Y"?
[ ] Is the final verdict in an isolated tag for parsing?
```

---

## Common Failure Patterns

### Pattern 1: "Ski Accident" (no domain context)

```
BAD PROMPT
"Analyze this report and say who's at fault."
+ <report in Swedish>
```

The model doesn't know it's a structured form. It invents interpretations. Fails silently
with confidence.

**Fix:** add part 3 (Background Data) with the domain structure.

### Pattern 2: Critical reminders at the top

```
BAD PROMPT
"CRITICAL RULE: never return prices in USD, always use the local currency.
[... 2000 lines of instructions ...]
OK, process the query."
```

The rule gets diluted. The model pays more attention to the last 200 lines.

**Fix:** move the rule to the end. Repeat it if needed.

### Pattern 3: Mixed instructions and data

```
BAD PROMPT
"You're a billing support agent. The user asked: 'why was I charged twice?'
and also keep in mind that refunds take 5-7 business days."
```

The model doesn't know where the user's query ends and your instructions begin. Prompt injection
risk if the query comes from external input.

**Fix:**
```
GOOD PROMPT
You're a billing support agent. Refunds take 5-7 business days.

<user_query>
why was I charged twice?
</user_query>

Respond factually. Do not promise a specific refund date.
```

### Pattern 4: Structured output without schema or pre-filling

```
BAD PROMPT
"Return the response as JSON."
```

The model adds "Here's the JSON you asked for:" before the `{`. Breaks the parser.

**Fix (API):** pre-fill the assistant response with `{`. Or provide an explicit schema and example.

---

## Output Format

The skill MUST report the audit with this structure. No fluff, no praise.

```markdown
## Audit: <absolute path of the file>

### Score: X/10 parts present

### Present
- [v] Role defined (line N)
- [v] Step-by-step instructions (lines N-M)
- [v] XML tags for data (line N)

### Weak / Missing
- [x] No tone context -> risk: overly conversational responses
- [!] Critical reminders at the top (line 3) instead of the end -> diluted in long prompts
- [x] No few-shot examples -> task produces structured output, risk of format drift
- [x] No domain background data (niche or ambiguous domain) -> "ski accident" risk

### Proposed Fixes
1. Move "CRITICAL RULES" block (lines 3-12) to the end of the file.
2. Add "Background Data" section with domain vocabulary (entity states, identifiers, business rules, etc.).
3. Add 1 few-shot example showing expected input/output for classifying movements.
4. Wrap user query in `<user_query>...</user_query>`.

### Main risk
<main_risk>one line identifying the worst smell — "ski accident", diluted instructions, or whatever it is</main_risk>
```

Conventions:
- `[v]` = present
- `[x]` = absent
- `[!]` = present but misplaced / weak
- Always include line number when referencing something in the file
- Always propose concrete fixes with suggested text, not just "add context"

---

## Examples

### Example 1: Audit of a weak prompt (score 2/10 → 9/10)

A ticket classification service needs to route incoming support tickets to the right team.

**BEFORE — `support_app/services/ticket_classifier.py` (embedded prompt):**

```python
PROMPT = f"""
Classify this support ticket. Return the category.
Ticket: {ticket_text}
"""
```

**Audit:**

```
## Audit: support_app/services/ticket_classifier.py

### Score: 2/10

### Present
- [v] Dynamic content (line 3, ticket_text interpolation)
- [v] Basic instruction (line 2)

### Weak / Missing
- [x] No assistant role
- [x] No tone — will add empathetic filler instead of being factual
- [x] No background data: what valid categories exist? what does each mean?
- [x] No step-by-step instructions
- [x] No few-shot examples
- [x] No critical reminders
- [x] No XML tags — ticket_text injected raw → prompt injection risk
- [x] No output format specified — string? JSON? enum? caller can't parse reliably
- [x] No reasoning order

### Main risk
<main_risk>Ski accident: no valid categories defined — model will invent names ("account_problem", "payment_error") that don't match any enum in the codebase, breaking the router silently.</main_risk>
```

**AFTER — V4 applying the full framework:**

```python
SYSTEM_PROMPT = """
You are a customer support ticket classifier. Your task is to assign each ticket
exactly one of the valid support categories. You are factual: if the ticket is
ambiguous or doesn't fit, return "other" — never invent a category.

<domain>
Valid categories:
- billing_issue: charges, invoices, refunds, payment failures
- technical_bug: product behaving incorrectly, crashes, data loss
- feature_request: user wants functionality that does not exist yet
- account_access: login failures, password reset, permission errors
- other: does not fit any category above, or insufficient information

Priority rule: if category is technical_bug and user_plan is "enterprise", set urgent=true.
</domain>

<instructions>
1. Read the subject and body together. Never classify on subject alone.
2. Identify the dominant issue (pick one category even if the ticket covers multiple topics).
3. Apply the priority rule.
4. Return ONLY a JSON object inside a <classification> tag.
</instructions>

<example>
Input: subject="Can't log in", body="Reset password but still get 403", plan=pro
Output: <classification>{"category": "account_access", "urgent": false}</classification>
</example>

<example>
Input: subject="Dashboard crashes", body="Crashes on load for all enterprise users", plan=enterprise
Output: <classification>{"category": "technical_bug", "urgent": true}</classification>
</example>
"""

USER_PROMPT = f"""
<ticket>
{json.dumps(ticket_data)}
</ticket>
"""

# Pre-fill the assistant response with "<classification>" to force the format.
```

Score post-fix: 9/10 (explicit pre-filling not shown — add it in the API call, not the prompt string).

---

### Example 2: Audit of a medium-quality CLAUDE.md (score 5/10)

**File:** `~/.claude/CLAUDE.md` (hypothetical mid-range version)

```markdown
You are a coding assistant for a SaaS application. Your goal is to help developers
write correct, maintainable code following the team's conventions.
Always respond in the same language as the user. Be concise and factual.
Never run destructive commands without explicit confirmation.

CRITICAL RULE: never include real API keys or secrets in code examples.
CRITICAL RULE: always use TypeScript strict mode — no `any`, no type assertions without justification.

Stack: Next.js 14 (App Router), Prisma + PostgreSQL, Vitest for unit tests, Tailwind CSS.
The codebase uses server components by default. Add "use client" only for interactivity.
Authentication uses NextAuth.js — never bypass the session check in API routes.

When the user asks for a feature: scaffold under /src/features/{name}/, not /src/pages/.
When the user asks for tests: use Vitest with @testing-library/react for components.
When the user asks about the DB: check /prisma/schema.prisma first, then answer.
```

**Audit:**

```
## Audit: ~/.claude/CLAUDE.md (hypothetical)

### Score: 5/10

### Present
- [v] Task Context — explicit role ("coding assistant for a SaaS") + explicit goal ("correct, maintainable code")
- [v] Tone — "concise and factual", language mirroring, "Never run destructive commands without confirmation"
- [v] Background Data — stack named (Next.js 14, Prisma, Vitest, NextAuth), file conventions, server component default
- [v] Dynamic Content — user messages are the implicit dynamic input (inherent to CLAUDE.md)
- [v] Detailed Instructions — three when/then rules, ordered and domain-specific

### Weak / Missing
- [!] Critical Reminders at the top (lines 6-7) instead of the end → dilute over a long session
- [x] No few-shot examples → what does a correct feature scaffold look like? Format unknown
- [x] No reasoning order → no "first check schema.prisma, then answer" for DB-related queries
- [x] No XML tags → user input not wrapped, injection risk if user pastes external content

### Proposed Fixes
1. Move CRITICAL RULE lines to the end of the file.
2. Add one example showing what a correct feature scaffold response looks like.
3. Add `<user_query>...</user_query>` wrapper instruction for user input.
4. Add reasoning order: "If the query touches the DB: read /prisma/schema.prisma first, then answer."

### Main risk
<main_risk>Critical reminders at the top: the two CRITICAL RULE lines appear at lines 6-7 — in a long session they will be the least-attended part of the context. Move them to the end.</main_risk>
```

---

## Resources

- **Original workshop:** "Prompting 101" — Hannah Moran and Christian Ryan, Anthropic.
  Code w/ Claude, San Francisco, May 22 2025.
- **Related skills:**
  - `skill-creator` — for creating new skills applying the framework from the start
  - `claude-api` — for prompts in code that call the Claude API (includes prompt caching)
- **Canonical case:** Swedish car insurance — V1 hallucinated "ski accident", V4 achieved zero-shot accuracy.

---

## CRITICAL REMINDERS (at the end, intentionally)

- The model doesn't fail — the context you give it fails. Iterate V1 to V4.
- Critical reminders go AT THE END. If you put them at the top in a long prompt, they get diluted.
- No background data in niche domains = guaranteed "ski accident".
- Pre-filling only applies to API calls, NOT to Claude Code / UI (you can't pre-fill the assistant there).
- Don't settle for "this prompt is fine" — count the 10 parts and report the score.
