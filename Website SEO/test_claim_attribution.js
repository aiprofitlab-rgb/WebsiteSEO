const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  let claimBody = null;

  await page.route('**/*', async route => {
    const req = route.request();
    const u = req.url();
    if (/offer\.aiprofitlab\.io\/claim$/.test(u) && req.method() === 'POST') {
      claimBody = JSON.parse(req.postData() || '{}');
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ok: true, ref: 'SS-TEST99', breakdown: {} }) });
    }
    if (/offer\.aiprofitlab\.io\/status/.test(u)) {
      // The exact shape the live service returns, captured from
      // GET https://offer.aiprofitlab.io/status on 2026-09-05.
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ok:true, soldOut:false, confirmed:0,
          activeTier:{price:249,seatsLeft:3,deposit:124.5},
          published:[{price:249,seats:3,seatsLeft:3,state:'live'},
                     {price:279,seats:7,seatsLeft:7,state:'next'},
                     {price:299,seats:10,seatsLeft:10,state:'next'}],
          moreRungsAfter:true,
          pledges:[{id:'testimonial',pct:15,label:'A video testimonial',detail:'x'},
                   {id:'referral',pct:20,label:'An introduction',detail:'y'}],
          pay:{card:false}, asOf:new Date().toISOString() }) });
    }
    if (/clarity\.ms|googletagmanager|google-analytics|connect\.facebook/.test(u)) {
      return route.fulfill({ status: 200, contentType: 'application/javascript', body: '' });
    }
    return route.continue();
  });

  // arrive exactly as a flyer scanner does
  await page.goto('http://localhost:8777/en/smart-storefront.html?utm_source=flyer',
                  { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800);

  let pass = 0, fail = 0;
  const check = (n, c, x) => c ? (pass++, console.log('  ok   ' + n))
                               : (fail++, console.log('  FAIL ' + n, JSON.stringify(x)));

  console.log('\nSubmitting the real claim form after a flyer scan');

  await page.fill('#f-name', 'Test Person');
  await page.fill('#f-business', 'Test Trading LLC');
  await page.fill('#f-sector', 'Auto parts');
  await page.fill('#f-whatsapp', '+968 9123 4567');
  await page.fill('#f-email', 'test@example.om');
  await page.check('#f-consent');

  // The gate first: everything else is filled in, so the ONLY thing that can
  // hold this submission back is the unanswered "how did you hear about us?".
  await page.evaluate(() => document.querySelector('form').requestSubmit());
  await page.waitForTimeout(600);
  check('an unanswered "how did you hear about us?" blocks the claim', !claimBody, claimBody);

  // "Someone recommended you" — the answer that opens the follow-up box, so
  // this also covers the reveal and the free text riding along with the id.
  await page.selectOption('#f-heard', 'referral');
  check('the follow-up box appears for a recommendation',
    await page.isVisible('#f-heard-detail'), 'hidden');
  await page.fill('#f-heard-detail', 'Ahmed at Gulf Lotus');

  // ...and closes again, taking its contents with it, if they change their mind.
  await page.selectOption('#f-heard', 'google');
  check('the follow-up box hides again for an answer that needs none',
    !(await page.isVisible('#f-heard-detail')), 'still visible');
  check('and it does not keep the answer to a question no longer being asked',
    await page.inputValue('#f-heard-detail') === '', await page.inputValue('#f-heard-detail'));

  await page.selectOption('#f-heard', 'referral');
  await page.fill('#f-heard-detail', 'Ahmed at Gulf Lotus');
  await page.evaluate(() => document.querySelector('form').requestSubmit());

  await page.waitForTimeout(2000);

  check('the claim was actually sent', !!claimBody, claimBody);
  if (claimBody) {
    check('name still posts (nothing broken)', claimBody.name === 'Test Person', claimBody.name);
    check('consent still posts', claimBody.consent === true, claimBody.consent);
    check('phone posts untouched', claimBody.whatsapp === '+968 9123 4567', claimBody.whatsapp);
    check('firstSource = flyer', claimBody.firstSource === 'flyer', claimBody.firstSource);
    check('firstMedium = print', claimBody.firstMedium === 'print', claimBody.firstMedium);
    check('firstCampaign carried', claimBody.firstCampaign === 'smart_storefront_launch', claimBody.firstCampaign);
    check('landing page recorded', !!claimBody.firstLandingPage, claimBody.firstLandingPage);
    check('touches sent', claimBody.touches === '1', claimBody.touches);
    check('daysToClaim sent', claimBody.daysToClaim === '0', claimBody.daysToClaim);
    check('gaClientId key present', 'gaClientId' in claimBody, Object.keys(claimBody));
    check('no undefined leaked as text',
      !JSON.stringify(claimBody).includes('"undefined"'), claimBody);
    // The id, not the label — the service maps it back, so an Arabic claim and
    // an English one land in one bucket.
    check('heardAbout posts the id', claimBody.heardAbout === 'referral', claimBody.heardAbout);
    check('heardDetail posts the free text',
      claimBody.heardDetail === 'Ahmed at Gulf Lotus', claimBody.heardDetail);
  }
  // ---- the Arabic funnel, which is a SEPARATE build and free to drift ----
  console.log('\nSubmitting the Arabic claim form');
  claimBody = null;
  // A FRESH context: same-origin localStorage is shared, so re-using ctx would hand the
  // Arabic page the flyer first-touch set by the English visit above. That is the
  // correct product behaviour and the wrong test — this asserts a new visitor.
  const arCtx = await browser.newContext();
  const ar = await arCtx.newPage();
  await ar.route('**/*', async route => {
    const req = route.request(); const u = req.url();
    if (/offer\.aiprofitlab\.io\/claim$/.test(u) && req.method() === 'POST') {
      claimBody = JSON.parse(req.postData() || '{}');
      return route.fulfill({ status:200, contentType:'application/json',
        body: JSON.stringify({ ok:true, ref:'SS-ARTEST', breakdown:{} }) });
    }
    if (/offer\.aiprofitlab\.io\/status/.test(u)) {
      return route.fulfill({ status:200, contentType:'application/json',
        body: JSON.stringify({ ok:true, soldOut:false, confirmed:0,
          activeTier:{price:249,seatsLeft:3,deposit:124.5},
          published:[{price:249,seats:3,seatsLeft:3,state:'live'}],
          moreRungsAfter:true, pledges:[], pay:{card:false},
          asOf:new Date().toISOString() }) });
    }
    if (/clarity\.ms|googletagmanager|google-analytics|connect\.facebook/.test(u)) {
      return route.fulfill({ status:200, contentType:'application/javascript', body:'' });
    }
    return route.continue();
  });
  await ar.goto('http://localhost:8777/smart-storefront-ar.html?utm_source=whatsapp&utm_medium=outreach&utm_campaign=smart_storefront_launch',
                { waitUntil:'domcontentloaded' });
  await ar.waitForTimeout(900);
  await ar.fill('#f-name', 'ناهد');
  await ar.fill('#f-business', 'شركة تجريبية');
  await ar.fill('#f-sector', 'قطع غيار');
  await ar.fill('#f-whatsapp', '+968 9123 4567');
  await ar.fill('#f-email', 'ar@example.om');
  await ar.check('#f-consent');
  await ar.selectOption('#f-heard', 'flyer');
  await ar.evaluate(() => document.querySelector('form').requestSubmit());
  await ar.waitForTimeout(2000);

  check('the Arabic claim was sent', !!claimBody, claimBody);
  if (claimBody) {
    check('Arabic name posts intact', claimBody.name === 'ناهد', claimBody.name);
    check('whatsapp outreach attributed', claimBody.firstSource === 'whatsapp', claimBody.firstSource);
    check('medium carried from the link', claimBody.firstMedium === 'outreach', claimBody.firstMedium);
    check('normaliser left an explicit medium alone', claimBody.firstMedium !== 'print', claimBody.firstMedium);
    check('gaClientId key present on AR too', 'gaClientId' in claimBody, Object.keys(claimBody));
    // The point of an id: the Arabic page shows "منشور مطبوع" and posts the
    // same string the English page does, so the flyer is ONE row in the count.
    check('the Arabic page posts the same channel id, not its label',
      claimBody.heardAbout === 'flyer', claimBody.heardAbout);
  }

  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
