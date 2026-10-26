---
name: code-quality
description: Build code that stays good - a test-first loop for each small slice, the project's real lint, type-check and coverage commands detected and run, and a review pass for the things tests miss (error handling, silent failures, naming, duplication, complexity, dead code, secrets in logs). Use this whenever the user is writing or changing non-trivial code, starting a feature, asks for "clean", "production quality", "best practices", "refactor", "review my code", "add tests", or has code that works but feels fragile. Use it during the build, slice by slice, rather than once at the end, because quality added afterwards is mostly rework. Run it before the ship gate.
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
---

# code-quality

Quality is cheapest at the smallest scale: one slice, one behaviour, one test. The
failure this prevents is the large, mostly-working change nobody can fully read
and whose tests were written afterwards to match whatever the code already did.

## 0. Learn the project's own definition of passing

Do not guess commands. Detect them:

```bash
python ~/.claude/skills/code-quality/scripts/detect.py .
```

It reads `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml` and `Makefile`
and prints the likely test, lint, type-check and coverage commands. Confirm against
CI config (`.github/workflows`), which is the most reliable statement of what the
project actually requires. If there is no linter, formatter or type-checker, say so
and propose the smallest standard set for the stack. Match the existing code's
style and idiom; do not introduce a second convention.

## 1. Cut a slice

Pick the smallest piece that delivers one observable behaviour. If you cannot state
it in one sentence ("a user can request a magic link and receives it"), it is too
big; split it. If the work arrived through the `bay` skill, the request's "done
when" line is the slice's acceptance test.

## 2. Red, green, refactor

1. **Write the failing test first** and run it. It must fail *for the right
   reason*; a test that fails on a typo proves nothing. This is how you learn the
   test can fail at all.
2. **Write the least code that passes.** Resist building the next slice.
3. **Refactor with the tests green**: rename, extract, delete duplication. Run the
   tests after each step.

For deeper guidance on the loop itself, the installed `superpowers:test-driven-development`
and `ecc:tdd-workflow` skills apply; use them when the slice is tricky. Write tests
that assert behaviour a user or caller would care about, not the shape of the
implementation, so a refactor does not break them for no reason.

## 3. Quality bar for every slice

Check these before calling a slice done. Each exists because it is where
otherwise-passing code goes wrong later.

- **Errors are handled where they can be handled, and surface where they cannot.**
  No empty `catch`/`except`, no swallowed exception that returns a plausible
  default. A silent failure is worse than a crash because nobody notices it.
- **Validate at the boundary.** Input from users, files, networks and other
  services is checked once, at the edge, with clear errors. Internals can then
  trust their types.
- **Names say what things are.** If you need a comment to explain what a name
  means, rename it. Comments explain *why*, not *what*.
- **Functions do one thing** and fit on a screen. Deep nesting and long parameter
  lists are the signal to split, not to comment.
- **No duplication that would have to change together.** Three similar lines is
  fine; the same business rule in three places is a future bug.
- **No dead code, no commented-out blocks, no debug prints.** Version control
  remembers.
- **Types or schemas where the language supports them**, kept honest: no blanket
  `any`/`# type: ignore` to silence a real problem.
- **Logging has no secrets or personal data**, and enough context to debug without
  reproducing.
- **Dependencies are intentional.** Each new package has a reason; prefer the
  standard library and what the project already uses.
- **Public interfaces are documented** where a caller cannot infer behaviour from
  the signature: what it returns, what it raises, what it assumes.

## 4. Run the whole gate

Run, in order, the detected commands: format, lint, type-check, tests, coverage.
Treat a failure as a stop, not a note. Aim for the project's existing coverage
level; where none exists, cover the changed lines and every branch that handles an
error. Coverage is a floor that shows what is untested, not proof that the tested
code is right.

Then apply the `verify` skill's test check: temporarily revert the production
change and confirm the new test **fails**. A test that passes without the change
is decoration.

## 5. Read it as a stranger

The `code-check` skill packages this step as a verdict (mechanical scan, gates,
five-lens read, independent reviewers, verified findings); run it for anything
non-trivial. What follows is the quick version.

Before handing off, read your own diff as a reviewer who did not write it. Then,
for non-trivial changes, delegate a fresh-eyes review to the matching reviewer
that is installed: `ecc:python-reviewer`, `ecc:typescript-reviewer`,
`ecc:go-reviewer`, `ecc:rust-reviewer` and so on, or `ecc:code-reviewer` for any
language. Give it the diff, not your conclusion, so it is not anchored on yours.
Judge each finding on its merits; fix the real ones, and record a refuted one in
`verification/refuted.md`.

If this slice touches authentication, authorization, payments, user data, file
uploads or external input, run the `security` skill on it now, not at the end.

## 6. Hand off

If a bug appears that you cannot explain in one sentence, stop patching and use
`investigate`. When the slice is done, deliver it through `bay` with a receipt that
says exactly what you ran, and let `ship` run the final merge gate.

## Report

End with a short factual status: commands run and their results, tests added,
coverage of the change, review findings fixed versus declined, and anything not
checked. "All green" is only a claim you may make about commands you actually ran.
