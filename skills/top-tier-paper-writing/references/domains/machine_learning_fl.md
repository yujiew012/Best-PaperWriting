# Domain Template: Machine Learning & Federated Learning Algorithms

<!-- domain-id: machine_learning_fl. Standard template; sections 1-7 hold established conventions, section 8 holds provisional rules added by evolve-paper-skill. Rule ids (R-xxxx) refer to evolution_ledger.json. -->

> **Use when** the paper proposes learning algorithms, especially federated, distributed or continual learning (heterogeneous clients, personalization, communication efficiency, robustness). Read it together with `references/writing/*.md`; this file adds only domain conventions.

## 1. Venues and reviewer expectations
- ML venues (NeurIPS, ICML, ICLR) weigh novelty of the mechanism, theory, and breadth of experiments. Journals (TPAMI, TNNLS, TCC, Computer Networks) expect complete setups, more ablations, and complexity or communication analysis.
- Reviewers check that heterogeneity is realistic, that baselines are current and tuned fairly, and that improvements exceed seed variance.

## 2. Paper skeleton

| § | Section | Must contain |
| :--- | :--- | :--- |
| 1 | Introduction | Setting and why heterogeneity or drift hurts; limitation of the state of the art with evidence; 2 challenges ↔ 2 components; contributions. |
| 2 | Related work | FL under heterogeneity / personalization / the specific sub-problem; each subsection ends with the shared gap. |
| 3 | Preliminaries | Clients, local objectives, global objective, partition model; notation table if heavy. No method names yet. |
| 4 | Method | Overview figure + algorithm box; one subsection per component (intuition → formulation → optimization); complexity and communication cost. |
| 5 | Theory (if any) | Assumptions stated explicitly; convergence or generalization result; proof sketch with the full proof in the appendix. |
| 6 | Experiments | RQs; setup (datasets, partitions, clients, rounds, baselines, metrics, implementation); main results; ablation; sensitivity; robustness / scalability. |
| 7 | Conclusion | Two paragraphs: closure, then concrete future directions. |

## 3. Mandatory elements
- Partition protocol stated precisely: Dirichlet concentration α and/or pathological shards per client; number of clients; participation rate; local epochs; rounds.
- Seeds: at least 3; report mean ± std. Specify the evaluation split (global test set vs. per-client test sets) and the aggregation of per-client metrics.
- Communication and computation cost per round (parameters transmitted, extra local computation).
- Fair tuning: the same tuning budget for baselines, with the grid reported in the appendix.

## 4. Evaluation protocol
- **Datasets:** standard vision benchmarks of increasing difficulty, plus at least one non-vision or naturally partitioned dataset when claiming generality.
- **Baselines:** FedAvg; heterogeneity-robust methods (proximal or control-variate corrections, contrastive model alignment); personalized FL methods when the claim is personalization; the most recent state of the art in the specific sub-problem.
- **Metrics:** accuracy (global and/or mean per-client); rounds to reach target accuracy; communication cost; fairness (variance across clients) when relevant.
- **Standard experiments:** main comparison across heterogeneity levels; convergence curves; ablation of each component; sensitivity to key hyperparameters; scalability in the number of clients; robustness to partial participation or dropping clients; cross-backbone variance when claiming architecture independence.

## 5. Figures and tables
- Overview figure in hub-and-spoke layout (server ↔ clients) with numbered steps.
- Main table: datasets × heterogeneity levels, best results in bold, mean ± std.
- Convergence curves with shaded std over seeds; mark distribution-shift points if any.
- Ablation as a table or grouped bars; sensitivity as line plots with the chosen value marked.

## 6. Narrative patterns
- Challenge pairs typically contrast *adapting to the current distribution* with *preserving previously acquired knowledge*, or *local fit* with *global consistency*. Map each challenge to exactly one component, marked (C1)/(C2).
- Explain improvements through the mechanism (what the component constrains or aligns), not by restating numbers.
- Sensitivity results: explain both sides of the optimum (under-capacity vs. over-fitting or over-regularization).

## 7. Common rejection reasons → preventive checks
- Only mild heterogeneity tested → include strong non-IID (small α or pathological shards).
- Missing recent baselines or untuned baselines → add them and report the tuning grid.
- Improvements within seed variance → report std and, where claims are close, significance.
- Communication or privacy cost ignored → quantify extra transmitted parameters, and discuss privacy implications of anything shared.
- Theory assumptions unrealistic or unstated → state them and discuss when they hold.

## 8. Provisional rules (evolution)

> Rules supported by a single exemplar paper. Treat them as suggestions. They become established (moved into §1–7) once a second paper supports them, and are retired if later papers contradict them.

_(none yet)_
