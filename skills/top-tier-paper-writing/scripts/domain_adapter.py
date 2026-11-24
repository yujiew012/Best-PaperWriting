#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
Domain Adaptive Alignment Module (自适应领域识别与微调对齐模块)
Part of top-tier-paper-writing skill.

What it does:
  1. Scores the input text against the keyword / venue lists in
     references/domain_taxonomies.json (whole-word matching) and picks the
     best-scoring domain. The scores and a confidence level are reported; if no
     keyword matches, nothing is guessed silently -- pass --domain explicitly.
  2. Optionally queries the arXiv API for relevance-ranked papers from the last
     N years that match the matched keywords (arXiv has no citation counts, so
     these are topical exemplars, not "most cited" papers).
  3. Writes a session profile JSON with the domain's mandatory sections,
     metrics, preferred plots and mechanism vocabulary.

Usage:
    python3 domain_adapter.py --text "Backdoor poisoning defense for federated learning"
    python3 domain_adapter.py --file idea.md --output session_domain_profile.json
    python3 domain_adapter.py --file idea.md --domain security_privacy --offline
"""

import os
import re
import sys
import json
import argparse
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TAXONOMY_PATH = SKILL_ROOT / "references" / "domain_taxonomies.json"
ARXIV_API = "https://export.arxiv.org/api/query"


def load_taxonomies():
    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(f"Taxonomy configuration not found at {TAXONOMY_PATH}")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["domains"]


def _term_regex(term: str) -> re.Pattern:
    # Whole-word match, tolerant of plural "s"/"es" and of "-" vs " " in compounds.
    body = r"[\s-]".join(re.escape(part) for part in re.split(r"[\s-]+", term.lower()))
    return re.compile(r"(?<![\w])" + body + r"(?:e?s)?(?![\w])")


def score_domains(text: str, taxonomies: dict) -> dict:
    """Return {domain_id: {"score": int, "matched_keywords": [...], "matched_venues": [...]}}."""
    low = text.lower()
    result = {}
    for domain_id, cfg in taxonomies.items():
        kws = {kw: len(_term_regex(kw).findall(low)) for kw in cfg.get("keywords", [])}
        kws = {k: n for k, n in kws.items() if n}
        venues = [v for v in cfg.get("venues", []) if _term_regex(v).search(low)]
        # Multi-word terms are more specific, so they weigh more.
        score = sum(n * (3 if " " in k or "-" in k else 2) for k, n in kws.items()) + 5 * len(venues)
        result[domain_id] = {"score": score,
                             "matched_keywords": sorted(kws, key=kws.get, reverse=True),
                             "matched_venues": venues}
    return result


def identify_domain(text: str, taxonomies: dict):
    """Return (domain_id or None, confidence, scores)."""
    scores = score_domains(text, taxonomies)
    ranked = sorted(scores, key=lambda d: scores[d]["score"], reverse=True)
    best, top = ranked[0], scores[ranked[0]]["score"]
    second = scores[ranked[1]]["score"] if len(ranked) > 1 else 0
    if top == 0:
        return None, "none", scores
    if top >= 6 and top >= 2 * second:
        confidence = "high"
    elif top > second:
        confidence = "medium"
    else:
        confidence = "low (tie)"
    return best, confidence, scores


def fetch_arxiv_exemplars(keywords: list, max_results: int = 3, years: int = 2):
    """Relevance-ranked arXiv papers from the last `years` years. Returns (list, error)."""
    if not keywords:
        return [], "no matched keywords to query"
    today = datetime.date.today()
    start = today.replace(year=today.year - years)
    terms = " AND ".join(f'all:"{kw}"' for kw in keywords[:2])
    query = f"({terms}) AND submittedDate:[{start:%Y%m%d}0000 TO {today:%Y%m%d}2359]"
    params = urllib.parse.urlencode({"search_query": query, "sortBy": "relevance",
                                     "sortOrder": "descending", "max_results": max_results})
    try:
        req = urllib.request.Request(f"{ARXIV_API}?{params}",
                                     headers={"User-Agent": "top-tier-paper-writing-skill/1.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read())
    except Exception as e:
        return [], f"arXiv request failed: {e}"
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    out = []
    for entry in root.findall("atom:entry", ns):
        get = lambda tag: " ".join((entry.findtext(f"atom:{tag}", default="", namespaces=ns) or "").split())
        if get("title"):
            summary = get("summary")
            out.append({"title": get("title"), "published": get("published")[:10],
                        "summary_snippet": summary[:250] + ("..." if len(summary) > 250 else ""),
                        "url": get("id")})
    return out, None


def create_domain_profile(input_text: str, output_path: str = None, domain: str = None,
                          offline: bool = False, max_results: int = 3, years: int = 2):
    taxonomies = load_taxonomies()
    detected, confidence, scores = identify_domain(input_text, taxonomies)
    if domain:
        if domain not in taxonomies:
            raise SystemExit(f"[error] unknown domain '{domain}'. Choose from: {', '.join(taxonomies)}")
        domain_id, source = domain, "user-specified"
    elif detected:
        domain_id, source = detected, "keyword-matched"
    else:
        raise SystemExit("[error] no domain keyword matched the input. Pass --domain with one of: "
                         + ", ".join(taxonomies))

    info = taxonomies[domain_id]
    matched = scores[domain_id]["matched_keywords"]
    if offline:
        exemplars, err = [], "skipped (--offline)"
    else:
        exemplars, err = fetch_arxiv_exemplars(matched or info["keywords"][:2], max_results, years)

    profile = {
        "identified_domain": domain_id,
        "domain_name": info["name"],
        "selection": {"source": source, "confidence": confidence if source == "keyword-matched" else "n/a",
                      "detected_domain": detected,
                      "scores": {d: s["score"] for d, s in scores.items()},
                      "matched_keywords": matched,
                      "matched_venues": scores[domain_id]["matched_venues"]},
        "target_venues": info["venues"],
        "retrieved_exemplars": exemplars,
        "retrieval_note": err or f"arXiv relevance ranking, last {years} years (no citation data)",
        "tailored_guidelines": {
            "mandatory_sections": info["structural_requirements"]["mandatory_sections"],
            "core_metrics": info["structural_requirements"]["eval_metrics"],
            "recommended_plots": info["preferred_plots"],
            "causal_mechanism_focus": info["causal_mechanism_focus"],
        },
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
    print(f"[*] Domain: {info['name']} ({source}, confidence: {profile['selection']['confidence']})",
          file=sys.stderr)
    if detected and domain and detected != domain:
        print(f"[!] Note: keywords pointed to '{detected}', overridden by --domain.", file=sys.stderr)
    if confidence.startswith("low") and not domain:
        print("[!] Low confidence: consider passing --domain explicitly.", file=sys.stderr)
    if err:
        print(f"[*] Exemplars: {err}", file=sys.stderr)
    if output_path:
        print(f"[*] Profile saved to: {output_path}", file=sys.stderr)
    return profile


def main(argv=None):
    parser = argparse.ArgumentParser(description="Adaptive Domain & Style Alignment Module")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", type=str, help="Paper idea, abstract, or keywords")
    src.add_argument("--file", type=str, help="Markdown / text file with the idea or abstract")
    parser.add_argument("--domain", type=str, help="Force a domain id (skips detection)")
    parser.add_argument("--output", type=str, default="session_domain_profile.json",
                        help="Output JSON profile path")
    parser.add_argument("--offline", action="store_true", help="Do not query arXiv")
    parser.add_argument("--max_results", type=int, default=3, help="Number of arXiv exemplars")
    parser.add_argument("--years", type=int, default=2, help="Exemplar recency window in years")
    args = parser.parse_args(argv)

    if args.file:
        if not os.path.exists(args.file):
            parser.error(f"file not found: {args.file}")
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = args.text

    profile = create_domain_profile(content, args.output, args.domain, args.offline,
                                    args.max_results, args.years)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
