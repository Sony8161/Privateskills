# Compliance for a small-business SaaS

What a small SaaS actually gets asked for, in the order it usually arrives. This
extends the `grc` skill, which already holds SOC 2, NIST CSF 2.0, ISO 27001 and
PCI DSS (`grc/references/frameworks.md`); read that for those. Health-data rules
(HIPAA and similar) are out of scope here by design.

**Two cautions that apply to everything below.** First, laws and standards get
revised and thresholds are adjusted; confirm the current version with a search
before putting any number or deadline in front of a customer. Second, whether a
law applies to this business is a legal determination. Map controls and flag the
question for counsel once, plainly. Do not decide it yourself.

## 1. Which frameworks apply? Let the trigger decide

| Trigger | What to do |
|---|---|
| Users or customers in the EU or UK | GDPR / UK GDPR (section 3) |
| Consumers in California or other US states | State privacy laws (section 3) |
| A customer sends a security questionnaire | Answer from the baseline in section 2; use CAIQ / SIG Lite style answers (section 4) |
| Mid-market or enterprise buyers ask for "SOC 2" | SOC 2 via `grc`; start evidence collection early |
| You take card payments | Keep card data off your systems: hosted checkout from a compliant processor, which usually means the lightest PCI self-assessment (SAQ A). Map with `grc` after confirming the data flow |
| Nothing has been asked yet | CIS Controls v8 Implementation Group 1 plus NIST CSF 2.0 as a self-assessment (section 2) |
| International enterprise customers, or a formal certificate is required | ISO 27001 (via `grc`), optionally ISO 27701 for privacy |
| The product contains AI features | AI governance (section 5) |
| Users may be under 13 | COPPA (US): parental consent and data limits; avoid the situation if possible |
| Selling to schools | FERPA considerations for student records (US); confirm with counsel |
| Selling to US federal agencies | FedRAMP is a large undertaking; treat as a later, funded decision |

The driver picks the framework, not preference. Doing nothing until a deal
demands it is a legitimate choice, but then the deal timeline becomes the audit
timeline, so decide on purpose.

## 2. The minimum viable security program

A small SaaS that does these twelve things well can answer most questionnaires and
passes most of the early work of SOC 2, ISO 27001 and CIS IG1 (roughly 56
safeguards in v8). Each row names the evidence an auditor will actually ask for.

| # | Control | Evidence to keep |
|---|---|---|
| 1 | MFA / SSO on email, source control, cloud, production, admin tools | Screenshot of enforced policy; list of accounts |
| 2 | Least-privilege access and a recurring access review | Dated review record; role list |
| 3 | Joiner / mover / leaver checklist, accounts removed fast | Completed offboarding tickets |
| 4 | Encryption in transit and at rest | Config or provider setting showing it |
| 5 | Backups with a tested restore | Restore-test record with date |
| 6 | Logging and alerting on security events | Log source list; sample alert |
| 7 | Vulnerability management: dependency and secret scanning, patch targets | Scanner output; ticket trail; `security/REPORT.md` |
| 8 | Secure development: PR review, protected main branch, CI tests | Branch protection settings; PR history |
| 9 | Change management through pull requests | The PRs themselves |
| 10 | Incident response plan, rehearsed once | The plan; tabletop notes |
| 11 | Vendor / subprocessor inventory with a review | Subprocessor list; review notes |
| 12 | Short written policies: security, acceptable use, data retention, plus yearly risk assessment and awareness training | The documents; training completion |

Also worth having early: asset inventory, device protection (disk encryption,
screen lock), and a continuity / disaster-recovery note. Keep evidence in one
folder with dates. Auditors test whether a control **operated over a period**, so
a control done once last week is weaker than a boring monthly record.

Scale to the stage. A two-person pre-revenue product should do rows 1, 4, 5, 7, 8
and 12 first and list the rest as deferred with the trigger (first employee, first
enterprise customer, first regulated customer data).

## 3. Privacy law

### GDPR and UK GDPR
Applies when you offer services to people in the EU/UK or monitor them, wherever
the company is based. The working basics:

- **Know your role.** For customers' end-user data you are normally a *processor*;
  for your own customers' account data you are a *controller*.
