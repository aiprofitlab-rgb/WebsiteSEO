/**
 * The upsell interstitial, on both checkouts, in a real browser.
 *
 * This covers the one screen on the site that stands between a buyer and a
 * card page, so the assertions that matter most are not "does the offer show"
 * but "does the payment ALWAYS still happen": every exit from the dialog -
 * accept, decline, close, Escape - has to land on the payment the buyer asked
 * for. A modal that can swallow a click here is the worst bug the site could
 * have.
 *
 * It also pins the two things the copy promises:
 *   - taking the offer does not change what is charged today;
 *   - the offer price never appears on the public price list (asserted in
 *     tools/v4/pay.py's check_services, not here).
 *
 * Serves public_html over HTTP rather than opening file:// URLs, because
 * Chromium denies localStorage on a file origin and localStorage is what
 * carries an accepted storefront offer across the round trip to the gateway.
 *
 *   node test_upsell.js
 */
const { chromium } = require('playwright');
const path = require('path');

let fails = 0;
const ok = (c, m) => { console.log((c ? '  ok  ' : '  FAIL ') + m); if (!c) fails++; };

// ---------------------------------------------------------------- server ---
const http = require('http');
const fs = require('fs');
const PORT = 8767;
const ROOT = path.join(__dirname, 'public_html');
const TYPES = { '.html':'text/html', '.js':'text/javascript', '.css':'text/css',
                '.svg':'image/svg+xml', '.json':'application/json', '.ico':'image/x-icon' };

function serve() {
  return new Promise((res) => {
    const s = http.createServer((rq, rs) => {
      const f = path.join(ROOT, decodeURIComponent(rq.url.split('?')[0]));
      fs.readFile(f, (e, buf) => {
        if (e) { rs.writeHead(404); return rs.end('nope'); }
        rs.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' });
        rs.end(buf);
      });
    });
    s.listen(PORT, '127.0.0.1', () => res(s));
  });
}

// ------------------------------------------------------- checkout suite ---
const BASE = "http://127.0.0.1:8767/";


async function fill(page) {
  await page.fill('#f-name', 'Nahid');
  await page.fill('#f-biz', 'Gulf Lotus Trading LLC');
  await page.fill('#f-email', 'buyer@example.om');
  await page.fill('#f-wa', '+968 9924 5250');
  await page.check('#f-agree');
}

