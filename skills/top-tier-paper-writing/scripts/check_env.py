#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Pre-flight check: is the environment ready for a given part of the skill? (stdlib only)

    python3 check_env.py                 # everything
    python3 check_env.py --for plot      # plot | layout | bib | lint | network (repeatable)
    python3 check_env.py --for layout --venue acl --paper-dir paper/   # + venue class and fonts

Prints one line per requirement and the exact fix. Never installs anything.
Exit codes: 0 all requested features ready, 1 something missing.
"""
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = os.path.join(SKILL_DIR, "requirements.txt")


def ok(label, good, detail="", fix=""):
    return {"label": label, "ok": good, "detail": detail, "fix": "" if good else fix}


def py_checks():
    v = sys.version_info
    return [ok("python >= 3.8", v >= (3, 8), f"{v.major}.{v.minor}.{v.micro}", "install Python 3.8+")]


def module(name):
    spec = importlib.util.find_spec(name)
    if not spec:
        return ok(f"python module {name}", False, "not importable",
                  f"run scripts with `uv run <script>` (installs into an isolated env), or ask the user "
                  f"before `python3 -m pip install -r {REQ}`")
    try:
        mod = __import__(name)
        return ok(f"python module {name}", True, getattr(mod, "__version__", ""))
    except Exception as e:  # noqa: BLE001
        return ok(f"python module {name}", False, str(e), f"reinstall {name}")


def latex_checks():
    res = []
    engines = [e for e in ("pdflatex", "xelatex", "lualatex") if shutil.which(e)]
    res.append(ok("LaTeX engine", bool(engines), ", ".join(engines) or "none on PATH",
                  "install TeX Live / MacTeX / MiKTeX (ask the user first)"))
    kpse = shutil.which("kpsewhich")
    if not kpse:
        res.append(ok("kpsewhich", False, "not on PATH", "comes with TeX Live / MiKTeX"))
        return res
    def find(f):
        try:
            return subprocess.run([kpse, f], capture_output=True, text=True, timeout=20).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    lt = find("latex.ltx")
    fmt = ""
    if lt:
        with open(lt, encoding="latin-1", errors="replace") as f:
            m = re.search(r"\\[egx]?def\\fmtversion\s*\{([0-9/-]+)\}", f.read())
        fmt = m.group(1) if m else ""
    good = bool(fmt) and fmt.replace("/", "-") >= "2020-10-01"
    res.append(ok("LaTeX kernel >= 2020-10-01 (floatcheck hooks)", good, fmt or "unknown",
                  "update the TeX distribution (tlmgr update --self --all, or the MiKTeX console)"))
    res.append(ok("letltxmacro.sty", bool(find("letltxmacro.sty")), find("letltxmacro.sty") or "missing",
                  "tlmgr install letltxmacro  (Debian/Ubuntu: texlive-latex-recommended)"))
    for tool in ("bibtex", "biber"):
        res.append(ok(f"{tool} (optional)", True, shutil.which(tool) or "not found -- only needed with --" + tool))
    return res


def venue_checks(name, paper_dir):
    import json
    with open(os.path.join(SKILL_DIR, "references", "venues.json"), encoding="utf-8") as f:
        venues = json.load(f)["venues"]
    if name not in venues:
        return [ok(f"venue '{name}'", False, "unknown", "choose one of: " + ", ".join(venues))]
    v = venues[name]
    kpse = shutil.which("kpsewhich")
    res = []

    def found(fname):
        if paper_dir and os.path.exists(os.path.join(paper_dir, fname)):
            return os.path.join(paper_dir, fname)
        if not kpse:
            return ""
        try:
            return subprocess.run([kpse, fname], capture_output=True, text=True, timeout=20).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""
    for cls in v.get("class_files", []):
        where = found(cls)
        res.append(ok(f"{name}: {cls}", bool(where), where or "missing",
                      "copy the official style files next to main.tex (pass --paper-dir), or install them; "
                      "without them page counts and float positions are only estimates"))
    # a font package only helps if its font files exist too (times.sty without the URW fonts
    # silently falls back to Computer Modern and changes every line break)
    probes = {"times.sty": "ptmr7t.tfm", "mathptmx.sty": "ptmr7t.tfm", "newtxtext.sty": "ntx-Regular-tlf-t1.tfm",
              "libertine.sty": "LinLibertineT-tlf-t1.tfm"}
    fonts = [f for f in v.get("font_packages", []) if found(f) and (f not in probes or found(probes[f]))]
    broken = [f for f in v.get("font_packages", []) if found(f) and f in probes and not found(probes[f])]
    if v.get("font_packages"):
        res.append(ok(f"{name}: body font ({v.get('body_font', '?')})", bool(fonts),
                      ", ".join(fonts) or ("package present but font files missing: " + ", ".join(broken)
                                           if broken else "none of " + ", ".join(v["font_packages"])),
                      "install the fonts (TeX Live: tlmgr install newtx, or the texlive-fonts-recommended "
                      "package); otherwise LaTeX falls back to another font and every line break differs"))
    if not v.get("class_files"):
        res.append(ok(f"{name}: style file", True, "year-specific file (e.g. " + v["name"].split("(")[-1].rstrip(")")
                      + "): check it is next to main.tex"))
    return res


def network_check():
    try:
        req = urllib.request.Request("https://export.arxiv.org/api/query?search_query=all:test&max_results=1",
                                     headers={"User-Agent": "top-tier-paper-writing-skill/1.2"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return [ok("arXiv API reachable", r.status == 200, f"HTTP {r.status}")]
    except Exception as e:  # noqa: BLE001
        return [ok("arXiv API reachable", False, str(e)[:90],
                   "use --offline / local files; network is optional")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--venue", help="also check the venue's class/style files and fonts (references/venues.json)")
    ap.add_argument("--paper-dir", help="directory of main.tex (style files may live there)")
    ap.add_argument("--for", dest="features", action="append",
                    choices=["plot", "layout", "bib", "lint", "network"], help="feature(s) to check")
    args = ap.parse_args(argv)
    feats = args.features or ["plot", "layout", "bib", "lint", "network"]

    results = py_checks()
    results.append(ok("uv (optional, isolated runs)", True,
                      shutil.which("uv") or "not found -- fall back to python3 + requirements.txt"))
    if "plot" in feats:
        results += [module("matplotlib"), module("numpy")]
    if "layout" in feats:
        results += latex_checks()
    if args.paper_dir and not os.path.isdir(args.paper_dir):
        results.append(ok("paper directory", False, f"{args.paper_dir} does not exist",
                          "pass the folder that contains main.tex"))
    if args.venue:
        results += venue_checks(args.venue, args.paper_dir)
    if "network" in feats:
        results += network_check()
    # lint and bib are stdlib-only: nothing beyond Python itself

    missing = [r for r in results if not r["ok"]]
    for r in results:
        print(f"[{' ok ' if r['ok'] else 'MISS'}] {r['label']}: {r['detail']}")
        if r["fix"]:
            print(f"        fix: {r['fix']}")
    critical = [r for r in missing if not r["label"].startswith("arXiv")] if "network" not in (args.features or []) else missing
    print("\nready" if not critical else f"\n{len(critical)} requirement(s) missing for: {', '.join(feats)}")
    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
