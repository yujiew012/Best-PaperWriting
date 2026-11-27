#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5", "numpy>=1.21"]
# ///
"""Line plot of mean +/- std across seeds (convergence, sensitivity, two-phase tests).

Input: long-format CSV with columns  method,x,seed,value  (seed may be omitted
when there is one run per point). Mean and std are computed here -- never by hand.
An optional 'panel' column produces a grid of small multiples (shared axes, one
legend), e.g. one panel per model.

    uv run plot_data_curves.py --data curves.csv --ours "FedPE (Ours)" \
        --xlabel "Communication rounds" --ylabel "Test accuracy (%)" --out fig_conv.pdf
    # sensitivity sweep: mark the best x of our method
    uv run plot_data_curves.py --data sweep.csv --ours Ours --mark-best max --out fig_sens.pdf
    # two-phase stress test: dashed separator at x=100
    uv run plot_data_curves.py --data stress.csv --ours Ours --phase-split 100 --out fig_phase.pdf
    # panels that sweep different parameters: --free-x, one x label per panel
    uv run plot_data_curves.py --data two_sweeps.csv --free-x --xlabel "Noise level c" "Fraction rho" --out fig.pdf
    # small multiples on a reversed log axis with a shaded, labelled regime
    uv run plot_data_curves.py --data sweep.csv --logx --invert-x --band 30 90 "vulnerable band" \
        --ncols 4 --venue acl --xlabel "Resolution (DPI)" --ylabel "ASR" --out fig_sweep.pdf

Exit codes: 0 ok, 2 bad input. Warns (stderr) when a series has < 3 seeds.
"""
import argparse
import csv
import os
import sys
from collections import OrderedDict, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure, series_styles, OKABE_ITO  # noqa: E402

BAND_SHADES = ["#BBBBBB", "#9FC9E3", "#F2D49B"]
DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "curves_example.csv")