async function checkoutSuite(b) {

  for (const [lang, file, yesRe] of [
    ['en', 'en/checkout.html', /Add it/],
    ['ar', 'checkout-ar.html', /أضِفه/],
  ]) {
    const page = await b.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto(BASE + file);

    console.log(`\n[${lang}] ${file}`);

    // ---- 1. dialog is closed on load, item unchecked
    ok(!(await page.locator('#upDlg').evaluate(d => d.open)), 'dialog starts closed');
    ok(!(await page.isChecked('#upItem')), 'upsell item starts unchecked');
    const sumBefore = await page.textContent('#sumLines');
    ok(!/Visibility|الظهور/.test(sumBefore), 'summary has no upsell line before');

    // ---- 2. submit opens the interstitial
    await fill(page);
    await page.click('#payBtn');
    await page.waitForTimeout(300);
    ok(await page.locator('#upDlg').evaluate(d => d.open), 'submit opens the interstitial');
    ok(!(await page.locator('#offlinePanel').evaluate(p => p.classList.contains('on'))),
       'payment has NOT proceeded while the dialog is open');

    const yes = await page.textContent('#upYes');
    ok(yesRe.test(yes), `accept button reads correctly (${yes.trim()})`);

    // the 97 and 300 both present, guarantee months present
    const body = await page.textContent('#upDlg');
    ok(/97/.test(body) && /300/.test(body), 'shows both 97 and the 300 rack rate');
    ok(/6/.test(body), 'shows the 6-month guarantee');

    // ---- 3. decline -> proceeds without the item
    await page.click('#upNo');
    await page.waitForTimeout(400);
    ok(!(await page.locator('#upDlg').evaluate(d => d.open)), 'decline closes the dialog');
    ok(!(await page.isChecked('#upItem')), 'decline leaves the item unchecked');
    ok(await page.locator('#offlinePanel').evaluate(p => p.classList.contains('on')),
       'decline PROCEEDS to payment (offline panel shown)');

    // ---- 4. it does not ask twice
    await page.click('#payBtn');
    await page.waitForTimeout(300);
    ok(!(await page.locator('#upDlg').evaluate(d => d.open)), 'does not ask a second time');

    // ---- 5. accept path, fresh load
    const p2 = await b.newPage();
    p2.on('pageerror', e => errs.push(e.message));
    await p2.goto(BASE + file);
    await fill(p2);
    await p2.click('#payBtn');
    await p2.waitForTimeout(300);
    const dueBefore = await p2.textContent('#dueVal');
    await p2.click('#upYes');
    await p2.waitForTimeout(400);
    ok(await p2.isChecked('#upItem'), 'accept ticks the item');
    const sumAfter = await p2.textContent('#sumLines');
    ok(/Visibility|الظهور/.test(sumAfter), 'accept adds the line to the order summary');
    ok(/97/.test(sumAfter), 'summary shows OMR 97');
    const dueAfter = await p2.textContent('#dueVal');
    ok(dueBefore === dueAfter, `due today UNCHANGED by the upsell (${dueBefore} = ${dueAfter})`);
    ok(await p2.locator('#offlinePanel').evaluate(p => p.classList.contains('on')),
       'accept PROCEEDS to payment');
    const wa = await p2.getAttribute('#offlineWa', 'href');
    ok(/97/.test(decodeURIComponent(wa)), 'WhatsApp handover carries the upsell');

    // ---- 6. Growth Desk selected -> interstitial stands down
    const p3 = await b.newPage();
    p3.on('pageerror', e => errs.push(e.message));
    await p3.goto(BASE + file);
    await p3.locator('label.opt:has(input[value=desk])').click();
    ok(await p3.isChecked('input[name=item][value=desk]'), 'Growth Desk got ticked');
    await fill(p3);
    await p3.click('#payBtn');
    await p3.waitForTimeout(400);
    ok(!(await p3.locator('#upDlg').evaluate(d => d.open)),
       'stands down when the Growth Desk is already taken');
    ok(await p3.locator('#offlinePanel').evaluate(p => p.classList.contains('on')),
       'and goes straight to payment');

    // ---- 7. Escape proceeds too
    const p4 = await b.newPage();
    p4.on('pageerror', e => errs.push(e.message));
    await p4.goto(BASE + file);
    await fill(p4);
    await p4.click('#payBtn');
    await p4.waitForTimeout(300);
    await p4.keyboard.press('Escape');
    await p4.waitForTimeout(400);
    ok(await p4.locator('#offlinePanel').evaluate(p => p.classList.contains('on')),
       'Escape still lands on payment, never a dead end');

    // ---- 8. validation still gates the dialog
    const p5 = await b.newPage();
    p5.on('pageerror', e => errs.push(e.message));
    await p5.goto(BASE + file);
    await p5.click('#payBtn');
    await p5.waitForTimeout(300);
    ok(!(await p5.locator('#upDlg').evaluate(d => d.open)),
       'empty form does NOT reach the upsell');

    ok(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.join(' | ') : ''));
  }

}

// ----------------------------------------------------- storefront suite ---
// Served over HTTP, not file://: Chromium denies localStorage on a file
// origin, and localStorage is exactly what carries an accepted offer across
// the round trip through the gateway. file:// would test a different page.
const FILE = "http://127.0.0.1:8767/en/pay.html";


const CLAIM = {
  ok: true, ref: "APL-TEST-01", business: "Gulf Lotus Trading LLC",
  price: 290, deposit: 145, status: "Awaiting_Deposit", paid: false, pledgePct: 0, canPayByCard: true
};

async function mount(b, opts = {}) {
  const { status = "", claim = CLAIM } = opts;
  const page = await b.newPage();
  const seen = [];
  page.on('pageerror', e => seen.push('ERR:' + e.message));
  await page.route('**/claim/**', r => r.fulfill({ json: claim }));
  // Thawani sends the buyer back to this same page with ?status=... , so the
  // mock does too: same origin, and it exercises the return journey as well.
  await page.route('**/pay/session', r => {
    seen.push('SESSION');
    r.fulfill({ json: { ok: true,
      redirect_url: 'http://127.0.0.1:8767/en/pay.html?ref=APL-TEST-01&status=success' } });
  });
  await page.route('**/pay/upsell', r => { seen.push('UPSELL-POST'); r.fulfill({ json: { ok: true } }); });

  const q = 'ref=APL-TEST-01' + (status ? '&status=' + status : '');
  await page.goto(FILE + '?' + q);
  await page.waitForSelector('#card:not([hidden])');
  return { page, seen };
}

