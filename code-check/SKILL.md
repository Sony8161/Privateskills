---
name: code-check
description: Check a code change before it merges and give a verdict on whether it is clean and secure - a diff-level scan for leftovers, secrets, risky patterns and complexity, the project's own lint, type and test commands, a five-lens read (correct, secure, simple, tested, maintainable), independent reviewer agents, and every finding verified before it can block. Ends in PASS, PASS WITH NOTES or BLOCK. Use this whenever the user says "check my code", "review this", "is this clean", "is this secure", "lint it", "code quality check", "before I merge", "audit this diff", or finishes a slice, feature or fix. Also run it at the end of every build slice and again before the ship gate, even if the user did not ask, because a change is cheapest to fix while it is still small.
allowed-tools:
  - Read
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - Skill
---

# code-check

A verdict, not a pile of observations. The failure to avoid is a long review that
buries the one real problem under twenty nitpicks, or the opposite: a green checkmark
that only means nobody looked closely. Every finding either gets verified or gets
labelled as unverified, and only verified problems can block.

## 1. Fix the change set

Decide what is under review and say it:

- Uncommitted work (default), or `--staged`.
- A branch: `--base main` (or the repo's default branch).
- A single commit: `--base HEAD~1`.

Check only what changed. Old problems matter, but they are a separate cleanup, and
mixing them in makes every review unfinishable.

## 2. Mechanical pass (cheap, run first)

```bash
python ~/.claude/skills/code-check/scripts/check.py .            # add --base main for a branch
python ~/.claude/skills/code-quality/scripts/detect.py .          # the project's own gate commands
```

`check.py` looks only at **added lines**: debuggers and focused tests left in
(BLOCK), TODOs, debug output, suppressed linters, empty catches, skipped tests,
secrets and risky sinks (reusing the `security` skill's rules), over-long or deeply
nested Python functions, source changed with no test changed, oversized diffs, and
dependency or sensitive-path changes.

Then **run the commands `detect.py` lists**: format check, lint, type-check, tests.
A failing gate is a BLOCK. If the change touched a manifest or lockfile, or this is
the pre-ship run, also run:

```bash
python ~/.claude/skills/security/scripts/audit.py .
```

Treat a `MISSING` scanner as a stated gap in the report, not as a pass.

## 3. Read it through five lenses

Read the changed code and the code around it, not only the diff. For each lens, ask
the question and look for the specific thing:

1. **Correct.** Does it do what the request asked? Edge cases: empty, null, huge,
   duplicate, concurrent. Off-by-one, wrong comparison, unhandled error path, a
   state that can be reached but not left.
2. **Secure.** Which of the change's inputs does an outsider control? Follow them to
   where they are used. Authorization on every new route (not just login), tenant
   scoping on every new query, output encoding, injection sinks, secrets, new
   dependencies. Use `security/references/checklist.md` for the surfaces touched.
3. **Simple.** Walk the ladder before accepting new code: does this need to exist at
   all? does the codebase already have it? does the standard library or platform
   cover it? does an already-installed dependency cover it? can it be shorter without
   becoming clever? Flag reinvented utilities, a new dependency for a few lines,
   abstractions with one caller, and flexibility nobody asked for. **Never trade away
   validation, error handling, security or accessibility to make code shorter.**
4. **Tested.** Is there a test that would fail if this behaviour broke? Does it
   assert behaviour rather than mirror the implementation? Were any tests deleted,
   skipped or loosened to get green? (Apply `verify` section C if in doubt: revert the
   change and confirm the test fails.)
5. **Maintainable.** Names that say what things are, one job per function, no
   duplicated business rule, no dead or commented-out code, comments that explain
   *why*, logging free of secrets and personal data, consistent with the surrounding
   style.

## 4. Bring in independent readers

Your own pass has blind spots. For anything beyond a trivial change, send the **diff,
not your conclusions**, to two or three reviewers chosen for the change (running all
of them wastes money and produces overlap). Launch them in parallel:

| Change involves | Reviewer |
|---|---|
| Any code | `ecc:code-reviewer` |
| Python / Django / FastAPI | `ecc:python-reviewer` / `ecc:django-reviewer` / `ecc:fastapi-reviewer` |
| TypeScript / JavaScript / React / Vue | `ecc:typescript-reviewer` / `ecc:react-reviewer` / `ecc:vue-reviewer` |
| Go / Rust / Java / Kotlin / C++ / C# / PHP / Swift | the matching `ecc:*-reviewer` |
| Auth, input, secrets, endpoints | `ecc:security-reviewer`, plus the built-in `security-review` skill |
| Error handling, retries, fallbacks | `ecc:silent-failure-hunter` |
| SQL, schema, migrations | `ecc:database-reviewer` |
| Tests | `ecc:pr-test-analyzer` |
| Complexity and reuse | `ponytail-review`, **only if the user has it installed** |

Never install a third-party skill or plugin on your own. If a listed reviewer is not
installed, say so and continue.

## 5. Verify before anything can block

Merge everything (mechanical hits, your read, reviewer output) into one list and
dedupe. Then for each item that would change the verdict:

- Apply the `verify` skill, section B: reproduce the failure or run the check. For a
  suspected vulnerability, use the `security` skill's playbook against a local copy.
- Mark it **certain** (you reproduced it or can point at the contradiction) or
  **suspected** (depends on something you could not check).
- Drop noise. A style preference that no one stated, a generic risk that applies to
  all code, and an objection you cannot tie to a mechanism are not findings. If a
  refuted claim might come back, add it to `verification/refuted.md`.

Reviewers inflate. Expect to remove a good share of what they return; that is the
step working, not wasted effort.

## 6. Verdict

| Verdict | When |
|---|---|
| **BLOCK** | A confirmed secret, a confirmed vulnerability, a failing format/lint/type/test gate, a newly focused or skipped test, an unexplained failing test, or a confirmed correctness bug |
| **PASS WITH NOTES** | Everything gates green, and certain findings remain that are worth fixing but not worth stopping for |
| **PASS** | Gates green, nothing confirmed, and you state what was and was not checked |

Report in this shape, short:

```markdown
## Verdict: <BLOCK | PASS WITH NOTES | PASS>
**Reviewed:** <change set and size>   **Gates:** <commands run and results>

### Blockers (confirmed)
- <file:line>: <what happens, the input that triggers it, the fix>

### Worth fixing (certain)
- ...

### Suspected (unverified)
- <claim> - <what would confirm it>

### Not checked
<tools missing, areas out of reach, what no automated check can see>
```

Never say "all clean" for something you did not run. If a scanner was missing or a
reviewer was not installed, that goes under **Not checked**.

## 7. Fix and re-check

Fix blockers through the `code-quality` loop (failing test first for bugs), then
re-run steps 2 and 5 on the new diff. If a failure cannot be explained in a sentence,
stop patching and use `investigate`. When the verdict is PASS or PASS WITH NOTES,
paste it into the PR body's "How verified" section so `ship` can quote it.
