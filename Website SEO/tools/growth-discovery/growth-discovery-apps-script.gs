/**
 * Growth Discovery questionnaire - intake.
 *
 * Backs https://aiprofitlab.io/en/growth-discovery/ (and /fa/ and /ar/, the same
 * form in Persian and Arabic): one row per submitted brief in a Google Sheet,
 * every voice answer in a Drive folder per client, and an email to Nahid with
 * the brief attached as a .md file - ready to paste into a planning session.
 *
 * Adapted from tools/brand-discovery/brand-discovery-apps-script.gs. Same
 * mechanics (the "Not sent yet" tab, the text-before-values rule, the change
 * notice). New here: voice answers arrive as files and the page marks where
 * each belongs with a [voice:FILE] token; this script swaps every token for the
 * file's Drive link in the sheet and in the email.
 *
 * It needs its OWN spreadsheet and its own deployment - do not paste it into
 * the brand discovery sheet, the two would fight over doPost.
 *
 * This is a Google Apps Script bound to the spreadsheet. It is NOT deployed by
 * any pipeline in this repo - it is pasted into the script editor by hand (or
 * pushed with clasp), and this file is the copy of record.
 *
 * ── SETUP, ONCE ────────────────────────────────────────────────────────────────
 *  1. Create a Google Sheet. Name it "Growth discovery briefs".
 *  2. Extensions > Apps Script. Delete the sample, paste this whole file.
 *  3. Run `setup` once. It will ask for permission (sheet, Drive, mail); allow it.
 *     It creates the tab, the Drive folder, and the on-change email trigger.
 *  4. Deploy > New deployment > type "Web app".
 *       Execute as:      Me
 *       Who has access:  Anyone            <- must be "Anyone", not "Anyone with
 *                                             a Google account".
 *  5. Copy the /exec URL into BRIEF_ENDPOINT in
 *     tools/growth-discovery/growth-discovery.src.html, run
 *     tools/growth-discovery/build_growth_discovery.py, then deploy the site.
 *  6. Open the /exec URL in a browser. It should say the service is alive.
 *
 * ── CHANGING THE QUESTIONS ─────────────────────────────────────────────────────
 *  Don't touch this file. The page sends the English question labels with every
 *  brief, and this script appends any column it has not seen before, at the END
 *  of the header row.
 *
 * ── REDEPLOYING ────────────────────────────────────────────────────────────────
 *  Deploy > Manage deployments > edit > Version: New. Keeping the same
 *  deployment keeps the same /exec URL.
 */

/* ── settings ─────────────────────────────────────────────────────────────── */

/** Empty means "the account that owns this script". Put an address here to send
 *  the notifications somewhere else, or several separated by commas. */
var NOTIFY_EMAIL = '';

var TAB = 'Growth discovery';
var FOLDER = 'Growth discovery voice notes';
var SITE = 'https://aiprofitlab.io/en/growth-discovery/';

/** Columns this script owns. Question columns are appended after them, in the
 *  order the form asks, and never reordered. */
var FIXED = ['Timestamp', 'Status', 'Business', 'Contact', 'WhatsApp', 'Email', 'Language',
             'Accounts', 'Gaps', 'Best fit', 'Chose', 'One more booking a week', 'Answered',
             'Voice notes', 'Full brief', 'First-month notes', 'Session'];

/** A Sheets cell holds at most 50,000 characters, and one over the limit fails
 *  the whole setValues - which would turn a good brief into an error the client
 *  sees. Long answers are cut in the CELL only; the email carries the full text. */
var CELL_MAX = 49000;

/* ── web app ──────────────────────────────────────────────────────────────── */

