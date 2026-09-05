const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  const hits = [];
  await page.route('**/*', route => {
    const u = route.request().url();
    if (/google-analytics|googletagmanager|clarity\.ms|connect\.facebook|offer\.aiprofitlab/.test(u)) {
      hits.push(u);
      return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    }
    route.continue();
  });

  let pass = 0, fail = 0;
  const check = (n, c, x) => c ? (pass++, console.log('  ok   ' + n))
                               : (fail++, console.log('  FAIL ' + n, JSON.stringify(x)));

  // ---- the exact printed flyer URL ----
  console.log('\nReal browser: the printed flyer QR URL');
  await page.goto('http://localhost:8777/en/smart-storefront.html?utm_source=flyer', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);

  const url = page.url();
  check('normaliser added utm_medium=print', url.includes('utm_medium=print'), url);
  check('normaliser added the campaign', url.includes('utm_campaign=smart_storefront_launch'), url);
  check('original utm_source preserved', url.includes('utm_source=flyer'), url);

  const attr = await page.evaluate(() => window.APLPage && window.APLPage.attributionFields());
  check('APLPage exposes attribution', !!attr, attr);
  check('firstSource = flyer', attr && attr.firstSource === 'flyer', attr);
  check('firstMedium = print (the fix)', attr && attr.firstMedium === 'print', attr);
  check('touches counted', attr && attr.touches === '1', attr);
  check('all values are strings', attr && Object.values(attr).every(v => typeof v === 'string'), attr);

  // ---- first touch survives a later organic visit, in the same profile ----
  console.log('\nReal browser: flyer first, then a return visit days later');
  await page.goto('http://localhost:8777/en/smart-storefront.html', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(400);
  const after = await page.evaluate(() => window.APLPage.attributionFields());
  check('first touch still flyer', after.firstSource === 'flyer', after);
  check('last touch not overwritten by a direct visit', after.lastSource === 'flyer', after);

  // ---- the claim form reads it ----
  console.log('\nReal browser: the claim payload picks it up');
  const payload = await page.evaluate(async () => {
    const a = window.APLPage.attributionFields();
    const ids = await new Promise(r => window.APLPage.gaIds(r, 800));
    return { a, ids };
  });
  check('attribution available to the form', payload.a.firstSource === 'flyer', payload.a);
  check('gaIds resolved without hanging', payload.ids && typeof payload.ids.client_id === 'string', payload.ids);

  // ---- pixel really is dark ----
  console.log('\nReal browser: no Meta pixel with no id');
  check('nothing requested from facebook', !hits.some(u => /facebook/.test(u)), hits.filter(u => /facebook/.test(u)));

  // ---- Arabic page ----
  console.log('\nReal browser: the Arabic storefront');
  await ctx.clearCookies();
  const p2 = await ctx.newPage();
  await p2.route('**/*', r => /offer\.aiprofitlab|clarity|googletag/.test(r.request().url())
    ? r.fulfill({ status: 200, contentType: 'application/json', body: '{}' }) : r.continue());
  await p2.goto('http://localhost:8777/smart-storefront-ar.html?utm_source=flyer', { waitUntil: 'domcontentloaded' });
  await p2.waitForTimeout(600);
  check('AR normaliser ran', p2.url().includes('utm_medium=print'), p2.url());
  const arAttr = await p2.evaluate(() => window.APLPage && window.APLPage.attributionFields());
  check('AR page reports language ar', await p2.evaluate(() => window.APLPage.language) === 'ar');
  check('AR attribution captured', arAttr && arAttr.firstSource === 'flyer', arAttr);

  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
