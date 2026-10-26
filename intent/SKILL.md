---
name: intent
description: Set up a layered intent stack for a project or an AI agent - SOUL (identity and values), GRAVITY (the founder's priorities and trade-offs), INTENT (decision heuristics for when instructions run out), and CLAUDE.md (operational rules) - and sort every rule into advisory, deterministic (hook or permission), or structural (required output section). Use this whenever the user starts a new project or startup, wants Claude or an agent to "know how I think", keeps repeating the same corrections, asks how to make an agent behave consistently, wants to write or clean up a CLAUDE.md, or asks what should be a hook versus an instruction. Use it at the start of a build, before specs exist, because everything later inherits it.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# intent

An instruction tells an agent what to do. Intent tells it what to do when the
instructions run out, which is most of the time. A single big system prompt mixes
the two with things that change weekly, so you cannot update one without
destabilising the rest. The fix is layers, each on its own clock.

## The stack

| File | Holds | Changes |
|---|---|---|
| `SOUL.md` | Identity: how the agent thinks, its voice, its values | Once or twice a year |
| `GRAVITY.md` | The founder's pull on the system: priorities, patterns, how they weigh trade-offs. A set of tendencies, not a biography | Quarterly or less |
| `INTENT.md` | Decision heuristics for the gaps, e.g. "simplicity is the cardinal virtue", "proceed on HOW, ask on WHAT" | Every few months |
| `CLAUDE.md` | Operational rules: what to read at start, tool usage, output format, commands | Weekly |

Keep them separate in files. The reason is not tidiness: a Tuesday tweak to an
output format should not be able to rewrite the agent's values.

Read `references/templates.md` for a starter of each file and the questions that
fill them in.

## Step 1: Interview, briefly

Ask in one `AskUserQuestion` batch, not a drip. You are after tacit knowledge:
the thing you would tell a new hire on day one that is not in the handbook.

1. What do you do when two good options conflict (speed vs. polish, scope vs.
   deadline, cost vs. quality)? Give one real example.
2. What have you had to correct an AI or a teammate on more than twice?
3. What is the one thing that must never happen without asking you first?
4. Where should it just proceed and tell you after?

Do not invent a personality. Draft only from what they said, quote their phrasing
where you can, and mark any line you inferred so they can strike it.

## Step 2: Classify every rule by how it is enforced

This is the part that makes the stack work. For each rule, ask what happens if the
agent ignores it:

- **Advisory**: guidance the model interprets. Tone, priorities, norms. A strong
  competing signal can override it, which is fine for these.
- **Deterministic**: a wall the system enforces. Hooks that fire before a tool
  runs, permission gates, tool restrictions. Use for irreversible actions,
  secrets, money, anything where "the model usually complies" is not good enough.
- **Structural**: a required slot in the output. A behaviour that has no slot
  quietly does nothing as prose. "Consider why you might be wrong" scored zero in
  testing; a mandatory "what would prove me wrong" section before the
  recommendation passed.

Match enforcement to stakes. Over-enforcing turns the agent into a brittle script
with extra steps; relying on advice for security boundaries produces an agent you
cannot fully trust. Output the classification as a table in `INTENT.md`, and for
every deterministic rule, offer to write the actual hook or permission (use the
`update-config` skill) rather than leaving it as a sentence.

## Step 3: Set the trust level per task type

| Level | Meaning |
|---|---|
| 1 | Verify every action |
| 2 | Supervise the critical actions, let the rest flow |
| 3 | Act autonomously, audit periodically |
| 4 | Trusted colleague, no routine checking |

Record the level for each kind of work (writing code, running migrations, sending
email, spending money). New work starts at 1 or 2. Moving up is a decision that
needs evidence from `agent-evals`, not a feeling.

## Output

Write the files to `intent/` at the project root, with a pointer at the top of the
project's `CLAUDE.md` telling sessions to read them. End by telling the user the
review dates: encoded intent goes stale as preferences change, and that drift is
silent. Put the next review for each layer in the file header.

## Known limits

Say these plainly when relevant: there is no formal measure of intent alignment,
independently engineered agents drift out of coherence with each other, and a
rule that was right last year may be wrong now. The stack reduces these; it does
not remove them.
