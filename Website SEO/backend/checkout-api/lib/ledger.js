/**
 * The order ledger.
 *
 * Same shape and same auth as the Smart Storefront's ledger (Cloud Run runtime
 * service account, a Google Sheet, because Nahid works in a spreadsheet and not
 * a database console). One difference that matters: this one is OPTIONAL.
 *
 * An order is written here BEFORE Thawani is called, so that a gateway failure
 * leaves an order behind instead of a silence. That guarantee is worth more
 * than the storage backend, so if CHECKOUT_SHEET_ID is not set the record goes
 * to stdout as one line of JSON — Cloud Logging keeps it, it is greppable by
 * reference, and the checkout keeps working. What must never happen is a
 * payment session existing for an order nobody recorded.
 */

const { google } = require("googleapis");

const SHEET_ID = process.env.CHECKOUT_SHEET_ID || "";
const TAB = process.env.CHECKOUT_SHEET_TAB || "Checkout_Orders";

const HEADERS = [
  "Timestamp",
  "Ref",
  "Status",
  "Plan",
  "Items",
  "Due baisa",
  "Total baisa",
  "Due OMR",
  "Total OMR",
  "Name",
  "Business",
  "Email",
  "WhatsApp",
  "CR",
  "City",
  "Notes",
  "Monthly",
  "Session ID",
  "Invoice",
  "Page",
  "Thawani env",
  // Recurring. "Customer ID" is the Thawani cus_… handle and is the ONLY thing
  // that makes a second charge possible — losing it means the saved card is
  // unreachable and the subscription has to be re-signed by the customer.
  "Customer ID",
  "Monthly baisa",
  "Subscription",
  "Next charge",
  "Anchor day",
  "Cycles",
  "Failures",
];

const COL = Object.fromEntries(HEADERS.map((h, i) => [h, i]));
const LAST_COL = columnLetter(HEADERS.length - 1);

// An order's life. Only PAID is money.
const STATUS = {
  CREATED: "Created", // written before Thawani was called
  PENDING: "Awaiting_Payment", // session created, buyer sent to the hosted page
  FAILED: "Gateway_Failed", // Thawani refused; the page fell back to WhatsApp
  PAID: "Paid",
  CANCELLED: "Cancelled",
};

const enabled = () => Boolean(SHEET_ID);

let sheetsClient = null;
function client() {
  if (!sheetsClient) {
    const auth = new google.auth.GoogleAuth({
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });
    sheetsClient = google.sheets({ version: "v4", auth });
  }
  return sheetsClient;
}

function columnLetter(index) {
  let n = index;
  let out = "";
  do {
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return out;
}

/** Bootstrap an empty spreadsheet on first use. No-op when there is no sheet. */
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

  const first = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `${TAB}!A1:${LAST_COL}1`,
  });
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

/** One line of JSON on stdout. The fallback ledger, and the audit trail either way. */
function log(event, record) {
  console.log(JSON.stringify({ ledger: event, ...record }));
}

async function append(record) {
  log("order", record);
  if (!enabled()) return false;
  try {
    const row = HEADERS.map((h) => (record[h] === undefined ? "" : record[h]));
    await client().spreadsheets.values.append({
      spreadsheetId: SHEET_ID,
      range: `${TAB}!A:${LAST_COL}`,
      valueInputOption: "USER_ENTERED",
      requestBody: { values: [row] },
    });
    return true;
  } catch (err) {
    // The stdout line above already happened, so the order is not lost. Never
    // fail a checkout because a spreadsheet was unreachable.
    console.error("LEDGER APPEND FAILED:", record.Ref, err && err.message);
    return false;
  }
}

async function rows() {
  const res = await client().spreadsheets.values.get({
    spreadsheetId: SHEET_ID,
    range: `${TAB}!A2:${LAST_COL}`,
  });
  return (res.data.values || []).map((values, i) => ({
    rowNumber: i + 2, // 1-indexed, and row 1 is the header
    get: (h) => values[COL[h]] || "",
  }));
}

async function findByRef(ref) {
  if (!enabled() || !ref) return null;
  try {
    const all = await rows();
    const want = String(ref).trim().toUpperCase();
    return all.find((r) => r.get("Ref").trim().toUpperCase() === want) || null;
  } catch (err) {
    console.error("LEDGER LOOKUP FAILED:", ref, err && err.message);
    return null;
  }
}

async function findBySession(sessionId) {
  if (!enabled() || !sessionId) return null;
  try {
    const all = await rows();
    return all.find((r) => r.get("Session ID").trim() === String(sessionId).trim()) || null;
  } catch (err) {
    console.error("LEDGER LOOKUP FAILED:", sessionId, err && err.message);
    return null;
  }
}

async function update(ref, patch) {
  log("update", { Ref: ref, ...patch });
  if (!enabled()) return false;
  try {
    const row = await findByRef(ref);
    if (!row) {
      console.error("LEDGER UPDATE: no row for", ref);
      return false;
    }
    const data = Object.entries(patch).map(([header, value]) => ({
      range: `${TAB}!${columnLetter(COL[header])}${row.rowNumber}`,
      values: [[value]],
    }));
    await client().spreadsheets.values.batchUpdate({
      spreadsheetId: SHEET_ID,
      requestBody: { valueInputOption: "USER_ENTERED", data },
    });
    return true;
  } catch (err) {
    console.error("LEDGER UPDATE FAILED:", ref, err && err.message);
    return false;
  }
}

function rowUrl(rowNumber) {
  return SHEET_ID
    ? `https://docs.google.com/spreadsheets/d/${SHEET_ID}/edit#gid=0&range=A${rowNumber}`
    : "";
}

module.exports = { HEADERS, STATUS, TAB, enabled, ensureTab, append, update, findByRef, findBySession, allRows: rows, rowUrl, log };
