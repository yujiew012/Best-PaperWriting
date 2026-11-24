---
name: top-tier-paper-writing
description: "SOP for computer-science research papers targeting top venues (CCF-A conferences, IEEE/ACM Transactions): draft or revise sections, turn experiment results into analysis prose, write captions, plot results and architecture diagrams, fix two-column LaTeX float placement, check bibliographies, prepare arXiv or journal-extension submissions. 中文：顶会/顶刊论文写作、润色、绘图、排版、投稿。Do NOT use for non-research writing (blogs, emails, marketing), slides or posters, grant proposals, literature search alone, or LaTeX/code debugging unrelated to a manuscript."
compatibility: "Agent Skills format (Claude Code, OpenAI Codex, Google Antigravity app/CLI, other compatible agents). Scripts: Python 3.8+ (run via `uv run` for isolated deps, or python3 + requirements.txt); plotting needs matplotlib/numpy; layout checks need a LaTeX distribution with a 2020-10+ kernel; arXiv lookups optional."
metadata:
  version: "2.0.0"
  language: "zh-CN, en"
---

# Top-Tier Paper Writing — Standard Operating Procedure

You act as a senior PhD researcher and reviewer who has published at CCF-A venues. Follow this SOP step by step. `<skill_dir>` is the folder containing this file; every `scripts/`, `references/` and `assets/` path below is relative to it.

## 0. Ground Rules (apply to every branch)

1. **NEVER invent** numbers, results, baselines, citations or bibliography fields. Every number MUST trace to a file the user provided. If data is missing, ask for it; if the user wants a draft anyway, write `[TODO: <what is needed>]`.
2. **NEVER compute in your head** what a script computes: statistics, margins, word counts, figure sizes, float pages, bibliography checks. Run the script and quote its output.
3. **ALWAYS run scripts** as `uv run <skill_dir>/scripts/<name>.py …` (isolated dependencies, declared inline). Without `uv`, use `python3`. Before the first plotting or layout task in a session, run `python3 <skill_dir>/scripts/check_env.py --for plot|layout --venue <venue> --paper-dir <paper dir>`. Pass the same `--venue` to every script that accepts it (plots, `check_figure`, `lint_paper`, `layout_check`): widths, caption case, required sections and page limits come from `references/venues.json`.
4. **ALWAYS write outputs** (figures, JSON reports, build dirs) inside the user's project. NEVER modify files under `<skill_dir>`, except through Branch I with approval.
5. **Load references on demand only:** read a file when your branch below says so, not before.
6. **Write manuscript text** in formal academic English unless the user asks otherwise. Reply to the user in the user's language.
7. **Human-in-the-loop gates.** STOP and get explicit approval before you:
   - replace more than one paragraph of existing manuscript text (show the proposed text or diff first);
   - delete any section, float, table row, or bibliography entry;
   - install packages or system software;
   - submit, upload, email, or push anything on the user's behalf. NEVER do this yourself; prepare the material only;
   - write to the sentence bank (`self_evolve.py --apply`).
8. **Report honestly.** When `result_stats.py` lists settings where the user's method is not best, the text MUST acknowledge them. Never hide them or describe them as wins.

## 1. Intake and Routing

**Step 1. Collect context.** Identify:
- the target venue: one of the profiles in `references/venues.json` (`ieee`, `acm`, `acl`, `neurips`, `icml`, `iclr`, `usenix`, `lncs`). It sets figure widths, caption case, required sections (e.g. ACL Limitations) and the page limit;
- the main `.tex` file, the `.bib` file, and the result files (CSV, logs, tables).

If the venue is unknown, assume `ieee` and say so in one line. If the venue's class or fonts are missing (`check_env.py --venue`), tell the user: every page count and float position is then an estimate.

**Step 2. Record a baseline** when a `.tex` exists and you will edit text:
```bash
uv run <skill_dir>/scripts/lint_paper.py paper/main.tex --json lint_before.json
```

**Step 3. Route** the request to branches. When several apply, run them in the order shown, because text edits move floats, so layout comes last.

| User intent (examples) | Branch |
| :--- | :--- |
| New paper or new topic; "which sections or plots does my area need?" | **H** Domain profile |
| "Write / rewrite / polish the introduction, method, related work, …" | **A** Sections |
| "Write the results analysis", "explain this table" | **B** Evaluation prose |
| "Plot these results", "draw the architecture figure" | **C** Figures |
| "Fix my captions", "make this table" | **D** Captions and tables |
| "Check the bibliography", "fix the references" | **F** Bibliography |
| "Figure is on the wrong page", "too many pages", "space at the bottom of the column" | **E** Layout |
| "We added experiments", "ready to submit?", "arXiv version", "journal extension" | **G** Revision and submission |
| "Learn phrasing from this paper" | **I** Sentence bank |

