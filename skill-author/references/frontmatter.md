# Step 5 — the frontmatter

Every field below is a decision. Walk the table field by field; an omission you never considered is
an inherited default, not a choice.

| Field | Rule |
|-------|------|
| `name` | kebab-case, matches the directory name exactly |
| `description` | For model-invoked skills this IS the trigger — see `references/trigger-decision.md`. For user-invoked skills it is documentation for the human. Combined with `when_to_use`, capped at 1536 chars in the listing. Omit it and the first paragraph of the markdown body is used instead — never rely on that for a model-invoked skill |
| `when_to_use` | Extra trigger phrases/examples appended to `description` under the same cap — use it instead of bloating the main paragraph |
| `argument-hint` | Autocomplete hint for expected args, e.g. `[issue-number]` |
| `arguments` | Named positional args substituted as `$name` in the body |
| `allowed-tools` | The narrowest set that lets the procedure run. An audit skill that writes files is a design error |
| `disallowed-tools` | Tools pulled from the pool while the skill is active — for autonomous skills that must not call something, e.g. `AskUserQuestion` in a background loop |
| `disable-model-invocation` | `true` for deliberate actions. Also keeps the skill out of subagent precloading, and stops a scheduled task from triggering it as a prompt — confirmed in 2.1.220; docs place it from v2.1.196. Its absence must be a decision, not a default |
| `user-invocable` | `false` hides the skill from `/name` and the human — for background knowledge only the agent should load. Independent of `disable-model-invocation`, not its opposite — see `references/trigger-decision.md` |
| `model` | Pins the model for the rest of the turn. Takes the same values as `/model`, plus `inherit`. Under `context: fork` it sets the forked subagent's model, not the session's. Set only when the procedure needs a specific model, never as a default |
| `effort` | Pins reasoning effort for the rest of the turn: `low`, `medium`, `high`, `xhigh`, `max` (alias `med` → `medium`), or an integer. `xhigh`/`max` degrade to `high` on models that lack them. Defaults to the session's. Same rule as `model` |
| `context` | `fork` runs the procedure in an isolated subagent — pair with `agent` and `background` |
| `agent` | Subagent type to launch when `context: fork` |
| `background` | With `context: fork`, `false` blocks for the result instead of running detached. Default `true` |
| `hooks` | Hooks the skill registers, active for the rest of the session |
| `paths` | Glob patterns that restrict auto-activation to matching files |
| `shell` | Shell used for the skill's `!`-command blocks: `bash` (default) or `powershell` |
| `metadata` | Free-form YAML for the skill's own data. Never reuse another frontmatter field's name as a `metadata` key |
| `metadata.version` | Bump on every structural change |

`license` is accepted but Claude Code doesn't act on it — pure pass-through per the Agent Skills spec.
`compatibility` belongs to the agentskills.io spec (a string capped at 500 chars *there*); Claude Code
2.1.220 neither validates it nor acts on it.

Boolean fields take `true`/`false`; since v2.1.218 they also accept `yes`, `no`, `on`, `off`, `1`, `0` in any
capitalisation. On older versions only `true`/`false` parse.
