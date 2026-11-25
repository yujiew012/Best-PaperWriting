#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Every number in the manuscript must come from a source file: the fabrication check.

    uv run check_numbers.py paper/main.tex --sources results/ stats.json notes.md
    uv run check_numbers.py paper/main.tex --sources stats.json --sections abstract,intro
    uv run check_numbers.py draft.md --sources facts.md --allow 2026,8 --json numbers.json

A number in the prose is SUPPORTED when, at the precision written in the draft, it equals
  - a number in a source file (CSV, JSON, TXT, MD, TEX, LOG; directories are searched recursively), or
  - that number as a percentage (0.432 -> 43.2%). Margins and ratios belong in the sources too: compute them
    with result_stats.py and pass its stats.json. With --derive, also
    a difference of two positive source numbers that sit together, a difference of fractions in percentage
    points (for % and pp values), a percent change (% values) or a ratio (values written with x or ×), each within
    one table, JSON entry or paragraph; reported as DERIVED so the author can confirm the arithmetic.
Ignored: citations, figure/table/section/equation numbers, years in citations, identifiers that contain digits
(GPT-4, Llama-3.1, ResNet-50), integers up to 10 without a unit, and anything inside equations, tables
and figure environments (tables are checked against their sources by the author).

Exit 1 if any number is UNSUPPORTED (or with --strict, if any is DERIVED), 0 otherwise, 2 on usage errors.
"""
import argparse
import itertools
import json
import os
import re
import sys

NUM = re.compile(r"(?<![\w.\-–])[-+−]?\d+(?:,\d{3})*(?:\.\d+)?(?![\w.]*\d)\s*(?:\\?%|×|x\b|pp\b|percentage points?\b|points?\b)?")
TEXT_EXT = (".csv", ".tsv", ".json", ".txt", ".md", ".tex", ".log", ".yaml", ".yml")


def to_float(s):
    s = s.replace(",", "").replace("−", "-")
    m = re.match(r"[-+]?\d+(?:\.\d+)?", s.strip())
    return float(m.group(0)) if m else None


def decimals(s):
    m = re.search(r"\.(\d+)", s.replace(",", ""))
    return len(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# draft
# ---------------------------------------------------------------------------

def read_tex(path, seen=None):
    seen = seen or set()
    path = os.path.abspath(path)
    if path in seen or not os.path.exists(path):
        return []
    seen.add(path)
    out = []
    for no, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        line = re.sub(r"(?<!\\)%.*", "", line.rstrip("\n"))
        m = re.search(r"\\(?:input|include)\{([^}]+)\}", line)
        if m:
            inc = os.path.join(os.path.dirname(path), m.group(1))
            out += read_tex(inc if inc.endswith(".tex") else inc + ".tex", seen)
            continue
        out.append((os.path.basename(path), no, line))
    return out


def blank_envs(lines):
    """Blank tables, figures, equations, algorithms and the bibliography (kept line-aligned)."""
    text = "\n".join(l for _, _, l in lines)
    text = re.sub(r"\\begin\{(table|figure|equation|align|algorithm|tabular|thebibliography|lstlisting)\*?\}.*?"
                  r"\\end\{\1\*?\}", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return text.split("\n")


def section_of(lines_text):
    """Section name per line: abstract / intro / body."""
    out, cur = [], "body"
    for l in lines_text:
        if re.search(r"\\begin\{abstract\}|^#+\s*abstract\b", l, re.I):
            cur = "abstract"
        elif re.search(r"\\end\{abstract\}", l):
            out.append(cur)
            cur = "body"
            continue
        elif re.search(r"\\section\*?\{\s*Introduction|^#+\s*(?:\d+\.?\s*)?Introduction\b", l, re.I):
            cur = "intro"
        elif re.search(r"\\section\*?\{|^#\s+\S", l):
            cur = "body"
        out.append(cur)
    return out


def clean_line(l):
    l = re.sub(r"\$[^$]*\$", " ", l)                                       # inline math
    l = re.sub(r"\\(?:cite\w*|ref|cref|Cref|autoref|eqref|label|url|href|includegraphics)\*?(\[[^\]]*\])?\{[^}]*\}",
               " ", l)
    l = re.sub(r"\[\d+(?:[,–-]\s*\d+)*\]", " ", l)                          # numeric citations [12, 13]
    l = re.sub(r"\([^()]*?(?:19|20)\d{2}[a-z]?\)", " ", l)                    # (Author et al., 2024)
    l = re.sub(r"\b(?:Fig(?:ure)?s?|Tab(?:le)?s?|Sec(?:tion)?s?|Eqs?|Equations?|Algorithm|Appendix|Line|Step|"
               r"Theorem|Lemma|Definition|Corollary|Proposition)\.?\s*~?\(?\d+(?:\.\d+)*\)?", " ", l, flags=re.I)
    l = re.sub(r"\b[A-Za-z][A-Za-z]*[-_]?\d[\w.-]*\b|\b\d+[A-Za-z][A-Za-z]*\b(?<!pp)(?<!x)", " ", l)  # GPT-4, 7B, 3D
    l = l.replace("\\%", "%").replace("\\times", "×").replace("~", " ").replace("{,}", ",")
    l = l.replace("$\\times$", "×")
    unit = r"(%|pp\b|percentage points?\b|points?\b|×|x\b)"
    l = re.sub(r"(\d+(?:\.\d+)?)\s*(?:--|–|—|to)\s*(\d+(?:\.\d+)?)\s*" + unit,
               lambda m: f"{m.group(1)}{m.group(3)} to {m.group(2)}{m.group(3)}", l)   # the unit applies to both ends
    l = re.sub(r"(?<=\d)\s*(?:--|–|—)\s*(?=\d)", " to ", l)               # ranges 4.2--49.5
    return l


def draft_numbers(path, sections):
    if path.endswith(".tex"):
        lines = read_tex(path)
        texts = blank_envs(lines)
        where = [(f, n) for f, n, _ in lines]
    else:
        raw = open(path, encoding="utf-8", errors="replace").read().split("\n")
        texts = [re.sub(r"^\s*\|.*\|\s*$", "", l) for l in raw]               # markdown tables are data
        where = [(os.path.basename(path), i + 1) for i in range(len(raw))]
    secs = section_of(texts)
    found = []
    for (f, n), text, sec in zip(where, texts, secs):
        if sections and sec not in sections:
            continue
        for m in NUM.finditer(clean_line(text)):
            tok = m.group(0).strip()
            v = to_float(tok)
            if v is None:
                continue
            unit = bool(re.search(r"%|×|x$|pp|point", tok))
            if not unit and "." not in tok and abs(v) <= 10:
                continue
            if not unit and "." not in tok and 1900 <= v <= 2100:
                continue                                                      # years
            found.append({"value": v, "text": tok, "decimals": decimals(tok), "pct": bool(re.search(r"%|pp|point", tok)),
                          "ratio": bool(re.search(r"×|x$", tok)),
                          "where": f"{f}:{n}", "section": sec, "context": text.strip()[:120]})
    return found


# ---------------------------------------------------------------------------
# sources
# ---------------------------------------------------------------------------

NUM_IN_TEXT = re.compile(r"(?<![\w.\-])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?![\w])")
GROUP_MAX = 300           # derivations are searched only among numbers that sit together (one table / entry)


def nums_in(text):
    return [x for x in (to_float(t) for t in NUM_IN_TEXT.findall(text)) if x is not None]


def leaves(obj):
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, str):
        return nums_in(obj)
    items = obj.values() if isinstance(obj, dict) else obj if isinstance(obj, list) else []
    return [x for v in items for x in leaves(v)]


def json_groups(obj, out):
    """Largest sub-trees with at most GROUP_MAX numbers: one result table, one entry, one row block."""
    vals = leaves(obj)
    if len(vals) <= GROUP_MAX or not isinstance(obj, (dict, list)):
        if vals:
            out.append(vals)
        return
    for v in (obj.values() if isinstance(obj, dict) else obj):
        json_groups(v, out)


def source_numbers(paths):
    """(all values, groups of values that may be combined, files)."""
    vals, groups, files = [], [], []
    for p in paths:
        cand = []
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                cand += [os.path.join(root, f) for f in fs if f.lower().endswith(TEXT_EXT)]
        elif os.path.exists(p):
            cand.append(p)
        else:
            print(f"[error] source not found: {p}", file=sys.stderr)
            sys.exit(2)
        for f in cand:
            files.append(f)
            txt = open(f, encoding="utf-8", errors="replace").read()
            if f.endswith(".json"):
                try:
                    obj = json.loads(txt)
                    vals += leaves(obj)
                    json_groups(obj, groups)
                    continue
                except json.JSONDecodeError:
                    pass
            fv = nums_in(txt)
            vals += fv
            if len(fv) <= GROUP_MAX:
                groups.append(fv)
            else:
                blocks = re.split(r"\n\s*\n", txt)
                groups += [g for g in (nums_in(b) for b in blocks) if g and len(g) <= GROUP_MAX]
    return sorted(set(vals)), [sorted(set(g)) for g in groups if len(g) > 1], files


def same(v, s, dec):
    tol = 0.5 * 10 ** (-dec) + 1e-9
    return abs(abs(v) - abs(s)) <= tol


def support(num, vals, groups, derive):
    v, dec = num["value"], num["decimals"]
    for s in vals:
        if same(v, s, dec):
            return "direct", f"{s:g}"
        if num["pct"] and same(v, s * 100, dec):
            return "direct", f"{s:g} as %"
    if not derive:
        return None, ""
    pairs = list(itertools.chain.from_iterable(itertools.permutations([x for x in g if x > 0], 2) for g in groups))
    # most specific derivation first; ratios only for "x"/"×" values, percent change only for "%" values
    for a, b in pairs:
        if same(v, a - b, dec):
            return "derived", f"{a:g} - {b:g}"
    if num["pct"]:
        for a, b in pairs:
            if a <= 1 and b <= 1 and same(v, (a - b) * 100, dec):
                return "derived", f"({a:g} - {b:g}) x 100"
        for a, b in pairs:
            if same(v, (a - b) / b * 100, dec):
                return "derived", f"({a:g} - {b:g}) / {b:g} x 100"
    if num.get("ratio"):
        for a, b in pairs:
            if same(v, a / b, dec):
                return "derived", f"{a:g} / {b:g}"
    return None, ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", help=".tex (\\input followed), .md or .txt")
    ap.add_argument("--sources", nargs="+", required=True, help="files or directories the numbers must come from")
    ap.add_argument("--sections", help="comma list of abstract,intro,body (default: all)")
    ap.add_argument("--allow", default="", help="comma-separated numbers to accept (e.g. a venue year)")
    ap.add_argument("--derive", action="store_true",
                    help="also accept differences/ratios of numbers that sit together in a source (reported as "
                         "DERIVED). Off by default: compute margins with result_stats.py and pass its stats.json")
    ap.add_argument("--strict", action="store_true", help="exit 1 on DERIVED numbers too")
    ap.add_argument("--json", help="write the findings as JSON")
    a = ap.parse_args(argv)
    if not os.path.exists(a.draft):
        print(f"[error] not found: {a.draft}", file=sys.stderr)
        return 2
    secs = {s.strip() for s in a.sections.split(",") if s.strip()} if a.sections else None
    if secs and not secs <= {"abstract", "intro", "body"}:
        print(f"[error] --sections takes abstract, intro, body; got {sorted(secs)}", file=sys.stderr)
        return 2
    nums = draft_numbers(a.draft, secs)
    vals, groups, files = source_numbers(a.sources)
    vals += [x for x in (to_float(t) for t in a.allow.split(",") if t.strip()) if x is not None]
    derive = a.derive
    rows = []
    for num in nums:
        kind, how = support(num, vals, groups, derive)
        rows.append(dict(num, status=(kind or "unsupported").upper(), basis=how))
    bad = [r for r in rows if r["status"] == "UNSUPPORTED"]
    der = [r for r in rows if r["status"] == "DERIVED"]
    for r in bad + der:
        print(f"{r['status']:11s} {r['where']:>18}  {r['text']:>9}  [{r['section']}]  "
              f"{r['basis'] or 'not in any source'}\n{'':32}> {r['context']}")
    print(f"\n{len(rows)} number(s) checked against {len(files)} source file(s): {len(rows) - len(bad) - len(der)} "
          f"direct, {len(der)} derived, {len(bad)} unsupported")
    if bad:
        print("Every UNSUPPORTED number must be traced to a source, replaced by [TODO: number], or removed.")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"numbers": rows, "sources": files}, f, indent=2, ensure_ascii=False)
    return 1 if bad or (a.strict and der) else 0


if __name__ == "__main__":
    sys.exit(main())
