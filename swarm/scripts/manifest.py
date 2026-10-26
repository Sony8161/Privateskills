#!/usr/bin/env python3
"""Track a multi-agent run on disk so it can be recovered after a crash.

Usage:
    manifest.py init   <run_dir> <brief.json> [<brief.json> ...]
    manifest.py status <run_dir>

`init` records each brief's id and output_path with status "pending".
`status` marks an agent "done" when its output file exists and is non-empty,
prints a table, and exits 1 while any agent is still missing.

Standard library only.
"""
import json
import sys
from pathlib import Path

MANIFEST = "manifest.json"


def cmd_init(run_dir, brief_paths):
    run = Path(run_dir)
    run.mkdir(parents=True, exist_ok=True)
    agents = []
    for path in brief_paths:
        brief = json.loads(Path(path).read_text(encoding="utf-8"))
        agents.append(
            {
                "id": brief["id"],
                "brief": str(path),
                "output_path": brief["output_path"],
                "status": "pending",
            }
        )
    (run / MANIFEST).write_text(json.dumps({"agents": agents}, indent=2), encoding="utf-8")
    print(f"manifest written: {run / MANIFEST} ({len(agents)} agents)")
    return 0


def cmd_status(run_dir):
    path = Path(run_dir) / MANIFEST
    if not path.exists():
        print(f"no manifest at {path}; run init first", file=sys.stderr)
        return 2
    manifest = json.loads(path.read_text(encoding="utf-8"))
    missing = []
    for agent in manifest["agents"]:
        out = Path(agent["output_path"])
        done = out.is_file() and out.stat().st_size > 0
        agent["status"] = "done" if done else "pending"
        if not done:
            missing.append(agent)
        print(f"{agent['status']:8} {agent['id']:28} {agent['output_path']}")
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if missing:
        print(f"\n{len(missing)} agent(s) have not produced output: relaunch only these.")
        return 1
    print("\nall agents produced output.")
    return 0


def main(argv):
    if len(argv) >= 4 and argv[1] == "init":
        return cmd_init(argv[2], argv[3:])
    if len(argv) == 3 and argv[1] == "status":
        return cmd_status(argv[2])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
