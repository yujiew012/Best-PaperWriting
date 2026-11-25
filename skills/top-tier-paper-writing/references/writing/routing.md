# Routing: paper type × motivation → how the paper argues

Read this before `abstract_and_introduction.md`. The domain template (`references/domains/<id>.md`) says what a research area expects (threat models, baselines, metrics); the **route** says how this particular paper makes its case. Choose the route first, write it into the claim map (`paper_type`, `motivation`, `tension`), then follow its plan. The 7-paragraph introduction in `abstract_and_introduction.md` is the plan for the `failure` route with two challenges (common in defense and systems papers); other routes use the plans below.

## 1. Paper type (the first "yes" wins)

| # | Question | Type |
| :--- | :--- | :--- |
| 1 | Is the main deliverable a theorem, bound or formal guarantee? | **L6 theory** |
| 2 | Is it a dataset, benchmark, tool or platform? | **L7 resource** |
| 3 | Is it a measurement of a deployed system, population or phenomenon (a vulnerability study, an Internet measurement, a user study)? | **L8 measurement** |
| 4 | Does it re-examine a popular claim or evaluation practice? | **L4 re-examination** |
| 5 | Does it explain a known phenomenon? | **L5 mechanism** |
| 6 | Is it a systematic sweep that yields an empirical law or recipe? | **L3 scaling / study** |
| 7 | Does it enable something that was not possible before? | **L2 new capability** |
| 8 | Otherwise: does an existing task better (more accurate, faster, safer, cheaper) | **L1 method** |

A new attack that is mainly *measured* (how often it works, on which systems, why) is L8; a new attack technique that is the contribution is L1/L2. A defense is L1.

## 2. Motivation (L1/L2) and tension

| Motivation | Choose when | Test question |
| :--- | :--- | :--- |
| `failure` | a strong method breaks under a specific, reproducible condition | Can you show the baseline failing? |
| `cost` | existing methods or the obvious fix work but are too slow, expensive or complex | Can you quantify the cost you remove? |
| `capability-gap` | no existing system can do the task at all | Is there no reasonable baseline for the full task? |
| `insight` | one observation makes a complex pipeline unnecessary | Is there one sentence from which the method follows? |
| `trend` | the work is the next step of a visible field-wide trend | Can you tell a three-stage history ending with this paper? |

Pick the motivation that explains **why the method exists**; a second one may get its own paragraph.

**Tension** (how the gap is made to feel like a conflict the idea resolves): `tradeoff` (two goals pull apart; the most common), `capability-missing`, `obvious-fix-too-costly`, `unexplained-phenomenon`, `open-question`, `belief-overturned`.

## 3. Route table

| Route | Introduction plan | Abstract arc | Figure 1 |
| :--- | :--- | :--- | :--- |
| L1 `failure` | task → credit the method you fix, incl. the component you will blame → failure condition + root cause → insight → one contribution per symptom → contrast with closest work → evidence | Setting → Gap → Insight → Method → Result | the baseline failing and ours fixing it (diagnosis) |
| L1 `cost` | credit + flaw as a thesis → why it works only in contrived settings → the obvious fix and its quantified cost → the principle that moves the cost → evidence + secondary advantages | Setting → Gap (cost) → Method → Result | old mechanism vs. ours, cost written on it |
| L2 `capability-gap` | a concrete scenario the reader can picture → credit current systems, "they lack the ability to ..." + the main reason → goal as a mechanism → technique 1 → its side effect → technique 2 → applications + new evaluation | Method first ("We present X, a ... that ...") → Result | showcase: real inputs → outputs |
| L1 `insight` | why it matters, one vivid example → dominant method, its cost itemized → "we show that ... can be done directly" + the observation → intuition, mechanism-level contrast → one contribution | Setting → Gap → Insight → Method → Result | the pipeline that disappears |
| L1/L2 `trend` | three-stage history → "even so, ... still" → closest work with two checkable limits → our step → evidence | Method first → Result | showcase or concept |
| L3 scaling / study | the decision at stake (with a number) → what the field uses and believes → the open question → what made the study possible → the regularity found + the surprising observation | Question → Study → Regularity → Recipe | plot with the regularity annotated |
| L4 re-examination | the belief, credited fairly → the question and why existing evidence does not settle it → our test → findings → stance | Setting → Test → Results → Stance | plot showing the reversal |
| L5 mechanism | the phenomenon, so a newcomer sees why it is puzzling → existing explanations and why they fall short → our explanation, named → evidence from two sides (controlled experiments + model) | Setting → Puzzle → Explanation → Evidence | concept, then a plot |
| L6 theory | the question → what is known → main result in words → comparison with known bounds → implications | Setting → Result in words → Implication | concept |
| L7 resource | the capability wanted + why data/tools are missing → why the obvious collection fails, our principle → contents (scale) + closest resources → what it enables (findings) → release | Gap → Resource (scale) → Findings → Release | the resource with its scale |
| L8 measurement | the phenomenon and why it matters, a concrete case → what is unknown or mis-measured → methodology → findings (characterizing the effect) → mechanism evidence → explanation and the experiments testing its predictions → mitigation → controls | Setting → Methodology → Findings → Implication | the measured phenomenon |

## 4. What every route shares

- Credit specific prior work before the gap, and describe the component you later blame.
- The gap = what fails or is missing + the condition + the technical reason; give the cause its own short sentence ("The main reason is that ...").
- State the insight as an observation about the problem, not as an announcement ("Our key insight is ..." at most once, never in the abstract).
- A **handle**: a short name for the idea itself, distinct from the method's name, used where the idea is introduced and in the title when it fits.
- One **concrete example** in paragraph 1 or 2: an input that breaks prior work, a scene, a striking number.
- Name the **closest work** and one checkable difference (mechanism, scope, cost, assumption, input, output, evaluation) after the method.
- Results as claims with headline numbers (`claims_and_evidence.md` §3); end with the strongest result or a stance.

## 5. Output of this step (goes into the claim map and the author report)

```text
Route: L1 / failure (secondary: cost); tension: tradeoff
Why: the baseline visibly fails when inputs are degraded, and we can name the mechanism.
Abstract: Setting -> Gap -> Insight -> Method -> Result
Introduction: credit -> failure + cause -> insight -> 2 contributions -> contrast -> evidence -> contributions
Figure 1: diagnosis (baseline failing vs. ours)
```
