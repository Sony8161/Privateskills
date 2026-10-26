# Automated scanning: CVEs, code, secrets, containers, supply chain

The point of automation is coverage you cannot get by reading: every dependency
checked against known vulnerabilities, every commit checked for secrets, every pull
request checked before it merges. The point of the rest of this skill is to separate
what the tools say from what is true. Tools produce leads; step 4 of `SKILL.md`
turns leads into findings.

## 1. The scan layers, and what each one catches

| Layer | Catches | Tools (use what fits the stack) |
|---|---|---|
| Dependencies (SCA) | Known CVEs in libraries you use, direct and transitive | `osv-scanner`, `npm audit` / `pnpm audit`, `pip-audit`, `cargo audit`, `govulncheck`, `trivy` |
| Static analysis (SAST) | Dangerous patterns in your own code: injection, unsafe deserialization, weak crypto | `semgrep`, `bandit` (Python), CodeQL (in CI) |
| Secrets | Keys and tokens in files and git history | `gitleaks`, GitHub secret scanning with push protection |
| Containers and IaC | Vulnerable base images, root containers, open storage, risky Terraform/Kubernetes settings | `trivy` (`image`, `config`), `checkov` |
| Licenses and provenance | Unexpected licenses, tampered or typosquatted packages | `dependency-review`, SBOM tooling |
| Dynamic (DAST) | Real behaviour of the running app | `pentest-playbook.md`, OWASP ZAP baseline against localhost |

No single tool covers all of it, and two tools in one layer disagree often enough to
justify running both. `osv-scanner` plus the ecosystem's own auditor is a good pair.

Run everything that is installed with:

```bash
python ~/.claude/skills/security/scripts/audit.py .
```

