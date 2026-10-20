/**
 * Brand Discovery questionnaire - intake.
 *
 * Backs https://aiprofitlab.io/en/brand-discovery/ (and /ar/brand-discovery/, the
 * same form in Arabic): one row per submitted brief in a Google Sheet, every
 * uploaded file in a Drive folder, and an email to Nahid both when a brief lands
 * and whenever anyone edits the sheet afterwards.
 *
 * Adapted from tools/onboarding/brief-apps-script.gs (the Smart Storefront brief).
 * Same mechanics; only the tab, the folder, the fixed columns and the wording
 * differ. It needs its OWN spreadsheet and its own deployment - do not paste it
 * into the storefront brief sheet, the two would fight over doPost.
 *
 * This is a Google Apps Script bound to the spreadsheet. It is NOT deployed by any
 * pipeline in this repo - it is pasted into the script editor by hand, and this
 * file is the copy of record. If you change one, change the other.
 *
 * ── SETUP, ONCE ────────────────────────────────────────────────────────────────
 *  1. Create a Google Sheet. Name it anything - "Brand discovery briefs".
 *  2. Extensions > Apps Script. Delete the sample, paste this whole file.
 *  3. Run `setup` once. It will ask for permission (sheet, Drive, mail); allow it.
 *     It creates the tab, the Drive folder, and the on-change email trigger.
 *  4. Deploy > New deployment > type "Web app".
 *       Execute as:      Me
 *       Who has access:  Anyone            <- must be "Anyone", not "Anyone with
 *                                             a Google account". Clients are not
 *                                             signed in, and the second option
 *                                             answers them with a login page.
 *  5. Copy the /exec URL it gives you into BRIEF_ENDPOINT in
 *     tools/brand-discovery/brand-discovery.src.html, run
 *     tools/brand-discovery/build_brand_discovery.py, then deploy the site.
 *  6. Open the /exec URL in a browser. It should say the service is alive.
 *
 * ── CHANGING THE QUESTIONS ─────────────────────────────────────────────────────
 *  Don't touch this file. The page sends the question labels (always in English,
 *  whichever language the client filled it in) with every brief, and this script
 *  appends any column it has not seen before, at the END of the header row.
 *  Existing rows keep their positions.
 *
 * ── REDEPLOYING ────────────────────────────────────────────────────────────────
 *  After editing this script: Deploy > Manage deployments > edit > Version: New.
 *  Keeping the same deployment keeps the same /exec URL, so the site needs no
 *  change. Creating a NEW deployment gives a NEW URL and the site will keep
 *  posting to the old one.
 */

/* ── settings ─────────────────────────────────────────────────────────────── */

/** Empty means "the account that owns this script". Put an address here to send
 *  the notifications somewhere else, or several separated by commas. */
var NOTIFY_EMAIL = '';

var TAB = 'Brand discovery';
var FOLDER = 'Brand discovery uploads';
var SITE = 'https://aiprofitlab.io/en/brand-discovery/';

/** Columns this script owns. Question columns are appended after them, in the
 *  order the form asks, and never reordered. */
var FIXED = ['Timestamp', 'Status', 'Business', 'Contact', 'Email', 'WhatsApp',
             'Project type', 'Answered', 'Files', 'Full brief'];

/** A Sheets cell holds at most 50,000 characters, and one over the limit fails
 *  the whole setValues - which would turn a good brief into an error the client
 *  sees. Long answers are cut in the CELL only; the email carries the full text. */
var CELL_MAX = 49000;

/* ── web app ──────────────────────────────────────────────────────────────── */

