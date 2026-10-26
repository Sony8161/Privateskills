---
name: forge
description: The end-to-end workflow for building a software product or startup from idea to shipped and secured - which skill to run at each stage, what must be true before moving on, and where the project's state is recorded. Chains the idea-validation, spec, design, build, security, hardening, ship and retro skills (spec, decide, pressure-test, swarm, verify, intent, bay, code-quality, code-check, security, agent-evals, grc, investigate, ship, retro, meeting-prep) into one gated pipeline. Use this whenever the user wants to build something end to end, start a new project or startup, asks "where do I start", "what's next", "what's the workflow", "plan the whole build", "how do I go from idea to launch", or returns to a project mid-way and needs to know where things stand. Run with no arguments to report current stage and next action.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Skill
  - AskUserQuestion
---

# forge

One pipeline from idea to a shipped, secured product, built from small skills that
each do one job. This skill does not do the work itself. It decides **which skill
runs next, what must be true before moving on, and where that is written down**,
so a long project survives context resets, session changes and enthusiasm.

```
0 Foundation -> 1 Discover -> 2 Define -> 3 Design -> 4 Build (loop)
              -> 5 Harden -> 6 Ship -> 7 Learn  (-> back to 1 or 4)
```

The gates are the point. Each stage ends in a check that can fail, and a failed
check stops the pipeline until it is fixed or the user knowingly accepts the risk
in writing. A pipeline that always proceeds is only a list.

## First, find out where you are

1. Read `forge/STATE.md` if it exists (template in `references/state-template.md`).
   It records the current stage, gate results, open risks and the next action.
2. Check the handoff log: `python ~/.claude/skills/bay/scripts/bay.py inbox claude`
   and `board`. Anything in flight belongs in your report.
3. If neither exists this is a new project: start at stage 0, and create STATE.md.

If the user ran `/forge` with no instruction, reply with: current stage, last gate
result, what is blocked, and the single next action. Do not start working until
they confirm; a status request is not a work order.

## Scale the pipeline to the job

Not every task needs eight stages. Naming the right entry point is part of the job:

| Situation | Enter at |
|---|---|
| Brand-new idea or startup | 0 |
| Have an idea, unsure anyone wants it | 1 |
| Know what to build, need a plan | 2 |
| Plan exists, need structure | 3 |
| Adding a feature or fixing something | 4, then `ship` |
| Something is built, worried about it | 5 |
| Ready to release | 6 |
| Something finished or stalled | 7 |

A small change inside an existing codebase is stage 4 plus `ship`. Say so and do not
run the ceremony.

## The stages

### 0. Foundation (once per project)
**Run:** `intent` to set up SOUL, GRAVITY, INTENT and the enforcement map. Use
`decide` for any one-way door already on the table (company structure, core stack
that is expensive to change).
**Gate:** the user has read and approved `intent/`, and every deterministic rule has
a real hook or permission behind it, not only a sentence.

### 1. Discover: is this worth building?
**Run:** `swarm` for the research (market, competitors, pricing, the customer's
current workaround), each worker briefed through `brief`; `verify` on the result;
`pressure-test` on the conclusion; `decide` for go / no-go. For a conversation with
a real customer, partner or investor, use `meeting-prep` first.
**Gate:** no unresolved *Fatal* finding from `pressure-test`; claims the decision
depends on are `confirmed`, not `unverified`; the user has named the first person
they will talk to. Demand is usually the weakest assumption, so do not let a swarm
report stand in for one real conversation.

### 2. Define: what exactly are we building?
**Run:** `spec` to scope the MVP (six must-haves at most, explicit out-of-scope,
kill criteria). `pressure-test` the spec. Run `grc` in **scoping mode only** (what
data, which framework, what the customer will ask) so compliance shapes design
instead of arriving as a surprise. Turn each must-have into a `bay` request with a
"done when" line.
**Gate:** spec has out-of-scope and validation sections; every must-have has a
request in the log; the data categories are known (this decides how hard stage 5 is).

### 3. Design: structure before code
**Run:** architecture, API and data-model decisions, using the installed
`ecc:architect`, `ecc:api-design`, `ecc:database-migrations` and
`ecc:postgres-patterns` skills as fits the stack, and `frontend-design:frontend-design`
for the interface. Use `decide` for each one-way door. Run `security` **section 1
(threat model)** now: assets, entry points, trust boundaries, and how tenant
isolation will work.
**Gate:** a threat model exists, tenancy and auth approaches are named, and every
irreversible choice has a decision memo.