function doGet() {
  return json({ ok: true, service: 'growth-discovery-intake' });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) return json({ ok: false, error: 'empty_body' });

    var body = JSON.parse(e.postData.contents);
    // The page's "reached the last screen" / "send failed" pings, not a brief.
    if (body.kind === 'progress') return json(handleProgress(body));
    // After the X-ray: the plan they tapped, and the optional first-month notes.
    // Both land on the brief's own row, found by its session id.
    if (body.kind === 'choice') return json(handleChoice(body));
    if (body.kind === 'plan') return json(handlePlan(body));

    var rows = body.rows || [];
    if (!rows.length) return json({ ok: false, error: 'no_answers' });

    var sheet = ensureSheet();

    /* Files first: a row that promises links we failed to write is worse than a
       slow submit. If Drive refuses, the whole brief fails and the page still
       has it on screen to send another way. */
    var saved = saveFiles(body);
    var links = saved.lines;
    var text = withVoiceLinks(body.text || '', saved.byName);

    var headers = ensureColumns(sheet, rows);
    var byHeader = {};
    rows.forEach(function (r) { byHeader[r.q] = withVoiceLinks(r.v, saved.byName); });

    var fixed = {
      'Timestamp': Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HH:mm'),
      'Status': 'New',
      'Business': body.business || '',
      'Contact': body.name || '',
      'WhatsApp': body.whatsapp || '',
      'Email': body.email || '',
      'Language': body.langName || body.lang || '',
      'Accounts': body.accounts || '',
      'Gaps': String(body.gaps == null ? '' : body.gaps),
      'Best fit': body.fit || '',
      'Chose': body.choice || '',
      'One more booking a week': body.gain || '',
      'Answered': (body.answered || 0) + ' of ' + (body.of || rows.length),
      'Voice notes': links.join('\n'),
      'Full brief': text,
      'First-month notes': '',
      'Session': body.sid || ''
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
      notifyNew(body, links, row, text);
      markQuiet();
    } catch (mailErr) {
      console.error('BRIEF SAVED BUT EMAIL FAILED: ' + mailErr);
    }
    try { markSent(body.sid); } catch (sentErr) { console.error('MARK SENT FAILED: ' + sentErr); }

    return json({ ok: true, row: row, files: Object.keys(saved.byName).length });
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
    console.log('growth discovery sheet widened by ' + add.length + ' column(s)');
  }
  return headers;
}

/* ── drive ────────────────────────────────────────────────────────────────── */

function briefFolder() {
  var it = DriveApp.getFoldersByName(FOLDER);
  return it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER);
}

function saveFiles(body, label) {
  var files = body.files || [];
  var byName = {};
  if (!files.length) return { lines: [], byName: byName };

  var who = (body.business || body.name || 'brief').replace(/[^\w \-&]/g, '').slice(0, 60).trim();
  var stamp = Utilities.formatDate(new Date(), 'Asia/Muscat', 'yyyy-MM-dd HHmm');
  var folder = briefFolder().createFolder(stamp + ' - ' + (who || 'brief') + (label ? ' - ' + label : ''));

  var out = [];
  files.forEach(function (f) {
    try {
      var blob = Utilities.newBlob(Utilities.base64Decode(f.data), f.type, f.name);
      var saved = folder.createFile(blob);
      byName[f.name] = saved.getUrl();
      out.push((f.field ? f.field + ': ' : '') + saved.getName() + ' — ' + saved.getUrl());
    } catch (err) {
      out.push('FAILED to save ' + f.name + ' (' + err + ')');
      console.error('FILE SAVE FAILED: ' + f.name + ' ' + err);
    }
  });

  // The client's own folder, so one click in the email opens everything at once.
  out.push('Folder: ' + folder.getUrl());
  return { lines: out, byName: byName };
}

/** The page writes [voice:07-topQs.webm] where a voice answer belongs. Swap
 *  each for its Drive link (or say plainly that the file did not save). */
function withVoiceLinks(s, byName) {
  return String(s == null ? '' : s).replace(/\[voice:([^\]]+)\]/g, function (m, name) {
    return byName[name] ? 'Voice answer: ' + byName[name] : 'Voice answer: ' + name + ' (file missing - ask the client to resend)';
  });
}

/* ── email ────────────────────────────────────────────────────────────────── */

function recipients() {
  return NOTIFY_EMAIL || Session.getEffectiveUser().getEmail();
}

