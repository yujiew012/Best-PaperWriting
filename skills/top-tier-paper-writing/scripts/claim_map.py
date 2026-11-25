#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Validate a claim map (claims -> evidence -> wording strength) and render it for the author report.

    uv run claim_map.py claim_map.json
    uv run claim_map.py claim_map.json --tex paper/main.tex --md claim_map.md

Format: assets/claim_map_example.json; rules: references/writing/claims_and_evidence.md.

  ERROR  duplicate or missing id; unknown kind/strength; a result/advantage/stance/contribution claim with
         neither evidence nor todo; a claim placed in more than one introduction paragraph ("say it once")
  WARN   wording stronger than the evidence (e.g. 'show' with one setting, 'causal' without an ablation,
         'prove' without a theorem); evidence-map gaps (method without method_section, result without
         experiment); headline numbers over budget; with --tex, more numbers in the abstract/introduction
         than the roles allow, or a claim id flagged abstract:true that has no headline/supporting number
  NOTE   claims still marked todo (they go to the author report)

Exit 1 on ERROR, 0 otherwise.
"""
import argparse
import json
import os
import re
import sys

KINDS = ("gap", "insight", "method", "result", "advantage", "stance", "contribution")
STRENGTHS = ("prove", "show", "causal", "observe", "hypothesis")
ROLES = ("headline", "supporting", "table")
NEEDS_EVIDENCE = ("result", "advantage", "stance", "contribution")
BUDGET = {"abstract": 5, "intro": 14}        # p90 of award papers (numbers per section), see claims_and_evidence.md


def shape_errors(cm):
    """Structural problems that make the other checks meaningless (reported with exit 2)."""
    if not isinstance(cm, dict):
        return ["the claim map must be a JSON object with a 'claims' list (see assets/claim_map_example.json)"]
    errs = []
    claims = cm.get("claims", [])
    if not isinstance(claims, list):
        return ["'claims' must be a list of objects"]
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            errs.append(f"claims[{i}] must be an object, got {type(c).__name__}")
            continue
        if "evidence" in c and not isinstance(c["evidence"], list):
            errs.append(f"claims[{i}] ({c.get('id')}): 'evidence' must be a list, e.g. [\"Tab. 1\"]")
        if "settings" in c and (isinstance(c["settings"], bool) or not isinstance(c["settings"], int)):
            errs.append(f"claims[{i}] ({c.get('id')}): 'settings' must be an integer")
        if "where" in c and not isinstance(c["where"], (str, list)):
            errs.append(f"claims[{i}] ({c.get('id')}): 'where' must be a string such as \"intro:P3\"")
    nums = cm.get("numbers", [])
    if not isinstance(nums, list) or any(not isinstance(n, dict) for n in nums):
        errs.append("'numbers' must be a list of objects {value, role, claim}")
    return errs


def check(cm, tex=None):
    out = []

    def add(level, msg):
        out.append((level, msg))

    claims = cm.get("claims", [])
    ids = [c.get("id") for c in claims]
    for i in {x for x in ids if ids.count(x) > 1}:
        add("ERROR", f"duplicate claim id {i}")
    for c in claims:
        cid = c.get("id") or "?"
        if not c.get("id"):
            add("ERROR", f"claim without id: {c.get('text', '')[:50]}")
        if c.get("kind") not in KINDS:
            add("ERROR", f"{cid}: kind must be one of {KINDS}")
        if c.get("strength", "observe") not in STRENGTHS:
            add("ERROR", f"{cid}: strength must be one of {STRENGTHS}")
        ev = [e for e in c.get("evidence", []) if str(e).strip()]
        if c.get("kind") in NEEDS_EVIDENCE and not ev and not c.get("todo"):
            add("ERROR", f"{cid}: a {c.get('kind')} claim needs evidence (table/figure/theorem/stats key) or a todo")
        where = c.get("where")
        if isinstance(where, list) and len([w for w in where if str(w).startswith("intro")]) > 1:
            add("ERROR", f"{cid}: stated in {len(where)} introduction paragraphs {where}; say it once")
        st = c.get("strength", "observe")
        if ev:
            if st == "prove" and not any(re.search(r"thm|theorem|lemma|prop|proof", str(e), re.I) for e in ev):
                add("WARN", f"{cid}: 'prove' needs a theorem; evidence is {ev}")
            settings = c.get("settings")
            if st == "show" and c.get("kind") in ("result", "advantage", "gap"):
                if settings is not None and settings < 2:
                    add("WARN", f"{cid}: 'show' means consistent across settings; {settings} setting supports "
                                f"'observe'")
                elif settings is None and len(ev) < 2:
                    add("NOTE", f"{cid}: 'show' needs >= 2 settings; set \"settings\" (models/benchmarks covered "
                                f"by {ev[0]}) or add evidence")
            if st == "causal" and not c.get("ablation"):
                add("WARN", f"{cid}: 'causal' wording needs an ablation or controlled intervention")
        if c.get("kind") == "method" and not c.get("method_section"):
            add("WARN", f"{cid}: method claim without method_section (evidence map)")
        if c.get("kind") in ("result", "advantage") and not c.get("experiment"):
            add("WARN", f"{cid}: result claim without experiment (evidence map)")
        if c.get("todo"):
            add("NOTE", f"{cid}: TODO {c['todo']}")
    nums = cm.get("numbers", [])
    for n in nums:
        if n.get("role") not in ROLES:
            add("ERROR", f"number {n.get('value')}: role must be one of {ROLES}")
        if n.get("claim") and n["claim"] not in ids:
            add("ERROR", f"number {n.get('value')}: unknown claim {n['claim']}")
    head = [n for n in nums if n.get("role") == "headline"]
    if len(head) > 3:
        add("WARN", f"{len(head)} headline numbers; keep 1-2 (plus one scale number)")
    if tex:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import check_numbers
        found = check_numbers.draft_numbers(tex, {"abstract", "intro"})
        for sec, lim in BUDGET.items():
            k = sum(1 for f in found if f["section"] == sec)
            planned = sum(1 for n in nums if n.get("role") in (("headline",) if sec == "abstract"
                                                                 else ("headline", "supporting")))
            if k > lim:
                add("WARN", f"{sec} has {k} numbers (90% of strong papers have <= {lim}); move the rest to tables")
            elif planned and k > planned + 1:
                add("WARN", f"{sec} has {k} numbers but the claim map plans {planned}; give each a role")
    return out


def render(cm):
    lines = ["| id | kind | claim | strength | evidence | where | method / experiment / ablation |",
             "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for c in cm.get("claims", []):
        ev = ", ".join(str(e) for e in c.get("evidence", [])) or f"**TODO**: {c.get('todo', '')}"
        em = " / ".join(str(c.get(k, "-")) for k in ("method_section", "experiment", "ablation"))
        lines.append(f"| {c.get('id')} | {c.get('kind')} | {c.get('text', '')} | {c.get('strength', '')} | {ev} | "
                     f"{c.get('where', '')}{' + abstract' if c.get('abstract') else ''} | {em} |")
    if cm.get("numbers"):
        lines += ["", "| number | role | claim |", "| :--- | :--- | :--- |"]
        lines += [f"| {n.get('value')} | {n.get('role')} | {n.get('claim', '')} |" for n in cm["numbers"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("claim_map")
    ap.add_argument("--tex", help="manuscript (.tex/.md) to count abstract/introduction numbers against the roles")
    ap.add_argument("--md", help="write the claim map as a Markdown table (for report.md)")
    a = ap.parse_args(argv)
    try:
        cm = json.load(open(a.claim_map, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[error] {a.claim_map}: {e}", file=sys.stderr)
        return 2
    shape = shape_errors(cm)
    if shape:
        for e in shape:
            print(f"[error] {a.claim_map}: {e}", file=sys.stderr)
        return 2
    if a.tex and not os.path.exists(a.tex):
        print(f"[error] not found: {a.tex}", file=sys.stderr)
        return 2
    issues = check(cm, a.tex)
    order = {"ERROR": 0, "WARN": 1, "NOTE": 2}
    for level, msg in sorted(issues, key=lambda x: order[x[0]]):
        print(f"{level:5s} {msg}")
    n = {k: sum(1 for l, _ in issues if l == k) for k in order}
    print(f"{len(cm.get('claims', []))} claim(s): {n['ERROR']} error(s), {n['WARN']} warning(s), {n['NOTE']} note(s)")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(render(cm))
        print(f"[ok] wrote {a.md}")
    return 1 if n["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
