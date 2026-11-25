# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Held-out evaluation for evolve.py: does a skill version write better abstracts and introductions?

  make-case    turn an exemplar paper (cached materials) into a held-out case: sanitized materials + graders.
               The paper is marked 'eval' in the ledger and can no longer contribute rules, style ranges
               or exemplars (it would leak into its own test).
  eval-task    workspace + task file for an Eval Writer sub-agent using the current skill (snapshot)
  eval-score   deterministic graders: sections present, every number traced to the materials, no lint errors
               or workflow traces, number budget, style findings, memorization of the original (8-gram overlap,
               longest shared run; computed locally, the original never leaves .evolution/)
  eval-blind   anonymized pack of several runs (and the original's abstract + introduction) for a Judge
               sub-agent; --reveal maps the letters back and records scores and ranks
  eval-status  every case, run, score and blind result

Everything lives in .evolution/evals/<paper_id>/ (git-ignored).
"""
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys

E = None
DIMS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]
MEMO_N = 8


def bind(module):
    global E
    E = module


def corpus():
    import corpus_mode
    corpus_mode.bind(E)
    return corpus_mode


def case_dir(ctx, pid):
    return os.path.join(ctx.workdir, "evals", pid)


def skill_version(skill):
    h = hashlib.sha256()
    for rel, path in sorted(E.skill_files(skill).items()):
        if rel in E.IGNORED:
            continue
        h.update(rel.encode())
        h.update(open(path, "rb").read())
    git = None
    try:
        git = subprocess.run(["git", "-C", skill, "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                             timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        pass
    return h.hexdigest()[:10], git


def load_case(ctx, pid):
    c = E.jload(os.path.join(case_dir(ctx, pid), "case.json"), default=None)
    if c is None:
        E.die(f"no eval case for {pid}; run `evolve.py make-case --paper {pid}`", 1)
    return c


def graders(mat):
    det = [
        {"id": "A1", "type": "det", "text": "The draft has a title, an abstract and an introduction"},
        {"id": "A2", "type": "det", "text": "Every number in the abstract and introduction comes from the materials"},
        {"id": "A3", "type": "det", "text": "lint_paper.py reports no error and no boilerplate or workflow trace (W306/W307)"},
        {"id": "A4", "type": "det", "text": "Number budget: abstract <= 5 numbers, introduction <= 14"},
        {"id": "A5", "type": "det", "text": "No long verbatim run from the original paper (< 12 words, 8-gram overlap < 3%)"},
    ]
    judge = [
        {"id": "J1", "type": "judge", "text": "The core idea is asserted confidently, not downgraded to a hypothesis"},
        {"id": "J2", "type": "judge", "text": "The gap is stated with its condition and its technical cause"},
        {"id": "J3", "type": "judge", "text": "The closest prior work is named with one checkable difference"},
        {"id": "J4", "type": "judge", "text": "Each claim is made once; the contributions do not repeat the results paragraph"},
        {"id": "J5", "type": "judge", "text": "No invented citation, baseline or result (missing ones are marked TODO)"},
    ]
    idea, prob = mat.get("idea", {}), mat.get("problem", {})
    k = 6
    if idea.get("core_insight"):
        judge.append({"id": f"J{k}", "type": "judge", "text": f"The text conveys this insight: {idea['core_insight']}"})
        k += 1
    if prob.get("motivating_example"):
        judge.append({"id": f"J{k}", "type": "judge",
                      "text": f"The introduction uses a concrete example like: {prob['motivating_example']}"})
        k += 1
    for ch in prob.get("challenges", [])[:3]:
        if ch.get("statement"):
            judge.append({"id": f"J{k}", "type": "judge", "text": f"The text addresses: {ch['statement']}"})
            k += 1
    return det + judge


def cmd_make_case(a):
    ctx = E.Ctx(a.workdir, a.run)
    pid = a.paper
    cache = ctx.paper_cache(pid)
    if not E.jload(os.path.join(cache, "materials.check.json"), default={}).get("ok"):
        E.die(f"paper {pid} has no validated materials (run the extractor and check-materials)", 1)
    led = ctx.ledger()
    used = sorted({r["id"] for r in led.get("rules", []) for e in r.get("evidence", []) if e.get("paper") == pid})
    if used and not a.force:
        E.die(f"paper {pid} already backs rules {used[:6]}{'...' if len(used) > 6 else ''}: the skill was trained "
              f"on it, so it is not held out. Pick an unseen paper (or --force to accept a biased case).", 1)
    if led.get("papers", {}).get(pid, {}).get("exemplars"):
        E.die(f"paper {pid} contributed exemplars; remove them first (`add-exemplars --remove {pid}`)", 1)
    mat = E.jload(os.path.join(cache, "materials.json"))
    d = case_dir(ctx, pid)
    os.makedirs(d, exist_ok=True)
    shown = {k: v for k, v in mat.items() if k not in ("source_meta", "terms")}
    E.jsave(os.path.join(d, "materials.json"), shown)
    src = corpus().paper_sources(ctx).get(pid)
    case = {"paper_id": pid, "created": E.now(), "domain": mat.get("domain", {}).get("id"),
            "venue": a.venue or "acl", "source": src, "graders": graders(mat), "biased": bool(used),
            "terms": sorted({t for key in ("method_names", "component_names", "other_identifiers")
                             for t in mat.get("terms", {}).get(key, []) if isinstance(t, str) and len(t) >= 3},
                            key=len, reverse=True)}
    E.jsave(os.path.join(d, "case.json"), case)
    led.setdefault("papers", {}).setdefault(pid, {})["role"] = "eval"
    E.jsave(ctx.ledger_path, led)
    print(f"case {pid}: {len(case['graders'])} graders ({sum(g['type'] == 'det' for g in case['graders'])} "
          f"deterministic) in {d}")
    print("The paper is now held out: propose, corpus-stats and add-exemplars refuse it.")
    print(f"next: evolve.py eval-task --case {pid}")
    return 0


def cmd_eval_task(a):
    ctx = E.Ctx(a.workdir, a.run)
    case = load_case(ctx, a.case)
    skill = ctx.skill
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    ws = os.path.join(case_dir(ctx, a.case), "runs", ts)
    os.makedirs(os.path.join(ws, "draft"))
    E.snapshot(skill, os.path.join(ws, "skill"))
    for f in ("evolution_ledger.json", "EVOLUTION_LOG.md"):
        p = os.path.join(ws, "skill", f)
        if os.path.exists(p):
            os.remove(p)
    corpus().strip_paper_exemplars(os.path.join(ws, "skill"), a.case)
    shutil.copyfile(os.path.join(case_dir(ctx, a.case), "materials.json"), os.path.join(ws, "materials.json"))
    ver, git = skill_version(skill)
    E.jsave(os.path.join(ws, "meta.json"), {"case": a.case, "run": ts, "skill_version": ver, "git": git,
                                            "label": a.label or git or ver, "created": E.now()})
    task = E.fill("eval_writer.md", {"WORKSPACE": ws, "MATERIALS_PATH": os.path.join(ws, "materials.json"),
                                     "SKILL_DIR": os.path.join(ws, "skill"), "DRAFT_DIR": os.path.join(ws, "draft"),
                                     "DOMAIN_ID": case.get("domain") or "unknown", "VENUE": case.get("venue", "acl")})
    tp = os.path.join(ws, "EVAL_WRITER_TASK.md")
    open(tp, "w", encoding="utf-8").write(task)
    print(f"eval run {ts} (skill {ver}{f' @ {git}' if git else ''})\nworkspace: {ws}\ntask file: {tp}")
    print("Give a fresh sub-agent ONLY this task file; then run `evolve.py eval-score --case "
          f"{a.case} --eval-run {ts}`.")
    return 0


def section_text(skill, tex):
    sm = corpus().skill_module(skill, "style_metrics")
    secs = sm.from_tex(tex) if os.path.exists(tex) else {}
    title = ""
    if os.path.exists(tex):
        m = re.search(r"\\title\{(.+?)\}\s*$", open(tex, encoding="utf-8", errors="replace").read(), re.S | re.M)
        title = " ".join(m.group(1).split()) if m else ""
    return title, secs


def run_json(cmd):
    r = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, timeout=300)
    return r


def cmd_eval_score(a):
    ctx = E.Ctx(a.workdir, a.run)
    case = load_case(ctx, a.case)
    ws = os.path.join(case_dir(ctx, a.case), "runs", a.eval_run)
    tex = os.path.join(ws, "draft", "main.tex")
    skill = os.path.join(ws, "skill")
    title, secs = section_text(skill, tex)
    res = {"case": a.case, "run": a.eval_run, "meta": E.jload(os.path.join(ws, "meta.json"), default={}), "graders": {}}
    g = res["graders"]
    g["A1"] = bool(title and secs.get("abstract") and secs.get("intro"))
    sc = os.path.join(skill, "scripts")
    nj = os.path.join(ws, "numbers.json")
    # only the materials count as a source (a writer cannot vouch for its own numbers); margins are accepted as
    # DERIVED from numbers that sit together in one materials entry
    run_json([os.path.join(sc, "check_numbers.py"), tex, "--sources", os.path.join(ws, "materials.json"),
              "--sections", "abstract,intro", "--derive", "--json", nj])
    nums = E.jload(nj, default={"numbers": []})["numbers"] if os.path.exists(tex) else []
    bad = [n for n in nums if n["status"] == "UNSUPPORTED"]
    g["A2"] = g["A1"] and not bad
    lj = os.path.join(ws, "lint.json")
    run_json([os.path.join(sc, "lint_paper.py"), tex, "--json", lj, "--venue", case.get("venue", "acl")])
    lint = E.jload(lj, default=[]) if os.path.exists(tex) else []
    codes = [i["code"] for i in lint]
    g["A3"] = g["A1"] and not any(c.startswith("E") or c in ("W306", "W307") for c in codes)
    n_abs = sum(1 for n in nums if n["section"] == "abstract")
    n_intro = sum(1 for n in nums if n["section"] == "intro")
    g["A4"] = g["A1"] and n_abs <= 5 and n_intro <= 14
    sj = os.path.join(ws, "style.json")
    run_json([os.path.join(sc, "style_metrics.py"), tex, "--domain", case.get("domain") or "", "--json", sj])
    style = E.jload(sj, default={}) if os.path.exists(tex) else {}
    warns = [f for s in style.get("sections", {}).values() for f in s.get("findings", []) if f["level"] == "WARN"]
    # memorization of the original (local only)
    draft = " ".join(" ".join(p) for p in secs.values())
    span, frac = 0, 0.0
    if case.get("source"):
        orig = corpus().paper_text(ctx, a.case, case["source"])
        mat_text = json.dumps(E.jload(os.path.join(ws, "materials.json")), ensure_ascii=False)
        grams = E.ngram_set(E.tokens(orig), MEMO_N) - E.ngram_set(E.tokens(mat_text), MEMO_N)
        span, frac = E.verbatim(draft, grams, MEMO_N)
    g["A5"] = span < 12 and frac < 0.03
    res.update({"title": title, "numbers": {"unsupported": [n["text"] for n in bad], "abstract": n_abs,
                                            "intro": n_intro},
                "lint": {c: codes.count(c) for c in sorted(set(codes))}, "style_warnings": [w["msg"] for w in warns],
                "memorization": {"longest_run": span, "overlap_8gram": round(frac, 4)},
                "det_passed": sum(bool(g[k]) for k in g), "det_total": len(g), "scored": E.now()})
    E.jsave(os.path.join(ws, "score.json"), res)
    hist_p = os.path.join(ctx.workdir, "evals", "history.json")
    hist = E.jload(hist_p, default={"scores": [], "blind": []})
    hist["scores"] = [h for h in hist["scores"] if not (h["case"] == a.case and h["run"] == a.eval_run)]
    entry = {k: res[k] for k in ("case", "run", "det_passed", "det_total")}
    entry.update({"skill": res["meta"].get("label"), "memorization": res["memorization"]})
    hist["scores"].append(entry)
    E.jsave(hist_p, hist)
    print(f"case {a.case} run {a.eval_run} (skill {res['meta'].get('label')}): {res['det_passed']}/{res['det_total']} "
          f"deterministic graders")
    for gid in sorted(g):
        text = next((x["text"] for x in case["graders"] if x["id"] == gid), "")
        print(f"  {'PASS' if g[gid] else 'FAIL'} {gid} {text}")
    if bad:
        print(f"  unsupported numbers: {', '.join(n['text'] for n in bad)}")
    print(f"  style warnings: {len(warns)}; memorization: longest run {span} words, {frac:.1%} 8-grams")
    print("Judge graders (J*) are answered in the blind comparison: evolve.py eval-blind.")
    return 0 if res["det_passed"] == res["det_total"] else 1


def anonymize(text, terms):
    for t in terms:
        text = re.sub(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", "[METHOD]", text, flags=re.I)
    return text


def cmd_eval_blind(a):
    ctx = E.Ctx(a.workdir, a.run)
    case = load_case(ctx, a.case)
    d = case_dir(ctx, a.case)
    hist_p = os.path.join(ctx.workdir, "evals", "history.json")
    if a.reveal:
        bd = os.path.join(d, "blind", a.reveal)
        key = E.jload(os.path.join(bd, "key.json"))
        j = E.jload(os.path.join(bd, "judgment.json"))
        errs = []
        for letter in key:
            c = j.get("candidates", {}).get(letter)
            if not c:
                errs.append(f"candidate {letter} not judged")
                continue
            for dim in DIMS:
                v = c.get("scores", {}).get(dim)
                if not isinstance(v, (int, float)) or not 1 <= v <= 5:
                    errs.append(f"{letter}.{dim} must be 1-5")
        if sorted(j.get("ranking", [])) != sorted(key):
            errs.append(f"ranking must list every candidate once: {sorted(key)}")
        if errs:
            for e in errs:
                print(f"[FAIL] judgment.json {e}")
            return 1
        rows = []
        for rank, letter in enumerate(j["ranking"], 1):
            c = j["candidates"][letter]
            mean = round(sum(c["scores"][x] for x in DIMS) / len(DIMS), 2)
            passed = sum(bool(v.get("pass")) for v in c.get("graders", {}).values())
            rows.append({"rank": rank, "letter": letter, "who": key[letter], "mean": mean, "judge_graders":
                         f"{passed}/{len(c.get('graders', {}))}", "difference": c.get("difference", "")})
        print(f"| rank | candidate | mean (D1-D8) | judge graders | most important difference |")
        print("| ---: | :--- | ---: | :--- | :--- |")
        for r in rows:
            print(f"| {r['rank']} | {r['who']} ({r['letter']}) | {r['mean']} | {r['judge_graders']} | {r['difference'][:90]} |")
        hist = E.jload(hist_p, default={"scores": [], "blind": []})
        hist["blind"] = [b for b in hist["blind"] if b.get("blind") != a.reveal]
        hist["blind"].append({"case": a.case, "blind": a.reveal, "results": rows, "t": E.now()})
        E.jsave(hist_p, hist)
        return 0
    runs = [r.strip() for r in (a.eval_runs or "").split(",") if r.strip()]
    if not runs:
        E.die("eval-blind needs --eval-runs RUN1[,RUN2...] (or --reveal BLIND_ID)")
    cands = []
    for r in runs:
        ws = os.path.join(d, "runs", r)
        title, secs = section_text(os.path.join(ws, "skill"), os.path.join(ws, "draft", "main.tex"))
        if not secs:
            E.die(f"run {r} has no abstract/introduction", 1)
        label = E.jload(os.path.join(ws, "meta.json"), default={}).get("label", r)
        cands.append((f"run {r} (skill {label})", title, secs))
    if not a.no_original and case.get("source"):
        sm = corpus().skill_module(ctx.skill, "style_metrics")
        secs = sm.extract(case["source"])
        if secs.get("abstract") and secs.get("intro"):
            cands.append(("original", "", secs))
        else:
            print("[warn] could not extract the original's abstract/introduction; comparing runs only")
    rng = random.Random(a.seed if a.seed is not None else os.urandom(8))
    rng.shuffle(cands)
    letters = [chr(ord("A") + i) for i in range(len(cands))]
    bid = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bd = os.path.join(d, "blind", bid)
    os.makedirs(bd)
    terms = case.get("terms", [])
    parts = [f"# Blind pack ({len(cands)} candidates)\n"]
    for letter, (_, title, secs) in zip(letters, cands):
        body = [f"## Candidate {letter}\n"]
        if title:
            body.append(f"**Title:** {anonymize(title, terms)}\n")
        body.append("### Abstract\n\n" + "\n\n".join(anonymize(p, terms) for p in secs.get("abstract", [])) + "\n")
        body.append("### Introduction\n\n" + "\n\n".join(anonymize(p, terms) for p in secs.get("intro", [])) + "\n")
        parts.append("\n".join(body))
    open(os.path.join(bd, "pack.md"), "w", encoding="utf-8").write("\n".join(parts))
    E.jsave(os.path.join(bd, "key.json"), {l: who for l, (who, _, _) in zip(letters, cands)})
    E.jsave(os.path.join(bd, "graders.json"), [g for g in case["graders"] if g["type"] == "judge"])
    task = E.fill("judge.md", {"PACK_PATH": os.path.join(bd, "pack.md"),
                               "RUBRIC_PATH": os.path.join(E.SKILL_HOME, "references", "eval_rubric.md"),
                               "GRADERS_PATH": os.path.join(bd, "graders.json"),
                               "OUTPUT_PATH": os.path.join(bd, "judgment.json")})
    open(os.path.join(bd, "JUDGE_TASK.md"), "w", encoding="utf-8").write(task)
    print(f"blind pack {bid}: {len(cands)} candidates in {bd}")
    print(f"Give a fresh Judge sub-agent ONLY {os.path.join(bd, 'JUDGE_TASK.md')} (never key.json); then run "
          f"`evolve.py eval-blind --case {a.case} --reveal {bid}`.")
    return 0


def cmd_eval_status(a):
    ctx = E.Ctx(a.workdir, a.run)
    root = os.path.join(ctx.workdir, "evals")
    hist = E.jload(os.path.join(root, "history.json"), default={"scores": [], "blind": []})
    cases = sorted(x for x in os.listdir(root) if os.path.isdir(os.path.join(root, x))) if os.path.isdir(root) else []
    if not cases:
        print("no eval cases (evolve.py make-case --paper <id>)")
        return 0
    for c in cases:
        case = E.jload(os.path.join(root, c, "case.json"), default={})
        print(f"case {c} [{case.get('domain')}]{' (biased: trained on it)' if case.get('biased') else ''}")
        for s in [s for s in hist["scores"] if s["case"] == c]:
            print(f"  run {s['run']} skill {s['skill']}: {s['det_passed']}/{s['det_total']} deterministic, "
                  f"memorization {s['memorization']['longest_run']} words")
        for b in [b for b in hist["blind"] if b["case"] == c]:
            print(f"  blind {b['blind']}: " + "; ".join(f"#{r['rank']} {r['who']} {r['mean']}" for r in b["results"]))
    return 0
