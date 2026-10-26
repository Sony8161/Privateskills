# forge/STATE.md template

Copy to `forge/STATE.md` in the project and keep it current. It is the single place
a new session reads to know where the project stands. Keep it short; link to the
detail instead of copying it.

```markdown
# Project state

**Project:** <name>
**Updated:** <YYYY-MM-DD>
**Current stage:** <0-7 and name>
**Next action:** <one concrete thing, and who does it>

## Gates
| Stage | Gate | Result | Date | Evidence |
|---|---|---|---|---|
| 0 Foundation | intent approved, hooks real | pass / fail / pending | | intent/ |
| 1 Discover | no Fatal, claims confirmed, first contact named | | | runs/<name>/synthesis.md |
| 2 Define | spec + requests + data categories | | | 01-<slug>.md |
| 3 Design | threat model, tenancy and auth named | | | security/REPORT.md (draft) |
| 4 Build | per slice: green, code-check not BLOCK, receipt | | | bay board |
| 5 Harden | no open Critical/High, unverified listed | | | security/REPORT.md |
| 6 Ship | code-check not BLOCK, ship gate green, rollback real | | | PR link |
| 7 Learn | lesson kept, kill criteria checked | | | RETRO.md |

## Open risks
<Anything known and unresolved. One line each, with owner.>

## Accepted risks
<Only what the user knowingly chose to proceed with. Quote their words. Add the
trigger that makes it worth revisiting.>

## Unverified
<Claims or findings not yet confirmed by running or fetching. Count: N.>

## Decisions
<Links to decision memos for one-way doors.>

## Rulings
<Calls made without asking, one per line: what, why, cost if wrong.>


## Review dates
- intent/SOUL.md: <date>   GRAVITY.md: <date>   INTENT.md: <date>
- security re-run due on: any change to auth, tenancy, payments, dependencies
```
