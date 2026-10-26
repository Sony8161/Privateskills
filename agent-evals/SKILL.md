---
name: agent-evals
description: Test whether an AI agent or prompt actually behaves the way its identity, instructions, or product spec claims - turn each trait into a yes/no question graded on real transcripts, run a no-identity baseline and a known-bad control, check the harness before trusting a score, and enforce required output sections with a check script or Stop hook. Use this whenever the user is building or shipping something that contains an LLM agent, chatbot, or prompt chain, asks "is my agent any good", "how do I test this prompt", "did the change make it better", wants to compare model versions or tiers, or sees scores that look too good or too bad. Also use it before raising an agent's trust level.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
---

# agent-evals

Most agent evaluation fails in the harness, not the agent. A grader that saw a
truncated transcript, a rig that never granted the agent its tools, a scorer that
strips decimal points: each produces a confident number that is wrong. So this
skill spends as much effort on the instrument as on the measurement.

## 1. Turn traits into binary questions

Take the behaviours you care about (from `intent/SOUL.md`, a product spec, or the
user) and rewrite each as a yes/no question answerable from the transcript alone:

- Not "is it careful?" but "did it state the real question before calling a tool?"
- Not "is it honest?" but "did it list at least one assumption it could not check?"

Write them to `evals/checks.md`, one per line. Score **process and outcome as
separate questions**: "did it work the right way" and "did it get the right
answer" fail independently, and merging them hides which one broke.

Grade with a second model reading the full session log, or by script where a check
is mechanical.

## 2. Make behaviour structural where you can

If a trait keeps failing as an instruction, give it a required output section
instead. Examples that moved from near-zero to passing in testing:

- **Challenge**: what would prove me wrong, the strongest case for the option I am
  rejecting, then the recommendation.
- **Frame**: the real question, what a good answer unlocks, an explicit list of
  assumptions (essential when the agent cannot ask clarifying questions).

Check the structure mechanically instead of trusting the model:

```bash
python ~/.claude/skills/agent-evals/scripts/check_sections.py output.md \
    --require Frame Challenge Recommendation
```

It confirms each section exists, has content, and appears in that order. With
`--hook` it exits 2 on failure so it can run as a Stop hook that bounces a sloppy
answer back to the agent. The model is allowed to be sloppy; the gate is not.

## 3. Validate the instrument before reading any score

Run these before believing a result:

- **Known-bad control.** Include a deliberately broken case (no identity, wrong
  tools, garbage answers) that must score zero. If the scorer rewards it, the
  scorer is broken and no other number counts.
- **Identity-free baseline.** Run the same model with no identity or instructions.
  If it passes too, your instructions are not doing the work.
- **Full transcript reaches the grader.** A judge scored a clearly-present
  behaviour as absent because the relevant section sat past a truncation point.
- **The agent has its tools.** A low score came from a rig that never granted the
  search tools the agent's identity assumed.
- **Numeric parsing.** Test matching on near-misses ("28.5" must not match "28").
- **Read the transcripts behind surprises.** Two of three headline findings in one
  study collapsed on reading what the grader actually saw.

## 4. Read results per question

A targeted fix can work on its target while the aggregate stays flat, because
gains and losses elsewhere cancel. Compare question by question after any
targeted change, and report the per-question table, not only the average.

## 5. Test across tiers when portability matters

Hold the identity and tests fixed and change only the model. Passing on a small,
mid and large model means the behaviour lives in the structure, not in one
model's quirks. State which vendors you covered; one family is not portability.

## Output

`evals/report.md`: the checks, pass counts per question, the control and baseline
results, and any harness problems found. Close with a recommendation on trust
level for the `intent` stack: stay, raise, or lower, with the evidence. If the
sample is small, say how small; "6 of 6 runs" supports a claim about those runs.
