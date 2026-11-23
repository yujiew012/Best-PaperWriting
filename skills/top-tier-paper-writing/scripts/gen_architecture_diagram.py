#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5"]
# ///
"""Modern-minimal architecture diagram from a JSON spec (vector PDF + PNG preview).

    uv run gen_architecture_diagram.py --spec fig_arch.json --out fig_arch.pdf
    uv run gen_architecture_diagram.py --demo --out /tmp/arch_demo.pdf   # bundled example

Spec (see assets/architecture_example.json):
{
  "layout": "double" | "single" | "onehalf",  "height": 2.6,
  "canvas": [10, 4],                         # data-coordinate extent (x, y)
  "groups": [{"label", "x", "y", "w", "h", "role"}],        # dashed role boundaries
  "blocks": [{"id", "label", "sub", "x", "y", "w", "h", "role"}],
  "edges":  [{"from", "to", "label", "step", "from_side", "to_side", "offset"}]
}
role: core (our module, blue) | support (server/aux, green) | adverse (attack/
constraint, vermilion) | neutral (data/generic, grey). `step` draws a numbered
badge (1-9) at the middle of the arrow. `*_side` in {left,right,top,bottom}
pins the attachment side; `offset` shifts the arrow perpendicular to itself
(use +/-0.25 for a pair of up/down-link arrows).

Validation (exit 2): unknown block ids, duplicate block ids, duplicate steps.
Warnings: overlapping blocks, labels wider than their box, gaps in step numbers.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "architecture_example.json")
ROLES = {
    "core": ("#E8F1F8", "#0072B2"),
    "support": ("#EAF6EE", "#009E73"),
    "adverse": ("#FDEEE6", "#D55E00"),
    "neutral": ("#FFFFFF", "#555555"),
}
GROUP_ROLES = {
    "core": ("#F3F8FC", "#0072B2"),
    "support": ("#F5F9F6", "#009E73"),
    "adverse": ("#FDF6F2", "#D55E00"),
    "neutral": ("#FAFAFA", "#999999"),
}


def validate(spec):
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
        print(f"[warn] steps are not 1..{len(steps)} without gaps: {sorted(steps)}", file=sys.stderr)
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                print(f"[warn] blocks overlap: {a['id']} and {b['id']}", file=sys.stderr)


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
    ap.add_argument("--out", required=True, help="output PDF path (a PNG preview is written next to it)")
    args = ap.parse_args(argv)

    path = DEMO if args.demo else args.spec
    if not os.path.exists(path):
        fail(f"spec not found: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"{path}: invalid JSON ({e})")
    validate(spec)

    import matplotlib.pyplot as plt
    from matplotlib import patches
    apply_style(spec.get("layout", "double"), spec.get("height", 2.6))
    plt.rcParams["axes.grid"] = False
    fig, ax = plt.subplots()
    cw, ch = spec.get("canvas", [10, 4])
    ax.set_xlim(0, cw)
    ax.set_ylim(0, ch)
    ax.set_aspect("auto")
    ax.axis("off")

    for g in spec.get("groups", []):
        fill, edge = GROUP_ROLES.get(g.get("role", "neutral"), GROUP_ROLES["neutral"])
        ax.add_patch(patches.FancyBboxPatch((g["x"], g["y"]), g["w"], g["h"], boxstyle="round,pad=0.05",
                                            facecolor=fill, edgecolor=edge, linestyle="--", linewidth=1.0,
                                            zorder=0))
        ax.text(g["x"] + 0.12, g["y"] + g["h"] - 0.12, g.get("label", ""), ha="left", va="top",
                fontsize=8, fontweight="bold", color=edge, zorder=1)

    blocks = {b["id"]: b for b in spec["blocks"]}
    texts = []
    for b in spec["blocks"]:
        fill, edge = ROLES[b.get("role", "neutral")]
        ax.add_patch(patches.FancyBboxPatch((b["x"], b["y"]), b["w"], b["h"],
                                            boxstyle="round,pad=0.03,rounding_size=0.08",
                                            facecolor=fill, edgecolor=edge, linewidth=1.1, zorder=2))
        cx = b["x"] + b["w"] / 2
        if b.get("sub"):
            t1 = ax.text(cx, b["y"] + b["h"] * 0.62, b["label"], ha="center", va="center",
                         fontsize=8, fontweight="bold", color="#111111", zorder=3)
            t2 = ax.text(cx, b["y"] + b["h"] * 0.30, b["sub"], ha="center", va="center",
                         fontsize=6.8, color="#444444", zorder=3)
            texts += [(b, t1), (b, t2)]
        else:
            texts.append((b, ax.text(cx, b["y"] + b["h"] / 2, b["label"], ha="center", va="center",
                                     fontsize=8, fontweight="bold", color="#111111", zorder=3)))

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
        color = ROLES[a.get("role", "neutral")][1] if a.get("role") == "adverse" else "#222222"
        ax.annotate("", xy=p2, xytext=p1, zorder=4,
                    arrowprops=dict(arrowstyle="-|>,head_width=0.18,head_length=0.3", color=color, lw=1.1,
                                    shrinkA=1, shrinkB=1))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        if norm < 0.35:
            print(f"[warn] edge {e['from']}->{e['to']} is only {norm:.2f} units long; "
                  f"move the blocks apart so the arrow and its badge are visible", file=sys.stderr)
        if e.get("label"):
            # put the label on the side of the normal that points up (or right), clear of the badge
            sgn = 1 if (ny > 1e-9 or (abs(ny) <= 1e-9 and nx > 0)) else -1
            if off < 0:
                sgn = -sgn
            dist = 0.36 if "step" in e else 0.18
            lt = ax.text(mx + nx * dist * sgn, my + ny * dist * sgn, e["label"], ha="center", va="center",
                         fontsize=6.8, color="#333333", zorder=5,
                         bbox=dict(facecolor="white", edgecolor="none", pad=0.4, alpha=0.85))
            labels.append(lt)
        if "step" in e:
            ax.add_patch(patches.Circle((mx, my), 0.14, transform=ax.transData, facecolor="#D55E00",
                                        edgecolor="black", linewidth=0.6, zorder=10))
            badges.append(ax.text(mx, my, str(e["step"]), ha="center", va="center", color="white",
                                  fontsize=7, fontweight="bold", zorder=11,
                                  bbox=dict(boxstyle="circle,pad=0.25", facecolor="none", edgecolor="none")))

    # Warn about labels that do not fit their box (measured with the real renderer).
    fig.canvas.draw()
    inv = ax.transData.inverted()
    for b, t in texts:
        bb = t.get_window_extent()
        (x0, _), (x1, _) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
        if x1 - x0 > b["w"] * 0.98:
            print(f"[warn] text '{t.get_text()}' is wider than block '{b['id']}' "
                  f"({x1 - x0:.2f} > {b['w']:.2f}); widen the block or shorten the text", file=sys.stderr)
    # Warn about any edge label / badge overlapping another text element.
    items = [(f"label '{t.get_text()}'", t) for t in labels] + \
            [(f"badge {t.get_text()}", t) for t in badges] + \
            [(f"block text '{t.get_text()}'", t) for _, t in texts]
    ext = [(name, t.get_window_extent().expanded(1.02, 1.05)) for name, t in items]
    seen = set()
    for i, (n1, b1) in enumerate(ext):
        for n2, b2 in ext[i + 1:]:
            if n1.startswith("block") and n2.startswith("block"):
                continue
            if b1.overlaps(b2) and (n1, n2) not in seen:
                seen.add((n1, n2))
                print(f"[warn] {n1} overlaps {n2}; adjust positions or the edge 'offset'", file=sys.stderr)
    if args.demo:
        print("[warn] DEMO spec -- never use this figure in a paper", file=sys.stderr)
    save_figure(fig, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
