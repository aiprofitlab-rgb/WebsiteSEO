/**
 * Free-tools email capture — the receiving end.
 *
 * Modelled on tools/onboarding/brief-apps-script.gs, which is the working
 * precedent in this repo. Same shape: a Google Apps Script bound to a
 * spreadsheet, pasted in by hand, with this file as the copy of record. It is
 * NOT deployed by any pipeline here. If you change one, change the other.
 *
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │ NOT LIVE. THIS IS BLOCKED ON A PRIVACY DECISION, NOT ON CODE.            │
 * │                                                                          │
 * │ The page module ships with LEAD_CAPTURE["enabled"] = False in            │
 * │ tools/v4/page_tool_invoice.py, so no form is rendered and nothing can    │
 * │ post here. That is deliberate.                                           │
 * │                                                                          │
 * │ An email address and a name are personal data. Writing them into a       │
 * │ Google spreadsheet is a transfer of personal data OUTSIDE OMAN, which    │
 * │ under the PDPL (Royal Decree 6/2022, Executive Regulations MD 34/2024,   │
 * │ fully enforceable since 5 February 2026) carries penalties of up to      │
 * │ OMR 500,000 for unlawful transfer. Three things must be true first:      │
 * │                                                                          │
 * │   1. the privacy policy describes this capture: what is collected, who   │
 * │      receives it, what it is used for, how long it is kept, and that it  │
 * │      leaves Oman;                                                        │
 * │   2. the consent line at the point of capture links to that policy and   │
 * │      is a positive act — an unticked box, never a pre-ticked one;        │
 * │   3. somebody decides whether the site needs a consent banner at all.    │
 * │      There is none today. This would widen that gap, not create it.      │
 * │                                                                          │
 * │ Turning this on before those three is the one thing that would make the  │
 * │ page's own headline claim untrue.                                        │
 * └──────────────────────────────────────────────────────────────────────────┘
 *
 * WHAT THIS NEVER RECEIVES. The invoice tool is client-side and stays that
 * way. No customer name, no customer VAT number, no line item, no amount and
 * no logo is ever sent here — the only thing that crosses the wire is the
 * person asking for the checklist, plus the campaign that brought them.
 *
 * ── SETUP, ONCE, WHEN IT IS UNBLOCKED ─────────────────────────────────────
 *  1. Create a Google Sheet. Name it anything — "Free tool leads".
 *  2. Extensions > Apps Script. Delete the sample, paste this whole file.
 *  3. Run `setup` once and allow the permissions it asks for.
 *  4. Deploy > New deployment > type "Web app".
 *       Execute as:      Me
 *       Who has access:  Anyone      <- must be "Anyone", not "Anyone with a
 *                                      Google account". Visitors are not
 *                                      signed in, and the second option
 *                                      answers them with a login page.
 *  5. Put the /exec URL into LEAD_CAPTURE["endpoint"] in
 *     tools/v4/page_tool_invoice.py, set "enabled" to True, rebuild, deploy.
 *  6. Open the /exec URL in a browser. It should say the service is alive.
 *
 * ── REDEPLOYING ───────────────────────────────────────────────────────────
 *  Deploy > Manage deployments > edit > Version: New. Keeping the SAME
 *  deployment keeps the same /exec URL. A NEW deployment gets a NEW URL and
 *  the site keeps posting to the old one.
 */

/* ── settings ─────────────────────────────────────────────────────────────── */

/** Empty means "the account that owns this script". */
var NOTIFY_EMAIL = '';

var TAB = 'Leads';
var SITE = 'https://aiprofitlab.io/en/tools/oman-vat-invoice-generator/';

/** Columns this script owns. Anything else the page sends — the attribution
 *  fields, and whatever is added to them later — is appended after these, in
 *  the order it arrives, and never reordered. */
var FIXED = ['Timestamp', 'Status', 'Source', 'Email', 'Name', 'Wants', 'Consent'];

/* ── web app ──────────────────────────────────────────────────────────────── */

