---
name: storm-render
description: >
  Regenerates the human view of an Event Storming workspace: runs storm-start's render.py over
  docs/domain/<slug>/eventstorm.yaml and writes eventstorm.html next to it (timelines grouped by
  lane, failure paths under their flow, pivots marked, hotspots first, light and dark mode). Thin wrapper; it never edits the YAML and never validates
  it — that is storm-verify. Invoke explicitly: /storm-render [domain-slug].
argument-hint: "[domain-slug]"
license: Apache-2.0
metadata:
  author: zaramando
  version: "1.2"
allowed-tools: Glob, Read, Bash(python3 *storm-start/scripts/render.py *)
disable-model-invocation: true
---

# storm-render

Thin wrapper over `render.py`, which storm-start owns. Stateless: the HTML is a pure function of
the YAML. This skill reads only storm-start's contract (step 1) and never the YAML's content, and
writes nothing but `eventstorm.html`. Report in one or two factual lines; say nothing about the
model's content.

Requires storm-start installed as a sibling directory: `${CLAUDE_SKILL_DIR}/../storm-start`. Its
`references/level-contract.md` is the contract this skill follows (read at step 1).

## Procedure

1. **Locate the model.** Read `${CLAUDE_SKILL_DIR}/../storm-start/references/level-contract.md` and
   follow "Locate the model".
2. **Render.**
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/../storm-start/scripts/render.py docs/domain/<slug>/eventstorm.yaml
   ```
3. **Report.** Exit 0 → give the path it printed. Exit 1 → the YAML is malformed, and exit 2
   → a setup problem: follow the matching rule in the contract's "Scripts" section (quote the
   `error:` message; do not re-run).

## Output format

```markdown
Vista generada: docs/domain/<slug>/eventstorm.html
No valida el modelo: para eso, `/storm-verify <slug>`.
```

## CRITICAL REMINDERS

- NEVER edit `eventstorm.html` by hand, and NEVER patch the YAML to make it render. A model that
  renders badly is fixed in a storm-* session, then rendered again.
- A successful render is not a valid model: say so every time.
