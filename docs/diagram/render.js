// Render docs/images/workflow.svg to a high-resolution PNG and verify the layout geometrically.
//   node docs/diagram/render.js [scale]      (default scale 3 -> 5700 px wide)
// Exit code 1 if any check fails: text outside its box, overlapping boxes or labels,
// arrows crossing boxes, labels or other arrows, or anything outside the canvas.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const scale = Number(process.argv[2] || 3);
  const svgPath = path.join(__dirname, '..', 'images', 'workflow.svg');
  const pngPath = path.join(__dirname, '..', 'images', 'workflow.png');
  const svg = fs.readFileSync(svgPath, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: scale, viewport: { width: 2000, height: 1500 } });
  await page.setContent(`<!doctype html><html><body style="margin:0;background:#fff">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);

  const problems = await page.evaluate(() => {
    const svg = document.querySelector('svg');
    const vb = svg.viewBox.baseVal;
    const out = [];
    const box = el => { const b = el.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, x2: b.x + b.width, y2: b.y + b.height }; };
    const inter = (a, b, pad = 0) => a.x < b.x2 - pad && b.x < a.x2 - pad && a.y < b.y2 - pad && b.y < a.y2 - pad;
    const inside = (a, b, pad = 0) => a.x >= b.x + pad && a.y >= b.y + pad && a.x2 <= b.x2 - pad && a.y2 <= b.y2 - pad;
    const name = el => `${el.dataset.kind}#${el.id}${el.textContent ? ` "${el.textContent.slice(0, 40)}"` : ''}`;

    const all = [...svg.querySelectorAll('[data-kind]')];
    const boxes = all.filter(e => ['card', 'chip', 'cell', 'gate'].includes(e.dataset.kind));
    const texts = all.filter(e => e.tagName === 'text');
    const arrows = all.filter(e => e.dataset.kind === 'arrow');
    const barriers = all.filter(e => e.dataset.kind === 'barrier');
    const byId = id => document.getElementById(id);
    const ancestors = el => { const a = []; let c = el; while (c && c.dataset.in) { c = byId(c.dataset.in); if (c) a.push(c); } return a; };
    const related = (a, b) => ancestors(a).includes(b) || ancestors(b).includes(a);

    // 1. content margin: everything stays inside the 60 px margin used by the layout (2 px tolerance)
    for (const e of [...boxes, ...texts]) {
      const b = box(e);
      if (b.x < 58 || b.y < 32 || b.x2 > vb.width - 58 || b.y2 > vb.height - 24) out.push(`outside the margin: ${name(e)}`);
    }
    // 2. text inside its container (with padding)
    for (const t of texts) {
      if (!t.dataset.in) continue;
      const c = byId(t.dataset.in);
      if (!inside(box(t), box(c), 3)) out.push(`text does not fit its box: ${name(t)} in ${name(c)}`);
    }
    // 3. text vs text
    for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++)
      if (inter(box(texts[i]), box(texts[j]), -3)) out.push(`texts closer than 3px: ${name(texts[i])} / ${name(texts[j])}`);
    // 4. free text vs boxes
    for (const t of texts) for (const b of boxes) {
      if (t.dataset.in && (t.dataset.in === b.id || ancestors(t).includes(b))) continue;
      if (inter(box(t), box(b), -3)) out.push(`text closer than 3px to box: ${name(t)} / ${name(b)}`);
    }
    // 5. box vs box (unless nested)
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (related(a, b)) continue;
      if (inter(box(a), box(b), -4)) out.push(`boxes closer than 4px: ${name(a)} / ${name(b)}`);
    }
    // 6. arrows: no passage through boxes or text, no crossings between arrows
    const samples = p => { const L = p.getTotalLength(), pts = []; for (let s = 3; s < L - 3; s += 2) pts.push(p.getPointAtLength(s)); return pts; };
    const inBox = (pt, b, pad) => pt.x > b.x + pad && pt.x < b.x2 - pad && pt.y > b.y + pad && pt.y < b.y2 - pad;
    for (const a of arrows) {
      const pts = samples(a);
      const ends = [a.dataset.from, a.dataset.to];
      for (const b of boxes) {
        if (ends.includes(b.id)) continue;
        const bb = box(b);
        if (pts.some(pt => inBox(pt, bb, 1))) out.push(`arrow crosses box: ${name(a)} / ${name(b)}`);
      }
      for (const t of texts) {
        const tb = box(t);
        if (pts.some(pt => inBox(pt, { x: tb.x - 2, y: tb.y - 2, x2: tb.x2 + 2, y2: tb.y2 + 2 }, 0)))
          out.push(`arrow crosses text: ${name(a)} / ${name(t)}`);
      }
    }
    for (let i = 0; i < arrows.length; i++) for (let j = i + 1; j < arrows.length; j++) {
      const A = samples(arrows[i]), B = samples(arrows[j]);
      if (A.some(p => B.some(q => Math.hypot(p.x - q.x, p.y - q.y) < 2.5))) out.push(`arrows touch: ${name(arrows[i])} / ${name(arrows[j])}`);
    }
    // 7b. divider rules vs text and boxes
    for (const l of all.filter(e => e.dataset.kind === 'rule')) {
      const lb = box(l), band = { ...lb, y: lb.y - 3, y2: lb.y2 + 3 };
      for (const t of [...texts, ...boxes]) if (inter(band, box(t))) out.push(`divider crosses: ${name(t)}`);
    }
    // 7. barrier lines vs text
    for (const l of barriers) { const lb = box(l); for (const t of texts) if (inter({ ...lb, x: lb.x - 1, x2: lb.x2 + 1 }, box(t))) out.push(`barrier crosses text: ${name(t)}`); }
    return { problems: out, counts: { boxes: boxes.length, texts: texts.length, arrows: arrows.length } };
  });

  const el = await page.$('svg');
  await el.screenshot({ path: pngPath, omitBackground: false });
  await browser.close();
  console.log(`checked ${problems.counts.boxes} boxes, ${problems.counts.texts} text blocks, ${problems.counts.arrows} arrows`);
  if (problems.problems.length) {
    console.log(`${problems.problems.length} layout problem(s):`);
    problems.problems.forEach(p => console.log('  - ' + p));
  } else {
    console.log('layout OK: no overlaps, every text fits its box');
  }
  console.log(`wrote ${path.relative(process.cwd(), pngPath)} at ${scale}x`);
  process.exit(problems.problems.length ? 1 : 0);
})();
