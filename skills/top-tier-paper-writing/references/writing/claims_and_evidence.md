# Claims and Evidence: claim map, number roles, say-it-once

Read this before drafting the abstract or introduction, and before writing the evaluation. The claim map is the single place where every claim of the paper, its evidence and its wording strength are decided; the abstract, introduction, method, evaluation, figures and conclusion all follow it.

## 1. Build the claim map first (`claim_map.json`)

Write it before any prose and validate it:

```bash
uv run <skill_dir>/scripts/claim_map.py claim_map.json --tex paper/main.tex --md claim_map.md
```

Format: `assets/claim_map_example.json`. One entry per claim:

| Field | Meaning |
| :--- | :--- |
| `story` (top level) | the 7W: `what`, `why`, `why_now`, `difficulty`, `method_insight`, `results`, `contributions` (`seven_principles.md` §1) |
| `id` | `C1`, `C2`, ... |
| `kind` | `gap`, `insight`, `method`, `result`, `advantage`, `stance`, `contribution` |
| `text` | the claim as it will read in the paper |
| `strength` | the rung of the evidence ladder (§2): `prove`, `show`, `causal`, `observe`, `hypothesis` |
| `evidence` | where it is proven: `"Tab. 2"`, `"Fig. 4"`, `"Thm. 1"`, `"stats.json:margins"`; empty only with `todo` |
| `settings` | how many models, benchmarks or settings the evidence covers (`show` needs ≥ 2) |
| `todo` | what is missing when there is no evidence yet (`"ablation without the filter"`) |
| `where` | the **one** introduction paragraph that states it (`"intro:P4"`) |
| `abstract` | `true` if the abstract states it too |
| `method_section`, `experiment`, `ablation` | the evidence map: where the claim is realized, measured, and isolated |

**List claims in presentation order, strongest evidence first** (`seven_principles.md` §6): within one paragraph, a `prove` claim comes before `show`, `show` before `causal`, `causal` before `observe`. `claim_map.py` warns when a stronger claim follows a weaker one.

Every claim of kind `method` names its `method_section`; every `result` and `advantage` names its `experiment`; every design choice that a result depends on names an `ablation`. A claim with no evidence is either softened to `hypothesis`, or gets a `todo` that goes into the author report. An experiment that supports no claim moves to the appendix.

## 2. Wording follows the strongest rung the evidence supports

| `strength` | Evidence | Wording |
| :--- | :--- | :--- |
| `prove` | a theorem with proof | *We prove that ...* |
| `show` | consistent results across ≥ 2 benchmarks, models or settings | *We show that ...; X outperforms Y on A, B and C by ...* |
| `causal` | a controlled ablation or intervention | *Removing X reduces Y by Z; X is responsible for ...* |
| `observe` | one setting, a correlation, probes | *We observe that ...; this is consistent with ...* |
| `hypothesis` | not tested | *We hypothesize that ...* (never for the core idea of the paper) |

This is the same ladder as the attribution ladder in `evaluation.md`; `claim_map.py` warns when the stated strength needs more evidence than listed. Under-claiming is also an error: when the evidence supports `show`, do not write *may* or *suggests*.

The core idea (insight) is the authors' position: assert it (*The main idea is ...*, *We argue that ...*). Its empirical consequences follow the ladder.

## 3. Number roles

Give every number one role before writing:

| Role | Where | Budget |
| :--- | :--- | :--- |
| `headline` | abstract and introduction | 1-2 numbers that carry the main claim (plus one scale number if scale defines the work) |
| `supporting` | introduction results paragraph | about 8 at most; more only for papers about scale, efficiency or a resource |
| `table` | evaluation | everything else, including ablation values and secondary metrics |

State results as claims first, then attach the headline number: *X outperforms the strongest baseline while using a tenth of the compute (Tab. 1)*. `claim_map.py --tex` counts the numbers in the abstract and the introduction against these budgets; `check_numbers.py` verifies that each number exists in a source file.

## 4. Say each claim once

The most common weakness that blind reviewers find in generated drafts is repetition. Each claim has exactly one introduction paragraph (`where`):

- the insight is not restated after the method;
- the research questions are not re-listed before the results;
- a contributions list, if used, has one line per contribution pointing to a section, and does not repeat the results paragraph;
- generic background is at most two sentences before the specific setting.

The abstract, introduction, contributions and conclusion state the same claims at the same strength and with the same numbers. When the claim map changes, update all four (see `principles_and_style.md` §1.3, backward consistency).

## 5. Mixed results and limitations

- Scope wins precisely, inside the claim: *on the two dynamic benchmarks*, *without ground-truth cameras*, *among open-weight models*. Never write *on all benchmarks* or *state-of-the-art* without naming the comparison.
- Settings where the method is not best are acknowledged in the evaluation (Ground Rule 8) and collected in the author report's **Limitations notes**. Venues that require a Limitations section (ACL, see `venues.json`) get them there.
- Whether limitations may also appear in the abstract or introduction is a house-style choice; ask the user when it matters. Do not hide them anywhere.

## 6. Stance

About half of strong introductions end with a stance: what the work changes for the field. Write one only when the results support more than "better on benchmark B":

- *We argue that [practice] is unnecessary, and show that [simpler alternative] suffices.*
- *Contrary to the common view that [belief], we find that [result].*
- *This is a step toward [long-standing goal]: [what now works].*

Record it as a claim of kind `stance` with its evidence.
