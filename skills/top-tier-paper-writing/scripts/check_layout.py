#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
Double-column LaTeX float placement checker.

Reads the position records that ``floatcheck.sty`` (same directory) writes into
the .aux file, plus the .log file, and checks the three layout rules from
SKILL.md:

  R1  Every float is on the SAME page as its first reference in running text,
      and comes BEFORE it in reading order (same column above it, or in the
      left column when the reference is in the right column; a full-width
      float at the top of the page always counts as before).
  R2  A full-width float (figure*/table*) can appear at the earliest on the
      page AFTER the one where it is defined, so its first reference must fall
      on that page or later (otherwise: move the definition earlier). Two-column
      layouts only: in a one-column document figure*/table* float like figure/table.
  R3  Column bottoms should not have large voids (detected heuristically via
      "Underfull \\vbox ... while \\output is active" in the log).

The log is also scanned for float-related LaTeX warnings ("Float too large",
"h float specifier changed", "Too many unprocessed floats", rerun requests,
undefined references).

Not detected (check visually): widows/orphans and short last lines of
paragraphs -- TeX does not report them in the log.

Usage:
    # 1) diagnostic build (source untouched):
    pdflatex -jobname=main "\\RequirePackage{floatcheck}\\input{main}"   # run twice
    # 2) check:
    python3 check_layout.py main.aux            # log defaults to main.log
    python3 check_layout.py build/main.aux --log build/main.log --json report.json

Exit status: 0 = no errors, 1 = at least one rule violation, 2 = usage error.
Without floatcheck records the script falls back to listing float pages only.
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# .aux parsing
# ---------------------------------------------------------------------------

_BRACES = r"\{((?:[^{}]|\{[^{}]*\})*)\}"


def _records(content: str, name: str, nargs: int) -> List[List[str]]:
    pattern = re.compile(r"\\" + name + _BRACES * nargs)
    return [list(m) if isinstance(m, tuple) else [m] for m in pattern.findall(content)]


@dataclass
class Pos:
    page: str        # \thepage as printed (may be roman)
    phys: int        # physical page (1-based)
    x: int           # sp from the left edge of the page
    y: int           # sp from the bottom of the page

    @classmethod
    def parse(cls, page, phys, x, y):
        # \ReadonlyShipoutCounter already counts the page being shipped out.
        return cls(page, max(int(phys), 1), int(x), int(y))


@dataclass
class Geometry:
    twocolumn: bool = True
    twoside: bool = False
    oddleft: int = 0
    evenleft: int = 0
    colwidth: int = 0
    colsep: int = 0

    def column(self, pos: Pos) -> int:
        if not self.twocolumn or self.colwidth == 0:
            return 0
        left = self.evenleft if (self.twoside and pos.phys % 2 == 0) else self.oddleft
        boundary = left + self.colwidth + self.colsep // 2
        return 0 if pos.x < boundary else 1


@dataclass
class FloatInfo:
    label: str
    ftype: str
    starred: bool
    pos: Pos
    defpos: Optional[Pos] = None
    first_ref: Optional[Pos] = None
    status: str = "ok"
    messages: List[str] = field(default_factory=list)


