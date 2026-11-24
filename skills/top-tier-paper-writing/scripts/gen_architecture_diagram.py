#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = ["matplotlib>=3.5", "pillow"]
# ///
"""Modern-minimal architecture diagram from a JSON spec (vector PDF + PNG preview).

    uv run gen_architecture_diagram.py --spec fig_arch.json --out fig_arch.pdf
    uv run gen_architecture_diagram.py --spec fig_arch.json --style llm_agent_security --venue acl --out fig_arch.pdf
    uv run gen_architecture_diagram.py --demo --out /tmp/arch_demo.pdf   # bundled example
    uv run gen_architecture_diagram.py --validate-style llm_agent_security  # check a style profile only

Style: --style <domain> (or the spec's "style" key) loads references/figure_styles/<domain>.json
(fonts, strokes, corners, fills, group lines, badge, role colours). Without it the
"default" profile is used. Profiles outside references/figure_styles/_bounds.json are rejected.

Spec (see assets/architecture_example.json; all coordinates are canvas units, origin bottom-left):
{
  "layout": "double" | "single" | "onehalf",  "height": 2.6,  "venue": "acl",  "style": "llm_agent_security",
  "canvas": [10, 4],
  "groups": [{"label", "x", "y", "w", "h", "role",
              "images": [{"path": "clean.png", "label": "Clean"}, ...], "cols": 4}],   # optional image grid
  "blocks": [{"id", "label", "sub", "x", "y", "w", "h", "role",
              "image": "plot.pdf",                     # optional inset (PNG/JPG/PDF), aspect kept, label below
              "shape": "actor_attacker",               # optional glyph instead of a box, label below
              "frame": true}],                         # draw the box around an image/shape block
  "edges":  [{"from", "to", "label", "step", "from_side", "to_side", "offset",
              "role": "adverse", "line": "solid" | "dashed" | "dotted"}]
}
role: core (our module) | support (server/aux) | adverse (attack/constraint) | neutral (data/generic);
colours come from the style profile. An edge takes the adverse colour when its source is adverse,
or when it sets "role": "adverse" (e.g. an attack edge out of a neutral payload).
shape: actor_attacker | actor_user | model | shield | document | database (vector glyphs in the role colour).
image: an inset such as a plot from plot_data_curves.py or a grid from compose_examples.py; PDFs are
rasterized at 300 dpi with pdftoppm. A group with "images" lays them out as equal cells with labels.
`step` draws a numbered badge (1-9) at the middle of the arrow. `*_side` in {left,right,top,bottom}
pins the attachment side; several arrows that meet one side of a block are spread along it
automatically (set `offset` to place an arrow yourself: +/-0.25 for a pair of up/down-link arrows).

Exit 2: invalid spec (unknown or duplicate block ids, duplicate steps, unknown shape, missing image).
Exit 1: layout issues, and the figure is still written:
  - texts: overlapping texts (labels, badges, titles, a block's title and sub-line), text closer than
    2 pt to its block border or wider than it, text beyond the canvas;
  - groups: a group title that runs into a block or an arrow, and groups that overlap partly or share
    a border (a group must be disjoint from, or nested with a margin inside, another);
  - arrows: shorter than 0.15 in (badge diameter + 0.1 in with a step badge), passing through a block that is not an endpoint, or crossing a group
    that neither endpoint belongs to;
  - images: an inset or grid cell smaller than 0.3 in;
  - canvas: an aspect ratio that stretches the boxes.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import apply_style, fail, save_figure  # noqa: E402
import figstyle  # noqa: E402

DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "architecture_example.json")
ROLES = ("core", "support", "adverse", "neutral")
LINES = {"dashed": "--", "dotted": ":", "solid": "-"}
SHAPES = ("actor_attacker", "actor_user", "model", "shield", "document", "database")
SIDES = ("left", "right", "top", "bottom")
MIN_ARROW_IN = 0.15         # shortest visible arrow, in inches
BADGE_ROOM_IN = 0.1         # extra length an arrow with a step badge needs beyond the badge diameter
CLEAR_PT = 2.0              # minimum clearance between a block's text and its border, in points
MIN_IMAGE_IN = 0.3          # smallest readable inset or grid cell
GPAD = 0.05                 # FancyBboxPatch pad of group frames (canvas units)


def validate(spec, base_dir):
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
        if b.get("shape") and b["shape"] not in SHAPES:
            fail(f"block {b['id']}: shape must be one of {list(SHAPES)}")
        if b.get("shape") and b.get("image"):
            fail(f"block {b['id']}: use either 'shape' or 'image', not both")
        if b.get("image") and not os.path.exists(resolve(b["image"], base_dir)):
            fail(f"block {b['id']}: image not found: {b['image']}")
    for g in spec.get("groups", []):
        for k in ("x", "y", "w", "h"):
            if k not in g:
                fail(f"group {g.get('label', '?')}: missing '{k}'")
        for im in g.get("images", []):
            if not os.path.exists(resolve(im.get("path", ""), base_dir)):
                fail(f"group {g.get('label', '?')}: image not found: {im.get('path')}")
    steps = []
    for e in spec.get("edges", []):
        for end in ("from", "to"):
            if e.get(end) not in ids:
                fail(f"edge {e}: unknown block id '{e.get(end)}'")
        for side in ("from_side", "to_side"):
            if e.get(side) and e[side] not in SIDES:
                fail(f"edge {e['from']}->{e['to']}: {side} must be one of {list(SIDES)}")
        if e.get("role", "neutral") not in ROLES:
            fail(f"edge {e['from']}->{e['to']}: role must be one of {list(ROLES)}")
        if e.get("line", "solid") not in LINES:
            fail(f"edge {e['from']}->{e['to']}: line must be one of {list(LINES)}")
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


def resolve(path, base_dir):
    return path if os.path.isabs(path) else os.path.join(base_dir, path)


def load_image(path, tmp):
    """Pixel array of a PNG/JPG, or of page 1 of a PDF rasterized at 300 dpi."""
    import numpy as np
    from PIL import Image
    if path.lower().endswith(".pdf"):
        if not shutil.which("pdftoppm"):
            fail(f"{path}: rasterizing a PDF inset needs pdftoppm (poppler-utils); pass a PNG instead")
        prefix = os.path.join(tmp, f"inset{len(os.listdir(tmp))}")
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", "300", "-png", "-singlefile", path, prefix],
                       check=True, capture_output=True)
        path = prefix + ".png"
    return np.asarray(Image.open(path).convert("RGBA"))


# ---------------------------------------------------------------------------
# geometry helpers (canvas units)
# ---------------------------------------------------------------------------

def center(b):
    return b["x"] + b["w"] / 2, b["y"] + b["h"] / 2


def side_toward(b, toward):
    """Which side of block b faces the point `toward` (ray from the centre)."""
    cx, cy = center(b)
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return "right"
    if abs(dx) * b["h"] >= abs(dy) * b["w"]:
        return "right" if dx > 0 else "left"
    return "top" if dy > 0 else "bottom"


def anchor(b, toward):
    """Point on block b's border on the ray from its centre to `toward`."""
    cx, cy = center(b)
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (b["w"] / 2) / abs(dx) if dx else math.inf
    sy = (b["h"] / 2) / abs(dy) if dy else math.inf
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def port(b, side, frac):
    """Point at fraction `frac` (0..1) along a side of block b."""
    if side in ("left", "right"):
        x = b["x"] if side == "left" else b["x"] + b["w"]
        return x, b["y"] + b["h"] * frac
    y = b["y"] if side == "bottom" else b["y"] + b["h"]
    return b["x"] + b["w"] * frac, y


