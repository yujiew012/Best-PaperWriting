#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""One-command float placement check: diagnostic build + check_layout.py (+ baseline compare).

Builds the paper into a separate output directory with floatcheck.sty injected
via TEXINPUTS (the paper's sources and its normal build are not touched),
reruns LaTeX until cross-references settle, then runs check_layout.py.

    uv run layout_check.py paper/main.tex --save-baseline layout_before.json
    # ... edit the paper ...
    uv run layout_check.py paper/main.tex --compare layout_before.json

Options: --engine pdflatex|xelatex|lualatex (match the paper's real engine),
--bibtex / --biber (when no up-to-date main.bbl sits next to main.tex),
--outdir DIR (default: a fresh temporary directory, printed at the end),
--verify-identical (also build WITHOUT floatcheck and compare page counts),
--allow-errors (measure even when LaTeX reports recoverable errors; by default they fail the run).

Exit codes: 0 ok / no regression, 1 rule violations or regression,
2 build failure or usage error (see the printed LaTeX errors).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_layout  # noqa: E402


def latex(engine, tex_dir, texname, stem, outdir, inject, env):
    body = ("\\RequirePackage{floatcheck}" if inject else "") + "\\input{" + texname + "}"
    cmd = [engine, "-interaction=nonstopmode", "-file-line-error", f"-output-directory={outdir}",
           f"-jobname={stem}", body]
    try:
        subprocess.run(cmd, cwd=tex_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=600)
    except FileNotFoundError:
        print(f"[error] '{engine}' not found; run scripts/check_env.py --for layout", file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print("[error] LaTeX timed out after 600 s", file=sys.stderr)
        sys.exit(2)
    log = os.path.join(outdir, stem + ".log")
    return open(log, encoding="utf-8", errors="ignore").read() if os.path.exists(log) else ""


def pages(log_text):
    m = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.S)
    return int(m.group(1)) if m else None


def build(args, tex, inject, outdir):
    tex_dir, texname = os.path.dirname(tex), os.path.basename(tex)
    stem = os.path.splitext(texname)[0]
    env = dict(os.environ)
    sep = os.pathsep
    env["TEXINPUTS"] = HERE + sep + tex_dir + sep + env.get("TEXINPUTS", "")
    if not env["TEXINPUTS"].endswith(sep):
        env["TEXINPUTS"] += sep          # trailing separator keeps the default search path
    env["BIBINPUTS"] = tex_dir + sep + env.get("BIBINPUTS", "")
    log = latex(args.engine, tex_dir, texname, stem, outdir, inject, env)
    if args.bibtex or args.biber:
        tool = ["bibtex", stem] if args.bibtex else ["biber", "--input-directory", tex_dir, stem]
        try:
            subprocess.run(tool, cwd=outdir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=300)
        except FileNotFoundError:
            print(f"[error] {tool[0]} not found", file=sys.stderr)
            sys.exit(2)
    forced = 2 if (args.bibtex or args.biber) else 0   # after a bib pass LaTeX needs two more runs
    for i in range(max(args.max_runs - 1, forced)):
        if i >= forced and not re.search(r"Rerun to get|Label\(s\) may have changed|Please rerun", log):
            break
        log = latex(args.engine, tex_dir, texname, stem, outdir, inject, env)
    return stem, log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", help="main .tex file")
    ap.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    bib = ap.add_mutually_exclusive_group()
    bib.add_argument("--bibtex", action="store_true")
    bib.add_argument("--biber", action="store_true")
    ap.add_argument("--outdir", help="build directory (default: new temp dir)")
    ap.add_argument("--max-runs", type=int, default=4)
    ap.add_argument("--venue", help="venue profile (references/venues.json): page limit + class-file check")
    ap.add_argument("--page-limit", type=float, help="main-body page limit (overrides the venue's)")
    ap.add_argument("--save-baseline", metavar="JSON", help="save this report for a later --compare")
    ap.add_argument("--compare", metavar="JSON", help="compare with a saved baseline report")
    ap.add_argument("--allow-errors", action="store_true",
                    help="measure the layout even if LaTeX reported (recoverable) errors")
    ap.add_argument("--verify-identical", action="store_true",
                    help="also build without floatcheck and check the page count is identical")
    args = ap.parse_args(argv)

    tex = os.path.abspath(args.tex)
    if not os.path.isfile(tex):
        print(f"[error] not found: {args.tex}", file=sys.stderr)
        return 2
    stem0 = os.path.splitext(os.path.basename(tex))[0]
    with open(tex, encoding="utf-8", errors="ignore") as f:
        src = f.read()
    if (re.search(r"\\bibliography\{", src) and not (args.bibtex or args.biber)
            and not os.path.exists(os.path.join(os.path.dirname(tex), stem0 + ".bbl"))):
        print(f"[warn] no {stem0}.bbl next to the paper and no --bibtex/--biber: the reference list "
              "will be empty, which changes page breaks", file=sys.stderr)

    limit, note = args.page_limit, None
    if args.venue:
        import json
        with open(os.path.join(HERE, "..", "references", "venues.json"), encoding="utf-8") as f:
            venues = json.load(f)["venues"]
        if args.venue not in venues:
            print(f"[error] unknown venue '{args.venue}'; choose from: {', '.join(venues)}", file=sys.stderr)
            return 2
        v = venues[args.venue]
        limit = limit or v.get("page_limit")
        tex_dir = os.path.dirname(tex)
        for cls in v.get("class_files", []):
            local = os.path.exists(os.path.join(tex_dir, cls))
            found = local or (shutil.which("kpsewhich") and subprocess.run(
                ["kpsewhich", cls], capture_output=True, text=True).stdout.strip())
            if not found:
                print(f"[warn] {cls} (venue {args.venue}) is not installed and not next to main.tex: a build "
                      f"with a stand-in class only ESTIMATES pages and float positions. Copy the official "
                      f"style files next to main.tex.", file=sys.stderr)
        if args.venue == "acl":
            note = ("ACL: the measured body includes Limitations/Ethics if they precede the references; "
                    "they do not count toward the limit, so the real body is shorter.")
    outdir = os.path.abspath(args.outdir) if args.outdir else tempfile.mkdtemp(prefix="floatcheck-")
    os.makedirs(outdir, exist_ok=True)
    stem, log = build(args, tex, True, outdir)
    aux = os.path.join(outdir, stem + ".aux")
    if not os.path.exists(aux) or "Fatal error occurred" in log or pages(log) is None:
        errs = re.findall(r"^(?:\S+:\d+: |! ).+$", log, re.M)[:5]
        print("[error] diagnostic build failed. First LaTeX errors:", file=sys.stderr)
        for e in errs or ["(no error lines found; see " + os.path.join(outdir, stem + ".log") + ")"]:
            print("   " + e, file=sys.stderr)
        print("Fix: compile the paper normally first; floatcheck needs a document that compiles.",
              file=sys.stderr)
        return 2
    latex_errors = re.findall(r"^(?:\S+\.tex:\d+: |! ).+$", log, re.M)
    if latex_errors and not args.allow_errors:
        print(f"[error] LaTeX reported {len(latex_errors)} error(s); a layout measured on a document with errors "
              f"is not the real layout. First errors:", file=sys.stderr)
        for e in latex_errors[:5]:
            print("   " + e, file=sys.stderr)
        print("Fix them (or pass --allow-errors to measure anyway).", file=sys.stderr)
        return 2

    if args.verify_identical:
        plain_dir = os.path.join(outdir, "_plain")
        os.makedirs(plain_dir, exist_ok=True)
        _, plain_log = build(args, tex, False, plain_dir)
        p1, p0 = pages(log), pages(plain_log)
        print(f"[verify] pages with floatcheck: {p1}, without: {p0} -> "
              f"{'identical' if p1 == p0 else 'DIFFERENT (report this; results may not reflect the real layout)'}")

    cl_args = [aux, "--log", os.path.join(outdir, stem + ".log")]
    if limit:
        cl_args += ["--page-limit", str(limit)]
    if note:
        cl_args += ["--budget-note", note]
    if args.save_baseline:
        cl_args += ["--save-baseline", args.save_baseline]
    if args.compare:
        cl_args += ["--compare", args.compare]
    rc = check_layout.main(cl_args)
    print(f"\n[build dir] {outdir}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
