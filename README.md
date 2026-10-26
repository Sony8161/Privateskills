# Privateskills

Claude Code skills for building a product from idea to shipped and secured. Copy the
folders into `~/.claude/skills/`. Start with `/forge`; it tells you what to run next.

These skills expect eight companion skills that are not in this repo: `spec`, `decide`,
`pressure-test`, `investigate`, `ship`, `retro`, `grc`, `meeting-prep`. Install those too,
or `forge` will point at skills that do not exist.

## The workflow, in order

`/forge` runs eight stages. Each ends in a gate that can fail, and a failed gate stops
the pipeline until it is fixed or you accept the risk in writing.

| Stage | Goal | Skills, in order |
|---|---|---|
| 0 Foundation | Set values and rules once | `intent`, `decide` |
| 1 Discover | Is it worth building? | `swarm` (with `brief`, `verify`), `disprove`, `pressure-test`, `decide`, `meeting-prep` |
| 2 Define | Exactly what to build | `spec`, `pressure-test`, `grc` (scoping), `bay` |
| 3 Design | Structure before code | `security` (threat model), `decide`, optionally `tournament` |
| 4 Build | One slice at a time | `bay`, `code-quality`, `investigate`, `security` (sensitive slices), `code-check`, `verify` |
| 5 Harden | Attack it before others do | `security` (full), `agent-evals`, `grc` |
| 6 Ship | Release | `code-check` (whole branch), `ship` |
| 7 Learn | Keep one lesson | `retro`, `pressure-test`, `security` re-run |

State lives in `forge/STATE.md` in your project; the handoff log lives in `bay/log.jsonl`.

## Skills in this repo

| Skill | What it does | Use it when |
|---|---|---|
| `forge` | The gated workflow, model and effort routing, state file | Starting a project, or asking "what's next" |
| `intent` | SOUL, GRAVITY and INTENT files; sorts rules into advisory, hook or required section | Project start; repeated corrections |
| `brief` | Typed, validated brief for any subagent; checks fields before dispatch | Before delegating to agents |
| `swarm` | Independent agents, reconcile, verify, challenge | Research you need to trust |
| `tournament` | Six strategies, blind judge, verified synthesis | High-stakes or open-ended creation |
| `disprove` | Attack your own answer with evidence; SURVIVED / SHAKY / BUSTED | "Are you sure", technical facts |
| `verify` | Re-fetch citations, reproduce claims, test "tests green" | Acting on agent output or a report |
| `bay` | Append-only handoff log with stable IDs and receipts | Work passing between sessions or roles |
| `code-quality` | Test-first loop per slice, the project's own gates | Writing code |
| `code-check` | Verdict on a change: PASS, PASS WITH NOTES or BLOCK | End of every slice; before shipping |
| `security` | Threat model, CVE and code scans, authorized pen test, compliance readiness | Auth, payments, data, before launch |
| `agent-evals` | Test an AI feature with binary checks, a control and a baseline | The product contains an LLM |

## Scripts

All standard-library Python; nothing is installed.

- `brief/scripts/validate_brief.py` validates briefs, renders prompts, prints `--dispatch` model and effort.
- `swarm/scripts/manifest.py` tracks which agents produced output.
- `tournament/scripts/blind.py` shuffles and anonymizes candidates for blind judging.
- `bay/scripts/bay.py` the handoff log.
- `agent-evals/scripts/check_sections.py` required-section checker, usable as a Stop hook.
- `code-quality/scripts/detect.py` finds the project's lint, type and test commands.
- `code-check/scripts/check.py` scans only the lines you added.
- `security/scripts/scan.py` quick grep for leads; `audit.py` runs the real scanners that are installed.

## Rules that hold everywhere

- Stop at red: never move past a failed gate silently.
- A missing scanner is a coverage gap, not a pass.
- Scanner output and reviewer output are leads; reproduce before reporting.
- Dynamic security testing runs only against systems you own, ideally localhost.
- Claude cannot change your session model or effort; it tells you the command.
