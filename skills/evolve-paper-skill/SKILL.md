---
name: evolve-paper-skill
description: "Self-evolve the top-tier-paper-writing skill from exemplar published papers: an Extractor sub-agent turns a paper into materials, a Writer sub-agent drafts the paper with the skill, a Reviewer sub-agent compares draft and original, and generalized rules are written back into domain templates over N user-set iterations. Use only when the user asks to evolve, train or improve the paper-writing skill from given papers. Do NOT use to write, polish or review the user's own paper."
compatibility: "Agent Skills format. Best with sub-agent support (Claude Code Agent tool, Codex/Antigravity sub-agents); falls back to sequential roles. Python 3.8+ stdlib; the target skill's scripts for lint and validation."
metadata:
  version: "1.0.0"
  target_skill: "top-tier-paper-writing"
---

# Evolve Paper Skill — Standard Operating Procedure

You are the **main agent (orchestrator)**. You run three roles per paper and per iteration, turn their findings into **generalized** skill edits, and let `scripts/evolve.py` enforce every deterministic step. `<evolver>` is this skill's folder; `<skill>` is the target skill folder (default `skills/top-tier-paper-writing`). Run every script as `uv run <evolver>/scripts/evolve.py …`, or with `python3`.

## 0. Ground Rules

1. **Generalize, never memorize.** Follow `references/anti_overfitting.md`. A single paper may only add *provisional* rules to its domain template. Universal rules need papers from ≥ 2 domains.
2. **Information barrier.** The Writer NEVER sees the source paper or its title. Give the Writer only the task file `evolve.py task --role writer` produces. Leakage is measured; a leaking draft is invalid.
3. **The script decides; you do not override it.** Use `evolve.py` for workspaces, validation, scores, keep/revert, rule status and edit checks. NEVER edit `evolution_ledger.json` or files under `.evolution/` by hand.
4. **Edit scope.** Edit only `<skill>/SKILL.md`, `<skill>/references/writing/`, the rule references and `<skill>/references/domains/`. NEVER edit scripts, assets or taxonomies; propose those changes to the user in the final report.
5. **Data hygiene.** Papers, materials and drafts stay in `.evolution/` (git-ignored). NEVER commit them or copy paper text into the skill.
6. **Human-in-the-loop gates.** STOP and ask the user:
   - before starting, confirming the papers, iterations and sub-agent count printed by `init`;
   - at the end, before keeping the changes (they commit) or discarding them (`revert --to-base`).
   NEVER commit, push or open pull requests yourself unless the user asks.

## 1. Setup

1. Ask for (or confirm) the papers, the number of iterations **N** (default 3, max 20), and optionally holdout papers from earlier runs (`evolve.py holdout --list`).
2. Run:
   ```bash
   uv run <evolver>/scripts/evolve.py init --skill <skill> --paper paper1.pdf [--paper paper2.md] --iterations N
   ```
3. Show the user the printed plan (papers, sub-agent runs, warnings) and wait for approval (gate 6).

## 2. Running a role (sub-agent portability)

For each role, run `evolve.py task --role <role> --paper <id> [--iter k]`. It prints a **task file** listing every path the role may read and write.

- **With sub-agents** (Claude Code Agent/Task tool, Codex sub-agents, Antigravity Agent Manager, …): spawn a fresh sub-agent per role invocation. Its prompt is: "Read and follow `<task file>` exactly." Pass nothing else, and wait for it to finish.
- **Without sub-agents:** perform the role yourself, reading only the paths in the task file. Before a Writer run, do not reopen the source paper. Leakage checks still apply.

## 3. Loop (per training paper)

**Step A — Extract (once per paper; cached across runs).** Run the Extractor. Then:
```bash
evolve.py check-materials --paper <id>
```
On FAIL, send the printed errors back to the Extractor and repeat. After 3 failures, stop and report.

**Step B — for k = 1 … N:**
1. **Write.** Run `task --role writer --paper <id> --iter k`, then the Writer sub-agent. Output: `draft/main.tex`, figures and `notes.md`.
2. **Review.** Run `task --role reviewer --paper <id> --iter k`, then the Reviewer sub-agent. Output: `review.json`.
3. **Score.** Run `evolve.py score --paper <id> --iter k` and act on its DECISION:
   - `keep`: continue with step 4 (skip steps 4–6 if k = N).
   - `revert_to_j`: run `evolve.py revert --paper <id> --to j`, then go to step 4 using review **j**. The rules just rejected cannot be re-proposed; choose different ones.
   - `invalid` (leakage): investigate how the Writer saw the paper, fix the barrier, and redo iteration k. This does not count as an iteration.
