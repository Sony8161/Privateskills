#!/usr/bin/env python3
"""Run whichever real security scanners are installed against a project.

Usage:
    audit.py [path] [--only npm-audit,osv-scanner,...] [--strict] [--timeout SECS]

Detects the project's ecosystems, runs each applicable scanner that is installed
(dependency CVEs, secrets, static analysis, containers/IaC), saves each tool's raw
output to <path>/security/scans/<tool>.txt, and prints a summary table.

Status meanings:
    CLEAN     the tool ran and reported nothing. This is not proof of security.
    FINDINGS  the tool reported issues; read its output file and verify each one.
    ERROR     the tool failed to run properly; the result says nothing either way.
    MISSING   applicable here but not installed; this is a coverage gap.

Exit codes: 0 no findings; 1 findings; 2 when a tool errored, or with --strict when
a tool that applies is missing.
Nothing is installed or modified. Some tools contact public vulnerability
databases; only package names and versions are sent, not your source code.
Standard library only.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist",
    "build", ".next", "target", "vendor", ".tox", "coverage",
}


def inventory(root):
    """Collect the manifest/lock files and source extensions present."""
    names, exts = set(), set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            names.add(f)
            exts.add(Path(f).suffix.lower())
    return names, exts


def build_tools(root, names, exts):
    """Each tool: binary, applicability, command, exit codes meaning 'findings'."""
    has_git = (root / ".git").exists()
    req = next((n for n in sorted(names) if n.startswith("requirements") and n.endswith(".txt")), None)
    py_project = req or "pyproject.toml" in names or "setup.py" in names
    lockfiles = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "go.sum",
                 "poetry.lock", "Pipfile.lock", "uv.lock", "Gemfile.lock", "composer.lock"}
    any_dep_file = bool(lockfiles & names) or py_project or "go.mod" in names
    code_exts = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rb", ".php", ".java", ".kt", ".rs", ".cs"}
    py_exclude = ",".join(f"./{d}" for d in sorted(SKIP_DIRS))

    pip_cmd = ["pip-audit", "-r", str(root / req)] if req else ["pip-audit", str(root)]
    return [
        dict(name="npm-audit", binary="npm", applies="package-lock.json" in names,
             cmd=["npm", "audit"], cwd=root, findings={1},
             hint="ships with Node.js; needs a package-lock.json (run `npm install --package-lock-only`)"),
        dict(name="pnpm-audit", binary="pnpm", applies="pnpm-lock.yaml" in names,
             cmd=["pnpm", "audit"], cwd=root, findings={1}, hint="install pnpm"),
        dict(name="pip-audit", binary="pip-audit", applies=bool(py_project),
             cmd=pip_cmd, cwd=root, findings={1}, hint="pip install pip-audit"),
        dict(name="cargo-audit", binary="cargo-audit", applies="Cargo.lock" in names,
             cmd=["cargo-audit", "audit"], cwd=root, findings={1}, hint="cargo install cargo-audit"),
        dict(name="govulncheck", binary="govulncheck", applies="go.mod" in names,
             cmd=["govulncheck", "./..."], cwd=root, findings={3},
             hint="go install golang.org/x/vuln/cmd/govulncheck@latest"),
        dict(name="osv-scanner", binary="osv-scanner", applies=any_dep_file,
             cmd=["osv-scanner", "scan", "source", "-r", str(root)], cwd=root, findings={1},
             ok_extra={128}, fallback=["osv-scanner", "-r", str(root)],
             hint="https://google.github.io/osv-scanner/installation/ (covers many ecosystems at once)"),
        dict(name="gitleaks", binary="gitleaks", applies=True,
             cmd=["gitleaks", "detect", "--source", str(root), "--redact", "--no-banner"]
             + ([] if has_git else ["--no-git"]),
             cwd=root, findings={1}, hint="https://github.com/gitleaks/gitleaks (also scans git history)"),
        dict(name="semgrep", binary="semgrep", applies=bool(code_exts & exts),
             cmd=["semgrep", "scan", "--config", "auto", "--metrics=off", "--error", "--quiet", str(root)],
             cwd=root, findings={1}, hint="pip install semgrep (rules are fetched from the Semgrep registry)"),
        dict(name="bandit", binary="bandit", applies=".py" in exts,
             cmd=["bandit", "-r", str(root), "-q", "-x", py_exclude], cwd=root, findings={1},
             hint="pip install bandit"),
        dict(name="trivy", binary="trivy", applies=True,
             cmd=["trivy", "fs", "--scanners", "vuln,secret,misconfig", "--exit-code", "1",
                  "--quiet", str(root)], cwd=root, findings={1},
             hint="https://trivy.dev (dependencies, secrets, Dockerfile and IaC misconfig)"),
    ]


def run(cmd, cwd, timeout):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return None, f"timed out after {timeout}s"
    except OSError as exc:
        return None, f"could not run: {exc}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--only", help="comma-separated tool names")
    parser.add_argument("--strict", action="store_true", help="exit 2 on gaps or errors")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    root = Path(args.path).resolve()
    names, exts = inventory(root)
    wanted = set(args.only.split(",")) if args.only else None
    out_dir = root / "security" / "scans"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, gaps, errors, findings = [], [], [], []
    for tool in build_tools(root, names, exts):
        if wanted and tool["name"] not in wanted:
            continue
        if not tool["applies"]:
            rows.append((tool["name"], "N/A", "nothing for this tool to scan here"))
            continue
        resolved = shutil.which(tool["binary"])
        if not resolved:
            gaps.append(tool)
            rows.append((tool["name"], "MISSING", tool["hint"]))
            continue

        # Launch the resolved path: on Windows `npm` is really npm.cmd and a bare name fails.
        code, output = run([resolved] + tool["cmd"][1:], tool["cwd"], args.timeout)
        if code is not None and code not in tool["findings"] | {0} | tool.get("ok_extra", set()):
            if tool.get("fallback"):
                code, output = run([resolved] + tool["fallback"][1:], tool["cwd"], args.timeout)
        (out_dir / f"{tool['name']}.txt").write_text(output, encoding="utf-8")

        if code is None:
            errors.append(tool["name"])
            rows.append((tool["name"], "ERROR", output.splitlines()[0] if output else "failed"))
        elif code == 0 or code in tool.get("ok_extra", set()):
            rows.append((tool["name"], "CLEAN", f"see security/scans/{tool['name']}.txt"))
        elif code in tool["findings"]:
            findings.append(tool["name"])
            rows.append((tool["name"], "FINDINGS", f"exit {code}; read security/scans/{tool['name']}.txt"))
        else:
            errors.append(tool["name"])
            first = next((l for l in output.splitlines() if l.strip()), "")[:100]
            rows.append((tool["name"], "ERROR", f"exit {code}: {first}"))

    print(f"Scanned: {root}\n")
    for name, status, detail in rows:
        print(f"{name:14} {status:9} {detail}")

    print("\nCLEAN means the tool ran and found nothing. It is not proof of security.")
    if gaps:
        print(f"Coverage gaps ({len(gaps)}): applicable tools that are not installed. "
              "Install them or say plainly that this check was not done.")
    if errors:
        print(f"Errors ({len(errors)}): {', '.join(errors)}; those results say nothing either way.")
    if findings:
        print(f"Findings in: {', '.join(findings)}. Reproduce or confirm each before reporting it.")
    print("Tip: add security/scans/ to .gitignore if the output names vulnerable paths.")

    if findings:
        return 1
    if errors or (args.strict and gaps):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
