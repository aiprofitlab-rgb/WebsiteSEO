// Minimal DOM stub — enough to run apl-analytics.js and inspect APLPage.
const fs = require('fs');
const vm = require('vm');
const SRC = fs.readFileSync('public_html/js/apl-analytics.js', 'utf8');

function makeStorage() {
  const m = new Map();
  return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k), _m: m };
}

function run({ path = '/en/smart-storefront/', search = '', referrer = '', local, session, source }) {
  const src = source || SRC;
  const ls = local || makeStorage();
  const ss = session || makeStorage();
  const events = [];
  const sets = [];
  const created = [];
  const sandbox = {
    console,
    URL, URLSearchParams, Date, Math, JSON, setTimeout, clearTimeout, isNaN, String, parseInt,
    location: { pathname: path, search, hostname: 'aiprofitlab.io', href: 'https://aiprofitlab.io' + path + search },
    navigator: { sendBeacon: () => true },
  };
  sandbox.window = sandbox;
  sandbox.window.localStorage = ls;
  sandbox.window.sessionStorage = ss;
  sandbox.window.addEventListener = () => {};
  sandbox.window.requestAnimationFrame = () => {};
  sandbox.window.scrollY = 0;
  sandbox.window.innerHeight = 800;
  sandbox.gtag = function (a, b, c) {
    if (a === 'event') events.push([b, c]);
    if (a === 'set') sets.push([b, c]);
  };
  sandbox.window.gtag = sandbox.gtag;
  sandbox.document = {
    documentElement: { getAttribute: () => 'en', scrollHeight: 3000, scrollTop: 0 },
    referrer,
    visibilityState: 'visible',
    addEventListener: () => {},
    querySelectorAll: (sel) => (sel.includes('gtag/js')
      ? [{ getAttribute: () => 'https://www.googletagmanager.com/gtag/js?id=G-SLR9GD3MJP' }] : []),
    createElement: (t) => { const el = { tagName: t, set src(v) { created.push(v); }, get src() { return ''; } }; return el; },
    getElementsByTagName: () => [{ parentNode: { insertBefore: () => {} } }],
  };
  sandbox.window.dataLayer = [];
  vm.createContext(sandbox);
  vm.runInContext(src, sandbox);
  return { api: sandbox.window.APLPage, ls, ss, events, sets, created, win: sandbox.window };
}

let pass = 0, fail = 0;
function check(name, cond, extra) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; console.log('  FAIL ' + name, extra !== undefined ? JSON.stringify(extra) : ''); }
}

console.log('\n1. Flyer QR scan — the exact printed URL');
{
  const { api, sets } = run({ search: '?utm_source=flyer' });
  const f = api.attributionFields();
  check('firstSource = flyer', f.firstSource === 'flyer', f);
  check('medium falls back to (none), not blank', f.firstMedium === '(none)', f);
  check('landing page recorded', f.firstLandingPage === '/en/smart-storefront/', f);
  check('user_properties set', sets.some(s => s[0] === 'user_properties' && s[1].first_source === 'flyer'), sets);
  check('touches = 1', f.touches === '1', f);
}

console.log('\n2. Flyer first, Google organic later — first touch must survive');
{
  const local = makeStorage();
  run({ search: '?utm_source=flyer', local, session: makeStorage() });
  const { api } = run({ search: '', referrer: 'https://www.google.com/search?q=x', local, session: makeStorage() });
  const f = api.attributionFields();
  check('first stays flyer', f.firstSource === 'flyer', f);
  check('last becomes google', f.lastSource === 'google', f);
  check('google classified organic', f.lastMedium === 'organic', f);
  check('touches = 2', f.touches === '2', f);
}

console.log('\n3. Direct return visit must NOT wipe the flyer (last non-direct)');
{
  const local = makeStorage();
  run({ search: '?utm_source=flyer', local, session: makeStorage() });
  const { api } = run({ search: '', referrer: '', local, session: makeStorage() });
  const f = api.attributionFields();
  check('first still flyer', f.firstSource === 'flyer', f);
  check('last still flyer (not direct)', f.lastSource === 'flyer', f);
  check('touches NOT incremented', f.touches === '1', f);
}

