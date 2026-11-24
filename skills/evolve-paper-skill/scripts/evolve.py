#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Deterministic orchestration for the Extractor -> Writer -> Reviewer self-evolution loop.

The main agent runs the three roles (as sub-agents when available); this script
does everything that must not depend on model judgment: workspaces with
information barriers, schema validation, verbatim-leakage checks, scoring,
keep/revert decisions, the rule-evidence ledger, and anti-overfitting guards on
every skill edit.

  init             register papers + iteration count, create a run
  task             build a role's workspace and task file (extractor | writer | reviewer)
  check-materials  validate materials.json (schema, no copied prose, identifiers listed)
  score            validate review.json, lint + leakage-check the draft, keep/revert decision
  propose          record a generalized rule in the ledger; says whether/where it may be applied
  check-edits      verify the skill diff of this iteration against the ledger and guards
  revert           restore the skill to an iteration's snapshot and reject its rules
  holdout          add an earlier paper (cached materials) to check for regressions
  status           scores, decisions and ledger summary
  finalize         promotion pass, report.md, EVOLUTION_LOG entry

Figure mode (`init --mode figure`, implemented in figure_mode.py) evolves the diagram rules,
the per-domain figure style profiles and a feature-request log for the generator:
  check-brief      validate the figure brief (no layout/colour words), crop the gold figure
  propose-style    bounds-checked, evidence-gated change to references/figure_styles/<domain>.json
  request-feature  record a generator limitation for a human (scripts are never edited by the loop)

