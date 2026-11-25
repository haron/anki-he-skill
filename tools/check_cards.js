// Usage: node check_cards.js cards.json OUTDIR SHOTS(0|1) — see check_cards.py
const { chromium } = require('playwright');
const [,, file, out, shots] = process.argv;
const cards = require(file);
const page = (c, cls, zoom) => `<!doctype html><html><head><meta name=viewport content="width=device-width">
  <style>${c.css}</style><style>html{zoom:${zoom}} body{margin:0;padding:8px}</style></head>
  <body class="${cls} card${c.ord + 1}"><div id=qa>${c.html.replace(/\[sound:[^\]]*\]/g, '')}</div></body></html>`;
(async () => {
  const b = await chromium.launch();
  let bad = 0, n = 0;
  for (const [vn, w, h, zoom] of [['phone', 360, 640, 1], ['ereader', 600, 800, 1.6], ['desktop', 1000, 700, 1]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    for (const c of cards) {
      await p.setContent(page(c, 'card', zoom)); await p.waitForTimeout(400);
      const r = await p.evaluate(() => { const de = document.documentElement;
        return { sh: de.scrollHeight, ih: innerHeight, sw: de.scrollWidth, cw: de.clientWidth }; });
      n++;
      if (r.sh > r.ih + 1 || r.sw > r.cw + 1) { bad++; console.log('OVERFLOW', vn, c.name, JSON.stringify(r)); }
      if (shots === '1') await p.screenshot({ path: `${out}/${vn}-${c.name}.png` });
    }
    await p.close();
  }
  const p = await b.newPage({ viewport: { width: 600, height: 800 } });
  for (const c of cards) {
    await p.setContent(page(c, 'card android', 1)); await p.waitForTimeout(200);
    const cols = await p.evaluate(() => [...new Set([...document.querySelectorAll('.fit *')].map(e => getComputedStyle(e).color))]);
    if (cols.some(x => x !== 'rgb(0, 0, 0)')) { bad++; console.log('NOT BLACK on AnkiDroid', c.name, cols.join(' ')); }
  }
  console.log(`checked ${n} renders + ${cards.length} AnkiDroid colour passes, problems: ${bad}`);
  await b.close(); process.exit(bad ? 1 : 0);
})();