console.log('\n4. Internal navigation is not a new touch');
{
  const local = makeStorage(); const session = makeStorage();
  run({ search: '?utm_source=flyer', local, session });
  const { api } = run({ path: '/en/pay/', referrer: 'https://aiprofitlab.io/en/smart-storefront/', local, session });
  const f = api.attributionFields();
  check('touches still 1', f.touches === '1', f);
  check('first landing page unchanged', f.firstLandingPage === '/en/smart-storefront/', f);
}

console.log('\n5. Meta ad click with UTMs stripped — fbclid alone must still attribute');
{
  const { api } = run({ search: '?fbclid=IwAR123abc' });
  const f = api.attributionFields();
  check('source = facebook', f.firstSource === 'facebook', f);
  check('medium = paid_social', f.firstMedium === 'paid_social', f);
  check('click id captured', f.clickId === 'IwAR123abc', f);
  check('click id type recorded', f.clickIdType === 'fbclid', f);
}

console.log('\n6. LinkedIn + WhatsApp outreach links');
{
  const a = run({ search: '?utm_source=linkedin&utm_medium=outreach&utm_campaign=storefront_launch&utm_content=dm_batch1' }).api.attributionFields();
  check('linkedin source', a.firstSource === 'linkedin', a);
  check('outreach medium', a.firstMedium === 'outreach', a);
  check('campaign kept', a.firstCampaign === 'storefront_launch', a);
  const b = run({ referrer: 'https://api.whatsapp.com/' }).api.attributionFields();
  check('whatsapp referrer named', b.firstSource === 'whatsapp', b);
}

console.log('\n7. Unattributed visitor returns empty strings, never "null"');
{
  const { api } = run({ search: '', referrer: '' });
  const f = api.attributionFields();
  check('attribution is null', api.attribution === null);
  check('every field is a string', Object.values(f).every(v => typeof v === 'string'), f);
  check('no "null" or "undefined" text', !JSON.stringify(f).match(/null|undefined/), f);
}

console.log('\n8. Storage blocked (private mode) must not throw');
{
  const boom = { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('denied'); } };
  let threw = null;
  try { run({ search: '?utm_source=flyer', local: boom, session: boom }); } catch (e) { threw = e.message; }
  check('page still loads', threw === null, threw);
}

console.log('\n9. Meta Pixel is completely dark with no id');
{
  const { created, win } = run({ search: '?utm_source=flyer' });
  check('no facebook script requested', !created.some(u => /facebook|fbevents/.test(u)), created);
  check('fbq never defined', typeof win.fbq === 'undefined');
}

console.log('\n10. Meta Pixel maps gtag events when an id is set');
{
  const withId = SRC.replace("var META_PIXEL_ID = '';", "var META_PIXEL_ID = '1234567890123456';");
  const { created, win } = run({ search: '?utm_source=flyer', source: withId });
  check('fbevents.js requested', created.some(u => /fbevents\.js/.test(u)), created);
  const calls = [];
  win.fbq = function () { calls.push([].slice.call(arguments)); };
  // a page firing its own gtag conversion, exactly as the storefront does
  win.dataLayer.push(['event', 'claim_submitted', { pledges: 2 }]);
  win.dataLayer.push(['event', 'seat_paid', { value: 124.5, currency: 'OMR' }]);
  win.dataLayer.push(['event', 'scroll_depth', { percent_scrolled: 50 }]);
  check('claim_submitted -> Lead', calls.some(c => c[1] === 'Lead'), calls);
  check('seat_paid -> Purchase with OMR', calls.some(c => c[1] === 'Purchase' && c[2].value === 124.5 && c[2].currency === 'OMR'), calls);
  check('scroll_depth NOT forwarded', !calls.some(c => c[1] === 'scroll_depth'), calls);
}

console.log('\n11. gaIds resolves even when gtag never calls back');
{
  const { api } = run({ search: '?utm_source=flyer' });
  let got = null;
  api.gaIds(r => { got = r; }, 50);
  setTimeout(() => {
    check('resolved with empty ids rather than hanging', got && got.client_id === '', got);
    console.log(`\n${pass} passed, ${fail} failed`);
    process.exit(fail ? 1 : 0);
  }, 120);
}
