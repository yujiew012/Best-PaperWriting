#!/usr/bin/env python3
"""Build the workflow diagram (SVG) for the README.

    python3 docs/diagram/build_workflow.py            # writes docs/images/workflow.svg
    node docs/diagram/render.js                       # renders workflow.png at 3x and checks overlaps

Layout is computed on a fixed grid; every text block, box and arrow carries
data-* attributes so render.js can verify geometrically that nothing overlaps.
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "workflow.svg")
W, H = 1600, 1150
M = 64                      # outer margin

C = {
    "bg": "#FBFAF7", "ink": "#1C2430", "muted": "#5B6573", "hair": "#D8D4CA", "card": "#FFFFFF",
    "write": "#0072B2", "write_tint": "#EAF2F8", "evolve": "#009E73", "evolve_tint": "#E8F4EF",
    "gate": "#D55E00", "chip": "#F1EEE6", "band": "#F3F0E8",
}
SANS, DISPLAY, MONO = "Inter", "Inter Display", "JetBrains Mono"

parts = []
_uid = [0]


def uid(prefix):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def text(x, y, lines, size=13, weight=400, fill=None, family=SANS, anchor="start", lh=None, tracking=0,
         role="text", container=None):
    """Multi-line text block; y is the baseline of the first line."""
    lines = [lines] if isinstance(lines, str) else lines
    lh = lh or round(size * 1.38)
    tid = uid("t")
    attrs = f'data-kind="{role}" id="{tid}"' + (f' data-in="{container}"' if container else "")
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{escape(s)}</tspan>' for i, s in enumerate(lines))
    ls = f' letter-spacing="{tracking}"' if tracking else ""
    parts.append(f'<text {attrs} x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill or C["ink"]}" text-anchor="{anchor}"{ls}>{spans}</text>')
    return tid


def rect(x, y, w, h, fill, stroke=None, sw=1.2, r=10, kind="box", dash=None, bid=None, extra=""):
    bid = bid or uid("b")
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    da = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(f'<rect id="{bid}" data-kind="{kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                 f'fill="{fill}"{st}{da} {extra}/>')
    return bid


def chip(x, y, label, container, w=None):
    """Monospace script/file chip; returns its height."""
    w = w or round(len(label) * 7.2 + 18)
    cid = rect(x, y, w, 22, C["chip"], None, r=5, kind="chip", extra=f'data-in="{container}"')
    text(x + 9, y + 15, label, size=11.5, family=MONO, fill=C["ink"], container=cid, role="chiptext")
    return w


def arrow(points, color=None, label=None, dash=None, ends=None, sw=1.4):
    color = color or C["ink"]
    d = "M " + " L ".join(f"{x} {y}" for x, y in points)
    aid = uid("a")
    da = f' stroke-dasharray="{dash}"' if dash else ""
    marker = "arrow-ink" if color == C["ink"] else ("arrow-write" if color == C["write"] else
                                                     "arrow-evolve" if color == C["evolve"] else "arrow-muted")
    e = f' data-from="{ends[0]}" data-to="{ends[1]}"' if ends else ""
    parts.append(f'<path id="{aid}" data-kind="arrow"{e} d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"'
                 f'{da} stroke-linejoin="round" marker-end="url(#{marker})"/>')
    return aid


def card(x, y, w, h, title, desc, check, accent, tag=None, gate=None):
    cid = rect(x, y, w, h, C["card"], C["hair"], kind="card")
    parts.append(f'<rect data-kind="deco" x="{x}" y="{y + 12}" width="3" height="{h - 24}" rx="1.5" fill="{accent}"/>')
    text(x + 16, y + 26, title, size=14, weight=600, container=cid, role="cardtitle")
    text(x + 16, y + 46, desc, size=12, fill=C["muted"], container=cid, lh=16)
    if check:
        chip(x + 16, y + h - 34, check, cid)
    if gate:                     # a gate takes the chip slot when the branch has no single script
        gw = round(len(gate) * 6.6 + 20)
        gx = x + 16 if not check else x + w - gw - 12
        gid = rect(gx, y + h - 34, gw, 22, C["card"], C["gate"], sw=1, r=11, kind="gate",
                   extra=f'data-in="{cid}"')
        text(gx + gw / 2, y + h - 19, gate, size=10.5, weight=600, fill=C["gate"], anchor="middle",
             container=gid, role="gatetext")
    return cid


# ---------------------------------------------------------------------------
# header
# ---------------------------------------------------------------------------
text(M, 62, "BEST-PAPERWRITING  ·  WORKFLOW", size=11.5, weight=600, fill=C["muted"], tracking=1.6, role="eyebrow")
text(M, 100, "Write with a deterministic SOP. Evolve it from exemplar papers.", size=30, weight=600,
     family=DISPLAY, role="title")
text(M, 128, "Two Agent Skills around one shared core: the model reasons and writes; scripts measure, check and decide.",
     size=14.5, fill=C["muted"], role="subtitle")

# ---------------------------------------------------------------------------
# lane 1: write
# ---------------------------------------------------------------------------
L1 = 176
text(M, L1, "① WRITE", size=12, weight=700, fill=C["write"], tracking=1.4, role="lanelabel")
text(M + 78, L1, "top-tier-paper-writing  ·  runs on your paper", size=12, fill=C["muted"], role="lanelabel")

CARD_TOP, CARD_H, GAP_V = 236, 112, 12
STACK_H = 2 * CARD_H + GAP_V                 # 236 .. 472

# inputs
inp = rect(M, CARD_TOP, 160, STACK_H, C["card"], C["hair"], kind="card")
text(M + 16, CARD_TOP + 28, "Your project", size=14, weight=600, container=inp, role="cardtitle")
yy = CARD_TOP + 52
for f in ["main.tex", "results.csv", "refs.bib", "figures/"]:
    chip(M + 16, yy, f, inp)
    yy += 32
text(M + 16, yy + 18, ["+ target venue", "  & template"], size=12, fill=C["muted"], container=inp, lh=16)

# intake
IX = M + 160 + 36
intake = rect(IX, CARD_TOP, 170, STACK_H, C["write_tint"], C["write"], sw=1.2, kind="card")
text(IX + 16, CARD_TOP + 28, "Intake & routing", size=14, weight=600, container=intake, role="cardtitle")
text(IX + 16, CARD_TOP + 52, ["1  collect context", "2  lint baseline", "3  route by intent",
                              "    (9 branches)"], size=12.5, fill=C["ink"], container=intake, lh=19)
text(IX + 16, CARD_TOP + 150, ["Ground rules:", "never invent numbers;", "never compute by hand;",
                               "load references", "on demand."], size=11.5, fill=C["muted"], container=intake, lh=15.5)
arrow([(M + 160, CARD_TOP + STACK_H / 2), (IX - 3, CARD_TOP + STACK_H / 2)], ends=(inp, intake))

# stage columns
SX = IX + 170 + 36
COLS = 6
CG = 18
CW = (W - M - SX - CG * (COLS - 1)) / COLS
stages = [
    ("1 · DOMAIN", [("Domain profile", ["template: skeleton,", "mandatory elements"], "domain_adapter.py", "H", None)]),
    ("2 · WRITE", [("Draft sections", ["section rules +", "domain template"], "lint_paper.py", "A", None),
                   ("Results → prose", ["claim → evidence", "→ mechanism"], "result_stats.py", "B", None)]),
    ("3 · VISUALIZE", [("Figures", ["your data → exact-", "width vector PDF"], "check_figure.py", "C", None),
                       ("Captions & tables", ["describe what is", "shown, never conclude"], "lint_paper.py", "D", None)]),
    ("4 · CITE", [("Bibliography", ["deterministic checks,", "then verify sources"], "check_bib.py", "F", None)]),
    ("5 · LAY OUT", [("Float placement", ["baseline → one fix", "→ compare, revert"], "layout_check.py", "E", None)]),
    ("6 · SUBMIT", [("Revision", ["reruns every check;", "arXiv, extension"], None, "G", "you submit")]),
]
col_x = [SX + i * (CW + CG) for i in range(COLS)]
first_cards, col_bottoms = [], []
for i, (head, cards) in enumerate(stages):
    x = col_x[i]
    text(x, CARD_TOP - 14, head, size=11, weight=700, fill=C["write"], tracking=1.2, role="stagehead")
    y = CARD_TOP
    for j, (title, desc, chk, letter, gate) in enumerate(cards):
        cid = card(x, y, CW, CARD_H, title, desc, chk, C["write"], gate=gate)
        text(x + CW - 14, y + 26, letter, size=11, weight=600, fill=C["muted"], family=MONO, anchor="end",
             container=cid, role="branchletter")
        if j == 0:
            first_cards.append(cid)
        y += CARD_H + GAP_V
    col_bottoms.append(y - GAP_V)
arrow([(IX + 170, CARD_TOP + CARD_H / 2), (col_x[0] - 3, CARD_TOP + CARD_H / 2)], ends=(intake, first_cards[0]))
for i in range(COLS - 1):   # run-order chevrons between stage headers
    xa = col_x[i] + CW + 3
    xb = col_x[i + 1] - 3
    arrow([(xa, CARD_TOP + CARD_H / 2), (xb, CARD_TOP + CARD_H / 2)], color=C["write"], sw=1.2,
          ends=(first_cards[i], first_cards[i + 1]))

# verify bar
VB_Y = CARD_TOP + STACK_H + 34                # 506
VB_H = 46
vb = rect(SX, VB_Y, W - M - SX, VB_H, C["card"], C["ink"], sw=1.2, kind="card")
text(SX + 18, VB_Y + 28, "Verify  →  Definition of Done", size=13.5, weight=600, container=vb, role="cardtitle")
text(SX + 236, VB_Y + 28, "every branch ends in a script check (exit 0)  ·  failure: diagnose, fix, rerun ≤ 3×, then report",
     size=12.5, fill=C["muted"], container=vb)
for i, x in enumerate(col_x):
    cx = x + CW / 2
    arrow([(cx, col_bottoms[i]), (cx, VB_Y - 3)], color=C["muted"], sw=1.1)

# ---------------------------------------------------------------------------
# shared core: the skill
# ---------------------------------------------------------------------------
B_Y, B_H = 612, 100
band = rect(M, B_Y, W - 2 * M, B_H, C["band"], C["ink"], sw=1.2, r=12, kind="card")
text(M + 20, B_Y + 30, "THE SKILL", size=11.5, weight=700, fill=C["ink"], tracking=1.6, container=band,
     role="bandlabel")
text(M + 20, B_Y + 52, ["shared core,", "read by ①, improved by ②"], size=12, fill=C["muted"], container=band, lh=16)
cells = [("SKILL.md", "SOP · routing · gates · DoD"), ("references/writing/", "rules for each section"),
         ("references/domains/", "5 standardized templates"), ("scripts/", "deterministic checkers"),
         ("evolution_ledger.json", "rule ↔ evidence")]
cx0 = M + 250
cw = (W - M - 20 - cx0 - 14 * (len(cells) - 1)) / len(cells)
cell_ids = []
for i, (name, sub) in enumerate(cells):
    x = cx0 + i * (cw + 14)
    cid = rect(x, B_Y + 18, cw, B_H - 36, C["card"], C["hair"], r=8, kind="cell", extra=f'data-in="{band}"')
    text(x + 14, B_Y + 44, name, size=12, family=MONO, weight=500, container=cid)
    text(x + 14, B_Y + 64, sub, size=11.5, fill=C["muted"], container=cid)
    cell_ids.append(cid)
# band -> intake: the SOP is loaded first
ix_c = IX + 85
arrow([(ix_c, B_Y), (ix_c, CARD_TOP + STACK_H + 3)], color=C["write"], ends=(band, intake))
text(ix_c + 10, B_Y - 26, ["loads SOP; references", "& scripts on demand"], size=11.5, fill=C["write"], lh=15,
     role="arrowlabel")

# ---------------------------------------------------------------------------
# lane 2: evolve
# ---------------------------------------------------------------------------
L2 = 770
text(M, L2, "② EVOLVE", size=12, weight=700, fill=C["evolve"], tracking=1.4, role="lanelabel")
text(M + 84, L2, "evolve-paper-skill  ·  maintainer loop, × N iterations", size=12, fill=C["muted"], role="lanelabel")

R_Y, R_H = 846, 126
widths = [150, 176, 176, 176, 260]
gap = (W - 2 * M - sum(widths)) / 4
xs = [M]
for w_ in widths[:-1]:
    xs.append(xs[-1] + w_ + gap)

# exemplar paper (document shape with folded corner)
px, pw = xs[0], widths[0]
fold = 18
paper_id = "paper"
parts.append(f'<path id="{paper_id}" data-kind="card" d="M {px} {R_Y + 8} Q {px} {R_Y} {px + 8} {R_Y} '
             f'L {px + pw - fold} {R_Y} L {px + pw} {R_Y + fold} L {px + pw} {R_Y + R_H - 8} '
             f'Q {px + pw} {R_Y + R_H} {px + pw - 8} {R_Y + R_H} L {px + 8} {R_Y + R_H} '
             f'Q {px} {R_Y + R_H} {px} {R_Y + R_H - 8} Z" fill="{C["card"]}" stroke="{C["ink"]}" stroke-width="1.2"/>')
parts.append(f'<path data-kind="deco" d="M {px + pw - fold} {R_Y} L {px + pw - fold} {R_Y + fold} L {px + pw} {R_Y + fold}" '
             f'fill="none" stroke="{C["ink"]}" stroke-width="1.2"/>')
text(px + 16, R_Y + 34, "Exemplar", size=14, weight=600, container=paper_id, role="cardtitle")
text(px + 16, R_Y + 54, ["published top-tier", "paper (PDF / MD)"], size=12, fill=C["muted"], container=paper_id, lh=16)
text(px + 16, R_Y + 106, "gold standard", size=11.5, weight=600, fill=C["evolve"], container=paper_id)


def agent(i, title, lines, note):
    x, w_ = xs[i], widths[i]
    aid = rect(x, R_Y, w_, R_H, C["card"], C["evolve"], sw=1.3, kind="card")
    clip = uid("clip")           # accent bar follows the card's rounded corners
    parts.append(f'<clipPath id="{clip}"><rect x="{x}" y="{R_Y}" width="{w_}" height="{R_H}" rx="10"/></clipPath>'
                 f'<rect data-kind="deco" x="{x}" y="{R_Y}" width="{w_}" height="6" fill="{C["evolve"]}" '
                 f'clip-path="url(#{clip})"/>')
    text(x + 16, R_Y + 28, "SUB-AGENT", size=10, weight=700, fill=C["evolve"], tracking=1.3, container=aid)
    text(x + 16, R_Y + 50, title, size=15, weight=600, container=aid, role="cardtitle")
    text(x + 16, R_Y + 72, lines, size=12, fill=C["muted"], container=aid, lh=16)
    if note:
        text(x + 16, R_Y + R_H - 14, note, size=11, weight=600, fill=C["evolve"], container=aid)
    return aid


ext = agent(1, "Extractor", ["idea, method, data", "as structured facts"], "no copied prose")
wri = agent(2, "Writer", ["drafts the full paper", "by following the skill"], "never sees the paper")
rev = agent(3, "Reviewer", ["draft vs. original:", "8 scores + typed gaps"], "root cause · scope")

ox, ow = xs[4], widths[4]
orch = rect(ox, R_Y, ow, R_H, C["ink"], None, kind="card")
text(ox + 18, R_Y + 28, "MAIN AGENT  ·  evolve.py", size=10, weight=700, fill="#9FD9C4", tracking=1.3, container=orch)
text(ox + 18, R_Y + 50, "Generalize & guard", size=15, weight=600, fill="#FFFFFF", container=orch, role="cardtitle")
text(ox + 18, R_Y + 72, ["paper-specific gaps → dropped", "rules: ledger id + evidence",
                         "keep best · revert on score drop"], size=12, fill="#C9D1DA", container=orch, lh=16)

mid = R_Y + R_H / 2
artifacts = ["materials.json", "draft/", "review.json"]
pairs = [(paper_id, ext), (ext, wri), (wri, rev), (rev, orch)]
for i in range(4):
    a_x = xs[i] + widths[i]
    b_x = xs[i + 1]
    arrow([(a_x, mid), (b_x - 3, mid)], color=C["ink"], ends=pairs[i])
    if i >= 1:
        text((a_x + b_x) / 2, mid - 12, artifacts[i - 1], size=11.5, family=MONO, anchor="middle", role="arrowlabel")

# information barrier between Extractor and Writer
bx = (xs[1] + widths[1] + xs[2]) / 2
parts.append(f'<line data-kind="barrier" x1="{bx}" y1="{R_Y - 8}" x2="{bx}" y2="{mid - 38}" stroke="{C["gate"]}" '
             f'stroke-width="1.4" stroke-dasharray="4 4"/>')
parts.append(f'<line data-kind="barrier" x1="{bx}" y1="{mid + 12}" x2="{bx}" y2="{R_Y + R_H + 8}" stroke="{C["gate"]}" '
             f'stroke-width="1.4" stroke-dasharray="4 4"/>')
text(bx, R_Y + R_H + 26, "information barrier", size=11, weight=600, fill=C["gate"], anchor="middle", role="arrowlabel")

# gold standard path: paper -> reviewer (below the row)
gy = R_Y + R_H + 56
rx_c = xs[3] + widths[3] / 2
arrow([(px + pw / 2, R_Y + R_H), (px + pw / 2, gy), (rx_c, gy), (rx_c, R_Y + R_H + 3)], color=C["muted"],
      dash="5 4", ends=(paper_id, rev))
text((px + pw / 2 + rx_c) / 2 + 60, gy + 20, "original paper → reviewer only (gold standard)", size=11.5,
     fill=C["muted"], anchor="middle", role="arrowlabel")

# band <-> lane 2
w_c = xs[2] + widths[2] / 2
arrow([(w_c, B_Y + B_H), (w_c, R_Y - 3)], color=C["evolve"], ends=(band, wri))
text(w_c + 12, B_Y + B_H + 30, ["reads the current", "skill snapshot"], size=11.5, fill=C["evolve"], lh=15,
     role="arrowlabel")
o_c = ox + ow / 2
arrow([(o_c, R_Y), (o_c, B_Y + B_H + 3)], color=C["evolve"], ends=(orch, band))
text(o_c - 12, B_Y + B_H + 30, ["writes generalized rules only;", "check-edits must pass"], size=11.5,
     fill=C["evolve"], anchor="end", lh=15, role="arrowlabel")
gw = 118
gid = rect(o_c + 14, B_Y + B_H + 18, gw, 22, C["card"], C["gate"], sw=1, r=11, kind="gate")
text(o_c + 14 + gw / 2, B_Y + B_H + 33, "you approve diff", size=10.5, weight=600, fill=C["gate"], anchor="middle",
     container=gid)

# ---------------------------------------------------------------------------
# legend
# ---------------------------------------------------------------------------
LY = H - 40
lx = M
parts.append(f'<line data-kind="deco" x1="{M}" y1="{LY - 30}" x2="{W - M}" y2="{LY - 30}" stroke="{C["hair"]}" stroke-width="1"/>')
lid = rect(lx, LY - 15, 72, 22, C["chip"], None, r=5, kind="chip")
text(lx + 9, LY + 0, "script", size=11.5, family=MONO, container=lid)
text(lx + 84, LY, "deterministic check, decides by exit code", size=12, fill=C["muted"], role="legend")
lx += 400
gl = rect(lx, LY - 15, 64, 20, C["card"], C["gate"], sw=1, r=10, kind="gate")
text(lx + 32, LY - 1, "gate", size=10.5, weight=600, fill=C["gate"], anchor="middle", container=gl)
text(lx + 76, LY, "human approval", size=12, fill=C["muted"], role="legend")
lx += 250
parts.append(f'<line data-kind="deco" x1="{lx}" y1="{LY - 4}" x2="{lx + 40}" y2="{LY - 4}" stroke="{C["gate"]}" '
             f'stroke-width="1.4" stroke-dasharray="4 4"/>')
text(lx + 52, LY, "information barrier", size=12, fill=C["muted"], role="legend")
lx += 230
parts.append(f'<rect data-kind="deco" x="{lx}" y="{LY - 12}" width="26" height="14" rx="3" fill="{C["card"]}" '
             f'stroke="{C["evolve"]}" stroke-width="1.3"/>')
text(lx + 38, LY, "sub-agent (fresh context)", size=12, fill=C["muted"], role="legend")
text(W - M, LY, "github.com/yujiew012/Best-PaperWriting", size=11.5, family=MONO, fill=C["muted"], anchor="end",
     role="legend")

# ---------------------------------------------------------------------------
defs = "".join(
    f'<marker id="arrow-{n}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    f'orient="auto-start-reverse"><path d="M 0 1 L 9 5 L 0 9 z" fill="{c}"/></marker>'
    for n, c in [("ink", C["ink"]), ("write", C["write"]), ("evolve", C["evolve"]), ("muted", C["muted"])])
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<defs>{defs}</defs><rect data-kind="bg" width="{W}" height="{H}" fill="{C["bg"]}"/>'
       + "".join(parts) + "</svg>\n")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {os.path.relpath(OUT)} ({W}x{H})")
