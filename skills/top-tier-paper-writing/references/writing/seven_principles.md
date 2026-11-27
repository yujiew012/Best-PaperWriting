# Seven Principles of Scientific Writing

Read this before drafting or revising any section. Each principle comes with the rules that apply it and the check that enforces it, so a draft can be verified rather than judged by feel.

| # | Principle | Apply it with | Check |
| :--- | :--- | :--- | :--- |
| 1 | Tell a good story (7W) | `story` in the claim map; `routing.md` | `claim_map.py` (missing W), `outline.py` (topic sentences tell the story) |
| 2 | Clear organizational structure | section opening and closing paragraphs; topic sentences | `outline.py` |
| 3 | Old-to-new information flow | topic position = old, stress position = new; define before use | `lint_paper.py` W311 |
| 4 | Strategic placement | put information where readers expect it; cross-reference | `outline.py`, `lint_paper.py` W101 |
| 5 | Sentence length and structure | one or two topics per sentence; verb next to subject | `lint_paper.py` W312, `style_metrics.py` |
| 6 | Decreasing order of credibility | strongest evidence first | `claim_map.py` (evidence order) |
| 7 | Cognitive alignment | present data the way readers expect it | `lint_paper.py` W314, `figures_and_captions.md` §0 |

## 1. Tell a good story around one thesis (7W)

A paper argues one central thesis. Before writing, answer the seven questions in the claim map's `story` block (`assets/claim_map_example.json`); every section then serves one of the answers.

| W | Question | Claim-map key | Where it is answered |
| :--- | :--- | :--- | :--- |
| What | What is the engineering or scientific problem? | `what` | title, abstract sentence 1, introduction ¶1 |
| Why | Why is it important? | `why` | introduction ¶1 |
| Why now | What makes the research necessary and urgent now? | `why_now` | introduction ¶1-2 (a trend, a deployment, a failure) |
| Difficulty | What are the core difficulties? | `difficulty` | introduction ¶2-3 (gap + technical cause) |
| How | What is the method, its key insight ("magic touch"), and why does it work? | `method_insight` | introduction ¶3-4, method section |
| Results | What are the main results? | `results` | abstract, introduction results ¶, evaluation |
| Contributions | What does the paper contribute? | `contributions` | introduction contributions, conclusion |

`claim_map.py` warns when a W is missing. Read the reverse outline (`outline.py`): the topic sentences alone should answer the seven questions in order.

## 2. Clear organizational structure

- Use the standard sections (title, abstract, keywords, introduction, related work, body, discussion, conclusion and future work); each has one function. **Innovate in the research, not in the format.**
- **Every section opens with a paragraph that states its purpose** (what this section establishes and how it is organized) and **ends with a transition** to the next section. A section that jumps straight into its first subsection has no such paragraph; `outline.py` flags it.
- **Every paragraph opens with a topic sentence** that states its main idea and ends with a transition to the next paragraph. A topic sentence of more than about 35 words usually carries two ideas: split the paragraph.
- The title, abstract, introduction and conclusion form one chain: the same thesis, the same terms, the same numbers (`claims_and_evidence.md` §4).

## 3. Old-to-new information flow

- **Topic position (sentence start) = old information** that links back to what the reader has just read; **stress position (sentence end) = new information** you want emphasized.
- Before writing a sentence, ask whether its first terms have been mentioned before. If not, reorder the sentence or introduce them first.
- **Never use a term before defining it.** Define acronyms at first use, in the abstract and again in the body: `lint_paper.py` W311 reports acronyms used before their definition.
- Repeat the key noun of the previous sentence at the start of the next one instead of adding a logical connector ("... a 2D dilation filter. This filter ...").

## 4. Strategic placement

- Put information where most readers expect it: the problem in the introduction, assumptions in the threat or system model, setup details in the evaluation setup, proofs and extra results in the appendix (`principles_and_style.md` §1.1).
- Take the reader's view: what does the reader need to know at this point, and where will they look for it?
- **Cross-reference** so that earlier and later conclusions echo each other: the introduction points to the section and table that prove each claim; the evaluation points back to the design choice it validates; every float is referenced (W101).
- Re-read the outline and move paragraphs until the order follows the logic. Revising the writing improves the thinking.

## 5. Sentence length and structure

- **One or two topics per sentence.** Prefer short sentences; split at about 40 words (`principles_and_style.md` §3.2). **Sixty words or more is always too long**: `lint_paper.py` W312.
- **Keep the verb next to the subject.** Readers look for the action right after the subject; move long modifiers after the main clause.
  - × *"The defense, which first transcribes the image with the same model and then, in a second prompt that never sees the image, judges the transcription, restores refusals."*
  - ✓ *"The defense restores refusals. It first transcribes the image with the same model, then judges the transcription in a second prompt that never sees the image."*
- Mix lengths: short sentences at the pivots (bottleneck, cause, idea), full sentences that carry a relation elsewhere (`style_metrics.py`).

## 6. Decreasing order of credibility

Argue like a case in court: present the strongest evidence first.

- Order the evidence for each claim from strongest to weakest: proof → consistent results across settings → controlled ablation → single observation → explanation (the strength ladder of `claims_and_evidence.md` §2). Once readers accept the strongest evidence, they accept the weaker evidence more readily, and a reviewer who disagrees with a later point has to think about why.
- Within the evaluation, the main comparison comes before ablations, ablations before case studies, case studies before anecdotes.
- Argue from several angles (benchmarks, models, metrics, ablations, analysis): independent pieces of evidence corroborate one another into a chain.
- `claim_map.py` warns when, in the same paragraph, a weaker claim is listed before a stronger one: the order of `claims` in the claim map is the presentation order.

## 7. Cognitive alignment

Present data the way readers expect to read it:

- the same method order, names, colours and markers in every table and figure (ours last before the ground truth, or first, but consistent); `lint_paper.py` W314 compares the method order across tables;
- metric direction marked (↑ / ↓), units in headers, best result in bold, axes that grow in the reading direction unless the convention of the field says otherwise (and then labelled);
- one message per figure, with the takeaway where the venue expects it (`figures_and_captions.md` §0);
- numbers in the text in the same order and rounding as in the table they come from.
