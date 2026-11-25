# Intake: what to ask before writing

Used by Branch A (and B for result claims). Ask for missing fields **once, in one compact message**, then continue with `[TODO: ...]` placeholders for what the user cannot answer yet. Never invent an answer. A copy-and-fill version for the user is `assets/intake_template.md`.

## 1. Required (ask before drafting)

| # | Field | A good answer | Why |
| :--- | :--- | :--- | :--- |
| R1 | One-line claim | *We show that [method/finding] [achieves what] [in which setting], because [reason].* | The spine of the claim map |
| R2 | Task | input → output, and 1-2 concrete uses | Opening paragraph |
| R3 | Dominant prior approach | how the strongest existing methods work (mechanism, not just names) | You must describe what you later criticize |
| R4 | Gap + reason | the observable limitation, the condition under which it appears, and its technical cause | Gap = limitation + condition + reason |
| R5 | Method components | name + one-sentence mechanism each | Contribution sentences, method section |
| R6 | Evidence | per result: benchmark/setting, baseline, metric, number, table/figure | Claim map, number roles |

## 2. Recommended: what makes the paper memorable (ask once, in the same message)

| # | Field | Notes |
| :--- | :--- | :--- |
| M1 | Key insight | the property of the problem that makes the design work (not a description of the architecture) |
| M2 | Closest work | 1-3 works and the one checkable difference (mechanism, scope, cost, assumption, input, output, evaluation) |
| M3 | Handle | a short name for the **idea**, distinct from the method's name (*transcribe, then judge*); propose one in the report if the user has none |
| M4 | Concrete example | one input that breaks prior work, a user request, a striking number |
| M5 | What is surprising | the counter-intuitive part of the result |
| M6 | Efficiency and integration | time, memory, data, cost; works with existing pipelines; supported inputs |
| M7 | What it changes | what readers should believe afterwards (*X is unnecessary*, *the common explanation is wrong*) |
| M8 | Limitations | failure cases and costs; they scope the claims and go into the report's Limitations notes |

## 3. Follow-up rules

- R4 has a limitation but no reason → ask: *What in the existing method causes this? What does it assume or compute that breaks?*
- M1 describes the method → ask: *What property of the problem makes this design work?*
- R6 lacks numbers → write `[TODO: number]` and keep the wording at `observe` until the numbers exist.
- The user insists on a claim the evidence does not support → draft it at the supported strength and flag it in the report.
- M3–M7 are missing → do not stop: derive the tension from R3–R4 and propose a handle in the report.

## 4. Revise mode: the user gives an existing abstract or introduction

Do not rewrite blindly.

1. **Decompose** the draft into the fields above and show the user one table: field, what the draft says, status (`present` / `vague` / `missing`). Facts, numbers and terminology in the draft are the user's: keep them verbatim, and never add a result, baseline or reference the draft does not contain.
2. **Ask once** for the missing required fields and the empty memorable fields (§2).
3. **Rewrite** following the route (`writing/routing.md`) and the claim map.
4. **Show a change table**, not a diff: `uv run <skill_dir>/scripts/change_table.py old.tex new.tex --section abstract --reasons reasons.json --out changes.md`. One row per sentence change (original → revised → reason → accept?), each reason naming the rule it follows. The author accepts or rejects row by row; apply only the accepted rows. This is how Ground Rule 7 (approval before replacing more than one paragraph) is met in revise mode.
