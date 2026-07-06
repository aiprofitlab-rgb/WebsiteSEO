import { chromium } from 'playwright';
const html = `<!doctype html><html><body style="margin:0;background:#333;font-family:sans-serif">
<div style="display:flex;gap:4px;align-items:flex-start">
<div style="flex:none;width:915px"><div style="color:#fff;padding:8px;font-size:20px;background:#111">ORIGINAL</div><img src="onmark.webflow.io_.png" style="width:915px;display:block"></div>
<div style="flex:none;width:915px"><div style="color:#fff;padding:8px;font-size:20px;background:#111">CLONE</div><img src="clone.png" style="width:915px;display:block"></div>
</div></body></html>`;
import { writeFileSync } from 'fs';
writeFileSync('compare.html', html);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1840, height: 1000 }, deviceScaleFactor: 1 });
await page.goto('file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/onmark-clone/compare.html');
await page.waitForTimeout(2000);
await page.screenshot({ path: 'comparison.png', fullPage: true });
await browser.close();
console.log('comparison saved');
