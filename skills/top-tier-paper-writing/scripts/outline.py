#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Reverse outline of a manuscript: every paragraph reduced to its topic sentence.

    uv run outline.py paper/main.tex                       # print the outline and the structure checks
    uv run outline.py paper/main.tex --claims claim_map.json --md outline.md

Read the outline alone: the topic sentences, in order, should tell the paper's story (the 7W of
references/writing/seven_principles.md §1); with --claims the claim map's `story` is printed above the
outline to compare against. Structure checks (seven_principles.md §2 and §4):

  WARN  a section that starts directly with a \\subsection: it has no opening paragraph stating its purpose
  WARN  a section without any paragraph (only a heading)
  NOTE  a topic sentence longer than 35 words (it probably carries two ideas: split the paragraph)
  NOTE  a labelled section that nothing cross-references (\\ref/\\cref) from elsewhere

Exit 0 (advisory); --strict exits 1 on WARN; 2 on usage errors.
"""
import argparse
import json
import os
import re
import sys

SECTION = re.compile(r"\\(section|subsection|subsubsection)\*?(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
TOPIC_MAX = 35


def read(path, seen=None):
    seen = seen or set()
    path = os.path.abspath(path)
    if path in seen or not os.path.exists(path):
        return ""
    seen.add(path)
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = re.sub(r"(?<!\\)%.*", "", line)
        m = re.search(r"\\(?:input|include)\{([^}]+)\}", line)
        if m:
            inc = os.path.join(os.path.dirname(path), m.group(1))
            line = line[:m.start()] + "\n\n" + read(inc if inc.endswith(".tex") else inc + ".tex", seen) + "\n\n" \
                + line[m.end():]
        out.append(line)
    return "".join(out)


def plain(t):
    t = re.sub(r"\$[^$]*\$", "X", t)
    t = re.sub(r"\\(?:cite\w*|label)\*?(?:\[[^\]]*\])?\{[^}]*\}", "", t)
    t = re.sub(r"\\c?ref\{[^}]*\}", "1", t)
    t = re.sub(r"\\(?:textbf|textit|emph|text|textsc|mathrm)\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\[A-Za-z]+\*?", "", t).replace("{", "").replace("}", "").replace("~", " ")
    t = " ".join(t.split())
    return re.sub(r"\s+([.,;:!?)])", r"\1", t)          # space left where a citation was removed


def first_sentence(p):
    p = p.split(" - ", 1)[0].strip()                  # a list paragraph: the lead-in is its topic sentence
    m = re.search(r"^(.+?[.!?:])(?=\s+[A-Z(]|$)", p)
    return m.group(1) if m else p


def continuation(p):
    """A paragraph that continues the previous one (e.g. 'where x is ...' after an equation)."""
    return bool(re.match(r"[a-z]", p))


def parse(text):
    body = text.split("\\begin{document}", 1)[-1].split("\\end{document}", 1)[0]
    body = re.sub(r"\\begin\{(figure|table|equation|align|algorithm|tabular|lstlisting|verbatim|thebibliography)\*?\}"
                  r".*?\\end\{\1\*?\}", "\n", body, flags=re.S)
    body = re.sub(r"\\(?:bibliography|bibliographystyle|maketitle|appendix)\b(?:\{[^}]*\})?", "\n\n", body)
    nodes = []          # (level, title, label, [paragraphs], starts_with_subsection)
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", body, re.S)
    if abstract:
        nodes.append({"level": 0, "title": "Abstract", "label": None, "paras": paragraphs(abstract.group(1)),
                      "opens_with_sub": False})
        body = body.replace(abstract.group(0), "\n")
    pos, last = 0, None
    marks = list(SECTION.finditer(body))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        chunk = body[m.end():end]
        lab = re.search(r"\\label\{([^}]+)\}", chunk[:200])
        level = {"section": 1, "subsection": 2, "subsubsection": 3}[m.group(1)]
        nxt = marks[i + 1] if i + 1 < len(marks) else None
        nodes.append({"level": level, "title": plain(m.group(2)), "label": lab.group(1) if lab else None,
                      "paras": paragraphs(chunk),
                      "opens_with_sub": bool(level == 1 and nxt is not None and nxt.group(1) == "subsection"
                                             and not paragraphs(chunk))})
    return nodes


def paragraphs(chunk):
    out = []
    for p in re.split(r"\n\s*\n", chunk):
        p = re.sub(r"\\label\{[^}]*\}", "", p)
        p = re.sub(r"\\begin\{(itemize|enumerate)\}|\\end\{(itemize|enumerate)\}", " ", p)
        p = re.sub(r"\\item\b", " - ", p)
        txt = plain(p)
        if len(txt.split()) >= 4:
            out.append(txt)
    return out


def check(nodes, text):
    issues = []
    refs = set()
    for m in re.finditer(r"\\(?:c|C|auto|name|v)?ref\{([^}]+)\}", text):
        refs.update(x.strip() for x in m.group(1).split(","))
    for i, n in enumerate(nodes):
        if n["title"] == "Abstract":
            continue
        if n["opens_with_sub"]:
            issues.append(("WARN", f"§ {n['title']}: starts directly with a subsection; open with a paragraph that "
                                   f"states the section's purpose and organization"))
        sub_follows = i + 1 < len(nodes) and nodes[i + 1]["level"] > n["level"]
        if not n["paras"] and not sub_follows:
            issues.append(("WARN", f"§ {n['title']}: no paragraph under this heading"))
        for k, p in enumerate(n["paras"], 1):
            ts = first_sentence(p)
            if not continuation(p) and len(ts.split()) > TOPIC_MAX:
                issues.append(("NOTE", f"§ {n['title']} ¶{k}: topic sentence of {len(ts.split())} words; state the "
                                       f"paragraph's one idea first: '{ts[:70]}...'"))
        if n["label"] and n["label"] not in refs and n["level"] == 1 and \
                not re.match(r"(intro|introduction|conclu)", n["title"], re.I):
            issues.append(("NOTE", f"§ {n['title']}: label '{n['label']}' is never cross-referenced; point to it "
                                   f"from the introduction or the sections that rely on it"))
    return issues


def render(nodes, story=None):
    lines = []
    if story:
        lines += ["## Story (claim map)", ""] + [f"- **{k}:** {v}" for k, v in story.items()] + [""]
    lines += ["## Reverse outline (topic sentences)", ""]
    for n in nodes:
        lines.append(f"{'#' * (n['level'] + 2) if n['level'] else '###'} {n['title']}")
        for k, p in enumerate(n["paras"], 1):
            lines.append(f"{k}. {'(continued) ' if continuation(p) else ''}{first_sentence(p)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", help="main .tex file (\\input followed)")
    ap.add_argument("--claims", help="claim_map.json: print its story block above the outline")
    ap.add_argument("--md", help="write the outline (and story) as Markdown")
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN")
    a = ap.parse_args(argv)
    if not os.path.exists(a.tex):
        print(f"[error] not found: {a.tex}", file=sys.stderr)
        return 2
    story = None
    if a.claims:
        try:
            story = json.load(open(a.claims, encoding="utf-8")).get("story")
        except (OSError, json.JSONDecodeError, AttributeError) as e:
            print(f"[error] cannot read {a.claims}: {e}", file=sys.stderr)
            return 2
    text = read(a.tex)
    nodes = parse(text)
    if not nodes:
        print("[error] no abstract or sections found", file=sys.stderr)
        return 2
    out = render(nodes, story)
    print(out)
    issues = check(nodes, text)
    for level, msg in sorted(issues, key=lambda x: x[0] != "WARN"):
        print(f"{level:5s} {msg}")
    n_warn = sum(1 for l, _ in issues if l == "WARN")
    print(f"\n{sum(len(n['paras']) for n in nodes)} paragraph(s) in {len(nodes)} heading(s): {n_warn} warning(s), "
          f"{len(issues) - n_warn} note(s). Read the topic sentences alone: do they tell the story in order?")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(out + "\n" + "\n".join(f"- {l}: {m}" for l, m in issues) + "\n")
        print(f"[ok] wrote {a.md}")
    return 1 if a.strict and n_warn else 0


if __name__ == "__main__":
    sys.exit(main())
