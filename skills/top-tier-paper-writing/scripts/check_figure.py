#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Check figure PDFs for publication readiness (stdlib only).

For each PDF:
  F1  page width matches a column format -> error. Default (IEEE): single 3.3-3.5 in,
      double 6.8-7.0 in (1.5-column 4.8-5.2 in with --allow-onehalf). With
      --venue NAME the venue's column and text widths from references/venues.json
      are used (+/- 0.1 in).
  F2  no Type 3 fonts (bitmap-like, rejected by IEEE PDF eXpress)    -> error
  F3  fonts are embedded (every font has a FontFile stream)          -> warning
  F4  the file is a vector PDF (not a single embedded raster image)  -> warning

    uv run check_figure.py fig1.pdf fig2.pdf
    uv run check_figure.py --venue acl figs/*.pdf
    uv run check_figure.py figs/*.pdf --json report.json

Exit codes: 0 all pass, 1 at least one error, 2 usage error.
"""
import argparse
import json
import os
import re
import sys
import zlib

RANGES = {"single": (3.3, 3.5), "double": (6.8, 7.0), "onehalf": (4.8, 5.2)}


def pdf_bytes(path):
    """Raw bytes plus the decompressed content of every Flate stream."""
    with open(path, "rb") as f:
        raw = f.read()
    if not raw.startswith(b"%PDF"):
        raise ValueError("not a PDF file")
    chunks = [raw]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S):
        try:
            chunks.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    return raw, b"\n".join(chunks)


def venue_ranges(name):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "venues.json")
    with open(path, encoding="utf-8") as f:
        venues = json.load(f)["venues"]
    if name not in venues:
        sys.exit(f"[error] unknown venue '{name}'; choose from: {', '.join(venues)}")
    v = venues[name]
    out = {"single": (v["column_width_in"] - 0.1, v["column_width_in"] + 0.1),
           "double": (v["text_width_in"] - 0.1, v["text_width_in"] + 0.1),
           "onehalf": (0.6 * v["text_width_in"], 0.85 * v["text_width_in"])}
    return out


def check(path, allow_onehalf, ranges=None):
    ranges = ranges or RANGES
    res = {"file": path, "errors": [], "warnings": []}
    try:
        raw, everything = pdf_bytes(path)
    except (OSError, ValueError) as e:
        res["errors"].append(f"cannot read: {e}")
        return res
    boxes = re.findall(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", everything)
    pages = len(re.findall(rb"/Type\s*/Page(?!s)", everything))
    if not boxes:
        res["errors"].append("no MediaBox found")
    else:
        x0, y0, x1, y1 = (float(v) for v in boxes[0])
        w, h = (x1 - x0) / 72.0, (y1 - y0) / 72.0
        res["width_in"], res["height_in"] = round(w, 3), round(h, 3)
        fmt = next((k for k, (lo, hi) in ranges.items()
                    if lo - 0.005 <= w <= hi + 0.005 and (k != "onehalf" or allow_onehalf)), None)
        res["format"] = fmt
        if fmt is None:
            want = ", ".join(f"{k} {lo:.2f}-{hi:.2f}" for k, (lo, hi) in ranges.items()
                             if k != "onehalf" or allow_onehalf)
            res["errors"].append(f"F1 width {w:.2f} in matches no column format ({want}); regenerate with "
                                 f"--layout (and --venue)")
    if pages > 1:
        res["warnings"].append(f"{pages} pages; a figure PDF should have exactly one")

    fonts = re.findall(rb"/Type\s*/Font\b(.*?)(?:>>)", everything, re.S)
    subtypes = re.findall(rb"/Subtype\s*/(Type3|Type1C?|TrueType|Type0|CIDFontType[02]|MMType1)", everything)
    names = sorted({n.decode("latin-1") for n in re.findall(rb"/BaseFont\s*/([A-Za-z0-9+#_.,-]+)", everything)})
    res["fonts"] = names
    if b"Type3" in subtypes:
        res["errors"].append("F2 Type 3 fonts present; set pdf.fonttype=42 (pubstyle.py does) and regenerate")
    font_files = len(re.findall(rb"/FontFile[23]?\b", everything))
    simple_fonts = len([s for s in subtypes if s in (b"TrueType", b"Type1", b"Type1C", b"MMType1",
                                                     b"CIDFontType0", b"CIDFontType2")])
    if simple_fonts and font_files < simple_fonts:
        res["warnings"].append(f"F3 only {font_files} of {simple_fonts} fonts look embedded "
                               "(standard-14 fonts may be referenced, not embedded)")
    images = len(re.findall(rb"/Subtype\s*/Image", everything))
    vector_ops = len(re.findall(rb"\b(?:re|l|c)\s*\n", everything))
    if images and vector_ops < 10 and not fonts:
        res["warnings"].append("F4 looks like a raster image wrapped in a PDF; export the figure as vector")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--allow-onehalf", action="store_true", help="accept 1.5-column widths")
    ap.add_argument("--venue", help="check widths against this venue (references/venues.json)")
    ap.add_argument("--json", help="write the report to this path")
    args = ap.parse_args(argv)
    ranges = venue_ranges(args.venue) if args.venue else None
    report = [check(p, args.allow_onehalf, ranges) for p in args.pdfs]
    n_err = 0
    for r in report:
        status = "FAIL" if r["errors"] else ("WARN" if r["warnings"] else " ok ")
        size = f"{r.get('width_in', '?')} x {r.get('height_in', '?')} in" if "width_in" in r else ""
        print(f"[{status}] {r['file']}  {size}  {r.get('format') or ''}")
        for m in r["errors"] + r["warnings"]:
            print(f"        - {m}")
        n_err += bool(r["errors"])
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
