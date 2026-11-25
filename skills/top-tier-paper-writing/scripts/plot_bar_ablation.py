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
    # before/after a treatment (e.g. a defense): one hue per group, change marked per pair
    uv run plot_bar_ablation.py --data defense.csv --paired "No defense" "With defense" \
        --ylabel "ASR" --venue acl --out fig_defense.pdf

--annotate-delta writes each variant's difference to --ours above its bar
(computed here, in the unit of the data, e.g. percentage points).
Error bars are drawn only where runs actually vary (never zero-width bars).
Bars keep the file's order (--order ours-first to put --ours first); vermilion is
used only for variants named in --adverse.
Exit codes: 0 ok, 2 bad input.
"""
import argparse
import csv
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure, series_styles, OKABE_ITO, BASELINE_COLORS  # noqa: E402

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
    ap.add_argument("--venue", help="venue profile from references/venues.json (sets the width)")
    ap.add_argument("--annotate-delta", action="store_true", help="label bars with the difference to --ours")
    ap.add_argument("--order", choices=["file", "ours-first"], default="file",
                    help="bar order within a group (default: order of first appearance in the file)")
    ap.add_argument("--adverse", nargs="+", default=[], metavar="VARIANT",
                    help="variants drawn in the attack/degradation colour (vermilion)")
    ap.add_argument("--paired", nargs=2, metavar=("BEFORE", "AFTER"),
                    help="before/after mode: one hue per group, BEFORE solid then AFTER light+hatched, "
                         "with the change marked on each pair")
    ap.add_argument("--legend-cols", type=int, help="legend columns (default: number of variants, max 3)")
    ap.add_argument("--min-seeds", type=int, default=3)
    args = ap.parse_args(argv)

    groups, variants, stats = load(DEMO if args.demo else args.data)
    if args.demo:
        print("[warn] DEMO data -- never use this figure in a paper", file=sys.stderr)
    for name in ([args.ours] if args.ours else []) + args.adverse + list(args.paired or []):
        if name not in variants:
            fail(f"variant '{name}' not found; variants are: {variants}")
    if args.annotate_delta and not args.ours:
        fail("--annotate-delta needs --ours (in --paired mode the change is always marked)")
    if args.paired:
        pairs = [g for g in groups if (g, args.paired[0]) in stats and (g, args.paired[1]) in stats]
        if not pairs:
            fail(f"--paired: no group has both '{args.paired[0]}' and '{args.paired[1]}'")
    missing = [(g, v) for g in groups for v in variants if (g, v) not in stats]
    if missing:
        print(f"[warn] missing bars (left empty): {missing}", file=sys.stderr)
    few = sorted({v for (g, v), (_, _, n) in stats.items() if n is not None and n < args.min_seeds})
    if few:
        print(f"[warn] fewer than {args.min_seeds} runs for {few}; state the number of runs in the caption",
              file=sys.stderr)

    import numpy as np
    import matplotlib.pyplot as plt
    apply_style(args.layout, args.height or 2.3, args.venue)
    fig, ax = plt.subplots()
    x = np.arange(len(groups))

    def errs_for(v):
        """Error bars only where there is real run-to-run variation (never zero-width bars)."""
        e = [stats.get((g, v), (np.nan, None, 0))[1] for g in groups]
        return [np.nan if (s is None or s == 0) else s for s in e]

    if not any(s not in (None, 0) for (_, _, s) in [(0, 0, st[1]) for st in stats.values()]):
        print("[note] no run-to-run variation in the data: error bars omitted; state the number of runs "
              "in the caption", file=sys.stderr)

    if args.paired:
        before, after = args.paired
        hues = [OKABE_ITO[c] for c in BASELINE_COLORS]
        width = 0.36
        for gi, g in enumerate(groups):
            hue = hues[gi % len(hues)]
            mb = stats.get((g, before), (np.nan, None, 0))
            ma = stats.get((g, after), (np.nan, None, 0))
            eb = errs_for(before)[gi]
            ea = errs_for(after)[gi]
            ax.bar(x[gi] - width / 2, mb[0], width, yerr=None if np.isnan(eb) else eb, capsize=2.5, color=hue,
                   edgecolor="black", linewidth=0.6, error_kw={"elinewidth": 0.8})
            ax.bar(x[gi] + width / 2, ma[0], width, yerr=None if np.isnan(ea) else ea, capsize=2.5, color=hue,
                   alpha=0.45, edgecolor="black", linewidth=0.6, hatch="///", error_kw={"elinewidth": 0.8})
            if not (np.isnan(mb[0]) or np.isnan(ma[0])):
                top = max(mb[0] + (0 if np.isnan(eb) else eb), ma[0] + (0 if np.isnan(ea) else ea))
                ax.annotate("", xy=(x[gi] + width / 2, ma[0]), xytext=(x[gi] - width / 2, mb[0]),
                            arrowprops=dict(arrowstyle="->", color="#333333", lw=0.9,
                                            connectionstyle="arc3,rad=-0.25"), zorder=6)
                ax.annotate(f"{ma[0] - mb[0]:+.2f}", xy=(x[gi], top), xytext=(0, 4), textcoords="offset points",
                            ha="center", va="bottom", fontsize=6.8, fontweight="bold")
        from matplotlib.patches import Patch
        handles = [Patch(facecolor="#888888", edgecolor="black", linewidth=0.6, label=before),
                   Patch(facecolor="#888888", alpha=0.45, edgecolor="black", linewidth=0.6, hatch="///",
                         label=after)]
        ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, borderaxespad=0.2)
        n_series = 2
    else:
        if args.order == "ours-first" and args.ours:
            order = [args.ours] + [v for v in variants if v != args.ours]
        else:
            order = list(variants)
        styles = series_styles(order, args.ours, tuple(args.adverse))
        width = min(0.8 / len(order), 0.28)
        hatches = ["", "//", "..", "xx", "\\\\", "++"]
        for k, v in enumerate(order):
            means = [stats.get((g, v), (np.nan, 0, 0))[0] for g in groups]
            errs = errs_for(v)
            pos = x + (k - (len(order) - 1) / 2) * width
            bars = ax.bar(pos, means, width, yerr=None if all(np.isnan(errs)) else errs, capsize=2.5, label=v,
                          color=styles[v]["color"], edgecolor="black", linewidth=0.6,
                          hatch=hatches[k % len(hatches)], error_kw={"elinewidth": 0.8})
            if args.annotate_delta and v != args.ours:
                for b, g, m, err in zip(bars, groups, means, errs):
                    ref = stats.get((g, args.ours))
                    if ref is None or np.isnan(m):
                        continue
                    ax.annotate(f"{m - ref[0]:+.2f}", xy=(b.get_x() + b.get_width() / 2,
                                                          m + (0 if np.isnan(err) else err)),
                                xytext=(0, 2), textcoords="offset points", ha="center", va="bottom",
                                fontsize=6.5, rotation=90)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=args.legend_cols or min(len(order), 3),
                  borderaxespad=0.2, handlelength=1.6, columnspacing=1.0)
        n_series = len(order)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel(args.ylabel)
    ax.grid(axis="x", visible=False)
    if args.ylim:
        ax.set_ylim(*args.ylim)
    else:
        lo, hi = ax.get_ylim()
        room = 0.22 if (args.annotate_delta or args.paired) else 0.08
        ax.set_ylim(lo, hi + room * (hi - lo))  # room for labels
    # rotate tick labels only if they actually overlap
    fig.canvas.draw()
    boxes = [lab.get_window_extent() for lab in ax.get_xticklabels()]
    if any(a.x1 > b.x0 for a, b in zip(boxes, boxes[1:])):
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right", rotation_mode="anchor")
    del n_series
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
