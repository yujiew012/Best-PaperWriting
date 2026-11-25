#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Retrieve exemplar passages by rhetorical function (references/exemplars/).

    uv run find_exemplars.py --list                          # functions and how many exemplars each has
    uv run find_exemplars.py intro.gap -n 3                  # sentence exemplars for a function (prefix match)
    uv run find_exemplars.py intro.contrast --paragraphs --type L1 --domain security_privacy
    uv run find_exemplars.py --check draft.tex               # 6-word runs a draft shares with the bank

Filters fall back gracefully: when no exemplar matches the domain or type, the others of the same function
are shown (and the fallback is said). Exemplars teach structure; never reuse their wording.
"""
import argparse
import json
import os
import random
import re
import sys

EX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "exemplars")


def records(paragraphs=False):
    path = os.path.join(EX, "paragraphs.jsonl" if paragraphs else "moves.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def functions():
    with open(os.path.join(EX, "functions.json"), encoding="utf-8") as f:
        d = json.load(f)
    return {f"{sec}.{fn}": why for sec, fns in d.items() if not sec.startswith("$") for fn, why in fns.items()}


def key(r):
    return f"{r.get('section')}.{r.get('function')}"


def grams(text, n=6):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("function", nargs="?", default="", help="section.function prefix, e.g. intro.gap")
    ap.add_argument("--paragraphs", action="store_true", help="paragraph-level exemplars")
    ap.add_argument("--type", help="paper type L1-L8 (writing/routing.md)")
    ap.add_argument("--motivation", help="failure / cost / capability-gap / insight / trend")
    ap.add_argument("--domain", help="domain id")
    ap.add_argument("-n", type=int, default=0, help="random sample of at most N")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", metavar="DRAFT", help="report 6-word runs shared with the bank")
    a = ap.parse_args(argv)
    fns = functions()
    recs = records(a.paragraphs)
    if a.check:
        if not os.path.exists(a.check):
            print(f"[error] not found: {a.check}", file=sys.stderr)
            return 2
        bank = set()
        for r in records(False) + records(True):
            bank |= grams(r.get("text", ""))
        shared = sorted(grams(open(a.check, encoding="utf-8", errors="replace").read()) & bank)
        for g in shared:
            print(f"shared: '{g}'")
        print(f"{len(shared)} shared 6-word run(s)")
        return 1 if shared else 0
    if a.list or not a.function:
        counts = {}
        for r in records(False) + records(True):
            counts[key(r)] = counts.get(key(r), 0) + 1
        for k, why in fns.items():
            print(f"{k:28s} {counts.get(k, 0):3d}  {why}")
        if not counts:
            print("\n(the bank is empty: it fills through evolve-paper-skill; see references/exemplars/README.md)")
        return 0
    if not any(k.startswith(a.function) for k in fns):
        print(f"[error] unknown function '{a.function}'; see --list", file=sys.stderr)
        return 2
    sel = [r for r in recs if key(r).startswith(a.function)]
    for field, want in (("domain", a.domain), ("paper_type", a.type), ("motivation", a.motivation)):
        if want:
            narrowed = [r for r in sel if r.get(field) == want]
            if narrowed:
                sel = narrowed
            elif sel:
                print(f"(no exemplar with {field}={want}; showing other {a.function} exemplars)\n")
    if not sel:
        desc = fns.get(a.function) or "; ".join(f"{k}: {v}" for k, v in fns.items() if k.startswith(a.function))
        print(f"no exemplars for {a.function} yet; write from the function description: {desc}")
        return 0
    if a.n and len(sel) > a.n:
        sel = random.sample(sel, a.n)
    for r in sel:
        print(f"[{key(r)} · {r.get('paper_type', '?')} · {r.get('domain', '?')}] {r.get('paper')} "
              f"({r.get('venue', '')} {r.get('year', '')})")
        if r.get("why"):
            print(f"  why: {r['why']}")
        print(f"  {r.get('text')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
