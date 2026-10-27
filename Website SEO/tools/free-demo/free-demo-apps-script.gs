/**
 * Free website demo - request intake.
 *
 * Backs https://aiprofitlab.io/en/free-demo/ (the Google Ads landing page since
 * 2026-10-25): one row per request in the "Requests" tab of the "Free demo
 * requests" sheet, the visitor's logo (if they sent one) in a Drive folder, an
 * email to Nahid with everything needed to start the demo, and - when the
 * visitor chose email - a short confirmation to them.
 *
 * This is a Google Apps Script bound to that spreadsheet. It is pushed with
 * clasp from a scratch folder (see docs/free-demo.md); this file is the copy of
 * record. If you change one, change the other.
 *
 * ── SETUP, ONCE ────────────────────────────────────────────────────────────────
 *  1. Open the sheet > Extensions > Apps Script.
 *  2. Pick `setup` in the function menu and press Run. Google asks for
 *     permission (sheet, Drive, mail); allow it. Until this is done, every
 *     request fails with an authorisation error and the page shows the visitor
 *     the email/WhatsApp fallback instead of "Received".
 *  3. The web app deployment must be "Execute as: Me" and "Who has access:
 *     Anyone" (not "Anyone with a Google account": visitors are not signed in).
 *  4. Open the /exec URL in a browser. It should answer {"ok":true,...}.
 *
 * ── REDEPLOYING ────────────────────────────────────────────────────────────────
 *  After an edit: clasp push, clasp version, then
 *  clasp deploy -i <deployment id> -V <version>, which keeps the same /exec URL.
 *  A NEW deployment gets a NEW URL and the page keeps posting to the old one.
 */

/* ── settings ─────────────────────────────────────────────────────────────── */

/** Empty = the account that owns this script. Comma-separate for several. */
var NOTIFY_EMAIL = '';

/** Send the visitor a confirmation when they asked for the demo by email. */
var CONFIRM_BY_EMAIL = true;

var TAB = 'Requests';
var FOLDER = 'Free demo logos';
var TZ = 'Asia/Muscat';
var PROMISE_HOURS = 24;

var COLS = ['Timestamp', 'Due by', 'Status', 'Business', 'Brand link', 'Sells', 'Send via',
            'WhatsApp', 'Email', 'Name', 'Instagram OK', 'Style picked', 'Logo',
            'First source', 'First medium', 'First campaign', 'Last source', 'Last medium',
            'Last campaign', 'Click ID', 'Click ID type', 'Touches', 'GA client ID',
            'GA session ID', 'Page', 'Referrer', 'User agent', 'Timeline'];
// New columns go on the END only: ensureSheet() extends an existing header
// row in place, which is safe only while earlier columns keep their places.

var CELL_MAX = 49000;
var LOGO_MAX_BYTES = 5 * 1024 * 1024;

/* ── web app ──────────────────────────────────────────────────────────────── */