async function storefrontSuite(b) {
  console.log('\n[storefront] en/pay.html');

  // 1. dialog closed on load
  {
    const { page } = await mount(b);
    ok(!(await page.locator('#upDlg').evaluate(d => d.open)), 'dialog starts closed');
    ok(await page.locator('#upBooked').evaluate(e => e.hidden), 'booked block hidden on load');
  }

  // 2. pay -> interstitial, payment NOT started
  {
    const { page, seen } = await mount(b);
    await page.click('#payBtn');
    await page.waitForTimeout(400);
    ok(await page.locator('#upDlg').evaluate(d => d.open), 'pay opens the interstitial');
    ok(!seen.includes('SESSION'), 'card session NOT created while deciding');
    const t = await page.textContent('#upDlg');
    ok(/97/.test(t) && /300/.test(t) && /6/.test(t), 'shows 97, 300 and the 6-month guarantee');
    ok(/Visibility Desk/.test(t), 'names the offer');
  }

  // 3. decline -> proceeds to the gateway
  {
    const { page, seen } = await mount(b);
    await page.click('#payBtn');
    await page.waitForTimeout(300);
    await page.click('#upNo');
    await page.waitForTimeout(600);
    ok(seen.includes('SESSION'), 'decline PROCEEDS to the card page');
    ok(!seen.includes('UPSELL-POST'), 'decline records nothing');
  }

  // 4. accept -> records, proceeds, and the record survives the round trip
  {
    const { page, seen } = await mount(b);
    await page.click('#payBtn');
    await page.waitForTimeout(300);
    await page.click('#upYes');
    await page.waitForTimeout(700);
    ok(seen.includes('UPSELL-POST'), 'accept posts the booking (best effort)');
    ok(seen.includes('SESSION'), 'accept still PROCEEDS to the card page');
    await page.waitForURL(/status=success/, { timeout: 5000 }).catch(() => {});
    const stored = await page.evaluate(() => { try { return localStorage.getItem('apl.upsell.APL-TEST-01'); } catch(e){ return 'THREW'; } });
    ok(stored === '1', `accept is remembered across the gateway round trip (${stored})`);
  }

  // 5. coming back paid -> the booked block appears with a prefilled WhatsApp msg
  {
    const ctx = await b.newContext();
    const page = await ctx.newPage();
    await page.route('**/claim/**', r => r.fulfill({ json: { ...CLAIM, status: 'Confirmed', paid: true, paidAmount: 145 } }));
    await page.addInitScript(() => { try { localStorage.setItem('apl.upsell.APL-TEST-01', '1'); } catch(e){} });
    await page.goto(FILE + '?ref=APL-TEST-01&status=success');
    await page.waitForSelector('#card:not([hidden])');
    await page.waitForTimeout(400);
    ok(!(await page.locator('#upBooked').evaluate(e => e.hidden)), 'booked block shows after payment');
    const href = await page.getAttribute('#upBookedWa', 'href');
    const msg = decodeURIComponent(href || '');
    ok(/APL-TEST-01/.test(msg) && /97/.test(msg), 'WhatsApp message carries ref + price');
    // and it must not re-ask
    await page.click('#payBtn').catch(() => {});
    await page.waitForTimeout(300);
    ok(!(await page.locator('#upDlg').evaluate(d => d.open)), 'never re-asks a buyer who took it');
    await ctx.close();
  }

  // 6. escape proceeds
  {
    const { page, seen } = await mount(b);
    await page.click('#payBtn');
    await page.waitForTimeout(300);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    ok(seen.includes('SESSION'), 'Escape still reaches the card page');
    ok(!seen.some(s => s.startsWith('ERR:')), 'no page errors' +
       (seen.filter(s => s.startsWith('ERR:')).join(' | ')));
  }

}

// ---------------------------------------------------------------- runner ---
(async () => {
  const srv = await serve();
  const b = await chromium.launch();
  try {
    await checkoutSuite(b);
    await storefrontSuite(b);
  } finally {
    await b.close();
    srv.close();
  }
  console.log(fails ? `\n${fails} FAILED` : '\nall passed');
  process.exit(fails ? 1 : 0);
})();