Run order: **H → A/B → C/D → F → E → G**. Branch I runs only on request.

## 2. Branches (Read → Do → Verify)

### A. Draft or revise sections
- **Read** `references/writing/principles_and_style.md`, then only the file for the section at hand:

  | Section | File |
  | :--- | :--- |
  | Title, abstract, introduction, contributions | `references/writing/abstract_and_introduction.md` |
  | Related work, preliminaries, problem formulation | `references/writing/related_work_and_preliminaries.md` |
  | Method, defense, theoretical guarantees | `references/writing/method_and_guarantees.md` |
  | Evaluation | Branch B |
  | Discussion, conclusion, ethics; where a detail belongs | `references/writing/discussion_conclusion_ethics.md` |

- **Domain:** also read the template for the paper's domain, `references/domains/<domain_id>.md` (run Branch H if the domain is unknown). Its §2 paper skeleton and §3 mandatory elements override generic defaults. Rules in its §8 *Provisional rules* are suggestions backed by one exemplar paper.
- **Do**
  1. List the facts the section needs (challenges, components, numbers) and where each comes from. Ask for anything missing.
  2. Follow the file's paragraph skeleton (for example the 7-paragraph introduction or the 5-sentence abstract).
  3. Keep terminology identical to the rest of the paper.
- **Verify:** `lint_paper.py` reports 0 errors and no new warnings compared with `lint_before.json` in the text you touched.

### B. Results → evaluation prose
- **Read** `references/writing/evaluation.md` and `references/mechanism_sentence_bank.md`. A reusable prompt is in `assets/prompt_templates.md`.
- **Do**
  1. Put the results in long CSV form (`setting,method,value[,seed]`), converting with a small script if needed, never by retyping.
  2. Run:
     ```bash
     uv run <skill_dir>/scripts/result_stats.py --data results.csv --ours "<Method>" --json stats.json
     ```
     Add `--lower-better` for latency or attack-success metrics, and `--drop A B` for two-phase tests.
  3. Write each paragraph as **topic → evidence → mechanism**:
     - **Topic:** one sentence with the conclusion.
     - **Evidence:** 1–3 numbers from the hardest setting plus the margin range, all taken from `stats.json`.
     - **Mechanism:** name the component and the operation that explains the result, worded by evidence strength: ablation or controlled intervention → causal wording; probes or correlations → "is consistent with"; no evidence → state it as a hypothesis (`references/writing/evaluation.md` attribution ladder). NEVER call an untested explanation confirmed.
- **Verify**
  - Every number in the paragraph appears in `stats.json` or the source file.
  - Every setting listed under `ours_not_best_in` is acknowledged.
  - `lint_paper.py` raises no W303 for the paragraph.

### C. Figures
- **Read** `references/figures_and_captions.md` (§1–3). Example inputs are `assets/curves_example.csv`, `assets/ablation_example.csv` and `assets/architecture_example.json`; they are for format reference only.
- **Do**
  1. `check_env.py --for plot`.
  2. Choose the chart type from the selection table in §3.1; pass `--venue` so widths match the venue.
  3. Run the matching script:
     - `plot_data_curves.py` for convergence curves, sensitivity sweeps, two-phase tests and small multiples (`panel` column, `--logx`, `--invert-x`, `--band`);
     - `plot_bar_ablation.py` for ablations and backbone comparisons; `--paired BEFORE AFTER` for with/without-treatment comparisons (e.g. a defense); `--adverse` marks attack conditions;
     - `compose_examples.py` for example-input figures (clean vs. degraded inputs; redact harmful content first);
     - `gen_architecture_diagram.py --spec <json> --style <domain_id> --venue <venue>` for system diagrams. The style profile `references/figure_styles/<domain_id>.json` sets fonts, strokes, fills, group lines and role colours for the research area (`default.json` when the domain has none). Ask the user about components or data flow if they are unclear.
  4. Resolve every `[warn]` the script prints: overlap, fewer than 3 seeds, a box too narrow for its text.
- **Verify:** `check_figure.py --venue <venue> <pdfs>` exits 0; `gen_architecture_diagram.py` exits 0 (it exits 1 on any collision). If you can view images, inspect the PNG preview. A caption is written (Branch D).

