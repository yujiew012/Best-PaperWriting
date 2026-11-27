#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Evidence numbers for results paragraphs, computed from data (stdlib only).

Input: long CSV  setting,method,value[,seed]   (setting = dataset/partition/attack/...)
Runs with the same (setting, method) are averaged; std is reported when >1 run.

Method papers ("ours vs. baselines"):
    uv run result_stats.py --data results.csv --ours FedPE
    uv run result_stats.py --data results.csv --ours FedPE --lower-better          # e.g. latency
Measurement papers (no "ours"; e.g. setting = input condition, method = model):
    uv run result_stats.py --data asr.csv                                            # describe each setting
    uv run result_stats.py --data asr.csv --drop "300 DPI" "60 DPI"                  # condition change per model

With --ours: per setting our mean, best baseline, margin, rank; then the margin
range, the hardest setting and EVERY setting where ours is not best.
Without --ours: per setting the min / max / mean / spread and which method is where.
--drop A B: each method's change from setting A to B, plus a summary -- how many
methods increase / decrease, the range of changes, and the EXCEPTIONS whose
change goes against the majority (report those honestly).
--json writes everything for traceability ("number -> source").
Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import json
import os
import statistics
import sys
from collections import OrderedDict


def load(path):
    if not os.path.exists(path):
        print(f"[error] data file not found: {path}", file=sys.stderr)
        sys.exit(2)
    runs = OrderedDict()
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (r.fieldnames or [])}
        for need in ("setting", "method", "value"):
            if need not in cols:
                print(f"[error] missing column '{need}' (need setting,method,value[,seed])", file=sys.stderr)
                sys.exit(2)
        for i, row in enumerate(r, start=2):
            try:
                v = float(row[cols["value"]])
            except (TypeError, ValueError):
                print(f"[error] {path}:{i}: non-numeric value {row[cols['value']]!r}", file=sys.stderr)
                sys.exit(2)
            runs.setdefault(row[cols["setting"]].strip(), OrderedDict()).setdefault(
                row[cols["method"]].strip(), []).append(v)
    return runs


def describe(runs, report, nd, sign):
    """Measurement mode: per setting, the spread across methods (no 'ours')."""
    print(f"{'setting':24s} {'n':>3s} {'min':>22s} {'max':>22s} {'mean':>8s} {'spread':>8s}")
    for setting, methods in runs.items():
        means = {m: statistics.mean(v) for m, v in methods.items()}
        lo = min(means, key=means.get)
        hi = max(means, key=means.get)
        mean = statistics.mean(means.values())
        report["settings"].append({"setting": setting, "n_methods": len(means), "min": means[lo], "min_method": lo,
                                   "max": means[hi], "max_method": hi, "mean": mean,
                                   "spread": means[hi] - means[lo], "values": means})
        print(f"{setting:24s} {len(means):3d} {lo[:12] + ' ' + fmt(means[lo], nd):>22s} "
              f"{hi[:12] + ' ' + fmt(means[hi], nd):>22s} {fmt(mean, nd):>8s} {fmt(means[hi] - means[lo], nd):>8s}")


def fmt(x, nd):
    return f"{_zero(x, nd):.{nd}f}"


def sfmt(x, nd):
    """Signed format without a negative zero ("-0.00" reads as a loss that is not there)."""
    return f"{_zero(x, nd):+.{nd}f}"


def _zero(x, nd):
    return 0.0 if round(x, nd) == 0 else x