Typical loop (see SKILL.md): init -> task extractor -> check-materials ->
[task writer -> task reviewer -> score -> propose* -> edit -> check-edits] x N -> finalize.
Figure loop: init --mode figure -> task fig-extractor -> check-brief ->
[task illustrator -> task critic -> score -> propose* / propose-style* / request-feature* -> check-edits] x N
-> finalize.
Exit codes: 0 ok, 1 check failed / action refused, 2 usage error.
"""
import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_HOME = os.path.dirname(HERE)
AGENTS = os.path.join(SKILL_HOME, "assets", "agents")
SCHEMAS = os.path.join(SKILL_HOME, "assets", "schemas")
SCORE_DIMS = ["structure", "introduction", "related_work", "method", "evaluation",
              "figures_tables", "language", "domain_conventions"]
UNIVERSAL_FILES = re.compile(r"^(SKILL\.md|references/writing/[\w-]+\.md|references/(figures_and_captions|"
                             r"layout_and_typesetting|bibliography|revision_and_submission|"
                             r"mechanism_sentence_bank)\.md)$")
DOMAIN_FILES = re.compile(r"^references/domains/([\w-]+)\.md$")
STYLE_FILES = re.compile(r"^references/figure_styles/([\w-]+)\.json$")
IGNORED = {"evolution_ledger.json", "EVOLUTION_LOG.md"}
MARKER = re.compile(r"<!--\s*(R-\d{4})\s*-->")


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------

def fig():
    """The figure-mode module, bound to this one (imported lazily)."""
    sys.path.insert(0, HERE)
    import figure_mode
    figure_mode.bind(sys.modules[__name__])
    return figure_mode


def is_figure(ctx):
    return (ctx.run or {}).get("mode") == "figure"


def die(msg, code=2):
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(code)


def now():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def jload(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        die(f"missing file: {path}")
    with open(path, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            die(f"{path}: invalid JSON ({e})", 1)


def jsave(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def ngram_set(toks, n):
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def verbatim(text, source_grams, n):
    """(longest verbatim span in words, fraction of n-grams found in source)."""
    t = tokens(text)
    if len(t) < n or not source_grams:
        return 0, 0.0
    hits = [tuple(t[i:i + n]) in source_grams for i in range(len(t) - n + 1)]
    best = run = 0
    for h in hits:
        run = run + 1 if h else 0
        best = max(best, run)
    return (best + n - 1) if best else 0, sum(hits) / len(hits)


def validate(obj, schema, path="$"):
    """Minimal JSON-Schema subset: type, required, properties, items, enum, minimum, maximum."""
    errs = []
    types = {"object": dict, "array": list, "string": str, "number": (int, float), "integer": int,
             "boolean": bool}
    t = schema.get("type")
    if t and not isinstance(obj, types[t]) or (t in ("number", "integer") and isinstance(obj, bool)):
        return [f"{path}: expected {t}"]
    if "enum" in schema and obj not in schema["enum"]:
        errs.append(f"{path}: {obj!r} not in {schema['enum']}")
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        if "minimum" in schema and obj < schema["minimum"]:
            errs.append(f"{path}: {obj} < {schema['minimum']}")
        if "maximum" in schema and obj > schema["maximum"]:
            errs.append(f"{path}: {obj} > {schema['maximum']}")
    if isinstance(obj, str) and schema.get("minLength") and len(obj.strip()) < schema["minLength"]:
        errs.append(f"{path}: empty or too short")
    if isinstance(obj, dict):
        for k in schema.get("required", []):
            if k not in obj:
                errs.append(f"{path}: missing '{k}'")
        for k, sub in schema.get("properties", {}).items():
            if k in obj:
                errs += validate(obj[k], sub, f"{path}.{k}")
    if isinstance(obj, list):
        if schema.get("minItems") and len(obj) < schema["minItems"]:
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        if "items" in schema:
            for i, it in enumerate(obj):
                errs += validate(it, schema["items"], f"{path}[{i}]")
    return errs


def strings_in(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings_in(v)


# ---------------------------------------------------------------------------
# run / paper / ledger state
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, workdir, run_id=None):
        self.workdir = os.path.abspath(workdir)
        self.run_id = run_id or self.latest_run()
        self.run_dir = os.path.join(self.workdir, "runs", self.run_id) if self.run_id else None
        self.run = jload(os.path.join(self.run_dir, "run.json")) if self.run_dir else None

    def latest_run(self):
        d = os.path.join(self.workdir, "runs")
        runs = sorted(os.listdir(d)) if os.path.isdir(d) else []
        return runs[-1] if runs else None

    def need_run(self):
        if not self.run:
            die("no run found; start with `evolve.py init`")
        return self.run

    def save_run(self):
        jsave(os.path.join(self.run_dir, "run.json"), self.run)

    @property
    def skill(self):
        return self.need_run()["skill_dir"]

    @property
    def ledger_path(self):
        return os.path.join(self.skill, "evolution_ledger.json")

    def ledger(self):
        return jload(self.ledger_path, default={"version": 1, "policy": {}, "papers": {}, "rules": [], "runs": []})

    def policy(self):
        p = {"domain_rule_promotion_papers": 2, "universal_rule_min_papers": 2, "universal_rule_min_domains": 2,
             "max_added_lines_per_iteration": 40, "max_provisional_rules_per_paper": 8, "verbatim_ngram": 8,
             "revert_tolerance": 0.25}
        p.update(self.ledger().get("policy", {}))
        return p

    def paper_cache(self, pid):
        return os.path.join(self.workdir, "papers", pid)

    def paper(self, pid):
        for p in self.need_run()["papers"]:
            if p["paper_id"] == pid or (len(pid) >= 4 and p["paper_id"].startswith(pid)):
                return p
        die(f"paper '{pid}' is not part of run {self.run_id}; papers: {[p['paper_id'] for p in self.run['papers']]}")

    def iter_dir(self, pid, k):
        return os.path.join(self.run_dir, "papers", pid, f"iter_{k}")


def source_grams(ctx, pid, n):
    p = os.path.join(ctx.paper_cache(pid), "source.txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as f:
        return ngram_set(tokens(f.read()), n)


def blocked_terms(ctx, pid):
    """Paper-specific identifiers and result numbers that must never enter the skill."""
    m = jload(os.path.join(ctx.paper_cache(pid), "materials.json"), default={})
    terms = set()
    t = m.get("terms", {})
    for key in ("method_names", "component_names", "other_identifiers"):
        terms.update(x.strip() for x in t.get(key, []) if isinstance(x, str) and len(x.strip()) >= 3)
    if m.get("idea", {}).get("method_name"):
        terms.add(m["idea"]["method_name"].strip())
    brief = jload(os.path.join(ctx.paper_cache(pid), "figure_brief.json"), default={})
    terms.update(x.strip() for x in brief.get("terms", []) if isinstance(x, str) and len(x.strip()) >= 3)
    for c in m.get("idea", {}).get("components", []):
        if c.get("name") and len(c["name"].strip()) >= 3:
            terms.add(c["name"].strip())
    numbers = set()
    for r in m.get("experiments", {}).get("results", []):
        for row in r.get("rows", []):
            for cell in row:
                for num in re.findall(r"\d+\.\d+", str(cell)):
                    numbers.add(num)
    return terms, numbers


def guard_text(ctx, text, pids, n):
    """Return reasons why `text` is paper-specific (blocked terms, numbers, verbatim spans)."""
    reasons = []
    for pid in pids:
        terms, numbers = blocked_terms(ctx, pid)
        for term in terms:
            if re.search(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", text, re.I if " " in term else 0):
                reasons.append(f"contains paper-specific identifier '{term}' (paper {pid})")
        for num in numbers:
            if re.search(r"(?<![\d.])" + re.escape(num) + r"(?![\d])", text):
                reasons.append(f"contains result value {num} from paper {pid}")
        grams = source_grams(ctx, pid, n)
        if grams:
            span, _ = verbatim(text, grams, n)
            if span:
                reasons.append(f"copies a {span}-word span verbatim from paper {pid}")
    return reasons


def skill_files(root):
    out = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        for f in files:
            if f.endswith((".pyc", ".tmp")):
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/")
            out[rel] = os.path.join(dirpath, f)
    return out


def skill_changed(snap, skill):
    a, b = skill_files(snap), skill_files(skill)
    for rel in set(a) | set(b):
        if rel in IGNORED:
            continue
        if rel not in a or rel not in b or open(a[rel], "rb").read() != open(b[rel], "rb").read():
            return True
    return False


def snapshot(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))


def fill(template, values):
    with open(os.path.join(AGENTS, template), encoding="utf-8") as f:
        text = f.read()
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        die(f"unfilled placeholders in {template}: {sorted(set(left))}")
    return text


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_init(a):
    skill = os.path.abspath(a.skill)
    if not os.path.isfile(os.path.join(skill, "SKILL.md")):
        die(f"not a skill folder (no SKILL.md): {skill}")
    if not 1 <= a.iterations <= 20:
        die("--iterations must be between 1 and 20")
    ctx = Ctx(a.workdir)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(ctx.workdir, "runs", run_id)
    os.makedirs(run_dir)
    papers = []
    for spec in a.paper:
        path = os.path.abspath(spec)
        if not os.path.isfile(path):
            die(f"paper not found: {spec}")
        pid = sha256(path)[:10]
        cache = ctx.paper_cache(pid)
        os.makedirs(cache, exist_ok=True)
        text_ok = os.path.exists(os.path.join(cache, "source.txt"))
        if not text_ok:
            if path.lower().endswith((".md", ".txt", ".tex", ".mmd")):
                shutil.copyfile(path, os.path.join(cache, "source.txt"))
                text_ok = True
            elif path.lower().endswith(".pdf") and shutil.which("pdftotext"):
                subprocess.run(["pdftotext", "-layout", path, os.path.join(cache, "source.txt")],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                text_ok = os.path.exists(os.path.join(cache, "source.txt"))
        papers.append({"paper_id": pid, "source": path, "text": text_ok,
                       "materials": os.path.exists(os.path.join(cache, "materials.json")), "role": "train"})
    base = os.path.join(run_dir, "base_snapshot")
    snapshot(skill, base)
    git = None
    try:
        git = subprocess.run(["git", "-C", skill, "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=10).stdout.strip() or None
        dirty = subprocess.run(["git", "-C", skill, "status", "--porcelain", "--", "."], capture_output=True,
                               text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        dirty = ""
    run = {"run_id": run_id, "created": now(), "skill_dir": skill, "iterations": a.iterations,
           "mode": a.mode, "venue": a.venue, "git_base": git, "papers": papers, "events": []}
    if a.mode == "figure":
        for p in papers:
            p["brief"] = bool(jload(os.path.join(ctx.paper_cache(p["paper_id"]), "figure_brief.check.json"),
                                    default={}).get("ok"))
    ctx.run_id, ctx.run_dir, ctx.run = run_id, run_dir, run
    ctx.save_run()
    print(f"run: {run_id} ({a.mode} mode)\nskill: {skill}\niterations per paper: {a.iterations}")
    if a.mode == "figure":
        for p in papers:
            print(f"paper {p['paper_id']}: {os.path.basename(p['source'])} "
                  f"[{'cached figure brief' if p['brief'] else 'needs figure extraction'}]")
            if not p["source"].lower().endswith(".pdf"):
                print("  [warn] figure mode needs a PDF to crop the gold figure")
        print(f"sub-agent runs needed: {sum((0 if p['brief'] else 1) + 2 * a.iterations for p in papers)}")
        if dirty:
            print("[warn] the skill has uncommitted changes; commit or stash them so the final diff is clean")
        print(f"\nnext: evolve.py task --role fig-extractor --paper {papers[0]['paper_id']}")
        return 0
    for p in papers:
        flags = [("text" if p["text"] else "NO TEXT (extractor must write source.txt)"),
                 ("cached materials" if p["materials"] else "needs extraction")]
        print(f"paper {p['paper_id']}: {os.path.basename(p['source'])} [{', '.join(flags)}]")
    n_agents = sum((0 if p["materials"] else 1) + 2 * a.iterations for p in papers)
    print(f"sub-agent runs needed: {n_agents}")
    if dirty:
        print("[warn] the skill has uncommitted changes; commit or stash them so the final diff is clean")
    print(f"\nnext: evolve.py task --role extractor --paper {papers[0]['paper_id']}")
    return 0


def cmd_task(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    figure_roles = ("fig-extractor", "illustrator", "critic")
    if is_figure(ctx) != (a.role in figure_roles):
        die(f"role '{a.role}' does not belong to a {run.get('mode', 'writing')}-mode run "
            f"(writing: extractor/writer/reviewer; figure: {'/'.join(figure_roles)})")
    if is_figure(ctx):
        return fig().cmd_task(a)
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    cache = ctx.paper_cache(pid)
    schema_dir = SCHEMAS
    if a.role == "extractor":
        ws = os.path.join(ctx.run_dir, "papers", pid, "extractor")
        os.makedirs(ws, exist_ok=True)
        task = fill("extractor.md", {
            "PAPER_PATH": p["source"], "OUTPUT_PATH": os.path.join(cache, "materials.json"),
            "SOURCE_TEXT_PATH": os.path.join(cache, "source.txt"),
            "WRITE_SOURCE_TEXT": "no (already extracted)" if p["text"] else "YES",
            "SCHEMA_PATH": os.path.join(schema_dir, "materials.schema.json"),
            "TAXONOMY_PATH": os.path.join(run["skill_dir"], "references", "domain_taxonomies.json")})
    else:
        k = a.iter
        if k is None or not 1 <= k <= run["iterations"]:
            die(f"--iter must be 1..{run['iterations']}")
        if not jload(os.path.join(cache, "materials.check.json"), default={}).get("ok"):
            die("materials not validated yet: run `evolve.py check-materials` first", 1)
        it = ctx.iter_dir(pid, k)
        if a.role == "writer":
            if k > 1:
                prev = jload(os.path.join(ctx.iter_dir(pid, k - 1), "metrics.json"), default={})
                if not prev:
                    die(f"iteration {k - 1} has not been scored yet", 1)
                pending = jload(os.path.join(ctx.iter_dir(pid, k - 1), "edits.check.json"), default=None)
                changed = skill_changed(os.path.join(ctx.iter_dir(pid, k - 1), "skill_snapshot"), run["skill_dir"])
                if changed and (pending is None or not pending.get("ok")):
                    die(f"the skill changed after iteration {k - 1} but `check-edits --iter {k - 1}` has not "
                        f"passed; run it (or revert) before the next draft", 1)
            snap = os.path.join(it, "skill_snapshot")
            snapshot(run["skill_dir"], snap)
            ws = os.path.join(it, "writer")
            if os.path.exists(ws):
                shutil.rmtree(ws)
            os.makedirs(os.path.join(ws, "draft"))
            mat = jload(os.path.join(cache, "materials.json"))
            mat.pop("source_meta", None)          # title/authors/venue details never reach the writer
            mat.pop("terms", None)                # guard list may contain the title or repo name
            jsave(os.path.join(ws, "materials.json"), mat)
            snapshot(run["skill_dir"], os.path.join(ws, "skill"))
            os.remove(os.path.join(ws, "skill", "evolution_ledger.json")) if os.path.exists(
                os.path.join(ws, "skill", "evolution_ledger.json")) else None
            task = fill("writer.md", {"WORKSPACE": ws, "MATERIALS_PATH": os.path.join(ws, "materials.json"),
                                      "SKILL_DIR": os.path.join(ws, "skill"),
                                      "DRAFT_DIR": os.path.join(ws, "draft"),
                                      "DOMAIN_ID": mat.get("domain", {}).get("id", "unknown"),
                                      "VENUE_TYPE": mat.get("domain", {}).get("venue_type", "conference")})
        else:
            draft = os.path.join(it, "writer", "draft")
            if not os.path.isdir(draft) or not os.listdir(draft):
                die(f"no draft in {draft}; run the writer first", 1)
            ws = os.path.join(it, "reviewer")
            os.makedirs(ws, exist_ok=True)
            mat = jload(os.path.join(cache, "materials.json"))
            task = fill("reviewer.md", {
                "PAPER_PATH": p["source"], "SOURCE_TEXT_PATH": os.path.join(cache, "source.txt"),
                "DRAFT_DIR": draft, "MATERIALS_PATH": os.path.join(cache, "materials.json"),
                "SKILL_DIR": os.path.join(it, "skill_snapshot"), "OUTPUT_PATH": os.path.join(it, "review.json"),
                "SCHEMA_PATH": os.path.join(schema_dir, "review.schema.json"),
                "RUBRIC_PATH": os.path.join(SKILL_HOME, "references", "review_rubric.md"),
                "PAPER_ID": pid, "ITERATION": k,
                "DOMAIN_ID": mat.get("domain", {}).get("id", "unknown")})
    task_path = os.path.join(ws, f"{a.role.upper()}_TASK.md")
    with open(task_path, "w", encoding="utf-8") as f:
        f.write(task)
    run["events"].append({"t": now(), "event": f"task {a.role}", "paper": pid, "iter": a.iter})
    ctx.save_run()
    print(f"role: {a.role}\nworkspace: {ws}\ntask file: {task_path}")
    print("Give the sub-agent ONLY this task file (it lists every path it may read).")
    return 0


def cmd_check_materials(a):
    ctx = Ctx(a.workdir, a.run)
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    cache = ctx.paper_cache(pid)
    mat = jload(os.path.join(cache, "materials.json"))
    errs = validate(mat, jload(os.path.join(SCHEMAS, "materials.schema.json")))
    warns = []
    if mat.get("paper_id") not in (None, pid):
        warns.append(f"paper_id in materials ({mat.get('paper_id')}) differs from {pid}; corrected")
        mat["paper_id"] = pid
        jsave(os.path.join(cache, "materials.json"), mat)
    if not os.path.exists(os.path.join(cache, "source.txt")):
        errs.append("source.txt missing: the extractor must save the paper's plain text (needed for leakage checks)")
    else:
        p["text"] = True
    n = ctx.policy()["verbatim_ngram"]
    grams = source_grams(ctx, pid, n)
    if grams:
        worst = (0, "")
        for s in strings_in({k: v for k, v in mat.items() if k not in ("source_meta", "terms")}):
            span, _ = verbatim(s, grams, n)
            if span > worst[0]:
                worst = (span, s[:80])
        limit = 2 * n
        if worst[0] > limit:
            errs.append(f"materials copy a {worst[0]}-word span from the paper (limit {limit}): "
                        f"'{worst[1]}...' -- rewrite as structured facts")
    terms, numbers = blocked_terms(ctx, pid)
    if not mat.get("terms", {}).get("method_names") and not mat.get("idea", {}).get("method_name"):
        errs.append("terms.method_names is empty: list the paper's method/system names (used by the overfitting guard)")
    dom = mat.get("domain", {}).get("id")
    taxonomy = jload(os.path.join(ctx.skill, "references", "domain_taxonomies.json"))["domains"]
    if dom not in taxonomy:
        warns.append(f"domain '{dom}' has no template; rules from this paper can only be universal candidates. "
                     f"Known domains: {list(taxonomy)}")
    ok = not errs
    jsave(os.path.join(cache, "materials.check.json"), {"ok": ok, "errors": errs, "warnings": warns, "t": now()})
    p["materials"] = ok
    p["domain"] = dom
    ctx.save_run()
    led = ctx.ledger()
    meta = mat.get("source_meta", {})
    led.setdefault("papers", {}).setdefault(pid, {}).update(
        {"title": meta.get("title", ""), "venue": meta.get("venue", mat.get("domain", {}).get("venue", "")),
         "year": meta.get("year", ""), "domain": dom})
    jsave(ctx.ledger_path, led)
    for e in errs:
        print(f"[FAIL] {e}")
    for w in warns:
        print(f"[warn] {w}")
    print(f"identifiers guarded: {len(terms)}; result values guarded: {len(numbers)}")
    print("materials OK" if ok else "materials REJECTED -- fix materials.json and rerun")
    return 0 if ok else 1


def lint_counts(skill, draft_dir):
    tex = None
    for name in ("main.tex", "paper.tex"):
        if os.path.exists(os.path.join(draft_dir, name)):
            tex = os.path.join(draft_dir, name)
    if tex is None:
        cands = [f for f in os.listdir(draft_dir) if f.endswith(".tex")]
        tex = os.path.join(draft_dir, cands[0]) if cands else None
    lint = os.path.join(skill, "scripts", "lint_paper.py")
    if not tex or not os.path.exists(lint):
        return None
    out = subprocess.run([sys.executable, lint, tex], capture_output=True, text=True, timeout=120).stdout
    m = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)", out)
    return {"file": os.path.basename(tex), "errors": int(m.group(1)), "warnings": int(m.group(2))} if m else None


def draft_text(draft_dir):
    parts = []
    for root, _, files in os.walk(draft_dir):
        for f in files:
            if f.endswith((".tex", ".md", ".txt")):
                with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                    parts.append(fh.read())
    return "\n".join(parts)


def cmd_score(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    if is_figure(ctx):
        return fig().cmd_score(a)
    p = ctx.paper(a.paper)
    pid, k = p["paper_id"], a.iter
    it = ctx.iter_dir(pid, k)
    review = jload(os.path.join(it, "review.json"))
    errs = validate(review, jload(os.path.join(SCHEMAS, "review.schema.json")))
    ids = [g.get("id") for g in review.get("gaps", [])]
    if len(ids) != len(set(ids)):
        errs.append("gap ids are not unique")
    for g in review.get("gaps", []):
        if g.get("generality") == "domain" and not g.get("domain_id"):
            errs.append(f"gap {g.get('id')}: generality 'domain' needs domain_id")
    if errs:
        for e in errs:
            print(f"[FAIL] review.json {e}")
        return 1
    pol = ctx.policy()
    draft = os.path.join(it, "writer", "draft")
    text = draft_text(draft)
    grams = source_grams(ctx, pid, pol["verbatim_ngram"])
    span, frac = verbatim(text, grams, pol["verbatim_ngram"]) if grams else (0, 0.0)
    leak = span >= 25 or frac > 0.05
    score = round(sum(review["scores"][d] for d in SCORE_DIMS) / len(SCORE_DIMS), 3)
    lint = lint_counts(os.path.join(it, "skill_snapshot"), draft)
    metrics = {"paper": pid, "iter": k, "score": score, "scores": review["scores"], "lint": lint,
               "leakage": {"longest_span": span, "ngram_overlap": round(frac, 4)}, "valid": not leak,
               "gaps": {"total": len(review["gaps"]),
                        "actionable": sum(g["generality"] != "paper_specific" and
                                          g["root_cause"] not in ("materials_missing", "writer_error")
                                          for g in review["gaps"])}}
    # keep / revert against the best earlier valid iteration of this paper in this run
    prev = []
    for j in range(1, k):
        mj = jload(os.path.join(ctx.iter_dir(pid, j), "metrics.json"), default={})
        if mj.get("valid") and not mj.get("reverted"):
            prev.append(mj)
    decision = "keep"
    if leak:
        decision = "invalid"
    elif p.get("role") == "holdout" and p.get("baseline") is not None:
        metrics["baseline"] = p["baseline"]
        decision = "regression" if score < p["baseline"] - pol["revert_tolerance"] else "no_regression"
    elif prev:
        best = max(prev, key=lambda m: m["score"])
        worse_lint = (lint and best.get("lint") and lint["errors"] > best["lint"]["errors"])
        if score < best["score"] - pol["revert_tolerance"] or worse_lint:
            decision = f"revert_to_{best['iter']}"
        metrics["best_previous"] = {"iter": best["iter"], "score": best["score"]}
    metrics["decision"] = decision
    jsave(os.path.join(it, "metrics.json"), metrics)
    led = ctx.ledger()
    pe = led.setdefault("papers", {}).setdefault(pid, {})
    if not leak and score > pe.get("best_score", 0):
        pe["best_score"] = score
    pe.setdefault("history", []).append({"run": run["run_id"], "iter": k, "score": score, "valid": not leak,
                                         "role": p.get("role", "train")})
    jsave(ctx.ledger_path, led)
    print(f"paper {pid} iteration {k}: score {score:.2f}/5  "
          + "  ".join(f"{d}={review['scores'][d]}" for d in SCORE_DIMS))
    if lint:
        print(f"lint ({lint['file']}): {lint['errors']} error(s), {lint['warnings']} warning(s)")
    print(f"leakage: longest verbatim span {span} words, {frac:.1%} of 8-grams from the source")
    print(f"gaps: {metrics['gaps']['total']} total, {metrics['gaps']['actionable']} actionable for the skill")
    if decision == "invalid":
        print("DECISION: invalid -- the draft copies the source paper. Discard it, check that the writer had no "
              "access to the paper, and rerun the writer for this iteration.")
        return 1
    if decision == "regression":
        print(f"DECISION: regression on holdout -- {score:.2f} vs earlier best {p['baseline']:.2f}. The run's edits "
              f"likely overfit; inspect the gaps, then consider `evolve.py revert --to-base`.")
        return 1
    if decision == "no_regression":
        print(f"DECISION: no regression on holdout ({score:.2f} vs earlier best {p['baseline']:.2f}).")
        return 0
    if decision.startswith("revert"):
        j = int(decision.split("_")[-1])
        print(f"DECISION: revert -- score dropped vs iteration {j} ({metrics['best_previous']['score']:.2f}). "
              f"Run `evolve.py revert --paper {pid} --to {j}` (restores the skill that produced draft {j} and "
              f"rejects the rules added after it), then propose DIFFERENT edits from review {j}.")
        return 1
    print("DECISION: keep" + (" (last iteration: run finalize)" if k == run["iterations"] else
                              " -- triage gaps, propose rules, edit, then check-edits"))
    return 0


def jaccard(a, b):
    sa, sb = set(tokens(a)), set(tokens(b))
    return len(sa & sb) / max(len(sa | sb), 1)


def rule_status(rule, pol, led):
    support = {e["paper"] for e in rule["evidence"]}
    counter = {e["paper"] for e in rule.get("counter", [])}
    if rule["status"] in ("rejected",):
        return "rejected"
    if counter and len(counter) >= len(support):
        return "retired"
    if rule["scope"] == "universal":
        domains = {led["papers"].get(pp, {}).get("domain") for pp in support}
        if len(support) >= pol["universal_rule_min_papers"] and len(domains - {None}) >= pol["universal_rule_min_domains"]:
            return "active"
        return "candidate"
    return "established" if len(support) >= pol["domain_rule_promotion_papers"] else "provisional"


def cmd_propose(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid = p["paper_id"]
    if p.get("role") == "holdout":
        die("holdout papers only measure regressions; do not propose rules from them", 1)
    pol = ctx.policy()
    figure = is_figure(ctx)
    review = jload(os.path.join(ctx.iter_dir(pid, a.iter), "figure_review.json" if figure else "review.json"))
    gap = next((g for g in review["gaps"] if g["id"] == a.gap), None)
    if not gap:
        die(f"gap {a.gap} not found in iteration {a.iter} review", 1)
    if figure and gap["root_cause"] in fig().NOT_RULES:
        die(f"gap {a.gap} has root cause '{gap['root_cause']}': {fig().NOT_RULES[gap['root_cause']]}", 1)
    if figure and a.scope == "universal" and a.target not in ("references/figures_and_captions.md", "SKILL.md"):
        die("figure-mode universal rules go to references/figures_and_captions.md (or SKILL.md)", 2)
    if gap["generality"] == "paper_specific":
        die(f"gap {a.gap} is paper-specific: record it in the report, do not turn it into a rule", 1)
    if gap["root_cause"] in ("materials_missing", "writer_error"):
        die(f"gap {a.gap} has root cause '{gap['root_cause']}' (not a skill defect); no rule", 1)
    led = ctx.ledger()
    paper_domain = led["papers"].get(pid, {}).get("figure_domain" if figure else "domain") or \
        led["papers"].get(pid, {}).get("domain")
    if a.scope == "domain":
        dom = a.domain or gap.get("domain_id") or paper_domain
        target = f"references/domains/{dom}.md"
        if not os.path.exists(os.path.join(ctx.skill, target)):
            die(f"no domain template {target}", 1)
        scope = f"domain:{dom}"
    else:
        scope, target = "universal", a.target
        if not target or not UNIVERSAL_FILES.match(target):
            die("universal rules need --target: SKILL.md or one of references/writing/*.md, "
                "figures_and_captions.md, layout_and_typesetting.md, bibliography.md, "
                "revision_and_submission.md, mechanism_sentence_bank.md", 2)
    reasons = guard_text(ctx, a.rule, [pp["paper_id"] for pp in run["papers"]], pol["verbatim_ngram"])
    if len(a.rule.split()) < 6:
        reasons.append("rule is too short to be actionable (write a complete imperative sentence)")
    if reasons:
        print("REFUSED (overfitting guard):")
        for r in reasons:
            print(f"  - {r}")
        print("Rewrite the rule at the level of the domain or of writing in general, then propose again.")
        return 1
    ev = {"paper": pid, "run": run["run_id"], "iter": a.iter, "gap": a.gap}
    if a.contradicts:
        rule = next((r for r in led["rules"] if r["id"] == a.contradicts), None)
        if not rule:
            die(f"unknown rule {a.contradicts}", 1)
        rule.setdefault("counter", []).append(ev)
        new_status = rule_status(rule, pol, led)
        rule["history"].append({"t": now(), "event": f"counter-evidence from {pid}", "status": new_status})
        rule["status"] = new_status
        jsave(ctx.ledger_path, led)
        print(f"{rule['id']}: counter-evidence recorded -> status {new_status}")
        if new_status == "retired":
            print(f"ACTION: delete the line marked <!-- {rule['id']} --> from {', '.join(rule['files'])}")
        return 0
    dead = [r for r in led["rules"] if r["scope"] == scope and r["status"] == "rejected"
            and jaccard(r["text"], a.rule) >= 0.5 and any(e.get("run") == run["run_id"] for e in r["evidence"])]
    if dead:
        print(f"REFUSED: too similar to {dead[0]['id']}, which was reverted in this run because the score dropped. "
              f"Address the gap differently.")
        return 1
    same = [r for r in led["rules"] if r["scope"] == scope and r["status"] not in ("rejected", "retired")
            and jaccard(r["text"], a.rule) >= 0.5]
    if same:
        rule = max(same, key=lambda r: jaccard(r["text"], a.rule))
        if any(e["paper"] == pid for e in rule["evidence"]):
            print(f"{rule['id']} already has evidence from paper {pid}; same paper cannot support a rule twice.")
            print(f"Existing text: {rule['text']}")
            return 0
        rule["evidence"].append(ev)
        created = False
    else:
        mine = [r for r in led["rules"] if r["scope"].startswith("domain:") and r["evidence"]
                and r["evidence"][0]["paper"] == pid and r["status"] == "provisional"]
        if scope.startswith("domain:") and len(mine) >= pol["max_provisional_rules_per_paper"]:
            print(f"REFUSED: paper {pid} already contributed {len(mine)} provisional rules "
                  f"(limit {pol['max_provisional_rules_per_paper']}); one paper must not dominate a template.")
            return 1
        rid = "R-%04d" % (1 + max([int(r["id"][2:]) for r in led["rules"]] or [0]))
        rule = {"id": rid, "scope": scope, "text": a.rule.strip(), "files": [target], "evidence": [ev],
                "counter": [], "status": "new", "root_cause": gap["root_cause"],
                "skill_location": gap.get("skill_location", ""), "history": []}
        led["rules"].append(rule)
        created = True
    old = rule["status"]
    rule["status"] = rule_status(rule, pol, led)
    rule["history"].append({"t": now(), "event": "created" if created else f"evidence from {pid}",
                            "status": rule["status"], "run": run["run_id"], "iter": a.iter})
    if rule["status"] in ("provisional", "established", "active") and old != rule["status"]:
        rule.setdefault("applied", []).append({"run": run["run_id"], "paper": pid, "iter": a.iter})
    jsave(ctx.ledger_path, led)
    rid, st = rule["id"], rule["status"]
    print(f"{rid} [{scope}] status: {st} (support: {len({e['paper'] for e in rule['evidence']})} paper(s))")
    marker = f"<!-- {rid} -->"
    if st == "provisional" and created:
        print(f"ACTION: append to {target} §8 'Provisional rules' (replace '_(none yet)_' if present):\n"
              f"  - {rule['text']} {marker}")
    elif st == "established" and old == "provisional":
        print(f"ACTION: promote -- move the line marked {marker} from §8 of {target} into the matching section "
              f"(§1-7), keeping the marker.")
    elif st == "active" and old != "active":
        where = f"the section matching '{rule['skill_location']}'" if rule.get("skill_location") else "the most relevant section"
        print(f"ACTION: add to {target}, in {where}, as an imperative bullet ending with {marker}:\n  - {rule['text']} {marker}")
    elif st == "candidate":
        domains = {led['papers'].get(e['paper'], {}).get('domain') for e in rule['evidence']}
        print(f"HOLD: universal rules need >= {pol['universal_rule_min_papers']} papers from >= "
              f"{pol['universal_rule_min_domains']} domains (now {len(rule['evidence'])} paper(s), "
              f"{len(domains - {None})} domain(s)). Do not edit the skill for this rule yet.")
    else:
        print("No file edit needed.")
    return 0


def section8_lines(path):
    """Set of 0-based line indexes inside '## 8.' of a domain template."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    inside, idx = False, set()
    for i, l in enumerate(lines):
        if l.startswith("## "):
            inside = l.startswith("## 8.")
        elif inside:
            idx.add(i)
    return lines, idx