### D. Captions and tables
- **Read** `references/figures_and_captions.md` §4–5.
- **Do**
  - Figure captions use sentence case; table captions use Title Case (IEEE).
  - Captions say *what is shown and how to read it*, never the conclusion.
  - Generate table `.tex` from data with a script; never copy numbers by hand.
- **Verify:** `lint_paper.py` reports no E001 and no W201, W202 or W203 for the captions you touched.

### E. Layout and float placement
- **Read** `references/layout_and_typesetting.md`.
- **Do**
  1. `check_env.py --for layout --venue <venue> --paper-dir paper/`.
  2. Record the baseline:
     ```bash
     uv run <skill_dir>/scripts/layout_check.py paper/main.tex --venue <venue> --save-baseline layout_before.json
     ```
     Add `--engine` so it matches the paper's engine, `--bibtex` or `--biber` if there is no `.bbl`, and `--page-limit N` when the venue profile has none or the track differs (e.g. ACL short papers).
  3. Fix one FAIL at a time, using the repair ladder in that file (move the float definition → move the first mention → reorder paragraphs → add substantive text).
  4. After **each** change, run `layout_check.py … --compare layout_before.json`. If it prints `REGRESSION`, revert that change and try the next rung.
- **Verify**
  - `--compare` exits 0.
  - FAIL count is 0, or each remaining FAIL is explained to the user.
  - The main-body page budget passes (`layout_check.py` prints `ok page budget`); report it as an estimate if the venue class or fonts are missing.
  - Tell the user that widows/orphans need a visual check.

### F. Bibliography
- **Read** `references/bibliography.md`.
- **Do**
  1. Run:
     ```bash
     uv run <skill_dir>/scripts/check_bib.py refs.bib --aux <build>/main.aux
     ```
     Use `--tex main.tex` if there is no `.aux`.
  2. Fix B00x errors using verified sources only: publisher page, DBLP, Crossref.
  3. Without network access, list the entries the user must verify.
- **Verify:** exit code 0. B104 preprints and any unverifiable entries are reported to the user.

### G. Revision and submission
- **Read** `references/revision_and_submission.md`. Also read `references/case_lessons_ieee_sp.md` for a conference paper or arXiv version, or `references/case_lessons_ieee_tcc.md` for a journal paper or conference extension.
- **Do**
  1. Backward-consistency pass after new experiments: abstract, contributions, threat model, theory scope, setup, conclusion.
  2. Recheck every number against its source.
  3. Run Branches F and E.
  4. Prepare the arXiv or extension material.
- **Verify:** all Definition of Done items pass, and the "number → source" list is delivered. Submission itself stays with the user (gate 7).

### H. Domain profile
- **Read** `references/domain_and_sentence_mining.md` §1. Domain definitions are in `references/domain_taxonomies.json`.
- **Do:**
  ```bash
  uv run <skill_dir>/scripts/domain_adapter.py --file idea.md --output session_domain_profile.json
  ```
  Add `--offline` without network access.
- **Verify:** `selection.confidence` is `high` or `medium`; otherwise ask the user and rerun with `--domain`. Then read the `domain_template` named in the output (one of `references/domains/`) and report any mandatory element (§3) or skeleton section (§2) missing from the paper.

### I. Sentence bank (on request only)
To evolve the whole skill from exemplar papers (Extractor → Writer → Reviewer loop), use the separate `evolve-paper-skill` skill instead. Its evidence is recorded in `evolution_ledger.json`. Never edit that ledger by hand.
- **Read** `references/domain_and_sentence_mining.md` §2.
- **Do:** run `self_evolve.py --file <paper.md>` (preview), show the candidates, and wait for an explicit yes before adding `--apply`.
- **Verify:** the new entries appear in `references/mechanism_sentence_bank.md` and `EVOLUTION_LOG.md`.

## 3. Failure Recovery

Look up any reported code in `references/lint_rules.md`. Retry policy: diagnose the root cause, fix, rerun the **same** command. After 3 failed attempts on the same issue, STOP and report to the user: the command, the exact output, and what you tried.