function sheetUrl() {
  return SpreadsheetApp.getActiveSpreadsheet().getUrl();
}

function notifyNew(body, links, row, text) {
  var who = body.business || body.name || 'Someone';
  var lang = body.langName || 'English';
  var lines = [
    who + ' has filled in the growth discovery questionnaire.',
    '',
    'Contact:   ' + (body.name || '—'),
    'WhatsApp:  ' + (body.whatsapp || '—'),
    'Email:     ' + (body.email || '—'),
    'Language:  ' + lang + (lang !== 'English' ? ' - typed answers are in ' + lang : ''),
    'Accounts:  ' + (body.accounts || '—'),
    'X-ray:     ' + (body.gaps == null ? '—' : body.gaps + ' gaps') + (body.fit ? ' · best fit ' + body.fit : ''),
    'One more booking a week: ' + (body.gain || '—'),
    'Chose:     ' + (body.choice || 'not yet - they pick a plan on the X-ray page'),
    'Answered:  ' + (body.answered || 0) + ' of ' + (body.of || '—'),
    'Voice:     ' + (links.length ? (links.length - 1) + ' voice answers' : 'none'),
    ''
  ];
  lines.push('Sheet row ' + row + ': ' + sheetUrl(), '');
  if (links.length) lines.push('Voice answers:', links.join('\n'), '');
  lines.push('────────────────────────────────────────', '', text || '');

  /* The same brief as a .md file, so it can be saved or dropped into a project
     folder without copying it out of the email body. */
  var slug = String(body.business || body.name || 'brief').toLowerCase()
    .replace(/[^a-z0-9؀-ۿ]+/g, '-').replace(/^-|-$/g, '') || 'brief';
  var md = Utilities.newBlob(text || '', 'text/markdown', 'growth-discovery-' + slug + '.md');

  MailApp.sendEmail({
    to: recipients(),
    subject: 'Growth discovery: ' + who + (lang !== 'English' ? '  [' + lang + ']' : '') + (body.gaps != null ? ' · ' + body.gaps + ' gaps' : ''),
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
      subject: 'Growth discovery sheet edited — ' + ss.getName(),
      body: [
        'Something changed in the growth discovery sheet.',
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

/* ── not sent yet ─────────────────────────────────────────────────────────────
   A client can answer everything, reach the review screen and close the tab
   without pressing Send. Their answers then exist only in their browser, and
   nothing here knew they had been at all. The page now pings this script when a
   client reaches the review (and again if a send fails), with their contact
   details and a session id. Each session is one row in the PENDING tab:

     Waiting  reached the review, no brief yet
     Alerted  still no brief WAIT_MS after their last visit to the review, and
              Nahid has been emailed about it (once)
     Sent     the brief arrived - the full brief has the same session id

   checkUnsent() runs on a 10-minute timer that exists only while a row is
   Waiting: handleProgress() creates it, checkUnsent() deletes it when there is
   nothing left to watch. */

var PENDING = 'Not sent yet';
var PENDING_COLS = ['First seen', 'Last seen', 'Status', 'Business', 'Contact', 'Email',
                    'WhatsApp', 'Language', 'Answered', 'Note', 'Session'];
var WAIT_MS = 30 * 60 * 1000;
var STAMP = 'yyyy-MM-dd HH:mm';

function pendingSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(PENDING);
  if (!sheet) {
    sheet = ss.insertSheet(PENDING);
    sheet.getRange(1, 1, 1, PENDING_COLS.length).setValues([PENDING_COLS]).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

/** Row number of a session in the PENDING tab, or 0. */
function findSession(sheet, sid) {
  var last = sheet.getLastRow();
  if (!sid || last < 2) return 0;
  var col = PENDING_COLS.indexOf('Session') + 1;
  var ids = sheet.getRange(2, col, last - 1, 1).getValues();
  for (var i = 0; i < ids.length; i++) if (String(ids[i][0]) === sid) return i + 2;
  return 0;
}

function handleProgress(body) {
  var sid = String(body.sid || '').slice(0, 64);
  if (!sid) return { ok: false, error: 'no_session' };
  var failed = body.stage === 'send_failed';
  var now = Utilities.formatDate(new Date(), 'Asia/Muscat', STAMP);

  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = pendingSheet();
    var row = findSession(sheet, sid);
    var cur = row ? sheet.getRange(row, 1, 1, PENDING_COLS.length).getValues()[0] : null;
    var status = cur ? String(cur[2]) : '';
    if (status === 'Sent') return { ok: true, status: status };

    var line = [
      cur ? String(cur[0]) : now,
      now,
      status === 'Alerted' ? 'Alerted' : 'Waiting',
      body.business || '', body.name || '', body.email || '', body.whatsapp || '',
      ({ ar: 'Arabic', fa: 'Persian' })[body.lang] || 'English',
      (body.answered || 0) + ' of ' + (body.of || '—'),
      failed ? 'Send failed: ' + String(body.why || 'unknown').slice(0, 120) : (cur ? String(cur[9]) : ''),
      sid
    ];
    if (!row) row = Math.max(sheet.getLastRow(), 1) + 1;
    // Plain text BEFORE the values, same reason as the brief row: "+968…" is a formula otherwise.
    var range = sheet.getRange(row, 1, 1, line.length);
    range.setNumberFormat('@');
    range.setValues([line]);
    markQuiet();
  } finally {
    lock.releaseLock();
  }

  ensureCheckTrigger();
  // A failed send is worth knowing about now, not in half an hour.
  if (failed) {
    try { notifyUnsent(body, now, 'Their Send button failed: ' + (body.why || 'unknown reason') + '.'); }
    catch (err) { console.error('SEND-FAILED EMAIL FAILED: ' + err); }
  }
  return { ok: true, status: 'Waiting' };
}

function markSent(sid) {
  if (!sid) return;
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = pendingSheet();
    var row = findSession(sheet, String(sid));
    if (!row) return;
    sheet.getRange(row, 2, 1, 2).setValues([[Utilities.formatDate(new Date(), 'Asia/Muscat', STAMP), 'Sent']]);
    markQuiet();
  } finally {
    lock.releaseLock();
  }
}

/** Timer: email Nahid about every session that reached the review and went quiet. */
function checkUnsent() {
  var sheet = pendingSheet();
  var last = sheet.getLastRow();
  var waiting = 0;
  if (last >= 2) {
    var data = sheet.getRange(2, 1, last - 1, PENDING_COLS.length).getValues();
    data.forEach(function (r, i) {
      if (String(r[2]) !== 'Waiting') return;
      var seen = Utilities.parseDate(String(r[1]), 'Asia/Muscat', STAMP).getTime();
      if (Date.now() - seen < WAIT_MS) { waiting++; return; }
      try {
        notifyUnsent({ business: r[3], name: r[4], email: r[5], whatsapp: r[6], lang: ({ Arabic: 'ar', Persian: 'fa' })[r[7]] || 'en',
                       answered: String(r[8]) }, String(r[1]),
                     'They reached the last screen but have not pressed Send for ' + (WAIT_MS / 60000) + ' minutes.' +
                     (r[9] ? ' ' + r[9] + '.' : ''));
        sheet.getRange(i + 2, 3).setValue('Alerted');
        markQuiet();
      } catch (err) {
        console.error('UNSENT EMAIL FAILED: ' + err);
        waiting++;  // try again on the next run
      }
    });
  }
  if (!waiting) removeCheckTrigger();
}

function notifyUnsent(p, seen, why) {
  var who = p.business || p.name || 'Someone';
  MailApp.sendEmail({
    to: recipients(),
    subject: 'Growth discovery NOT SENT: ' + who,
    body: [
      who + ' filled in the growth discovery questionnaire, but it has not reached us.',
      '',
      why,
      '',
      'Contact:   ' + (p.name || '—'),
      'Email:     ' + (p.email || '—'),
      'WhatsApp:  ' + (p.whatsapp || '—'),
      'Language:  ' + (({ ar: 'Arabic', fa: 'Persian' })[p.lang] || 'English'),
      'Answered:  ' + (typeof p.answered === 'string' ? p.answered : (p.answered || 0) + ' of ' + (p.of || '—')),
      'Last seen: ' + seen + ' (Muscat)',
      '',
      'Their answers are saved only in their own browser. Ask them to open',
      SITE + ' again on the same phone or computer,',
      'in the same browser, and press "Send and see my X-ray" on the last screen.',
      'If sending keeps failing, the last screen lets them download a PDF to send on WhatsApp.',
      '',
      'Sheet ("' + PENDING + '" tab): ' + sheetUrl()
    ].join('\n'),
    replyTo: p.email || undefined,
    name: 'AI Profit Lab briefs'
  });
}

function ensureCheckTrigger() {
  var have = ScriptApp.getProjectTriggers().some(function (t) { return t.getHandlerFunction() === 'checkUnsent'; });
  if (!have) ScriptApp.newTrigger('checkUnsent').timeBased().everyMinutes(10).create();
}

function removeCheckTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'checkUnsent') ScriptApp.deleteTrigger(t);
  });
}

