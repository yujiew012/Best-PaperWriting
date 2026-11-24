#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5", "numpy>=1.21"]
# ///
"""Grid of example inputs (e.g. clean vs. attacked images) at an exact column width.

    uv run compose_examples.py --images clean.png blur.png noise.png --labels "Clean" "Blur" "Noise" \
        --ncols 3 --venue acl --out fig_examples.pdf
    uv run compose_examples.py --images a.png b.png c.png d.png --labels 300 60 30 15 \
        --row-labels "Rendered prompt" --ncols 4 --layout double --out fig_dpi_examples.pdf

Every image is fitted into an equal cell (aspect preserved, never stretched) with
its label underneath. Use benign or redacted content when the real input is
harmful -- this script does not redact. Exit codes: 0 ok, 2 bad input.
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--images", nargs="+", required=True, help="image files (PNG/JPG), row-major order")
    ap.add_argument("--labels", nargs="+", help="one label per image (shown under it)")
    ap.add_argument("--row-labels", nargs="+", help="optional label per row (left side)")
    ap.add_argument("--ncols", type=int, default=0, help="images per row (default: all in one row, max 4)")
    ap.add_argument("--layout", choices=["single", "double", "onehalf"], default="double")
    ap.add_argument("--venue", help="venue profile from references/venues.json (sets the width)")
    ap.add_argument("--height", type=float, help="figure height in inches (default: from the image aspect)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    for f in args.images:
        if not os.path.isfile(f):
            fail(f"image not found: {f}")
    if args.labels and len(args.labels) != len(args.images):
        fail(f"{len(args.labels)} labels for {len(args.images)} images")
    n = len(args.images)
    ncols = args.ncols or min(n, 4)
    nrows = math.ceil(n / ncols)
    if args.row_labels and len(args.row_labels) != nrows:
        fail(f"{len(args.row_labels)} row labels for {nrows} rows")

    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    imgs = [mpimg.imread(f) for f in args.images]
    aspect = sum(im.shape[0] / im.shape[1] for im in imgs) / n          # mean height/width
    from pubstyle import venue_widths
    width = venue_widths(args.venue)[args.layout]
    left = 0.35 if args.row_labels else 0.0
    cell_w = (width - left) / ncols
    height = args.height or nrows * (cell_w * aspect + 0.28) + 0.05
    apply_style(args.layout, height, args.venue)
    plt.rcParams["axes.grid"] = False
    fig, axes = plt.subplots(nrows, ncols, squeeze=False)
    for k in range(nrows * ncols):
        ax = axes[k // ncols][k % ncols]
        ax.set_xticks([])
        ax.set_yticks([])
        if k >= n:
            ax.axis("off")
            continue
        ax.imshow(imgs[k], aspect="equal", interpolation="lanczos")
        for s in ax.spines.values():
            s.set_linewidth(0.6)
            s.set_color("#555555")
        if args.labels:
            ax.set_xlabel(args.labels[k], fontsize=8, labelpad=3)
        if args.row_labels and k % ncols == 0:
            ax.set_ylabel(args.row_labels[k // ncols], fontsize=8)
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