It saves raw output under `security/scans/`, prints one status per tool, and lists
tools that apply but are not installed. **A missing tool is a coverage gap you must
report, not a pass.** Offer to install the missing ones, and ask first; installing
scanners is the user's call. Suggested installs: `pip install pip-audit bandit
semgrep`, the `osv-scanner`, `gitleaks` and `trivy` releases from their project
pages, `go install golang.org/x/vuln/cmd/govulncheck@latest`, `cargo install
cargo-audit`.

Data note: dependency scanners send package names and versions to public
vulnerability databases. They do not send your source. `semgrep --config auto`
downloads rules from the Semgrep registry; the script turns telemetry off.

## 2. Triage a CVE: severity is not risk

A scanner's severity label is where triage starts. Decide with these, in order:

1. **Is it on the CISA Known Exploited Vulnerabilities (KEV) list?** Actively
   exploited in the wild outranks everything else.
2. **Is the vulnerable code reachable in your product?** A flaw in a function you
   never call, or in a dev-only tool that never ships, is lower priority than the
   same flaw on a request path. Show reachability; do not assume it.
3. **How likely is exploitation?** EPSS gives a probability; high CVSS with a very
   low EPSS and no reachable path is usually not tonight's problem.
4. **What does exploitation give an attacker here?** Read the advisory: needs
   authentication, needs local access, needs unusual configuration?
5. **Is a fix available, and what does upgrading break?**

Suggested default response times, to adjust per product and written into the
report so they can be audited:

| Situation | Target |
|---|---|
| Reachable, on KEV or with a public exploit | Fix or mitigate within 1-2 days |
| Reachable Critical or High | Within 7 days |
| Reachable Medium | Within 30 days |
| Not reachable, or Low | Next planned upgrade; record why |

Rules that save pain:

- **Do not run `npm audit fix --force` (or any forced upgrade) blindly.** It may
  jump a major version outside your declared range, as it proposes for old
  `lodash`. Upgrade deliberately, run the tests, read the changelog.
- **Transitive dependency?** Upgrade the parent that pulls it in; if none exists,
  use an override (`overrides` in npm, `resolutions` in yarn/pnpm, a constraints
  file for pip) and record that it is a temporary patch.
- **No fix exists?** Mitigate (disable the feature, validate input, add a WAF rule),
  note the mitigation, and set a review date. If you decide the risk is acceptable,
  write who decided, why and until when in the report's accepted-risk section.
- **Not exploitable here?** Record it in `verification/refuted.md` with the reason,
  so the same alert is not re-investigated every week.
- Re-scan after the fix. A fix you did not re-scan is a hope.

Primary sources for advisories: GitHub Advisory Database (GHSA), OSV, the vendor's
own bulletin, and NVD. They sometimes disagree on affected versions; trust the
vendor and the advisory text over a summary.

## 3. Supply-chain hygiene

- **Lockfiles committed and honoured**: `npm ci`, `pip install --require-hashes`
  where practical, `cargo build --locked`. CI should fail if the lockfile is stale.
- **Look before you add a package**: age, maintainers, downloads, repository link,
  and a name that is not one letter off a popular package (typosquatting).
- **Install scripts** run code at install time. Prefer `--ignore-scripts` in CI
  jobs that do not need them.
- **Pin GitHub Actions to a full commit SHA**, not a moving tag, and keep them
  updated with Dependabot. Give workflows the least token permissions they need.
- **Protect the publishing path**: MFA on registry and cloud accounts, no
  long-lived tokens in CI where short-lived or OIDC credentials exist, and package
  provenance if you publish.
- **Keep an SBOM per release** so that when a new CVE is announced you can answer
  "are we affected?" in minutes: `syft dir:. -o cyclonedx-json > sbom.json`, then
  `grype sbom:sbom.json`; `trivy fs --format cyclonedx .` is an alternative.

## 4. Containers and infrastructure as code

- Small, maintained base image, pinned by version or digest; rebuild regularly.
- Run as a non-root user; no secrets in image layers or build args; copy only what
  the app needs.
- Scan the built image (`trivy image <name>`) and the config (`trivy config .`, or
  `checkov -d .` for Terraform/Kubernetes). Look for public buckets, open security
  groups, wildcard IAM and unencrypted storage.

## 5. Make it continuous: pre-commit and CI

**Pre-commit secret check**, so a key never reaches history. With gitleaks installed:
`gitleaks git --pre-commit --staged` (older versions: `gitleaks protect --staged`),
wired through a git hook or the `pre-commit` framework. A secret that reaches a
remote must be rotated, not just deleted.

**GitHub settings to turn on** (availability depends on the repository's plan;
check): Dependabot alerts and security updates, secret scanning with push
protection, code scanning (CodeQL), branch protection requiring review and passing
checks.

**`.github/dependabot.yml`**

```yaml
version: 2
updates:
  - package-ecosystem: "npm"          # add one block per ecosystem you use
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

**`.github/workflows/security.yml`** (a starting point; set the CodeQL `languages`
for your stack, and **replace every `@vX` with the full commit SHA of the current
release**, verifying the version first, because tags can move):

```yaml
name: security
on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"      # weekly, so new CVEs in old code are caught

permissions:
  contents: read

jobs:
  dependency-review:          # blocks risky new dependencies on pull requests
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@vX
      - uses: actions/dependency-review-action@vX
        with:
          fail-on-severity: high

  codeql:                     # static analysis of your own code
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@vX
      - uses: github/codeql-action/init@vX
        with:
          languages: javascript-typescript    # python, go, java-kotlin, ruby, ...
      - uses: github/codeql-action/analyze@vX

  trivy:                      # dependency CVEs, secrets, IaC and Dockerfile config
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@vX
      - uses: aquasecurity/trivy-action@vX
        with:
          scan-type: fs
          scanners: vuln,secret,misconfig
          severity: HIGH,CRITICAL
          ignore-unfixed: true
          exit-code: "1"
```

Make `security` a required status check on `main`. Findings that block a merge get
fixed or explicitly accepted in the PR; they are never silently dismissed.

## 6. What "very secure" honestly means

Scanning shrinks the known-bad surface: old vulnerable libraries, leaked secrets,
common code patterns. It does not find logic flaws such as broken authorization,
insecure design or business-logic abuse, which is why the threat model, the
checklist, the specialist reviewers and the authorized pen test exist. Say in the
report which layers ran, which were missing, and what none of them can see.