/* ── after the X-ray: plan choice and first-month notes ─────────────────────────
   Both come from the results page, after the brief itself was sent, and carry
   the brief's session id. They are written onto the brief's row; if that row
   is missing (the brief never arrived), the notes get a row of their own. */

function headerRow(sheet) {
  var last = Math.max(sheet.getLastColumn(), FIXED.length);
  return sheet.getRange(1, 1, 1, last).getValues()[0].map(function (h) { return String(h).trim(); });
}

/** Row number of the brief with this session id in the main tab, or 0. */
function findBrief(sheet, sid) {
  var col = headerRow(sheet).indexOf('Session') + 1;
  var last = sheet.getLastRow();
  if (!sid || !col || last < 2) return 0;
  var ids = sheet.getRange(2, col, last - 1, 1).getValues();
  for (var i = ids.length - 1; i >= 0; i--) if (String(ids[i][0]) === sid) return i + 2;
  return 0;
}

function setText(sheet, row, col, v) {
  v = String(v == null ? '' : v);
  if (v.length > CELL_MAX) v = v.slice(0, CELL_MAX) + '\n[cut to fit the cell - full text is in the email]';
  var cell = sheet.getRange(row, col);
  cell.setNumberFormat('@');  // before the value, as everywhere in this script
  cell.setValue(v);
}

