#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5", "numpy>=1.21"]
# ///
"""Line plot of mean +/- std across seeds (convergence, sensitivity, two-phase tests).

Input: long-format CSV with columns  method,x,seed,value  (seed may be omitted
when there is one run per point). Mean and std are computed here -- never by hand.

    uv run plot_data_curves.py --data curves.csv --ours "FedPE (Ours)" \
        --xlabel "Communication rounds" --ylabel "Test accuracy (%)" --out fig_conv.pdf
    # sensitivity sweep: mark the best x of our method
    uv run plot_data_curves.py --data sweep.csv --ours Ours --mark-best max --out fig_sens.pdf
    # two-phase stress test: dashed separator at x=100
    uv run plot_data_curves.py --data stress.csv --ours Ours --phase-split 100 --out fig_phase.pdf

Exit codes: 0 ok, 2 bad input. Warns (stderr) when a series has < 3 seeds.
"""
import argparse
import csv
import os
import sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure, series_styles, OKABE_ITO  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "curves_example.csv")


def load(path):
    if not os.path.exists(path):
        fail(f"data file not found: {path}")
    series = OrderedDict()   # method -> {x: [values]}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        for need in ("method", "x", "value"):
            if need not in cols:
                fail(f"{path}: missing column '{need}' (need method,x,[seed,]value; got {reader.fieldnames})")
        for i, row in enumerate(reader, start=2):
            try:
                m = row[cols["method"]].strip()
                x = float(row[cols["x"]])
                v = float(row[cols["value"]])
            except (TypeError, ValueError):
                fail(f"{path}:{i}: non-numeric x/value in row {row}")
            series.setdefault(m, defaultdict(list))[x].append(v)
    if not series:
        fail(f"{path}: no data rows")
    return series


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", help="long-format CSV: method,x,seed,value")
    src.add_argument("--demo", action="store_true", help="plot the bundled example data (NOT for papers)")
    ap.add_argument("--out", required=True, help="output PDF path (a PNG preview is written next to it)")
    ap.add_argument("--ours", help="method name to highlight (blue, solid, drawn on top)")
    ap.add_argument("--xlabel", default="x")
    ap.add_argument("--ylabel", default="value")
    ap.add_argument("--layout", choices=["single", "double", "onehalf"], default="single")
    ap.add_argument("--height", type=float, help="figure height in inches")
    ap.add_argument("--xlim", type=float, nargs=2)
    ap.add_argument("--ylim", type=float, nargs=2)
    ap.add_argument("--legend", default="best", help="matplotlib legend location")
    ap.add_argument("--markers", type=int, default=10, help="approximate number of markers per line")
    ap.add_argument("--phase-split", type=float, help="x value of a Phase I / Phase II separator")
    ap.add_argument("--mark-best", choices=["max", "min"], help="annotate the best mean of --ours")
    ap.add_argument("--min-seeds", type=int, default=3)
    args = ap.parse_args(argv)

    data = load(DEMO if args.demo else args.data)
    if args.demo:
        print("[warn] DEMO data -- never use this figure in a paper", file=sys.stderr)
    if args.ours and args.ours not in data:
        fail(f"--ours '{args.ours}' not found; methods are: {list(data)}")

    import numpy as np
    import matplotlib.pyplot as plt
    apply_style(args.layout, args.height)
    fig, ax = plt.subplots()
    styles = series_styles(list(data), args.ours)

    for method, points in data.items():
        xs = np.array(sorted(points))
        runs = [points[x] for x in xs]
        mean = np.array([np.mean(r) for r in runs])
        std = np.array([np.std(r, ddof=1) if len(r) > 1 else 0.0 for r in runs])
        n_seeds = min(len(r) for r in runs)
        if n_seeds < args.min_seeds:
            print(f"[warn] '{method}': only {n_seeds} run(s) at some x; state the number of seeds "
                  f"in the caption (rule: >= {args.min_seeds})", file=sys.stderr)
        st = styles[method]
        every = max(1, len(xs) // max(args.markers, 1))
        ax.plot(xs, mean, label=method, color=st["color"], linestyle=st["linestyle"],
                marker=st["marker"], markevery=every, zorder=st["zorder"])
        if n_seeds > 1:
            ax.fill_between(xs, mean - std, mean + std, color=st["color"],
                            alpha=0.18 if method == args.ours else 0.12, linewidth=0, zorder=st["zorder"] - 1)
        if args.mark_best and method == args.ours:
            idx = int(np.argmax(mean) if args.mark_best == "max" else np.argmin(mean))
            ax.annotate(f"{xs[idx]:g}", xy=(xs[idx], mean[idx]), xytext=(0, 8), textcoords="offset points",
                        ha="center", fontsize=7.5, fontweight="bold", color=OKABE_ITO["blue"])
            ax.plot([xs[idx]], [mean[idx]], marker="*", markersize=9, color=OKABE_ITO["blue"], zorder=6)

    if args.phase_split is not None:
        ax.axvline(args.phase_split, color="#555555", linestyle="--", linewidth=0.9)
        tr = ax.get_xaxis_transform()   # x in data units, y in axes units
        ax.text(args.phase_split, 0.04, "  Phase II", transform=tr, ha="left", va="bottom",
                fontsize=7.5, color="#555555")
        ax.text(args.phase_split, 0.04, "Phase I  ", transform=tr, ha="right", va="bottom",
                fontsize=7.5, color="#555555")

    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    if args.xlim:
        ax.set_xlim(*args.xlim)
    if args.ylim:
        ax.set_ylim(*args.ylim)
    handles, labels = ax.get_legend_handles_labels()
    if args.ours in labels:   # put ours first in the legend
        i = labels.index(args.ours)
        handles.insert(0, handles.pop(i))
        labels.insert(0, labels.pop(i))
    ax.legend(handles, labels, loc=args.legend)
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
