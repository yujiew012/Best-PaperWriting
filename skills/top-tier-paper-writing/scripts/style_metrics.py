#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Style metrics of the abstract and introduction, compared with a corpus profile (two-sided).

    uv run style_metrics.py paper/main.tex                       # profile chosen from --domain, else general
    uv run style_metrics.py paper/main.tex --domain security_privacy --json style.json
    uv run style_metrics.py exemplar.pdf --raw --json m.json     # metrics only (used by evolve.py corpus-stats)
    uv run style_metrics.py draft.md --no-dashes                 # also flag punctuation dashes (house style)

Input: .tex (\\begin{abstract} and the Introduction section, \\input followed), .md (# Abstract,
# Introduction), .txt or .pdf (pdftotext; headings "Abstract" and "1 Introduction").

Profiles live in references/style_corpus/<name>.json and hold p10..p90 per metric for 'abstract' and
'intro'. A domain profile is used when it has >= 5 papers (evolve.py corpus-stats builds them from
exemplar papers); otherwise the general profile is used and every finding is downgraded to NOTE,
because a corpus from another area is a reference, not a target.

Every rule is two-sided: being far below the corpus is as much a tell as being far above it
(no connectors at all reads choppy; merging every short sentence produces ", making ..." tails).
Levels: WARN outside p10-p90 of a matching profile, NOTE otherwise. Exit 0 always (advisory);
--strict exits 1 on WARN.
"""
import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texpaths import expand_simple_macros, refs_to_text, resolve_input  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "..", "references", "style_corpus")
GENERAL = "general"
MIN_PAPERS = 5

CONNECTORS = ["however", "therefore", "thus", "hence", "consequently", "moreover", "furthermore", "additionally",
              "in addition", "yet", "nevertheless", "nonetheless", "whereas", "while", "in contrast", "instead",
              "rather", "unlike", "accordingly", "as a result", "to this end", "on the other hand", "specifically",
              "in particular", "more specifically", "as such", "importantly", "finally", "to summarize"]
HEDGES = ["may", "might", "could", "likely", "possibly", "suggest", "suggests", "appear to", "appears to",
          "seem to", "seems to", "potentially"]
BOOSTERS = ["significantly", "substantially", "dramatically", "remarkably", "notably", "surprisingly",
            "strikingly", "drastically", "considerably", "greatly"]
PRAISE = ["novel", "effective", "efficient", "powerful", "superior", "state-of-the-art", "SOTA", "outperform",
          "outperforms", "first"]
INSIGHTS = ["key insight", "central insight", "core insight", "key idea", "key observation", "central observation",
            "main insight", "our insight"]
# trailing participial clause that restates significance: ", making ...", ", thereby enabling ..."
PART = re.compile(r",\s+(?:thereby\s+)?(?!during|including|according|following|using|regarding|concerning|"
                  r"excluding|notwithstanding)[a-z]{3,}ing\b")
ANTI = re.compile(r"\b(?:is|are|does|do|was|were) not\b|\bnot yet\b|\bnot the same\b|\brather than\b|"
                  r"\binstead of\b|\bneed not\b|\bisn't\b|\baren't\b")
DASH = re.compile(r"—|\s[–-]\s")
CITE = re.compile(r"\[(?:\s*\d+[a-z]?\s*[,;–—-]?)+\]|\[c\]|\([A-Z][^()]{0,60}?(?:19|20)\d{2}[a-z]?\)")
WORD = re.compile(r"[^\W_]+(?:[-’'/.,][^\W_]+)*(?:%|×)?", re.UNICODE)
REF = re.compile(r"\b(?:Figures?|Figs?\.?|Tables?|Tabs?\.?|Sections?|Secs?\.?|Eqs?\.?|Equations?)\s*\(?\d+(?:\.\d+)*\)?",
                 re.I)
NUM = re.compile(r"(?<![\w])\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+(?:\.\d+)?)?(?:%|×)?")

# metric -> (direction checked, why); "high": warn above p90; "low": below p10; "both"
RULES = {
    "sent_len_mean": ("both", "mean sentence length; keep short sentences for the pivots and let the rest carry a "
                              "relation (because / while / by / which)"),
    "short_sent_ratio": ("high", "share of short sentences (<= 12 words); keep 3-4 short pivots"),
    "numbers": ("high", "numbers; keep the headline numbers and move the rest to the evaluation"),
    "connector_per_100w": ("both", "logical connectors per 100 words (however/thus/...); let sentence order carry "
                                   "most of the logic, but not none of it"),
    "colon_or_dash_sentences": ("high", "share of sentences with a colon or dash"),
    "participle_tail_ratio": ("high", "share of sentences ending in ', making ...'-type clauses; use because/while/"
                                      "by/which or end the sentence"),
    "hedge_count": ("high", "hedges (may/could/suggest/...)"),
    "booster_count": ("high", "boosters (significantly/remarkably/...)"),
    "self_praise_count": ("low", "evaluative claims (outperforms/efficient/first/...); state the strongest supported "
                                 "advantage"),
    "antithesis_ratio": ("high", "aphoristic contrasts ('X is not Y', 'rather than'); keep one for the thesis"),
}


def phrase_hits(text, phrases):
    pat = r"(?<!\w)(?:" + "|".join(re.escape(x) for x in sorted(phrases, key=len, reverse=True)) + r")(?!\w)"
    return list(re.finditer(pat, text, re.I))


def words(t):
    return WORD.findall(CITE.sub("", t))


def split_sentences(p):
    prot = p
    for pat in (r"\b(?:e\.g\.|i\.e\.|w\.r\.t\.|i\.i\.d\.)", r"\bet al\.", r"\b(?:Fig|Figs|Tab|Eq|Eqs|Sec|cf|vs|etc|"
                r"resp|approx)\.", r"(?<=\d)\.(?=\d)"):
        prot = re.sub(pat, lambda m: m.group().replace(".", "\uE000"), prot, flags=re.I)
    out, start = [], 0
    for m in re.finditer(r"[.!?][”’\"\)\]]*(?=\s|$)", prot):
        out.append(p[start:m.end()].strip())
        start = m.end()
    if p[start:].strip():
        out.append(p[start:].strip())
    return [s for s in out if s]


def number_tokens(t):
    t = CITE.sub(" ", t)
    t = re.sub(r"\([^)]*\)", lambda m: re.sub(r"\b(?:19|20)\d{2}\b", " ", m.group()), t)
    t = REF.sub(" ", t)
    t = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*\b",
               lambda m: " " if any(c.isdigit() for c in m.group()) else m.group(), t)
    return NUM.findall(t)


def connector_hits(s):
    hits = []
    for m in phrase_hits(s, CONNECTORS):
        if m.group().lower() == "while":          # only contrastive 'while' (sentence start or after a comma)
            before = s[:m.start()].rstrip()
            if before and not before.endswith(","):
                continue
        hits.append(m)
    return hits


def short_run_max(paras, th=15):
    best = 0
    for p in paras:
        cur = 0
        for x in split_sentences(p):
            cur = cur + 1 if len(words(x)) < th else 0
            best = max(best, cur)
    return best


def metrics(paras):
    ss = [s for p in paras for s in split_sentences(p)]
    lens = [len(words(s)) for s in ss]
    n, w = max(len(ss), 1), max(sum(lens), 1)
    return {
        "words": sum(lens), "sentences": len(ss), "prose_paragraphs": len(paras),
        "sent_len_mean": round(statistics.mean(lens), 3) if lens else 0.0,
        "short_sent_ratio": round(sum(x <= 12 for x in lens) / n, 3),
        "numbers": sum(len(number_tokens(s)) for s in ss),
        "connector_per_100w": round(sum(len(connector_hits(s)) for s in ss) / w * 100, 3),
        "colon_or_dash_sentences": round(sum(bool(re.search(r"(?<![\d/]):(?![/\d])|—|\s[–-]\s", s)) for s in ss) / n, 3),
        "hedge_count": sum(len(phrase_hits(s, HEDGES)) for s in ss),
        "booster_count": sum(len(phrase_hits(s, BOOSTERS)) for s in ss),
        "self_praise_count": sum(len(phrase_hits(s, PRAISE)) for s in ss),
        "insight_formula_count": sum(len(phrase_hits(s, INSIGHTS)) for s in ss),
        "we_sentence_ratio": round(sum(bool(re.match(r"[\"“(]?(We|Our)\b", s)) for s in ss) / n, 3),
        "participle_tail_ratio": round(sum(bool(PART.search(s)) for s in ss) / n, 3),
        "antithesis_ratio": round(sum(bool(ANTI.search(s)) for s in ss) / n, 3),
        "short_run_max": short_run_max(paras),
        "dash_count": sum(len(DASH.findall(s)) for s in ss),
    }


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def read_tex(path, seen=None, root=None):
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
            out.append(line[:m.start()] + read_tex(resolve_input(m.group(1), path, root), seen, root)
                       + line[m.end():])
        else:
            out.append(line)
    return "".join(out)


def tex_to_text(t):
    t = re.sub(r"\\begin\{(figure|table|equation|align|algorithm)\*?\}.*?\\end\{\1\*?\}", " ", t, flags=re.S)
    t = re.sub(r"\\(?:todo|TODO)\{(?:[^{}]|\{[^{}]*\})*\}|\[TODO[^\]]*\]", " ", t)
    t = re.sub(r"\\cite[tp]?\*?(\[[^\]]*\])?\{[^}]*\}", "[c]", t)
    t = refs_to_text(t)
    t = re.sub(r"\\(?:label|section|subsection|paragraph)\*?\{[^}]*\}", "", t)
    t = re.sub(r"\\item\s*", "\n\n", t)
    t = t.replace("---", "—").replace("--", "–").replace("``", "“").replace("''", "”").replace("~", " ")
    t = t.replace("\\times", "×").replace("\\%", "%")
    for _ in range(3):
        t = re.sub(r"\\(?:textbf|textit|emph|mathrm|text|textsc|texttt)\{([^{}]*)\}", r"\1", t)
    t = re.sub(r"\\[A-Za-z]+\*?", "", t).replace("{", "").replace("}", "").replace("$", "")
    return t


def paragraphs(text):
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 3]


def from_tex(path):
    raw = expand_simple_macros(read_tex(path))
    secs = {}
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.S)
    if m:
        secs["abstract"] = paragraphs(tex_to_text(m.group(1)))
    m = re.search(r"\\section\*?\{\s*Introduction\s*\}(.*?)(?=\\section\*?\{|\\appendix|\\bibliography|\\end\{document\})",
                  raw, re.S | re.I)
    if m:
        secs["intro"] = paragraphs(tex_to_text(m.group(1)))
    return secs


def from_md(path):
    secs, cur = {}, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        h = re.match(r"^#+\s*(?:\d+\.?\s*)?(abstract|introduction)\b", ln, re.I)
        if h:
            cur = "abstract" if h.group(1).lower() == "abstract" else "intro"
            secs[cur] = ""
            continue
        if re.match(r"^#+\s", ln):
            cur = None
        if cur:
            secs[cur] += re.sub(r"^\s*[-*]\s+", "\n\n", ln)
    return {k: paragraphs(re.sub(r"\[TODO[^\]]*\]", " ", v)) for k, v in secs.items()}


def clean_pdf_text(t):
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)                       # hyphenation at line ends
    out, skip = [], False
    for ln in t.split("\n"):
        s = ln.strip()
        if re.match(r"^(Figure|Fig\.|Table)\s*\d+\s*[:.]", s):   # captions run until a blank line
            skip = True
        if not s:
            skip = False
            out.append("")
            continue
        if skip or re.match(r"^\*|^arXiv:", s):                    # footnote marks, arXiv stamp
            continue
        out.append(s)
    return "\n".join(out)


def from_plain(text):
    text = clean_pdf_text(text)
    secs = {}
    a = re.search(r"(?mi)^\s*abstract\s*[.:—-]?\s*$|^\s*abstract[.:—]\s*", text)
    intro = re.search(r"(?m)^\s*(?:1|I)\.?\s*\n*\s*Introduction\s*$", text) or \
        re.search(r"(?mi)^\s*(?:1\.?|I\.)?\s*Introduction\s*$", text)
    if a and intro and intro.start() > a.end():
        secs["abstract"] = [" ".join(text[a.end():intro.start()].split())]
    if intro:
        rest = text[intro.end():]
        nxt = re.search(r"(?m)^\s*(?:2|II)\.?\s+[A-Z][A-Za-z ,&-]{2,60}$|^\s*(?:2|II)\s*\n\s*[A-Z][A-Za-z ,&-]{2,60}$",
                        rest)
        secs["intro"] = paragraphs(rest[:nxt.start()] if nxt else rest[:8000])
        # pdftotext breaks paragraphs at every column; merge lines inside a paragraph
    return secs


def extract(path):
    low = path.lower()
    if low.endswith(".tex"):
        return from_tex(path)
    if low.endswith(".md"):
        return from_md(path)
    if low.endswith(".pdf"):
        if not shutil.which("pdftotext"):
            sys.exit("[error] pdftotext not found (poppler-utils)")
        text = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True).stdout
        return from_plain(text)
    return from_plain(open(path, encoding="utf-8", errors="replace").read())


# ---------------------------------------------------------------------------
# profiles and comparison
# ---------------------------------------------------------------------------

def load_profile(domain=None, name=None):
    """(profile, matching) -- matching is False when a profile from another area stands in."""
    if name:
        p = name if name.endswith(".json") else os.path.join(CORPUS, f"{name}.json")
        if not os.path.exists(p):
            have = sorted(f[:-5] for f in os.listdir(CORPUS) if f.endswith(".json"))
            print(f"[error] style profile not found: {name} (available: {', '.join(have)})", file=sys.stderr)
            sys.exit(2)
        return json.load(open(p, encoding="utf-8")), True
    if domain:
        p = os.path.join(CORPUS, f"{domain}.json")
        if os.path.exists(p):
            prof = json.load(open(p, encoding="utf-8"))
            if prof.get("n_papers", 0) >= MIN_PAPERS:
                return prof, True
    prof = json.load(open(os.path.join(CORPUS, f"{GENERAL}.json"), encoding="utf-8"))
    return prof, bool(domain) and domain in prof.get("domains", [])


def band(v, d):
    for p in (10, 25, 50, 75, 90):
        if v <= d[f"p{p}"]:
            return f"<=p{p}"
    return ">p90"


def compare(sec, m, prof, matching, no_dashes=False):
    findings = []
    stats = prof.get(sec, {})
    for key, (direction, why) in RULES.items():
        d = stats.get(key)
        if not d:
            continue
        hi = direction in ("high", "both") and m[key] > d["p90"]
        lo = direction in ("low", "both") and m[key] < d["p10"]
        if hi or lo:
            side = f"above p90 ({d['p90']})" if hi else f"below p10 ({d['p10']})"
            findings.append(("WARN" if matching else "NOTE", key, f"{why}: {m[key]} is {side}; aim near the median "
                                                                  f"({d['p50']})"))
    if sec == "abstract" and m["insight_formula_count"] >= 1:
        findings.append(("WARN", "insight_formula_count", "the abstract announces 'our key insight'; state the "
                                                          "observation itself"))
    if sec == "intro" and m["insight_formula_count"] >= 2:
        findings.append(("WARN", "insight_formula_count", "more than one 'key insight'-type formula"))
    limit = 3 if sec == "intro" else 2
    if m["short_run_max"] >= limit:
        findings.append(("WARN", "short_run_max", f"{m['short_run_max']} consecutive sentences under 15 words; merge "
                                                  f"bare facts so each sentence carries a relation"))
    if no_dashes and m["dash_count"]:
        findings.append(("WARN", "dash_count", f"{m['dash_count']} punctuation dash(es); house style: use a colon, a "
                                               f"comma or a second sentence"))
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--domain", help="domain id (references/domains/); selects references/style_corpus/<domain>.json")
    ap.add_argument("--profile", help="profile name or path (overrides --domain)")
    ap.add_argument("--raw", action="store_true", help="print metrics only, no comparison")
    ap.add_argument("--no-dashes", action="store_true", help="house style without punctuation dashes")
    ap.add_argument("--json", help="write metrics and findings as JSON")
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN")
    a = ap.parse_args(argv)
    if not os.path.exists(a.file):
        print(f"[error] not found: {a.file}", file=sys.stderr)
        return 2
    secs = {k: v for k, v in extract(a.file).items() if v}
    if not secs:
        print("[error] no abstract or introduction found (tex: \\begin{abstract} / \\section{Introduction}; "
              "md: '# Abstract' / '# Introduction')", file=sys.stderr)
        return 2
    out = {"file": a.file, "sections": {}}
    if a.raw:
        for sec, paras in secs.items():
            out["sections"][sec] = {"metrics": metrics(paras)}
            print(f"== {sec}")
            for k, v in out["sections"][sec]["metrics"].items():
                print(f"  {k:26s} {v}")
    else:
        prof, matching = load_profile(a.domain, a.profile)
        out["profile"] = {"name": prof.get("name"), "n_papers": prof.get("n_papers"), "matching": matching}
        print(f"profile: {prof.get('name')} ({prof.get('n_papers')} papers"
              f"{'' if matching else '; from another area: findings are NOTEs, not targets'})")
        warns = 0
        for sec, paras in secs.items():
            m = metrics(paras)
            fs = compare(sec, m, prof, matching, a.no_dashes)
            out["sections"][sec] = {"metrics": m, "findings": [dict(level=l, metric=k, msg=s) for l, k, s in fs]}
            print(f"\n== {sec}: {m['words']} words, {m['sentences']} sentences")
            for k, v in m.items():
                d = prof.get(sec, {}).get(k)
                ref = f"   corpus p10/p50/p90 {d['p10']}/{d['p50']}/{d['p90']} ({band(v, d)})" if d else ""
                print(f"  {k:26s} {v:<8}{ref}")
            for level, k, s in fs:
                print(f"{level:5s} {sec}: {s}")
            warns += sum(l == "WARN" for l, _, _ in fs)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    return 1 if a.strict and not a.raw and warns else 0


if __name__ == "__main__":
    sys.exit(main())
