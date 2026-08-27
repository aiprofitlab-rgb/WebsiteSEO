#!/usr/bin/env node
/**
 * Prove against the REAL spreadsheet that a 17-digit Instagram id survives the
 * round trip.
 *
 * The unit test asserts we ask for RAW. Only this can show what Google actually
 * stored, and this failure mode produces no error at all — the id simply reads
 * back as a different number, and the email backfill then never finds its row.
 * Worth thirty seconds after any change to ledger.js.
 *
 *   node --env-file=.env scripts/verify-sheet.js
 *
 * Writes one row to the configured tab and deletes nothing; remove it by hand.
 */

const ledger = require("../lib/ledger");

// 17 significant digits. float64 carries ~15, so USER_ENTERED corrupts this.
const PROBE_COMMENT_ID = "17925384756201943";
const PROBE_USER_ID = "78412345678901234";

async function main() {
  if (!ledger.enabled()) {
    console.error("IG_SHEET_ID is not set — nothing to verify. (That is a valid config; leads go to the logs.)");
    process.exit(2);
  }

  console.log(`sheet tab: ${ledger.TAB}`);
  await ledger.ensureTab();

  const marker = `verify-${Date.now()}`;
  const ok = await ledger.append({
    Timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
    Username: marker,
    "Commenter ID": PROBE_USER_ID,
    "Comment ID": PROBE_COMMENT_ID,
    "Comment text": "ID PRECISION PROBE — safe to delete",
    Rule: "verify",
    Status: "Probe",
  });
  if (!ok) {
    console.error("append failed — check the service account has Editor access to the sheet");
    process.exit(1);
  }

  // Read it back the same way the email backfill does.
  const found = await ledger.update(PROBE_COMMENT_ID, { Notes: "read back OK" });

  console.log("");
  if (found) {
    console.log(`PASS — ${PROBE_COMMENT_ID} was found again, byte for byte.`);
    console.log(`Delete the row marked ${marker} when you are done.`);
    process.exit(0);
  }

  console.error(`FAIL — wrote ${PROBE_COMMENT_ID} and could not find it again.`);
  console.error("That is the USER_ENTERED rounding bug. Check valueInputOption in lib/ledger.js:");
  console.error(`Sheets will have stored ${Number(PROBE_COMMENT_ID)} instead.`);
  process.exit(1);
}

main().catch((err) => {
  console.error("VERIFY CRASHED:", err && err.message);
  process.exit(1);
});
