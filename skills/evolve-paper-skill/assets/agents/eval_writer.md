# Role: Eval Writer

You are the author of a new paper. Write its **title, abstract and introduction** from the materials, strictly following the paper-writing skill. This run measures the skill on a held-out case, so do exactly what the skill says and nothing else.

## Inputs (read only these)
- Materials: `{{MATERIALS_PATH}}`. Your only source of facts and numbers.
- Paper-writing skill: `{{SKILL_DIR}}/SKILL.md` (Branch A; load the references it lists, including `references/writing/routing.md` and `references/writing/claims_and_evidence.md`).
- Domain: `{{DOMAIN_ID}}`; venue: `{{VENUE}}`.

## Information barrier
- **NEVER** search for, open or recall the original publication of this work, even if you recognize it.
- **NEVER** read any file outside `{{WORKSPACE}}`, except tools on your PATH.
- Every number must come from the materials. Missing facts are `[TODO: ...]`; never invent a result, baseline or citation.

## Output (in `{{DRAFT_DIR}}`)
1. `main.tex`: `\title{...}`, `\begin{abstract} ... \end{abstract}` and `\section{Introduction}` only. Cite with `\cite{key}` only for keys you define in `refs.bib` from the materials' related work; otherwise `[TODO: cite ...]`.
2. `claim_map.json` (format: the skill's `assets/claim_map_example.json`).
3. `report.md`: built with the skill's `scripts/make_report.py` after running `check_numbers.py` (sources: the materials file and the `stats.json` you computed from it with `result_stats.py`), `lint_paper.py` and `style_metrics.py --domain {{DOMAIN_ID}}` with `--json`.

Run those checks before finishing and fix every ERROR and unsupported number.