- **Record what you hold:** data map, purposes, lawful basis, retention, who it is
  shared with.
- **Contracts:** a data processing agreement with customers (you as processor) and
  with your own subprocessors. Keep a current subprocessor list.
- **Transfers outside the EU/UK:** use a valid mechanism (standard contractual
  clauses, or the EU-US Data Privacy Framework where the recipient is certified).
- **Individual rights:** access, deletion, correction, portability, with a
  process that can answer within one month.
- **Breach handling:** a controller notifies the supervisory authority within 72
  hours of becoming aware where required; a processor tells its customer without
  undue delay. Your incident plan must include this clock.
- **Risk assessments (DPIA)** for high-risk processing; an EU/UK representative if
  you have no establishment there and the rules require one.
- Penalties can reach the greater of EUR 20M or 4% of worldwide turnover. Treat
  that as the reason to keep records, not as an average outcome.

### US state privacy laws
California (CCPA/CPRA) and a growing number of states (Virginia, Colorado,
Connecticut, Texas and others) give residents rights to access, delete, correct and
opt out of sale or sharing. Most apply only above thresholds based on revenue or
volume of residents' data, so a small SaaS may be exempt today; **look up the
current thresholds** and write down the date you checked and the result. Where you
act as a service provider, the customer contract must carry the required
restrictions. Analytics and advertising cookies may need consent or opt-out.

## 4. Customer-facing trust artifacts

These close deals faster than certificates for an early company.

- **Public security page:** how data is protected, where it lives, who to contact.
- **`SECURITY.md` and `/.well-known/security.txt`** (RFC 9116): how to report
  vulnerabilities privately.
- **DPA template and subprocessor list**, kept current.
- **Pre-filled questionnaire answers** based on section 2 evidence, in the shape of
  the common formats (CSA CAIQ, SIG Lite, or the customer's own sheet). Answer from
  evidence only; "yes" without an artifact behind it becomes a liar's contract.
- **Pen-test summary letter:** an executive summary of `security/REPORT.md`
  (scope, date, headline result, remediation status). Never send reproduction detail.
- **Accessibility statement / VPAT** if selling to public-sector or large buyers;
  procurement often asks.

## 5. AI features

If the product calls an LLM or ships an agent:

- Frameworks to cite: **NIST AI RMF** (Govern, Map, Measure, Manage), **ISO/IEC
  42001** (AI management system), and the **EU AI Act** (risk tiers, obligations
  phased in over several years; confirm the current timetable and which tier your
  use falls into).
- Practical controls: an inventory of models and providers; a written position on
  whether customer data is used for training (default to no, and say so); transparency
  that users are dealing with AI; human oversight for consequential decisions; logs
  sufficient to investigate a bad output; tested defences against prompt injection
  and tool abuse (`pentest-playbook.md`, section 9); eval evidence from `agent-evals`.

## 6. Roadmap by stage

| Stage | Do |
|---|---|
| Pre-revenue | Rows 1, 4, 5, 7, 8, 12; a privacy notice; `SECURITY.md`; decide data locations |
| First paying customers | DPA, subprocessor list, access reviews, incident plan, pre-filled questionnaire |
| First enterprise ask | Choose SOC 2 Type I then II (or ISO 27001), run `grc`, start monthly evidence |
| International growth | GDPR program in full, transfer mechanism, local counsel |
| AI at the core | AI governance artifacts and recurring evals |

## 7. Tooling, and its limits

Compliance-automation platforms exist to collect evidence continuously and
generate policies; they cost money and suit teams heading for an audit. Free tools
cover much of the technical half: secret scanners (gitleaks), dependency scanners
(osv-scanner, npm audit, pip-audit), container and config scanners (trivy), and
static analysis (semgrep). A platform does not make a company compliant. Evidence of
controls operating does. Verify any vendor's claims about which framework versions
and criteria it supports.

## 8. Hand-off

Record the chosen framework, the driver, the date and the open gaps in
`forge/STATE.md`. Feed confirmed `security` findings into the `grc` risk register.
Refresh this assessment when you add a market, a data category, a subprocessor, or
an AI feature.
