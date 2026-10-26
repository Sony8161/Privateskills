#!/usr/bin/env python3
"""Diff-focused code checks: leftovers, risky patterns, secrets, complexity, test gaps.

Usage:
    check.py [path] [--base REF | --staged]

Looks only at lines you ADDED, so old problems do not drown out new ones.
    default        uncommitted changes (working tree vs HEAD) plus untracked files
    --base REF     working tree vs REF, e.g. --base main or --base HEAD~1
    --staged       only what is staged

Prints findings as `file:line  [rule]  snippet`, grouped BLOCK / REVIEW / INFO.
These are leads for a reviewer, not verdicts. Exit 1 if anything is BLOCK.
Reuses the secret and risky-sink rules from the security skill when installed.
Standard library only.
"""
import argparse
import ast
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

TEST_HINT = re.compile(r"(^|/)(tests?|__tests__|spec)(/|$)|(\.|_)(test|spec)\.|^test_", re.I)
SENSITIVE_PATH = re.compile(
    r"auth|login|session|token|passw|crypto|secret|payment|billing|stripe|webhook|upload|"
    r"admin|permission|policy|rbac|tenant|rls|migration|middleware|cors|csrf", re.I)
MANIFESTS = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "requirements.txt",
             "pyproject.toml", "poetry.lock", "uv.lock", "Cargo.toml", "Cargo.lock", "go.mod",
             "go.sum", "Gemfile", "Gemfile.lock", "composer.json", "composer.lock", "Dockerfile"}
SOURCE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".swift"}

# (rule, pattern, severity, extensions or None for any, skip_in_tests)
LINE_RULES = [
    ("focused-test", re.compile(r"\b(?:it|test|describe)\.only\(|\bfdescribe\(|\bfit\("), "BLOCK", None, False),
    ("debugger-left", re.compile(r"\bdebugger;|\bbreakpoint\(\)|pdb\.set_trace\(\)|binding\.pry"), "BLOCK", None, False),
    ("debug-output", re.compile(r"\bconsole\.(?:log|debug)\(|\bvar_dump\(|\bdd\("), "REVIEW", None, True),
    ("todo-left", re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b"), "REVIEW", None, False),
    ("check-suppressed", re.compile(r"eslint-disable|@ts-ignore|@ts-nocheck|#\s*type:\s*ignore|#\s*noqa|nosec|//\s*nolint|@SuppressWarnings"), "REVIEW", None, False),
    ("bare-except", re.compile(r"^\s*except\s*:\s*(?:#.*)?$|except\s+Exception\s*:\s*pass|except\s*:\s*pass"), "REVIEW", {".py"}, False),
    ("empty-catch", re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}"), "REVIEW", {".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".cs", ".php"}, False),
    ("skipped-test", re.compile(r"\bxit\(|\bxdescribe\(|\b(?:it|test|describe)\.skip\(|@pytest\.mark\.skip|@Disabled|t\.Skip\("), "REVIEW", None, False),
    ("hook-bypass", re.compile(r"--no-verify|--no-gpg-sign|SKIP=|HUSKY=0"), "REVIEW", None, False),
    ("any-type", re.compile(r":\s*any\b|\bas\s+any\b|<any>"), "INFO", {".ts", ".tsx"}, True),
]


