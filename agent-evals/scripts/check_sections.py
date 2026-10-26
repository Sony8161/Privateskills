#!/usr/bin/env python3
"""Check that an agent's output contains required sections, with content, in order.

Usage:
    check_sections.py <file> --require Frame Challenge Recommendation [--hook]

A section is a markdown heading (any level) whose text contains the given name,
case-insensitively. It must have at least one non-blank line of body before the
next heading. Sections must appear in the order listed.

Exit codes: 0 ok; 1 failed; 2 failed with --hook (the code Claude Code hooks use
to send stderr back to the agent).

Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")


def parse_sections(text):
    """Return a list of (heading_text, body_text) in document order."""
    sections, current, body = [], None, []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            if current is not None:
                sections.append((current, "\n".join(body)))
            current, body = match.group(1), []
        elif current is not None:
            body.append(line)
    if current is not None:
        sections.append((current, "\n".join(body)))
    return sections


def check(text, required):
    sections = parse_sections(text)
    problems, last_index = [], -1
    for name in required:
        needle = name.lower()
        found = next(
            (i for i, (head, _) in enumerate(sections) if needle in head.lower()), None
        )
        if found is None:
            problems.append(f"missing section: {name}")
            continue
        if not sections[found][1].strip():
            problems.append(f"empty section: {name}")
        if found < last_index:
            problems.append(f"section out of order: {name}")
        last_index = max(last_index, found)
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("--require", nargs="+", required=True)
    parser.add_argument("--hook", action="store_true", help="exit 2 on failure")
    args = parser.parse_args()

    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read {args.file}: {exc}", file=sys.stderr)
        return 2 if args.hook else 1

    problems = check(text, args.require)
    if problems:
        print("Output rejected, fix and resubmit:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2 if args.hook else 1
    print("ok: all required sections present, non-empty, in order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