function doGet() {
  return json({ ok: true, service: 'free-demo-intake' });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return json({ ok: false, error: 'empty_body' });
    var b = JSON.parse(e.postData.contents);
    if (b.kind !== 'free_demo') return json({ ok: false, error: 'wrong_kind' });

    var business = clip(b.business, 80);
    var whatsapp = clip(b.whatsapp, 24);
    var email = clip(b.email, 120);
    if (!business) return json({ ok: false, error: 'no_business' });
    if (!whatsapp && !email) return json({ ok: false, error: 'no_contact' });

    // The logo first: a row that promises a file we failed to save is worse
    // than a slower send.
    var logo = saveLogo(b.logo, business);

    var now = new Date();
    var due = new Date(now.getTime() + PROMISE_HOURS * 3600 * 1000);
    var a = b.attribution || {};
    var values = {
      'Timestamp': fmt(now),
      'Due by': fmt(due),
      'Status': 'New',
      'Business': business,
      'Brand link': clip(b.brandLink, 200),
      'Sells': clip(b.sells, 160),
      'Send via': b.via === 'email' ? 'Email' : 'WhatsApp',
      'WhatsApp': whatsapp,
      'Email': email,
      'Name': clip(b.name, 60),
      'Instagram OK': b.instagramOk ? 'Yes, anonymised' : 'No',
      'Style picked': clip(b.trade, 20) + (b.palette ? ' ' + clip(b.palette, 10) : ''),
      'Logo': logo || '',
      'First source': clip(a.firstSource, 80), 'First medium': clip(a.firstMedium, 80),
      'First campaign': clip(a.firstCampaign, 120), 'Last source': clip(a.lastSource, 80),
      'Last medium': clip(a.lastMedium, 80), 'Last campaign': clip(a.lastCampaign, 120),
      'Click ID': clip(a.clickId, 200), 'Click ID type': clip(a.clickIdType, 20),
      'Touches': clip(a.touches, 10),
      'GA client ID': clip(b.gaClientId, 60), 'GA session ID': clip(b.gaSessionId, 60),
      'Page': clip(b.page, 200), 'Referrer': clip(b.referrer, 300), 'User agent': clip(b.ua, 300),
      // "This month" / "1-3 months" / "Just looking": the page's one qualifier
      'Timeline': clip(b.timeline, 20)
    };

    var lock = LockService.getScriptLock();
    lock.waitLock(20000);
    var row;
    try {
      var sheet = ensureSheet();
      row = sheet.getLastRow() + 1;
      var line = COLS.map(function (c) { return String(values[c] == null ? '' : values[c]).slice(0, CELL_MAX); });
      /* Plain text BEFORE setValues, never after. setValues parses like a
         person typing, so "+968..." becomes #ERROR! and a GA client id loses
         digits; reformatting afterwards does not bring them back. */
      var range = sheet.getRange(row, 1, 1, line.length);
      range.setNumberFormat('@');
      range.setValues([line]);
    } finally {
      lock.releaseLock();
    }

    // Saved is what matters. A mail failure after this must not turn a saved
    // request into an error the visitor sees.
    try { notify(values, row); } catch (mailErr) { console.error('SAVED BUT OWNER EMAIL FAILED: ' + mailErr); }
    if (CONFIRM_BY_EMAIL && values['Send via'] === 'Email' && /@/.test(email)) {
      try { confirmToVisitor(values); } catch (cErr) { console.error('CONFIRMATION FAILED: ' + cErr); }
    }
    return json({ ok: true, row: row });
  } catch (err) {
    console.error('FREE DEMO POST FAILED: ' + (err && err.stack ? err.stack : err));
    return json({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function clip(v, n) { return String(v == null ? '' : v).trim().slice(0, n); }
function fmt(d) { return Utilities.formatDate(d, TZ, 'yyyy-MM-dd HH:mm'); }

/* ── sheet ────────────────────────────────────────────────────────────────── */

function ensureSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB);
  if (!sheet) {
    sheet = ss.insertSheet(TAB, 0);
    sheet.getRange(1, 1, 1, COLS.length).setValues([COLS]).setFontWeight('bold');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(4, 200);
    // the default "Sheet1" a new spreadsheet starts with is just noise
    var stray = ss.getSheetByName('Sheet1');
    if (stray && ss.getSheets().length > 1 && stray.getLastRow() === 0) ss.deleteSheet(stray);
  } else if (sheet.getLastColumn() < COLS.length) {
    // a tab made before a column was added: give the new column its header
    sheet.getRange(1, 1, 1, COLS.length).setValues([COLS]).setFontWeight('bold');
  }
  return sheet;
}

/* ── drive ────────────────────────────────────────────────────────────────── */

function saveLogo(f, business) {
  if (!f || !f.data) return '';
  var bytes = Utilities.base64Decode(f.data);
  if (bytes.length > LOGO_MAX_BYTES) return 'Logo refused: over 5 MB';
  var type = String(f.type || '');
  if (!/^image\/|^application\/pdf$/.test(type)) return 'Logo refused: ' + type;
  var it = DriveApp.getFoldersByName(FOLDER);
  var folder = it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER);
  var safe = business.replace(/[^\w \-&؀-ۿ]/g, '').slice(0, 50).trim() || 'logo';
  var name = Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd HHmm') + ' - ' + safe + ' - ' + clip(f.name, 80);
  return folder.createFile(Utilities.newBlob(bytes, type, name)).getUrl();
}