def load_security_rules():
    """Return (secret_rules, sink_rules, redact_fn) from the security skill, or empty."""
    path = Path.home() / ".claude" / "skills" / "security" / "scripts" / "scan.py"
    if not path.exists():
        return [], [], None
    spec = importlib.util.spec_from_file_location("sec_scan", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return list(mod.SECRET_RULES), list(mod.SINK_RULES), mod.redact_match
    except Exception:
        return [], [], None


def git(root, *args):
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout


def added_lines(root, base, staged):
    """Map path -> [(line_number, text)] for lines added in the chosen change set."""
    cmd = ["diff", "-U0", "--no-color"] + (["--staged"] if staged else [base])
    rc, out = git(root, *cmd)
    if rc != 0:
        sys.exit(f"git diff failed (is this a git repo with a commit?): {out.strip()[:200]}")
    files, cur, ln = {}, None, 0
    for line in out.splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
            if cur:
                files.setdefault(cur, [])
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            ln = int(m.group(1)) if m else 0
        elif line.startswith("+") and cur:
            files[cur].append((ln, line[1:]))
            ln += 1
    if not staged:
        _, untracked = git(root, "ls-files", "--others", "--exclude-standard")
        for f in untracked.splitlines():
            try:
                text = (root / f).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            files[f] = list(enumerate(text.splitlines(), 1))
    return files


def python_complexity(root, path, changed_lines):
    """Flag changed Python functions that are long, branchy or deeply nested."""
    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    out = []
    branch_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.ExceptHandler, ast.IfExp, ast.comprehension)
    nest_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    def depth(node, d=0):
        deepest = d
        for child in ast.iter_child_nodes(node):
            deepest = max(deepest, depth(child, d + 1 if isinstance(child, nest_nodes) else d))
        return deepest

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            if not any(node.lineno <= n <= end for n in changed_lines):
                continue
            length = end - node.lineno + 1
            branches = sum(isinstance(n, branch_nodes) for n in ast.walk(node))
            nest = depth(node)
            if length > 60 or branches > 12 or nest > 4:
                out.append((node.lineno, "complexity",
                            f"{node.name}: {length} lines, {branches} branches, nesting {nest}; consider splitting"))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    files = {f: l for f, l in added_lines(root, args.base, args.staged).items() if l}
    if not files:
        print("No added lines found. For work already committed, try --base main or --base HEAD~1.")
        return 0

    secret_rules, sink_rules, redact = load_security_rules()
    if not secret_rules:
        print("note: security skill rules not found; secret and risky-sink checks skipped.\n")

    findings, notes = [], []
    added_total = sum(len(lines) for lines in files.values())
    src_files = [f for f in files if not TEST_HINT.search(f) and Path(f).suffix.lower() in SOURCE_EXTS]
    test_files = [f for f in files if TEST_HINT.search(f)]

    for f, lines in files.items():
        ext, is_test = Path(f).suffix.lower(), bool(TEST_HINT.search(f))
        for no, text in lines:
            if len(text) > 600:
                continue
            for rule, rx, sev, exts, skip_tests in LINE_RULES:
                if (exts is None or ext in exts) and not (skip_tests and is_test) and rx.search(text):
                    findings.append((sev, f, no, rule, text.strip()[:120]))
            for rule, rx in secret_rules:
                if rx.search(text):
                    findings.append(("BLOCK", f, no, f"secret:{rule}", redact(rule, text)))
            if not is_test:
                for rule, rx, exts in sink_rules:
                    if (exts is None or ext in exts) and rx.search(text):
                        findings.append(("REVIEW", f, no, f"risky-sink:{rule}", text.strip()[:120]))
        if ext == ".py" and not is_test:
            for no, rule, msg in python_complexity(root, f, {n for n, _ in lines}):
                findings.append(("REVIEW", f, no, rule, msg))
        if Path(f).name in MANIFESTS:
            notes.append(f"{f}: dependency or build file changed. Run security/scripts/audit.py "
                         "and vet any new package (age, maintainers, name close to a popular one).")
        if SENSITIVE_PATH.search(f) and not is_test:
            notes.append(f"{f}: security-sensitive surface touched. Run the security skill on this slice.")

    if src_files and not test_files:
        notes.append(f"{len(src_files)} source file(s) changed and no test file did. Is the new behaviour covered?")
    if added_total > 400:
        notes.append(f"{added_total} lines added. A change this size is hard to review; consider splitting it.")

    order = {"BLOCK": 0, "REVIEW": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x[0]], x[1], x[2]))
    for sev in ("BLOCK", "REVIEW", "INFO"):
        group = [x for x in findings if x[0] == sev]
        print(f"== {sev} ({len(group)})")
        for _, f, no, rule, snip in group:
            print(f"  {f}:{no}  [{rule}]  {snip}")
    print(f"\n== NOTES ({len(notes)})")
    for n in notes:
        print(f"  {n}")
    print(f"\nChecked {len(files)} file(s), {added_total} added line(s). These are leads, not verdicts: "
          "read each in context and verify before reporting.")
    return 1 if any(x[0] == "BLOCK" for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