def seg_hits_rect(p1, p2, r, shrink=0.0):
    """Liang-Barsky: does segment p1-p2 pass through rect r=(x0,y0,x1,y1) shrunk by `shrink`?"""
    x0, y0, x1, y1 = r[0] + shrink, r[1] + shrink, r[2] - shrink, r[3] - shrink
    if x0 >= x1 or y0 >= y1:
        return False
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, p1[0] - x0), (dx, x1 - p1[0]), (-dy, p1[1] - y0), (dy, y1 - p1[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def rect(o, pad=0.0):
    return (o["x"] - pad, o["y"] - pad, o["x"] + o["w"] + pad, o["y"] + o["h"] + pad)


def inside(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


# ---------------------------------------------------------------------------
# glyphs: drawn in a square of side `s` inches, so circles stay round on any canvas
# ---------------------------------------------------------------------------

def draw_glyph(ax, shape, gx, gy, s, ux, uy, fill, edge, lw):
    """Vector pictogram in a square of side `s` inches whose bottom-left corner is (gx, gy) in canvas
    units; ux, uy = canvas units per inch, so circles stay round on any canvas aspect."""
    from matplotlib import patches

    def P(u, v):
        return gx + u * s * ux, gy + v * s * uy

    def ellipse(u, v, du, dv, **kw):
        return patches.Ellipse(P(u, v), du * s * ux, dv * s * uy, **kw)

    def poly(pts, **kw):
        return patches.Polygon([P(u, v) for u, v in pts], closed=True, **kw)

    def roundbox(u, v, du, dv, r, **kw):
        return patches.FancyBboxPatch(P(u, v), du * s * ux, dv * s * uy,
                                      boxstyle=f"round,pad=0,rounding_size={r * s * min(ux, uy)}", **kw)

    def line(pts, width=lw):
        xs, ys = zip(*[P(u, v) for u, v in pts])
        ax.plot(xs, ys, color=edge, linewidth=width, solid_capstyle="round", zorder=4)

    body = dict(facecolor=fill, edgecolor=edge, linewidth=lw, zorder=3)
    ink = dict(facecolor=edge, edgecolor=edge, linewidth=lw, zorder=4)
    parts = []
    if shape in ("actor_user", "actor_attacker"):
        parts.append(roundbox(0.14, 0.04, 0.72, 0.36, 0.16, **body))          # shoulders
        parts.append(ellipse(0.5, 0.66, 0.44, 0.44, **body))                    # head
        if shape == "actor_attacker":
            parts.append(roundbox(0.28, 0.62, 0.44, 0.09, 0.03, **ink))         # mask band
            parts.append(poly([(0.30, 0.80), (0.5, 0.96), (0.70, 0.80)], **ink))  # hood
    elif shape == "model":
        parts.append(roundbox(0.1, 0.1, 0.8, 0.8, 0.12, **body))
        nodes = [(0.32, 0.30), (0.32, 0.70), (0.70, 0.50)]
        line([nodes[0], nodes[2]])
        line([nodes[1], nodes[2]])
        line([nodes[0], nodes[1]])
        parts += [ellipse(u, v, 0.16, 0.16, **ink) for u, v in nodes]
    elif shape == "shield":
        parts.append(poly([(0.5, 0.95), (0.88, 0.80), (0.82, 0.38), (0.5, 0.05), (0.18, 0.38), (0.12, 0.80)],
                          **body))
        line([(0.33, 0.52), (0.46, 0.38), (0.70, 0.68)], width=lw * 1.6)        # check mark
    elif shape == "document":
        parts.append(poly([(0.2, 0.05), (0.8, 0.05), (0.8, 0.72), (0.6, 0.95), (0.2, 0.95)], **body))
        parts.append(poly([(0.6, 0.95), (0.6, 0.72), (0.8, 0.72)], **ink))      # folded corner
        for v in (0.55, 0.40, 0.25):
            line([(0.3, v), (0.7, v)])
    elif shape == "database":
        parts.append(patches.Rectangle(P(0.15, 0.15), 0.7 * s * ux, 0.7 * s * uy, facecolor=fill,
                                       edgecolor="none", zorder=3))
        parts.append(ellipse(0.5, 0.15, 0.7, 0.24, **body))
        line([(0.15, 0.15), (0.15, 0.85)])
        line([(0.85, 0.15), (0.85, 0.85)])
        parts.append(ellipse(0.5, 0.85, 0.7, 0.24, **body))
    for p in parts:
        ax.add_patch(p)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

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
    base_dir = os.path.dirname(os.path.abspath(path))
    issues = validate(spec, base_dir)
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
    ux, uy = cw / fw, ch / fh                 # canvas units per inch
    stretch = (cw / ch) / (fw / fh)
    if not 0.85 <= stretch <= 1.18:
        issues.append(f"canvas aspect {cw}:{ch} does not match the figure ({fw:.2f} x {fh:.2f} in): boxes are "
                      f"stretched {stretch:.2f}x; use a canvas of about {cw}:{cw * fh / fw:.1f}")
    tmp = tempfile.mkdtemp(prefix="arch_")

    # ---- groups (frames, titles, image-grid labels) ----------------------------------------
    groups = spec.get("groups", [])
    group_titles, grid_cells = [], []        # grid_cells: (group, image entry, cell rect, label text)
    for g in groups:
        fill, edge = figstyle.role_colors(S, g.get("role", "neutral"), group=True)
        ax.add_patch(patches.FancyBboxPatch((g["x"], g["y"]), g["w"], g["h"], boxstyle=f"round,pad={GPAD}",
                                            facecolor=fill, edgecolor=edge, linestyle=LINES[S["group"]["line"]],
                                            linewidth=W["group"], zorder=0))
        t = ax.text(g["x"] + 0.12, g["y"] + g["h"] - 0.12, g.get("label", ""), ha="left", va="top",
                    fontsize=F["group_title"], fontweight="bold", color=edge, zorder=1)
        group_titles.append((g, t))
        for i, im in enumerate(g.get("images", [])):
            grid_cells.append([g, im, i, None])

    # ---- blocks: frames and texts (positions finalized after the first draw) ---------------
    blocks = {b["id"]: b for b in spec["blocks"]}
    block_texts = {}                         # id -> [title, sub?]
    for b in spec["blocks"]:
        role = b.get("role", "neutral")
        fill, edge = figstyle.role_colors(S, role)
        lw = W["block"] * (W["core_emphasis"] if role == "core" else 1.0)
        framed = b.get("frame", not (b.get("shape") or b.get("image")))
        if framed:
            corner = S["block"]["corner"]
            box = f"round,pad=0.03,rounding_size={corner}" if corner > 0 else "square,pad=0.03"
            ax.add_patch(patches.FancyBboxPatch((b["x"], b["y"]), b["w"], b["h"], boxstyle=box,
                                                facecolor=fill if not b.get("image") else "#FFFFFF",
                                                edgecolor=edge, linewidth=lw, zorder=2))
        ts = [ax.text(0, 0, b["label"], ha="center", va="center", fontsize=F["block_title"], fontweight="bold",
                      color="#111111", zorder=3)]
        if b.get("sub"):
            ts.append(ax.text(0, 0, b["sub"], ha="center", va="center", fontsize=F["block_sub"],
                              color="#444444", zorder=3))
        block_texts[b["id"]] = ts
    for cell in grid_cells:
        cell[3] = ax.text(0, 0, cell[1].get("label", ""), ha="center", va="bottom", fontsize=F["block_sub"],
                          color="#333333", zorder=3)

    fig.canvas.draw()
    inv = ax.transData.inverted()
    pt = fig.dpi / 72.0                      # display pixels per point

    def h_data(t):
        bb = t.get_window_extent()
        return inv.transform([[0, bb.y1]])[0][1] - inv.transform([[0, bb.y0]])[0][1]

    gap = 1.5 * uy / 72                      # 1.5 pt between stacked lines, in canvas units
    vis = {}                                 # id -> visible rect of an unframed glyph/image (arrows attach to it)
    # stack title + sub; plain blocks centre the stack, glyph/image blocks put it at the bottom
    for b in spec["blocks"]:
        ts = block_texts[b["id"]]
        heights = [h_data(t) for t in ts]
        total = sum(heights) + gap * (len(ts) - 1)
        cx = b["x"] + b["w"] / 2
        visual = b.get("shape") or b.get("image")
        padx, pady = 3 * ux / 72, 3 * uy / 72                 # 3 pt
        top = (b["y"] + pady + total) if visual else (b["y"] + b["h"] / 2 + total / 2)
        for t, h in zip(ts, heights):
            t.set_position((cx, top - h / 2))
            top -= h + gap
        if visual:
            area = (b["x"] + padx, b["y"] + 2 * pady + total, b["x"] + b["w"] - padx, b["y"] + b["h"] - pady)
            aw, ah = (area[2] - area[0]) / ux, (area[3] - area[1]) / uy       # inches
            if aw < MIN_IMAGE_IN or ah < MIN_IMAGE_IN:
                issues.append(f"block '{b['id']}': only {aw:.2f} x {ah:.2f} in left for its "
                              f"{'glyph' if b.get('shape') else 'image'} above the label; enlarge the block")
                continue
            if b.get("shape"):
                s = min(aw, ah)
                gx = (area[0] + area[2]) / 2 - s * ux / 2
                fill, edge = figstyle.role_colors(S, b.get("role", "neutral"))
                if b.get("role", "neutral") == "neutral":
                    fill = "#F2F2F2"
                draw_glyph(ax, b["shape"], gx, area[1], s, ux, uy, fill, edge, W["block"])
                if not b.get("frame"):
                    vis[b["id"]] = {"x": gx, "y": area[1], "w": s * ux, "h": s * uy}
            else:
                img = load_image(resolve(b["image"], base_dir), tmp)
                ar = img.shape[0] / img.shape[1]
                wi = min(aw, ah / ar)
                hi = wi * ar
                x0 = (area[0] + area[2]) / 2 - wi * ux / 2
                y0 = area[1] + (ah - hi) * uy / 2
                ax.imshow(img, extent=(x0, x0 + wi * ux, y0, y0 + hi * uy), aspect="auto", zorder=3,
                          interpolation="lanczos")
                if not b.get("frame"):
                    vis[b["id"]] = {"x": x0, "y": y0, "w": wi * ux, "h": hi * uy}
                if wi < MIN_IMAGE_IN:
                    issues.append(f"block '{b['id']}': inset is only {wi:.2f} in wide; enlarge the block")
    # image grids: equal cells below the group title, label under each image
    for g, t in group_titles:
        cells = [c for c in grid_cells if c[0] is g]
        if not cells:
            continue
        n = len(cells)
        cols = max(1, min(int(g.get("cols", n)), n))
        rows = math.ceil(n / cols)
        top = g["y"] + g["h"] - 0.12 - h_data(t) - 0.08
        x0, x1, y0 = g["x"] + 0.1, g["x"] + g["w"] - 0.1, g["y"] + 0.08
        cw_, ch_ = (x1 - x0) / cols, (top - y0) / rows
        for k, (gg, im, i, lab) in enumerate(cells):
            r, c = divmod(k, cols)
            cx0, cy0 = x0 + c * cw_, top - (r + 1) * ch_
            lab.set_position((cx0 + cw_ / 2, cy0 + 0.02))
            lh = h_data(lab) + gap
            aw, ah = (cw_ - 0.08) / ux, (ch_ - lh - 0.06) / uy
            img = load_image(resolve(im["path"], base_dir), tmp)
            ar = img.shape[0] / img.shape[1]
            wi = max(min(aw, ah / ar), 0.01)
            hi = wi * ar
            ix = cx0 + cw_ / 2 - wi * ux / 2
            stack = hi * uy + lh                         # image directly above its label, centred in the cell
            sy = cy0 + (ch_ - stack) / 2
            lab.set_position((cx0 + cw_ / 2, sy))
            iy = sy + lh
            ax.imshow(img, extent=(ix, ix + wi * ux, iy, iy + hi * uy), aspect="auto", zorder=3,
                      interpolation="lanczos")
            ax.add_patch(patches.Rectangle((ix, iy), wi * ux, hi * uy, fill=False, edgecolor="#888888",
                                           linewidth=0.5, zorder=4))
            if min(wi, hi) < MIN_IMAGE_IN:
                issues.append(f"group '{g.get('label', '')}': image cell {i + 1} is only {wi:.2f} x {hi:.2f} in; "
                              f"use fewer columns or a taller group")
    ax.set_xlim(0, cw)                       # imshow resets the limits
    ax.set_ylim(0, ch)

    # ---- edges: ports spread along shared sides -------------------------------------------
    edges = spec.get("edges", [])
    geo = {bid: vis.get(bid, b) for bid, b in blocks.items()}
    ends = {}                                # (block id, side) -> list of (edge index, end, other centre)
    plan = []
    for i, e in enumerate(edges):
        a, b = geo[e["from"]], geo[e["to"]]
        sa = e.get("from_side") or side_toward(a, center(b))
        sb = e.get("to_side") or side_toward(b, center(a))
        plan.append({"sa": sa, "sb": sb})
        if not float(e.get("offset", 0.0)):
            ends.setdefault((e["from"], sa), []).append((i, "a", center(b)))
            ends.setdefault((e["to"], sb), []).append((i, "b", center(a)))
    for (bid, side), lst in ends.items():
        b = geo[bid]
        if len(lst) == 1:
            i, end, other = lst[0]
            pinned = edges[i].get("from_side" if end == "a" else "to_side")
            plan[i][end] = port(b, side, 0.5) if pinned else anchor(b, other)   # keep the centre line
            continue
        horiz = side in ("top", "bottom")
        lst.sort(key=lambda it: it[2][0] if horiz else it[2][1])
        n = len(lst)
        for k, (i, end, _) in enumerate(lst):
            plan[i][end] = port(b, side, 0.15 + 0.7 * k / (n - 1))

    labels, badges, segments = [], [], []
    for i, e in enumerate(edges):
        a, b = geo[e["from"]], geo[e["to"]]
        p1 = plan[i].get("a") or (port(a, e["from_side"], 0.5) if e.get("from_side") else anchor(a, center(b)))
        p2 = plan[i].get("b") or (port(b, e["to_side"], 0.5) if e.get("to_side") else anchor(b, center(a)))
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm            # unit normal
        off = float(e.get("offset", 0.0))
        p1 = (p1[0] + nx * off, p1[1] + ny * off)
        p2 = (p2[0] + nx * off, p2[1] + ny * off)
        segments.append((e, p1, p2))
        role = e.get("role") or ("adverse" if blocks[e["from"]].get("role") == "adverse" else "neutral")
        color = figstyle.role_colors(S, role)[1] if role != "neutral" else "#222222"
        ax.annotate("", xy=p2, xytext=p1, zorder=4,
                    arrowprops=dict(arrowstyle="-|>,head_width=0.18,head_length=0.3", color=color,
                                    lw=W["arrow"], shrinkA=1, shrinkB=1,
                                    linestyle=LINES[e.get("line", "solid")]))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        length_in = math.hypot(dx / ux, dy / uy)
        need = round(S["badge"]["size"] / 72 + BADGE_ROOM_IN, 2) if "step" in e else MIN_ARROW_IN
        if length_in < need - 0.005:
            issues.append(f"edge {e['from']}->{e['to']} is only {length_in:.2f} in long (min {need} in"
                          f"{' with a step badge' if 'step' in e else ''}); "
                          f"move the blocks apart so the arrow and its badge are visible")
        if e.get("label"):
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
    T = ax.transData

    def disp_rect(r):
        (x0, y0), (x1, y1) = T.transform([[r[0], r[1]], [r[2], r[3]]])
        return Bbox([[x0, y0], [x1, y1]])

    clear = CLEAR_PT * pt
    for b in spec["blocks"]:
        br = disp_rect(rect(b))
        ts = block_texts[b["id"]]
        for t in ts:
            tb = t.get_window_extent()
            if tb.width > br.width - 2 * clear:
                issues.append(f"text '{t.get_text()}' does not fit block '{b['id']}' with {CLEAR_PT:g} pt "
                              f"clearance; widen the block or shorten the text")
            elif (tb.x0 < br.x0 + clear or tb.x1 > br.x1 - clear or tb.y0 < br.y0 + clear
                  or tb.y1 > br.y1 - clear):
                issues.append(f"text '{t.get_text()}' is closer than {CLEAR_PT:g} pt to the border of block "
                              f"'{b['id']}'; enlarge the block or shorten the text")
        if len(ts) == 2 and ts[0].get_window_extent().overlaps(ts[1].get_window_extent()):
            issues.append(f"block '{b['id']}': title and sub-line overlap; enlarge the block or shorten the sub")
    for g, t in group_titles:
        tb = t.get_window_extent()
        if tb.x1 > disp_rect((g["x"], g["y"], g["x"] + g["w"] - 0.1, g["y"] + g["h"])).x1:
            issues.append(f"group title '{t.get_text()}' is wider than its group; shorten it or widen the group")
    for g, im, i, lab in grid_cells:
        cols = max(1, min(int(g.get("cols", len(g["images"]))), len(g["images"])))
        cell_w = (g["w"] - 0.2) / cols
        if lab.get_window_extent().width > disp_rect((0, 0, cell_w, 0)).width:
            issues.append(f"group '{g.get('label', '')}': image label '{lab.get_text()}' is wider than its cell")

    canvas = ax.get_window_extent()
    every = ([(f"group title '{t.get_text()}'", t) for _, t in group_titles]
             + [(f"label '{t.get_text()}'", t) for t in labels]
             + [(f"badge {t.get_text()}", t) for t in badges]
             + [(f"block text '{t.get_text()}'", t) for ts in block_texts.values() for t in ts]
             + [(f"image label '{c[3].get_text()}'", c[3]) for c in grid_cells])
    owner = {id(t): bid for bid, ts in block_texts.items() for t in ts}
    ext = [(name, t, t.get_window_extent().expanded(1.02, 1.05)) for name, t in every]
    for name, _, bb in ext:
        if bb.x0 < canvas.x0 - 1 or bb.x1 > canvas.x1 + 1 or bb.y0 < canvas.y0 - 1 or bb.y1 > canvas.y1 + 1:
            issues.append(f"{name} extends beyond the canvas")
    for i, (n1, t1, b1) in enumerate(ext):
        for n2, t2, b2 in ext[i + 1:]:
            same = owner.get(id(t1)) is not None and owner.get(id(t1)) == owner.get(id(t2))
            if same:
                continue                                   # handled by the title/sub check above
            if b1.overlaps(b2):
                issues.append(f"{n1} overlaps {n2}")
    # group titles must not run into blocks or arrows
    for g, t in group_titles:
        tb = t.get_window_extent()
        for b in spec["blocks"]:
            if tb.overlaps(disp_rect(rect(b))):
                issues.append(f"group title '{t.get_text()}' overlaps block '{b['id']}'")
        (tx0, ty0), (tx1, ty1) = ax.transData.inverted().transform([[tb.x0, tb.y0], [tb.x1, tb.y1]])
        for e, p1, p2 in segments:
            if seg_hits_rect(p1, p2, (tx0, ty0, tx1, ty1)):
                issues.append(f"edge {e['from']}->{e['to']} runs through group title '{t.get_text()}'")
    # groups: disjoint, or nested with a margin
    margin = 0.06
    for i, g1 in enumerate(groups):
        r1 = rect(g1, GPAD)
        for g2 in groups[i + 1:]:
            r2 = rect(g2, GPAD)
            if r1[0] >= r2[2] or r2[0] >= r1[2] or r1[1] >= r2[3] or r2[1] >= r1[3]:
                continue
            def nested(a, b):
                return (a[0] >= b[0] + margin and a[1] >= b[1] + margin and a[2] <= b[2] - margin
                        and a[3] <= b[3] - margin)
            if not (nested(r1, r2) or nested(r2, r1)):
                issues.append(f"groups '{g1.get('label', '')}' and '{g2.get('label', '')}' overlap partly or "
                              f"share a border; make them disjoint or nest one inside the other with a margin")
    # arrows must not pass through other blocks, nor through groups neither endpoint belongs to
    for e, p1, p2 in segments:
        for b in spec["blocks"]:
            if b["id"] in (e["from"], e["to"]):
                continue
            if seg_hits_rect(p1, p2, rect(b), shrink=0.02):
                issues.append(f"edge {e['from']}->{e['to']} passes through block '{b['id']}'; reroute it "
                              f"(move blocks, or pin from_side/to_side)")
        ca, cb = center(blocks[e["from"]]), center(blocks[e["to"]])
        for g in groups:
            r = rect(g, GPAD)
            if inside(ca, r) or inside(cb, r):
                continue
            if seg_hits_rect(p1, p2, r, shrink=0.02):
                issues.append(f"edge {e['from']}->{e['to']} crosses group '{g.get('label', '')}' that neither "
                              f"endpoint belongs to")

    shutil.rmtree(tmp, ignore_errors=True)
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
