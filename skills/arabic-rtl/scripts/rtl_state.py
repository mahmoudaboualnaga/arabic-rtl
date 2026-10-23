#!/usr/bin/env python3
"""Remember the user's answer to the "fix old Arabic content?" offer, so it is not asked again.

Usage:
  rtl_state.py decline --session ID      don't offer again for this chat
  rtl_state.py decline --folder DIR      don't offer again for this folder
  rtl_state.py done --session ID         chat was fixed (offer again only if new problems appear)
  rtl_state.py is-declined --session ID | --folder DIR   exit 0 if declined
  rtl_state.py reset                     forget all answers
"""
import argparse
import json
import os
import sys

STATE = os.path.join(os.path.expanduser("~"), ".claude", "arabic-rtl", "state.json")


def load():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": {}, "folders": {}}


def save(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def key(a):
    if a.session:
        return "sessions", a.session
    if a.folder:
        return "folders", os.path.abspath(a.folder)
    sys.exit("give --session or --folder")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["decline", "done", "is-declined", "reset"])
    ap.add_argument("--session")
    ap.add_argument("--folder")
    a = ap.parse_args()
    s = load()
    if a.action == "reset":
        save({"sessions": {}, "folders": {}})
        print("All answers forgotten.")
        return
    group, k = key(a)
    if a.action == "is-declined":
        sys.exit(0 if s.get(group, {}).get(k) == "declined" else 1)
    s.setdefault(group, {})[k] = "declined" if a.action == "decline" else "done"
    save(s)
    print(f"Saved: {a.action} for {k}")


if __name__ == "__main__":
    main()
