# Model and effort routing

Pay for capability where a mistake is expensive or the reasoning is deep. Pay
less where the work is high-volume and a script can check it. Never downgrade a
security-critical or irreversible judgment to save money.

## What Claude can and cannot change

This is documented behaviour of Claude Code; confirm against the current docs if a
version differs.

| Layer | Who can change it | How |
|---|---|---|
| **Subagents** | Claude, per call | Pass `model` (`haiku`, `sonnet`, `opus`, `fable`) and `effort` (`low`, `medium`, `high`, `xhigh`, `max`) on the Agent call. This file is the standing instruction to set `effort`; the tool expects an explicit instruction before it is used. `effort` on a subagent needs a recent Claude Code release; if the call is rejected, drop it and say so |
| **A skill's own turn** | The skill, in frontmatter | `model:` and `effort:` fields override the session for the current turn only, then the session setting resumes. `security` and `disprove` set `effort: high` this way |
| **The main session** | **Only the user** | `/model <name>`, `/effort <level>`, `claude --model`, `claude --effort`. Claude cannot switch its own session model or effort. It can only tell the user the exact command and why, then wait |

Useful main-session settings:

- **`/model opusplan`**: Opus while in plan mode, Sonnet while executing. A good
  default for stages 3 and 4: think with the stronger model, type with the cheaper one.
- **`/effort high`** before design and security work, **`/effort auto`** afterwards to
  clear it. Current Opus, Sonnet and Haiku default to medium effort.
- **`/model best`** (alias) when the user wants the strongest available model for a
  one-off hard problem.

Never claim to have switched the main session. Say: "This stage benefits from X;
run `/model ...`", and continue only after they have, or carry on at the current
setting if they decline and say what that costs in risk.

## Tiers

| Tier | Model / effort | Use for |
|---|---|---|
| **Light** | `haiku`, low to medium | Listing and searching files, fetching and extracting facts from a page, re-fetching citations (`verify` A), running scanners and summarizing output, rendering briefs, formatting, boilerplate, simple renames |
| **Standard** | `sonnet`, medium | Ordinary build slices, writing tests, refactors with green tests, research workers in `swarm`, tournament candidates, `code-check` mechanical reading, doc drafts, e2e test writing |
| **Deep** | `opus`, high | Architecture and API design, the threat model, security review of auth, tenancy and payments, `disprove` attack passes, `spec` and `pressure-test`, tournament judge, swarm challenger, root cause after one failed attempt |
| **Maximum** | The strongest model available, `xhigh` or `max` | One-way-door `decide` memos, final security sign-off before launch, the hardest bug after two failed attempts |

## By forge stage

| Stage | Default | Raise to Deep/Maximum when |
|---|---|---|
| 0 Foundation | Standard | A one-way door is on the table |
| 1 Discover | Standard workers; Deep to reconcile and challenge | The decision commits money or direction |
| 2 Define | Deep for `spec` and `pressure-test`; Standard for `grc` scoping | Always for the kill criteria |
| 3 Design | Deep (`/model opusplan` helps) | Always for the threat model |
| 4 Build | Standard; Light for trivial edits | `code-check` BLOCKs twice, or `investigate` cannot state a root cause |
| 5 Harden | Deep for `security`; Light for scanner runs | Anything touching auth, tenancy or payments |
| 6 Ship | Standard | A risky migration |
| 7 Learn | Standard | Never |

## Rules of thumb

- **Start at the cheapest tier that fits, escalate one tier on evidence**: a second
  BLOCK on the same slice, no explainable root cause, or a tournament where the top
  two candidates are within a point.
- **Judges and challengers differ from generators.** Use a different tier or model
  from the one that produced the work, so they do not share its blind spots.
- **Few well-scoped agents beat many tiny ones.** In a 12-run test, every
  general-purpose subagent used roughly 58k tokens whatever its brief said, so each
  agent carries a large fixed cost. Choosing the model and the number of agents moves
  the bill far more than choosing words.
- **Record the choice.** Put `model` and `effort` in the brief JSON (the `brief`
  validator accepts and checks both) and run `validate_brief.py --dispatch` to print
  the values to copy into each Agent call.
- **Say it when you route.** One line is enough: "Using sonnet/medium for the slice,
  opus/high for the threat model."