def auto_digits(runs):
    """Enough decimals to show two significant digits of the smallest non-zero value (2..6).

    A fixed two decimals hides every difference between rates such as 0.001 and 0.002."""
    import math
    values = [abs(v) for methods in runs.values() for vals in methods.values() for v in vals if v]
    if not values:
        return 2
    return max(2, min(6, 1 - math.floor(math.log10(min(values)))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ours", help="our method in the 'method' column (omit for measurement papers)")
    ap.add_argument("--lower-better", action="store_true", help="smaller values are better")
    ap.add_argument("--drop", nargs=2, metavar=("BEFORE", "AFTER"), help="per-method change between two settings")
    ap.add_argument("--digits", type=int, default=None,
                    help="decimals in the printed report (default: enough for the smallest non-zero value)")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    runs = load(args.data)
    nd = args.digits if args.digits is not None else auto_digits(runs)
    sign = -1 if args.lower_better else 1
    report = {"source": os.path.abspath(args.data), "ours": args.ours,
              "direction": "lower is better" if args.lower_better else "higher is better", "settings": []}

    methods_all = sorted({m for ms in runs.values() for m in ms})
    if args.ours and args.ours not in methods_all:
        print(f"[error] --ours '{args.ours}' is not a method in {args.data}; methods: {', '.join(methods_all)}",
              file=sys.stderr)
        return 2
    print(f"source: {args.data}  ({report['direction']})\n")
    if not args.ours:
        describe(runs, report, nd, sign)
    else:
        print(f"{'setting':24s} {'ours':>14s} {'best baseline':>24s} {'margin':>8s} rank")
    for setting, methods in (runs.items() if args.ours else []):
        if args.ours not in methods:
            print(f"{setting:24s} (ours missing)")
            continue
        stats = {m: (statistics.mean(v), statistics.stdev(v) if len(v) > 1 else None, len(v))
                 for m, v in methods.items()}
        ranked = sorted(stats, key=lambda m: sign * stats[m][0], reverse=True)
        base = [m for m in ranked if m != args.ours]
        o = stats[args.ours]
        entry = {"setting": setting, "ours_mean": o[0], "ours_std": o[1], "runs": o[2],
                 # rank = 1 + methods strictly better (ties do not depend on the CSV row order)
                 "rank": 1 + sum(1 for m in ranked if m != args.ours and sign * stats[m][0] > sign * o[0] + 1e-12),
                 "n_methods": len(ranked)}
        if base:
            b = base[0]
            entry.update(best_baseline=b, best_baseline_mean=stats[b][0], margin=sign * (o[0] - stats[b][0]))
        report["settings"].append(entry)
        ours_s = fmt(o[0], nd) + (f"±{fmt(o[1], nd)}" if o[1] is not None else "")
        bb = f"{entry.get('best_baseline', '-')} {fmt(entry['best_baseline_mean'], nd)}" if base else "-"
        mg = sfmt(entry["margin"], nd) if base else "-"
        print(f"{setting:24s} {ours_s:>14s} {bb:>24s} {mg:>8s} {entry['rank']}/{entry['n_methods']}")

    with_margin = [s for s in report["settings"] if "margin" in s]
    if with_margin:
        margins = [s["margin"] for s in with_margin]
        hardest = min(report["settings"], key=lambda s: sign * s["ours_mean"])
        not_best = [s["setting"] for s in report["settings"] if s["rank"] != 1]
        tied = [s["setting"] for s in with_margin if abs(s["margin"]) <= 1e-12]
        summary = {"margin_min": min(margins), "margin_max": max(margins),
                   "hardest_setting": hardest["setting"], "ours_not_best_in": not_best, "ours_tied_best_in": tied}
        report["summary"] = summary
        print(f"\nmargin over best baseline: {sfmt(min(margins), nd)} to {sfmt(max(margins), nd)}"
              f"  (positive = ours better)")
        print(f"hardest setting for ours: {hardest['setting']} ({fmt(hardest['ours_mean'], nd)})")
        print("ours is NOT best in: " + (", ".join(not_best) if not_best else "none")
              + ("   <- must be reported, not hidden" if not_best else ""))
        if tied:
            print("ours only TIES the best baseline in: " + ", ".join(tied) + "   <- do not call these wins")

    if args.drop:
        a, b = args.drop
        if a not in runs or b not in runs:
            print(f"[error] --drop settings must exist; have {list(runs)}", file=sys.stderr)
            return 2
        print(f"\nchange from '{a}' to '{b}':")
        report["drop"] = {}
        for m in runs[a]:
            if m in runs[b]:
                va, vb = statistics.mean(runs[a][m]), statistics.mean(runs[b][m])
                report["drop"][m] = {"before": va, "after": vb, "abs": vb - va,
                                     "rel_pct": (vb - va) / va * 100 if va else None,
                                     "ratio": vb / va if va else None}
                rel = f"{(vb - va) / va * 100:+.{nd}f}%" if va else "n/a"
                print(f"  {m:20s} {fmt(va, nd)} -> {fmt(vb, nd)}  ({sfmt(vb - va, nd)} abs, {rel} rel)")
        missing = [m for m in set(runs[a]) ^ set(runs[b])]
        if missing:
            print(f"  (only in one of the two settings, skipped: {', '.join(sorted(missing))})")
        ch = {m: d["abs"] for m, d in report["drop"].items()}
        if ch:
            up = sorted(m for m, v in ch.items() if v > 0)
            down = sorted(m for m, v in ch.items() if v < 0)
            same = sorted(m for m, v in ch.items() if v == 0)
            majority = "increase" if len(up) >= len(down) else "decrease"
            exceptions = (down + same) if majority == "increase" else (up + same)
            rels = [d["rel_pct"] for d in report["drop"].values() if d["rel_pct"] is not None]
            report["drop_summary"] = {"increase": up, "decrease": down, "unchanged": same, "majority": majority,
                                      "abs_min": min(ch.values()), "abs_max": max(ch.values()),
                                      "rel_pct_min": min(rels) if rels else None,
                                      "rel_pct_max": max(rels) if rels else None, "exceptions": exceptions}
            print(f"\nsummary: {len(up)} increase, {len(down)} decrease, {len(same)} unchanged "
                  f"(of {len(ch)}); change {sfmt(min(ch.values()), nd)} to {sfmt(max(ch.values()), nd)} abs"
                  + (f", {min(rels):+.{nd}f}% to {max(rels):+.{nd}f}% rel" if rels else ""))
            print("against the majority (" + majority + "): "
                  + (", ".join(m + (" (unchanged)" if m in same else "") for m in exceptions) if exceptions else "none")
                  + ("   <- must be reported, not hidden" if exceptions else ""))
    # each method's mean over the settings it appears in (source for "on average across N settings" claims)
    per_method = {}
    for setting, methods in runs.items():
        for m, v in methods.items():
            per_method.setdefault(m, []).append(statistics.mean(v))
    report["method_mean_over_settings"] = {m: {"mean": statistics.mean(v), "n_settings": len(v)}
                                           for m, v in per_method.items()}
    if len(runs) > 1:
        print("\nmean over settings: " + ", ".join(f"{m} {fmt(d['mean'], nd)} (n={d['n_settings']})"
                                               for m, d in report["method_mean_over_settings"].items()))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