def cmd_check_edits(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    p = ctx.paper(a.paper)
    pid, k = p["paper_id"], a.iter
    pol = ctx.policy()
    snap = os.path.join(ctx.iter_dir(pid, k), "skill_snapshot")
    if not os.path.isdir(snap):
        die(f"no snapshot for iteration {k}", 1)
    led = ctx.ledger()
    rules = {r["id"]: r for r in led["rules"]}
    old, new = skill_files(snap), skill_files(run["skill_dir"])
    errors, warns, added_total = [], [], 0
    pids = [pp["paper_id"] for pp in run["papers"]]
    for rel in sorted(set(old) | set(new)):
        if rel in IGNORED:
            continue
        a_txt = open(old[rel], encoding="utf-8", errors="replace").read().splitlines() if rel in old else []
        b_txt = open(new[rel], encoding="utf-8", errors="replace").read().splitlines() if rel in new else []
        if a_txt == b_txt:
            continue
        uni, dom = UNIVERSAL_FILES.match(rel), DOMAIN_FILES.match(rel)
        if STYLE_FILES.match(rel) and is_figure(ctx):
            errors += fig().check_style_file(rel, old.get(rel), new.get(rel), rules, run["skill_dir"])
            continue
        if not (uni or dom):
            errors.append(f"{rel}: evolution may only edit SKILL.md, references/writing/, the rule reference "
                          f"files, references/domains/ and (figure mode, via propose-style) "
                          f"references/figure_styles/<domain>.json; scripts, assets and taxonomies need a human")
            continue
        sm = difflib.SequenceMatcher(None, a_txt, b_txt, autojunk=False)
        added = [(j, b_txt[j]) for tag, _, _, j1, j2 in sm.get_opcodes() if tag in ("replace", "insert")
                 for j in range(j1, j2)]
        removed = [a_txt[i] for tag, i1, i2, _, _ in sm.get_opcodes() if tag in ("replace", "delete")
                   for i in range(i1, i2)]
        sec8 = section8_lines(new[rel])[1] if dom else set()
        for j, line in added:
            s = line.strip()
            if not s or s.startswith("#") or re.fullmatch(r"[|:\-\s]+", s) or s == "_(none yet)_":
                continue
            added_total += 1
            ids = MARKER.findall(line)
            if not ids:
                errors.append(f"{rel}:{j + 1}: added line has no rule marker <!-- R-xxxx --> "
                              f"(every evolution edit must be backed by a ledger rule): {s[:70]}")
                continue
            for rid in ids:
                r = rules.get(rid)
                if not r:
                    errors.append(f"{rel}:{j + 1}: {rid} is not in the ledger")
                    continue
                st = r["status"]
                if st in ("retired", "rejected", "candidate", "new"):
                    errors.append(f"{rel}:{j + 1}: {rid} has status '{st}' and must not appear in the skill")
                elif dom:
                    if r["scope"] != f"domain:{dom.group(1)}":
                        errors.append(f"{rel}:{j + 1}: {rid} has scope {r['scope']}, not this domain")
                    elif st == "provisional" and j not in sec8:
                        errors.append(f"{rel}:{j + 1}: {rid} is provisional -> it belongs in §8 'Provisional rules'")
                    elif st == "established" and j in sec8:
                        errors.append(f"{rel}:{j + 1}: {rid} is established -> move it out of §8")
                elif uni and r["scope"] != "universal":
                    errors.append(f"{rel}:{j + 1}: {rid} is a {r['scope']} rule; universal files need active "
                                  f"universal rules")
            for reason in guard_text(ctx, MARKER.sub("", line), pids, pol["verbatim_ngram"]):
                errors.append(f"{rel}:{j + 1}: {reason}")
        for line in removed:
            for rid in MARKER.findall(line):
                r = rules.get(rid)
                still = any(rid in l for l in b_txt) or any(rid in open(f, encoding="utf-8", errors="replace").read()
                                                            for f in new.values() if f.endswith(".md"))
                if r and r["status"] not in ("retired", "rejected") and not still:
                    warns.append(f"{rel}: rule {rid} was deleted from the skill but is '{r['status']}' in the ledger")
    if added_total > pol["max_added_lines_per_iteration"]:
        errors.append(f"{added_total} lines added in one iteration (limit {pol['max_added_lines_per_iteration']}); "
                      f"keep only the highest-impact rules")
    # every retired rule must be gone, every provisional/established/active rule present once
    corpus = {rel: open(path, encoding="utf-8", errors="replace").read() for rel, path in new.items()
              if rel.endswith(".md")}
    for r in led["rules"]:
        if r["scope"].startswith("style:"):
            continue          # style values live in figure_styles/*.json and are checked above
        where = [rel for rel, txt in corpus.items() if f"<!-- {r['id']} -->" in txt]
        if r["status"] in ("retired", "rejected", "candidate") and where:
            errors.append(f"{r['id']} is {r['status']} but still appears in {where}")
        if r["status"] in ("provisional", "established", "active") and not where and \
                any(ap.get("run") == run["run_id"] for ap in r.get("applied", [])):
            warns.append(f"{r['id']} ({r['status']}) was approved in this run but is not in the skill yet")
    validator = os.path.join(run["skill_dir"], "scripts", "validate_skill.py")
    if os.path.exists(validator):
        res = subprocess.run([sys.executable, validator, run["skill_dir"]], capture_output=True, text=True,
                             timeout=60)
        if res.returncode != 0:
            errors.append("validate_skill.py failed:\n" + res.stdout.strip())
        elif "warning" in res.stdout and " 0 warning" not in res.stdout:
            warns.append("validate_skill.py: " + res.stdout.strip().splitlines()[-1])
    ok = not errors
    jsave(os.path.join(ctx.iter_dir(pid, k), "edits.check.json"),
          {"ok": ok, "errors": errors, "warnings": warns, "added_lines": added_total, "t": now()})
    for e in errors:
        print(f"[FAIL] {e}")
    for w in warns:
        print(f"[warn] {w}")
    print(f"{added_total} rule line(s) added; " + ("edits OK" if ok else "edits REJECTED -- fix or revert"))
    return 0 if ok else 1


def cmd_revert(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    if a.to_base:
        snap = os.path.join(ctx.run_dir, "base_snapshot")
        since = None
    else:
        p = ctx.paper(a.paper)
        snap = os.path.join(ctx.iter_dir(p["paper_id"], a.to), "skill_snapshot")
        since = (p["paper_id"], a.to)
    if not os.path.isdir(snap):
        die(f"snapshot not found: {snap}", 1)
    skill = run["skill_dir"]
    cur, old = skill_files(skill), skill_files(snap)
    restored = 0
    for rel in set(cur) | set(old):
        if rel in IGNORED:
            continue
        if rel in old:
            if rel not in cur or open(cur[rel], "rb").read() != open(old[rel], "rb").read():
                os.makedirs(os.path.dirname(os.path.join(skill, rel)), exist_ok=True)
                shutil.copyfile(old[rel], os.path.join(skill, rel))
                restored += 1
        else:
            os.remove(cur[rel])
            restored += 1
    led = ctx.ledger()
    rejected = []
    for r in led["rules"]:
        applied = [ap for ap in r.get("applied", []) if ap.get("run") == run["run_id"]]
        if since is None:
            hit = bool(applied)
        else:
            hit = any(ap["paper"] == since[0] and ap["iter"] >= since[1] for ap in applied)
        if not hit:
            continue
        mine = [e for e in r["evidence"] if e.get("run") == run["run_id"]]
        if len(mine) == len(r["evidence"]):
            r["status"] = "rejected"
        else:
            r["evidence"] = [e for e in r["evidence"] if e.get("run") != run["run_id"]]
            r["status"] = rule_status(r, ctx.policy(), led)
        r["history"].append({"t": now(), "event": f"reverted in run {run['run_id']}", "status": r["status"]})
        rejected.append(r["id"])
    jsave(ctx.ledger_path, led)
    if since:   # drafts produced by the discarded skill versions no longer count as "best"
        for j in range(since[1] + 1, run["iterations"] + 1):
            m = os.path.join(ctx.iter_dir(since[0], j), "metrics.json")
            if os.path.exists(m):
                mj = jload(m)
                mj["reverted"] = True
                jsave(m, mj)
    run["events"].append({"t": now(), "event": "revert", "to": "base" if since is None else since})
    ctx.save_run()
    print(f"restored {restored} file(s) from {snap}")
    print(f"rules rejected or evidence withdrawn: {', '.join(rejected) or 'none'}")
    return 0


def cmd_holdout(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    led = ctx.ledger()
    if a.list or not a.paper:
        print("papers with cached materials (usable as holdout):")
        for pid, info in led.get("papers", {}).items():
            ok = os.path.exists(os.path.join(ctx.paper_cache(pid), "materials.json"))
            print(f"  {pid}  best={info.get('best_score', '-')}  figure={info.get('figure_best_score', '-')}  domain={info.get('domain')}  "
                  f"{info.get('title', '')[:50]}  {'' if ok else '(no cached materials)'}")
        return 0
    pid = a.paper
    key = "figure_best_score" if is_figure(ctx) else "best_score"
    if is_figure(ctx):
        if not jload(os.path.join(ctx.paper_cache(pid), "figure_brief.check.json"), default={}).get("ok"):
            die(f"no validated figure brief cached for {pid}", 1)
    elif not os.path.exists(os.path.join(ctx.paper_cache(pid), "materials.json")):
        die(f"no cached materials for {pid}", 1)
    if any(p["paper_id"] == pid for p in run["papers"]):
        die(f"{pid} is already in this run", 1)
    run["papers"].append({"paper_id": pid, "source": led["papers"].get(pid, {}).get("title", pid), "text": True,
                          "materials": True, "role": "holdout", "domain": led["papers"].get(pid, {}).get("domain"),
                          "baseline": led["papers"].get(pid, {}).get(key), "brief": is_figure(ctx)})
    ctx.save_run()
    print(f"holdout {pid} added (previous best {led['papers'].get(pid, {}).get(key, '-')}). Run "
          f"{'illustrator + critic' if is_figure(ctx) else 'writer + reviewer'} for iteration 1 and score; a drop > {ctx.policy()['revert_tolerance']} means the run "
          f"overfitted -> consider `revert --to-base`.")
    return 0


def collect(ctx):
    run = ctx.need_run()
    rows = []
    for p in run["papers"]:
        for k in range(1, run["iterations"] + 1):
            m = jload(os.path.join(ctx.iter_dir(p["paper_id"], k), "metrics.json"), default={})
            if m:
                rows.append((p, m))
    return rows


def cmd_status(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    print(f"run {run['run_id']}  skill {run['skill_dir']}  iterations {run['iterations']}")
    for p, m in collect(ctx):
        lint = f"lint {m['lint']['errors']}E/{m['lint']['warnings']}W" if m.get("lint") else ""
        extra = f" (baseline {p['baseline']})" if p.get("role") == "holdout" else ""
        print(f"  {p['paper_id']} [{p.get('role', 'train')}] iter {m['iter']}: {m['score']:.2f}{extra}  "
              f"{lint}  -> {m['decision']}{' (reverted)' if m.get('reverted') else ''}")
    led = ctx.ledger()
    by = {}
    for r in led["rules"]:
        by[r["status"]] = by.get(r["status"], 0) + 1
    print("ledger rules: " + (", ".join(f"{k}={v}" for k, v in sorted(by.items())) or "none"))
    return 0


def cmd_finalize(a):
    ctx = Ctx(a.workdir, a.run)
    run = ctx.need_run()
    led, pol = ctx.ledger(), ctx.policy()
    changes = []
    for r in led["rules"]:
        if r["scope"].startswith("style:"):
            continue          # style rules are synced with their profile by propose-style
        st = rule_status(r, pol, led) if r["status"] not in ("rejected",) else "rejected"
        if st != r["status"]:
            changes.append(f"{r['id']}: {r['status']} -> {st}")
            r["history"].append({"t": now(), "event": "finalize", "status": st})
            r["status"] = st
    led.setdefault("runs", []).append({"run": run["run_id"], "finished": now(),
                                       "papers": [p["paper_id"] for p in run["papers"]]})
    jsave(ctx.ledger_path, led)
    base = os.path.join(ctx.run_dir, "base_snapshot")
    diffstat = []
    cur, old = skill_files(run["skill_dir"]), skill_files(base)
    for rel in sorted(set(cur) | set(old)):
        if rel in IGNORED:
            continue
        a_t = open(old[rel], encoding="utf-8", errors="replace").read().splitlines() if rel in old else []
        b_t = open(cur[rel], encoding="utf-8", errors="replace").read().splitlines() if rel in cur else []
        if a_t != b_t:
            d = list(difflib.unified_diff(a_t, b_t, lineterm="", n=0))
            plus = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
            minus = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
            diffstat.append(f"| `{rel}` | +{plus} | -{minus} |")
    rows = collect(ctx)
    rules_run = [r for r in led["rules"] if any(e.get("run") == run["run_id"] for e in r["evidence"] + r.get("counter", []))
                 and not r["scope"].startswith("style:")]
    lines = [f"# Evolution report — run {run['run_id']}" + (" (figure mode)" if is_figure(ctx) else ""), "",
             f"- Skill: `{run['skill_dir']}`  (git base: `{run.get('git_base') or 'n/a'}`)",
             f"- Iterations per paper: {run['iterations']}"]
    if is_figure(ctx):
        lines += fig().report_lines(ctx, rows)
    else:
        lines += ["", "## Scores", "", "| paper | role | iter | score | lint E/W | leakage span | decision |",
                  "| :--- | :--- | ---: | ---: | :--- | ---: | :--- |"]
    for p, m in ([] if is_figure(ctx) else rows):
        lint = f"{m['lint']['errors']}/{m['lint']['warnings']}" if m.get("lint") else "-"
        lines.append(f"| {p['paper_id']} | {p.get('role', 'train')} | {m['iter']} | {m['score']:.2f} | {lint} | "
                     f"{m['leakage']['longest_span']} | {m['decision']}{' (reverted)' if m.get('reverted') else ''} |")
    lines += ["", "## Rules touched in this run", "", "| id | scope | status | support | text |",
              "| :--- | :--- | :--- | ---: | :--- |"]
    for r in rules_run:
        lines.append(f"| {r['id']} | {r['scope']} | {r['status']} | {len({e['paper'] for e in r['evidence']})} | "
                     f"{r['text'][:110]} |")
    lines += ["", "## Status changes at finalize", ""] + ([f"- {c}" for c in changes] or ["- none"])
    lines += ["", "## Skill diff vs. run start", "", "| file | added | removed |", "| :--- | ---: | ---: |"]
    lines += diffstat or ["| (no changes) | | |"]
    lines += ["", "## Next steps (human)", "",
              "1. Review the diff: `git diff -- <skill_dir>` (and `evolution_ledger.json`).",
              "2. Keep it: commit. Discard it: `evolve.py revert --to-base`.",
              "3. Promotion actions listed above (provisional -> established, candidate -> active) must be "
              "applied to the files and re-checked with `check-edits` in the next run."]
    report = os.path.join(ctx.run_dir, "report.md")
    with open(report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log = os.path.join(run["skill_dir"], "EVOLUTION_LOG.md")
    if os.path.exists(log):
        best = {}
        for p, m in rows:
            if p.get("role", "train") == "train" and m["valid"] and not m.get("reverted"):
                best.setdefault(p["paper_id"], []).append(m["score"])
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"\n### [Evolution run {run['run_id']}{' (figure mode)' if is_figure(ctx) else ''} — {now()}]\n")
            for pid, sc in best.items():
                f.write(f"- Paper `{pid}` ({led['papers'].get(pid, {}).get('domain')}): "
                        f"{'figure ' if is_figure(ctx) else ''}score "
                        f"{sc[0]:.2f} -> {sc[-1]:.2f} over {len(sc)} iteration(s)\n")
            if is_figure(ctx):
                st = [r for r in led["rules"] if r["scope"].startswith("style:")
                      and any(e.get("run") == run["run_id"] for e in r["evidence"])]
                f.write(f"- Style changes: {', '.join(r['id'] + ' ' + r['param'] + '=' + repr(r['value']) + ' (' + r['status'] + ')' for r in st) or 'none'}\n")
                fr = [x for x in led.get("feature_requests", []) if any(e.get("run") == run["run_id"] for e in x["evidence"])]
                f.write(f"- Feature requests: {', '.join(x['id'] for x in fr) or 'none'}\n")
            f.write(f"- Rules touched: {', '.join(r['id'] + ' (' + r['status'] + ')' for r in rules_run) or 'none'}\n"
                    "\n---\n")
    print("\n".join(lines))
    print(f"\nreport: {report}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", default=".evolution", help="run data (papers, drafts); keep out of git")
    ap.add_argument("--run", help="run id (default: latest)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init")
    s.add_argument("--skill", required=True, help="path to the skill to evolve (e.g. skills/top-tier-paper-writing)")
    s.add_argument("--paper", action="append", required=True, help="exemplar paper (.pdf/.md/.txt/.tex); repeatable")
    s.add_argument("--iterations", type=int, default=3)
    s.add_argument("--mode", choices=["writing", "figure"], default="writing",
                   help="writing: evolve the writing rules; figure: evolve diagram rules and style profiles")
    s.add_argument("--venue", help="figure mode: venue profile for the figure width (default: from the paper)")
    s = sub.add_parser("task")
    s.add_argument("--role", choices=["extractor", "writer", "reviewer", "fig-extractor", "illustrator", "critic"],
                   required=True)
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int)
    for name in ("check-materials", "check-brief"):
        s = sub.add_parser(name)
        s.add_argument("--paper", required=True)
    s = sub.add_parser("score")
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int, required=True)
    s = sub.add_parser("propose")
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int, required=True)
    s.add_argument("--gap", required=True, help="gap id from review.json, e.g. G3")
    s.add_argument("--scope", choices=["domain", "universal"], required=True)
    s.add_argument("--domain", help="domain id (default: the gap's domain_id or the paper's domain)")
    s.add_argument("--target", help="universal rules: file to edit (relative to the skill)")
    s.add_argument("--rule", required=True, help="generalized imperative rule text (no paper specifics)")
    s.add_argument("--contradicts", help="rule id this gap contradicts (adds counter-evidence instead)")
    s = sub.add_parser("propose-style")
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int, required=True)
    s.add_argument("--gap", required=True, help="figure-review gap with root_cause style_parameter")
    s.add_argument("--param", help="override the gap's style_change.param")
    s.add_argument("--value", help="override the gap's style_change.value")
    s.add_argument("--reason", help="general reason recorded with the change (default: gap.why_general)")
    s.add_argument("--default", action="store_true", help="change default.json instead of the domain profile")
    s = sub.add_parser("request-feature")
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int, required=True)
    s.add_argument("--gap", required=True, help="figure-review gap with root_cause generator_limitation")
    s.add_argument("--text", help="override the gap's feature_request text")
    s = sub.add_parser("check-edits")
    s.add_argument("--paper", required=True)
    s.add_argument("--iter", type=int, required=True, help="iteration whose review the edits respond to")
    s = sub.add_parser("revert")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--to", type=int, help="restore the skill snapshot taken before this iteration's draft")
    g.add_argument("--to-base", action="store_true", help="restore the skill as it was at `init`")
    s.add_argument("--paper")
    s = sub.add_parser("holdout")
    s.add_argument("--paper", help="paper id with cached materials")
    s.add_argument("--list", action="store_true")
    sub.add_parser("status")
    sub.add_parser("finalize")
    a = ap.parse_args(argv)
    if a.cmd == "revert" and a.to and not a.paper:
        die("revert --to needs --paper")
    fn = {"init": cmd_init, "task": cmd_task, "check-materials": cmd_check_materials, "score": cmd_score,
          "propose": cmd_propose, "check-edits": cmd_check_edits, "revert": cmd_revert, "holdout": cmd_holdout,
          "status": cmd_status, "finalize": cmd_finalize,
          "check-brief": lambda x: fig().cmd_check_brief(x),
          "propose-style": lambda x: fig().cmd_propose_style(x),
          "request-feature": lambda x: fig().cmd_request_feature(x)}[a.cmd]
    if a.cmd in ("check-brief", "propose-style", "request-feature"):
        ctx = Ctx(a.workdir, a.run)
        if not is_figure(ctx):
            die(f"`{a.cmd}` needs a figure-mode run (`init --mode figure`)")
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
