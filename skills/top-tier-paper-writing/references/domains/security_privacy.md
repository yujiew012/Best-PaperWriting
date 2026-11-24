# Domain Template: Security & Privacy

<!-- domain-id: security_privacy. Standard template; sections 1-7 hold established conventions, section 8 holds provisional rules added by evolve-paper-skill. Rule ids (R-xxxx) refer to evolution_ledger.json. -->

> **Use when** the paper is about attacks, defenses or privacy for systems, networks or ML: poisoning and backdoors, Byzantine robustness, inference attacks, differential privacy, cryptographic protocols. LLM- and agent-specific security uses `llm_agent_security.md` instead. Read it together with `references/writing/*.md`.

## 1. Venues and reviewer expectations
- S&P, CCS, USENIX Security, NDSS, TDSC and TIFS expect: a precise threat model; security arguments (formal where possible); evaluation against strong and adaptive adversaries; utility and performance cost; ethics.
- Reviewers look for the weakest assumption. State every assumption and justify why it is realistic.

## 2. Paper skeleton

| § | Section | Must contain |
| :--- | :--- | :--- |
| 1 | Introduction | Concrete scenario; why existing defenses or attacks fall short, quantified; insight; contributions. |
| 2 | Background | Only what the threat model and design need. |
| 3 | Threat model | Adversary goals, capabilities, knowledge, budget; trusted parties; out-of-scope attacks. |
| 4 | Design | Design goals G1–Gn; components; design decisions with rationale (alternatives considered). |
| 5 | Security analysis | Theorem or argument per goal: assumptions → statement → proof sketch → what it does not cover. |
| 6 | Evaluation | Attacks of increasing strength, including adaptive ones; utility; overhead; comparison with defenses. |
| 7 | Discussion | Limitations, adaptive adversaries, deployment. |
| 8 | Related work | Grouped by technique; the shared gap at the end of each subsection. |
| 9 | Ethics considerations | Disclosure, data handling, dual use. |

## 3. Mandatory elements
- Adversary model table or paragraph: goals, capabilities, knowledge (white/grey/black-box), budget (fraction of malicious parties, ε, queries).
- A design-goals table comparing against prior defenses (✓/✗ per goal).
- Adaptive attacks against the proposed defense.
- Cost: accuracy or utility loss, runtime, communication or storage overhead.

## 4. Evaluation protocol
- Sweep attacker strength (malicious fraction, perturbation budget, ε) and show where the defense breaks.
- Report detection metrics as TPR/FPR (or ROC/AUC), not accuracy alone; report false positives on benign data.
- Use standard datasets and models of the sub-field, plus at least one realistic deployment setting.

## 5. Figures and tables
- System and threat overview figure marking trusted and untrusted parties, attacker entry points, and numbered steps.
- Trade-off curves: attack budget vs. ASR / accuracy; privacy budget vs. utility.
- A table of attacks × defenses with both ASR and clean accuracy.

## 6. Narrative patterns
- Frame the gap as a violated assumption of prior work (e.g. "assumes an honest majority", "assumes the server sees plaintext updates").
- Each design decision is one paragraph: the decision → the alternative → why the alternative fails under the threat model.
- Security claims are scoped: "under assumption A, the adversary cannot …"; say what remains possible.

## 7. Common rejection reasons → preventive checks
- Weak or non-adaptive adversary → add adaptive attacks and strongest-known attacks.
- Unrealistic threat model → justify each capability with a real deployment.
- Utility cost not reported → add clean accuracy and overhead.
- Formal claims without assumptions → state assumptions next to each theorem.

## 8. Provisional rules (evolution)

> Rules supported by a single exemplar paper. Treat them as suggestions. They become established (moved into §1–7) once a second paper supports them, and are retired if later papers contradict them.

_(none yet)_
