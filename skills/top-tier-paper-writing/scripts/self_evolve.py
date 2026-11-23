#!/usr/bin/env python3
"""
Skill Self-Evolution Module (技能自进化模块)
Part of top-tier-paper-writing skill.

Mines candidate sentences from a paper (e.g. MinerU Markdown of a full text) or
from arXiv abstracts, using keyword patterns for three kinds of expressions:
causal attributions, critical transitions in related work, and figure phrasings.

This is pattern matching, not language understanding: every candidate should
be reviewed by a person. By default the script only PREVIEWS candidates;
pass --apply to append them to references/mechanism_sentence_bank.md and log
the event in EVOLUTION_LOG.md.

Note: arXiv mode only sees titles + abstracts (the API does not return full
text), so it yields far fewer and more generic sentences than a full paper.

Usage:
    python3 self_evolve.py --file paper.md                    # preview
    python3 self_evolve.py --file paper.md --apply            # write to the bank
    python3 self_evolve.py --arxiv_query "federated continual learning" --max_papers 5
"""

import os
import re
import sys
import argparse
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SENTENCE_BANK_PATH = SKILL_ROOT / "references" / "mechanism_sentence_bank.md"
EVOLUTION_LOG_PATH = SKILL_ROOT / "EVOLUTION_LOG.md"
ARXIV_API = "https://export.arxiv.org/api/query"

# Patterns are applied to one sentence at a time (case-insensitive).
PATTERNS = {
    "mechanisms": [
        r"\b(?:stems?|stemming) from\b", r"\bowing to\b", r"\battributable to\b",
        r"\b(?:is|are) attributed to\b", r"\bcan be traced (?:back )?to\b",
        r"\b(?:decouples?|disentangles?|decoupling)\b.+\bfrom\b",
        r"\bpenaliz\w+\b.+\b(?:thereby|thus)\b",
        r"\bsuppress\w*\b.+\b(?:without|while)\b",
        r"\bmitigat\w+\b.+\bby (?:dynamically|adaptively|explicitly)\b",
        r"\bthis (?:is because|can be explained by|behavior arises)\b",
    ],
    "rhetoricals": [
        r"^despite (?:its|their|these|the)\b.+\b(?:suffer|fall short|fail|remain)\w*\b",
        r"\bwhile (?:prior|existing|previous) (?:studies|works?|methods?|approaches)\b.+\b(?:overlook|ignore|neglect|assume)\w*\b",
        r"\bthe fundamental limitation\b",
        r"\b(?:existing|prior) (?:methods|approaches|works) (?:implicitly |largely |typically )?(?:assume|overlook|ignore)\b",
    ],
    "figure_phrases": [
        r"^as (?:depicted|shown|illustrated) in (?:fig\.|figure|table)\s*\d+",
        r"\bshaded (?:area|region|band)s? (?:denotes?|indicates?|represents?)\b",
    ],
}
LENGTH_LIMITS = {"mechanisms": (40, 320), "rhetoricals": (40, 320), "figure_phrases": (30, 260)}

# Abbreviations that must not end a sentence.
_ABBREV = ["Fig.", "Figs.", "Eq.", "Eqs.", "Sec.", "Tab.", "e.g.", "i.e.", "et al.",
           "vs.", "cf.", "etc.", "resp.", "approx.", "No.", "Ref."]


def clean_text(text: str) -> str:
    """Undo common MinerU / PDF-to-Markdown artifacts."""
    text = re.sub(r"<(sub|sup)>(.*?)</\1>", r"\2", text, flags=re.S)   # e<sub>p</sub> -> ep
    text = re.sub(r"<[^>]+>", " ", text)                                 # other tags
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)                    # images
    text = re.sub(r"\[([^\]]+)\]\((?:https?://)[^)]*\)", r"\1", text)    # links -> text
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)                 # display math
    text = re.sub(r"\s*\[\d+(?:\s*[,–-]\s*\d+)*\]", "", text)            # [12], [3,4], [5-7]
    text = re.sub(r"^#+\s.*$", " ", text, flags=re.M)                    # headings
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)                   # hyphenated line breaks
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str):
    protected = text
    for i, ab in enumerate(_ABBREV):
        protected = protected.replace(ab, ab.replace(".", f"\u0000{i}\u0000"))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"(])", protected)
    out = []
    for p in parts:
        for i, ab in enumerate(_ABBREV):
            p = p.replace(ab.replace(".", f"\u0000{i}\u0000"), ab)
        out.append(p.strip())
    return out


def looks_clean(s: str) -> bool:
    """Reject sentences that still carry extraction noise."""
    if re.search(r"[<>{}\\|]|https?://|\$|\bTable\s*$", s):
        return False
    if not s[0].isupper() or s[-1] not in ".!?":
        return False
    letters = sum(c.isalpha() for c in s)
    if letters / max(len(s), 1) < 0.7:
        return False
    no_abbrev = s
    for ab in _ABBREV:
        no_abbrev = no_abbrev.replace(ab, " ")
    words = re.findall(r"[A-Za-z]+", no_abbrev)
    # Many 1-letter fragments ("ex ands", "su p") signal broken OCR words.
    singles = sum(1 for w in words if len(w) == 1 and w.lower() not in ("a", "i"))
    return singles <= 1


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def existing_bank_sentences() -> set:
    if not SENTENCE_BANK_PATH.exists():
        return set()
    return {_normalize(s) for s in split_sentences(clean_text(SENTENCE_BANK_PATH.read_text(encoding="utf-8")))}


