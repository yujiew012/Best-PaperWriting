#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5"]
# ///
"""Modern-minimal architecture diagram from a JSON spec (vector PDF + PNG preview).

    uv run gen_architecture_diagram.py --spec fig_arch.json --out fig_arch.pdf
    uv run gen_architecture_diagram.py --spec fig_arch.json --style llm_agent_security --out fig_arch.pdf
    uv run gen_architecture_diagram.py --demo --out /tmp/arch_demo.pdf   # bundled example
    uv run gen_architecture_diagram.py --validate-style llm_agent_security  # check a style profile only

Style: --style <domain> (or the spec's "style" key) loads references/figure_styles/<domain>.json
(fonts, strokes, corners, fills, group lines, badge, role colours). Without it the
"default" profile is used. Profiles outside references/figure_styles/_bounds.json are rejected.

Spec (see assets/architecture_example.json):
{
  "layout": "double" | "single" | "onehalf",  "height": 2.6,  "venue": "acl",  "style": "llm_agent_security",
  "canvas": [10, 4],                         # data-coordinate extent (x, y)
  "groups": [{"label", "x", "y", "w", "h", "role"}],        # dashed role boundaries
  "blocks": [{"id", "label", "sub", "x", "y", "w", "h", "role"}],
  "edges":  [{"from", "to", "label", "step", "from_side", "to_side", "offset"}]
}
role: core (our module) | support (server/aux) | adverse (attack/constraint) |
neutral (data/generic); the colour of each role comes from the style profile. `step` draws a numbered
badge (1-9) at the middle of the arrow. `*_side` in {left,right,top,bottom}
pins the attachment side; `offset` shifts the arrow perpendicular to itself
(use +/-0.25 for a pair of up/down-link arrows).

Exit 2: invalid spec (unknown or duplicate block ids, duplicate steps).
Exit 1: layout issues -- overlapping blocks or texts (labels, badges, block and group
titles), text wider than its block or group, text beyond the canvas, arrows too
short, a canvas aspect that stretches the boxes. The figure is still written.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure  # noqa: E402
import figstyle  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "architecture_example.json")
ROLES = ("core", "support", "adverse", "neutral")
GROUP_LINES = {"dashed": "--", "dotted": ":", "solid": "-"}


def validate(spec):
    """Hard errors exit 2; layout problems are returned as a list of issue strings."""
    issues = []
    blocks = spec.get("blocks", [])
    ids = [b.get("id") for b in blocks]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        fail(f"duplicate block ids: {sorted(dup)}")
    for b in blocks:
        for k in ("id", "label", "x", "y", "w", "h"):
            if k not in b:
                fail(f"block {b.get('id', '?')}: missing '{k}'")
        if b.get("role", "neutral") not in ROLES:
            fail(f"block {b['id']}: role must be one of {list(ROLES)}")
    steps = []
    for e in spec.get("edges", []):
        for end in ("from", "to"):
            if e.get(end) not in ids:
                fail(f"edge {e}: unknown block id '{e.get(end)}'")
        if "step" in e:
            steps.append(int(e["step"]))
    if len(steps) != len(set(steps)):
        fail(f"duplicate step numbers: {sorted(steps)}")
    if steps and sorted(steps) != list(range(1, len(steps) + 1)):
        issues.append(f"steps are not 1..{len(steps)} without gaps: {sorted(steps)}")
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                issues.append(f"blocks overlap: {a['id']} and {b['id']}")
    return issues


def anchor(b, toward, side=None):
    """Point on block b's border facing `toward` (or the middle of `side`)."""
    cx, cy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    if side:
        return {"left": (b["x"], cy), "right": (b["x"] + b["w"], cy),
                "top": (cx, b["y"] + b["h"]), "bottom": (cx, b["y"])}[side]
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (b["w"] / 2) / abs(dx) if dx else math.inf
    sy = (b["h"] / 2) / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--spec", help="JSON diagram spec")
    src.add_argument("--demo", action="store_true", help="render the bundled example (NOT for papers)")
    src.add_argument("--validate-style", metavar="NAME_OR_PATH", help="only validate a style profile")
    ap.add_argument("--out", help="output PDF path (a PNG preview is written next to it)")
    ap.add_argument("--style", help="style profile: a domain name in references/figure_styles/ or a JSON path")
    ap.add_argument("--venue", help="venue profile for the width (references/venues.json)")
    args = ap.parse_args(argv)

    if args.validate_style:
        prof, ppath = figstyle.load(args.validate_style)
        errs = figstyle.validate(prof)
        for e in errs:
            print(f"[error] {e}", file=sys.stderr)
        print(f"{os.path.basename(ppath)}: {'OK' if not errs else f'{len(errs)} error(s)'}"
              f" ({len(prof.get('provisional', {}))} provisional override(s))")
        return 2 if errs else 0
    if not args.out:
        fail("--out is required")

    path = DEMO if args.demo else args.spec
    if not os.path.exists(path):
        fail(f"spec not found: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"{path}: invalid JSON ({e})")
    issues = validate(spec)
    profile, ppath = figstyle.load(args.style or spec.get("style", "default"))
    errs = figstyle.validate(profile)
    if errs:
        fail(f"style profile {ppath} violates its bounds: " + "; ".join(errs))
    S = figstyle.effective(profile)
    F, W = S["font"], S["stroke"]
    for b in spec["blocks"]:
        if len(str(b["label"]).split()) > S["max_label_words"]:
            issues.append(f"block '{b['id']}' label has {len(str(b['label']).split())} words "
                          f"(style allows {S['max_label_words']}); move detail into 'sub'")

    import matplotlib.pyplot as plt
    from matplotlib import patches
    from matplotlib.transforms import Bbox
    fw, fh = apply_style(spec.get("layout", "double"), spec.get("height", 2.6), args.venue or spec.get("venue"))
    plt.rcParams["axes.grid"] = False
    plt.rcParams["figure.constrained_layout.use"] = False   # a diagram owns the whole figure
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    cw, ch = spec.get("canvas", [10, 4])
    ax.set_xlim(0, cw)
    ax.set_ylim(0, ch)
    ax.set_aspect("auto")
    ax.axis("off")
    stretch = (cw / ch) / (fw / fh)
    if not 0.85 <= stretch <= 1.18:
        issues.append(f"canvas aspect {cw}:{ch} does not match the figure ({fw:.2f} x {fh:.2f} in): boxes are "
                      f"stretched {stretch:.2f}x; use a canvas of about {cw}:{cw * fh / fw:.1f}")

    group_titles = []
    for g in spec.get("groups", []):
        fill, edge = figstyle.role_colors(S, g.get("role", "neutral"), group=True)
        ax.add_patch(patches.FancyBboxPatch((g["x"], g["y"]), g["w"], g["h"], boxstyle="round,pad=0.05",
                                            facecolor=fill, edgecolor=edge, linestyle=GROUP_LINES[S["group"]["line"]],
                                            linewidth=W["group"], zorder=0))
        group_titles.append((g, ax.text(g["x"] + 0.12, g["y"] + g["h"] - 0.12, g.get("label", ""), ha="left",
                                        va="top", fontsize=F["group_title"], fontweight="bold", color=edge,
                                        zorder=1)))

    blocks = {b["id"]: b for b in spec["blocks"]}
    texts = []
    for b in spec["blocks"]:
        role = b.get("role", "neutral")
        fill, edge = figstyle.role_colors(S, role)
        lw = W["block"] * (W["core_emphasis"] if role == "core" else 1.0)
        corner = S["block"]["corner"]
        box = f"round,pad=0.03,rounding_size={corner}" if corner > 0 else "square,pad=0.03"
        ax.add_patch(patches.FancyBboxPatch((b["x"], b["y"]), b["w"], b["h"], boxstyle=box,
                                            facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2))
        cx = b["x"] + b["w"] / 2
        if b.get("sub"):
            t1 = ax.text(cx, b["y"] + b["h"] * 0.62, b["label"], ha="center", va="center",
                         fontsize=F["block_title"], fontweight="bold", color="#111111", zorder=3)
            t2 = ax.text(cx, b["y"] + b["h"] * 0.30, b["sub"], ha="center", va="center",
                         fontsize=F["block_sub"], color="#444444", zorder=3)
            texts += [(b, t1), (b, t2)]
        else:
            texts.append((b, ax.text(cx, b["y"] + b["h"] / 2, b["label"], ha="center", va="center",
                                     fontsize=F["block_title"], fontweight="bold", color="#111111", zorder=3)))

    labels, badges = [], []
    for e in spec.get("edges", []):
        a, b = blocks[e["from"]], blocks[e["to"]]
        ca = (a["x"] + a["w"] / 2, a["y"] + a["h"] / 2)
        cb = (b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
        p1 = anchor(a, cb, e.get("from_side"))
        p2 = anchor(b, ca, e.get("to_side"))
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm            # unit normal
        off = float(e.get("offset", 0.0))
        p1 = (p1[0] + nx * off, p1[1] + ny * off)
        p2 = (p2[0] + nx * off, p2[1] + ny * off)
        color = figstyle.role_colors(S, "adverse")[1] if a.get("role") == "adverse" else "#222222"
        ax.annotate("", xy=p2, xytext=p1, zorder=4,
                    arrowprops=dict(arrowstyle="-|>,head_width=0.18,head_length=0.3", color=color,
                                    lw=W["arrow"], shrinkA=1, shrinkB=1))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        if norm < 0.35:
            issues.append(f"edge {e['from']}->{e['to']} is only {norm:.2f} units long; move the blocks apart "
                          f"so the arrow and its badge are visible")
        if e.get("label"):
            # put the label on the side of the normal that points up (or right), clear of the badge
            sgn = 1 if (ny > 1e-9 or (abs(ny) <= 1e-9 and nx > 0)) else -1
            if off < 0:
                sgn = -sgn
            dist = 0.36 if "step" in e else 0.18
            labels.append(ax.text(mx + nx * dist * sgn, my + ny * dist * sgn, e["label"], ha="center",
                                  va="center", fontsize=F["edge_label"], color="#333333", zorder=5,
                                  bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.85)
                                  if S["edge"]["label_box"] else None))
        if "step" in e:
            # marker size is in points, so the badge stays a circle whatever the canvas aspect
            ax.plot([mx], [my], marker="o", markersize=S["badge"]["size"],
                    markerfacecolor=figstyle.OKABE[S["badge"]["color"]], markeredgecolor="black",
                    markeredgewidth=0.6, linestyle="none", zorder=10)
            badges.append(ax.text(mx, my, str(e["step"]), ha="center", va="center", color="white",
                                  fontsize=F["badge"], fontweight="bold", zorder=11,
                                  bbox=dict(boxstyle="circle,pad=0.25", facecolor="none", edgecolor="none")))

    # ---- geometric checks with the real renderer -------------------------------------------
    fig.canvas.draw()
    inv = ax.transData.inverted()

    def width_in_data(t):
        bb = t.get_window_extent()
        (x0, _), (x1, _) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
        return x1 - x0

    for b, t in texts:
        if width_in_data(t) > b["w"] * 0.98:
            issues.append(f"text '{t.get_text()}' is wider than block '{b['id']}' "
                          f"({width_in_data(t):.2f} > {b['w']:.2f}); widen the block or shorten the text")
    for g, t in group_titles:
        if width_in_data(t) > g["w"] - 0.2:
            issues.append(f"group title '{t.get_text()}' is wider than its group "
                          f"({width_in_data(t):.2f} > {g['w'] - 0.2:.2f}); shorten it or widen the group")
    canvas = ax.get_window_extent()
    every = ([(f"group title '{t.get_text()}'", t) for _, t in group_titles]
             + [(f"label '{t.get_text()}'", t) for t in labels]
             + [(f"badge {t.get_text()}", t) for t in badges]
             + [(f"block text '{t.get_text()}'", t) for _, t in texts])
    ext = [(name, t.get_window_extent().expanded(1.02, 1.05)) for name, t in every]
    for name, bb in ext:
        if bb.x0 < canvas.x0 - 1 or bb.x1 > canvas.x1 + 1 or bb.y0 < canvas.y0 - 1 or bb.y1 > canvas.y1 + 1:
            issues.append(f"{name} extends beyond the canvas")
    for i, (n1, b1) in enumerate(ext):
        for n2, b2 in ext[i + 1:]:
            if n1.startswith("block") and n2.startswith("block"):
                continue
            if b1.overlaps(b2):
                issues.append(f"{n1} overlaps {n2}")
    # group titles must not run into block boxes
    for g, t in group_titles:
        tb = t.get_window_extent()
        for b in spec["blocks"]:
            (x0, y0), (x1, y1) = ax.transData.transform([[b["x"], b["y"]], [b["x"] + b["w"], b["y"] + b["h"]]])
            if tb.overlaps(Bbox([[x0, y0], [x1, y1]])):
                issues.append(f"group title '{t.get_text()}' overlaps block '{b['id']}'")

    for msg in dict.fromkeys(issues):
        print(f"[issue] {msg}", file=sys.stderr)
    if args.demo:
        print("[warn] DEMO spec -- never use this figure in a paper", file=sys.stderr)
    save_figure(fig, args.out)
    if issues:
        print(f"{len(set(issues))} layout issue(s): fix the spec and regenerate (the figure was still written "
              f"for inspection)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
