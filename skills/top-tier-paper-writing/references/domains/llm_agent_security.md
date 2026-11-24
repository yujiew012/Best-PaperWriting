# Domain Template: LLM & Agent Security

<!-- domain-id: llm_agent_security. Standard template; sections 1-7 hold established conventions, section 8 holds provisional rules added by evolve-paper-skill. Rule ids (R-xxxx) refer to evolution_ledger.json. -->

> **Use when** the paper attacks or defends LLMs or LLM agents: prompt injection (direct or indirect), jailbreaks, tool or plugin misuse, data exfiltration, guardrails, red teaming. Read it together with `references/writing/*.md`; this file adds only domain conventions.

## 1. Venues and reviewer expectations
- Security venues (S&P, CCS, USENIX Security, NDSS) expect a precise threat model, adaptive attackers, a measured utility cost, and responsible disclosure. ML/NLP venues (ICLR, NeurIPS, ACL) weigh benchmark breadth and ablations more heavily.
- Reviewers distrust results on a single model or a single benchmark, and defenses evaluated only against the attacks they were designed for.

## 2. Paper skeleton

| § | Section | Must contain |
| :--- | :--- | :--- |
| 1 | Introduction | A concrete attack scenario (running example); why existing defenses fail, with numbers; the core insight; contributions. |
| 2 | Background | LLM agent loop (planner, tools, memory); where untrusted data enters the context. |
| 3 | Threat model | Attacker position (user prompt vs. third-party content vs. tool output); capabilities; knowledge (black-box vs. white-box); goal (hijack, exfiltrate, harmful output); defender's assumptions and trusted components. |
| 4 | Design | Trust boundary enforced or broken; each component; why it holds against an adaptive attacker. |
| 5 | Evaluation | RQ-driven setup; benchmarks; target models with versions; attacks (including adaptive); defenses as baselines; security vs. utility. |
| 6 | Discussion | Limits; adaptive-attack analysis; deployment cost. |
| 7 | Related work | Attacks / defenses / evaluation frameworks, each subsection ending with the shared gap. |
| 8 | Ethics and disclosure | What was disclosed to whom, when; harmful-content handling; artifact release policy. |

## 3. Mandatory elements
- Model identifiers with versions and access dates (API models change over time); decoding parameters; system prompts in the appendix.
- An explicit trust boundary diagram: which inputs are trusted, which are untrusted, and where the defense sits.
- An adaptive attack: an attacker who knows the defense and optimizes against it. If none is possible, explain why.
- Both security and utility: report the attack success rate (ASR) together with benign task success, utility under attack, and over-refusal / false-positive rate.

## 4. Evaluation protocol
- **Benchmarks:** prefer public suites for the attack surface studied (agent prompt-injection suites, jailbreak suites, harmful-behavior sets), plus a held-out or newly built set when public ones are saturated. Document how any new set was built and validated.
- **Models:** cover at least one closed API model and one open-weight model, of different sizes.
- **Baselines:** no defense; prompting-based defenses; detection/filtering defenses; system-level isolation defenses.
- **Metrics:** ASR (state the success criterion and judge); benign utility; utility under attack; false-positive rate; overhead (latency, tokens, cost).
- **LLM-as-judge:** validate the judge against human labels on a sample and report agreement.
- **Repetition:** sample multiple runs or seeds for stochastic decoding; report variance.

## 5. Figures and tables
- Diagram style: `references/figure_styles/llm_agent_security.json` (pass `--style llm_agent_security` to `gen_architecture_diagram.py`).
- Figure 1: the attack or defense flow on the running example, showing where untrusted content enters (numbered steps).
- Main table: models × defenses, reporting both ASR and utility (never ASR alone).
- A security-utility trade-off plot when the defense has a threshold or budget.
- Per-attack-type breakdown (heatmap or grouped bars) to show coverage.

## 6. Narrative patterns
- Challenge framing: "the model cannot distinguish instructions from data" → insight: enforce separation outside the model (provenance, privilege, isolation) rather than asking the model to behave.
- When reporting failures, distinguish a *capability failure* (the agent could not do the task) from a *security failure* (the agent did the attacker's task).
- Report residual risk honestly: which attack classes remain out of scope.

## 7. Common rejection reasons → preventive checks
- No adaptive attack → add one, or argue why the defense is not optimizable against.
- Utility cost hidden → report benign utility and over-refusal side by side with ASR.
- Single model or outdated models → add a recent closed model and an open-weight model.
- Unvalidated LLM judge → report human agreement on a labeled sample.
- Missing disclosure → add an Ethics Considerations section.

## 8. Provisional rules (evolution)

> Rules supported by a single exemplar paper. Treat them as suggestions. They become established (moved into §1–7) once a second paper supports them, and are retired if later papers contradict them.

- When the attack payload is a perceptual input (image, audio, rendered document), show concrete examples early: a clean and an attacked input side by side with the model's responses, plus one example of every attack variant evaluated; use benign or redacted content when the real payload is harmful. Prefer a panel inside the overview or threat-model figure over a separate full-width float; a pipeline diagram alone does not replace these examples. <!-- R-0001 -->
- When the main contribution is a newly measured vulnerability rather than a defense, use a measurement-paper skeleton: methodology, then only the experiments that characterize the effect, then mechanism evidence, then the explanatory hypothesis, then the experiments that test its predictions (other input variants, other languages, removing the presumed cause), then a short mitigation derived from it, then confounder controls. The introduction's roadmap follows this order exactly, and the main table crosses models with input conditions with a capability metric beside ASR. <!-- R-0002 -->
