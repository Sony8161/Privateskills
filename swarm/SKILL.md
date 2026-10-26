---
name: swarm
description: Run several independent agents on one question and turn their output into a conclusion you can trust - typed briefs, a manifest on disk, one output file per agent, vocabulary reconciliation, disagreements sorted into "same thing, different name" versus real conflict, and a challenge pass from a different model. Use this whenever the user wants multi-agent research, a market or technical investigation split across angles, a second opinion from several perspectives, "fan out", "have a few agents look into", or wants to know whether an AI-produced finding can be believed. Use it for startup validation research, competitor and pricing scans, architecture comparisons, and any question where one agent's confident answer is not enough.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - WebSearch
  - WebFetch
---

# swarm

A swarm is not trustworthy because it is large. It is trustworthy to the degree
that its members worked independently, its disagreements were handled honestly,
and something outside the swarm tried to break the result. Everything here exists
to build those three things in, because a confident swarm and a correct swarm are
different objects.

```
scout -> briefs (validated) -> N independent agents -> one file each
      -> reconcile -> verify -> challenge (different model) -> conclusion
```

## 1. Scout, then brief

Spend a few cheap calls learning the terrain before splitting it: what the
question really is, what the natural facets are, what is already known. Then use
the `brief` skill to write one validated brief per agent, each with a *different*
facet. Agents with no channel between them are the point; when separate workers
reach the same conclusion without coordinating, the agreement carries weight one
agent never could. (Shared model lineage still means shared blind spots, so
agreement is evidence, not proof. Step 5 exists for this.)

## 2. Write the manifest before dispatching

The recoverable state lives on disk, never in your head. Context gets summarised,
sessions end, agents crash.

```bash
python ~/.claude/skills/swarm/scripts/manifest.py init runs/<name> briefs/*.json
python ~/.claude/skills/swarm/scripts/manifest.py status runs/<name>
```

`init` writes `runs/<name>/manifest.json` listing every agent, its output path, and
its status (`pending`). `status` checks which output files exist and prints what
is still missing. After a crash, relaunch only those, not the whole swarm.

## 3. Dispatch and collect

Launch the agents with the Agent tool, in one message so they run concurrently,
using the rendered brief as each prompt. When they return, run `manifest.py
status` again. Count files, not reports: a worker that ran out of budget will
often not tell you it wrote nothing.

## 4. Reconcile

This is the real work and not cleanup. Agents routinely agree on a concept and
name it differently ("transport layer", "envelope", "wire format").

1. Pick one canonical vocabulary and translate every report into it.
2. Sort each disagreement into one of two bins:
   - **Name-level**: same claim, different words. Merge.
   - **Substance-level**: genuinely different findings. **Keep as an open
     question.** Never average them; an average of two different truths is a
     confident answer that is wrong in a new way.
3. Write `runs/<name>/synthesis.md` with the merged findings, the open questions
   listed separately, and which agent supported what.

## 5. Verify, then challenge

Run the `verify` skill on the synthesis before anything is concluded: sampled
citations re-fetched, defect claims reproduced. Citation accuracy in agent
reports is often only 40-80% and falls as tool-call counts rise, so verification
is the baseline here, not an extra.

Then challenge it with a **different lineage**, not a second copy of the same
model reading the same brief, which repeats the same blind spots. Give the
challenger one job: attack the reconciled result. A good challenge does not only
catch wrong answers; it adds conditions. The target shape of the final verdict is
"right under these conditions, breaks outside them." If a differently built
model is unavailable, use `pressure-test` as the structured adversary and say in
the report that the challenger shared your lineage.

## Output

```markdown
# <Question>

## Verdict
<Right under these conditions; breaks outside them.>

## What the agents agreed on independently
## Open questions (substance-level disagreements)
## What verification removed or downgraded
## Challenger's strongest objection, and how it changed the verdict
## Provenance
<agents, facets, output files, manifest path>
```

## Judgement

**Do not fan out a question that one careful agent can answer.** Swarms cost
roughly in proportion to their size and the benefit comes from independence of
facets, not headcount. Three to five distinct facets beats twelve overlapping ones.

**Treat unanimous output with suspicion if the briefs were similar.** Agreement
only means something if the agents could have disagreed.
