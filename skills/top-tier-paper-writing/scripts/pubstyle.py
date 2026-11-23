"""Shared publication style for the plotting scripts (IEEE/ACM two-column).

Import from a script in this directory:
    from pubstyle import apply_style, OKABE_ITO, series_styles, save_figure

All sizes are exact: figures are laid out with constrained layout and saved
WITHOUT bbox_inches="tight", so the PDF page is exactly the requested width.
"""
import os
import sys

WIDTHS = {"single": 3.4, "double": 6.9, "onehalf": 5.0}
DEFAULT_HEIGHTS = {"single": 2.4, "double": 2.8, "onehalf": 3.2}

OKABE_ITO = {
    "blue": "#0072B2",           # our method
    "orange": "#E69F00",         # main baseline
    "bluish_green": "#009E73",   # variant / support component
    "vermilion": "#D55E00",      # attack / degraded / adverse
    "reddish_purple": "#CC79A7", # secondary baseline
    "sky_blue": "#56B4E9",       # auxiliary
    "black": "#000000",          # reference line
    "yellow": "#F0E442",         # special marks only (low contrast on white)
}
# Order used for non-"ours" series.
BASELINE_COLORS = ["orange", "reddish_purple", "vermilion", "bluish_green", "sky_blue", "black"]
MARKERS = ["s", "^", "D", "v", "P", "X", "*"]
LINESTYLES = ["--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1, 1, 1)), (0, (1, 1))]


def apply_style(layout="single", height=None):
    """Set rcParams for publication figures and return (width, height) in inches."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    width = WIDTHS[layout]
    height = height or DEFAULT_HEIGHTS[layout]
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "legend.frameon": False,
        "figure.figsize": (width, height),
        "figure.constrained_layout.use": True,
        "lines.linewidth": 1.5,
        "lines.markersize": 4,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "pdf.fonttype": 42,   # embed TrueType, never Type 3
        "ps.fonttype": 42,
        "savefig.dpi": 300,
    })
    return width, height


def series_styles(names, ours=None):
    """Assign color/marker/linestyle per series; `ours` gets blue, solid, circles."""
    styles, k = {}, 0
    for n in names:
        if ours is not None and n == ours:
            styles[n] = {"color": OKABE_ITO["blue"], "marker": "o", "linestyle": "-", "zorder": 5}
        else:
            styles[n] = {"color": OKABE_ITO[BASELINE_COLORS[k % len(BASELINE_COLORS)]],
                         "marker": MARKERS[k % len(MARKERS)],
                         "linestyle": LINESTYLES[k % len(LINESTYLES)], "zorder": 3}
            k += 1
    return styles


def save_figure(fig, out_path, png=True):
    """Save vector PDF (+ PNG preview) at the exact figure size and report it."""
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(out_path, format="pdf")
    paths = [out_path]
    if png:
        png_path = os.path.splitext(out_path)[0] + ".png"
        fig.savefig(png_path, format="png")
        paths.append(png_path)
    w, h = fig.get_size_inches()
    for p in paths:
        print(f"[ok] wrote {p} ({w:.2f} x {h:.2f} in)")
    return paths


def fail(msg, code=2):
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(code)
