---
name: disprove
description: Before delivering an answer where being wrong is costly, try hard to prove it wrong with real evidence and ship only the claims that survive - a ledger of load-bearing claims, attacks from two independent angles (run it, read the source, hunt for counter-evidence), verdicts of SURVIVED, SHAKY or BUSTED, and a rewritten answer that flags what could not be verified. Use this whenever the user says "are you sure", "double check", "make sure this is right", "I can't afford to be wrong", or asks for a technical fact, API or version behaviour, a number, a root-cause explanation, or a recommendation that rests on facts. Also use it on your own when you notice you are about to state something confidently from memory. Not for opinions, taste or creative work.
effort: high
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - WebSearch
  - WebFetch
---

# disprove

No skill can promise you never get a wrong answer. What this one does is turn
hidden errors into two visible kinds: claims that were corrected, and claims that
are flagged as unverified. That is a real improvement, and it is the honest version
of "never wrong".

The central design point: **re-reading your own reasoning mostly re-endorses it.**
A model asked to critique its own answer without new information tends to agree
with itself. What catches errors is outside evidence. So every attack below must
produce an *observation* (output of a command, a line of source, a primary
document), not another paragraph of thinking.

## 1. Draft privately

Write the answer for yourself first and do not show it yet. You are testing it, not
presenting it.

## 2. List the load-bearing claims

Pull out each claim a conclusion depends on: facts, numbers, names, API behaviour,
version-specific details, causal statements ("X happens because Y"), and negative
claims ("that function doesn't exist", "this isn't supported"). Next to each, mark
where you know it from:

- **ran it / read it this session**: strongest.
- **from memory**: prime suspect. Models are most wrong where they feel surest,
  and negatives and version details are the usual casualties.

Keep the list to the claims that matter, roughly seven at most. Attacking every
sentence is how this turns into noise.

## 3. Attack with evidence, from two different angles

For each important claim use two independent methods:

1. **Test it directly.** Run the code, the command or the query. Read the actual
   source, config, changelog or doc for the version in use. Open the file instead of
   recalling it.
2. **Try to break it.** Ask "if this were false, what would I see?" and go look. Find
   the edge input, the newer version, the conflicting primary source, the counter-example.
   Prefer primary sources (the code, official docs, the standard) over summaries.

Only run read-only, non-destructive commands, and never probe systems the user does
not own. If a claim cannot be tested safely, it is SHAKY, not SURVIVED.

## 4. Give each claim a verdict

| Verdict | Meaning | What you do |
|---|---|---|
| **SURVIVED** | Held up, and you can cite the evidence | State it plainly. No hedging on survivors |
| **SHAKY** | Could not verify either way | Say it is unverified and what would confirm it. Never present it as fact |
| **BUSTED** | Disproved | Correct or delete it; record the replacement |

## 5. Rewrite from the survivors

Build the final answer only from SURVIVED claims, with SHAKY ones flagged inline. If
a central claim was BUSTED, say so at the top: the first answer was wrong, here is
what changed. That sentence is the most valuable thing this skill produces.

## Output

```markdown
<The answer, with unverified statements marked inline.>

**Unverified:** <SHAKY claims and what would confirm each>

**Kill list:** <BUSTED claim -> what replaced it, and the evidence>
```

If everything survived, say that in one line and give the answer. Do not invent
objections to look rigorous.

## Guardrails against the opposite failure

- **Stop when each load-bearing claim has evidence or a SHAKY label.** One pass is
  normal; a second only if something central was busted.
- **Do not hedge what survived.** Doubt belongs only on SHAKY items. An answer wrapped
  in qualifiers is as useless as a wrong one.
- **Do not chase the unverifiable.** Mark it SHAKY and move on.
- **Match effort to stakes.** A one-line factual question gets a quick check; a
  recommendation that commits money or architecture gets the full ledger.

## Where it fits

`verify` checks claims made by others (agents, reports, tests); `pressure-test`
attacks a plan; this skill attacks **your own answer** before it leaves. In `forge`,
run it on stage 1 conclusions, on security findings before they are reported, and on
any root-cause claim in `investigate`. To make it a standing habit, add "every
technical recommendation ends with Unverified and Kill list sections" to
`intent/INTENT.md` as a structural rule and enforce it with
`agent-evals/scripts/check_sections.py`.

Idea credit: the mechanism is modelled on the `/crash-out` mode in the MIT-licensed
`claude-illegal-codes` repo. This is an independent write-up, adding the
evidence-only rule, the stop conditions and the integration with the rest of the
stack.
