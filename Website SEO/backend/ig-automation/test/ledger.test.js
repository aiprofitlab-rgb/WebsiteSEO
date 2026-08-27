/**
 * The two properties that protect real data in the sheet.
 *
 * Both are the kind of bug that produces no error at all — a wrong number in a
 * cell, and a log that walks sideways across the spreadsheet — so they get
 * asserted rather than remembered.
 */

// Read before the module is required: it captures the id at load time.
process.env.IG_SHEET_ID = "sheet-under-test";
process.env.IG_SHEET_TAB = "IG_Leads";

const test = require("node:test");
const assert = require("node:assert");

const ledger = require("../lib/ledger");

/** Records what the Sheets API was asked to do. */
function fakeSheets() {
  const appends = [];
  const batchUpdates = [];
  const store = { rows: [] };
  ledger._setClient({
    spreadsheets: {
      get: async () => ({ data: { sheets: [{ properties: { title: "IG_Leads" } }] } }),
      batchUpdate: async (a) => (batchUpdates.push(a), {}),
      values: {
        append: async (a) => (appends.push(a), store.rows.push(a.requestBody.values[0]), {}),
        get: async () => ({ data: { values: store.rows } }),
        update: async () => ({}),
        batchUpdate: async (a) => (batchUpdates.push(a), {}),
      },
    },
  });
  return { appends, batchUpdates, store };
}

const lead = (over = {}) => ({
  Timestamp: "2026-08-27 09:15:00",
  Account: "17841400000000000",
  Username: "a_follower",
  "Commenter ID": "78412345678901234",
  "Comment ID": "17925384756201943",
  "Media ID": "17900000000000001",
  "Comment text": "storefront",
  Keyword: "storefront",
  Rule: "storefront",
  DM: "sent",
  Status: ledger.STATUS.SENT,
  ...over,
});

test("a 17-digit comment id survives the write byte for byte", async () => {
  const f = fakeSheets();
  await ledger.append(lead());

  const row = f.appends[0].requestBody.values[0];
  const id = row[ledger.COL["Comment ID"]];

  assert.equal(id, "17925384756201943");
  assert.equal(typeof id, "string", "a number here would be rounded by float64 on the way in");
  assert.equal(id.length, 17);
  assert.equal(row[ledger.COL["Commenter ID"]], "78412345678901234");
});

test("valueInputOption is RAW — USER_ENTERED silently rounds those ids", async () => {
  // 17925384756201943 has 17 significant digits. float64 carries about 15, so
  // USER_ENTERED would store 17925384756201944 and the email backfill, which
  // matches on this column, would never find the row again.
  const asNumber = Number("17925384756201943");
  assert.notEqual(String(asNumber), "17925384756201943", "this is the corruption being guarded against");

  const f = fakeSheets();
  await ledger.append(lead());
  assert.equal(f.appends[0].valueInputOption, "RAW");
});

test("the append range is bounded to the header width, so the log cannot walk sideways", async () => {
  const f = fakeSheets();
  await ledger.append(lead());

  const range = f.appends[0].range;
  assert.equal(range, `IG_Leads!A1:${ledger.columnLetter(ledger.HEADERS.length - 1)}`);
  assert.ok(!/!A:[A-Z]+$/.test(range), "an open A:Z range latches onto stray data islands");
  assert.equal(f.appends[0].insertDataOption, "INSERT_ROWS");
});

test("every header has a cell and every cell has a header", async () => {
  const f = fakeSheets();
  await ledger.append(lead());
  // The invariant the bounded range depends on: the row is never wider than the
  // header, or the extra columns form a headerless island and the drift starts.
  assert.equal(f.appends[0].requestBody.values[0].length, ledger.HEADERS.length);
});

test("missing fields become empty strings, never undefined holes", () => {
  const row = ledger.toRow({ "Comment ID": "123" });
  assert.equal(row.length, ledger.HEADERS.length);
  assert.ok(row.every((v) => typeof v === "string"));
  assert.equal(row[ledger.COL.Email], "");
});

test("the email backfill finds the row by its unrounded comment id", async () => {
  const f = fakeSheets();
  await ledger.append(lead());

  const ok = await ledger.update("17925384756201943", { Email: "khalid@gulflotus.om", Status: ledger.STATUS.EMAIL_CAPTURED });
  assert.equal(ok, true);

  const patch = f.batchUpdates.at(-1).requestBody;
  assert.equal(patch.valueInputOption, "RAW");
  assert.equal(patch.data[0].range, `IG_Leads!${ledger.columnLetter(ledger.COL.Email)}2`, "row 2 — row 1 is the header");
  assert.equal(patch.data[0].values[0][0], "khalid@gulflotus.om");
});

test("a sheet outage does not throw — the stdout journal already has the lead", async () => {
  ledger._setClient({
    spreadsheets: {
      values: {
        append: async () => {
          throw new Error("The caller does not have permission");
        },
      },
    },
  });
  assert.equal(await ledger.append(lead()), false, "reports failure, does not explode");
});

test("an update for a comment id that is not in the sheet reports it instead of guessing", async () => {
  const f = fakeSheets();
  await ledger.append(lead());
  assert.equal(await ledger.update("99999999999999999", { Email: "x@y.z" }), false);
});