function handleChoice(body) {
  var sid = String(body.sid || '').slice(0, 64);
  var plan = String(body.plan || '').slice(0, 60);
  if (!sid || !plan) return { ok: false, error: 'no_choice' };
  var now = Utilities.formatDate(new Date(), 'Asia/Muscat', STAMP);
  var row = 0;
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = ensureSheet();
    row = findBrief(sheet, sid);
    if (row) setText(sheet, row, headerRow(sheet).indexOf('Chose') + 1, plan + ' · ' + now);
    markQuiet();
  } finally {
    lock.releaseLock();
  }
  try {
    var who = body.business || body.name || 'Someone';
    MailApp.sendEmail({
      to: recipients(),
      subject: 'Growth X-ray: ' + who + ' wants to talk about ' + plan,
      body: [
        who + ' has just tapped "' + plan + '" on their Growth X-ray.',
        'WhatsApp opened on their phone with a message to you, ready to send.',
        '',
        'Best fit from their answers: ' + (body.fit || '—'),
        'Contact:   ' + (body.name || '—'),
        'WhatsApp:  ' + (body.whatsapp || '—'),
        'Email:     ' + (body.email || '—'),
        '',
        row ? 'Their brief is row ' + row + ': ' + sheetUrl() : 'Their brief is not in the sheet (it may not have been sent).'
      ].join('\n'),
      replyTo: body.email || undefined,
      name: 'AI Profit Lab briefs'
    });
  } catch (err) {
    console.error('CHOICE EMAIL FAILED: ' + err);
  }
  return { ok: true, row: row };
}