def extract_patterns_from_text(text: str) -> dict:
    """Return {"mechanisms": [...], "rhetoricals": [...], "figure_phrases": [...]}."""
    extracted = {k: [] for k in PATTERNS}
    seen = existing_bank_sentences()
    for sent in split_sentences(clean_text(text)):
        norm = _normalize(sent)
        if norm in seen or not looks_clean(sent):
            continue
        for kind, pats in PATTERNS.items():
            lo, hi = LENGTH_LIMITS[kind]
            if lo < len(sent) < hi and any(re.search(p, sent, re.I) for p in pats):
                extracted[kind].append(sent)
                seen.add(norm)
                break
    return extracted


def fetch_arxiv_text(query: str, max_papers: int = 2) -> list:
    """Fetch the newest arXiv papers matching query (title + abstract only)."""
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}", "sortBy": "submittedDate",
        "sortOrder": "descending", "max_results": max_papers})
    papers = []
    try:
        req = urllib.request.Request(f"{ARXIV_API}?{params}",
                                     headers={"User-Agent": "top-tier-paper-writing-skill/1.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read())
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            get = lambda tag: (entry.findtext(f"atom:{tag}", default="", namespaces=ns) or "").strip()
            title, summary = " ".join(get("title").split()), " ".join(get("summary").split())
            if title and summary:
                papers.append({"title": title, "text": f"{title}. {summary}", "url": get("id")})
    except Exception as e:
        print(f"[!] arXiv fetch failed: {e}", file=sys.stderr)
    return papers


def evolve_skill(source_desc: str, extracted: dict, per_kind: int = 5):
    """Append candidates to the sentence bank and record the event in the log."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    counts = {k: len(v) for k, v in extracted.items()}

    log_entry = (f"\n### [Evolution Event: {now_str}]\n- **Source**: {source_desc}\n"
                 f"- **Extracted Causal Patterns**: {counts['mechanisms']}\n"
                 f"- **Extracted Rhetorical Transitions**: {counts['rhetoricals']}\n"
                 f"- **Extracted Figure Phrasings**: {counts['figure_phrases']}\n\n"
                 "**Sample Discovered Expressions:**\n")
    for label, kind in (("Causal", "mechanisms"), ("Rhetorical", "rhetoricals"), ("Figure", "figure_phrases")):
        for s in extracted[kind][:2]:
            log_entry += f"- *{label}*: \"{s}\"\n"
    log_entry += "\n---\n"

    if not EVOLUTION_LOG_PATH.exists():
        EVOLUTION_LOG_PATH.write_text("# Skill Evolution & Knowledge Growth Log\n\n"
                                      "> This log tracks self-evolution events of top-tier-paper-writing skill.\n\n",
                                      encoding="utf-8")
    with open(EVOLUTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)

    headings = {"mechanisms": "Discovered Causal Attributions",
                "rhetoricals": "Discovered Rhetorical Transitions",
                "figure_phrases": "Discovered Figure Phrasings"}
    with open(SENTENCE_BANK_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n\n### [Autonomous Evolution: {now_str} from {source_desc}]\n")
        for kind, heading in headings.items():
            if extracted[kind]:
                f.write(f"#### {heading}:\n")
                for item in extracted[kind][:per_kind]:
                    f.write(f"- `{item}`\n")
    print(f"[*] Appended to {SENTENCE_BANK_PATH.name} and logged in {EVOLUTION_LOG_PATH.name}.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Skill Self-Evolution Module (preview by default)")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", type=str, help="Paper text / Markdown file to ingest (full text works best)")
    src.add_argument("--arxiv_query", type=str, help="Query arXiv for recent papers (abstracts only)")
    parser.add_argument("--max_papers", type=int, default=3, help="Number of arXiv papers to fetch")
    parser.add_argument("--per_kind", type=int, default=5, help="Max sentences per category to append")
    parser.add_argument("--apply", action="store_true",
                        help="Write candidates to the sentence bank and evolution log (default: preview only)")
    args = parser.parse_args(argv)

    total = {k: [] for k in PATTERNS}
    if args.file:
        if not os.path.exists(args.file):
            parser.error(f"file not found: {args.file}")
        with open(args.file, "r", encoding="utf-8") as f:
            total = extract_patterns_from_text(f.read())
        source_info = f"Local File: {os.path.basename(args.file)}"
    else:
        papers = fetch_arxiv_text(args.arxiv_query, args.max_papers)
        if not papers:
            print("[!] No papers retrieved; nothing to do.")
            return 1
        source_info = f"arXiv abstracts: '{args.arxiv_query}' ({len(papers)} papers)"
        for p in papers:
            for k, v in extract_patterns_from_text(p["text"]).items():
                total[k].extend(s for s in v if s not in total[k])

    print(f"[*] Source: {source_info}")
    for kind, items in total.items():
        print(f"\n== {kind} ({len(items)}) ==")
        for s in items:
            print(f"  - {s}")

    if not any(total.values()):
        print("\n[*] No new candidate sentences found.")
        return 0
    if args.apply:
        evolve_skill(source_info, total, args.per_kind)
    else:
        print("\n[*] Preview only. Review the candidates above, then re-run with --apply to save them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
