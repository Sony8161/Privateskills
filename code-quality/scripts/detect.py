#!/usr/bin/env python3
"""Detect a project's stack and print its likely quality-gate commands.

Usage:
    detect.py [project_dir]

Reads package.json, pyproject.toml, requirements.txt, go.mod, Cargo.toml and
Makefile. Prints suggestions only; confirm against CI config before relying on them.
Standard library only.
"""
import json
import re
import sys
from pathlib import Path


def js_commands(root):
    pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts", {})
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    runner = "pnpm" if (root / "pnpm-lock.yaml").exists() else (
        "yarn" if (root / "yarn.lock").exists() else "npm run")
    found = {}
    for gate, names in {
        "test": ["test", "test:unit"],
        "lint": ["lint"],
        "typecheck": ["typecheck", "type-check", "tsc"],
        "format": ["format", "prettier"],
        "coverage": ["coverage", "test:coverage"],
        "build": ["build"],
    }.items():
        for name in names:
            if name in scripts:
                found[gate] = f"{runner} {name}"
                break
    if "typecheck" not in found and "typescript" in deps:
        found["typecheck"] = "npx tsc --noEmit"
    if "lint" not in found and "eslint" in deps:
        found["lint"] = "npx eslint ."
    return "JavaScript/TypeScript", found


def py_commands(root):
    text = ""
    for name in ("pyproject.toml", "requirements.txt", "setup.cfg", "tox.ini"):
        if (root / name).exists():
            text += (root / name).read_text(encoding="utf-8", errors="ignore").lower()
    found = {}
    found["test"] = "python -m pytest" if "pytest" in text or (root / "tests").is_dir() else "python -m unittest discover"
    if "ruff" in text:
        found["lint"], found["format"] = "ruff check .", "ruff format --check ."
    elif "flake8" in text:
        found["lint"] = "flake8"
    if "black" in text and "format" not in found:
        found["format"] = "black --check ."
    if "mypy" in text:
        found["typecheck"] = "mypy ."
    elif "pyright" in text:
        found["typecheck"] = "pyright"
    if "pytest-cov" in text or "coverage" in text:
        found["coverage"] = "python -m pytest --cov --cov-report=term-missing"
    return "Python", found


def make_targets(root):
    path = root / "Makefile"
    if not path.exists():
        return {}
    targets = set(re.findall(r"^([A-Za-z0-9_.-]+):", path.read_text(encoding="utf-8", errors="ignore"), re.M))
    return {t: f"make {t}" for t in ("test", "lint", "check", "build", "fmt", "format") if t in targets}


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    detected = []
    if (root / "package.json").exists():
        detected.append(js_commands(root))
    if any((root / n).exists() for n in ("pyproject.toml", "requirements.txt", "setup.py")):
        detected.append(py_commands(root))
    if (root / "go.mod").exists():
        detected.append(("Go", {"test": "go test ./...", "lint": "go vet ./...",
                                "format": "gofmt -l .", "coverage": "go test -cover ./..."}))
    if (root / "Cargo.toml").exists():
        detected.append(("Rust", {"test": "cargo test", "lint": "cargo clippy -- -D warnings",
                                  "format": "cargo fmt --check", "build": "cargo build"}))

    if not detected:
        print("No known project files found. Ask the user how this project is built and tested.")
        return 1
    for stack, cmds in detected:
        print(f"== {stack}")
        for gate, cmd in cmds.items():
            print(f"  {gate:10} {cmd}")
    extra = make_targets(root)
    if extra:
        print("== Makefile targets (often the project's own entry points)")
        for gate, cmd in extra.items():
            print(f"  {gate:10} {cmd}")
    ci = root / ".github" / "workflows"
    print(f"\nCI config: {'present in .github/workflows, read it' if ci.is_dir() else 'none found'}")
    print("Missing a gate (no linter, no type-check, no tests)? Say so and propose the smallest set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
