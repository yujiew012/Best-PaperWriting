"""Shared publication style for the plotting scripts (IEEE/ACM two-column).

Import from a script in this directory:
    from pubstyle import apply_style, OKABE_ITO, series_styles, save_figure

All sizes are exact: figures are laid out with constrained layout and saved
WITHOUT bbox_inches="tight", so the PDF page is exactly the requested width.
"""
import json
import os
import sys

WIDTHS = {"single": 3.4, "double": 6.9, "onehalf": 5.0}       # IEEE defaults when no --venue is given
VENUES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "venues.json")


def load_venue(name):
    """Return the venue profile from references/venues.json (None for no venue)."""
    if not name:
        return None
    with open(VENUES_PATH, encoding="utf-8") as f:
        venues = json.load(f)["venues"]
    if name not in venues:
        fail(f"unknown venue '{name}'; choose from: {', '.join(venues)}")
    return venues[name]


def venue_widths(name):
    """{'single': column width, 'double': text width, 'onehalf': ...} for a venue (inches)."""
    v = load_venue(name)
    if not v:
        return dict(WIDTHS)
    return {"single": v["column_width_in"], "double": v["text_width_in"],
            "onehalf": round(0.72 * v["text_width_in"], 2)}
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
# Order used for non-"ours" series. Vermilion is reserved for series explicitly marked adverse
# (attack / degraded / undefended), so it is never handed out by position.
BASELINE_COLORS = ["orange", "reddish_purple", "bluish_green", "sky_blue", "black"]
MARKERS = ["s", "^", "D", "v", "P", "X", "*"]
LINESTYLES = ["--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1, 1, 1)), (0, (1, 1))]


def apply_style(layout="single", height=None, venue=None):
    """Set rcParams for publication figures and return (width, height) in inches.

    layout: single = one column (or the full text width in one-column venues), double = text width.
    venue:  a key of references/venues.json; without it IEEE widths are used.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    width = venue_widths(venue)[layout]
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


def series_styles(names, ours=None, adverse=()):
    """Assign color/marker/linestyle per series; `ours` gets blue, solid, circles;
    series listed in `adverse` (attack, degraded, undefended) get vermilion."""
    styles, k = {}, 0
    # with an adverse (vermilion) series present, skip orange: the two warm hues are hard to tell apart
    palette = [c for c in BASELINE_COLORS if not (adverse and c == "orange")] or BASELINE_COLORS
    for n in names:
        if ours is not None and n == ours:
            styles[n] = {"color": OKABE_ITO["blue"], "marker": "o", "linestyle": "-", "zorder": 5}
        elif n in adverse:
            styles[n] = {"color": OKABE_ITO["vermilion"], "marker": "X", "linestyle": (0, (5, 2)), "zorder": 4}
        else:
            styles[n] = {"color": OKABE_ITO[palette[k % len(palette)]],
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
