#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5", "numpy>=1.21"]
# ///
"""Grouped bar chart with error bars (ablations, cross-backbone comparisons).

Input CSV, either raw runs or pre-aggregated:
    group,variant,seed,value        -> mean/std computed here
    group,variant,mean,std          -> used as given
`group` is the x-axis category (e.g. dataset), `variant` the bar within a group
(e.g. "Full model", "w/o PKM"). Order follows first appearance in the file.

    uv run plot_bar_ablation.py --data ablation.csv --ours "Full model" \
        --ylabel "Accuracy (%)" --annotate-delta --out fig_ablation.pdf

--annotate-delta writes each variant's difference to --ours above its bar
(computed here, in the unit of the data, e.g. percentage points).
Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure, series_styles  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "ablation_example.csv")


def load(path):
    """Return (groups, variants, stats) with stats[(g, v)] = (mean, std, n)."""
    import numpy as np
    if not os.path.exists(path):
        fail(f"data file not found: {path}")
    raw, given = OrderedDict(), {}
    groups, variants = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
        if "group" not in cols or "variant" not in cols:
            fail(f"{path}: need columns group,variant and either value or mean[,std]; got {reader.fieldnames}")
        aggregated = "mean" in cols
        if not aggregated and "value" not in cols:
            fail(f"{path}: need a 'value' column (raw runs) or 'mean'[,'std'] (aggregated)")
        for i, row in enumerate(reader, start=2):
            g, v = row[cols["group"]].strip(), row[cols["variant"]].strip()
            if g not in groups:
                groups.append(g)
            if v not in variants:
                variants.append(v)
            try:
                if aggregated:
                    std = float(row[cols["std"]]) if "std" in cols and row[cols["std"]].strip() else 0.0
                    given[(g, v)] = (float(row[cols["mean"]]), std, None)
                else:
                    raw.setdefault((g, v), []).append(float(row[cols["value"]]))
            except (TypeError, ValueError):
                fail(f"{path}:{i}: non-numeric value in row {row}")
    stats = dict(given)
    for key, vals in raw.items():
        stats[key] = (float(np.mean(vals)), float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0, len(vals))
    if not stats:
        fail(f"{path}: no data rows")
    return groups, variants, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--data", help="CSV with group,variant,seed,value or group,variant,mean,std")
    src.add_argument("--demo", action="store_true", help="plot the bundled example data (NOT for papers)")
    ap.add_argument("--out", required=True, help="output PDF path (a PNG preview is written next to it)")
    ap.add_argument("--ours", help="variant to highlight (blue); reference for --annotate-delta")
    ap.add_argument("--ylabel", default="value")
    ap.add_argument("--layout", choices=["single", "double", "onehalf"], default="single")
    ap.add_argument("--height", type=float)
    ap.add_argument("--ylim", type=float, nargs=2)
    ap.add_argument("--annotate-delta", action="store_true", help="label bars with the difference to --ours")
    ap.add_argument("--legend-cols", type=int, help="legend columns (default: number of variants, max 3)")
    ap.add_argument("--min-seeds", type=int, default=3)
    args = ap.parse_args(argv)

    groups, variants, stats = load(DEMO if args.demo else args.data)
    if args.demo:
        print("[warn] DEMO data -- never use this figure in a paper", file=sys.stderr)
    if args.ours and args.ours not in variants:
        fail(f"--ours '{args.ours}' not found; variants are: {variants}")
    if args.annotate_delta and not args.ours:
        fail("--annotate-delta needs --ours")
    missing = [(g, v) for g in groups for v in variants if (g, v) not in stats]
    if missing:
        print(f"[warn] missing bars (left empty): {missing}", file=sys.stderr)
    few = sorted({v for (g, v), (_, _, n) in stats.items() if n is not None and n < args.min_seeds})
    if few:
        print(f"[warn] fewer than {args.min_seeds} runs for {few}; state the number of seeds in the caption",
              file=sys.stderr)

    import numpy as np
    import matplotlib.pyplot as plt
    apply_style(args.layout, args.height or 2.3)
    fig, ax = plt.subplots()
    order = ([args.ours] if args.ours else []) + [v for v in variants if v != args.ours]
    styles = series_styles(order, args.ours)
    x = np.arange(len(groups))
    width = min(0.8 / len(order), 0.28)
    hatches = ["", "//", "..", "xx", "\\\\", "++"]
    for k, v in enumerate(order):
        means = [stats.get((g, v), (np.nan, 0, 0))[0] for g in groups]
        errs = [stats.get((g, v), (np.nan, 0, 0))[1] for g in groups]
        pos = x + (k - (len(order) - 1) / 2) * width
        bars = ax.bar(pos, means, width, yerr=errs, capsize=2.5, label=v, color=styles[v]["color"],
                      edgecolor="black", linewidth=0.6, hatch=hatches[k % len(hatches)],
                      error_kw={"elinewidth": 0.8})
        if args.annotate_delta and v != args.ours:
            for b, g, m, err in zip(bars, groups, means, errs):
                ref = stats.get((g, args.ours))
                if ref is None or np.isnan(m):
                    continue
                d = m - ref[0]
                # above the error bar, rotated so neighbouring labels never collide
                ax.annotate(f"{d:+.2f}", xy=(b.get_x() + b.get_width() / 2, m + (err or 0)),
                            xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                            fontsize=6.5, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel(args.ylabel)
    ax.grid(axis="x", visible=False)
    if args.ylim:
        ax.set_ylim(*args.ylim)
    else:
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + (0.22 if args.annotate_delta else 0.08) * (hi - lo))  # room for labels
    # legend above the axes (constrained layout reserves the space)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=args.legend_cols or min(len(order), 3),
              borderaxespad=0.2, handlelength=1.6, columnspacing=1.0)
    # rotate tick labels only if they actually overlap
    fig.canvas.draw()
    boxes = [lab.get_window_extent() for lab in ax.get_xticklabels()]
    if any(a.x1 > b.x0 for a, b in zip(boxes, boxes[1:])):
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
