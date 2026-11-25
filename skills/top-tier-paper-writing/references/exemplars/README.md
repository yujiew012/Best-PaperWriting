# Exemplar bank

Short, attributed passages from published papers, tagged with the rhetorical function they perform. They teach **order of information, rhythm and calibration**, never wording.

| File | Content |
| :--- | :--- |
| `functions.json` | the functions per section (`intro.gap`, `intro.contrast`, `evaluation.claim-first`, ...) |
| `moves.jsonl` | sentence-level exemplars (1-2 sentences, at most 60 words) |
| `paragraphs.jsonl` | paragraph-level exemplars (at most 160 words) |

Record: `{"id", "section", "function", "text", "why", "paper", "venue", "year", "domain", "paper_type", "motivation"}`.

## Use
```bash
uv run <skill_dir>/scripts/find_exemplars.py --list                       # functions with counts
uv run <skill_dir>/scripts/find_exemplars.py intro.gap --domain security_privacy -n 3
uv run <skill_dir>/scripts/find_exemplars.py intro.contrast --paragraphs --type L1
```
Read 2-3 exemplars with the same function (and, when possible, the same route or domain) before writing a paragraph. **NEVER** reuse a sentence or a run of 6 or more words: `lint_paper.py` reports such reuse as W310.

## How the bank grows
Only through `evolve-paper-skill` (`evolve.py add-exemplars`): the extractor proposes passages from an exemplar paper; the script verifies each one verbatim against the paper's text, enforces the length limits and at most 6 sentence and 3 paragraph exemplars per paper, and records the source. Never edit these files by hand. Quoted passages remain the copyright of their authors; they are kept short, attributed and used for commentary on structure. Remove a paper's exemplars on request with `evolve.py add-exemplars --remove <paper_id>`.

The bank starts empty and fills as papers are evolved.