def load(path):
    if not os.path.exists(path):
        fail(f"data file not found: {path}")
    series = OrderedDict()   # panel -> method -> {x: [values]}  (panel "" when there is no panel column)
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
            panel = row[cols["panel"]].strip() if "panel" in cols else ""
            series.setdefault(panel, OrderedDict()).setdefault(m, defaultdict(list))[x].append(v)
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
    ap.add_argument("--xlabel", nargs="+", default=["x"],
                    help="x-axis label; with --free-x one label per panel (in panel order) is allowed")
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
    ap.add_argument("--venue", help="venue profile from references/venues.json (sets the width)")
    ap.add_argument("--adverse", nargs="+", default=[], metavar="METHOD",
                    help="series drawn in the attack/degradation colour (vermilion)")
    ap.add_argument("--logx", action="store_true", help="logarithmic x axis")
    ap.add_argument("--invert-x", action="store_true", help="x decreases to the right (e.g. resolution)")
    ap.add_argument("--band", nargs=3, action="append", metavar=("X1", "X2", "LABEL"), default=[],
                    help="shade the x-range [X1, X2] and label it (repeatable)")
    ap.add_argument("--free-x", action="store_true",
                    help="panels keep their own x axis (panels that sweep different parameters)")
    ap.add_argument("--ncols", type=int, default=0,
                    help="panels per row when the CSV has a 'panel' column (default: up to 4)")
    args = ap.parse_args(argv)

    data = load(DEMO if args.demo else args.data)
    if args.demo:
        print("[warn] DEMO data -- never use this figure in a paper", file=sys.stderr)
    methods = list(OrderedDict.fromkeys(m for panel in data.values() for m in panel))
    for name in ([args.ours] if args.ours else []) + args.adverse:
        if name not in methods:
            fail(f"'{name}' not found; methods are: {methods}")

    import math
    if args.logx:
        bad = sorted({x for pdata in data.values() for pts in pdata.values() for x in pts if x <= 0})
        if bad:
            fail(f"--logx needs x > 0; found x = {bad} (a log axis would silently drop these points)")
    import numpy as np
    import matplotlib.pyplot as plt
    panels = list(data)
    n = len(panels)
    ncols = args.ncols or min(n, 4)
    nrows = math.ceil(n / ncols)
    layout = args.layout if n == 1 else ("double" if args.layout == "single" else args.layout)
    fw, fh = apply_style(layout, args.height or (2.4 if n == 1 else 1.7 * nrows + 0.5), args.venue)
    if len(args.xlabel) not in (1, n):
        fail(f"--xlabel takes one label or one per panel ({n}); got {len(args.xlabel)}")
    if len(args.xlabel) > 1 and not args.free_x:
        fail("one x label per panel needs --free-x (panels with a shared x axis share its label)")
    fig, axes = plt.subplots(nrows, ncols, sharex=not args.free_x, sharey=True, squeeze=False)
    styles = series_styles(methods, args.ours, tuple(args.adverse))
    warned = set()

    for pi, panel in enumerate(panels):
        ax = axes[pi // ncols][pi % ncols]
        for method, points in data[panel].items():
            xs = np.array(sorted(points))
            runs = [points[x] for x in xs]
            mean = np.array([np.mean(r) for r in runs])
            std = np.array([np.std(r, ddof=1) if len(r) > 1 else 0.0 for r in runs])
            n_seeds = min(len(r) for r in runs)
            if n_seeds < args.min_seeds and method not in warned:
                warned.add(method)
                print(f"[warn] '{method}': only {n_seeds} run(s) at some x; state the number of runs "
                      f"in the caption (rule: >= {args.min_seeds})", file=sys.stderr)
            st = styles[method]
            every = max(1, len(xs) // max(args.markers, 1))
            ax.plot(xs, mean, label=method, color=st["color"], linestyle=st["linestyle"],
                    marker=st["marker"], markevery=every, zorder=st["zorder"])
            if n_seeds > 1 and std.max() > 0:      # never draw a zero-width band
                ax.fill_between(xs, mean - std, mean + std, color=st["color"],
                                alpha=0.18 if method == args.ours else 0.12, linewidth=0, zorder=st["zorder"] - 1)
            if args.mark_best and method == args.ours:
                idx = int(np.argmax(mean) if args.mark_best == "max" else np.argmin(mean))
                ax.annotate(f"{xs[idx]:g}", xy=(xs[idx], mean[idx]), xytext=(0, 8), textcoords="offset points",
                            ha="center", fontsize=7.5, fontweight="bold", color=OKABE_ITO["blue"])
                ax.plot([xs[idx]], [mean[idx]], marker="*", markersize=9, color=OKABE_ITO["blue"], zorder=6)
        tr = ax.get_xaxis_transform()        # x in data units, y in axes units
        for bi, (x1, x2, label) in enumerate(args.band):
            x1, x2 = float(x1), float(x2)
            # band labels go into the legend (as a shaded swatch) so they never sit on top of data
            ax.axvspan(min(x1, x2), max(x1, x2), color=BAND_SHADES[bi % len(BAND_SHADES)], alpha=0.35,
                       linewidth=0, zorder=0, label=f"__band{bi}" if pi else (label or f"x in [{x1:g}, {x2:g}]"))
        if args.phase_split is not None:
            ax.axvline(args.phase_split, color="#555555", linestyle="--", linewidth=0.9)
            ax.text(args.phase_split, 0.04, "  Phase II", transform=tr, ha="left", va="bottom",
                    fontsize=7.5, color="#555555")
            ax.text(args.phase_split, 0.04, "Phase I  ", transform=tr, ha="right", va="bottom",
                    fontsize=7.5, color="#555555")
        if panel:
            ax.set_title(panel, fontsize=8.5)
        if args.logx:
            ax.set_xscale("log")
            # plain labels at the data's own x values; no minor-tick labels (they collide on log axes)
            from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
            xs_all = sorted({x for m in data[panel].values() for x in m})
            if len(xs_all) > 8:                # thin out, but always keep both ends
                step = math.ceil(len(xs_all) / 8)
                xs_all = sorted(set(xs_all[::step]) | {xs_all[0], xs_all[-1]})
            ax.xaxis.set_major_locator(FixedLocator(xs_all))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
            ax.xaxis.set_minor_formatter(NullFormatter())
        if args.free_x or pi // ncols == nrows - 1:
            ax.set_xlabel(args.xlabel[pi] if len(args.xlabel) > 1 else args.xlabel[0])
        if pi % ncols == 0:
            ax.set_ylabel(args.ylabel)
    for k in range(n, nrows * ncols):        # hide unused panels
        axes[k // ncols][k % ncols].axis("off")
    ax0 = axes[0][0]
    x_axes = [axes[k // ncols][k % ncols] for k in range(n)] if args.free_x else [ax0]
    for ax in x_axes:
        if args.xlim:
            ax.set_xlim(*args.xlim)
        if args.invert_x:
            ax.invert_xaxis()                # shared x: inverting the first panel inverts every panel
    if args.ylim:
        ax0.set_ylim(*args.ylim)
    handles, labels = [], []                 # every panel: a method may appear only in later panels
    for k in range(n):
        for h, lab in zip(*axes[k // ncols][k % ncols].get_legend_handles_labels()):
            if lab not in labels:
                handles.append(h)
                labels.append(lab)
    if args.ours in labels:   # put ours first in the legend
        i = labels.index(args.ours)
        handles.insert(0, handles.pop(i))
        labels.insert(0, labels.pop(i))
    if n == 1:
        ax0.legend(handles, labels, loc=args.legend)
    else:
        try:                                   # matplotlib >= 3.7 reserves the space itself
            fig.legend(handles, labels, loc="outside upper center", ncol=min(len(labels), 5))
        except ValueError:
            fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=min(len(labels), 5))
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
