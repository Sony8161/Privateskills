---
name: security
description: Find and prove vulnerabilities in code you own - threat model, static review against the OWASP Top 10, automated scanning for known CVEs in dependencies, code, secrets, containers and infrastructure (npm audit, pip-audit, osv-scanner, semgrep, gitleaks, trivy and more, plus a CI workflow), and an authorized penetration test of your own running app (auth bypass, IDOR, injection, XSS, CSRF, SSRF, headers, rate limits), with every finding reproduced before it is reported, independent second opinions from specialist reviewers, a compliance-readiness check for a small SaaS (GDPR, US privacy laws, SOC 2 and ISO 27001 readiness, questionnaires, AI governance), then a security report and a public disclosure policy. Use this whenever the user asks about security, vulnerabilities, a pen test, hardening, "is this safe", "can someone hack this", an auth or payment or multi-tenant feature, secrets in a repo, a dependency CVE, or before launching anything that takes user data. Trigger it before shipping any app that handles logins, personal data, or money, even if the user only said "review this". Only for systems the user owns or is explicitly authorized to test.
effort: high
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebFetch
  - WebSearch
  - AskUserQuestion
---

# security

The goal is a short list of vulnerabilities that are **real, reproduced, and
fixed**, not a long list of things that look scary. Scanners and agents produce
suspicions in bulk and most are noise. A report that mixes the two trains people
to ignore it, so everything here funnels toward proof.

## Authorization comes first

Penetration testing is only legitimate against systems the user owns or has
written permission to test. Before any dynamic testing, establish and record:

1. **What is in scope**: repo, local dev server, a named staging URL.
2. **Who owns it** and that the user is authorized to test it.
3. **What is out of bounds**: production, third-party services (payment
   providers, auth vendors, cloud consoles), other people's accounts and data.

Default to **localhost or a staging copy with seeded fake data**. If the target is
production or anything the user does not control, stop and ask. Never test a host
you were not given. Static review of the code needs no special authorization and
is always the safe starting point.

Rules of engagement for dynamic testing: non-destructive only, no denial-of-service
or load-based attacks, no exfiltrating real data (prove access with one benign
record or a metadata count, then stop), no persistence, no lateral movement beyond
the stated scope. A proof of concept demonstrates the flaw; it does not exploit it
further.

## 1. Threat model (15 minutes, before reading code)

Write down, briefly:

- **Assets**: what an attacker wants (user data, credentials, money, admin access,
  the ability to impersonate).
- **Entry points**: every place outside input arrives (routes, forms, webhooks,
  file uploads, query params, headers, background job payloads, LLM prompts).
- **Trust boundaries**: where data crosses between user, server, database, third
  parties. Anything crossing inward is untrusted.
- **Actors**: anonymous, user, user-of-another-tenant, admin, a compromised
  dependency.

For multi-tenant systems, the first question is always: *what stops tenant A from
reading tenant B?* An unscoped query is a cross-tenant breach and outranks a dozen
smaller findings. Read the row-level policies and every query path that takes a
tenant or user id, especially those where the id comes from the request.

## 2. Static review

Run the quick scanner for leads, then read the code where leads cluster:

```bash
python ~/.claude/skills/security/scripts/scan.py .
```

It lists likely secrets (values redacted), risky sinks, and tracked env files. It
produces **leads, not findings**. Then work the checklist in
`references/checklist.md`, which maps the OWASP Top 10 to concrete things to grep
for and read. Prioritise by what the threat model says matters: authentication,
authorization, and anything touching money or tenant data come before cosmetic
header gaps.

`scan.py` is a quick grep with no dependencies. The real coverage comes from the
scanners in step 2b.

## 2b. Automated scanning: CVEs, code, secrets, containers

Run the real tools, not just the grep:

```bash
python ~/.claude/skills/security/scripts/audit.py .
```

It detects the project's ecosystems and runs every applicable scanner that is
installed: dependency CVEs (`osv-scanner`, `npm audit`, `pip-audit`, `cargo audit`,
`govulncheck`), static analysis (`semgrep`, `bandit`), secrets and history
(`gitleaks`), and dependencies, secrets and Dockerfile/IaC misconfiguration
(`trivy`). Raw output lands in `security/scans/`, and each tool gets one status:
`CLEAN`, `FINDINGS`, `ERROR` or `MISSING`.

How to read the result honestly:

- **`MISSING` is a coverage gap, not a pass.** List it in the report's scan-coverage
  table, offer to install the tool (ask first; installs are the user's call), and
  re-run. Do not describe the project as scanned for something no tool checked.
- **`CLEAN` means the tool ran and found nothing.** It is not proof of security, and
  it says nothing about logic flaws.
- **`ERROR` says nothing either way.** Fix the cause and re-run.
- **`FINDINGS` are leads.** Triage each CVE by exploitation status, reachability,
  likelihood and fix cost, not by the scanner's severity label alone, then
  reproduce or confirm per step 4. The method, default response times, supply-chain
  hygiene, SBOMs, container and IaC checks, and a ready CI workflow with
  Dependabot are in `references/scanning.md`.

Do not run forced upgrades (`npm audit fix --force`) blindly: they can jump a major
version. Re-scan after every fix. Then make the scans continuous: pre-commit secret
check, Dependabot, and a required `security` CI check on `main`, using the templates
in `references/scanning.md`.

## 3. Dynamic test of your own app

Only after the scope above is confirmed. Start the app locally with seeded fake
data and two test users in different tenants. Work through
`references/pentest-playbook.md`: authentication, authorization (IDOR/BOLA),
injection, XSS, CSRF, SSRF, file handling, rate limiting, session handling, and
business-logic abuse. Use `curl` and small scripts. OWASP ZAP in baseline mode
against localhost is a reasonable broad pass if installed.

## 4. Prove every finding

Apply the `verify` skill, section B, to each lead:

- Write the smallest request or test that demonstrates it. Run it. Capture the
  output.
- **Confirmed**: reproduced. **Refuted**: the code or framework prevents it; record
  why in `verification/refuted.md`. **Unverified**: you could not run it here; say
  what is needed. Never report an unverified item as confirmed.

Rate confirmed findings by **likelihood x impact** in this system, not by the
generic severity label of the bug class. A reflected XSS on an internal admin page
with no sensitive session is not the same as one on a public login page.

## 5. Fix and leave a test

For each confirmed finding: the smallest fix that removes the mechanism, plus a
regression test that fails without the fix (the `investigate` skill's step 5). Fix
the class, not the instance: grep for siblings of the same pattern.

## 6. Second opinions and specialist skills

Your own review has your own blind spots, so bring in independent readers. Give
each one the code or diff, not your conclusions, so they are not anchored on yours.
Treat everything they return as **leads** and send it through step 4 before it
reaches the report.

| When | Use | What it adds |
|---|---|---|
| Always, once your review is done | the built-in `security-review` skill | An independent pass over the pending changes with a different method |
| Auth, input handling, secrets, API endpoints | `ecc:security-reviewer` agent | Fresh-eyes review for injection, SSRF, unsafe crypto, exposed secrets |
| The stack is Django | `ecc:django-security` | Framework-specific settings, CSRF, ORM and middleware traps |
| The stack is Laravel | `ecc:laravel-security` | Mass assignment, policies, validation, config |
| The stack is Spring Boot | `ecc:springboot-security` | Spring Security config, method security, actuator exposure |
| The stack is Quarkus | `ecc:quarkus-security` | Quarkus auth and extension hardening |
| The stack is Perl | `ecc:perl-security` | Taint mode and injection patterns |
| Crypto, DeFi, token or AMM code | `ecc:defi-amm-security`, `ecc:llm-trading-agent-security` | Contract-level and trading-agent risks |
| Once per machine or project, about the AI tooling itself | `ecc:security-scan` | Audits Claude hooks, MCP servers, permissions and secrets in your setup |

There is no dedicated skill for every stack (JavaScript/TypeScript, FastAPI,
Rails, Go and others). For those, `references/checklist.md` and the framework's own
security documentation are the specialist; say that rather than implying a skill
covered it. If a listed skill is not installed, say so and carry on with the
checklist. Health-data compliance (HIPAA and similar) is out of scope for this
skill by design.

## 7. Compliance readiness (small SaaS)

Security findings are the evidence side of compliance. Close the loop in four
moves, using `references/compliance-saas.md`:

1. **Find the driver.** Where are users, who are the buyers, do you take cards, does
   the product contain AI, has anyone sent a questionnaire? The trigger table
   there picks the frameworks; do not pick by preference.
2. **Check the minimum viable program.** The twelve baseline controls, each with the
   evidence an auditor would ask for. Mark every one `evidenced`, `self-attested`,
   `gap` or `not assessed`, as `grc` does, and never upgrade a status to look
   better.
3. **Hand heavy frameworks to `grc`.** For SOC 2, ISO 27001, NIST CSF 2.0 or PCI DSS,
   run `grc` and feed it your confirmed findings as risk-register rows.
4. **Flag the legal questions once.** Whether GDPR, a US state law, COPPA or the EU AI
   Act applies is for counsel; map the controls and say so plainly.

Keep this proportionate. A two-person pre-revenue product needs the first handful of
baseline controls, a privacy notice and `SECURITY.md`, not an enterprise program.
Record deferred items with the trigger that makes them relevant.

## Output

Two files, because they have different audiences:

**`security/REPORT.md`** (private; keep out of public repos if it contains
reproduction detail):

```markdown
# Security assessment - <system>

**Date:** <YYYY-MM-DD>   **Scope:** <what was tested>   **Authorization:** <who approved>
**Method:** threat model, static review, dynamic test (local/staging), tools used

## Summary
<Counts by status and severity. The single most serious finding, first.>

## Scan coverage
| Layer | Tool | Result (clean / findings / error / missing / n/a) | Notes |
|---|---|---|---|
<Every layer in references/scanning.md, including the ones that did not run.
A missing tool is listed here as a gap, never omitted.>

## Findings
| ID | Title | Severity | Status | Where | Reproduction | Fix |
|---|---|---|---|---|---|---|
<Status: confirmed / fixed / refuted / unverified. Reproduction names the request
or test file.>

## Compliance readiness
<Driver, frameworks that apply and why, baseline controls by status
(evidenced / self-attested / gap / not assessed), deferred items with their
triggers, and the questions flagged for counsel. Date every claim.>

## Not tested
<What was out of scope or could not be reached, so the reader knows the edges.>

## Residual risk and accepted risk
<Anything knowingly left, with the owner and the trigger to revisit.>
```

**`SECURITY.md`** at the repo root is the *public* vulnerability-disclosure policy
that GitHub displays: how to report privately, what to expect, supported versions.
Keep it short and free of any finding details. Create it if absent.

## Close the loop

End by telling the user: findings by status, what is fixed versus open, and the one
thing to fix first. Feed confirmed items into `grc` as risk-register rows if a
framework is in play, and re-run this skill after any change to auth, tenancy,
payments, or dependencies. Security is a state you keep checking, not a stamp.