### 4. Build: the loop, one slice at a time
For each request, in order:
1. `bay move <id> accepted`.
2. `code-quality`: failing test, minimal code, refactor, project gate commands.
3. A failure you cannot explain in a sentence: `investigate`. No patching by guess.
4. Slice touches auth, payments, user data, uploads or external input: run
   `security` on that slice now.
5. `code-check` on the slice's diff: mechanical scan, the project's own gates, a
   five-lens read, independent reviewers, every finding verified. **BLOCK sends you
   back to step 2**; PASS or PASS WITH NOTES continues.
6. `verify` section C: the new test fails without the change.
7. `bay move <id> delivered --receipt "<exactly what was run and seen, and the
   code-check verdict>"`.

**Gate (per slice):** commands actually run and green, `code-check` not BLOCK,
receipt written. Update
`forge/STATE.md` after each slice so the next session starts from the file, not from
memory.

### 5. Harden: attack it before others do
**Run:** `security` in full (static review, dependency and secret scan, authorized
dynamic test of the local or staging app), with every finding reproduced through
`verify`. If the product contains an LLM, `agent-evals`. Use `ecc:e2e-testing` for
the critical user journeys. If a customer or framework requires it, `grc` for the
full control mapping with named evidence.
**Gate:** no *confirmed* Critical or High finding open; everything unverified is
listed, not hidden; for AI features, an eval report with the baseline and
known-bad control passing.

### 6. Ship
**Run:** `code-check --base main` over the whole branch (with `security`'s
`audit.py` so dependency CVEs are included), then `ship` (diff read, tests, build,
exercise the change, PR with rollback). Quote the code-check verdict in the PR's
"How verified" section. Deployment details from `ecc:deployment-patterns` and
`ecc:docker-patterns`. Make sure the public `SECURITY.md` disclosure policy exists.
**Gate:** `code-check` is not BLOCK, and `ship` reports green, honestly. The
rollback line is real. Secrets are in the environment, not the repo.

### 7. Learn
**Run:** `retro` with evidence from git and the `bay` log; one lesson to memory.
Re-run `pressure-test` against what actually happened versus the spec's kill
criteria. Revisit `intent/` on its review dates. Re-run `security` after any change
to auth, tenancy, payments or dependencies.
**Gate:** the retro wrote a lesson or honestly wrote none; kill criteria were
checked against their date. Then loop to stage 1 or 4.

## Rules that keep it honest

- **Stop at red.** Do not move past a failed gate. If the user chooses to proceed
  anyway, record it in STATE.md under *Accepted risks* with their words and a
  revisit trigger.
- **State is a file.** After every gate, update `forge/STATE.md`. Anything that
  lives only in conversation is lost at the next reset.
- **Report real status.** "Passed" means you ran the check and saw it pass. Say how
  many items remain unverified.
- **One input at a time from the user.** Ask only for decisions that are genuinely
  theirs; make the sensible default yourself and say so.
- **Never test what you do not own.** Dynamic security testing stays on the user's
  own local or staging systems.

## Skill map

| Need | Skill | Source |
|---|---|---|
| Set values, rules, trust levels | `intent` | new |
| Brief an agent or worker | `brief` | new |
| Multi-agent research you can trust | `swarm` | new |
| Check a claim, citation or "tests green" | `verify` | new |
| Scope an MVP | `spec` | yours |
| Hard choice, reversibility | `decide` | yours |
| Attack a plan | `pressure-test` | yours |
| Prep a high-stakes conversation | `meeting-prep` | yours |
| Handoffs with stable IDs and receipts | `bay` | new |
| Write quality code, tests first | `code-quality` | new |
| Verdict on whether a change is clean and secure | `code-check` | new |
| Find the root cause of a bug | `investigate` | yours |
| Vulnerabilities and authorized pen test | `security` | new |
| Test an AI agent or prompt | `agent-evals` | new |
| Compliance controls and evidence | `grc` | yours |
| Pre-merge gate and PR | `ship` | yours |
| Review the period, keep one lesson | `retro` | yours |
