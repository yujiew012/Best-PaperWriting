#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Validate a figure plan against the claim map and the manuscript; list placeholders still to fill.

    uv run figure_plan.py figure_plan.json --claims claim_map.json --tex paper/main.tex --md figure_plan.md

Format: assets/figure_plan_example.json; rules: references/figures_and_captions.md §0.

  ERROR  duplicate id; unknown status/type; a row without a claim; a claim id not in the claim map;
         a figure that carries several claims
  WARN   a gap/result/advantage claim with no figure or table; Figure 1 type not the one suggested for the
         route (writing/routing.md §3); a 'draw' row whose material says results are needed; with --tex,
         a planned figure missing from the paper or a paper float missing from the plan
  NOTE   rows still 'placeholder'; with --tex, every \\FigPlaceholder / \\FigPlan left in the paper

Exit 1 on ERROR, 0 otherwise.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpaths import resolve_input  # noqa: E402

STATUS = ("draw", "placeholder", "done")
TYPES = ("diagnosis", "contrast-schematic", "contrast-results", "showcase", "concept", "plot", "system", "resource",
         "overview", "qualitative", "ablation", "table", "other")
ROUTE_FIG1 = {"failure": ("diagnosis", "contrast-results"), "cost": ("contrast-schematic", "plot"),
              "capability-gap": ("showcase", "system"), "trend": ("showcase", "concept"),
              "insight": ("contrast-schematic", "concept"),
              "L3": ("plot",), "L4": ("plot",), "L5": ("concept", "plot"), "L6": ("concept",),
              "L7": ("resource", "system"), "L8": ("showcase", "plot", "concept")}
NEEDS_FIGURE = ("gap", "result", "advantage")


def check(plan, claims=None, tex=None):
    out = []

    def add(level, msg):
        out.append((level, msg))

    rows = plan.get("figures", [])
    ids = [r.get("id") for r in rows]
    for i in {x for x in ids if ids.count(x) > 1}:
        add("ERROR", f"duplicate id {i}")
    cmap = {c["id"]: c for c in (claims or {}).get("claims", []) if c.get("id")}
    for r in rows:
        rid = r.get("id", "?")
        if not r.get("id"):
            add("ERROR", "a row without 'id' (use the float's \\label, e.g. fig:overview)")
        if r.get("status") not in STATUS:
            add("ERROR", f"{rid}: status must be one of {STATUS}")
        if r.get("type") not in TYPES:
            add("ERROR", f"{rid}: type must be one of {TYPES}")
        claim = r.get("claim")
        if not claim:
            add("ERROR", f"{rid}: every figure carries one claim (set 'claim'); a figure without one goes to the appendix")
        elif isinstance(claim, list):
            add("ERROR", f"{rid}: carries {len(claim)} claims {claim}; split it or pick the one it proves")
        elif claims is not None and claim not in cmap:
            add("ERROR", f"{rid}: claim {claim} is not in the claim map")
        if r.get("status") == "draw" and re.search(r"result|render|curve|number|measure|run|output",
                                                   str(r.get("material", "")), re.I):
            add("WARN", f"{rid}: 'draw' is only for schematics of stated mechanisms; it needs results "
                        f"({r.get('material')}) -> placeholder")
        if r.get("status") == "placeholder":
            add("NOTE", f"{rid}: placeholder; needs {r.get('material', '?')}")
        if not r.get("caption_takeaway") and r.get("type") != "table":
            add("WARN", f"{rid}: write the caption's takeaway sentence before drawing")
    if claims is not None:
        carried = {r.get("claim") for r in rows}
        for cid, c in cmap.items():
            if c.get("kind") in NEEDS_FIGURE and cid not in carried and not any(
                    re.match(r"(Tab|Fig)", str(e)) for e in c.get("evidence", []) + [c.get("experiment", "")]):
                add("WARN", f"{cid} ({c.get('kind')}) has no figure or table: '{c.get('text', '')[:60]}'")
        figs = [r for r in rows if r.get("type") != "table"]
        route = claims.get("motivation") if claims.get("paper_type") in ("L1", "L2") else claims.get("paper_type")
        if figs and route in ROUTE_FIG1 and figs[0].get("type") not in ROUTE_FIG1[route]:
            add("WARN", f"Figure 1 ({figs[0].get('id')}) is '{figs[0].get('type')}'; route '{route}' usually uses "
                        f"{' or '.join(ROUTE_FIG1[route])} (writing/routing.md §3)")
    if tex:
        text = read(tex)
        body = re.sub(r"\\(?:provide|new|renew)command\{?\\(?:FigPlaceholder|FigPlan)\}?", " ", text)
        for m in re.finditer(r"\\(FigPlaceholder|FigPlan)\b", body):
            line = body.count("\n", 0, m.start()) + 1
            add("NOTE", f"\\{m.group(1)} still in the paper (line {line} of the expanded source)")
        labels = set(re.findall(r"\\begin\{(?:figure|table)\*?\}.*?\\label\{([^}]+)\}", text, re.S))
        for r in rows:
            if r.get("status") != "placeholder" and r.get("id") not in labels:
                add("WARN", f"{r.get('id')}: planned but no float with this \\label in the paper")
        for lab in sorted(labels - set(ids)):
            add("WARN", f"{lab}: float in the paper is not in the figure plan (which claim does it carry?)")
    return out


