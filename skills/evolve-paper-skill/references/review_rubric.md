# Review Rubric (1–5 per dimension)

Score the **draft as a paper for the target venue**, using the gold paper as the reference for what "publishable" looks like. Use the anchors below; half points are allowed. The overall score is the mean of the 8 dimensions (computed by `evolve.py score`).

| Dimension | 1 | 3 | 5 |
| :--- | :--- | :--- | :--- |
| `structure` | Sections missing or misordered; domain-mandatory sections absent; no central thesis | Standard structure; minor imbalance (an over-long background, a thin evaluation); some sections lack an opening purpose paragraph or transitions | One thesis told as a story (the 7W answered); structure matches the venue and domain template; every section opens with its purpose and ends with a transition; topic sentences alone tell the story; section lengths proportional to their importance |
| `introduction` | Problem unclear; no gap evidence; contributions vague | Gap and method stated; challenges and components not clearly paired | Concrete scenario → quantified gap → challenges ↔ insights ↔ components → precise contributions |
| `related_work` | A list of papers | Grouped by approach; limitations stated loosely | Taxonomy by technical approach; each group ends with the shared limitation this paper resolves |
| `method` | Hard to follow; notation inconsistent | Correct but flat; intuition or overview missing | Overview figure + algorithm; each component: intuition → formulation → why it works; consistent notation |
| `evaluation` | Reads tables aloud; setup incomplete | RQ-driven; some analysis; evidence selection uneven or weak evidence first | Every paragraph: claim → selected evidence → mechanism; evidence in decreasing order of credibility (main comparison → ablation → analysis → cases); complete setup; ablation and sensitivity explained |
| `figures_tables` | Missing or unreadable; captions break the venue's convention | Adequate; style, caption or ordering conventions partly violated | Right chart types; colorblind-safe; captions follow the venue (descriptive or takeaway-first); the same method order, names and colours in every table and figure; tables generated from data |
| `language` | Vague, hedging, inconsistent terms; terms used before they are defined; sentences of 60+ words | Clear but wordy or repetitive; new information often at the start of sentences | Concise, precise, consistent terminology; old information first and new information last; every term defined before use; one or two topics per sentence with the verb next to the subject; formal register |
| `domain_conventions` | Ignores the area's norms (e.g. no threat model in security) | Most norms present | All mandatory elements of the domain template present and well executed |

## Calibration
- A score of 5 means the dimension would not draw a reviewer complaint at the target venue, not that it matches the gold word for word.
- If the gold itself is weak on a dimension, do not penalize the draft for differing; note it in `summary`.
- Score each draft independently. Do not adjust scores to show progress across iterations.