def parse_aux(aux_path: str):
    with open(aux_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # Follow \@input{chapter.aux} includes.
    base = os.path.dirname(aux_path)
    for inc in re.findall(r"\\@input\{([^}]+)\}", content):
        p = os.path.join(base, inc)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content += "\n" + f.read()

    geom = None
    g = _records(content, "FCgeom", 6)
    if g:
        tc, ts, odd, even, cw, cs = g[-1]
        geom = Geometry(tc == "1", ts == "1", int(odd), int(even), int(cw), int(cs))

    defs: Dict[str, Pos] = {}
    for seq, _t, _s, page, phys, x, y in _records(content, "FCdef", 7):
        defs[seq] = Pos.parse(page, phys, x, y)

    floats: Dict[str, FloatInfo] = {}
    for label, seq, ftype, star, page, phys, x, y in _records(content, "FCfloat", 8):
        if label in floats:      # \label executed twice (e.g. caption measured)
            continue
        floats[label] = FloatInfo(label, ftype, star == "1",
                                  Pos.parse(page, phys, x, y), defs.get(seq))

    refs: Dict[str, List[Pos]] = {}
    for labels, page, phys, x, y in _records(content, "FCref", 5):
        p = Pos.parse(page, phys, x, y)
        for lab in labels.split(","):
            refs.setdefault(lab.strip(), []).append(p)

    # Plain \newlabel entries (fallback mode, and labels outside floatcheck).
    newlabels = {}
    for label, body in re.findall(r"\\newlabel\{([^}]+)\}\{\{[^}]*\}\{([^}]*)\}", content):
        newlabels[label] = body
    marks = {}
    for what, page, phys, x, y in _records(content, "FCmark", 5):
        marks.setdefault(what, Pos.parse(page, phys, x, y))     # first occurrence
    blk = _records(content, "FCblock", 2)
    block = (int(blk[-1][0]), int(blk[-1][1])) if blk else None
    return geom, floats, refs, newlabels, marks, block


def body_length(geom, marks, block):
    """Main-body length in pages, up to the first bibliography/appendix marker (None if unknown)."""
    ends = [p for k, p in marks.items() if k in ("bibliography", "appendix")]
    if not ends or not block or geom is None:
        return None, None
    end = min(ends, key=lambda p: (p.phys, geom.column(p), -p.y))
    top, bottom = block
    frac_col = min(max((top - end.y) / max(top - bottom, 1), 0.0), 1.0)
    used = (geom.column(end) + frac_col) / 2 if geom.twocolumn else frac_col
    return round(end.phys - 1 + used, 2), end


# ---------------------------------------------------------------------------
# rules
# ---------------------------------------------------------------------------

def reading_key(pos: Pos, geom: Geometry):
    return (pos.phys, geom.column(pos), -pos.y)


def check_floats(geom: Geometry, floats: Dict[str, FloatInfo], refs: Dict[str, List[Pos]]):
    for fl in floats.values():
        rlist = refs.get(fl.label, [])
        if not rlist:
            fl.status = "warning"
            fl.messages.append("never referenced in running text")
            continue
        fl.first_ref = min(rlist, key=lambda p: reading_key(p, geom))
        r, f = fl.first_ref, fl.pos

        # R2: full-width floats; only in two-column layouts -- in a one-column document
        # (e.g. an elsarticle preprint) figure*/table* behave like figure/table
        full_width = fl.starred and geom.twocolumn
        if full_width and fl.defpos is not None:
            earliest = fl.defpos.phys + 1
            if r.phys < earliest:
                fl.status = "error"
                fl.messages.append(
                    f"R2: defined on p.{fl.defpos.page}, so it cannot appear before "
                    f"p.{earliest} (physical), but is first referenced on p.{r.page}; "
                    f"move \\begin{{{fl.ftype}*}} at least one page before the reference"
                    + (f"; NOTE: a full-width {fl.ftype}* can never appear on page 1 -- use a column-width "
                       f"{fl.ftype} for a page-1 teaser, or cite it first on page 2" if r.phys == 1 else ""))
            elif f.phys > earliest and f.phys > r.phys:
                fl.messages.append(
                    f"deferred to p.{f.page} although p.{earliest} was possible "
                    f"(float queue congestion or [p] placement)")

        # R1: same page, before in reading order
        if f.phys > r.phys:
            fl.status = "error"
            fl.messages.append(
                f"R1: placed on p.{f.page}, AFTER its first reference on p.{r.page}")
        elif f.phys < r.phys:
            if fl.status != "error":
                fl.status = "warning"
            fl.messages.append(
                f"R1: placed on p.{f.page}, a page BEFORE its first reference on p.{r.page}")
        elif not full_width:
            fc, rc = geom.column(f), geom.column(r)
            if fc > rc or (fc == rc and f.y < r.y):
                if fl.status != "error":
                    fl.status = "warning"
                where = "right column" if fc > rc else "below the reference"
                fl.messages.append(
                    f"R1: same page (p.{f.page}) but after the reference in reading "
                    f"order ({where})")


# ---------------------------------------------------------------------------
# .log scanning
# ---------------------------------------------------------------------------

_LOG_PATTERNS = [
    (re.compile(r"Underfull \\vbox \(badness (\d+)\) has occurred while \\output is active"),
     "R3: column/page stretched to fill (badness {0}) -- likely a void at the column bottom"),
    (re.compile(r"LaTeX Warning: Float too large for page by ([\d.]+pt)"),
     "float too large for page by {0}"),
    (re.compile(r"LaTeX Warning: `(!?h)' float specifier changed to `(!?ht)'"),
     "`{0}' float specifier changed to `{1}' (float could not go here)"),
    (re.compile(r"Too many unprocessed floats"),
     "too many unprocessed floats (float queue overflow)"),
]
_RERUN = re.compile(r"Label\(s\) may have changed|Rerun to get cross-references right")
_UNDEF = re.compile(r"There were undefined references")


def scan_log(log_path: str):
    issues, notes, errors = [], [], []
    if not os.path.exists(log_path):
        notes.append(f"log not found: {log_path}")
        return issues, notes, errors
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        log = f.read()
    errors = re.findall(r"^! (.+)$", log, flags=re.M)
    # Track shipped pages: TeX prints "[<page>" when a page is shipped out.
    shipped = 0
    events = sorted(
        [(m.start(), "page", m) for m in re.finditer(r"(?<![\w\\])\[(\d+)(?=[\s\]{<])", log)] +
        [(m.start(), i, m) for i, (pat, _) in enumerate(_LOG_PATTERNS) for m in pat.finditer(log)],
        key=lambda e: e[0])
    for _, kind, m in events:
        if kind == "page":
            shipped += 1
        else:
            msg = _LOG_PATTERNS[kind][1].format(*m.groups())
            issues.append({"page_approx": shipped + 1, "message": msg})
    if _RERUN.search(log):
        notes.append("LaTeX asks for a rerun: positions may be stale -- compile again")
    if _UNDEF.search(log):
        notes.append("there are undefined references")
    return issues, notes, errors


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def resolve_paths(target: str, log: Optional[str]):
    stem, ext = os.path.splitext(target)
    if os.path.isdir(target):
        cands = [f for f in os.listdir(target) if f.endswith(".aux")]
        if len(cands) != 1:
            sys.exit(f"[error] expected exactly one .aux in {target}, found {cands}; pass it explicitly")
        aux = os.path.join(target, cands[0])
    elif ext in (".tex", ".log", ".pdf", ""):
        aux = stem + ".aux"
    else:
        aux = target
    return aux, log or os.path.splitext(aux)[0] + ".log"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check float placement in a compiled LaTeX paper.")
    ap.add_argument("target", help="main.aux (or main.tex / build dir)")
    ap.add_argument("--log", help="LaTeX log file (default: next to the .aux)")
    ap.add_argument("--json", "--save-baseline", dest="json",
                    help="write the report as JSON (use it later as a --compare baseline)")
    ap.add_argument("--page-limit", type=float, help="main-body page limit (fails above it)")
    ap.add_argument("--budget-note", help=argparse.SUPPRESS)
    ap.add_argument("--compare", metavar="BASELINE_JSON",
                    help="compare with a saved report; exit 1 only if the layout got worse")
    args = ap.parse_args(argv)

    aux, log = resolve_paths(args.target, args.log)
    if not os.path.exists(aux):
        print(f"[error] aux file not found: {aux} (compile the paper first)", file=sys.stderr)
        return 2

    geom, floats, refs, newlabels, marks, block = parse_aux(aux)
    log_issues, notes, tex_errors = scan_log(log)
    report = {"aux": aux, "log": log, "mode": "floatcheck" if geom else "fallback", "pages": count_pages(log),
              "floats": [], "log_issues": log_issues, "notes": notes, "tex_errors": tex_errors}

    print(f"[Layout Checker] {aux}")
    if tex_errors:
        print(f"[error] the LaTeX run reported {len(tex_errors)} error(s); positions are unreliable. First: "
              f"{tex_errors[0]}")
    if geom is None:
        print("[warning] no floatcheck records found -- only listing float pages.\n"
              "          Build with floatcheck.sty for real checks, e.g.:\n"
              "          pdflatex -jobname=main \"\\RequirePackage{floatcheck}\\input{main}\"")
        for lab, page in newlabels.items():
            if re.match(r"(fig|tab|table|figure)[:.-]", lab):
                print(f"  - {lab:30s} p.{page}")
                report["floats"].append({"label": lab, "page": page})
        n_err = 0
    else:
        check_floats(geom, floats, refs)
        order = sorted(floats.values(), key=lambda fl: reading_key(fl.pos, geom))
        n_err = sum(fl.status == "error" for fl in order)
        n_warn = sum(fl.status == "warning" for fl in order)
        mark = {"ok": " ok ", "warning": "WARN", "error": "FAIL"}
        print(f"{len(order)} floats, {n_err} errors, {n_warn} warnings "
              f"({'two' if geom.twocolumn else 'one'}-column layout)\n")
        for fl in order:
            ref = f"first ref p.{fl.first_ref.page}" if fl.first_ref else "no ref"
            kind = fl.ftype + ("*" if fl.starred else "")
            print(f"  [{mark[fl.status]}] {fl.label:30s} {kind:8s} on p.{fl.pos.page:4s} {ref}")
            for m in fl.messages:
                print(f"           - {m}")
            d = asdict(fl)
            report["floats"].append(d)

    if log_issues:
        print("\nLog findings (page numbers approximate):")
        for it in log_issues:
            print(f"  - ~p.{it['page_approx']}: {it['message']}")
    for n in notes:
        print(f"[note] {n}")
    print("\nNot checked automatically: widows/orphans and 1-2 word last lines -- inspect the PDF.")

    if report["pages"]:
        print(f"Total pages: {report['pages']}")
    body, end = body_length(geom, marks, block)
    limit = args.page_limit
    over = False
    if body is not None:
        what = "bibliography" if marks.get("bibliography") is end else "appendix"
        report["body_pages"] = body
        print(f"Main body: {body:.2f} pages (until the {what} starts on p.{end.page})")
        if limit:
            over = body > limit
            report["page_limit"] = limit
            print(("FAIL" if over else "ok  ") + f" page budget: {body:.2f} / {limit} pages"
                  + (" -- trim the body" if over else f" ({limit - body:.2f} to spare)"))
            if 0 <= limit - body < 0.5:
                print("[note] less than half a page to spare: a different font or class version can push it over")
    elif limit:
        print("[note] page budget not checked: no bibliography/appendix marker (build with floatcheck.sty)")
    if args.budget_note:
        print(f"[note] {args.budget_note}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    if args.compare:
        return compare(report, args.compare) or (1 if (tex_errors or over) else 0)
    return 1 if (n_err or tex_errors or over) else 0


def count_pages(log_path):
    try:
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            m = re.search(r"Output written on .*?\((\d+) pages?", f.read(), re.S)
        return int(m.group(1)) if m else None
    except OSError:
        return None


def compare(report, baseline_path):
    """Print the difference to a baseline report; return 1 if the layout got worse."""
    rank = {"ok": 0, "warning": 1, "error": 2}
    try:
        with open(baseline_path, encoding="utf-8") as f:
            base = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[error] cannot read baseline {baseline_path}: {e}", file=sys.stderr)
        return 2
    old = {fl["label"]: fl.get("status", "ok") for fl in base.get("floats", [])}
    new = {fl["label"]: fl.get("status", "ok") for fl in report.get("floats", [])}
    worse, better = [], []
    for lab in sorted(set(old) | set(new)):
        a, b = old.get(lab), new.get(lab)
        if a is None or b is None:
            print(f"  [diff] {lab}: {'added' if a is None else 'REMOVED (check the float was not deleted)'}")
            if b is None:
                worse.append(lab)
            continue
        if rank[b] > rank[a]:
            worse.append(lab)
            print(f"  [WORSE] {lab}: {a} -> {b}")
        elif rank[b] < rank[a]:
            better.append(lab)
            print(f"  [better] {lab}: {a} -> {b}")
    n_old = sum(s == "error" for s in old.values())
    n_new = sum(s == "error" for s in new.values())
    print(f"\nCompared with {baseline_path}: FAIL {n_old} -> {n_new}; "
          f"{len(better)} improved, {len(worse)} worse")
    if base.get("pages") and report.get("pages") and report["pages"] != base["pages"]:
        print(f"[note] page count changed: {base['pages']} -> {report['pages']}")
    regressed = bool(worse) or n_new > n_old
    print("RESULT: " + ("REGRESSION -- revert or fix before continuing" if regressed else "no regression"))
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
