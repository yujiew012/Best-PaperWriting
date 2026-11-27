#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Assemble the author report (report.md) that goes with every drafted or revised section.

    uv run make_report.py --claims claim_map.json --tex paper/main.tex --out report.md \\
        [--figures figure_plan.json] [--numbers numbers.json] [--lint lint.json] [--style style.json] \\
        [--changes changes.md] [--outline outline.md]

Sections: the paper's claim and route; the claim map; open TODOs (claims without evidence, [TODO] markers,
figure placeholders); check results (fabrication check, lint, style metrics); the figure plan; the change
table of a revision; Limitations notes (claim_map.json "limitations"); questions for the authors
(claim_map.json "questions"). Inputs are the JSON files the other scripts write, so the report never
restates a number by hand.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import claim_map as cmap  # noqa: E402
import figure_plan as fplan  # noqa: E402


def load(path):
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[error] cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)


def todos_in_tex(tex):
    if not tex or not os.path.exists(tex):
        return []
    text = fplan.read(tex)
    # the definition of a TODO macro (\newcommand{\TODO}[1]{...[TODO: #1]}) is not an open item
    text = re.sub(r"\\(?:(?:re|provide)?newcommand\*?|def)\s*\{?\\\w+\}?[^\n]*",
                  lambda m: " " * len(m.group(0)), text)
    out = []
    for m in re.finditer(r"\[TODO:?([^\]]*)\]|\\(?:todo|TODO)\{([^}]*)\}|\\FigPlan\{([^}]*)\}", text):
        what = " ".join(next(g for g in m.groups() if g is not None).split()) or "(unspecified)"
        if re.fullmatch(r"#\d", what):
            continue
        out.append(f"line {text.count(chr(10), 0, m.start()) + 1}: {what}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claims", required=True, help="claim_map.json")
    ap.add_argument("--tex", help="manuscript (TODO markers, placeholders)")
    ap.add_argument("--figures", help="figure_plan.json")
    ap.add_argument("--numbers", help="JSON from check_numbers.py --json")
    ap.add_argument("--lint", help="JSON from lint_paper.py --json")
    ap.add_argument("--style", help="JSON from style_metrics.py --json")
    ap.add_argument("--changes", help="Markdown change table from change_table.py")
    ap.add_argument("--outline", help="Markdown reverse outline from outline.py --md")
    ap.add_argument("--out", default="report.md")
    a = ap.parse_args(argv)
    cm = load(a.claims)
    shape = cmap.shape_errors(cm)
    if shape:
        for e in shape:
            print(f"[error] {a.claims}: {e}", file=sys.stderr)
        return 2
    L = ["# Author report", ""]
    L += ["## 1. Claim and route", ""]
    for key, label in (("one_line", "Claim"), ("paper_type", "Paper type"), ("motivation", "Motivation"),
                       ("tension", "Tension"), ("insight", "Insight"), ("handle", "Handle"), ("stance", "Stance")):
        if cm.get(key):
            L.append(f"- **{label}:** {cm[key]}")
    for cw in cm.get("closest_work", []):
        L.append(f"- **Closest work:** {cw.get('name')}: {cw.get('difference')}")
    L += ["", "## 2. Claim map", "", cmap.render(cm)]
    issues = cmap.check(cm, a.tex if a.tex and os.path.exists(a.tex) else None)
    if any(l != "NOTE" for l, _ in issues):
        L += ["Claim-map findings:", ""] + [f"- {l}: {m}" for l, m in issues if l != "NOTE"] + [""]
    L += ["## 3. Open TODOs", ""]
    todo = [f"- {c['id']}: {c['todo']}" for c in cm.get("claims", []) if c.get("todo")]
    todo += [f"- manuscript {t}" for t in todos_in_tex(a.tex)]
    plan = load(a.figures)
    if plan:
        todo += [f"- {r.get('id', '?')}: needs {r.get('material', '?')}" for r in plan.get("figures", [])
                 if r.get("status") == "placeholder"]
    L += (todo or ["- none"]) + [""]
    L += ["## 4. Checks", ""]
    nums = load(a.numbers)
    if nums:
        rows = nums["numbers"]
        bad = [r for r in rows if r["status"] == "UNSUPPORTED"]
        der = [r for r in rows if r["status"] == "DERIVED"]
        L.append(f"- **Numbers** (`check_numbers.py`): {len(rows)} checked, {len(der)} derived, {len(bad)} unsupported")
        L += [f"  - UNSUPPORTED {r['text']} at {r['where']}: {r['context'][:80]}" for r in bad]
        L += [f"  - derived {r['text']} at {r['where']} = {r['basis']} (confirm)" for r in der]
    lint = load(a.lint)
    if lint is not None:
        items = lint if isinstance(lint, list) else lint.get("issues", [])
        codes = {}
        for i in items:
            codes[i["code"]] = codes.get(i["code"], 0) + 1
        L.append(f"- **Lint** (`lint_paper.py`): " + (", ".join(f"{k}×{v}" for k, v in sorted(codes.items())) or "clean"))
    style = load(a.style)
    if style:
        prof = style.get("profile", {})
        L.append(f"- **Style** (`style_metrics.py`, profile {prof.get('name')}, "
                 f"{'matching' if prof.get('matching') else 'reference only'}):")
        for sec, d in style.get("sections", {}).items():
            for f in d.get("findings", []):
                L.append(f"  - {f['level']} {sec}: {f['msg']}")
    if not (nums or lint is not None or style):
        L.append("- no check results given (run check_numbers.py, lint_paper.py and style_metrics.py with --json)")
    L.append("")
    if plan:
        L += ["## 5. Figure plan", "", fplan.render(plan)]
        issues = fplan.check(plan, cm, a.tex if a.tex and os.path.exists(a.tex) else None)
        L += [f"- {l}: {m}" for l, m in issues if l != "NOTE"] + [""]
    if a.outline:
        if not os.path.exists(a.outline):
            print(f"[error] not found: {a.outline}", file=sys.stderr)
            return 2
        L += ["## 5b. Reverse outline (read the topic sentences alone: do they tell the story?)", "",
              re.sub(r"## Story \(claim map\).*?(?=## Reverse outline)", "",       # the story is already in §2
                     open(a.outline, encoding="utf-8").read(), flags=re.S), ""]
    if a.changes and os.path.exists(a.changes):
        L += ["## 6. Change table (accept or reject each row)", "", open(a.changes, encoding="utf-8").read(), ""]
    L += ["## 7. Limitations notes", "", "Weaknesses, costs and settings where the method is not best; they belong in "
          "the evaluation or the Limitations section, never hidden.", ""]
    L += [f"- {x}" for x in cm.get("limitations", [])] or ["- none recorded (ask the authors)"]
    L += ["", "## 8. Questions for the authors", ""]
    L += [f"- {q}" for q in cm.get("questions", [])] or ["- none"]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"[ok] wrote {a.out} ({len(todo)} open TODO(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
