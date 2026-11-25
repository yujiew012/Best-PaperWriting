# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Corpus commands for evolve.py: per-domain style ranges and the exemplar bank.

  corpus-stats    style metrics of every cached exemplar paper -> references/style_corpus/<domain>.json
                  (numbers only: no text of any paper enters the skill)
  add-exemplars   verify proposed exemplar passages verbatim against the paper and add them to
                  references/exemplars/*.jsonl (short, attributed, limited per paper); --remove drops a paper's

Papers registered as held-out eval cases (evolve.py make-case) never contribute to either.
evolve.py imports this module lazily and calls bind(evolve_module) first.
"""
import glob
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess

E = None
SENT_MAX_WORDS, PARA_MAX_WORDS = 60, 160
MAX_SENT_PER_PAPER, MAX_PARA_PER_PAPER = 6, 3
PCTS = (10, 25, 50, 75, 90)


def bind(module):
    global E
    E = module


def skill_module(skill, name):
    path = os.path.join(skill, "scripts", f"{name}.py")
    if not os.path.exists(path):
        E.die(f"{path} not found: update the target skill")
    spec = importlib.util.spec_from_file_location(f"{name}_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def paper_sources(ctx):
    """paper_id -> source path, over every run in the workdir."""
    out = {}
    for rj in glob.glob(os.path.join(ctx.workdir, "runs", "*", "run.json")):
        for p in E.jload(rj, default={}).get("papers", []):
            if p.get("source") and os.path.exists(p["source"]):
                out.setdefault(p["paper_id"], p["source"])
    return out


def is_eval(led, pid):
    return led.get("papers", {}).get(pid, {}).get("role") == "eval"


def paper_text(ctx, pid, source):
    """Reading-order plain text of a paper (pdftotext without -layout), for verbatim checks."""
    if source and source.lower().endswith(".pdf") and shutil.which("pdftotext"):
        t = subprocess.run(["pdftotext", source, "-"], capture_output=True, text=True).stdout
    else:
        p = os.path.join(ctx.paper_cache(pid), "source.txt")
        t = open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""
    # drop figure captions and footnotes that pdftotext interleaves with the running text
    return skill_module(ctx.skill, "style_metrics").clean_pdf_text(t)


def norm(t):
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)
    t = t.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").replace("ﬁ", "fi").replace("ﬂ", "fl")
    return " ".join(re.findall(r"[A-Za-z0-9%'\"]+", t.lower()))


def percentiles(vals):
    vals = sorted(vals)
    out = {}
    for p in PCTS:
        k = (len(vals) - 1) * p / 100
        lo, hi = int(k), min(int(k) + 1, len(vals) - 1)
        out[f"p{p}"] = round(vals[lo] + (vals[hi] - vals[lo]) * (k - lo), 3)
    out["n"] = len(vals)
    return out


def cmd_corpus_stats(a):
    ctx = E.Ctx(a.workdir, a.run)
    skill = ctx.skill
    sm = skill_module(skill, "style_metrics")
    led = ctx.ledger()
    sources = paper_sources(ctx)
    by_domain = {}
    skipped = []
    for pid, info in led.get("papers", {}).items():
        dom = info.get("domain")
        if is_eval(led, pid):
            skipped.append(f"{pid}: held-out eval case")
            continue
        if not dom:
            skipped.append(f"{pid}: no domain")
            continue
        src = sources.get(pid)
        if not src:
            skipped.append(f"{pid}: source file not found")
            continue
        secs = {k: v for k, v in sm.extract(src).items() if v}
        if "abstract" not in secs or "intro" not in secs:
            skipped.append(f"{pid}: abstract/introduction not found in {os.path.basename(src)}")
            continue
        by_domain.setdefault(dom, {})[pid] = {sec: sm.metrics(paras) for sec, paras in secs.items()}
    if a.domain:
        by_domain = {k: v for k, v in by_domain.items() if k == a.domain}
    written = []
    for dom, papers in by_domain.items():
        path = os.path.join(skill, "references", "style_corpus", f"{dom}.json")
        prof = E.jload(path, default={})
        merged = dict(prof.get("papers", {}))
        merged.update(papers)
        out = {"name": dom, "description": f"Style ranges of the abstracts and introductions of {len(merged)} "
                                           f"exemplar paper(s) in {dom}, computed by evolve.py corpus-stats.",
               "source": "evolve.py corpus-stats (numbers only; no paper text)", "n_papers": len(merged),
               "domains": [dom], "papers": merged}
        for sec in ("abstract", "intro"):
            keys = sorted({k for m in merged.values() for k in m.get(sec, {})})
            out[sec] = {k: percentiles([m[sec][k] for m in merged.values() if k in m.get(sec, {})]) for k in keys}
        E.jsave(path, out)
        written.append(f"{dom}: {len(merged)} paper(s) -> {os.path.relpath(path, skill)}"
                       f"{'' if len(merged) >= sm.MIN_PAPERS else f' (used as a target from {sm.MIN_PAPERS} papers)'}")
    for s in skipped:
        print(f"[skip] {s}")
    for w in written:
        print(f"[ok] {w}")
    if not written:
        print("no domain profile written")
    return 0


def cmd_add_exemplars(a):
    ctx = E.Ctx(a.workdir, a.run)
    skill = ctx.skill
    led = ctx.ledger()
    ex_dir = os.path.join(skill, "references", "exemplars")
    files = {"sentence": os.path.join(ex_dir, "moves.jsonl"), "paragraph": os.path.join(ex_dir, "paragraphs.jsonl")}

    def read(kind):
        p = files[kind]
        return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []

    def write(kind, recs):
        with open(files[kind], "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if a.remove:
        n = 0
        for kind in files:
            recs = read(kind)
            keep = [r for r in recs if r.get("paper_id") != a.remove]
            n += len(recs) - len(keep)
            write(kind, keep)
        if a.remove in led.get("papers", {}):
            led["papers"][a.remove]["exemplars"] = 0
            E.jsave(ctx.ledger_path, led)
        print(f"removed {n} exemplar(s) of paper {a.remove}")
        return 0
    if not a.paper or not a.file:
        E.die("add-exemplars needs --paper and --file (or --remove PAPER_ID)")
    pid = a.paper
    if pid not in led.get("papers", {}):
        E.die(f"paper {pid} is not in the ledger (run the extractor and check-materials first)", 1)
    if is_eval(led, pid):
        E.die(f"paper {pid} is a held-out eval case; its text must not enter the skill", 1)
    info = led["papers"][pid]
    fns = json.load(open(os.path.join(ex_dir, "functions.json"), encoding="utf-8"))
    valid = {f"{s}.{f}" for s, d in fns.items() if not s.startswith("$") for f in d}
    proposed = E.jload(a.file)
    proposed = proposed.get("exemplars", proposed) if isinstance(proposed, dict) else proposed
    if not isinstance(proposed, list) or any(not isinstance(x, dict) for x in proposed):
        E.die(f"{a.file}: expected a JSON list of {{kind, section, function, text, why}} objects", 2)
    src = paper_sources(ctx).get(pid)
    text = norm(paper_text(ctx, pid, src))
    if not text:
        E.die(f"no text for paper {pid}: cannot verify the passages", 1)
    have = {k: [r for r in read(k) if r.get("paper_id") == pid] for k in files}
    added = {k: [] for k in files}
    for i, ex in enumerate(proposed, 1):
        kind = ex.get("kind", "sentence")
        fn = f"{ex.get('section')}.{ex.get('function')}"
        body = " ".join(str(ex.get("text", "")).split())
        nw = len(body.split())
        why = []
        if kind not in files:
            why.append(f"kind must be sentence or paragraph")
        if fn not in valid:
            why.append(f"unknown function {fn} (references/exemplars/functions.json)")
        if nw > (SENT_MAX_WORDS if kind == "sentence" else PARA_MAX_WORDS):
            why.append(f"{nw} words (limit {SENT_MAX_WORDS if kind == 'sentence' else PARA_MAX_WORDS})")
        if norm(body) not in text:
            why.append("not found verbatim in the paper (copy the exact words; no paraphrase, no ellipsis)")
        lim = MAX_SENT_PER_PAPER if kind == "sentence" else MAX_PARA_PER_PAPER
        if kind in files and len(have[kind]) + len(added[kind]) >= lim:
            why.append(f"paper already has {lim} {kind} exemplars")
        if not ex.get("why"):
            why.append("missing 'why' (what the passage does well, in your own words)")
        if why:
            print(f"[reject] #{i} {fn}: " + "; ".join(why))
            continue
        added[kind].append({
            "id": f"X-{pid}-{kind[0]}{len(have[kind]) + len(added[kind]) + 1}", "paper_id": pid,
            "section": ex["section"], "function": ex["function"], "text": body, "why": str(ex["why"]).strip(),
            "paper": info.get("title", pid)[:80], "venue": info.get("venue", ""), "year": info.get("year", ""),
            "domain": info.get("domain", ""), "paper_type": ex.get("paper_type", info.get("paper_type", "")),
            "motivation": ex.get("motivation", info.get("motivation", ""))})
    for kind, recs in added.items():
        if recs:
            write(kind, read(kind) + recs)
    n = sum(len(v) for v in added.values())
    print(f"added {n} exemplar(s) from {pid} ({len(added['sentence'])} sentence, {len(added['paragraph'])} paragraph)")
    if n:
        led["papers"][pid].setdefault("exemplars", 0)
        led["papers"][pid]["exemplars"] += n
        E.jsave(ctx.ledger_path, led)
    return 0


def check_corpus_file(rel, new_path, led):
    """check-edits support: style_corpus profiles hold numbers only; exemplar records come from known papers."""
    errs = []
    if rel.startswith("references/style_corpus/"):
        if os.path.basename(rel) == "general.json":
            return [f"{rel}: the general profile is maintained by a human"]
        try:
            prof = json.load(open(new_path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            return [f"{rel}: invalid JSON ({e})"]
        texty = [k for k, v in prof.items() if isinstance(v, str) and k not in ("name", "description", "source")]
        if texty:
            errs.append(f"{rel}: unexpected text fields {texty} (profiles hold numbers only)")
        for pid in prof.get("papers", {}):
            if is_eval(led, pid):
                errs.append(f"{rel}: contains held-out eval paper {pid}")
        return errs
    if rel.startswith("references/exemplars/") and rel.endswith(".jsonl"):
        for i, line in enumerate(open(new_path, encoding="utf-8"), 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                errs.append(f"{rel}:{i}: invalid JSON")
                continue
            pid = r.get("paper_id")
            if pid not in led.get("papers", {}):
                errs.append(f"{rel}:{i}: exemplar from unknown paper {pid} (use evolve.py add-exemplars)")
            elif is_eval(led, pid):
                errs.append(f"{rel}:{i}: exemplar from held-out eval paper {pid}")
        return errs
    return [f"{rel}: not a corpus file"]


def strip_paper_exemplars(skill_copy, pid):
    """Information barrier: a writer must not see exemplars quoted from the paper it is rewriting."""
    for name in ("moves.jsonl", "paragraphs.jsonl"):
        p = os.path.join(skill_copy, "references", "exemplars", name)
        if os.path.exists(p):
            keep = [l for l in open(p, encoding="utf-8") if l.strip() and json.loads(l).get("paper_id") != pid]
            with open(p, "w", encoding="utf-8") as f:
                f.writelines(keep)