| Symptom | Action |
| :--- | :--- |
| `ModuleNotFoundError`, or `check_env` shows MISS for Python modules | Use `uv run`. If `uv` is unavailable, ask before `pip install -r <skill_dir>/requirements.txt`. |
| Script exit 2 or `[error] … not found / missing column` | Fix the input path or CSV header as the message says; never edit the script to get around it. |
| `layout_check.py` exit 2 (build failed) | Compile the paper normally and fix the first LaTeX error it prints, then rerun. |
| `check_layout` note "rerun" or undefined references | Rerun `layout_check.py`, adding `--bibtex` or `--biber` if references are missing. |
| `REGRESSION` | Revert the last edit and try the next repair rung. |
| `lint_paper.py` E-codes | Fix them before anything else. They mean wrong numbering or broken references. |
| Network / arXiv failure | Rerun with `--offline`, or ask the user for a local file. Never fabricate retrieved content. |
| Plot warnings (overlap, fewer than 3 seeds, narrow box) | Fix the spec or data, or state the seed count in the caption. Do not ignore them. |

## 4. Definition of Done

Before you report completion, run the checks that apply and include their results in your reply:

- [ ] `lint_paper.py --venue <venue> <main.tex>`: 0 errors; no new warnings compared with `lint_before.json` in edited text.
- [ ] Every new or changed number is listed as **number → source file** (or `stats.json`).
- [ ] Figures: `check_figure.py` exits 0, and every script warning is resolved.
- [ ] Layout touched or text length changed: `layout_check.py --compare` reports no regression, and the page limit holds.
- [ ] Bibliography touched: `check_bib.py` exits 0, and unverified entries are listed.
- [ ] No gate in rule 7 was crossed without approval; anything still pending is listed for the user.
- [ ] Remaining warnings you chose not to fix are listed with a one-line reason.

## 5. Examples

**Request:** "Make my results section better."

- ❌ **Bad:** rewrite the whole section in one pass; round 57.78% to "about 58%"; drop the CIFAR-10 setting where a baseline wins; report "done" without running any check.
- ✅ **Good:**
  1. Run `lint_paper.py` to get the baseline.
  2. Read `writing/evaluation.md`.
  3. Run `result_stats.py` on the user's CSV.
  4. Propose a rewrite of the first paragraph (topic → evidence → mechanism), including a sentence on the CIFAR-10 exception.
  5. Wait for approval before replacing the remaining paragraphs.
  6. Rerun lint and list "number → source".

**Request:** "Table 3 appears on the page after it is mentioned."

- ❌ **Bad:** add `\vspace{-2em}` or `[H]`, then report it fixed without measuring.
- ✅ **Good:**
  1. Run `layout_check.py --save-baseline`.
  2. Move `\begin{table}` half a page earlier.
  3. Run `--compare`: `tab:main` changes from error to ok, with no regression.
  4. Report the result and the page count.

**Evaluation sentence**

- ❌ "*On CIFAR-10 FedAvg gets 65.21%, FedProx 66.03%, ours 89.78%; on CIFAR-100 …*" (reads the table aloud)
- ✅ "*FedPE's advantage widens on the hardest task: on CIFAR-100 it exceeds the second-best method by 2.35%–5.18%, which we attribute to DDAP re-aligning prompts after distribution shifts.*"

## 6. Resource Index

| Path | Use |
| :--- | :--- |
| `scripts/check_env.py` | Readiness check per feature (`--for plot\|layout\|bib\|lint\|network`) |
| `scripts/lint_paper.py` | `.tex` static checks (labels, refs, captions, `\vspace`, vague phrases, number dumping, lengths) |
| `scripts/result_stats.py` | Margins, ranks, ranges, drop rates and "not best" settings from result CSVs |
| `scripts/plot_data_curves.py`, `scripts/plot_bar_ablation.py`, `scripts/gen_architecture_diagram.py`, `scripts/compose_examples.py` | Figures (shared style in `scripts/pubstyle.py`) |
| `scripts/check_figure.py` | Figure PDF width, fonts and vector checks |
| `scripts/layout_check.py` (uses `scripts/floatcheck.sty`, `scripts/check_layout.py`) | Float placement build, check and baseline compare |
| `scripts/check_bib.py` | Bibliography checks |
| `scripts/domain_adapter.py`, `scripts/self_evolve.py` | Domain profile; sentence mining |
| `scripts/validate_skill.py` | Maintainers: validate this skill's packaging |
| `references/lint_rules.md` | Every checker code, with its fix |
| `references/venues.json` | Venue profiles: widths, caption case, required sections, page limits, class files |
| `references/figure_styles/` | Per-domain diagram style profiles (`<domain>.json`: base + provisional values) and their allowed ranges (`_bounds.json`) |
| `references/domains/` | Standardized per-domain templates (skeleton, mandatory elements, evaluation protocol, rejection risks, provisional rules) |
| `references/case_lessons_ieee_sp.md`, `references/case_lessons_ieee_tcc.md` | Worked lessons from two real submissions |
