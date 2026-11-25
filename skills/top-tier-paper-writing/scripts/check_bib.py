#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Deterministic BibTeX checks (stdlib only). Online verification is a separate, manual step.

  B001  duplicate citation key                                             error
  B002  key cited in the paper but missing from the .bib                   error
  B003  required field missing for the entry type                          error
  B004  "et al." typed into the author field (use "and others" instead)    error
  B005  placeholder entry (TODO / FIXME / XXX / TBD / ?? in a field or key) error
  B101  duplicate title under different keys                               warning
  B102  year is not a 4-digit number                                       warning
  B103  acronym / CamelCase word in title not protected by braces          warning
        (BibTeX styles lowercase it: "FedAvg" -> "Fedavg")
  B104  arXiv / CoRR preprint: check whether a peer-reviewed version exists warning
  B105  entry never cited (only with --aux or --tex)                       info
  B106  @misc entry without url / doi / eprint / howpublished (unlocatable) warning

    uv run check_bib.py refs.bib
    uv run check_bib.py refs.bib --aux build/main.aux      # cited keys from the compiled .aux
    uv run check_bib.py refs.bib --tex paper/main.tex      # cited keys from \\cite commands

Exit codes: 0 no errors, 1 errors, 2 usage error.
"""
import argparse
import json
import os
import re
import sys

REQUIRED = {
    "article": ["author", "title", "journal", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "conference": ["author", "title", "booktitle", "year"],
    "book": ["title", "publisher", "year"],
    "incollection": ["author", "title", "booktitle", "publisher", "year"],
    "phdthesis": ["author", "title", "school", "year"],
    "mastersthesis": ["author", "title", "school", "year"],
    "techreport": ["author", "title", "institution", "year"],
    "misc": ["title"],
    "online": ["title", "url"],
}
SKIP_TYPES = {"comment", "string", "preamble"}


def parse_bib(text):
    """Yield (type, key, fields, line) for each entry."""
    for m in re.finditer(r"@(\w+)\s*([{(])", text):
        etype = m.group(1).lower()
        if etype in SKIP_TYPES:
            continue
        open_ch = m.group(2)
        close_ch = "}" if open_ch == "{" else ")"
        i, depth = m.end(), 1
        while i < len(text) and depth:
            if text[i] == open_ch or (open_ch == "(" and text[i] == "{"):
                depth += 1 if text[i] == open_ch else 0
            if text[i] == close_ch:
                depth -= 1
            elif text[i] == "{" and open_ch == "{":
                pass
            i += 1
        body = text[m.end():i - 1]
        key, _, rest = body.partition(",")
        line = text.count("\n", 0, m.start()) + 1
        yield etype, key.strip(), parse_fields(rest), line


def parse_fields(s):
    fields, i, n = {}, 0, len(s)
    while i < n:
        m = re.compile(r"\s*([A-Za-z][\w-]*)\s*=\s*").match(s, i)
        if not m:
            i += 1
            continue
        name, i = m.group(1).lower(), m.end()
        if i < n and s[i] == "{":
            depth, j = 0, i
            while j < n:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            fields[name] = s[i + 1:j]
            i = j + 1
        elif i < n and s[i] == '"':
            j = s.find('"', i + 1)
            fields[name] = s[i + 1:j if j > 0 else n]
            i = (j if j > 0 else n) + 1
        else:
            m2 = re.compile(r"[^,]*").match(s, i)
            fields[name] = m2.group(0).strip()
            i = m2.end()
    return fields


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", re.sub(r"\\[a-zA-Z]+", "", t.lower())).strip()


def unprotected_acronyms(title):
    # remove brace-protected parts, then look for words with an internal capital or all caps
    depth, out = 0, []
    for ch in title:
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            continue
        out.append(ch if depth == 0 else " ")
    # hyphenated parts are checked separately ("Non-IID" -> "IID"); the first word is checked too,
    # because BibTeX styles also lowercase everything after its first letter ("FedAvg" -> "Fedavg")
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", "".join(out))
    return sorted({w for w in words if len(w) > 1 and (w.isupper() or re.search(r"[a-z][A-Z]", w))})


def cited_keys(aux=None, tex=None):
    keys = set()
    if aux:
        with open(aux, encoding="utf-8", errors="replace") as f:
            for m in re.finditer(r"\\(?:citation|abx@aux@cite\{[^}]*\})\{([^}]+)\}", f.read()):
                keys.update(k.strip() for k in m.group(1).split(","))
    if tex:
        base = os.path.dirname(os.path.abspath(tex))
        todo, seen = [os.path.abspath(tex)], set()
        while todo:
            p = todo.pop()
            if p in seen or not os.path.exists(p):
                continue
            seen.add(p)
            with open(p, encoding="utf-8", errors="replace") as f:
                src = re.sub(r"(?<!\\)%.*", "", f.read())
            for m in re.finditer(r"\\(?:no)?cite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}", src):
                keys.update(k.strip() for k in m.group(1).split(","))
            for m in re.finditer(r"\\(?:input|include|subfile)\{([^}]+)\}", src):
                q = os.path.join(base, m.group(1))
                todo.append(q if q.endswith(".tex") else q + ".tex")
    return keys                       # may contain "*" (\nocite{*}: every entry counts as cited)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib", nargs="+", help=".bib file(s)")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--aux", help="compiled .aux file (most reliable list of cited keys)")
    src.add_argument("--tex", help="main .tex file (follows \\input)")
    ap.add_argument("--json", help="write findings as JSON")
    args = ap.parse_args(argv)

    entries = []
    for b in args.bib:
        if not os.path.isfile(b):
            print(f"[error] not found: {b}", file=sys.stderr)
            return 2
        with open(b, encoding="utf-8", errors="replace") as f:
            entries += [(os.path.basename(b),) + e for e in parse_bib(f.read())]

    out = []

    def add(code, where, msg):
        out.append({"code": code, "where": where, "message": msg})

    seen_keys, seen_titles = {}, {}
    for fname, etype, key, fields, line in entries:
        where = f"{fname}:{line} [{key}]"
        if key in seen_keys:
            add("B001", where, f"duplicate key (first at {seen_keys[key]})")
        seen_keys.setdefault(key, f"{fname}:{line}")
        for req in REQUIRED.get(etype, ["title"]):
            alt = {"journal": "journaltitle", "year": "date"}.get(req)
            if not fields.get(req, "").strip() and not (alt and fields.get(alt, "").strip()):
                add("B003", where, f"@{etype} is missing '{req}'")
        placeholder = re.compile(r"\b(?:TODO|FIXME|XXX|TBD|PLACEHOLDER)\b|\?\?")
        hits = [k for k, v in fields.items() if placeholder.search(v)] + (["key"] if placeholder.search(key) else [])
        if hits:
            add("B005", where, f"placeholder text in {', '.join(hits)}: replace with the verified reference")
        if etype == "misc" and not any(fields.get(k, "").strip() for k in ("url", "doi", "eprint", "howpublished")):
            add("B106", where, "@misc without url/doi/eprint/howpublished: a reader cannot locate this source")
        author = fields.get("author", "")
        if re.search(r"\bet\s*al\.?", author, re.I):
            add("B004", where, "author field contains 'et al.'; list all authors (the style abbreviates)")
        year = fields.get("year", "").strip("{} ")
        if year and not re.fullmatch(r"\d{4}", year):
            add("B102", where, f"year '{year}' is not a 4-digit number")
        title = fields.get("title", "")
        if title:
            nt = norm_title(title)
            if nt in seen_titles and seen_titles[nt] != key:
                add("B101", where, f"same title as [{seen_titles[nt]}]")
            seen_titles.setdefault(nt, key)
            acr = unprotected_acronyms(title)
            if acr:
                add("B103", where, f"protect with braces so the style keeps capitals: {', '.join(acr)}")
        venue = " ".join(fields.get(k, "") for k in ("journal", "booktitle", "publisher", "eprinttype",
                                                     "archiveprefix", "howpublished", "url", "note"))
        if re.search(r"arxiv|corr\b", venue, re.I) or fields.get("eprint"):
            add("B104", where, "preprint: check DBLP / Google Scholar for a peer-reviewed version and cite that")

    if args.aux or args.tex:
        for given in (args.aux, args.tex):
            if given and not os.path.exists(given):
                print(f"[error] not found: {given}", file=sys.stderr)
                return 2
        cited = cited_keys(args.aux, args.tex)
        everything = "*" in cited
        cited.discard("*")
        for k in sorted(cited - set(seen_keys)):
            add("B002", k, "cited but not in the .bib")
        for k in sorted(set(seen_keys) - cited) if not everything else []:
            add("B105", seen_keys[k] + f" [{k}]", "entry never cited")

    order = {"B0": 0, "B1": 1}
    out.sort(key=lambda r: (order.get(r["code"][:2], 2), r["code"], r["where"]))
    for r in out:
        print(f"{r['code']} {r['where']}: {r['message']}")
    errors = sum(r["code"].startswith("B00") for r in out)
    print(f"\n{len(entries)} entries, {errors} error(s), "
          f"{sum(r['code'].startswith('B10') and r['code'] != 'B105' for r in out)} warning(s)")
    print("Next: verify every entry against the publisher page / DBLP (see references/bibliography.md).")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
