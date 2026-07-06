import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 915, height: 807 }, deviceScaleFactor: 2 });
await page.goto('file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/onmark-clone/index.html');
await page.waitForTimeout(1500);
const data = await page.evaluate(() => {
  const sel = {
    heroPanel: '.hero-panel', introSub: '.intro .subtitle', introCounter: '.big-counter',
    worksPanel: '.works', worksTitle: '.works .section-title', firstCard: '.project-card',
    services: '.services', servTitle: '.services .section-title', servGrid: '.services-grid',
    stats: '.stats-row', testi: '.testimonials', testiImg: '.testi-image',
    testiHead: '.testi-heading', arrows: '.testi-arrows', pricing: '.pricing',
    priceTitle: '.pricing .section-title', plan1: '.plan-card', body: 'body',
  };
  const out = {};
  for (const [k, s] of Object.entries(sel)) {
    const el = document.querySelector(s);
    if (el) { const r = el.getBoundingClientRect(); out[k] = { top: Math.round(r.top + scrollY), bottom: Math.round(r.bottom + scrollY), h: Math.round(r.height) }; }
  }
  out.pageH = document.body.scrollHeight;
  return out;
});
console.log(JSON.stringify(data, null, 1));
await browser.close();
