---
name: brief
description: Write a typed, validated brief before handing work to any subagent, parallel agent, or fresh Claude session - required fields (role, goal, criteria, tool quota, write budget, pacing, output path), a validator that refuses to dispatch an incomplete brief, and a renderer that compiles the brief into the prompt. Use this whenever the user is about to delegate, fan out, spawn agents, run a research swarm, write a prompt for another agent, or says "dispatch", "have agents do", "parallelize this", "hand this off". Also use it when delegated work came back empty, truncated, or off-target, because that is almost always a brief that left a critical instruction as a sentence instead of a field.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# brief

A brief is an API, not a prompt. The interface between you and a worker matters
more than the worker's raw ability, and the way that interface fails is quiet: a
critical rule lives in the middle of a paragraph, one dispatch drops it, and the
agent burns its whole tool budget researching and never writes a word.

The fix is to make every instruction that must not be forgotten a **required
field**, check the fields in plain code *before* anything launches, and generate
the prompt from the fields instead of writing it by hand. Missing fields then
cost nothing, because no agent has been spawned yet.

## Roles, so the boundaries stay clear

- **Operator** (the user): sets the goal, judges the result, owns the boundaries.
- **Orchestrator** (you): writes briefs, dispatches, reconciles what comes back.
- **Workers** (subagents): do one bounded job and write one file.

## The fields

Every brief is a JSON object with these keys. `references/brief.example.json` is
a filled-in copy to start from.

| Field | Why it is required |
|---|---|
| `id` | Stable name, so the output file and manifest row can be matched to it. |
| `role` | The identity the worker adopts. Without it, workers default to generic. |
| `goal` | The one question or deliverable, stated so it can be checked. |
| `facet` | The angle this worker owns. Distinct facets are what make agreement between workers meaningful. |
| `criteria` | The rubric the worker self-grades against before finishing. |
| `tool_quota` | Hard ceiling on tool calls. Unbounded workers research until they run dry. |
| `write_budget` | Turns reserved for writing. This is the field whose absence caused the empty-output failure. |
| `pacing_instruction` | When to stop gathering and start writing, e.g. "At call N-2, stop researching." |
| `output_path` | The one file the worker must write. The folder is the deliverable. |

**Optional fields.** `model` (`haiku`, `sonnet`, `opus`, `fable` or `inherit`) and
`effort` (`low`, `medium`, `high`, `xhigh`, `max`) record how the worker should be
run. The validator checks them when present, and `--dispatch` prints them so you
copy the same values onto the Agent call. Choose them with `forge/references/model-routing.md`.

## Workflow

1. **Write the brief(s)** as JSON, one per worker, into `briefs/` in the project.
   Give each worker a different `facet`. Same facet twice is waste; different
   facets reaching the same conclusion is evidence.
2. **Validate before dispatch:**
   ```bash
   python ~/.claude/skills/brief/scripts/validate_brief.py briefs/*.json
   ```
   It exits non-zero and lists every missing or empty field. Do not dispatch past
   a failure. It also catches `write_budget` >= `tool_quota` and duplicate
   `output_path` values, since two workers writing one file is a silent overwrite.
3. **Render the prompt from the struct:**
   ```bash
   python ~/.claude/skills/brief/scripts/validate_brief.py --render briefs/a.json
   ```
   Paste the rendered text as the worker's prompt. Edit the JSON, never the
   rendered prompt, so the struct stays the source of truth.
4. **Record the dispatch** with the `swarm` skill's manifest before launching, so a
   crash mid-run can be recovered by relaunching only the missing workers.
5. **Check the folder, not the reports.** When workers finish, count the files in
   `output_path`. A missing file is a failure the worker did not report.

## Judgement

**A brief with a vague `goal` passes the validator and still fails.** The validator
checks presence, not quality. Read the goal once as the worker would: could two
reasonable workers interpret it differently? If so, sharpen it.

**Resist adding fields casually.** Each required field is a promise that a worker
failing without it has been observed. Add one when a real dispatch failed for
want of it, not because it sounds thorough.

**A one-off single-agent task does not need this.** The structure pays for itself
from about three workers, or any task where the cost of an empty return is high.
