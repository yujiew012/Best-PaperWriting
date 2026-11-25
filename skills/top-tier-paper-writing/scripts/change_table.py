#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Sentence-level change table for a revision: original -> revised -> reason, one row per change.

    uv run change_table.py old_abstract.tex new_abstract.tex --out changes.md
    uv run change_table.py old.md new.md --section intro --reasons reasons.json --out changes.md

Inputs: .tex (prose; with --section abstract|intro only that section of a full paper), .md or .txt.
Sentences are aligned with difflib; each row is kept / changed / added / removed. Unchanged sentences are
omitted unless --all. The 'Reason' column is filled from --reasons (a JSON object mapping a row number or a
revised sentence prefix to its reason) and otherwise left as TODO: every changed row needs a reason that
names the rule it follows (e.g. "claims_and_evidence.md §3: one headline number") before the author sees it.
The author accepts or rejects each row, so never merge several edits into one row.
"""
import argparse
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_metrics as sm  # noqa: E402


def sentences(path, section=None):
    if path.endswith(".tex"):
        raw = sm.read_tex(path)
        if section:
            secs = sm.from_tex(path)
            paras = secs.get(section, [])
        else:
            paras = sm.paragraphs(sm.tex_to_text(raw))
    elif path.endswith(".md") and section:
        paras = sm.from_md(path).get(section, [])
    else:
        paras = sm.paragraphs(open(path, encoding="utf-8", errors="replace").read())
    return [s for p in paras for s in sm.split_sentences(p)]


def norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def rows(old, new, show_all=False):
    sm_ = difflib.SequenceMatcher(None, [norm(s) for s in old], [norm(s) for s in new], autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm_.get_opcodes():
        if tag == "equal":
            if show_all:
                out += [("kept", old[i], new[j]) for i, j in zip(range(i1, i2), range(j1, j2))]
            continue
        a, b = old[i1:i2], new[j1:j2]
        if tag == "replace":
            # pair sentences one-to-one by similarity; leftovers become added/removed rows
            pairs = []
            used = set()
            span = max(len(b), 1) / max(len(a), 1)
            for ii, x in enumerate(a):
                best, score = None, 0.0
                for k, y in enumerate(b):
                    if k in used:
                        continue
                    r = difflib.SequenceMatcher(None, norm(x), norm(y)).ratio()
                    if r > score:
                        best, score = k, r
                if best is not None and score >= 0.3:
                    used.add(best)
                    pairs.append((best, ("changed", x, b[best])))
                else:
                    pairs.append((ii * span - 0.5, ("removed", x, "")))
            pairs += [(k, ("added", "", y)) for k, y in enumerate(b) if k not in used]
            out += [row for _, row in sorted(pairs, key=lambda p: p[0])]   # reading order of the revision
        elif tag == "delete":
            out += [("removed", x, "") for x in a]
        else:
            out += [("added", "", y) for y in b]
    return out


def reason_for(i, revised, reasons):
    if str(i) in reasons:
        return reasons[str(i)]
    for k, v in reasons.items():
        if not k.isdigit() and revised.startswith(k):
            return v
    return "TODO: reason (rule it follows)"


def cell(s):
    return s.replace("|", "\\|").replace("\n", " ") or "—"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--section", choices=["abstract", "intro"])
    ap.add_argument("--reasons", help="JSON: {row number or revised-sentence prefix: reason}")
    ap.add_argument("--all", action="store_true", help="also list unchanged sentences")
    ap.add_argument("--out", help="write the Markdown table here (default: stdout)")
    a = ap.parse_args(argv)
    for p in (a.old, a.new):
        if not os.path.exists(p):
            print(f"[error] not found: {p}", file=sys.stderr)
            return 2
    old, new = sentences(a.old, a.section), sentences(a.new, a.section)
    if not old and not new:
        print("[error] no sentences found (check --section)", file=sys.stderr)
        return 2
    reasons = json.load(open(a.reasons, encoding="utf-8")) if a.reasons else {}
    rs = rows(old, new, a.all)
    lines = ["| # | Status | Original | Revised | Reason | Accept? |", "| ---: | :--- | :--- | :--- | :--- | :---: |"]
    todo = 0
    for i, (status, x, y) in enumerate(rs, 1):
        r = "" if status == "kept" else reason_for(i, y or x, reasons)
        todo += r.startswith("TODO")
        lines.append(f"| {i} | {status} | {cell(x)} | {cell(y)} | {cell(r)} | ☐ |")
    text = "\n".join(lines) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[ok] wrote {a.out}")
    else:
        print(text)
    changed = sum(1 for s, _, _ in rs if s != "kept")
    print(f"{len(old)} -> {len(new)} sentences; {changed} change row(s); {todo} without a reason", file=sys.stderr)
    return 1 if todo and a.reasons else 0


if __name__ == "__main__":
    sys.exit(main())
