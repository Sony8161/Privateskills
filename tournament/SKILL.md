---
name: tournament
description: Make something several different ways in parallel, judge the candidates blind against a rubric set in advance, and combine the strongest parts into one result that is verified to beat every individual candidate - six attempts with distinct strategies plus a judge by default. Use this for high-stakes or open-ended work where the first idea is rarely the best - specs, architectures, API designs, names and copy, prompts, UI concepts, hard algorithms with tests. Trigger it when the user says "try it several ways", "best of six", "give me the strongest possible version", "tournament", "compare approaches", "make it six times and pick the best", or when a decision is expensive to get wrong. Not for routine or easily-checked tasks, since it costs roughly seven times a single attempt.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# tournament

A first answer is one sample from a wide range of possible answers. Generating
several that genuinely differ, then choosing and combining, raises the ceiling. It
only works if four things hold, and each step below exists to protect one of them:

1. The candidates differ in **approach**, not just wording.
2. They are judged against **criteria written before anyone generated anything**.
3. The judge **cannot tell who wrote what**.
4. The combined result is **checked**, because a merge of good parts can be worse
   than its best part.

## 0. Decide whether it is worth the money

The cost is about seven runs: six attempts and a judge, plus the verification
pass. Say that plainly and get a yes with `AskUserQuestion` unless the user already
asked for it. Offer a cheaper setting: three attempts instead of six.

Skip it when the answer is cheap to check (write it once, run the tests), when the
task is trivial, or when `decide` or `pressure-test` would serve. It earns its cost
on work where the best of several is meaningfully better than the first and the
mistake is expensive: specs, architecture, API shape, naming, copy, prompts, UI
concepts, hard algorithms.

## 1. Frame once

Write one task brief (with the `brief` skill's fields) that all candidates receive
verbatim, so their outputs are comparable: the task, the deliverable format, the
constraints. Then write the **rubric before generating**: four to six weighted
criteria, plus any **objective checks** that can be run on a candidate (tests, a
linter, a word limit, a benchmark). Save as `tournament/<name>/brief.md` and
`rubric.md`. A rubric invented after seeing the candidates drifts toward whatever
looks best.

## 2. Fan out, with a different strategy locked into each agent

Spawn all attempts in one message so they run in parallel, as separate agents that
cannot see each other. Each gets the same brief and one strategy lock, and writes a
complete standalone answer to `candidates/<lock>.md`, no hedging. The default six:

| Lock | Instruction |
|---|---|
| Minimalist | The smallest thing that fully works |
| Maximalist | The most complete version, every edge case covered |
| First principles | Ignore convention; derive the answer from scratch |
| Prior art | Adapt the strongest pattern from existing solutions |
| Adversarial | Design against failure first; keep what survives |
| Wildcard | One unreasonable creative bet, executed seriously |

Rename the locks to fit the domain (for copy: plain, story-led, data-led, contrarian
and so on). If no agent tool is available, run the attempts one after another and
reset context between them, and tell the user that is weaker because the attempts
leak into each other.

## 3. Run the objective checks first

Run the tests, linter or measurements on every candidate and record the results.
Taste cannot rescue a candidate that fails an objective check, and it is the
cheapest signal you have.

## 4. Judge blind

```bash
python ~/.claude/skills/tournament/scripts/blind.py tournament/<name>/candidates tournament/<name>/judging
```

This copies the candidates to `X1`, `X2`, ... in random order and saves the key
outside the folder. Give a **fresh judge agent** only the rubric, the objective
results and the anonymized files; use a different model if one is available. The
judge writes no answer of its own first. For each candidate it gives a 1-10 score
per criterion with a quoted line of evidence, a one-line verdict, the candidate's
strongest element and its fatal flaw, then a ranking. Only then reveal the key with
`blind.py --reveal`.

## 5. Synthesize, sparingly

Build on the winner's structure and graft in only the elements the judge named as
strongest **and** that fit together coherently. Keep a ledger of what came from
which candidate. Resist taking everything: a result stitched from six styles is
usually worse than any one of them. If the top two take incompatible approaches,
choose one instead of blending.

## 6. Prove the merge beat the winner

Re-run the objective checks on the synthesis, then judge it blind against the
winner, order randomized. **If the synthesis does not clearly beat the winner, ship
the winner and say so.** Then apply the checks the artifact normally needs: `verify`
for factual claims, `code-check` and `security` for code, `pressure-test` for a plan.

## 7. Deliver

```markdown
# <Task>: tournament result
**Attempts:** <n> | **Judge:** <model> | **Cost:** about <n+1> runs

## Leaderboard
| Rank | Strategy | Score | Verdict |

## Final
<the result>

## What was taken from whom
<ledger>

## What this could not tell you
<see below>
```

Be honest about the limit: six attempts from one model are not six independent
minds, and shared blind spots survive the tournament. For a check that does not share
them, follow with `pressure-test` or a reviewer of a different lineage.
