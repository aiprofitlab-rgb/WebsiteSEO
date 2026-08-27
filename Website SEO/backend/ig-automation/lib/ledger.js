/**
 * The lead ledger — a Google Sheet, because that is where Nahid actually looks.
 *
 * Two properties carried over from checkout-api's ledger, both deliberate:
 *
 *   1. Every record is printed to stdout as one line of JSON BEFORE the Sheets
 *      call. A sheet outage then degrades to "the lead is in the journal" rather
 *      than "the lead is gone". A DM was sent to a real person; losing the record
 *      of who is the actual failure.
 *   2. No sheet configured is a supported mode, not an error. The automation
 *      still works; the leads live in the logs.
 *
 * Two things are NOT carried over, and changing them back will break real data:
 *
 *   valueInputOption is RAW, not USER_ENTERED. Instagram comment and user IDs
 *   are 17-19 digit numerics. USER_ENTERED asks Sheets to parse cells the way
 *   typing does, so those become float64 numbers, which carry ~15 significant
 *   digits — the ID reads back CHANGED, with no error anywhere. The email
 *   backfill matches rows on comment ID, so a rounded ID means the email lands
 *   on the wrong row or none at all.
 *
 *   The append range is bounded to the header width, not A:Z. values.append
 *   searches its range for a table and anchors the new row on that table's first
 *   column; an open range latches onto any stray island of data to the right and
 *   walks the log sideways across the sheet, permanently. (Learned the hard way
 *   in SmartChatBot/aiden-backend/sheets.js.)
 */

const { google } = require("googleapis");

const SHEET_ID = process.env.IG_SHEET_ID || "";
const TAB = process.env.IG_SHEET_TAB || "IG_Leads";

const HEADERS = [
  "Timestamp",
  "Account",
  "Username",
  "Commenter ID",
  "Comment ID",
  "Media ID",
  "Permalink",
  "Comment text",
  "Keyword",
  "Rule",
  "DM",
  "Public reply",
  "Email",
  "Status",
  "Notes",
];

const COL = Object.fromEntries(HEADERS.map((h, i) => [h, i]));
const LAST_COL = columnLetter(HEADERS.length - 1);

const STATUS = {
  SENT: "DM_Sent",
  AWAITING_EMAIL: "Awaiting_Email",
  EMAIL_CAPTURED: "Email_Captured",
  FAILED: "Failed",
  SKIPPED: "Skipped",
};

const enabled = () => Boolean(SHEET_ID);

function columnLetter(index) {
  let n = index;
  let out = "";
  do {
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return out;
}

let sheetsClient = null;
function client() {
  if (!sheetsClient) {
    // GoogleAuth's default chain reads GOOGLE_APPLICATION_CREDENTIALS, so the
    // same code path works on the VPS (a service-account JSON key at a path) and
    // on Cloud Run (an attached runtime identity, no key file at all). Only set
    // IG_SA_KEY_FILE when the key is somewhere the env var cannot point at.
    const opts = { scopes: ["https://www.googleapis.com/auth/spreadsheets"] };
    if (process.env.IG_SA_KEY_FILE) opts.keyFile = process.env.IG_SA_KEY_FILE;
    sheetsClient = google.sheets({ version: "v4", auth: new google.auth.GoogleAuth(opts) });
  }
  return sheetsClient;
}
/** Tests inject a fake. */
function _setClient(c) {
  sheetsClient = c;
}

async function ensureTab() {
  if (!enabled()) return false;
  const sheets = client();
  const meta = await sheets.spreadsheets.get({ spreadsheetId: SHEET_ID });
  const exists = (meta.data.sheets || []).some((s) => s.properties.title === TAB);

  if (!exists) {
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SHEET_ID,
      requestBody: { requests: [{ addSheet: { properties: { title: TAB } } }] },
    });
  }

  const first = await sheets.spreadsheets.values.get({ spreadsheetId: SHEET_ID, range: `${TAB}!A1:${LAST_COL}1` });
  if (!first.data.values || first.data.values.length === 0) {
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEET_ID,
      range: `${TAB}!A1`,
      valueInputOption: "RAW",
      requestBody: { values: [HEADERS] },
    });
  }
  return true;
}

/** The journal. Happens whether or not a sheet exists, and before it is written. */
function log(event, record) {
  console.log(JSON.stringify({ ledger: event, ...record }));
}

function toRow(record) {
  // Every value goes across as a string. With RAW that is exactly what lands in
  // the cell, which is the whole point for the ID columns.
  return HEADERS.map((h) => (record[h] === undefined || record[h] === null ? "" : String(record[h])));
}

async function append(record) {
  log("lead", record);
  if (!enabled()) return false;
  try {
    await client().spreadsheets.values.append({
      spreadsheetId: SHEET_ID,
      range: `${TAB}!A1:${LAST_COL}`, // bounded — see the header comment
      valueInputOption: "RAW",
      insertDataOption: "INSERT_ROWS",
      requestBody: { values: [toRow(record)] },
    });
    return true;
  } catch (err) {
    console.error("LEDGER APPEND FAILED:", record["Comment ID"], err && err.message);
    return false;
  }
}

async function rows() {
  const res = await client().spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `${TAB}!A2:${LAST_COL}`,
    valueRenderOption: "UNFORMATTED_VALUE",
  });
  return (res.data.values || []).map((values, i) => ({
    rowNumber: i + 2,
    get: (h) => (values[COL[h]] === undefined ? "" : String(values[COL[h]])),
  }));
}

/** Backfill, keyed on comment ID — which is why it must not have been rounded. */
async function update(commentId, patch) {
  log("update", { "Comment ID": commentId, ...patch });
  if (!enabled() || !commentId) return false;
  try {
    const all = await rows();
    const want = String(commentId).trim();
    const row = all.find((r) => r.get("Comment ID").trim() === want);
    if (!row) {
      console.error("LEDGER UPDATE: no row for comment", want);
      return false;
    }
    const data = Object.entries(patch).map(([header, value]) => ({
      range: `${TAB}!${columnLetter(COL[header])}${row.rowNumber}`,
      values: [[value === undefined || value === null ? "" : String(value)]],
    }));
    await client().spreadsheets.values.batchUpdate({
      spreadsheetId: SHEET_ID,
      requestBody: { valueInputOption: "RAW", data },
    });
    return true;
  } catch (err) {
    console.error("LEDGER UPDATE FAILED:", commentId, err && err.message);
    return false;
  }
}

module.exports = { HEADERS, STATUS, TAB, COL, enabled, ensureTab, append, update, toRow, log, columnLetter, _setClient };