4. **Triage.** Read `review.json` and the Writer's `notes.md`. For each gap not marked `paper_specific`, `materials_missing` or `writer_error`, in priority order (major first, recurring first):
   1. Generalize the proposed rule with the five tests in `references/anti_overfitting.md` §2.
   2. Run:
      ```bash
      evolve.py propose --paper <id> --iter k --gap G# --scope domain|universal --rule "<text>" [--target <file>] [--contradicts R-xxxx]
      ```
   3. Follow its ACTION line exactly: where to add the line, the marker to append (`<!-- R-xxxx -->`), whether to promote or delete. On `HOLD` or `REFUSED`, make no edit; for REFUSED, generalize further or drop the gap.

   For `rule_not_followed` gaps, follow §3 of `references/anti_overfitting.md` (salience, not new rules).
5. **Edit.** Apply only the ACTION lines, plus wording changes to rules that already carry a marker.
6. **Check.** Run `evolve.py check-edits --paper <id> --iter k`. On FAIL, fix the listed lines, or revert with `evolve.py revert --paper <id> --to k`. The next Writer run is blocked until this passes.

**Step C — Holdout (when the run touched the skill and earlier papers exist).** Run `evolve.py holdout --paper <old-id>`, then Writer → Reviewer → `score --iter 1` for that paper. On `regression`, report it and recommend `revert --to-base`. Never propose rules from holdout papers.

## 4. Finish

1. Run `evolve.py finalize`. It promotes or retires rules based on accumulated evidence and writes `report.md`; it also appends to `<skill>/EVOLUTION_LOG.md`.
2. Run `python3 <skill>/scripts/validate_skill.py <skill>` (must report 0 errors).
3. Show the user `report.md`, the `git diff` of `<skill>`, and suggestions you could not apply (script or extractor changes). Ask whether to keep or discard (gate 6).

## 5. Failure Recovery

| Symptom | Action |
| :--- | :--- |
| A sub-agent output fails schema validation | Send the exact errors back to the same role and rerun; after 3 failures, stop and report. |
| `score` reports `invalid` (leakage) | Discard the draft, tighten the barrier (fresh sub-agent, workspace-only access), and rerun the Writer. |
| `propose` REFUSED (identifier, number, verbatim) | Rewrite at a higher level of abstraction; if impossible, the gap is paper-specific, so drop it. |
| `check-edits` FAIL | Fix exactly the listed lines; never remove markers to get around the check. |
| Scores do not improve over 2 consecutive iterations | Stop early, finalize, and report the plateau (more papers are needed, not more iterations). |
| No sub-agent support and the context is getting long | Finish the current iteration, finalize, and ask the user to continue in a new session. Run state persists in `.evolution/`. |

## 6. Definition of Done
- [ ] Every iteration has `metrics.json` with decision `keep` or a completed revert; no `invalid` drafts remain.
- [ ] `check-edits` passed for every iteration that changed the skill.
- [ ] `finalize` ran; `report.md` and `EVOLUTION_LOG.md` are updated.
- [ ] `validate_skill.py` on the target skill: 0 errors.
- [ ] Holdout run done, or the reason it was skipped is stated (e.g. first paper ever).
- [ ] The user has seen the diff and decided keep or discard.

## 7. Resources
| Path | Use |
| :--- | :--- |
| `scripts/evolve.py` | All deterministic steps (`--help` for each subcommand) |
| `assets/agents/extractor.md`, `assets/agents/writer.md`, `assets/agents/reviewer.md` | Role prompts (filled in by `evolve.py task`; do not hand them out unfilled) |
| `assets/schemas/materials.schema.json`, `assets/schemas/review.schema.json` | Output contracts for the Extractor and the Reviewer |
| `references/anti_overfitting.md` | Scope ladder, generalization tests, root cause → edit type, budgets |
| `references/review_rubric.md` | Scoring anchors used by the Reviewer |