def read(path, seen=None, root=None):
    seen = seen or set()
    path = os.path.abspath(path)
    root = root or os.path.dirname(path)
    if path in seen or not os.path.exists(path):
        return ""
    seen.add(path)
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = re.sub(r"(?<!\\)%.*", "", line)
        m = re.search(r"\\(?:input|include)\{([^}]+)\}", line)
        if m:
            line = line[:m.start()] + read(resolve_input(m.group(1), path, root), seen, root) + line[m.end():]
        out.append(line)
    return "".join(out)


def render(plan):
    lines = ["| id | place | claim | type | panels | material needed | status | caption takeaway |",
             "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in plan.get("figures", []):
        lines.append("| " + " | ".join(str(r.get(k, "")).replace("|", "\\|") for k in
                                        ("id", "place", "claim", "type", "panels", "material", "status",
                                         "caption_takeaway")) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--claims", help="claim_map.json")
    ap.add_argument("--tex", help="main .tex (placeholders, labels)")
    ap.add_argument("--md", help="write the plan as a Markdown table (for report.md)")
    a = ap.parse_args(argv)
    try:
        plan = json.load(open(a.plan, encoding="utf-8"))
        claims = json.load(open(a.claims, encoding="utf-8")) if a.claims else None
    except (OSError, json.JSONDecodeError) as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2
    errs = []
    if not isinstance(plan, dict) or not isinstance(plan.get("figures", []), list) or \
            any(not isinstance(r, dict) for r in plan.get("figures", [])):
        errs.append(f"{a.plan}: must be an object with a 'figures' list of objects (see assets/figure_plan_example.json)")
    if claims is not None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import claim_map
        errs += [f"{a.claims}: {e}" for e in claim_map.shape_errors(claims)]
    if a.tex and not os.path.exists(a.tex):
        errs.append(f"not found: {a.tex}")
    if errs:
        for e in errs:
            print(f"[error] {e}", file=sys.stderr)
        return 2
    issues = check(plan, claims, a.tex)
    order = {"ERROR": 0, "WARN": 1, "NOTE": 2}
    for level, msg in sorted(issues, key=lambda x: order[x[0]]):
        print(f"{level:5s} {msg}")
    n = {k: sum(1 for l, _ in issues if l == k) for k in order}
    print(f"{len(plan.get('figures', []))} row(s): {n['ERROR']} error(s), {n['WARN']} warning(s), {n['NOTE']} note(s)")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(render(plan))
        print(f"[ok] wrote {a.md}")
    return 1 if n["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main())
