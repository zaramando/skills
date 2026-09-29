---
name: storm-verify
description: >
  Checks an Event Storming workspace structurally with storm-start's verify.py and reports every
  failure with the session that fixes it. Reports; never edits the model. Invoke explicitly:
  /storm-verify [domain-slug] [--close <level>].
argument-hint: "[domain-slug] [--close big-picture|process|design]"
license: Apache-2.0
metadata:
  author: zaramando
  version: "2.1"
allowed-tools: Glob, Read, Bash(python3 *storm-start/scripts/verify.py *)
disable-model-invocation: true
---

# storm-verify

Thin wrapper over `verify.py`, which storm-start owns. It is an audit: it writes nothing. Report
factually; no verdict of your own on the model.

Requires storm-start installed as a sibling directory: `${CLAUDE_SKILL_DIR}/../storm-start`. Its
`references/level-contract.md` is the contract this skill follows (read at step 1). verify.py is the
only list of checks; this skill never restates them.

## Procedure

1. **Locate the model.** Read `${CLAUDE_SKILL_DIR}/../storm-start/references/level-contract.md` and
   follow "Locate the model".
2. **Run the structural checks.** Pass `--close <level>` only if the user gave it.
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/../storm-start/scripts/verify.py docs/domain/<slug>/eventstorm.yaml [--close <level>]
   ```
3. **Exit 2** → follow the exit-2 rule in the contract's "Scripts" section.
4. **Exit 1 with no report** (an `error:` message, no `FAIL` lines) → the YAML is malformed: follow
   the malformed-YAML rule in the contract's "Scripts" section (quote it, do not re-run).
5. **Exit 1 with a report** → report every `FAIL` line with its ids and where it is fixed, translating the
   `fixed in:` text of the report into the user's language: a `/storm-<level>` command stays as is;
   a phrase ("the session that wrote the element", "the session that wrote the hotspot"…) becomes
   its plain translation followed by the ids of the line, e.g. "la sesión que escribió
   `cmd-prestar-libro`"; `/storm-<the hotspot's level>` becomes the command for that hotspot's
   `level`.
6. **Exit 0** → report PASS. With `--close`, add that the level MAY now close, and that closing
   happens in `/storm-<level>`.

A semantic critique of the model is not offered here. When praxis-challenge accepts `model_file`,
this is the skill that will launch it after a PASS.

## Output format

```markdown
Estructura: PASS | FAIL (<n> checks, <m> problemas)
- <check>: <problem with ids> → se corrige en <translated fixed-in>
```

## CRITICAL REMINDERS

- NEVER edit the YAML or the HTML. This skill reports; fixing happens in a storm-* session with the
  stakeholder.
- A PASS is structural only. Say so; never present it as a judgment on the model's meaning.
