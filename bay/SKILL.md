---
name: bay
description: A durable, file-based handoff log between roles or agents (research to engineering, planner to builder, one session to the next) - requests and deliveries with stable IDs, an enforced lifecycle, receipts required before anything is marked delivered, inboxes, a status board, and traceability from a shipped item back to its request. Use this whenever work passes between sessions, agents, or people and could be lost or misremembered: "hand this off", "what's the status", "what did we agree", "pick up where we left off", multi-session builds, or a startup where one person plays several roles. Use it to replace "I think we decided that" with a record you can cite.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# bay

Agents and sessions do not share memory, so the record has to. This is a small,
deliberately boring message log: one append-only file, an explicit lifecycle, and
IDs that mean the same thing forever.

## Why it is built this way

**Stable IDs.** A database row number is a position, not an identity. Rebuild or
migrate the store and a citation like "see message 41" silently points somewhere
else. The rule: once an ID is written down outside the log, it must keep meaning
the same thing forever. So IDs are generated once, never reused, and the log is
append-only: the source of truth is the log, and any board or index is a view you
can rebuild from it.

**Receipts.** A delivery cannot be marked delivered without saying what was
verified. This one gate stops "done" from meaning "I stopped".

**Enforced transitions.** Legal state changes are checked when written, so the
board cannot drift into states that mean nothing.

## Messages

A **request** says: what to build, why it should exist, what done looks like.
A **delivery** says: what shipped, where it lives, what was verified, what remains
open. Both link to what they answer via `--ref`, so any shipped item traces back
through its delivery, its request, and the investigation behind it.

```
open -> accepted -> delivered -> verified -> closed
  \-> rejected          \-> accepted (rework)
```

## Commands

```bash
B="python ~/.claude/skills/bay/scripts/bay.py"

$B new request --thread auth --from founder --to claude \
   --title "Magic-link login" \
   --body "Build: ...  Why: ...  Done when: ..."
$B inbox claude                      # what is waiting for me (check at session start)
$B move REQ-xxxxxxxx accepted
$B new delivery --thread auth --from claude --to founder --ref REQ-xxxxxxxx \
   --title "Magic-link login shipped" --body "Shipped: ... Where: ... Open: ..."
$B move REQ-xxxxxxxx delivered --receipt "unit tests + manual login in browser, 2 gaps listed"
$B board                             # queued / active / done
$B show REQ-xxxxxxxx                 # full trace, with citation string
```

The log lives at `bay/log.jsonl` in the project. Commit it.

## Citing

When you refer to a message anywhere outside the log, cite it as the ID plus
thread, date and sender, which `show` prints for you:
`REQ-a1b2c3d4 (auth, 2026-10-25, founder)`. If an ID is ever damaged, the context
lets a search find it again.

## Judgement

**Keep requests under-specified on design on purpose.** Leave real design
decisions open and require the builder to take a position, ask questions, and
correct its own proposal before building. A request that dictates the design
removes the one review that catches a bad design cheaply.

**This is for handoffs, not chat.** If it would not matter in a week, it does not
belong in the log.

**Check the inbox at the start of every session** and the board before saying
anything about status. Memory of what is outstanding is the thing that fails.
