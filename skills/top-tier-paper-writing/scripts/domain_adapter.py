#!/usr/bin/env python3
"""
Domain Adaptive Alignment Module (自适应领域识别与微调对齐模块)
Part of top-tier-paper-writing skill.
Inspired by Orchestra-Research/AI-Research-SKILLs domain taxonomy & routing.

Usage:
    python3 domain_adapter.py --text "Federated learning with dynamic prompt adaptation on non-iid data"
    python3 domain_adapter.py --file idea.md --output session_domain_profile.json
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TAXONOMY_PATH = SKILL_ROOT / "references" / "domain_taxonomies.json"

def load_taxonomies():
    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(f"Taxonomy configuration not found at {TAXONOMY_PATH}")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["domains"]

def identify_domain(text: str, taxonomies: dict) -> tuple:
    """Identify the top domain based on keyword relevance scoring."""
    text_lower = text.lower()
    scores = {}
    for domain_id, config in taxonomies.items():
        score = 0
        for kw in config.get("keywords", []):
            if kw.lower() in text_lower:
                score += text_lower.count(kw.lower()) * 2
        # Venue mentions also add score
        for venue in config.get("venues", []):
            if venue.lower() in text_lower:
                score += 5
        scores[domain_id] = score

    # Default fallback to machine_learning_fl if no keywords hit
    best_domain = max(scores, key=scores.get) if any(scores.values()) else "machine_learning_fl"
    return best_domain, taxonomies[best_domain]

def fetch_arxiv_exemplars(domain_name: str, keywords: list, max_results: int = 3):
    """Retrieve exemplar top-tier papers from arXiv."""
    query_terms = "+AND+".join([urllib.parse.quote(f'all:"{kw}"') for kw in keywords[:2]])
    url = f"http://export.arxiv.org/api/query?search_query={query_terms}&sortBy=relevance&sortOrder=descending&max_results={max_results}"
    
    exemplars = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TopTierPaperAgent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()
            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                link = entry.find("atom:id", ns).text.strip()
                exemplars.append({
                    "title": title,
                    "summary_snippet": summary[:250] + "...",
                    "url": link
                })
    except Exception as e:
        exemplars.append({
            "title": f"Exemplar benchmark for {domain_name}",
            "summary_snippet": f"Retrieved offline baseline due to network timeout ({e}).",
            "url": "https://arxiv.org"
        })
    return exemplars

def create_domain_profile(input_text: str, output_path: str = None):
    taxonomies = load_taxonomies()
    domain_id, domain_info = identify_domain(input_text, taxonomies)
    
    # Extract top keywords from user input that match domain
    relevant_kws = [kw for kw in domain_info["keywords"] if kw in input_text.lower()]
    if not relevant_kws:
        relevant_kws = domain_info["keywords"][:2]

    exemplars = fetch_arxiv_exemplars(domain_info["name"], relevant_kws, max_results=3)

    profile = {
        "identified_domain": domain_id,
        "domain_name": domain_info["name"],
        "target_venues": domain_info["venues"],
        "retrieved_exemplars": exemplars,
        "tailored_guidelines": {
            "mandatory_sections": domain_info["structural_requirements"]["mandatory_sections"],
            "core_metrics": domain_info["structural_requirements"]["eval_metrics"],
            "recommended_plots": domain_info["preferred_plots"],
            "causal_mechanism_focus": domain_info["causal_mechanism_focus"]
        }
    }

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"[*] Successfully adapted to domain: {domain_info['name']}")
        print(f"[*] Profile saved to: {output_path}")

    return profile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Adaptive Domain & Style Alignment Module")
    parser.add_argument("--text", type=str, help="Input paper idea, abstract, or keywords")
    parser.add_argument("--file", type=str, help="Path to input markdown or text file")
    parser.add_argument("--output", type=str, default="session_domain_profile.json", help="Path to output json profile")
    args = parser.parse_args()

    content = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        content = "Federated learning dynamic prompt adaptation with prior knowledge memory against catastrophic forgetting non-iid."

    res = create_domain_profile(content, args.output)
    print(json.dumps(res, indent=2, ensure_ascii=False))
