#!/usr/bin/env node
/**
 * Create ONE real Thawani payment link for a trivial amount, so the live
 * merchant account can be proven with real money without anybody paying 249.
 *
 * WHY THIS EXISTS
 * ---------------
 * The checkout re-prices every order from its own catalogue and refuses any
 * mismatch (routes/session.js, "never charge the browser's number"). That is
 * correct, and it means there is no way to push a small amount through the
 * website. So the small-amount test has to be made deliberately, here, and
 * OUTSIDE the ordering flow.
 *
 * It calls lib/thawani.js — the same module the checkout uses — so a pass here
 * is evidence about production code, not about a script that resembles it.
 *
 * WHAT A PASS PROVES, AND WHAT IT DOES NOT
 * ----------------------------------------
 * Proves : the live keys work, Thawani accepts a session, the hosted page
 *          renders, a real card is charged, the money reaches the merchant
 *          account, and retrieving the session afterwards reports it paid.
 * Does NOT prove : anything about the website, the order sheet, the receipt
 *          email, or the seat ledger. Those are exercised only by a real
 *          order through the site. Test them on UAT (.env.uat) where money
 *          is fake and the flow is complete.
 *
 * The two tests are complementary and neither replaces the other.
 *
 *   node scripts/live-test-payment.js            # 100 baisa = OMR 0.100
 *   node scripts/live-test-payment.js 250        # 250 baisa = OMR 0.250
 *   node scripts/live-test-payment.js 100 --status <session_id>
 *
 * The secret key is read from .env.live and is never printed.
 */
"use strict";

const fs = require("fs");
const path = require("path");

// ---------------------------------------------------------------- env load --
// .env.live is gitignored and Mac-only. Load it WITHOUT echoing anything.
const ENV_FILE = path.join(__dirname, "..", ".env.live");
if (!fs.existsSync(ENV_FILE)) {
  console.error("Cannot find .env.live next to this script. Run it from the repo on your Mac.");
  process.exit(1);
}
for (const line of fs.readFileSync(ENV_FILE, "utf8").split("\n")) {
  const m = /^([A-Z_][A-Z0-9_]*)=(.*)$/.exec(line.trim());
  if (m) process.env[m[1]] = m[2];
}

const thawani = require("../lib/thawani");

const cfg = thawani.config();
if (!cfg.secret || !cfg.publishable) {
  console.error("The Thawani keys are not both set in .env.live.");
  process.exit(1);
}

// ------------------------------------------------------------------- guard --
// A typo here is a real charge, so refuse anything that is not obviously small.
const CEILING = 1000; // 1 OMR
const baisa = Number(process.argv[2] || 100);
if (!Number.isInteger(baisa) || baisa <= 0 || baisa > CEILING) {
  console.error(
    `Amount must be a whole number of baisa between 1 and ${CEILING} (OMR ${CEILING / 1000}).\n` +
      `You asked for: ${process.argv[2]}\n` +
      `This script is deliberately incapable of creating a large charge.`
  );
  process.exit(1);
}

const statusFlag = process.argv.indexOf("--status");

(async () => {
  if (statusFlag > -1) {
    const id = process.argv[statusFlag + 1];
    if (!id) {
      console.error("--status needs a session id.");
      process.exit(1);
    }
    const s = await thawani.retrieveSession(id);
    // "paid" is decided the same way production decides it (routes/session.js:378),
    // not by trusting the return redirect — a buyer can simply type the success URL.
    const paid = s.paymentStatus === "paid";
    console.log("\nsession   :", id);
    console.log("paid      :", paid ? "YES — real money moved" : `no (${s.paymentStatus})`);
    console.log("reference :", s.reference || "(none)");
    console.log("invoice   :", s.invoice || "(none)");
    console.log("amount    :", s.totalAmount != null ? `${s.totalAmount} baisa (OMR ${s.totalAmount / 1000})` : "(none)");
    return;
  }

  const reference = `LIVETEST-${Date.now().toString(36).toUpperCase()}`;

  console.log(`\ngateway   : ${cfg.base}${cfg.live ? "  (LIVE — REAL MONEY)" : "  (uat — no real money)"}`);
  console.log(`amount    : ${baisa} baisa  =  OMR ${(baisa / 1000).toFixed(3)}`);
  console.log(`reference : ${reference}`);

  const s = await thawani.createSession({
    reference,
    products: [{ name: "Live gateway test", unit_amount: baisa, quantity: 1 }],
    successUrl: "https://aiprofitlab.io/en/pay/?livetest=paid",
    cancelUrl: "https://aiprofitlab.io/en/pay/?livetest=cancelled",
    metadata: { purpose: "live gateway verification", note: "not a customer order" },
  });

  console.log("\n  Pay it here:\n");
  console.log("   ", s.redirectUrl);
  console.log("\n  Then check it actually landed:\n");
  console.log(`    node scripts/live-test-payment.js 100 --status ${s.sessionId}`);
  console.log("\n  Refund it from the Thawani merchant portal when you are done.\n");
})().catch((err) => {
  console.error("\nFAILED:", err.message);
  console.error("\nNothing was charged. If this says 401 the keys are wrong; 4003 usually means");
  console.error("the merchant account is not enabled for this operation.\n");
  process.exit(1);
});
