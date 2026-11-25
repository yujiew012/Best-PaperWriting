#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Static checks for a LaTeX manuscript (stdlib only, no compilation needed).

Follows \\input / \\include / \\subfile from the main file and reports:

  E001  float's main \\label comes before its \\caption (wrong number)       error
  E003  \\ref / \\cref / \\autoref to a label that is never defined           error
  W002  float without \\caption                                             warning
  W003  float without \\label                                               warning
  W101  float label never referenced in the text                            warning
  W201  figure caption looks like Title Case (IEEE: sentence case)          warning
  W202  table caption looks like sentence case (IEEE: Title Case)           warning
  W203  caption states a conclusion ("outperforms", ...) (venues with neutral captions)   warning
  W204  caption's first sentence > 20 words (venues with takeaway-first captions)    warning
  W301  negative \\vspace / \\vskip or \\enlargethispage used to squeeze layout warning
  W302  vague or hedging phrase ("we hope", "very", "clearly", ...)          warning
  W303  paragraph quotes >= N numbers (reads the table instead of analysing) warning
  W304  "Fig. \\ref" with a breakable space (use Fig.~\\ref)                  warning
  W305  overclaiming verb (proves, conclusively, confirms that, ...) outside a formal proof warning
  W306  boilerplate / machine-written tell ("has attracted increasing attention", "delve", ...) warning
  W307  workflow trace left in the text ("supplied", "the provided results", move labels) warning
  W308  "Unlike X, we ..." compares a method with the authors                  warning
  W309  "although ..., but ..."                                              warning
  W310  copies a run of >= 6 words from the exemplar bank (references/exemplars/) warning
  W401  abstract length outside 150-250 words                               warning
  W402  conclusion length outside 120-200 words                             warning
  W403  a section the venue requires is missing (--venue, e.g. ACL Limitations) warning

    uv run lint_paper.py paper/main.tex
    uv run lint_paper.py paper/main.tex --caption-style sentence --json lint.json
    uv run lint_paper.py paper/main.tex --disable W302,W304 --strict
    uv run lint_paper.py paper/main.tex --venue acl     # caption case/content + required sections from the venue

