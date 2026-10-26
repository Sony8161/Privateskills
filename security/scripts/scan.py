#!/usr/bin/env python3
"""Quick static scan of your own repository for security leads.

Usage:
    scan.py [path] [--fail-on-secrets]

Prints `path:line  [rule]  snippet`. Secret values are redacted. Results are
LEADS to review, not confirmed vulnerabilities: reproduce each one before
reporting it. Standard library only.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist",
    "build", ".next", ".nuxt", "target", "vendor", ".tox", "coverage",
}
SCAN_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rb", ".php",
    ".java", ".kt", ".rs", ".cs", ".sh", ".yml", ".yaml", ".json", ".toml",
    ".env", ".ini", ".cfg", ".conf", ".tf", ".sql", ".html", ".vue", ".svelte",
}
MAX_BYTES = 1_000_000

SECRET_RULES = [
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe-live-key", re.compile(r"\b[sr]k_live_[A-Za-z0-9]{16,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("env-style-secret", re.compile(
        r"(?i)^\s*(?:export\s+)?[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|API_?KEY|PRIVATE_?KEY)[A-Z0-9_]*\s*=\s*[^\s'\"$#]{8,}\s*$")),
    ("generic-secret-assignment", re.compile(
        r"""(?ix)\b(?:api[_-]?key|secret|passwd|password|token|auth)[\w-]*\s*[:=]\s*
            ['"][A-Za-z0-9_\-/+=]{16,}['"]""")),
]

SINK_RULES = [
    ("eval-exec", re.compile(r"\b(?:eval|exec)\s*\("), {".py", ".js", ".ts", ".jsx", ".tsx", ".php", ".rb"}),
    ("shell-true", re.compile(r"shell\s*=\s*True|os\.system\s*\(|child_process\.exec\s*\("), {".py", ".js", ".ts"}),
    ("unsafe-deserialize", re.compile(r"pickle\.loads?\(|yaml\.load\((?![^)]*Safe)|marshal\.loads?\("), {".py"}),
    ("sql-string-build", re.compile(
        r"""(?i)(?:execute|query|raw)\s*\(\s*(?:f['"]|['"][^'"]*(?:%s|\{|['"]\s*\+))[^)]*\b(?:select|insert|update|delete)\b"""), {".py", ".js", ".ts", ".php", ".rb"}),
    ("html-injection-sink", re.compile(r"innerHTML\s*=|dangerouslySetInnerHTML|document\.write\(|v-html"), {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html"}),
    ("tls-verify-off", re.compile(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true"), None),
    ("weak-hash", re.compile(r"\b(?:md5|sha1)\s*\(|hashlib\.(?:md5|sha1)\b|createHash\(['\"](?:md5|sha1)"), None),
    ("insecure-random", re.compile(r"Math\.random\(\)|\brandom\.random\(\)"), {".py", ".js", ".ts", ".jsx", ".tsx"}),
    ("cors-wildcard", re.compile(r"""Access-Control-Allow-Origin['"]?\s*[:,]\s*['"]\*|origin\s*:\s*['"]\*['"]|allow_origins\s*=\s*\[\s*['"]\*"""), None),
    ("debug-enabled", re.compile(r"\bdebug\s*=\s*True\b|DEBUG\s*=\s*True"), {".py"}),
    ("jwt-none-or-no-verify", re.compile(r"""algorithms?\s*[:=]\s*\[?\s*['"]none['"]|verify_signature['"]?\s*[:=]\s*False|jwt\.decode\([^)]*verify\s*=\s*False"""), None),
]


def redact(snippet):
    return re.sub(
        r"""(['"])([A-Za-z0-9_\-/+=]{4})[A-Za-z0-9_\-/+=]{8,}(['"])""", r"\1\2****\3", snippet
    )


def redact_match(rule, line):
    if rule in ("private-key",):
        return "-----BEGIN ... PRIVATE KEY-----"
    if rule == "env-style-secret":
        name, _, value = line.partition("=")
        return f"{name.strip()}={value.strip()[:2]}****"
    out = re.sub(r"\b(AKIA|gh[pousr]_|xox[abprs]-|[sr]k_live_|sk-ant-)[A-Za-z0-9_-]+", r"\1****", line)
    return redact(out).strip()[:140]


def iter_files(root):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and (path.suffix.lower() in SCAN_EXT or path.name.startswith(".env")):
            try:
                if path.stat().st_size <= MAX_BYTES:
                    yield path
            except OSError:
                continue


def tracked_env_files(root):
    """Env files committed to git are a classic leak."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0:
        return []
    return [
        f for f in out.stdout.splitlines()
        if Path(f).name.startswith(".env") and not f.endswith((".example", ".sample", ".template"))
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--fail-on-secrets", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    self_path = Path(__file__).resolve()
    secrets, sinks = [], []

    for path in iter_files(root):
        if path.resolve() == self_path:
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = path.relative_to(root)
        for no, line in enumerate(lines, 1):
            if len(line) > 600:
                continue
            for rule, rx in SECRET_RULES:
                if rx.search(line):
                    secrets.append((rel, no, rule, redact_match(rule, line)))
            for rule, rx, exts in SINK_RULES:
                if (exts is None or path.suffix.lower() in exts) and rx.search(line):
                    sinks.append((rel, no, rule, line.strip()[:140]))

    tracked = tracked_env_files(root)

    print(f"== possible secrets ({len(secrets)}), values redacted")
    for rel, no, rule, snip in secrets:
        print(f"{rel}:{no}  [{rule}]  {snip}")
    print(f"\n== tracked env files ({len(tracked)})")
    for f in tracked:
        print(f"{f}  [env-file-in-git]  remove from history and rotate anything inside")
    print(f"\n== risky sinks ({len(sinks)}), review each in context")
    for rel, no, rule, snip in sinks:
        print(f"{rel}:{no}  [{rule}]  {snip}")
    print("\nThese are leads. Reproduce each before reporting it as a finding.")

    return 1 if args.fail_on_secrets and (secrets or tracked) else 0


if __name__ == "__main__":
    sys.exit(main())