function handlePlan(body) {
  var rows = body.rows || [];
  if (!rows.length) return { ok: false, error: 'no_answers' };
  var sid = String(body.sid || '').slice(0, 64);
  var now = Utilities.formatDate(new Date(), 'Asia/Muscat', STAMP);
  var saved = saveFiles(body, 'first month');
  var text = withVoiceLinks(body.text || '', saved.byName);
  var row = 0;
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = ensureSheet();
    var headers = ensureColumns(sheet, rows);
    row = findBrief(sheet, sid);
    if (!row) {
      row = sheet.getLastRow() + 1;
      var fixed = { 'Timestamp': now, 'Status': 'First-month notes only', 'Business': body.business || '', 'Contact': body.name || '',
                    'WhatsApp': body.whatsapp || '', 'Email': body.email || '', 'Language': body.langName || body.lang || '',
                    'Chose': body.choice || '', 'Session': sid };
      Object.keys(fixed).forEach(function (h) { setText(sheet, row, headers.indexOf(h) + 1, fixed[h]); });
    }
    rows.forEach(function (r) {
      var col = headers.indexOf(r.q) + 1;
      if (col) setText(sheet, row, col, withVoiceLinks(r.v, saved.byName));
    });
    setText(sheet, row, headers.indexOf('First-month notes') + 1, 'Received ' + now + (saved.lines.length ? '\n' + saved.lines.join('\n') : ''));
    markQuiet();
  } finally {
    lock.releaseLock();
  }
  try {
    var who = body.business || body.name || 'Someone';
    var slug = String(who).toLowerCase().replace(/[^a-z0-9؀-ۿ]+/g, '-').replace(/^-|-$/g, '') || 'brief';
    MailApp.sendEmail({
      to: recipients(),
      subject: 'Growth discovery: ' + who + ' sent their first-month notes',
      body: [who + ' filled in the optional first-month step after their X-ray.', '',
             'Chose:  ' + (body.choice || '—'), 'Sheet row ' + row + ': ' + sheetUrl(), '',
             (saved.lines.length ? 'Voice answers:\n' + saved.lines.join('\n') + '\n' : ''),
             '────────────────────────────────────────', '', text].join('\n'),
      attachments: [Utilities.newBlob(text, 'text/markdown', 'first-month-' + slug + '.md')],
      replyTo: body.email || undefined,
      name: 'AI Profit Lab briefs'
    });
  } catch (err) {
    console.error('PLAN EMAIL FAILED: ' + err);
  }
  return { ok: true, row: row, files: Object.keys(saved.byName).length };
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
    subject: 'Growth discovery intake is set up',
    body: [
      'The growth discovery intake is ready.',
      '',
      'Sheet:  ' + sheetUrl(),
      'Drive:  ' + briefFolder().getUrl(),
      'Form:   ' + SITE,
      '',
      'Still to do: Deploy > New deployment > Web app (Execute as: Me,',
      'Who has access: Anyone), then paste the /exec URL into BRIEF_ENDPOINT',
      'in tools/growth-discovery/growth-discovery.src.html and rebuild.'
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
        business: 'TEST - delete me', name: 'Test Person', email: 'test@example.com', whatsapp: '+968 9000 0000',
        accounts: '@test_page · Persian · Active', choice: '', gain: '520 OMR a month (typical booking 120 OMR)', gaps: 2, fit: 'Digital Partner',
        sid: 'selftest-' + Date.now(),
        lang: 'fa', langName: 'Persian', answered: 3, of: 3,
        rows: [
          { q: 'Form language', v: 'Persian' },
          { q: 'Business name', v: 'TEST - delete me' },
          { q: 'What do customers ask you most?', v: 'Typed part\n[voice:01-topQs.webm]' }
        ],
        files: [{ name: '01-topQs.webm', type: 'audio/webm', size: 4, data: Utilities.base64Encode('test'), field: 'What do customers ask you most?' }],
        text: '# Growth discovery — TEST\n\n[voice:01-topQs.webm]\n\nThis is a self test. Delete the row and the Drive folder.'
      })
    }
  });
  console.log(res.getContent());
}
