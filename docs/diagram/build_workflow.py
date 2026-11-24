#!/usr/bin/env python3
"""Build the workflow diagram (SVG) for the README.

    python3 docs/diagram/build_workflow.py            # writes docs/images/workflow.svg
    node docs/diagram/render.js                       # renders workflow.png at 3x and checks the layout

Style: white background, no heavy fills; elements are defined by strong outlines
in the lane colour, large type and thick lines. Every text block, box and arrow
carries data-* attributes so render.js can verify geometrically that nothing
overlaps and every text fits its box.
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "workflow.svg")
W, H = 1900, 1380
M = 60

C = {
    "bg": "#FFFFFF", "ink": "#16202B", "muted": "#4A5563", "line": "#7A8594",
    "write": "#0072B2", "evolve": "#009E73", "gate": "#D55E00", "white": "#FFFFFF",
}
SANS, DISPLAY, MONO = "Inter", "Inter Display", "JetBrains Mono"
SW = 2.0          # default outline weight
AW = 2.2          # arrow weight

parts = []
_uid = [0]


def uid(prefix):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def text(x, y, lines, size=15, weight=400, fill=None, family=SANS, anchor="start", lh=None, tracking=0,
         role="text", container=None):
    """Multi-line text block; y is the baseline of the first line."""
    lines = [lines] if isinstance(lines, str) else lines
    lh = lh or round(size * 1.35)
    tid = uid("t")
    attrs = f'data-kind="{role}" id="{tid}"' + (f' data-in="{container}"' if container else "")
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(s)}</tspan>' for i, s in enumerate(lines))
    ls = f' letter-spacing="{tracking}"' if tracking else ""
    parts.append(f'<text {attrs} x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill or C["ink"]}" text-anchor="{anchor}"{ls}>{spans}</text>')
    return tid


def rect(x, y, w, h, stroke, sw=SW, r=12, kind="box", dash=None, bid=None, extra="", fill=None):
    bid = bid or uid("b")
    da = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<rect id="{bid}" data-kind="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                 f'fill="{fill or C["white"]}" stroke="{stroke}" stroke-width="{sw}"{da} {extra}/>')
    return bid


def chip(x, y, label, container, color=None):
    """Outlined monospace chip for a script or file name."""
    w = round(len(label) * 8.7 + 22)
    cid = rect(x, y, w, 28, color or C["line"], sw=1.5, r=6, kind="chip", extra=f'data-in="{container}"')
    text(x + 11, y + 19.5, label, size=14, family=MONO, weight=500, fill=C["ink"], container=cid,
         role="chiptext")
    return w


def gate(x, y, label, container=None):
    w = round(len(label) * 7.6 + 26)
    gid = rect(x, y, w, 28, C["gate"], sw=1.8, r=14, kind="gate",
               extra=f'data-in="{container}"' if container else "")
    text(x + w / 2, y + 19, label, size=13.5, weight=700, fill=C["gate"], anchor="middle", container=gid,
         role="gatetext")
    return w


def arrow(points, color=None, dash=None, ends=None, sw=AW):
    color = color or C["ink"]
    d = "M " + " L ".join(f"{x} {y}" for x, y in points)
    aid = uid("a")
    da = f' stroke-dasharray="{dash}"' if dash else ""
    marker = {C["ink"]: "ink", C["write"]: "write", C["evolve"]: "evolve"}.get(color, "line")
    e = f' data-from="{ends[0]}" data-to="{ends[1]}"' if ends else ""
    parts.append(f'<path id="{aid}" data-kind="arrow"{e} d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"'
                 f'{da} stroke-linejoin="round" stroke-linecap="round" marker-end="url(#arrow-{marker})"/>')
    return aid


# ---------------------------------------------------------------------------
# header
# ---------------------------------------------------------------------------
text(M, 64, "BEST-PAPERWRITING  ·  WORKFLOW", size=14, weight=700, fill=C["muted"], tracking=2, role="eyebrow")
text(M, 112, "Write with a deterministic SOP. Evolve it from exemplar papers.", size=38, weight=700,
     family=DISPLAY, role="title")
text(M, 150, "Two Agent Skills around one shared core: the model reasons and writes; scripts measure, check and decide.",
     size=18, fill=C["muted"], role="subtitle")

# ---------------------------------------------------------------------------
# lane 1: write
# ---------------------------------------------------------------------------
L1 = 212
text(M, L1, "① WRITE", size=16, weight=800, fill=C["write"], tracking=1.6, role="lanelabel")
text(M + 108, L1, "top-tier-paper-writing  ·  runs on your paper", size=16, fill=C["muted"], role="lanelabel")

CARD_TOP, CARD_H, GAP_V = 268, 140, 16
STACK_H = 2 * CARD_H + GAP_V

# inputs
IN_W = 170
inp = rect(M, CARD_TOP, IN_W, STACK_H, C["ink"], kind="card")
text(M + 18, CARD_TOP + 34, "Your project", size=18, weight=700, container=inp, role="cardtitle")
yy = CARD_TOP + 56
for f in ["main.tex", "results.csv", "refs.bib", "figures/"]:
    chip(M + 18, yy, f, inp)
    yy += 40
text(M + 18, yy + 28, ["+ target venue", "& template"], size=15, fill=C["muted"], container=inp, lh=20)

# intake
IX = M + IN_W + 36
IN2_W = 200
intake = rect(IX, CARD_TOP, IN2_W, STACK_H, C["write"], sw=2.6, kind="card")
text(IX + 18, CARD_TOP + 34, "Intake & routing", size=18, weight=700, container=intake, role="cardtitle")
text(IX + 18, CARD_TOP + 64, ["1  collect context", "2  lint baseline", "3  route by intent", "    (9 branches)"],
     size=15, container=intake, lh=22)
text(IX + 18, CARD_TOP + 178, ["Ground rules:", "never invent numbers;", "never compute by hand;",
                               "load references", "on demand."], size=14, fill=C["muted"], container=intake, lh=19)
arrow([(M + IN_W, CARD_TOP + STACK_H / 2), (IX - 4, CARD_TOP + STACK_H / 2)], ends=(inp, intake))

# stage columns
SX = IX + IN2_W + 36
COLS, CG = 6, 20
CW = (W - M - SX - CG * (COLS - 1)) / COLS
stages = [
    ("1 · DOMAIN", [("Domain profile", ["template: skeleton,", "mandatory elements"], "domain_adapter.py", None)]),
    ("2 · WRITE", [("Draft sections", ["section rules +", "domain template"], "lint_paper.py", None),
                   ("Results → prose", ["claim → evidence", "→ mechanism"], "result_stats.py", None)]),
    ("3 · VISUALIZE", [("Figures", ["your data → exact-", "width vector PDF"], "check_figure.py", None),
                       ("Captions & tables", ["describe what is shown,", "never conclude"], "lint_paper.py", None)]),
    ("4 · CITE", [("Bibliography", ["deterministic checks,", "then verify sources"], "check_bib.py", None)]),
    ("5 · LAY OUT", [("Float placement", ["baseline → one fix", "→ compare, revert"], "layout_check.py", None)]),
    ("6 · SUBMIT", [("Revision", ["reruns every check;", "arXiv, extension"], None, "you submit")]),
]
col_x = [SX + i * (CW + CG) for i in range(COLS)]
first_cards, col_bottoms = [], []
for i, (head, cards) in enumerate(stages):
    x = col_x[i]
    text(x, CARD_TOP - 18, head, size=14, weight=800, fill=C["write"], tracking=1.4, role="stagehead")
    y = CARD_TOP
    for j, (title, desc, chk, gt) in enumerate(cards):
        cid = rect(x, y, CW, CARD_H, C["write"], kind="card")
        text(x + 18, y + 34, title, size=18, weight=700, container=cid, role="cardtitle")
        text(x + 18, y + 60, desc, size=15, fill=C["muted"], container=cid, lh=20)
        if chk:
            chip(x + 18, y + CARD_H - 44, chk, cid)
        if gt:
            gate(x + 18, y + CARD_H - 44, gt, cid)
        if j == 0:
            first_cards.append(cid)
        y += CARD_H + GAP_V
    col_bottoms.append(y - GAP_V)
arrow([(IX + IN2_W, CARD_TOP + CARD_H / 2), (col_x[0] - 4, CARD_TOP + CARD_H / 2)], ends=(intake, first_cards[0]))
for i in range(COLS - 1):
    arrow([(col_x[i] + CW, CARD_TOP + CARD_H / 2), (col_x[i + 1] - 4, CARD_TOP + CARD_H / 2)], color=C["write"],
          ends=(first_cards[i], first_cards[i + 1]))

# verify bar
VB_Y, VB_H = CARD_TOP + STACK_H + 44, 58
vb = rect(SX, VB_Y, W - M - SX, VB_H, C["ink"], sw=2.4, kind="card")
text(SX + 22, VB_Y + 37, "Verify  →  Definition of Done", size=17, weight=700, container=vb, role="cardtitle")
text(SX + 300, VB_Y + 37, "every branch ends in a script check (exit 0)  ·  on failure: diagnose, fix, rerun ≤ 3×, "
     "then report", size=15, fill=C["muted"], container=vb)
for i, x in enumerate(col_x):
    arrow([(x + CW / 2, col_bottoms[i]), (x + CW / 2, VB_Y - 4)], color=C["line"], sw=1.8)

# ---------------------------------------------------------------------------
# shared core: the skill
# ---------------------------------------------------------------------------
B_Y, B_H = 746, 124
band = rect(M, B_Y, W - 2 * M, B_H, C["ink"], sw=2.6, r=14, kind="card")
text(M + 24, B_Y + 40, "THE SKILL", size=16, weight=800, tracking=2, container=band, role="bandlabel")
text(M + 24, B_Y + 68, ["shared core: read by ①,", "improved by ②"], size=15, fill=C["muted"], container=band, lh=20)
cells = [("SKILL.md", "SOP · routing · gates · DoD"), ("references/writing/", "rules for each section"),
         ("references/domains/", "5 standardized templates"), ("scripts/", "deterministic checkers"),
         ("evolution_ledger.json", "rule ↔ evidence")]
cx0 = M + 300
cgap = 16
cw = (W - M - 22 - cx0 - cgap * (len(cells) - 1)) / len(cells)
for i, (name, sub) in enumerate(cells):
    x = cx0 + i * (cw + cgap)
    cid = rect(x, B_Y + 22, cw, B_H - 44, C["line"], sw=1.6, r=9, kind="cell", extra=f'data-in="{band}"')
    text(x + 16, B_Y + 54, name, size=15, family=MONO, weight=600, container=cid)
    text(x + 16, B_Y + 78, sub, size=14.5, fill=C["muted"], container=cid)
ix_c = IX + IN2_W / 2
arrow([(ix_c, B_Y), (ix_c, CARD_TOP + STACK_H + 4)], color=C["write"], ends=(band, intake))
text(ix_c + 14, VB_Y + VB_H + 24, ["loads SOP; references", "& scripts on demand"], size=15, weight=600,
     fill=C["write"], lh=19, role="arrowlabel")

# ---------------------------------------------------------------------------
# lane 2: evolve
# ---------------------------------------------------------------------------
L2 = 928
text(M, L2, "② EVOLVE", size=16, weight=800, fill=C["evolve"], tracking=1.6, role="lanelabel")
text(M + 118, L2, "evolve-paper-skill  ·  maintainer loop, × N iterations", size=16, fill=C["muted"],
     role="lanelabel")

R_Y, R_H = 1010, 154
widths = [176, 214, 214, 214, 310]
gap = (W - 2 * M - sum(widths)) / 4
xs = [M]
for w_ in widths[:-1]:
    xs.append(xs[-1] + w_ + gap)

# exemplar paper (document with folded corner)
px, pw = xs[0], widths[0]
fold = 22
paper_id = "paper"
parts.append(f'<path id="{paper_id}" data-kind="card" d="M {px} {R_Y + 10} Q {px} {R_Y} {px + 10} {R_Y} '
             f'L {px + pw - fold} {R_Y} L {px + pw} {R_Y + fold} L {px + pw} {R_Y + R_H - 10} '
             f'Q {px + pw} {R_Y + R_H} {px + pw - 10} {R_Y + R_H} L {px + 10} {R_Y + R_H} '
             f'Q {px} {R_Y + R_H} {px} {R_Y + R_H - 10} Z" fill="{C["white"]}" stroke="{C["ink"]}" '
             f'stroke-width="{SW + 0.4}" stroke-linejoin="round"/>')
parts.append(f'<path data-kind="deco" d="M {px + pw - fold} {R_Y} L {px + pw - fold} {R_Y + fold} L {px + pw} '
             f'{R_Y + fold}" fill="none" stroke="{C["ink"]}" stroke-width="{SW + 0.4}" stroke-linejoin="round"/>')
text(px + 18, R_Y + 40, "Exemplar", size=19, weight=700, container=paper_id, role="cardtitle")
text(px + 18, R_Y + 66, ["published top-tier", "paper (PDF / MD)"], size=15, fill=C["muted"], container=paper_id, lh=20)
text(px + 18, R_Y + R_H - 20, "gold standard", size=14, weight=700, fill=C["evolve"], container=paper_id)


def agent(i, title, lines, note):
    x, w_ = xs[i], widths[i]
    aid = rect(x, R_Y, w_, R_H, C["evolve"], sw=2.6, kind="card")
    text(x + 18, R_Y + 32, "SUB-AGENT", size=12.5, weight=800, fill=C["evolve"], tracking=1.6, container=aid)
    text(x + 18, R_Y + 60, title, size=20, weight=700, container=aid, role="cardtitle")
    text(x + 18, R_Y + 86, lines, size=15, fill=C["muted"], container=aid, lh=20)
    text(x + 18, R_Y + R_H - 18, note, size=14, weight=700, fill=C["evolve"], container=aid)
    return aid


ext = agent(1, "Extractor", ["idea, method, data", "as structured facts"], "no copied prose")
wri = agent(2, "Writer", ["drafts the full paper", "by following the skill"], "never sees the paper")
rev = agent(3, "Reviewer", ["draft vs. original:", "8 scores + typed gaps"], "root cause · scope")

ox, ow = xs[4], widths[4]
orch = rect(ox, R_Y, ow, R_H, C["ink"], sw=3, kind="card")
text(ox + 20, R_Y + 32, "MAIN AGENT  ·  evolve.py", size=12.5, weight=800, fill=C["evolve"], tracking=1.6,
     container=orch)
text(ox + 20, R_Y + 60, "Generalize & guard", size=20, weight=700, container=orch, role="cardtitle")
text(ox + 20, R_Y + 86, ["paper-specific gaps → dropped", "rules: ledger id + evidence",
                         "keep best · revert on score drop"], size=15, fill=C["muted"], container=orch, lh=20)

mid = R_Y + R_H / 2
artifacts = ["materials.json", "draft/", "review.json"]
pairs = [(paper_id, ext), (ext, wri), (wri, rev), (rev, orch)]
for i in range(4):
    a_x, b_x = xs[i] + widths[i], xs[i + 1]
    arrow([(a_x, mid), (b_x - 4, mid)], ends=pairs[i])
    if i >= 1:
        text((a_x + b_x) / 2, mid - 16, artifacts[i - 1], size=15, family=MONO, weight=600, anchor="middle",
             role="arrowlabel")

# information barrier
bx = (xs[1] + widths[1] + xs[2]) / 2
for y1, y2 in [(R_Y - 10, mid - 46), (mid + 14, R_Y + R_H + 10)]:
    parts.append(f'<line data-kind="barrier" x1="{bx}" y1="{y1}" x2="{bx}" y2="{y2}" stroke="{C["gate"]}" '
                 f'stroke-width="2.4" stroke-dasharray="7 6" stroke-linecap="round"/>')
text(bx, R_Y + R_H + 34, "information barrier", size=15, weight=700, fill=C["gate"], anchor="middle",
     role="arrowlabel")

# gold-standard path
gy = R_Y + R_H + 72
rx_c = xs[3] + widths[3] / 2
arrow([(px + pw / 2, R_Y + R_H), (px + pw / 2, gy), (rx_c, gy), (rx_c, R_Y + R_H + 4)], color=C["line"],
      dash="8 6", ends=(paper_id, rev))
text((px + pw / 2 + rx_c) / 2 + 90, gy + 28, "original paper → reviewer only (gold standard)", size=15,
     fill=C["muted"], anchor="middle", role="arrowlabel")

# core <-> lane 2
w_c = xs[2] + widths[2] / 2
arrow([(w_c, B_Y + B_H), (w_c, R_Y - 4)], color=C["evolve"], ends=(band, wri))
text(w_c + 14, B_Y + B_H + 34, ["reads the current", "skill snapshot"], size=15, weight=600, fill=C["evolve"],
     lh=19, role="arrowlabel")
o_c = ox + ow * 0.42            # left of centre so the approval pill stays inside the margin
arrow([(o_c, R_Y), (o_c, B_Y + B_H + 4)], color=C["evolve"], ends=(orch, band))
text(o_c - 14, B_Y + B_H + 34, ["writes generalized rules only;", "check-edits must pass"], size=15, weight=600,
     fill=C["evolve"], anchor="end", lh=19, role="arrowlabel")
gate(o_c + 16, B_Y + B_H + 20, "you approve diff")

# ---------------------------------------------------------------------------
# legend
# ---------------------------------------------------------------------------
LY = H - 42
parts.append(f'<line data-kind="rule" x1="{M}" y1="{LY - 38}" x2="{W - M}" y2="{LY - 38}" stroke="{C["line"]}" '
             f'stroke-width="1.5"/>')
lx = M
lid = rect(lx, LY - 20, round(len("script") * 8.7 + 22), 28, C["line"], sw=1.5, r=6, kind="chip")
text(lx + 11, LY - 0.5, "script", size=14, family=MONO, weight=500, container=lid)
text(lx + 92, LY, "deterministic check, decides by exit code", size=15, fill=C["muted"], role="legend")
lx += 470
gate(lx, LY - 20, "gate")
text(lx + 76, LY, "human approval", size=15, fill=C["muted"], role="legend")
lx += 300
parts.append(f'<line data-kind="deco" x1="{lx}" y1="{LY - 6}" x2="{lx + 48}" y2="{LY - 6}" stroke="{C["gate"]}" '
             f'stroke-width="2.4" stroke-dasharray="7 6" stroke-linecap="round"/>')
text(lx + 62, LY, "information barrier", size=15, fill=C["muted"], role="legend")
lx += 280
parts.append(f'<rect data-kind="deco" x="{lx}" y="{LY - 18}" width="34" height="22" rx="5" fill="{C["white"]}" '
             f'stroke="{C["evolve"]}" stroke-width="2.6"/>')
text(lx + 48, LY, "sub-agent (fresh context)", size=15, fill=C["muted"], role="legend")
text(W - M, LY, "github.com/yujiew012/Best-PaperWriting", size=14, family=MONO, fill=C["muted"], anchor="end",
     role="legend")

# ---------------------------------------------------------------------------
defs = "".join(
    f'<marker id="arrow-{n}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.2" markerHeight="5.2" '
    f'orient="auto-start-reverse"><path d="M 0 0.8 L 9.5 5 L 0 9.2 z" fill="{c}"/></marker>'
    for n, c in [("ink", C["ink"]), ("write", C["write"]), ("evolve", C["evolve"]), ("line", C["line"])])
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<defs>{defs}</defs><rect data-kind="bg" width="{W}" height="{H}" fill="{C["bg"]}"/>'
       + "".join(parts) + "</svg>\n")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {os.path.relpath(OUT)} ({W}x{H})")