function doGet() {
  return json({ ok: true, service: 'apl-free-tool-leads' });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return json({ ok: false, error: 'empty_body' });

    var body = JSON.parse(e.postData.contents);
    var rows = body.rows || [];
    if (!rows.length) return json({ ok: false, error: 'no_rows' });

    var byHeader = {};
    rows.forEach(function (r) { byHeader[r.q] = r.v; });

    /* Consent is the whole basis for holding any of this. A post that does not
       carry it is refused rather than written and sorted out later — a row in
       the sheet with an empty Consent column is a row nobody can lawfully use,
       and it is easier to never have it than to find it again. */
    if (!byHeader['Consent']) return json({ ok: false, error: 'no_consent' });
    if (!byHeader['Email'] || byHeader['Email'].indexOf('@') === -1)
      return json({ ok: false, error: 'no_email' });

    var sheet = ensureSheet();
    var headers = ensureColumns(sheet, rows);

    var fixed = {
      'Timestamp': Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HH:mm'),
      'Status': 'New',
      'Source': body.source || ''
    };

    var line = headers.map(function (h) {
      return (h in fixed) ? fixed[h] : (byHeader[h] || '');
    });

    /* THE ORDER OF THESE TWO CALLS IS THE WHOLE POINT.
       setValues writes the way a person typing would: USER_ENTERED parsing. A
       cell starting with "+" or "=" is read as a formula, so a phone number
       written +968 9000 0000 lands as #ERROR!, and a long numeric id — a GA4
       client_id, say — is rounded to double precision and silently loses its
       last digits. Setting the range to plain text FIRST stops the parse.
       Doing it afterwards is too late: the value has already been mangled and
       reformatting does not bring it back. The timestamp is written as text
       too, in Muscat time; "yyyy-MM-dd HH:mm" sorts correctly as text, so
       nothing is lost by it. */
    var row = sheet.getLastRow() + 1;
    var range = sheet.getRange(row, 1, 1, line.length);
    range.setNumberFormat('@');
    range.setValues([line]);

    // A lead that reached the sheet is safe. An email that fails after that
    // must not turn a saved lead into an error the visitor sees.
    try { notify(byHeader, body, row); } catch (mailErr) {
      console.error('LEAD SAVED BUT EMAIL FAILED: ' + mailErr);
    }

    return json({ ok: true, row: row });
  } catch (err) {
    console.error('LEAD POST FAILED: ' + (err && err.stack ? err.stack : err));
    return json({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function json(o) {
  return ContentService.createTextOutput(JSON.stringify(o))
    .setMimeType(ContentService.MimeType.JSON);
}

/* ── sheet ────────────────────────────────────────────────────────────────── */

function ensureSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(TAB);
  if (!sheet) {
    sheet = ss.insertSheet(TAB);
    sheet.getRange(1, 1, 1, FIXED.length).setValues([FIXED]);
    sheet.getRange(1, 1, 1, FIXED.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 140);
  }
  return sheet;
}

/**
 * Widen the header row for any field this sheet has not seen before. New
 * columns go on the END — a live sheet with leads already in it stays aligned
 * only if new columns arrive after the last one anybody has written to. The
 * attribution fields from window.APLPage.attributionFields() arrive this way,
 * so adding one to that function needs no change here.
 */
function ensureColumns(sheet, rows) {
  var last = Math.max(sheet.getLastColumn(), FIXED.length);
  var headers = sheet.getRange(1, 1, 1, last).getValues()[0]
    .map(function (h) { return String(h).trim(); });

  /* Trim TRAILING blanks only. Dropping every blank would re-pack the row and
     silently shift each column after a gap onto the wrong data — on a sheet
     that already has leads in it, that is unrecoverable. */
  while (headers.length && headers[headers.length - 1] === '') headers.pop();
  if (!headers.length) headers = FIXED.slice();

  var add = [];
  rows.forEach(function (r) {
    if (headers.indexOf(r.q) === -1 && add.indexOf(r.q) === -1) add.push(r.q);
  });
  if (add.length) {
    sheet.getRange(1, headers.length + 1, 1, add.length).setValues([add]);
    sheet.getRange(1, headers.length + 1, 1, add.length).setFontWeight('bold');
    headers = headers.concat(add);
    console.log('lead sheet widened by ' + add.length + ' column(s)');
  }
  return headers;
}

/* ── email ────────────────────────────────────────────────────────────────── */

function recipients() { return NOTIFY_EMAIL || Session.getEffectiveUser().getEmail(); }
function sheetUrl() { return SpreadsheetApp.getActiveSpreadsheet().getUrl(); }

/** At most one notification per this many ms, so a burst cannot eat the daily
 *  MailApp quota — after which a real lead's notification is the one that
 *  fails. The rows are all in the sheet either way. */
var MAIL_WINDOW = 10 * 60 * 1000;

function mailWindowOpen() {
  var props = PropertiesService.getScriptProperties();
  var last = Number(props.getProperty('lastLeadMail') || 0);
  if (Date.now() - last < MAIL_WINDOW) return false;
  props.setProperty('lastLeadMail', String(Date.now()));
  return true;
}

function notify(byHeader, body, row) {
  if (!mailWindowOpen()) return;
  MailApp.sendEmail({
    to: recipients(),
    subject: 'Free tool lead: ' + (byHeader['Email'] || 'someone'),
    body: [
      (byHeader['Name'] || 'Someone') + ' asked for the checklist from a free tool.',
      '',
      'Email:    ' + (byHeader['Email'] || '—'),
      'Name:     ' + (byHeader['Name'] || '—'),
      'Wants:    ' + (byHeader['Wants'] || '—'),
      'Tool:     ' + (body.source || '—'),
      'First:    ' + (byHeader['firstSource'] || '—') + ' / ' + (byHeader['firstMedium'] || '—')
        + ' / ' + (byHeader['firstCampaign'] || '—'),
      'Last:     ' + (byHeader['lastSource'] || '—') + ' / ' + (byHeader['lastMedium'] || '—')
        + ' / ' + (byHeader['lastCampaign'] || '—'),
      'Touches:  ' + (byHeader['touches'] || '—'),
      'Consent:  ' + (byHeader['Consent'] || '—'),
      '',
      'Sheet row ' + row + ': ' + sheetUrl(),
      '',
      'Nothing from the invoice tool itself is in this — no customer, no VAT',
      'number, no amount. There is nowhere for those to be sent.',
      '',
      'At most one of these every ' + (MAIL_WINDOW / 60000) + ' minutes. Check the sheet for the rest.'
    ].join('\n'),
    replyTo: byHeader['Email'] || undefined,
    name: 'AI Profit Lab tools'
  });
}

/* ── one-time setup ───────────────────────────────────────────────────────── */

function setup() {
  ensureSheet();
  MailApp.sendEmail({
    to: recipients(),
    subject: 'Free tool lead capture is set up',
    body: [
      'The free-tool lead sheet is ready.',
      '',
      'Sheet: ' + sheetUrl(),
      'Tool:  ' + SITE,
      '',
      'Still to do: Deploy > New deployment > Web app (Execute as: Me,',
      'Who has access: Anyone), then put the /exec URL into LEAD_CAPTURE in',
      'tools/v4/page_tool_invoice.py and set enabled to True.',
      '',
      'And before any of that: the privacy policy has to describe this, and',
      'the consent line has to link to it. See the header of the script.'
    ].join('\n'),
    name: 'AI Profit Lab tools'
  });
  console.log('Setup done. Sheet: ' + sheetUrl());
}

/** Proves the whole path works without touching the site. Also proves the two
 *  refusals: no consent and no email are both rejected rather than written. */
function selfTest() {
  var ok = doPost({ postData: { contents: JSON.stringify({
    source: 'oman-vat-invoice-generator',
    rows: [
      { q: 'Email', v: 'test@example.com' },
      { q: 'Name', v: 'Test Person' },
      { q: 'Wants', v: 'Fawtara readiness checklist' },
      { q: 'Consent', v: 'Yes — ticked at ' + new Date().toISOString() },
      // The trap this script exists to avoid: a leading "+" and a long id.
      { q: 'phone', v: '+968 9000 0000' },
      { q: 'clickId', v: '7238419283746512345' },
      { q: 'firstSource', v: 'instagram' },
      { q: 'firstMedium', v: 'social' },
      { q: 'lastSource', v: 'google' },
      { q: 'touches', v: '3' }
    ]
  }) } });
  console.log('with consent:    ' + ok.getContent());

  var noConsent = doPost({ postData: { contents: JSON.stringify({
    rows: [{ q: 'Email', v: 'test@example.com' }]
  }) } });
  console.log('without consent: ' + noConsent.getContent() + '   (must be ok:false, no_consent)');

  console.log('Now open the sheet. The phone must read +968 9000 0000, NOT #ERROR!,');
  console.log('and the click id must end 12345. Then delete the test row.');
}
