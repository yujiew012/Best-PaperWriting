# Review Rubric (1–5 per dimension)

Score the **draft as a paper for the target venue**, using the gold paper as the reference for what "publishable" looks like. Use the anchors below; half points are allowed. The overall score is the mean of the 8 dimensions (computed by `evolve.py score`).

| Dimension | 1 | 3 | 5 |
| :--- | :--- | :--- | :--- |
| `structure` | Sections missing or misordered; domain-mandatory sections absent | Standard structure; minor imbalance (an over-long background, a thin evaluation) | Structure matches the venue and domain template; section lengths proportional to their importance |
| `introduction` | Problem unclear; no gap evidence; contributions vague | Gap and method stated; challenges and components not clearly paired | Concrete scenario → quantified gap → challenges ↔ insights ↔ components → precise contributions |
| `related_work` | A list of papers | Grouped by approach; limitations stated loosely | Taxonomy by technical approach; each group ends with the shared limitation this paper resolves |
| `method` | Hard to follow; notation inconsistent | Correct but flat; intuition or overview missing | Overview figure + algorithm; each component: intuition → formulation → why it works; consistent notation |
| `evaluation` | Reads tables aloud; setup incomplete | RQ-driven; some analysis; evidence selection uneven | Every paragraph: claim → selected evidence → mechanism; complete setup; ablation and sensitivity explained |
| `figures_tables` | Missing or unreadable; captions state conclusions | Adequate; style or caption conventions partly violated | Right chart types; colorblind-safe; captions describe without concluding; tables generated from data |
| `language` | Vague, hedging, inconsistent terms | Clear but wordy or repetitive | Concise, precise, consistent terminology; formal register |
| `domain_conventions` | Ignores the area's norms (e.g. no threat model in security) | Most norms present | All mandatory elements of the domain template present and well executed |

## Calibration
- A score of 5 means the dimension would not draw a reviewer complaint at the target venue, not that it matches the gold word for word.
- If the gold itself is weak on a dimension, do not penalize the draft for differing; note it in `summary`.
- Score each draft independently. Do not adjust scores to show progress across iterations.
