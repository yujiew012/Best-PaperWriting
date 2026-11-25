# /// script
# requires-python = ">=3.8"
# dependencies = ["pillow"]
# ///
"""Figure mode for evolve.py: Figure Extractor -> Illustrator -> Critic.

Everything that must not depend on model judgment lives here:
  * check-brief     validate the brief, reject layout/colour words and copied prose, crop the gold figure
  * task            workspaces for fig-extractor / illustrator / critic (the illustrator never sees the gold)
  * score           validate the critic's review, re-render the spec, measure brief coverage, keep/revert
  * propose-style   script-written, bounds-checked, evidence-gated changes to figure_styles/<domain>.json
  * request-feature log generator limitations for a human (the loop never edits scripts)
  * resolve-feature a human marks a request done or declined after changing (or not) the generator
  * check_styles    the part of check-edits that verifies style-profile diffs against the ledger

evolve.py imports this module lazily and calls bind(evolve_module) first.
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys

E = None                                    # the evolve module (set by bind)
FIG_DIMS = ["completeness", "structure_clarity", "flow_readability", "emphasis", "domain_conventions",
            "visual_quality"]
NOT_RULES = {"style_parameter": "use `propose-style` (style values are written by the script)",
             "generator_limitation": "use `request-feature` (generator changes need a human)",
             "brief_missing": "fix the brief instead (rerun the figure extractor)",
             "illustrator_error": "a one-off mistake is not a skill defect"}
STYLE_FILES = re.compile(r"^references/figure_styles/([\w-]+)\.json$")
# appearance words: a brief describes content only, so the illustrator's layout is its own
APPEARANCE = re.compile(
    r"(?<![\w-])(left|right|top|bottom|above|below|beneath|underneath|leftmost|rightmost|row|rows|column|"
    r"columns|horizontal(?:ly)?|vertical(?:ly)?|side[- ]by[- ]side|clockwise|corner|centre|center|"
    r"red(?!\s+team)|blue|green|orange|yellow|purple|grey|gray|black|white|pink|colou?r(?:ed|s)?|shaded|"
    r"dashed|dotted|solid line|bold|italic|font|arrows?|box|boxes|circle|circles|rectangle|icon|icons|"
    r"emoji|cylinder|cloud shape)(?![\w-])", re.I)
MAX_STYLE_PER_ITER, MAX_STYLE_PER_PAPER = 3, 6


def bind(module):
    global E
    E = module


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def brief_path(ctx, pid):
    return os.path.join(ctx.paper_cache(pid), "figure_brief.json")


def gold_path(ctx, pid):
    return os.path.join(ctx.paper_cache(pid), "figure_gold.png")


def brief_ok(ctx, pid):
    return E.jload(os.path.join(ctx.paper_cache(pid), "figure_brief.check.json"), default={}).get("ok")


def review_path(ctx, pid, k):
    return os.path.join(ctx.iter_dir(pid, k), "figure_review.json")


def brief_terms(ctx, pid):
    b = E.jload(brief_path(ctx, pid), default={})
    return {t.strip() for t in b.get("terms", []) if isinstance(t, str) and len(t.strip()) >= 3}


def style_module(skill):
    """figstyle.py of a given skill copy (live skill or an iteration snapshot)."""
    import importlib.util
    path = os.path.join(skill, "scripts", "figstyle.py")
    if not os.path.exists(path):
        E.die(f"{path} not found: figure mode needs a skill with figure style profiles")
    spec = importlib.util.spec_from_file_location(f"figstyle_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_tokens(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {"the", "a", "an", "of", "and", "to", "for"}


def venue_for(ctx, pid):
    run = ctx.need_run()
    if run.get("venue"):
        return run["venue"]
    venues = E.jload(os.path.join(run["skill_dir"], "references", "venues.json"), default={}).get("venues", {})
    meta = E.jload(os.path.join(ctx.paper_cache(pid), "materials.json"), default={})
    text = " ".join(str(x) for x in (meta.get("source_meta", {}).get("venue", ""),
                                     meta.get("domain", {}).get("venue", ""))).lower()
    for key in venues:
        if re.search(r"(?<![a-z])" + key + r"(?![a-z])", text):
            return key
    return "ieee"


# ---------------------------------------------------------------------------
# check-brief
# ---------------------------------------------------------------------------

def crop_gold(pdf, page, bbox, out):
    if not shutil.which("pdftoppm"):
        return "pdftoppm not found (install poppler-utils) -- cannot crop the gold figure"
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return "Pillow not installed -- cannot crop the gold figure"
    prefix = out[:-4] + "_page"
    r = subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "300", "-png", "-singlefile",
                        pdf, prefix], capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.exists(prefix + ".png"):
        return f"pdftoppm failed for page {page}: {r.stderr.strip()[:200]}"
    im = Image.open(prefix + ".png").convert("RGB")
    W, H = im.size
    x0, y0, x1, y1 = bbox
    crop = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    ink = ImageOps.invert(crop.convert("L")).point(lambda v: 255 if v > 40 else 0).getbbox()
    if not ink:
        return f"the crop of page {page} at {bbox} is blank -- fix source.bbox"
    crop.save(out)
    return None


def cmd_check_brief(a):
    ctx = E.Ctx(a.workdir, a.run)
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    cache = ctx.paper_cache(pid)
    b = E.jload(brief_path(ctx, pid))
    errs, warns = [], []
    if b.get("no_diagram"):
        E.jsave(os.path.join(cache, "figure_brief.check.json"), {"ok": False, "no_diagram": True, "t": E.now()})
        print(f"paper {pid} has no architecture diagram ({b.get('reason', '')}); drop it from this run")
        return 1
    errs += E.validate(b, E.jload(os.path.join(E.SCHEMAS, "figure_brief.schema.json")))
    if b.get("paper_id") not in (None, pid):
        warns.append(f"paper_id {b.get('paper_id')} corrected to {pid}")
        b["paper_id"] = pid
        E.jsave(brief_path(ctx, pid), b)
    ids = [e.get("id") for e in b.get("entities", [])]
    if len(ids) != len(set(ids)):
        errs.append("entity ids are not unique")
    for r in b.get("relations", []):
        for end in ("from", "to"):
            if r.get(end) not in ids:
                errs.append(f"relation {r.get('from')}->{r.get('to')}: unknown entity '{r.get(end)}'")
    for g in b.get("groups", []):
        for m in g.get("members", []):
            if m not in ids:
                errs.append(f"group '{g.get('name')}': unknown member '{m}'")
    steps = [r["step"] for r in b.get("relations", []) if "step" in r]
    if len(steps) != len(set(steps)):
        errs.append(f"duplicate step numbers {sorted(steps)}")
    # content only: no appearance words anywhere except entity names and the source block
    def scan(obj, path):
        if isinstance(obj, str):
            for m in APPEARANCE.finditer(obj):
                errs.append(f"{path}: appearance word '{m.group(0)}' -- describe what it is/does, not how it is "
                            f"drawn: '{obj[:70]}'")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if k not in ("source", "name", "terms", "paper_id", "figure_id", "id", "members", "from", "to"):
                    scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")
    scan(b, "$")
    n = ctx.policy()["verbatim_ngram"]
    grams = E.source_grams(ctx, pid, n)
    if grams:
        for s in E.strings_in({k: v for k, v in b.items() if k not in ("source", "terms")}):
            span, _ = E.verbatim(s, grams, n)
            if span > 2 * n:
                errs.append(f"copies a {span}-word span from the paper: '{s[:70]}...' -- paraphrase")
    if not b.get("terms"):
        warns.append("terms is empty: list the paper-specific names in the figure (guards rules against them)")
    src = b.get("source", {})
    bbox = src.get("bbox", [])
    if len(bbox) != 4 or not all(isinstance(v, (int, float)) for v in bbox):
        errs.append("source.bbox must be 4 numbers [x0, y0, x1, y1]")
    elif not (0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1):
        errs.append(f"source.bbox {bbox} must satisfy 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1")
    elif (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) < 0.02:
        errs.append(f"source.bbox {bbox} covers < 2% of the page -- is that the whole figure?")
    if not errs:
        if not p["source"].lower().endswith(".pdf"):
            errs.append("figure mode needs the paper as a PDF (the gold figure is cropped from it)")
        else:
            e = crop_gold(p["source"], int(src["page"]), bbox, gold_path(ctx, pid))
            if e:
                errs.append(e)
    ok = not errs
    E.jsave(os.path.join(cache, "figure_brief.check.json"), {"ok": ok, "errors": errs, "warnings": warns,
                                                            "t": E.now()})
    led = ctx.ledger()
    led.setdefault("papers", {}).setdefault(pid, {}).setdefault("domain", b.get("domain_id"))
    led["papers"][pid]["figure_domain"] = b.get("domain_id")
    E.jsave(ctx.ledger_path, led)
    p["domain"] = p.get("domain") or b.get("domain_id")
    p["brief"] = ok
    ctx.save_run()
    for e in errs:
        print(f"[FAIL] {e}")
    for w in warns:
        print(f"[warn] {w}")
    if ok:
        print(f"brief OK: {len(ids)} entities, {len(b['relations'])} relations, {len(b.get('groups', []))} groups, "
              f"{len(steps)} numbered steps")
        print(f"gold figure: {gold_path(ctx, pid)}")
        print("VIEW the gold crop now: it must contain the whole figure and no caption or body text; "
              "otherwise fix source.bbox and rerun.")
    else:
        print("brief REJECTED -- fix figure_brief.json and rerun")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# task
# ---------------------------------------------------------------------------

def cmd_task(a):
    ctx = E.Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    cache = ctx.paper_cache(pid)
    skill = run["skill_dir"]
    if a.role == "fig-extractor":
        ws = os.path.join(ctx.run_dir, "papers", pid, "fig_extractor")
        os.makedirs(ws, exist_ok=True)
        task = E.fill("fig_extractor.md", {
            "PAPER_PATH": p["source"], "OUTPUT_PATH": brief_path(ctx, pid), "PAPER_ID": pid,
            "SCHEMA_PATH": os.path.join(E.SCHEMAS, "figure_brief.schema.json"),
            "TAXONOMY_PATH": os.path.join(skill, "references", "domain_taxonomies.json")})
    else:
        k = a.iter
        if k is None or not 1 <= k <= run["iterations"]:
            E.die(f"--iter must be 1..{run['iterations']}")
        if not brief_ok(ctx, pid):
            E.die("brief not validated yet: run `evolve.py check-brief` first", 1)
        brief = E.jload(brief_path(ctx, pid))
        dom = brief["domain_id"]
        it = ctx.iter_dir(pid, k)
        if a.role == "illustrator":
            if k > 1:
                prev = ctx.iter_dir(pid, k - 1)
                if not E.jload(os.path.join(prev, "metrics.json"), default={}):
                    E.die(f"iteration {k - 1} has not been scored yet", 1)
                pending = E.jload(os.path.join(prev, "edits.check.json"), default=None)
                if E.skill_changed(os.path.join(prev, "skill_snapshot"), skill) and not (pending or {}).get("ok"):
                    E.die(f"the skill changed after iteration {k - 1} but `check-edits --iter {k - 1}` has not "
                          f"passed; run it (or revert) before the next figure", 1)
            E.snapshot(skill, os.path.join(it, "skill_snapshot"))
            ws = os.path.join(it, "illustrator")
            if os.path.exists(ws):
                shutil.rmtree(ws)
            os.makedirs(os.path.join(ws, "figure"))
            shown = {k2: v for k2, v in brief.items() if k2 not in ("source", "terms")}
            E.jsave(os.path.join(ws, "brief.json"), shown)
            E.snapshot(skill, os.path.join(ws, "skill"))
            for f in ("evolution_ledger.json", "EVOLUTION_LOG.md"):
                fp = os.path.join(ws, "skill", f)
                if os.path.exists(fp):
                    os.remove(fp)
            task = E.fill("illustrator.md", {
                "WORKSPACE": ws, "BRIEF_PATH": os.path.join(ws, "brief.json"),
                "SKILL_DIR": os.path.join(ws, "skill"), "OUT_DIR": os.path.join(ws, "figure"),
                "DOMAIN_ID": dom, "VENUE": venue_for(ctx, pid)})
        else:
            fig = os.path.join(it, "illustrator", "figure")
            if not os.path.exists(os.path.join(fig, "figure.png")):
                E.die(f"no figure.png in {fig}; run the illustrator first", 1)
            ws = os.path.join(it, "critic")
            os.makedirs(ws, exist_ok=True)
            snap = os.path.join(it, "skill_snapshot")
            task = E.fill("critic.md", {
                "GOLD_PATH": gold_path(ctx, pid), "FIGURE_DIR": fig,
                "BRIEF_PATH": os.path.join(it, "illustrator", "brief.json"), "SKILL_DIR": snap,
                "BOUNDS_PATH": os.path.join(snap, "references", "figure_styles", "_bounds.json"),
                "OUTPUT_PATH": review_path(ctx, pid, k),
                "SCHEMA_PATH": os.path.join(E.SCHEMAS, "figure_review.schema.json"),
                "RUBRIC_PATH": os.path.join(E.SKILL_HOME, "references", "figure_rubric.md"),
                "PAPER_ID": pid, "ITERATION": k, "DOMAIN_ID": dom})
    task_path = os.path.join(ws, f"{a.role.upper().replace('-', '_')}_TASK.md")
    with open(task_path, "w", encoding="utf-8") as f:
        f.write(task)
    run["events"].append({"t": E.now(), "event": f"task {a.role}", "paper": pid, "iter": a.iter})
    ctx.save_run()
    print(f"role: {a.role}\nworkspace: {ws}\ntask file: {task_path}")
    print("Give the sub-agent ONLY this task file (it lists every path it may read).")
    return 0


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------

def coverage(brief, spec):
    """Deterministic share of brief entities / relations / steps / groups that the spec draws."""
    blocks = spec.get("blocks", [])
    btoks = {b["id"]: norm_tokens(b.get("label", "") + " " + b.get("sub", "") + " " + b["id"]) for b in blocks}
    emap = {}
    for e in brief["entities"]:
        et = norm_tokens(e["name"])
        best, score = None, 0.0
        for bid, bt in btoks.items():
            s = len(et & bt) / max(len(et), 1)
            if s > score:
                best, score = bid, s
        if score >= 0.5:
            emap[e["id"]] = best
    # an entity may also be drawn as a group (e.g. a party that contains components)
    gtoks = [norm_tokens(g.get("label", "")) for g in spec.get("groups", [])]
    for e in brief["entities"]:
        if e["id"] not in emap:
            et = norm_tokens(e["name"])
            if any(len(et & gt) / max(len(et), 1) >= 0.5 for gt in gtoks):
                emap[e["id"]] = "group"
    pairs = {(x["from"], x["to"]) for x in spec.get("edges", [])}
    rel_hit = 0
    for r in brief["relations"]:
        a, b = emap.get(r["from"]), emap.get(r["to"])
        if a and b and (a == "group" or b == "group" or (a, b) in pairs or (b, a) in pairs):
            rel_hit += 1
    want_steps = sum(1 for r in brief["relations"] if "step" in r)
    got_steps = sum(1 for x in spec.get("edges", []) if "step" in x)
    groups = brief.get("groups", [])
    return {"entities": round(len(emap) / max(len(brief["entities"]), 1), 3),
            "missing_entities": [e["name"] for e in brief["entities"] if e["id"] not in emap],
            "relations": round(rel_hit / max(len(brief["relations"]), 1), 3),
            "steps": f"{got_steps}/{want_steps}",
            "groups": f"{len(spec.get('groups', []))}/{len(groups)}"}


def rerender(ctx, pid, k, dom):
    it = ctx.iter_dir(pid, k)
    spec = os.path.join(it, "illustrator", "figure", "spec.json")
    if not os.path.exists(spec):
        return None, ["spec.json missing -- the figure was not made with the skill's generator"]
    gen = os.path.join(it, "skill_snapshot", "scripts", "gen_architecture_diagram.py")
    out = os.path.join(it, "verify", "figure.pdf")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([sys.executable, gen, "--spec", spec, "--style", dom, "--venue", venue_for(ctx, pid),
                        "--out", out], capture_output=True, text=True, timeout=180)
    issues = [l[len("[issue] "):] for l in r.stderr.splitlines() if l.startswith("[issue] ")]
    if r.returncode == 2:
        issues.append("invalid spec: " + r.stderr.strip().splitlines()[-1][:160])
    return r.returncode, issues


def cmd_score(a):
    ctx = E.Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid, k = p["paper_id"], a.iter
    it = ctx.iter_dir(pid, k)
    review = E.jload(review_path(ctx, pid, k))
    errs = E.validate(review, E.jload(os.path.join(E.SCHEMAS, "figure_review.schema.json")))
    ids = [g.get("id") for g in review.get("gaps", [])]
    if len(ids) != len(set(ids)):
        errs.append("gap ids are not unique")
    fs = style_module(os.path.join(it, "skill_snapshot"))
    for g in review.get("gaps", []):
        if g.get("generality") == "domain" and not g.get("domain_id"):
            errs.append(f"gap {g.get('id')}: generality 'domain' needs domain_id")
        if g.get("root_cause") == "style_parameter":
            sc = g.get("style_change") or {}
            e = fs.check_value(sc.get("param", ""), sc.get("value")) if sc else "missing style_change"
            if e:
                errs.append(f"gap {g.get('id')}: style_change invalid ({e})")
        if g.get("root_cause") == "generator_limitation" and not g.get("feature_request"):
            errs.append(f"gap {g.get('id')}: generator_limitation needs feature_request")
    if errs:
        for e in errs:
            print(f"[FAIL] figure_review.json {e}")
        return 1
    pol = ctx.policy()
    brief = E.jload(brief_path(ctx, pid))
    dom = brief["domain_id"]
    rc, issues = rerender(ctx, pid, k, dom)
    spec = E.jload(os.path.join(it, "illustrator", "figure", "spec.json"), default={})
    cov = coverage(brief, spec) if spec else {"entities": 0.0, "relations": 0.0, "missing_entities": []}
    score = round(sum(review["scores"][d] for d in FIG_DIMS) / len(FIG_DIMS), 3)
    valid = rc is not None and rc != 2
    metrics = {"paper": pid, "iter": k, "mode": "figure", "score": score, "scores": review["scores"],
               "layout_issues": len(issues), "issues": issues[:20], "coverage": cov, "valid": valid,
               "gaps": {"total": len(review["gaps"]),
                        "by_root_cause": {rcause: sum(g["root_cause"] == rcause for g in review["gaps"])
                                          for rcause in sorted({g["root_cause"] for g in review["gaps"]})}}}
    prev = []
    for j in range(1, k):
        mj = E.jload(os.path.join(ctx.iter_dir(pid, j), "metrics.json"), default={})
        if mj.get("valid") and not mj.get("reverted"):
            prev.append(mj)
    decision = "keep"
    if not valid:
        decision = "invalid"
    elif p.get("role") == "holdout" and p.get("baseline") is not None:
        metrics["baseline"] = p["baseline"]
        decision = "regression" if score < p["baseline"] - pol["revert_tolerance"] else "no_regression"
    elif prev:
        best = max(prev, key=lambda m: m["score"])
        worse = (score < best["score"] - pol["revert_tolerance"] or
                 len(issues) > best.get("layout_issues", 0) or
                 cov.get("entities", 0) < best.get("coverage", {}).get("entities", 0) - 0.1)
        if worse:
            decision = f"revert_to_{best['iter']}"
        metrics["best_previous"] = {"iter": best["iter"], "score": best["score"]}
    metrics["decision"] = decision
    if E.jload(os.path.join(it, "metrics.json"), default={}).get("reverted"):
        metrics["reverted"] = True          # re-scoring never revives an iteration that was reverted
    E.jsave(os.path.join(it, "metrics.json"), metrics)
    led = ctx.ledger()
    pe = led.setdefault("papers", {}).setdefault(pid, {})
    if valid and score > pe.get("figure_best_score", 0):
        pe["figure_best_score"] = score
    pe["figure_history"] = [h for h in pe.get("figure_history", []) if (h.get("run"), h.get("iter")) != (run["run_id"], k)]
    pe["figure_history"].append({"run": run["run_id"], "iter": k, "score": score, "valid": valid,
                                                "role": p.get("role", "train")})
    E.jsave(ctx.ledger_path, led)
    print(f"paper {pid} figure iteration {k}: score {score:.2f}/5  "
          + "  ".join(f"{d}={review['scores'][d]}" for d in FIG_DIMS))
    print(f"re-render: {len(issues)} layout issue(s)" + "".join(f"\n  - {i}" for i in issues[:8]))
    print(f"coverage: entities {cov.get('entities', 0):.0%}, relations {cov.get('relations', 0):.0%}, "
          f"steps {cov.get('steps', '-')}, groups {cov.get('groups', '-')}"
          + (f"; missing: {', '.join(cov['missing_entities'])}" if cov.get("missing_entities") else ""))
    print("gaps by root cause: " + ", ".join(f"{r}={n}" for r, n in metrics["gaps"]["by_root_cause"].items()))
    if decision == "invalid":
        print("DECISION: invalid -- no renderable spec. Rerun the illustrator for this iteration.")
        return 1
    if decision == "regression":
        print(f"DECISION: regression on holdout ({score:.2f} vs {p['baseline']:.2f}); consider `revert --to-base`.")
        return 1
    if decision == "no_regression":
        print(f"DECISION: no regression on holdout ({score:.2f} vs {p['baseline']:.2f}).")
        return 0
    if decision.startswith("revert"):
        j = int(decision.split("_")[-1])
        print(f"DECISION: revert -- worse than iteration {j} (score, layout issues or coverage). Run "
              f"`evolve.py revert --paper {pid} --to {j}`, then try DIFFERENT changes from review {j}.")
        return 1
    print("DECISION: keep" + (" (last iteration: run finalize)" if k == run["iterations"] else
                              " -- triage gaps: propose (rules), propose-style, request-feature; then check-edits"))
    return 0


# ---------------------------------------------------------------------------
# propose-style / request-feature
# ---------------------------------------------------------------------------

def load_profile(skill, dom):
    path = os.path.join(skill, "references", "figure_styles", f"{dom}.json")
    if os.path.exists(path):
        return E.jload(path), path, False
    base = E.jload(os.path.join(skill, "references", "figure_styles", "default.json"))
    base["domain"], base["provisional"] = dom, {}
    base["notes"] = f"Created by the figure-evolution loop from default.json for domain {dom}."
    return base, path, True


def write_profile(path, prof):
    E.jsave(path, prof)


def style_status(rule, pol, led):
    """Domain styles: established at 2 papers. default.json: 2 papers from 2 domains (like universal rules)."""
    st = E.rule_status(rule, pol, led)
    if rule["scope"] == "style:default" and st == "established":
        domains = {led["papers"].get(e["paper"], {}).get("figure_domain") for e in rule["evidence"]} - {None}
        if len(domains) < pol["universal_rule_min_domains"]:
            return "provisional"
    return st


def cmd_propose_style(a):
    ctx = E.Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    if p.get("role") == "holdout":
        E.die("holdout papers only measure regressions", 1)
    review = E.jload(review_path(ctx, pid, a.iter))
    gap = next((g for g in review["gaps"] if g["id"] == a.gap), None)
    if not gap:
        E.die(f"gap {a.gap} not found in iteration {a.iter} figure review", 1)
    if gap["root_cause"] != "style_parameter":
        E.die(f"gap {a.gap} has root cause '{gap['root_cause']}', not style_parameter", 1)
    if gap["generality"] == "paper_specific":
        E.die(f"gap {a.gap} is paper-specific: a domain style must not follow one figure", 1)
    sc = gap.get("style_change") or {}
    param = a.param or sc.get("param")
    value = sc.get("value") if a.value is None else json.loads(a.value) if re.match(r"^[\d.\-]+$|^(true|false)$",
                                                                                     a.value) else a.value
    skill = run["skill_dir"]
    fs = style_module(skill)
    e = fs.check_value(param, value)
    if e:
        print(f"REFUSED: {e}")
        return 1
    brief = E.jload(brief_path(ctx, pid))
    dom = gap.get("domain_id") if gap["generality"] == "domain" and gap.get("domain_id") else brief["domain_id"]
    if gap["generality"] == "universal" and not a.default:
        print("note: universal style gaps change the domain profile of this paper; pass --default to change "
              "default.json instead (needs evidence from >= 2 domains to reach the base)")
    if a.default:
        dom = "default"
    scope = f"style:{dom}"
    led, pol = ctx.ledger(), ctx.policy()
    mine_iter = [r for r in led["rules"] if r["scope"].startswith("style:") and any(
        ev.get("run") == run["run_id"] and ev["paper"] == pid and ev["iter"] == a.iter for ev in r["evidence"])]
    mine_paper = [r for r in led["rules"] if r["scope"].startswith("style:") and any(
        ev["paper"] == pid for ev in r["evidence"])]
    if len(mine_iter) >= MAX_STYLE_PER_ITER:
        print(f"REFUSED: {MAX_STYLE_PER_ITER} style changes already proposed in this iteration")
        return 1
    if len(mine_paper) >= MAX_STYLE_PER_PAPER:
        print(f"REFUSED: paper {pid} already backs {MAX_STYLE_PER_PAPER} style changes; one figure must not "
              f"define a domain's look")
        return 1
    prof, ppath, created = load_profile(skill, dom)
    cur = fs.get(fs.effective(prof), param)
    ev = {"paper": pid, "run": run["run_id"], "iter": a.iter, "gap": a.gap}
    live = [r for r in led["rules"] if r["scope"] == scope and r.get("param") == param
            and r["status"] in ("provisional", "established")]
    dead = [r for r in led["rules"] if r["scope"] == scope and r.get("param") == param and r.get("value") == value
            and r["status"] == "rejected" and any(e2.get("run") == run["run_id"] for e2 in r["evidence"])]
    if dead:
        print(f"REFUSED: {dead[0]['id']} set {param}={value!r} earlier in this run and was reverted")
        return 1
    if live and live[0]["status"] == "provisional" and {e2["paper"] for e2 in live[0]["evidence"]} == {pid} \
            and live[0]["value"] != value:
        # the same paper refines its own provisional value (e.g. 9 -> 8.5): update in place
        rule = live[0]
        rule["history"].append({"t": E.now(), "event": f"value {rule['value']!r} -> {value!r} ({a.gap})",
                                "status": "provisional", "run": run["run_id"], "iter": a.iter})
        rule["value"] = value
        rule["evidence"].append(ev)
        rule["text"] = re.sub(r"set (\S+) = .*? \(was", f"set {param} = {value!r} (was", rule["text"], count=1)
        prof.setdefault("provisional", {})[param] = {"value": value, "rule": rule["id"]}
        rule.setdefault("applied", []).append({"run": run["run_id"], "paper": pid, "iter": a.iter})
        E.jsave(ctx.ledger_path, led)
        write_profile(ppath, prof)
        print(f"{rule['id']}: provisional value refined to {param}={value!r} in {os.path.relpath(ppath, skill)}")
        return 0
    if live:
        rule = live[0]
        if rule["value"] == value:
            if any(e2["paper"] == pid for e2 in rule["evidence"]):
                print(f"{rule['id']} already has evidence from {pid}; no change")
                return 0
            rule["evidence"].append(ev)
        else:
            rule.setdefault("counter", []).append(ev)
        old = rule["status"]
        rule["status"] = style_status(rule, pol, led)
        rule["history"].append({"t": E.now(), "event": f"{'evidence' if rule['value'] == value else 'counter'} "
                                f"from {pid}", "status": rule["status"]})
        if rule["status"] == "established" and old == "provisional":
            fs.set_path(prof["base"], param, rule["value"])
            prof.get("provisional", {}).pop(param, None)
            rule.setdefault("applied", []).append({"run": run["run_id"], "paper": pid, "iter": a.iter})
            msg = f"{rule['id']}: established -> {param}={rule['value']!r} moved into the base of {dom}.json"
        elif rule["status"] == "retired":
            if old == "provisional":
                prof.get("provisional", {}).pop(param, None)
            else:
                fs.set_path(prof["base"], param, rule.get("previous"))
            msg = (f"{rule['id']}: retired by counter-evidence ({param} restored to {rule.get('previous')!r}); "
                   f"propose again to try {value!r}")
        elif rule["value"] != value:
            print(f"HOLD: {param}={value!r} conflicts with {rule['id']} ({rule['value']!r}, "
                  f"{len({e2['paper'] for e2 in rule['evidence']})} paper(s)); counter-evidence recorded, "
                  f"no change.")
            E.jsave(ctx.ledger_path, led)
            return 0
        else:
            msg = f"{rule['id']}: evidence added, status {rule['status']}"
        E.jsave(ctx.ledger_path, led)
        write_profile(ppath, prof)
        print(msg)
        return 0
    if cur == value:
        print(f"{param} is already {value!r} in {dom}.json; nothing to do")
        return 0
    rid = "S-%04d" % (1 + max([int(r["id"][2:]) for r in led["rules"] if r["id"].startswith("S-")] or [0]))
    reason = (a.reason or gap.get("why_general") or gap["observation"]).strip()
    for r2 in E.guard_text(ctx, reason, [pp["paper_id"] for pp in run["papers"]], pol["verbatim_ngram"]):
        print(f"REFUSED (overfitting guard on --reason): {r2}")
        return 1
    rule = {"id": rid, "scope": scope, "param": param, "value": value, "previous": cur,
            "text": f"{dom} diagrams: set {param} = {value!r} (was {cur!r}). {reason}",
            "files": [os.path.relpath(ppath, skill)], "evidence": [ev], "counter": [], "status": "new",
            "root_cause": "style_parameter", "history": []}
    led["rules"].append(rule)
    rule["status"] = style_status(rule, pol, led)
    rule["history"].append({"t": E.now(), "event": "created", "status": rule["status"], "run": run["run_id"],
                            "iter": a.iter})
    rule["applied"] = [{"run": run["run_id"], "paper": pid, "iter": a.iter}]
    prof.setdefault("provisional", {})[param] = {"value": value, "rule": rid}
    E.jsave(ctx.ledger_path, led)
    write_profile(ppath, prof)
    print(f"{rid} [{scope}] provisional: {param} {cur!r} -> {value!r} written to "
          f"{os.path.relpath(ppath, skill)}{' (new profile)' if created else ''}")
    print("It becomes the domain's base value only when a figure from a second paper asks for the same value.")
    return 0


def cmd_request_feature(a):
    ctx = E.Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    review = E.jload(review_path(ctx, pid, a.iter))
    gap = next((g for g in review["gaps"] if g["id"] == a.gap), None)
    if not gap:
        E.die(f"gap {a.gap} not found", 1)
    if gap["root_cause"] != "generator_limitation":
        E.die(f"gap {a.gap} has root cause '{gap['root_cause']}', not generator_limitation", 1)
    text = (a.text or gap.get("feature_request", "")).strip()
    if len(text.split()) < 5:
        E.die("feature request is too short: say what the generator should be able to draw", 1)
    reasons = E.guard_text(ctx, text, [pp["paper_id"] for pp in run["papers"]], ctx.policy()["verbatim_ngram"])
    if reasons:
        print("REFUSED (overfitting guard):\n  - " + "\n  - ".join(reasons))
        return 1
    led = ctx.ledger()
    frs = led.setdefault("feature_requests", [])
    ev = {"paper": pid, "run": run["run_id"], "iter": a.iter, "gap": a.gap}
    same = [f for f in frs if f["status"] == "open" and E.jaccard(f["text"], text) >= 0.4]
    if same:
        fr = same[0]
        if all(e2["paper"] != pid for e2 in fr["evidence"]):
            fr["evidence"].append(ev)
        print(f"{fr['id']} (existing): now requested by {len({e2['paper'] for e2 in fr['evidence']})} paper(s)")
    else:
        fid = "F-%04d" % (len(frs) + 1)
        frs.append({"id": fid, "text": text, "aspect": gap["aspect"], "status": "open", "evidence": [ev],
                    "created": E.now()})
        print(f"{fid} recorded for a human: {text}")
    E.jsave(ctx.ledger_path, led)
    print("The loop never edits scripts; the finalize report lists open requests ranked by support.")
    return 0


def cmd_resolve_feature(a):
    """A human implemented (or declined) a feature request: record it so the report stops listing it."""
    ctx = E.Ctx(a.workdir, a.run)
    led = ctx.ledger()
    fr = next((f for f in led.get("feature_requests", []) if f["id"] == a.id), None)
    if not fr:
        E.die(f"unknown feature request {a.id}", 1)
    if len(a.note.split()) < 3:
        E.die("--note must say what was done (e.g. the option or check that now exists)", 2)
    fr["status"] = "declined" if a.declined else "done"
    fr.setdefault("history", []).append({"t": E.now(), "event": fr["status"], "note": a.note.strip()})
    E.jsave(ctx.ledger_path, led)
    print(f"{fr['id']}: {fr['status']} -- {a.note.strip()}")
    return 0


# ---------------------------------------------------------------------------
# check-edits support
# ---------------------------------------------------------------------------

def check_style_file(rel, old_path, new_path, rules, skill):
    """Errors for one changed figure_styles/<d>.json: every base/provisional difference must be a ledger rule."""
    errs = []
    m = STYLE_FILES.match(rel)
    if not m or m.group(1).startswith("_"):
        return [f"{rel}: only references/figure_styles/<domain>.json may change (_bounds.json needs a human)"]
    dom = m.group(1)
    fs = style_module(skill)
    try:
        new = json.load(open(new_path, encoding="utf-8")) if new_path else None
    except json.JSONDecodeError as e:
        return [f"{rel}: invalid JSON ({e})"]
    if new is None:
        return [f"{rel}: style profiles must not be deleted by the loop"]
    old = json.load(open(old_path, encoding="utf-8")) if old_path else \
        json.load(open(os.path.join(skill, "references", "figure_styles", "default.json"), encoding="utf-8"))
    errs += [f"{rel}: {e}" for e in fs.validate(new)]
    for key in set(old) | set(new):
        if key not in ("base", "provisional", "notes", "domain") and old.get(key) != new.get(key):
            errs.append(f"{rel}: key '{key}' changed (only base/provisional values may evolve)")
    b = fs.bounds()
    for param in b:
        try:
            ov, nv = fs.get(old["base"], param), fs.get(new["base"], param)
        except (KeyError, TypeError):
            continue
        if ov != nv:
            ok = any(r["scope"] == f"style:{dom}" and r.get("param") == param and
                     ((r["status"] == "established" and r.get("value") == nv) or
                      (r["status"] == "retired" and r.get("previous") == nv)) for r in rules.values())
            if not ok:
                errs.append(f"{rel}: base {param} {ov!r} -> {nv!r} is not backed by an established style rule "
                            f"(base values change only through `propose-style`)")
    for param, entry in new.get("provisional", {}).items():
        rid = entry.get("rule") if isinstance(entry, dict) else None
        r = rules.get(rid)
        if not r or r["scope"] != f"style:{dom}" or r.get("param") != param or r.get("value") != entry.get("value"):
            errs.append(f"{rel}: provisional {param} is not backed by a matching ledger rule ({rid})")
        elif r["status"] != "provisional":
            errs.append(f"{rel}: provisional {param} belongs to {rid}, which is '{r['status']}'")
    return errs


def report_lines(ctx, rows):
    run = ctx.need_run()
    led = ctx.ledger()
    lines = ["", "## Figure scores", "",
             "| paper | role | iter | score | layout issues | entity cov. | relation cov. | decision |",
             "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |"]
    for p, m in rows:
        c = m.get("coverage", {})
        lines.append(f"| {p['paper_id']} | {p.get('role', 'train')} | {m['iter']} | {m['score']:.2f} | "
                     f"{m.get('layout_issues', '-')} | {c.get('entities', 0):.0%} | {c.get('relations', 0):.0%} | "
                     f"{m['decision']}{' (reverted)' if m.get('reverted') else ''} |")
    style = [r for r in led["rules"] if r["scope"].startswith("style:")
             and any(e.get("run") == run["run_id"] for e in r["evidence"] + r.get("counter", []))]
    lines += ["", "## Style-profile changes in this run", "", "| id | profile | param | value | status | support |",
              "| :--- | :--- | :--- | :--- | :--- | ---: |"]
    lines += [f"| {r['id']} | {r['scope'][6:]} | `{r['param']}` | {r.get('previous')!r} -> {r['value']!r} | "
              f"{r['status']} | {len({e['paper'] for e in r['evidence']})} |" for r in style] or ["| none | | | | | |"]
    frs = sorted([f for f in led.get("feature_requests", []) if f["status"] == "open"],
                 key=lambda f: -len({e["paper"] for e in f["evidence"]}))
    lines += ["", "## Generator feature requests (open, for a human)", ""]
    lines += [f"- **{f['id']}** ({len({e['paper'] for e in f['evidence']})} paper(s), {f['aspect']}): {f['text']}"
              for f in frs] or ["- none"]
    closed = [f for f in led.get("feature_requests", []) if f["status"] != "open"]
    if closed:
        lines += ["", "Closed by a human: " + ", ".join(
            f"{f['id']} ({f['status']})" for f in closed)]
    return lines
