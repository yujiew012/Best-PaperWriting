# Blind-comparison rubric (abstract + introduction)

Candidates: the drafts of each skill version under test and, when available, the published paper's own abstract and introduction, all anonymized (A, B, C, ...; method names replaced). Score each candidate 1-5 per dimension, then rank them. Adapted from the blind rubric of Best-Paper-Writing-Skill (CC BY 4.0, see the target skill's `NOTICE.md`).

| # | Dimension | 1 | 3 | 5 |
| :--- | :--- | :--- | :--- | :--- |
| D1 | Gap and tension | "existing methods have limitations" | a concrete failure or missing capability | a concrete gap with its condition and cause, set up as a tension the idea resolves |
| D2 | Core idea | the method is only described | the idea is stated but forgettable | one sentence or short name for the idea that a reader would repeat |
| D3 | Gap ↔ contribution | unrelated | mostly matched | each gap answered by exactly one contribution |
| D4 | Calibrated claims | over-claims (unsupported "first", "state-of-the-art", "eliminates") **or** hedges that undercut supported results | supported but timid, or partly inflated | the strongest claims the evidence supports, with numbers and scope |
| D5 | Concreteness | adjectives and abstractions | some numbers | examples, mechanisms and numbers carry the argument |
| D6 | Positioning | no prior work named | named, vague difference | the closest work named with a specific, checkable difference |
| D7 | Flow and economy | repetitive; paragraphs restate each other; terms used before definition | readable, but new information often opens sentences | every sentence adds something; topic sentences carry the story; old-to-new flow; short sentences at the pivots |
| D8 | Overall | a generic machine draft | a solid main-conference paper | as convincing as the best papers of the venue |

Rules for the judge:
- Any invented number, dataset, baseline or citation sets D4 to 1.
- Do not reward length.
- Domain conventions (threat model in security, system model in systems) count under D5 and D6.

Report per case: the score table, the ranking, and for each candidate the most important difference from the best one. `evolve.py eval-blind --reveal` maps the letters back to skill versions and records the result in `.evolution/evals/history.json`.