function doGet() {
  return json({ ok: true, service: 'brand-discovery-intake' });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return json({ ok: false, error: 'empty_body' });

    var body = JSON.parse(e.postData.contents);
    var rows = body.rows || [];
    if (!rows.length) return json({ ok: false, error: 'no_answers' });

    var sheet = ensureSheet();

    /* Files first: a row that promises links we failed to write is worse than a
       slow submit. If Drive refuses, the whole brief fails and the page still
       has it on screen to send another way. */
    var links = saveFiles(body);

    var headers = ensureColumns(sheet, rows);
    var byHeader = {};
    rows.forEach(function (r) { byHeader[r.q] = r.v; });

    var fixed = {
      'Timestamp': Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HH:mm'),
      'Status': 'New',
      'Business': body.business || '',
      'Contact': body.name || '',
      'Email': body.email || '',
      'WhatsApp': body.whatsapp || '',
      'Project type': body.projectType || '',
      'Answered': (body.answered || 0) + ' of ' + (body.of || rows.length),
      'Files': links.join('\n'),
      'Full brief': body.text || ''
    };

    var line = headers.map(function (h) {
      var v = String((h in fixed) ? fixed[h] : (byHeader[h] || ''));
      return v.length > CELL_MAX ? v.slice(0, CELL_MAX) + '\n[cut to fit the cell - full text is in the email]' : v;
    });

    /* THE ORDER OF THESE TWO CALLS IS THE WHOLE POINT.
       setValues writes the way a person typing would: a cell starting with "+"
       or "=" is parsed as a formula, so a WhatsApp number lands as #ERROR! and a
       long numeric id is rounded to double precision. Setting the range to plain
       text FIRST stops the parse. Doing it afterwards is too late - the value has
       already been mangled, and reformatting does not bring it back.
       The timestamp is written as text too, in Muscat time, for the same reason:
       one format for the row, no juggling. "yyyy-MM-dd HH:mm" sorts correctly as
       text, so nothing is lost. */
    var row = sheet.getLastRow() + 1;
    var range = sheet.getRange(row, 1, 1, line.length);
    range.setNumberFormat('@');
    range.setValues([line]);

    // A brief that reached the sheet is safe. An email that fails after that
    // must not turn a saved brief into an error the client sees.
    try {
      notifyNew(body, links, row);
      markQuiet();
    } catch (mailErr) {
      console.error('BRIEF SAVED BUT EMAIL FAILED: ' + mailErr);
    }

    return json({ ok: true, row: row, files: links.length });
  } catch (err) {
    console.error('BRIEF POST FAILED: ' + (err && err.stack ? err.stack : err));
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
 * Widen the header row for any question this sheet has not seen before. New
 * columns go on the END - a live sheet with briefs already in it stays aligned
 * only if new columns arrive after the last one anybody has written to.
 */
function ensureColumns(sheet, rows) {
  var last = Math.max(sheet.getLastColumn(), FIXED.length);
  var headers = sheet.getRange(1, 1, 1, last).getValues()[0]
    .map(function (h) { return String(h).trim(); });

  /* Trim TRAILING blanks only. Dropping every blank would re-pack the row and
     silently shift each column after a gap onto the wrong data - on a sheet that
     already has briefs in it, that is unrecoverable. A gap in the middle is left
     exactly where it is. */
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
    console.log('brand discovery sheet widened by ' + add.length + ' column(s)');
  }
  return headers;
}

/* ── drive ────────────────────────────────────────────────────────────────── */

function briefFolder() {
  var it = DriveApp.getFoldersByName(FOLDER);
  return it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER);
}

function saveFiles(body) {
  var files = body.files || [];
  if (!files.length) return [];

  var who = (body.business || body.name || 'brief').replace(/[^\w \-&]/g, '').slice(0, 60).trim();
  var stamp = Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HHmm');
  var folder = briefFolder().createFolder(stamp + ' - ' + (who || 'brief'));

  var out = [];
  files.forEach(function (f) {
    try {
      var blob = Utilities.newBlob(Utilities.base64Decode(f.data), f.type, f.name);
      var saved = folder.createFile(blob);
      out.push((f.field ? f.field + ': ' : '') + saved.getName() + ' — ' + saved.getUrl());
    } catch (err) {
      out.push('FAILED to save ' + f.name + ' (' + err + ')');
      console.error('FILE SAVE FAILED: ' + f.name + ' ' + err);
    }
  });

  // The client's own folder, so one click in the email opens everything at once.
  out.push('Folder: ' + folder.getUrl());
  return out;
}

/* ── email ────────────────────────────────────────────────────────────────── */

function recipients() {
  return NOTIFY_EMAIL || Session.getEffectiveUser().getEmail();
}

function sheetUrl() {
  return SpreadsheetApp.getActiveSpreadsheet().getUrl();
}

function notifyNew(body, links, row) {
  var who = body.business || body.name || 'Someone';
  var arabic = body.lang === 'ar';
  var lines = [
    who + ' has filled in the brand discovery questionnaire.',
    '',
    'Contact:   ' + (body.name || '—'),
    'Email:     ' + (body.email || '—'),
    'WhatsApp:  ' + (body.whatsapp || '—'),
    'Project:   ' + (body.projectType || '—'),
    'Language:  ' + (arabic ? 'Arabic - they filled the form in Arabic' : 'English'),
    'Answered:  ' + (body.answered || 0) + ' of ' + (body.of || '—'),
    'Files:     ' + (links.length ? (links.length - 1) + ' uploaded' : 'none'),
    ''
  ];
  lines.push('Sheet row ' + row + ': ' + sheetUrl(), '');
  if (links.length) lines.push('Files:', links.join('\n'), '');
  lines.push('────────────────────────────────────────', '', body.text || '');

  /* The same brief as a .md file, so it can be saved or dropped into a project
     folder without copying it out of the email body. */
  var slug = String(body.business || body.name || 'brief').toLowerCase()
    .replace(/[^a-z0-9؀-ۿ]+/g, '-').replace(/^-|-$/g, '') || 'brief';
  var md = Utilities.newBlob(body.text || '', 'text/markdown', 'brand-discovery-' + slug + '.md');

  MailApp.sendEmail({
    to: recipients(),
    subject: 'Brand discovery: ' + who + (arabic ? '  [Arabic]' : ''),
    body: lines.join('\n'),
    attachments: [md],
    replyTo: body.email || undefined,
    name: 'AI Profit Lab briefs'
  });
}

