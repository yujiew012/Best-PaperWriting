# Domain Template: NLP & Large Language Models

<!-- domain-id: nlp_llm. Standard template; sections 1-7 hold established conventions, section 8 holds provisional rules added by evolve-paper-skill. Rule ids (R-xxxx) refer to evolution_ledger.json. -->

> **Use when** the paper proposes or analyses LLM/NLP methods: reasoning, alignment, retrieval, agents (non-security), evaluation, benchmarks. Security of LLMs and agents uses `llm_agent_security.md`. Read it together with `references/writing/*.md`.

## 1. Venues and reviewer expectations
- ACL, EMNLP, NAACL, COLING and TACL require a **Limitations** section, and most also require an ethics statement. NeurIPS, ICML and ICLR weigh method novelty and breadth.
- Reviewers check: model and benchmark breadth; data contamination; prompt sensitivity; fairness of comparisons (same model, same budget); validity of automatic metrics or LLM judges.

## 2. Paper skeleton

| § | Section | Must contain |
| :--- | :--- | :--- |
| 1 | Introduction | Task and why current models fail (with an example); insight; method; results; contributions. |
| 2 | Related work | By approach; the gap at the end of each subsection. |
| 3 | Method | Problem formulation; method components; prompts or training objectives; inference procedure and cost. |
| 4 | Experimental setup | Models (versions, sizes, open/closed); benchmarks; baselines; metrics; decoding parameters; compute. |
| 5 | Results and analysis | Main results; ablations; analysis (error analysis, case studies, scaling with model size or compute). |
| 6 | Conclusion | Closure and concrete future work. |
| — | Limitations | Required at ACL venues; honest scope of claims. |
| — | Ethics statement | Data, human annotators, potential misuse. |

## 3. Mandatory elements
- Exact model identifiers and versions, decoding settings, and the number of samples; prompts in the appendix.
- Contamination discussion for benchmarks that may appear in pre-training data.
- Compute and cost: GPU hours or API cost; tokens per query for inference-time methods.
- Human evaluation details when used: annotators, guidelines, agreement.

## 4. Evaluation protocol
- At least two model families and two sizes when claiming generality; at least three benchmarks covering the claim.
- Baselines at equal budget (same base model, comparable inference compute) — e.g. compare against self-consistency at an equal number of samples.
- Report variance over seeds or prompt paraphrases; significance tests for close results.
- Validate LLM-as-judge against human judgments.

## 5. Figures and tables
- Diagram style: `references/figure_styles/nlp_llm.json` (pass `--style nlp_llm` to `gen_architecture_diagram.py`).
- Main table: methods × benchmarks for each model; best results in bold; average column.
- Scaling plots (accuracy vs. model size, samples or tokens).
- One qualitative example figure or table showing the method's behaviour (with a failure case in the appendix).

## 6. Narrative patterns
- Motivate with a concrete failure example of current models; return to it in the analysis.
- Separate *what improves* (results) from *why* (analysis: ablation, error categories, attention to cost).

## 7. Common rejection reasons → preventive checks
- Unequal compute vs. baselines → match budgets or plot accuracy vs. compute.
- Single model family → add another family or size.
- Possible contamination → discuss it and add a held-out or recent benchmark.
- Missing Limitations section (ACL) → desk-reject risk; always include it.

## 8. Provisional rules (evolution)

> Rules supported by a single exemplar paper. Treat them as suggestions. They become established (moved into §1–7) once a second paper supports them, and are retired if later papers contradict them.

_(none yet)_
