#!/usr/bin/env python3
"""Append-only handoff log with stable IDs and an enforced lifecycle.

Commands:
    bay.py new <request|delivery> --thread T --from A --to B --title X --body Y [--ref ID ...]
    bay.py move <ID> <state> [--receipt TEXT] [--note TEXT]
    bay.py inbox <who>
    bay.py board
    bay.py show <ID>

Storage: bay/log.jsonl under the current directory (override with BAY_LOG).
Every line is an event; state is derived by replaying events, so the log is the
single source of truth and nothing else needs rebuilding.

Standard library only.
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(os.environ.get("BAY_LOG", "bay/log.jsonl"))
PREFIX = {"request": "REQ", "delivery": "DLV"}
TRANSITIONS = {
    "open": {"accepted", "rejected"},
    "accepted": {"delivered"},
    "delivered": {"verified", "accepted"},
    "verified": {"closed"},
    "rejected": set(),
    "closed": set(),
}
BOARD_COLUMNS = {
    "queued": ("open",),
    "active": ("accepted", "delivered"),
    "done": ("verified", "closed", "rejected"),
}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(event):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def replay():
    """Rebuild current message state from the event log."""
    messages = {}
    if not LOG.exists():
        return messages
    for line in LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event["event"] == "create":
            messages[event["id"]] = {**event, "state": "open", "history": []}
        elif event["event"] == "move" and event["id"] in messages:
            msg = messages[event["id"]]
            msg["state"] = event["state"]
            msg["history"].append(event)
    return messages


def cite(msg):
    return f"{msg['id']} ({msg['thread']}, {msg['ts'][:10]}, {msg['sender']})"


def cmd_new(args):
    msg_id = f"{PREFIX[args.kind]}-{uuid.uuid4().hex[:8]}"
    messages = replay()
    for ref in args.ref or []:
        if ref not in messages:
            print(f"unknown ref: {ref}", file=sys.stderr)
            return 1
    append(
        {
            "event": "create",
            "id": msg_id,
            "ts": now(),
            "kind": args.kind,
            "thread": args.thread,
            "sender": args.sender,
            "to": args.to,
            "title": args.title,
            "body": args.body,
            "refs": args.ref or [],
        }
    )
    print(msg_id)
    return 0


def cmd_move(args):
    messages = replay()
    msg = messages.get(args.id)
    if not msg:
        print(f"unknown id: {args.id}", file=sys.stderr)
        return 1
    if args.state not in TRANSITIONS.get(msg["state"], set()):
        legal = ", ".join(sorted(TRANSITIONS.get(msg["state"], set()))) or "none"
        print(f"illegal move {msg['state']} -> {args.state}; legal: {legal}", file=sys.stderr)
        return 1
    if args.state == "delivered" and not (args.receipt or "").strip():
        print("moving to delivered requires --receipt (what was verified)", file=sys.stderr)
        return 1
    append(
        {
            "event": "move",
            "id": args.id,
            "ts": now(),
            "state": args.state,
            "receipt": args.receipt,
            "note": args.note,
        }
    )
    print(f"{args.id}: {msg['state']} -> {args.state}")
    return 0


def cmd_inbox(args):
    waiting = [
        m
        for m in replay().values()
        if m["to"] == args.who and m["state"] in ("open", "accepted", "delivered")
    ]
    if not waiting:
        print(f"inbox for {args.who}: empty")
        return 0
    for m in waiting:
        print(f"{m['state']:9} {cite(m)}  {m['title']}")
    return 0


def cmd_board(_args):
    messages = [m for m in replay().values() if m["kind"] == "request"]
    for column, states in BOARD_COLUMNS.items():
        print(f"== {column}")
        items = [m for m in messages if m["state"] in states]
        for m in items:
            print(f"  [{m['state']}] {cite(m)}  {m['title']}")
        if not items:
            print("  (none)")
    return 0


def cmd_show(args):
    messages = replay()
    msg = messages.get(args.id)
    if not msg:
        print(f"unknown id: {args.id}", file=sys.stderr)
        return 1
    print(f"cite:   {cite(msg)}")
    print(f"state:  {msg['state']}   to: {msg['to']}")
    print(f"title:  {msg['title']}\n\n{msg['body']}\n")
    for h in msg["history"]:
        extra = f"  receipt: {h['receipt']}" if h.get("receipt") else ""
        print(f"  {h['ts']}  -> {h['state']}{extra}")
    chain, seen = list(msg["refs"]), set()
    while chain:
        ref = chain.pop(0)
        if ref in seen or ref not in messages:
            continue
        seen.add(ref)
        print(f"traces to: {cite(messages[ref])}  {messages[ref]['title']}")
        chain.extend(messages[ref]["refs"])
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("new")
    n.add_argument("kind", choices=list(PREFIX))
    n.add_argument("--thread", required=True)
    n.add_argument("--from", dest="sender", required=True)
    n.add_argument("--to", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--body", required=True)
    n.add_argument("--ref", action="append")
    n.set_defaults(fn=cmd_new)

    m = sub.add_parser("move")
    m.add_argument("id")
    m.add_argument("state", choices=list(TRANSITIONS))
    m.add_argument("--receipt")
    m.add_argument("--note")
    m.set_defaults(fn=cmd_move)

    i = sub.add_parser("inbox")
    i.add_argument("who")
    i.set_defaults(fn=cmd_inbox)

    sub.add_parser("board").set_defaults(fn=cmd_board)

    s = sub.add_parser("show")
    s.add_argument("id")
    s.set_defaults(fn=cmd_show)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
