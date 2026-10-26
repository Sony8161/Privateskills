# Static review checklist

Work in this order: the categories at the top cause most real breaches. For each
item, the right move is to read the code path, not to trust that a framework
handles it. Category names follow the OWASP Top 10; numbering changes between
editions, so go by name.

## 1. Broken access control (read this first, always)

- Does every route that returns or changes data check **who is asking and whether
  they may touch this specific record**? Login alone is not authorization.
- IDOR/BOLA: any handler taking an id from the URL, body or query that loads a
  record without scoping by the caller's user or tenant. Grep for lookups by id
  alone (`findById`, `.get(id)`, `WHERE id = ?` with no owner column).
- Row-level security / tenant filters: present on every table, and no code path
  using a privileged connection that skips them.
- Admin and internal routes: authenticated and role-checked server-side, not
  hidden behind a client-side flag.
- Mass assignment: request bodies bound straight onto models, letting a user set
  `role`, `is_admin`, `tenant_id`, `price`.
- Client-supplied tenant/user ids trusted instead of derived from the session.

## 2. Authentication and session

- Passwords hashed with a slow, salted algorithm (argon2, bcrypt, scrypt), never
  plain, md5, sha1 or unsalted sha256.
- Reset and magic-link tokens: random, high entropy, single-use, short expiry,
  invalidated after use.
- Session/JWT: signature verified, algorithm pinned (reject `none`), expiry set,
  secret not hard-coded, logout actually invalidates.
- Login, reset and verification endpoints rate-limited; no user enumeration via
  different messages or timing.
- Cookies: `HttpOnly`, `Secure`, `SameSite` set appropriately.

## 3. Injection

- SQL: any query assembled by string concatenation or f-strings with request data.
  Parameterised queries or an ORM's safe API only.
- NoSQL operator injection (`{"$ne": ...}` accepted from JSON bodies).
- OS commands: user data reaching `exec`, `system`, `shell=True`, backticks.
- Template injection, path traversal (`../` in file names), header/log injection.
- XSS: user data rendered through `innerHTML`, `dangerouslySetInnerHTML`, `v-html`,
  unescaped template output. Check where output encoding is turned off.

## 4. Cryptographic failures and data exposure

- Secrets in source, config, client bundles, logs, or git history. Anything found
  must be rotated, not just deleted.
- Sensitive data encrypted in transit (TLS everywhere, certificate checks on) and
  at rest where it matters.
- API responses returning more fields than the client needs (password hashes,
  internal ids, other users' emails).
- Verbose errors and stack traces reaching users; debug mode on in production.
- Non-cryptographic randomness (`Math.random`, `random`) used for tokens or ids.

## 5. Insecure design and business logic

- Trust in client-side checks (price, quantity, discount, role) with no server
  re-validation. Negative amounts, zero, huge values, repeated submission.
- Race conditions on balance, inventory, coupon and one-time-use flows.
- Missing limits on expensive operations: file size, page size, export size,
  anything that calls a paid third-party API per request.
- Webhooks accepted without verifying the sender's signature.

## 6. Security misconfiguration

- Security headers (CSP, HSTS, `X-Content-Type-Options`, frame protection).
- CORS: no wildcard origin together with credentials; allow-list, not reflection.
- Default or example credentials, open admin panels, public storage buckets,
  overly broad IAM/service keys, `.env` committed.
- Dependency and container hardening: pinned versions, non-root container user.

## 7. Server-side request forgery and file handling

- Any feature that fetches a URL the user supplies (previews, imports, webhooks):
  blocks internal addresses (localhost, private ranges, cloud metadata), follows
  redirects safely, limits size and time.
- Uploads: type checked by content not only extension, size capped, stored outside
  the web root with generated names, never executed.

## 8. Vulnerable and outdated components

- Run the ecosystem audit (`npm audit`, `pip-audit`, `osv-scanner`, `cargo audit`).
- Triage by reachability: a CVE in a function you never call is lower priority than
  one on a request path. Lockfile committed; no wildcard version ranges for
  security-relevant packages.
- Supply chain: install scripts, typosquat-shaped package names, unpinned CI actions.

## 9. Logging and monitoring

- Security-relevant events logged (login failures, permission denials, resets,
  admin actions) with who/when/what.
- Logs contain no passwords, tokens, full card numbers or personal data.
- Someone would actually notice a spike in failures.

## 10. If the product contains an LLM

- **Prompt injection**: untrusted text (web pages, emails, uploaded files, other
  users' content) reaches the model alongside instructions. Assume it can try to
  redirect the agent.
- **Over-powered tools**: the agent can send email, run code, spend money or reach
  the database. Apply least privilege and a human confirmation for irreversible
  actions; enforce limits in code (deterministic), not in the prompt.
- **Data leakage**: model output rendered as HTML, links or markdown images that
  can exfiltrate data; one tenant's context visible to another's session.
- **Cost abuse**: no per-user caps on token or tool use.