/* ── email ────────────────────────────────────────────────────────────────── */

function notify(v, row) {
  var to = NOTIFY_EMAIL || Session.getEffectiveUser().getEmail();
  var digits = String(v['WhatsApp']).replace(/\D/g, '');
  var lines = [
    v['Business'] + ' asked for a free website demo.',
    '',
    'DUE BY:      ' + v['Due by'] + ' (Muscat), the page promised under 24 hours',
    'WANTS IT:    ' + (v['Timeline'] || '-'),
    '',
    // since 2026-10-25 the page asks one field for the link OR what they sell,
    // and no longer asks their name; the Sells and Name columns stay for old rows
    'Brand link:  ' + (v['Brand link'] || '-'),
    'Send via:    ' + v['Send via'],
    // api.whatsapp.com, not wa.me: a mobile network was found blocking DNS for wa.me
    'WhatsApp:    ' + (v['WhatsApp'] || '-') + (digits ? '   https://api.whatsapp.com/send?phone=' + digits : ''),
    'Email:       ' + (v['Email'] || '-'),
    'Logo:        ' + (v['Logo'] || 'none sent'),
    'Instagram:   ' + v['Instagram OK'] + ' (post it without their name, logo or contact details)',
    'Style they played with on the page: ' + (v['Style picked'] || '-'),
    '',
    'Came from:   ' + [v['Last source'], v['Last medium'], v['Last campaign']].filter(String).join(' / ') +
      (v['Click ID'] ? '  (' + v['Click ID type'] + ' ' + v['Click ID'] + ')' : ''),
    '',
    'Sheet row ' + row + ': ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
  ];
  MailApp.sendEmail({
    to: to,
    subject: 'Free demo request: ' + v['Business'] + ' (due ' + v['Due by'] + ')',
    body: lines.join('\n'),
    replyTo: /@/.test(v['Email']) ? v['Email'] : undefined,
    name: 'AI Profit Lab demos'
  });
}

function confirmToVisitor(v) {
  var hi = v['Name'] ? 'Hi ' + v['Name'] + ',' : 'Hello,';
  MailApp.sendEmail({
    to: v['Email'],
    subject: 'Your free website demo for ' + v['Business'],
    body: [
      hi,
      '',
      'Thank you. I have your request for a free website demo for ' + v['Business'] + '.',
      'You will get the link at this address by ' + v['Due by'] + ' (Muscat time).',
      '',
      'Nothing else to do. If you want to add something, a logo, a photo, a colour you like,',
      'just reply to this email.',
      '',
      'Nahid Abyari',
      'Founder, AI Profit Lab',
      'hello@aiprofitlab.io · aiprofitlab.io'
    ].join('\n'),
    replyTo: 'hello@aiprofitlab.io',
    name: 'AI Profit Lab'
  });
}

/* ── one-time setup ───────────────────────────────────────────────────────── */

/** Run once from the editor: creates the tab and grants the script its scopes. */
function setup() {
  ensureSheet();
  var it = DriveApp.getFoldersByName(FOLDER);
  if (!it.hasNext()) DriveApp.createFolder(FOLDER);
  MailApp.getRemainingDailyQuota();
  console.log('Ready. Requests go to: ' + SpreadsheetApp.getActiveSpreadsheet().getUrl());
}