/**
 * Installed by setup(). Fires when the sheet changes - including edits YOU make
 * by hand, which is the point: a note typed into a Status cell is a decision, and
 * this is the record of it.
 *
 * A new brief already sends its own, much better, email from doPost. markQuiet()
 * leaves a 90-second flag behind so this one does not double up on it.
 */
function onSheetChange(e) {
  try {
    if (isQuiet()) return;
    /* onChange fires per change, so tidying up twenty cells would otherwise send
       twenty emails and eat the daily MailApp quota - after which a real brief's
       notification is the one that fails. One notice per CHANGE_WINDOW covers the
       whole editing session. */
    if (!changeWindowOpen()) return;
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    MailApp.sendEmail({
      to: recipients(),
      subject: 'Brand discovery sheet edited — ' + ss.getName(),
      body: [
        'Something changed in the brand discovery sheet.',
        '',
        'Sheet:  ' + sheet.getName(),
        'Change: ' + ((e && e.changeType) || 'EDIT'),
        'When:   ' + Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HH:mm') + ' (Muscat)',
        '',
        sheetUrl(),
        '',
        'This is the plain change notice, and it covers everything edited in the',
        'last ' + (CHANGE_WINDOW / 60000) + ' minutes, not one cell. A newly submitted brief sends its',
        'own email with the whole brief in it, and suppresses this one.'
      ].join('\n'),
      name: 'AI Profit Lab briefs'
    });
  } catch (err) {
    console.error('CHANGE EMAIL FAILED: ' + err);
  }
}

/** At most one "sheet was edited" email per this many ms. */
var CHANGE_WINDOW = 10 * 60 * 1000;

function changeWindowOpen() {
  var props = PropertiesService.getScriptProperties();
  var last = Number(props.getProperty('lastChangeMail') || 0);
  if (Date.now() - last < CHANGE_WINDOW) return false;
  props.setProperty('lastChangeMail', String(Date.now()));
  return true;
}

function markQuiet() {
  PropertiesService.getScriptProperties().setProperty('quietUntil', String(Date.now() + 90000));
}

function isQuiet() {
  var v = Number(PropertiesService.getScriptProperties().getProperty('quietUntil') || 0);
  return Date.now() < v;
}

/* ── one-time setup ───────────────────────────────────────────────────────── */

function setup() {
  ensureSheet();
  briefFolder();

  var have = ScriptApp.getProjectTriggers().some(function (t) {
    return t.getHandlerFunction() === 'onSheetChange';
  });
  if (!have) {
    ScriptApp.newTrigger('onSheetChange')
      .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
      .onChange()
      .create();
  }

  MailApp.sendEmail({
    to: recipients(),
    subject: 'Brand discovery intake is set up',
    body: [
      'The brand discovery intake is ready.',
      '',
      'Sheet:  ' + sheetUrl(),
      'Drive:  ' + briefFolder().getUrl(),
      'Form:   ' + SITE,
      '',
      'Still to do: Deploy > New deployment > Web app (Execute as: Me,',
      'Who has access: Anyone), then paste the /exec URL into BRIEF_ENDPOINT',
      'in tools/brand-discovery/brand-discovery.src.html and rebuild.'
    ].join('\n'),
    name: 'AI Profit Lab briefs'
  });

  console.log('Setup done. Sheet: ' + sheetUrl());
}

/** Handy in the editor: proves the whole path works without touching the site. */
function selfTest() {
  var res = doPost({
    postData: {
      contents: JSON.stringify({
        business: 'Test Trading LLC',
        name: 'Test Person',
        email: 'test@example.com',
        whatsapp: '+968 9000 0000',
        projectType: 'A brand new brand',
        lang: 'en',
        answered: 2, of: 2,
        rows: [
          { q: 'Form language', v: 'English' },
          { q: 'Business name', v: 'Test Trading LLC' },
          { q: 'In one sentence: what do you do, and for whom?', v: 'Test answer.' }
        ],
        files: [],
        text: '# Brand discovery — Test Trading LLC\n\nThis is a self test. Delete the row.'
      })
    }
  });
  console.log(res.getContent());
}
