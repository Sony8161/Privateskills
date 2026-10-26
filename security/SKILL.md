---
name: security
description: Find and prove vulnerabilities in code you own - threat model, static review against the OWASP Top 10, secrets and dependency scanning, and an authorized penetration test of your own running app (auth bypass, IDOR, injection, XSS, CSRF, SSRF, headers, rate limits), with every finding reproduced before it is reported, then a SECURITY report and a public disclosure policy. Use this whenever the user asks about security, vulnerabilities, a pen test, hardening, "is this safe", "can someone hack this", an auth or payment or multi-tenant feature, secrets in a repo, a dependency CVE, or before launching anything that takes user data. Trigger it before shipping any app that handles logins, personal data, or money, even if the user only said "review this". Only for systems the user owns or is explicitly authorized to test.
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

Use real tools when they are installed (check with `--version` before assuming):
`gitleaks` or `trufflehog` for secrets, `semgrep` for patterns, `bandit` for
Python, `npm audit` / `pip-audit` / `osv-scanner` for dependencies. If one is
missing, say so and offer to install it; do not silently skip the check or install
global tooling without asking.

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

## Findings
| ID | Title | Severity | Status | Where | Reproduction | Fix |
|---|---|---|---|---|---|---|
<Status: confirmed / fixed / refuted / unverified. Reproduction names the request
or test file.>

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
