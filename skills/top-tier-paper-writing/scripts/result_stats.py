#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""Evidence numbers for results paragraphs, computed from data (stdlib only).

Input: long CSV  setting,method,value[,seed]   (setting = dataset/partition/attack/...)
Runs with the same (setting, method) are averaged; std is reported when >1 run.

    uv run result_stats.py --data results.csv --ours FedPE
    uv run result_stats.py --data results.csv --ours FedPE --lower-better          # e.g. latency, ASR
    uv run result_stats.py --data stress.csv --ours FedPE --drop "Phase I" "Phase II"

Prints, per setting: our mean, best baseline, margin, rank; then a summary with
the margin range, the hardest setting, and EVERY setting where ours is not best
(report those honestly). --drop A B adds each method's change from setting A to B.
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
        sys.exit(f"[error] data file not found: {path}")
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


def fmt(x, nd):
    return f"{x:.{nd}f}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--ours", required=True, help="name of our method in the 'method' column")
    ap.add_argument("--lower-better", action="store_true", help="smaller values are better")
    ap.add_argument("--drop", nargs=2, metavar=("BEFORE", "AFTER"), help="per-method change between two settings")
    ap.add_argument("--digits", type=int, default=2)
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    runs = load(args.data)
    nd, sign = args.digits, (-1 if args.lower_better else 1)
    report = {"source": os.path.abspath(args.data), "ours": args.ours,
              "direction": "lower is better" if args.lower_better else "higher is better", "settings": []}

    print(f"source: {args.data}  ({report['direction']})\n")
    print(f"{'setting':24s} {'ours':>14s} {'best baseline':>24s} {'margin':>8s} rank")
    for setting, methods in runs.items():
        if args.ours not in methods:
            print(f"{setting:24s} (ours missing)")
            continue
        stats = {m: (statistics.mean(v), statistics.stdev(v) if len(v) > 1 else None, len(v))
                 for m, v in methods.items()}
        ranked = sorted(stats, key=lambda m: sign * stats[m][0], reverse=True)
        base = [m for m in ranked if m != args.ours]
        o = stats[args.ours]
        entry = {"setting": setting, "ours_mean": o[0], "ours_std": o[1], "runs": o[2],
                 "rank": ranked.index(args.ours) + 1, "n_methods": len(ranked)}
        if base:
            b = base[0]
            entry.update(best_baseline=b, best_baseline_mean=stats[b][0], margin=sign * (o[0] - stats[b][0]))
        report["settings"].append(entry)
        ours_s = fmt(o[0], nd) + (f"±{fmt(o[1], nd)}" if o[1] is not None else "")
        bb = f"{entry.get('best_baseline', '-')} {fmt(entry['best_baseline_mean'], nd)}" if base else "-"
        mg = f"{entry['margin']:+.{nd}f}" if base else "-"
        print(f"{setting:24s} {ours_s:>14s} {bb:>24s} {mg:>8s} {entry['rank']}/{entry['n_methods']}")

    with_margin = [s for s in report["settings"] if "margin" in s]
    if with_margin:
        margins = [s["margin"] for s in with_margin]
        hardest = min(report["settings"], key=lambda s: sign * s["ours_mean"])
        not_best = [s["setting"] for s in report["settings"] if s["rank"] != 1]
        summary = {"margin_min": min(margins), "margin_max": max(margins),
                   "hardest_setting": hardest["setting"], "ours_not_best_in": not_best}
        report["summary"] = summary
        print(f"\nmargin over best baseline: {min(margins):+.{nd}f} to {max(margins):+.{nd}f}"
              f"  (positive = ours better)")
        print(f"hardest setting for ours: {hardest['setting']} ({fmt(hardest['ours_mean'], nd)})")
        print("ours is NOT best in: " + (", ".join(not_best) if not_best else "none")
              + ("   <- must be reported, not hidden" if not_best else ""))

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
                                     "rel_pct": (vb - va) / va * 100 if va else None}
                rel = f"{(vb - va) / va * 100:+.{nd}f}%" if va else "n/a"
                print(f"  {m:20s} {fmt(va, nd)} -> {fmt(vb, nd)}  ({vb - va:+.{nd}f} abs, {rel} rel)")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
