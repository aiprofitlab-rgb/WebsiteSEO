import { chromium } from 'playwright';

const out = process.argv[2] || 'clone.png';
const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 915, height: 807 },
  deviceScaleFactor: 2,
});
await page.goto('file:///Users/nahid/Desktop/Nahid/AI%20Profit%20Lab/Website/Website%20SEO/onmark-clone/index.html');
await page.waitForTimeout(2200);
await page.screenshot({ path: out, fullPage: true });
await browser.close();
console.log('saved', out);
