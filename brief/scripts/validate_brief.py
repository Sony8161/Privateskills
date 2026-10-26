#!/usr/bin/env python3
"""Validate agent briefs before dispatch, and optionally render them to a prompt.

Usage:
    validate_brief.py briefs/*.json            # validate; exit 1 on any problem
    validate_brief.py --render briefs/a.json   # print the compiled prompt

Standard library only, so it runs anywhere Python does.
"""
import argparse
import json
import sys
from pathlib import Path

REQUIRED = [
    "id",
    "role",
    "goal",
    "facet",
    "criteria",
    "tool_quota",
    "write_budget",
    "pacing_instruction",
    "output_path",
]


MODELS = {"haiku", "sonnet", "opus", "fable", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def validate(brief):
    """Return a list of problems for one brief. Empty list means it is valid."""
    problems = []
    for key in REQUIRED:
        if key not in brief:
            problems.append(f"missing field: {key}")
        elif is_empty(brief[key]):
            problems.append(f"empty field: {key}")

    quota, budget = brief.get("tool_quota"), brief.get("write_budget")
    for name, value in (("tool_quota", quota), ("write_budget", budget)):
        if value is not None and not (isinstance(value, int) and value > 0):
            problems.append(f"{name} must be a positive integer, got {value!r}")
    if isinstance(quota, int) and isinstance(budget, int) and budget >= quota:
        problems.append(
            "write_budget must be smaller than tool_quota, "
            "otherwise nothing is left for research"
        )
    if isinstance(brief.get("criteria"), str):
        problems.append("criteria should be a list of checkable statements")
    if "model" in brief and brief["model"] not in MODELS:
        problems.append(f"model must be one of {sorted(MODELS)}, got {brief['model']!r}")
    if "effort" in brief and brief["effort"] not in EFFORTS:
        problems.append(f"effort must be one of {sorted(EFFORTS)}, got {brief['effort']!r}")
    return problems


def render(brief):
    quota, budget = brief["tool_quota"], brief["write_budget"]
    criteria = "\n".join(f"- {c}" for c in brief["criteria"])
    return f"""You are: {brief['role']}

GOAL
{brief['goal']}

YOUR FACET (work only this angle; other workers cover the rest)
{brief['facet']}

BUDGET
- Tool calls allowed: {quota}
- Reserve {budget} of them for writing your findings.
- Pacing: {brief['pacing_instruction']}

BEFORE YOU FINISH, check your work against these criteria:
{criteria}

OUTPUT
Write your findings to exactly one file: {brief['output_path']}
Cite a source for every factual claim. If you could not confirm something, say
so in the file instead of omitting it. Writing the file is the deliverable; a
run that ends without it has failed.
"""


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: cannot read as JSON ({exc})", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--render", action="store_true", help="print the compiled prompt")
    parser.add_argument("--dispatch", action="store_true",
                        help="print the model and effort to pass on each Agent call")
    args = parser.parse_args()

    failed = False
    seen_outputs = {}
    for path in args.files:
        brief = load(path)
        if brief is None:
            failed = True
            continue
        problems = validate(brief)
        out = brief.get("output_path")
        if out:
            if out in seen_outputs:
                problems.append(f"output_path {out!r} already used by {seen_outputs[out]}")
            seen_outputs[out] = path
        if problems:
            failed = True
            print(f"FAIL {path}")
            for p in problems:
                print(f"  - {p}")
        elif args.render:
            print(render(brief))
        elif args.dispatch:
            print(f"{brief['id']}: model={brief.get('model', 'inherit')} "
                  f"effort={brief.get('effort', 'session default')}")
        else:
            print(f"ok   {path}")

    if failed:
        print("\nDispatch blocked: fix the briefs above first.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
