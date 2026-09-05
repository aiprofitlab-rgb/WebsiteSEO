/**
 * "How did you hear about us?" on the checkout, in both languages.
 *
 * Needs a server:  python3 -m http.server 8777 --directory public_html
 *
 * Three things are worth holding down here, and none of them are visible from
 * the Python that generates the page:
 *
 *   1. The question is a GATE. Every other field is valid when the first press
 *      happens, so nothing but the missing answer can be what stops it.
 *   2. The follow-up box is EMPTIED when it closes. A name typed under "someone
 *      recommended you" that survived a change of mind would be filed against
 *      "Google search" — a wrong answer, which is worse than no answer.
 *   3. On the offline route the WhatsApp message is the ONLY copy of the answer
 *      that ever reaches Nahid, because nothing has been posted to the server.
 *      It has to carry the label the buyer read, not the id the server wants.
 *
 * Sibling: test_claim_attribution.js does the same for the storefront claim.
 */
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const check = (n, c, x) => c ? (pass++, console.log('  ok   ' + n))
                               : (fail++, console.log('  FAIL ' + n, JSON.stringify(x)));

  for (const [lang, url, want] of [
    ['EN', 'http://localhost:8777/en/checkout.html', 'Heard about us: '],
    ['AR', 'http://localhost:8777/checkout-ar.html', 'سمعت عنّا عبر: '],
  ]) {
    console.log(`\n${lang} checkout`);
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await page.route('**/*', r =>
      /clarity\.ms|googletagmanager|google-analytics|connect\.facebook/.test(r.request().url())
        ? r.fulfill({ status: 200, contentType: 'application/javascript', body: '' })
        : r.continue());
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);

    check('the select rendered', await page.isVisible('#f-heard'), 'missing');
    check('the follow-up starts hidden', !(await page.isVisible('#f-heard-detail')), 'visible');

    await page.fill('#f-name', 'Khalid Al Balushi');
    await page.fill('#f-biz', 'Gulf Lotus Trading LLC');
    await page.fill('#f-email', 'khalid@gulflotus.om');
    await page.fill('#f-wa', '+968 9123 4567');
    await page.check('#f-agree');

    // Everything else is valid, so only the unanswered question can stop it.
    await page.click('#payBtn');
    await page.waitForTimeout(400);
    check('an unanswered question blocks the order',
      !(await page.isVisible('#offlinePanel.on')), 'the order went through');
    check('and the select is the field flagged',
      await page.getAttribute('#f-heard', 'aria-invalid') === 'true',
      await page.getAttribute('#f-heard', 'aria-invalid'));

    await page.selectOption('#f-heard', 'referral');
    check('the follow-up opens for a recommendation', await page.isVisible('#f-heard-detail'), 'hidden');
    await page.fill('#f-heard-detail', 'Ahmed at Gulf Lotus');
    await page.selectOption('#f-heard', 'flyer');
    check('and closes, emptied, for one that needs none',
      !(await page.isVisible('#f-heard-detail')) && (await page.inputValue('#f-heard-detail')) === '',
      await page.inputValue('#f-heard-detail'));

    await page.selectOption('#f-heard', 'referral');
    await page.fill('#f-heard-detail', 'Ahmed at Gulf Lotus');
    await page.click('#payBtn');
    await page.waitForTimeout(500);
    // The upsell interstitial stands between "pay" and the handover. Pre-existing
    // and nothing to do with this field — decline it and carry on.
    if (await page.isVisible('#upNo')) { await page.click('#upNo'); await page.waitForTimeout(700); }

    check('the order now goes through', await page.isVisible('#offlinePanel.on'), 'still blocked');
    const wa = decodeURIComponent((await page.getAttribute('#offlineWa', 'href')) || '');
    check('the WhatsApp handover carries the answer', wa.includes(want), wa.slice(-320));
    check('...as the label the buyer read, not the id',
      !/heardAbout|"referral"/.test(wa) && /recommended|رشّح/.test(wa), wa.slice(-320));
    check('...with the name they typed', wa.includes('Ahmed at Gulf Lotus'), wa.slice(-320));

    // The payload the gateway would have received, read off the page's own code.
    const sent = await page.evaluate(() => {
      const f = document.getElementById('coForm');
      const g = n => (f.elements[n].value || '').trim();
      return { heardAbout: g('heard'), heardDetail: g('heardDetail') };
    });
    check('the form holds the id, never the label', sent.heardAbout === 'referral', sent);
    await ctx.close();
  }

  console.log(`\n${pass} passed, ${fail} failed`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
