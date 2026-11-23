#!/usr/bin/env python3
"""
Skill Self-Evolution & Continuous Literature Ingestion Module (自进化与知识沉淀模块)
Part of top-tier-paper-writing skill.
Inspired by Orchestra-Research/AI-Research-SKILLs outer-loop reflection & continuous learning.

Usage:
    python3 self_evolve.py --file /path/to/paper_text.md
    python3 self_evolve.py --arxiv_query "federated continual learning" --max_papers 2
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
SENTENCE_BANK_PATH = SKILL_ROOT / "references" / "mechanism_sentence_bank.md"
EVOLUTION_LOG_PATH = SKILL_ROOT / "EVOLUTION_LOG.md"

# Causal mechanism indicator patterns commonly seen in CCF-A papers
MECHANISM_PATTERNS = [
    r'([A-Z][^.!?]*(?:stems? from|owing to|attributable to|is accredited to|can be traced to)[^.!?]*\.)',
    r'([A-Z][^.!?]*(?:decouples? [^.!?]* from|disentangles? [^.!?]* from)[^.!?]*\.)',
    r'([A-Z][^.!?]*(?:penalizes? [^.!?]*(?:thereby|thus) preventing|suppresses? [^.!?]*(?:without|while))[^.!?]*\.)',
    r'([A-Z][^.!?]*(?:mitigates? [^.!?]* by dynamically [^.!?]*)[^.!?]*\.)',
    r'([A-Z][^.!?]*(?:manifests? as [^.!?]* leading to a negligible [^.!?]*)[^.!?]*\.)'
]

# Rhetorical transition & critical review patterns
RHETORICAL_PATTERNS = [
    r'([A-Z][^.!?]*(?:Despite (?:its|their|these) [^.!?]*, existing [^.!?]*(?:inherently suffer from|fall short of|fail to))[^.!?]*\.)',
    r'([A-Z][^.!?]*(?:While prior studies have demonstrated [^.!?]*, they overlook [^.!?]*)\.)',
    r'([A-Z][^.!?]*(?:Crucially, the fundamental limitation lies in [^.!?]*)\.)'
]

# Figure & plot description patterns
FIGURE_PATTERNS = [
    r'([A-Z][^.!?]*(?:As depicted in (?:Fig\.|Figure) [^.!?]*, our method [^.!?]*)\.)',
    r'([A-Z][^.!?]*(?:The shaded area denotes [^.!?]* standard deviation across [^.!?]* seeds)\.)'
]

def extract_patterns_from_text(text: str) -> dict:
    """Scan text for top-tier rhetorical, causal, and figure patterns."""
    extracted = {
        "mechanisms": [],
        "rhetoricals": [],
        "figure_phrases": []
    }
    
    # Clean text
    clean_text = re.sub(r'\s+', ' ', text)
    
    for pat in MECHANISM_PATTERNS:
        matches = re.findall(pat, clean_text, re.IGNORECASE)
        for m in matches:
            m_strip = m.strip()
            if 30 < len(m_strip) < 300 and m_strip not in extracted["mechanisms"]:
                extracted["mechanisms"].append(m_strip)

    for pat in RHETORICAL_PATTERNS:
        matches = re.findall(pat, clean_text, re.IGNORECASE)
        for m in matches:
            m_strip = m.strip()
            if 30 < len(m_strip) < 300 and m_strip not in extracted["rhetoricals"]:
                extracted["rhetoricals"].append(m_strip)

    for pat in FIGURE_PATTERNS:
        matches = re.findall(pat, clean_text, re.IGNORECASE)
        for m in matches:
            m_strip = m.strip()
            if 25 < len(m_strip) < 250 and m_strip not in extracted["figure_phrases"]:
                extracted["figure_phrases"].append(m_strip)

    return extracted

def fetch_arxiv_text(query: str, max_papers: int = 2) -> list:
    """Fetch recent papers matching query from arXiv and return abstracts & titles."""
    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_papers}"
    papers = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SkillEvolutionBot/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read())
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
                link = entry.find("atom:id", ns).text.strip()
                papers.append({"title": title, "text": f"{title}. {summary}", "url": link})
    except Exception as e:
        print(f"[!] Warning: arXiv fetch failed ({e})")
    return papers

def evolve_skill(source_desc: str, extracted: dict):
    """Integrate new findings into mechanism_sentence_bank.md and record into EVOLUTION_LOG.md."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Update EVOLUTION_LOG.md
    log_entry = f"""
### [Evolution Event: {now_str}]
- **Source**: {source_desc}
- **Extracted Causal Patterns**: {len(extracted['mechanisms'])}
- **Extracted Rhetorical Transitions**: {len(extracted['rhetoricals'])}
- **Extracted Figure Phrasings**: {len(extracted['figure_phrases'])}

**Sample Discovered Expressions:**
"""
    for m in extracted["mechanisms"][:2]:
        log_entry += f"- *Causal*: \"{m}\"\n"
    for r in extracted["rhetoricals"][:2]:
        log_entry += f"- *Rhetorical*: \"{r}\"\n"
    log_entry += "\n---\n"

    if not EVOLUTION_LOG_PATH.exists():
        with open(EVOLUTION_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("# Skill Evolution & Knowledge Growth Log\n\n> This log tracks self-evolution events of top-tier-paper-writing skill.\n\n")
            f.write(log_entry)
    else:
        with open(EVOLUTION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)

    # 2. Append new high-value sentences to mechanism_sentence_bank.md if applicable
    if extracted["mechanisms"] or extracted["rhetoricals"]:
        with open(SENTENCE_BANK_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n\n### [Autonomous Evolution: {now_str} from {source_desc}]\n")
            if extracted["mechanisms"]:
                f.write("#### Discovered Causal Attributions:\n")
                for item in extracted["mechanisms"][:3]:
                    f.write(f"- `{item}`\n")
            if extracted["rhetoricals"]:
                f.write("#### Discovered Rhetorical Transitions:\n")
                for item in extracted["rhetoricals"][:3]:
                    f.write(f"- `{item}`\n")

    print(f"[*] Self-evolution completed! Logged to {EVOLUTION_LOG_PATH.name} and synced with sentence bank.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill Self-Evolution Module")
    parser.add_argument("--file", type=str, help="Path to paper text/markdown file to ingest")
    parser.add_argument("--arxiv_query", type=str, help="Query arXiv for recent papers to ingest")
    parser.add_argument("--max_papers", type=int, default=2, help="Number of papers to fetch from arXiv")
    args = parser.parse_args()

    total_extracted = {"mechanisms": [], "rhetoricals": [], "figure_phrases": []}
    source_info = ""

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        source_info = f"Local File: {os.path.basename(args.file)}"
        total_extracted = extract_patterns_from_text(content)
    elif args.arxiv_query:
        papers = fetch_arxiv_text(args.arxiv_query, args.max_papers)
        source_info = f"arXiv Query: '{args.arxiv_query}' ({len(papers)} papers)"
        for p in papers:
            res = extract_patterns_from_text(p["text"])
            for k in total_extracted:
                total_extracted[k].extend(res[k])
    else:
        # Default ingestion test on FedPE markdown if available
        sample_path = "/Users/wyj/Desktop/paper/1-s2.0-S1389128625007674-main.pdf-4ad76249-5cab-4aae-8862-a71cbdc4915a/MinerU_markdown_202611230132987_61ec902c.md"
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                content = f.read()
            source_info = "MinerU Exemplar: FedPE (Computer Networks 2025)"
            total_extracted = extract_patterns_from_text(content)
        else:
            source_info = "Self-Evolution Baseline"
            total_extracted["mechanisms"] = ["The performance gain stems from dynamic prompt scaling, which penalizes divergence without compromising convergence rate."]

    print(f"[*] Analyzing source: {source_info}")
    print(f"[*] Discovered: {len(total_extracted['mechanisms'])} mechanisms, {len(total_extracted['rhetoricals'])} rhetoricals, {len(total_extracted['figure_phrases'])} figure patterns.")
    
    evolve_skill(source_info, total_extracted)
