# Anti-Overfitting Rules (how a gap becomes a skill edit)

> Core principle: the skill stores **transferable conventions**, never facts about the exemplar paper. One paper is weak evidence; agreement across papers is strong evidence.

## 1. Where a rule may go

| Evidence | Scope | Where it may be written | Status |
| :--- | :--- | :--- | :--- |
| 1 paper | domain | `references/domains/<id>.md` **§8 Provisional rules** only | `provisional` |
| ≥ 2 papers, same domain | domain | Moved into the matching §1–7 of that domain template | `established` |
| 1 paper, or ≥ 2 papers from one domain | universal | **Nowhere yet**: kept in the ledger | `candidate` |
| ≥ 2 papers from ≥ 2 domains | universal | `SKILL.md`, `references/writing/*.md`, or the figure / layout / bibliography / revision references | `active` |
| Later papers contradict it at least as often as they support it | any | Removed | `retired` |
| Its iteration made the next draft worse | any | Removed (reverted) | `rejected` |

`evolve.py propose` computes the status. `evolve.py check-edits` enforces this table on the actual diff.

## 2. Generalize before proposing

Rewrite each `proposed_rule` from the review until it passes all five tests:

1. **Swap test:** it would still be correct for another paper in the same scope with a different method.
2. **No identifiers:** no method or component names, no result numbers, no phrases from the paper (the guard blocks these automatically).
3. **Actionable:** an imperative that a writer can follow and a reviewer can check ("State X in Y", "NEVER Z").
4. **Right layer:** a domain convention goes into the domain template, a writing principle into the universal files, a recurring check into a script (propose a script change to the human; evolution never edits `scripts/`).
5. **Not a duplicate:** if an existing rule covers it, strengthen that rule's wording or salience. `propose` merges rules with similar text automatically as extra evidence.

| | Example |
| :--- | :--- |
| ❌ paper-specific | "Report the 2.35%–5.18% margin on CIFAR-100 in the abstract." |
| ❌ too narrow | "Always use exactly two challenges and two components." (one paper's choice) |
| ✅ domain | "In FL papers, state the partition protocol (α or shards per client) in the first paragraph of the setup." |
| ✅ universal (once ≥ 2 domains agree) | "In the abstract, give one quantitative result together with the setting that makes it meaningful." |

## 3. Root cause → type of edit

| Root cause | Edit |
| :--- | :--- |
| `missing_rule` | Add a rule (subject to §1). |
| `vague_rule` | Rewrite the existing rule more concretely, keep or add its marker, and add a ❌/✅ example if it helps. |
| `wrong_rule` | `propose --contradicts R-xxxx` (counter-evidence). For unmarked base rules, raise it with the human in the final report; do not silently delete base content. |
| `rule_not_followed` | Increase salience: move the rule into the branch's **Verify** step or the Definition of Done, or ask the human for a script check. Do not add a duplicate rule. |
| `materials_missing` / `writer_error` | No skill edit. Note it in the report (extractor prompt issues go to the human). |
| `paper_specific` | No skill edit. |

## 4. Budgets
- At most 40 added rule lines per iteration, and at most 8 provisional rules from any single paper. Prioritize major gaps that recur.
- `SKILL.md` stays under 500 lines (checked by `validate_skill.py`). Prefer references over `SKILL.md`.
- Every added line ends with its marker `<!-- R-xxxx -->`; unmarked additions are rejected.

## 5. Regression protection
- The keep/revert decision compares each new draft with the best earlier draft of the same paper (tolerance 0.25 on the 1–5 scale). A drop reverts the edits that caused it, and those rules become `rejected`.
- Run at least one **holdout** paper (an earlier exemplar with cached materials) after evolving on a new paper. A drop against its previous best means the edits overfit; consider `revert --to-base`.

## 6. Figure mode

A figure is judged on what it communicates, not on whether it looks like the original.

1. **No imitation.** A gap that only says "make it look like the gold" (same colours, same arrangement) is not a skill defect. Rules and style changes must name a communication goal, e.g. "the attacker must be visually distinct from benign parties" or "a trust boundary encloses the trusted components".
2. **Content-only brief.** The brief must not dictate layout, so the Illustrator's design follows the skill rather than the original. `check-brief` rejects appearance words; do not work around it with synonyms.
3. **Three kinds of change, three paths:**
   - *Figure rules* (what to show, numbering, labelling, conventions of a research area) follow the same ladder as writing rules: §8 of the domain template first, `figures_and_captions.md` only with papers from ≥ 2 domains.
   - *Style values* (fonts, strokes, fills, role colours, default topology) change only through `propose-style`. Values are confined to `references/figure_styles/_bounds.json`, start as provisional overrides of one domain's profile, and move into its base when a second paper agrees. `default.json` needs agreement from 2 domains.
   - *Generator capabilities* (icons, curved or bundled edges, panels, nested groups) are **never** changed by the loop. `request-feature` logs them with their support count for a human, who closes them with `resolve-feature` after changing the generator (or declining).
4. **Budgets.** ≤ 3 style changes per iteration and ≤ 6 per paper. A value reverted in a run cannot be proposed again in that run.
5. **Deterministic floor.** A figure that renders with more layout issues or lower brief coverage than the best earlier iteration is reverted, whatever the Critic's score.

