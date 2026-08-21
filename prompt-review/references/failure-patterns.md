# Failure patterns

Four recurring shapes. When an audit finds one, name it with its leading word and paste the fix.

## 1. Ski accident — no domain context

```
BAD
"Analyze this report and say who is at fault."
+ <report in Swedish>
```

The model does not know the input is a structured form with fixed semantics, so it invents an
interpretation. It fails silently and confidently — there is no hedging in the output to warn the
caller. This is the most expensive failure because it looks like success.

**Fix:** add part 3. Enumerate the domain: valid values, what each one means, how the format
behaves in practice. See `canonical-case.md` V3.

## 2. Dilution — critical reminders at the top

```
BAD
"CRITICAL RULE: never return prices in USD, always use local currency.
[... 2000 lines of instructions ...]
OK, process the query."
```

Attention concentrates at the start and end of the context. In a short prompt the top is fine; in a
long one the rule is thousands of tokens away from the moment of generation and gets diluted.

**Fix:** move the rule to the end. If it is genuinely load-bearing, state it in both places — the
duplication is deliberate, not sediment.

## 3. Raw injection — instructions and data concatenated

```
BAD
"You're a billing support agent. The user asked: 'why was I charged twice?'
and also keep in mind that refunds take 5-7 business days."
```

There is no boundary marking where user text ends. The model cannot reliably tell instruction from
data, and if the text comes from an external source it is a prompt-injection vector.

**Fix:**
```
GOOD
You are a billing support agent. Refunds take 5-7 business days.

<user_query>
why was I charged twice?
</user_query>

Respond factually. Do not promise a specific refund date.
```

## 4. Structured output with no schema or pre-fill

```
BAD
"Return the response as JSON."
```

The model prepends "Here's the JSON you asked for:" and the parser breaks on the first token.

**Fix (API):** pre-fill the assistant turn with `{`, or with the opening tag. **Fix (anywhere):**
give the explicit schema plus one example of a valid payload, and require the payload inside a
named tag so the caller can extract it while ignoring surrounding prose.

## 5. No-op instructions

```
BAD
"Read the file carefully before answering."
"Be thorough and think step by step about the user's request."
```

These describe default behavior. They consume tokens and dilute the rules that do carry weight.

**Fix:** apply the deletion test — remove the line and check whether the output degrades. If it does
not, delete it. Replace with an instruction that has an observable consequence: not "read
carefully", but "write one evidence line per part before producing a score".
