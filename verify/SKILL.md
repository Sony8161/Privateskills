---
name: verify
description: Check a claim before anyone relies on it - re-fetch sampled citations and confirm the source says what the report says, reproduce any claimed bug or vulnerability by running the code, and treat "tests are green" as plausibility rather than proof. Keeps a ledger of refuted claims so false alarms are not rediscovered. Use this whenever the user has AI-generated research, a review, an audit finding, a bug report, or a "this is broken" claim and is about to act on it, and whenever someone says "tests pass", "it works", "the agent says", "according to the report", or "I think there's a vulnerability". Use it before shipping a finding, not after.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebFetch
  - WebSearch
---

# verify

Confident output is wrong until a check says otherwise. That is not cynicism, it
is arithmetic: cited-source accuracy in agent reports has been measured at roughly
40-80% and drops as tool calls rise. So the pipeline does the doubting, instead of
relying on a person to feel suspicious at the right moment.

Three checks, depending on what kind of claim you hold.

## A. A factual claim with a citation

1. **Sample, don't skim.** Take every load-bearing claim plus a random handful of
   the rest. Load-bearing means a conclusion would change if it were false.
2. **Re-fetch each source** and find the sentence that supports the claim. The
   standard is that the source *says it*, not that the topic is nearby. A page that
   exists and a page that supports the claim are different things.
3. **Mark each one** `confirmed`, `partly` (source says less than the claim),
   `unsupported`, or `unreachable`. Unreachable is not confirmed.
4. If more than about a fifth of the sample fails, stop trusting the unsampled
   remainder and say so; the sample is a measurement of the whole.

## B. A claim about specific shipped code (bug, vulnerability, regression)

**No claim about a specific line goes anywhere until someone has run that code and
watched it fail.** Reading and reasoning produce suspicions; execution produces
findings. Many confident reports describe a path that is unreachable, a check
that exists one frame up, or input the framework already rejects.

1. Write the smallest input or test that should trigger the claimed failure.
2. Run it against the real code. Capture the output.
3. Failing as claimed: **confirmed**, attach the reproduction. Not failing:
   **refuted**, record why (what actually prevents it). Cannot run it here:
   **unverified**, and say what is needed. Never promote unverified to confirmed.

For a confirmed bug, hand off to `investigate` for the root cause and the
regression test. For a confirmed security issue, report through `security`.

## C. "The tests are green"

Passing tests are evidence the code does what the tests assert, which may be
little. Before trusting green:

- Does a test **fail without the change**? Revert the fix locally and run it. A
  regression test that passes before the fix tests nothing.
- Would these tests **catch the failure you're worried about**? Name one wrong
  behaviour that would still pass.
- Did you **run the thing** the way a user would? (This is step 4 of `ship`.)

## The ledger of refuted claims

Append every refuted or downgraded claim to `verification/refuted.md` with the
evidence that killed it:

```markdown
## <YYYY-MM-DD> <claim, one line>
**Source:** <agent / report / person>
**Verdict:** refuted | partly | unsupported
**Evidence:** <what you ran or fetched, and what it showed>
```

This is what stops the same false alarm from being rediscovered, re-reported and
re-investigated next month. Read it before verifying a claim that sounds familiar.

## Output

Return a short table of claims and verdicts, then the one-sentence consequence:
what can now be relied on, what cannot, and what is still unverified. Report the
unverified count even when it is uncomfortable, because the honest size of the
unknown is part of the answer.
