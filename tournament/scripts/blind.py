#!/usr/bin/env python3
"""Anonymize and shuffle candidate files so a judge cannot tell who wrote what.

Usage:
    blind.py <candidates_dir> <judging_dir> [--seed N]
    blind.py --reveal <judging_dir>

Copies every file in <candidates_dir> to <judging_dir>/X1.<ext>, X2.<ext>, ... in a
random order. The key (X1 -> original file name) is written NEXT TO the judging
folder as <judging_dir>.key.json, outside it, so a judge reading the folder never
sees it. Warns when a candidate's text mentions its own file name (a giveaway).
Use --reveal after judging to print the key.

Standard library only.
"""
import argparse
import json
import random
import shutil
import sys
from pathlib import Path


def key_path(judging):
    return judging.with_name(judging.name + ".key.json")


def blind(cands, judging, seed):
    files = sorted(p for p in cands.iterdir() if p.is_file())
    if len(files) < 2:
        sys.exit("need at least two candidate files")
    order = files[:]
    random.Random(seed).shuffle(order)
    judging.mkdir(parents=True, exist_ok=True)
    key = {}
    for i, src in enumerate(order, 1):
        label = f"X{i}"
        shutil.copyfile(src, judging / f"{label}{src.suffix}")
        key[label] = src.name
        stem = src.stem.lower()
        if len(stem) > 3 and stem in src.read_text(encoding="utf-8", errors="ignore").lower():
            print(f"warning: {src.name} mentions its own name ({stem!r}); edit the copy "
                  f"{label}{src.suffix} so it does not give itself away")
    key_path(judging).write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"wrote {len(key)} anonymized candidates to {judging}")
    print(f"key saved outside it at {key_path(judging)} -- do not show it to the judge")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("first")
    parser.add_argument("second", nargs="?")
    parser.add_argument("--reveal", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    if args.reveal:
        path = key_path(Path(args.first))
        if not path.exists():
            sys.exit(f"no key at {path}")
        for label, name in json.loads(path.read_text(encoding="utf-8")).items():
            print(f"{label} = {name}")
        return 0
    if not args.second:
        parser.error("need <candidates_dir> and <judging_dir>")
    blind(Path(args.first), Path(args.second), args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
