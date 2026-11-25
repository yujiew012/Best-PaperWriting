# Notice and attribution

## Best-Paper-Writing-Skill (CC BY 4.0)
Several ideas in this skill are adapted from **Best-Paper-Writing-Skill** by gulucaptain
(https://github.com/gulucaptain/Best-Paper-Writing-Skill), licensed under CC BY 4.0:

- routing by paper type and motivation, and Figure 1 chosen by route (`references/writing/routing.md`);
- the claim map, number roles and the say-it-once rule (`references/writing/claims_and_evidence.md`);
- the "memorable" intake fields and the change table for revisions (`references/intake.md`, `scripts/change_table.py`);
- two-sided style metrics against a corpus, the boilerplate and workflow-trace checks
  (`scripts/style_metrics.py`, `lint_paper.py` W306-W310);
- the figure plan with placeholders that carry their plan (`scripts/figure_plan.py`, `assets/figure_placeholders.tex`);
- the function-tagged exemplar bank with a copy guard (`references/exemplars/`, `scripts/find_exemplars.py`);
- the held-out evaluation with a blind comparison that includes the original paper (`evolve-paper-skill`).

The text and code here were written for this skill; nothing was copied verbatim except
`references/style_corpus/general.json`, which reproduces the aggregate percentiles (no text) of
`references/corpus/corpus_stats.json` from that repository. Changes: only the metrics this skill computes were kept,
values rounded to three decimals.

No sentences or passages from the papers quoted in that repository are included here.

## Quoted passages in references/exemplars/
Exemplar passages are short, attributed quotations from published papers, added only through
`evolve.py add-exemplars` and used for commentary on structure. Their copyright remains with their authors.
Authors can ask for removal; `evolve.py add-exemplars --remove <paper_id>` removes a paper's passages.