Exit codes: 0 no errors (warnings allowed unless --strict), 1 errors, 2 usage error.
Rule rationale and fixes: references/lint_rules.md.
"""
import argparse
import bisect
import json
import os
import re
import sys

REF_CMDS = r"(?:ref|autoref|cref|Cref|vref|Vref|eqref|pageref|labelcref|nameref)\*?"
FLOAT_ENVS = ("figure", "figure*", "table", "table*", "wrapfigure", "wraptable")
VAGUE = [
    r"\bwe hope\b", r"\bvery\b", r"\bquite\b", r"\bobviously\b", r"\bclearly\b", r"\bit is worth noting\b",
    r"\bit should be noted\b", r"\bin order to\b", r"\ba lot of\b", r"\bextremely\b", r"\bhuge\b",
    r"\bwe believe\b", r"\bto some extent\b", r"\bsomewhat\b", r"\bbasically\b", r"\bactually\b",
]
OVERCLAIM = [
    r"\bconclusively\b", r"\bprov(?:e|es|ed|en|ing)\b(?!\s+(?:to|useful|difficult|hard|effective))",
    r"\bconfirm(?:s|ed|ing)? (?:that|our|the hypothesis)\b", r"\bundoubtedly\b", r"\bdefinitively\b",
    r"\bunequivocally\b", r"\bindisputabl[ey]\b", r"\bwithout (?:any )?doubt\b",
]
CONCLUSION_WORDS = [
    r"\boutperform\w*", r"\bsuperior\b", r"\bdemonstrat\w+", r"\bshows? that\b", r"\bclearly\b",
    r"\bsignificantly (?:better|higher|lower|worse)\b", r"\bbetter than\b", r"\bproves?\b", r"\bbeats?\b",
]
BOILERPLATE = [
    r"(?:has|have) attracted (?:increasing|growing|much|more and more) attention", r"\bhot topic\b",
    r"plays? an? (?:important|vital|key|crucial|significant|pivotal) role(?=\s*(?:in [^.,;]*)?[.;])",
    r"extensive experiments (?:demonstrate|show|verify|validate) the (?:effectiveness|superiority)",
    r"\bdelv(?:e|es|ing)\b", r"\bpivotal\b", r"\bparadigm shift\b", r"unlock(?:s|ing)? the (?:full )?potential",
    r"\bseamless(?:ly)?\b", r"\ba myriad of\b", r"\bin the realm of\b", r"\bsimple yet effective\b",
    r"\bcomprehensive experiments\b", r"\bthe landscape of\b", r"\bin today'?s (?:world|era)\b",
]
WORKFLOW = [
    r"\bsupplied\b", r"\bthe provided (?:results|numbers|data|evaluation|facts|materials?)\b",
    r"\bthe reported (?:evaluation|results|experiments)\b", r"\baccording to the (?:user|notes|input|materials)\b",
    r"\[(?:intro|abstract|relwork|method|exp|eval)\.[a-z.-]+\]", r"\b(?:Paragraph|Para\.) \d+:",
    r"(?<!\$)→(?![^$]*\$)",
]
SMALL_WORDS = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "as", "at", "by", "in", "of",
               "on", "to", "up", "via", "vs", "per", "with", "from", "into", "over", "than", "under"}


# ---------------------------------------------------------------------------
# source loading with file:line mapping
# ---------------------------------------------------------------------------

def strip_comment(line):
    out, i = [], 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            out.append(line[i:i + 2])
            i += 2
            continue
        if c == "%":
            break
        out.append(c)
        i += 1
    return "".join(out)


def load(path, seen=None):
    """Return list of (file, lineno, text) with inputs expanded and comments removed."""
    seen = seen or set()
    path = os.path.abspath(path)
    if path in seen:
        return []
    seen.add(path)
    base = os.path.dirname(path)
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for no, line in enumerate(f, 1):
            line = strip_comment(line.rstrip("\n"))
            m = (re.search(r"\\(?:input|include|subfile|@@input|InputIfFileExists)\{([^}]+)\}", line)
                 or re.search(r"\\(?:input|@@input)\s+([\w./-]+\.tex)\b", line))
            if m:
                inc = os.path.join(base, m.group(1).strip())
                if not inc.endswith(".tex"):
                    inc += ".tex"
                before, after = line[:m.start()], line[m.end():]
                if before.strip():
                    out.append((path, no, before))
                if os.path.exists(inc):
                    out.extend(load(inc, seen))
                else:
                    out.append((path, no, f"%MISSING-INPUT {m.group(1)}"))
                if after.strip():
                    out.append((path, no, after))
                continue
            out.append((path, no, line))
    return out


class Doc:
    def __init__(self, lines, root):
        self.root = root
        self.text = "\n".join(t for _, _, t in lines)
        self.starts, pos = [], 0
        for _, _, t in lines:
            self.starts.append(pos)
            pos += len(t) + 1
        self.lines = lines

    def where(self, offset):
        i = max(bisect.bisect_right(self.starts, offset) - 1, 0)
        f, n, _ = self.lines[i]
        return f"{os.path.relpath(f, self.root)}:{n}"


def braced(text, i):
    """Given text[i] == '{', return (content, end_index_after_brace)."""
    depth, j = 0, i
    while j < len(text):
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
        j += 1
    return text[i + 1:], len(text)


def plain(tex):
    """Rough LaTeX -> plain text for word counts and caption analysis."""
    t = re.sub(r"\$[^$]*\$", " X ", tex)
    t = re.sub(r"\\(?:cite\w*|ref|cref|Cref|autoref|label|eqref)\*?(\[[^\]]*\])?\{[^}]*\}", " ", t)
    t = re.sub(r"\\[a-zA-Z@]+\*?(\[[^\]]*\])?", " ", t)
    t = t.replace("{", " ").replace("}", " ").replace("~", " ")
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

def caption_case_issue(text, kind):
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", plain(text))
    cand = []
    for k, w in enumerate(words[1:], 1):
        if len(w) < 4 or w.lower() in SMALL_WORDS:
            continue
        if w.isupper() or re.search(r"[a-z][A-Z]", w) or re.search(r"\d", w):
            continue   # acronyms / CamelCase method names are proper nouns
        cand.append(w[0].isupper())
    if len(cand) < 3:
        return False
    ratio = sum(cand) / len(cand)
    return ratio >= 0.6 if kind == "title-in-figure" else ratio <= 0.4


def exemplar_grams(n=6):
    """6-grams of every quote in references/exemplars/*.jsonl (the draft must not reuse them)."""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "exemplars")
    grams = set()
    for name in ("moves.jsonl", "paragraphs.jsonl"):
        p = os.path.join(d, name)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    w = re.findall(r"[a-z0-9]+", json.loads(line).get("text", "").lower())
                    grams |= {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}
    return grams


def run(main_tex, caption_style, num_threshold, disabled, required_sections=(), caption_content="neutral"):
    root = os.path.dirname(os.path.abspath(main_tex))
    doc = Doc(load(main_tex), root)
    text = doc.text
    issues = []

    def add(code, offset, msg):
        if code not in disabled:
            issues.append({"code": code, "where": doc.where(offset), "message": msg})

    for m in re.finditer(r"%MISSING-INPUT (.+)", text):
        add("E003", m.start(), f"\\input file not found: {m.group(1)}")

    body_start = text.find("\\begin{document}")
    body_start = body_start if body_start >= 0 else 0

    # labels and references
    labels = {m.group(1).strip(): m.start() for m in re.finditer(r"\\label(?:\[[^\]]*\])?\{([^}]+)\}", text)}
    refs = {}
    for m in re.finditer(r"\\" + REF_CMDS + r"\{([^}]+)\}", text):
        for lab in m.group(1).split(","):
            refs.setdefault(lab.strip(), []).append(m.start())

    # floats
    float_labels = []
    env_re = "|".join(re.escape(e) for e in FLOAT_ENVS)
    for m in re.finditer(r"\\begin\{(" + env_re + r")\}", text):
        env = m.group(1)
        end = text.find("\\end{" + env + "}", m.end())
        end = end if end >= 0 else len(text)
        block = text[m.end():end]
        caps = [c for c in re.finditer(r"\\caption(?:\[[^\]]*\])?(?=\{)", block)]
        labs = [l for l in re.finditer(r"\\label(?:\[[^\]]*\])?\{([^}]+)\}", block)]
        kind = "figure" if "figure" in env else "table"
        if not caps:
            add("W002", m.start(), f"{env} without \\caption")
        if not labs:
            add("W003", m.start(), f"{env} without \\label")
        if caps and labs:
            last_cap = caps[-1].start()
            after = [l for l in labs if l.start() > last_cap]
            if not after:
                add("E001", m.end() + labs[-1].start(),
                    f"\\label{{{labs[-1].group(1)}}} precedes \\caption: move it after the caption")
            main_label = (after or labs)[0].group(1).strip()
            float_labels.append((main_label, m.start()))
        for c in caps:
            cap_text, _ = braced(block, c.end())
            off = m.end() + c.start()
            if caption_style == "ieee":
                if kind == "figure" and caption_case_issue(cap_text, "title-in-figure"):
                    add("W201", off, "figure caption looks like Title Case; IEEE figures use sentence case")
                if kind == "table" and caption_case_issue(cap_text, "sentence-in-table"):
                    add("W202", off, "table caption looks like sentence case; IEEE tables use Title Case")
            elif caption_style == "sentence" and caption_case_issue(cap_text, "title-in-figure"):
                add("W201", off, f"{kind} caption looks like Title Case; this venue uses sentence case")
            if caption_content == "neutral":
                for pat in CONCLUSION_WORDS:
                    w = re.search(pat, plain(cap_text), re.I)
                    if w:
                        add("W203", off, f"caption states a conclusion ('{w.group(0)}'); this venue keeps "
                                         f"conclusions in the text")
                        break
            else:
                first = re.split(r"(?<=[.!?])\s+", plain(cap_text).strip(), maxsplit=1)[0]
                if len(first.split()) > 20:
                    add("W204", off, f"first caption sentence has {len(first.split())} words; open with a "
                                     f"takeaway of 3-12 words, then describe the panels")

    for lab, pos in refs.items():
        if lab not in labels and not lab.startswith("#"):
            add("E003", pos[0], f"reference to undefined label '{lab}'")
    for lab, pos in float_labels:
        if lab not in refs:
            add("W101", pos, f"float '{lab}' is never referenced in the text")

    body = text[body_start:]
    for m in re.finditer(r"\\vspace\*?\{\s*-|\\vskip\s*-|\\enlargethispage", body):
        add("W301", body_start + m.start(), "layout squeezing command; fix float placement with the "
                                            "repair ladder in references/layout_and_typesetting.md")
    for pat in VAGUE:
        for m in re.finditer(pat, body, re.I):
            add("W302", body_start + m.start(), f"vague/hedging phrase '{m.group(0)}'")
    # overclaiming verbs, except inside theorem/proof/lemma environments
    no_proofs = re.sub(r"\\begin\{(proof|theorem|lemma|proposition|corollary)\*?\}.*?\\end\{\1\*?\}",
                       lambda mm: " " * len(mm.group(0)), body, flags=re.S)
    for pat in OVERCLAIM:
        for m in re.finditer(pat, no_proofs, re.I):
            add("W305", body_start + m.start(), f"overclaiming '{m.group(0)}': match the wording to the evidence "
                                                "(ablation -> causal; correlation -> 'is consistent with'; "
                                                "none -> hypothesis)")
    for pat in BOILERPLATE:
        for m in re.finditer(pat, body, re.I):
            add("W306", body_start + m.start(), f"boilerplate '{m.group(0)}': say the specific fact instead")
    for pat in WORKFLOW:
        for m in re.finditer(pat, body):
            add("W307", body_start + m.start(), f"workflow trace '{m.group(0)}': write as the authors, without "
                                                f"move labels or references to the inputs you were given")
    for m in re.finditer(r"\bUnlike [^,.;]{2,80},\s*we\b", body):
        add("W308", body_start + m.start(), "'Unlike X, we' compares a method with the authors; write "
                                            "'Unlike X, our method ...'")
    for m in re.finditer(r"\b[Aa]lthough\b[^.;]{0,200},\s*but\b", body):
        add("W309", body_start + m.start(), "'although ..., but': drop 'but'")
    bank = exemplar_grams() if "W310" not in disabled else set()
    if bank:
        prose = plain(re.sub(r"\\begin\{(" + env_re + r")\}.*?\\end\{\1\}", " ", body, flags=re.S))
        w = re.findall(r"[a-z0-9]+", prose.lower())
        hit_at = [i for i in range(len(w) - 5) if " ".join(w[i:i + 6]) in bank]
        runs, start = [], None
        for k, i in enumerate(hit_at):                      # merge overlapping 6-grams into runs
            if start is None:
                start = i
            if k + 1 == len(hit_at) or hit_at[k + 1] != i + 1:
                runs.append(" ".join(w[start:i + 6]))
                start = None
        for r in runs[:10]:
            add("W310", body_start, f"reuses {len(r.split())} words of an exemplar ('{r[:80]}'); exemplars "
                                    f"teach structure only")
    for m in re.finditer(r"\b(Fig\.|Figs\.|Figure|Table|Tables|Section|Sec\.|Eq\.|Algorithm|Appendix) "
                         r"\\(?:ref|cref|autoref)\{", body):
        add("W304", body_start + m.start(), f"use '{m.group(1)}~\\ref' (non-breaking space)")

    # paragraphs that dump numbers (outside floats / tabulars / math displays)
    stripped = re.sub(r"\\begin\{(" + env_re + r"|tabular\*?|table|equation\*?|align\*?)\}.*?\\end\{\1\}",
                      lambda mm: " " * len(mm.group(0)), body, flags=re.S)
    # real paragraph spans (blank-line separated), so reported lines never drift
    for pm in re.finditer(r"(?:[^\n]|\n(?!\s*\n))+", stripped):
        para = pm.group(0)
        if not para.strip():
            continue
        # a reported number: a decimal or a percentage/pp/x value that is not part of an
        # identifier such as GPT-4.1, Seed-1.6, 4.5V or 235B
        found = [m for m in re.finditer(
            r"(?<![\w.\-])\d+(?:\.\d+)?(?![\w.])(?:\s*(?:\\%|%|pp\b|×|x\b))?", para)
            if "." in m.group(0) or re.search(r"%|pp|×|x$", m.group(0))]
        nums = [m.group(0) for m in found]
        if len(nums) >= num_threshold:
            lead = found[0].start()                       # point at the first reported number
            add("W303", body_start + pm.start() + lead,
                f"paragraph quotes {len(nums)} numbers; keep 1-3 key numbers and let the table carry the rest")

    # abstract / conclusion length
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S)
    if m:
        n = len(plain(m.group(1)).split())
        if not 150 <= n <= 250:
            add("W401", m.start(), f"abstract has {n} words (target 150-250)")
    m = re.search(r"\\section\*?\{\s*Conclusions?[^}]*\}(.*?)(?=\\section|\\appendix|\\bibliography|"
                  r"\\printbibliography|\\end\{document\})", text, re.S | re.I)
    if m:
        n = len(plain(m.group(1)).split())
        if not 120 <= n <= 200:
            add("W402", m.start(), f"conclusion has {n} words (target 120-200, two paragraphs)")

    titles = [(m.start(), plain(braced(text, m.end() - 1)[0]).lower())
              for m in re.finditer(r"\\(?:section|subsection|paragraph)\*?(?:\[[^\]]*\])?\{", text)]
    for req in required_sections:
        if not any(req.lower() in title for _, title in titles):
            add("W403", body_start, f"the venue requires a '{req}' section; none found")

    issues.sort(key=lambda i: (i["code"][0] != "E", i["code"], i["where"]))
    return issues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("main_tex")
    ap.add_argument("--caption-style", choices=["ieee", "sentence", "off"],
                    help="ieee: figures sentence case, tables Title Case; sentence: both sentence case "
                         "(default: from --venue, else ieee)")
    ap.add_argument("--venue", help="venue profile from references/venues.json: sets the caption style and the "
                                    "required sections")
    ap.add_argument("--caption-content", choices=["neutral", "takeaway"],
                    help="neutral: no conclusions in captions (W203); takeaway: captions open with the takeaway "
                         "(W204). Default: from --venue, else neutral")
    ap.add_argument("--numbers", type=int, default=6, help="W303 threshold (numbers per paragraph)")
    ap.add_argument("--disable", default="", help="comma-separated codes to skip, e.g. W302,W304")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    ap.add_argument("--max-per-code", type=int, default=15, help="print at most N findings per code")
    ap.add_argument("--json", help="write all findings as JSON")
    args = ap.parse_args(argv)
    if not os.path.isfile(args.main_tex):
        print(f"[error] not found: {args.main_tex}", file=sys.stderr)
        return 2

    style, required, content = args.caption_style, (), args.caption_content
    if args.venue:
        vpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "venues.json")
        with open(vpath, encoding="utf-8") as f:
            venues = json.load(f)["venues"]
        if args.venue not in venues:
            print(f"[error] unknown venue '{args.venue}'; choose from: {', '.join(venues)}", file=sys.stderr)
            return 2
        v = venues[args.venue]
        required = v.get("required_sections", [])
        content = content or v.get("caption_content", "neutral")
        if style is None:
            case = v.get("caption_case", {})
            style = ("off" if not case.get("figure") else
                     "ieee" if case.get("table") == "title" else "sentence")
    issues = run(args.main_tex, style or "ieee", args.numbers,
                 {c.strip() for c in args.disable.split(",") if c.strip()}, required, content or "neutral")
    errors = [i for i in issues if i["code"].startswith("E")]
    warns = [i for i in issues if i["code"].startswith("W")]
    shown = {}
    for i in issues:
        shown[i["code"]] = shown.get(i["code"], 0) + 1
        if shown[i["code"]] <= args.max_per_code:
            print(f"{i['code']} {i['where']}: {i['message']}")
    for code, n in shown.items():
        if n > args.max_per_code:
            print(f"{code}: ... {n - args.max_per_code} more (see --json)")
    print(f"\n{len(errors)} error(s), {len(warns)} warning(s)")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2, ensure_ascii=False)
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
