#!/usr/bin/env node
/**
 * Create a real Thawani payment link, by hand, for one named customer.
 *
 * WHY THIS EXISTS
 * ---------------
 * There are three ways to take a card, and each covers a gap the others leave:
 *
 *   1. The website checkout (routes/session.js). The proper path — it re-prices
 *      the basket, writes a ledger row, emails a receipt. It is NOT deployed
 *      yet, and until it is, the site takes no cards at all.
 *   2. The Thawani portal's own Payment Links. No code, but capped at OMR 999,
 *      which is under the Smart Website at 950 once anything is added to it,
 *      and far under the Operator Stack.
 *   3. This script. A checkout session, which Thawani caps at OMR 5,000 per
 *      line — enough for anything we sell — addressed to a named buyer whose
 *      details ride along in the metadata so the portal row is recognisable.
 *
 * It calls lib/thawani.js, the same module the checkout uses, so the link it
 * produces is the same kind of object a website order produces.
 *
 * WHAT IT DOES NOT DO
 * -------------------
 * This is a link, not an order. Nothing here writes to the seat ledger, emails
 * an invoice, or fires the GA4 purchase event — all of that lives in the
 * deployed service. A payment taken this way is reconciled BY HAND:
 *   - confirm it with --status (the browser's success screen is not proof),
 *   - raise the invoice yourself with tools/invoice.py (the LGI- series).
 *
 * USAGE
 * -----
 *   node scripts/payment-link.js --list
 *   node scripts/payment-link.js --item website --name "Ahmed Al Rashdi" \
 *        --email ahmed@example.om --phone 91234567
 *   node scripts/payment-link.js --amount 250 --for "Deposit, Operator Stack" \
 *        --name "Ahmed Al Rashdi" --email ahmed@example.om
 *   node scripts/payment-link.js --status checkout_xxx
 *
 *   --uat   practise against uatcheckout.thawani.om, where money is fake
 *   --yes   skip the confirmation prompt (for scripting; think twice)
 *
 * The secret key is read from .env.live (or .env.uat) and is never printed.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const readline = require("readline");

const args = process.argv.slice(2);
const has = (flag) => args.includes(flag);
const opt = (flag) => {
  const i = args.indexOf(flag);
  return i > -1 && args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : null;
};

// ---------------------------------------------------------------- env load --
// Both files are gitignored and Mac-only. Load WITHOUT echoing anything.
const ENV_FILE = path.join(__dirname, "..", has("--uat") ? ".env.uat" : ".env.live");
if (!fs.existsSync(ENV_FILE)) {
  console.error(`Cannot find ${path.basename(ENV_FILE)} next to this script. Run it from the repo on your Mac.`);
  process.exit(1);
}
for (const line of fs.readFileSync(ENV_FILE, "utf8").split("\n")) {
  const m = /^([A-Z_][A-Z0-9_]*)=(.*)$/.exec(line.trim());
  if (m) process.env[m[1]] = m[2];
}

const thawani = require("../lib/thawani");
const CATALOG = require("../catalog.json");

const cfg = thawani.config();
if (!cfg.secret || !cfg.publishable) {
  console.error(`The Thawani keys are not both set in ${path.basename(ENV_FILE)}.`);
  process.exit(1);
}

const SITE = (process.env.SITE_ORIGIN || "https://aiprofitlab.io").replace(/\/+$/, "");
const ORDER_PATH = process.env.ORDER_PATH || "/en/order-v4/";

// Money is integer baisa end to end (1 OMR = 1000 baisa) because Thawani's
// unit_amount rejects decimals. The CLI takes rials because that is what a
// human says out loud, and a 1000x slip is the expensive kind of typo.
const omr = (baisa) => `OMR ${(baisa / 1000).toFixed(3)}`;

function toBaisa(rials) {
  if (!/^\d+(\.\d{1,3})?$/.test(String(rials).trim())) return null;
  // Round rather than truncate: 0.1*1000 is 100.00000000000001 in binary float.
  return Math.round(Number(rials) * 1000);
}

// ------------------------------------------------------------------ --list --
if (has("--list")) {
  console.log(`\n  Catalog (${CATALOG.currency}), from pay.py via catalog.json:\n`);
  for (const i of CATALOG.items) {
    console.log(`    --item ${i.id.padEnd(12)} ${omr(i.price).padStart(14)}   ${i.name}`);
  }
  console.log(`    --item ${CATALOG.bundle.id.padEnd(12)} ${omr(CATALOG.bundle.price).padStart(14)}   ${CATALOG.bundle.name}`);
  console.log(`    --deposit${" ".repeat(10)} ${omr(CATALOG.deposit).padStart(14)}   Build slot deposit`);
  console.log("\n  Or name your own:  --amount 250 --for \"what it is for\"\n");
  process.exit(0);
}

// ----------------------------------------------------------------- --status --
if (has("--status")) {
  const id = opt("--status");
  if (!id) {
    console.error("--status needs a session id.");
    process.exit(1);
  }
  thawani
    .retrieveSession(id)
    .then((s) => {
      // "paid" is decided the way production decides it (routes/session.js),
      // not by trusting the return redirect — a buyer can type the success URL.
      const paid = s.paymentStatus === "paid";
      console.log("\n  session   :", id);
      console.log("  paid      :", paid ? "YES — real money moved" : `no (${s.paymentStatus})`);
      console.log("  reference :", s.reference || "(none)");
      console.log("  invoice   :", s.invoice || "(none)");
      console.log("  amount    :", s.totalAmount != null ? `${s.totalAmount} baisa (${omr(s.totalAmount)})` : "(none)");
      const who = s.metadata || {};
      if (who.customer_name) console.log("  customer  :", who.customer_name, who.customer_email ? `<${who.customer_email}>` : "");
      if (paid) console.log("\n  Now raise the invoice by hand: python3 tools/invoice.py\n");
      else console.log("");
    })
    .catch((err) => {
      console.error("\nFAILED:", err.message, "\n");
      process.exit(1);
    });
  return;
}

// ------------------------------------------------------------- what to sell --
// Either a catalog id (price cannot be mistyped) or a free amount with a label.
let baisa = null;
let label = null;

const itemId = opt("--item");
if (itemId) {
  const row = CATALOG.items.find((i) => i.id === itemId) || (CATALOG.bundle.id === itemId ? CATALOG.bundle : null);
  if (!row) {
    console.error(`Unknown item "${itemId}". Run with --list to see them.`);
    process.exit(1);
  }
  baisa = row.price;
  label = row.name;
} else if (has("--deposit")) {
  baisa = CATALOG.deposit;
  label = "Build slot deposit";
} else if (opt("--amount")) {
  baisa = toBaisa(opt("--amount"));
  if (baisa === null) {
    console.error(`--amount must be rials, up to three decimals. You gave: ${opt("--amount")}`);
    process.exit(1);
  }
  label = opt("--for");
  if (!label) {
    console.error('--amount needs --for "what the customer is paying for" — it is what they see on the page.');
    process.exit(1);
  }
} else {
  console.error(
    "\n  Nothing to charge. Pick one:\n\n" +
      "    --item <id>              a catalog price (run --list to see them)\n" +
      "    --deposit                the build slot deposit\n" +
      '    --amount 250 --for "…"   your own figure\n'
  );
  process.exit(1);
}

// Thawani's real limits, VERIFIED against the API (see lib/thawani.js), not
// guessed. Refusing here gives a sentence; refusing at Thawani gives a 4000.
if (baisa < thawani.AMOUNT_MIN) {
  console.error(`Thawani's floor is ${thawani.AMOUNT_MIN} baisa (${omr(thawani.AMOUNT_MIN)}). You asked for ${omr(baisa)}.`);
  process.exit(1);
}
if (baisa > thawani.SESSION_UNIT_MAX) {
  console.error(`Thawani's ceiling is ${omr(thawani.SESSION_UNIT_MAX)} per line. You asked for ${omr(baisa)}.`);
  process.exit(1);
}

// The name is what the buyer reads on the hosted page, and Thawani truncates it
// at 40 characters — silently. Clamp it here so what we print is what they see.
const productName = label.trim().slice(0, thawani.NAME_MAX);

// ---------------------------------------------------------------- the buyer --
const customer = {
  name: opt("--name"),
  email: opt("--email"),
  phone: opt("--phone"),
  business: opt("--business"),
};
if (!customer.name) {
  console.error('--name is required. A payment with no name attached cannot be reconciled to anybody.');
  process.exit(1);
}

// LNK- deliberately differs from the website's APL- series (routes/session.js
// mintRef) so a hand-made link is never mistaken for a site order in the
// Thawani portal. Same unambiguous alphabet: this gets read down a phone line.
const ALPHABET = "ACDEFGHJKLMNPQRTUVWXY2346789";
const d = new Date();
const p = (n) => String(n).padStart(2, "0");
const stamp = String(d.getFullYear()).slice(2) + p(d.getMonth() + 1) + p(d.getDate());
let tail = "";
for (const b of crypto.randomBytes(4)) tail += ALPHABET[b % ALPHABET.length];
const reference = `LNK-${stamp}-${tail}`;

// Ten keys is the whole metadata budget and an eleventh fails the session
// outright (verified UAT). This uses six.
const metadata = {};
const put = (k, v) => {
  const s = String(v == null ? "" : v).trim().slice(0, thawani.META_MAX_VALUE);
  if (s) metadata[k] = s;
};
put("order_id", reference);
put("customer_name", customer.name);
put("customer_email", customer.email);
put("customer_phone", thawani.phone(customer.phone));
put("customer_business", customer.business);
put("order_amount", `${baisa} baisa`);
put("source", "manual payment link");

// ------------------------------------------------------------- confirm, pay --
(async () => {
  console.log(`\n  gateway   : ${cfg.base}${cfg.live ? "  (LIVE — REAL MONEY)" : "  (uat — no real money)"}`);
  console.log(`  charging  : ${omr(baisa)}`);
  console.log(`  for       : ${productName}${label.length > thawani.NAME_MAX ? "   ← truncated to 40 chars by Thawani" : ""}`);
  console.log(`  customer  : ${customer.name}${customer.email ? `  <${customer.email}>` : ""}`);
  console.log(`  reference : ${reference}`);

  if (!has("--yes")) {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = await new Promise((r) => rl.question(`\n  Create this link? (yes/no) `, r));
    rl.close();
    if (answer.trim().toLowerCase() !== "yes") {
      console.log("\n  Cancelled. Nothing was created.\n");
      return;
    }
  }

  const s = await thawani.createSession({
    reference,
    products: [{ name: productName, unit_amount: baisa, quantity: 1 }],
    successUrl: `${SITE}${ORDER_PATH}?status=success&ref=${encodeURIComponent(reference)}`,
    cancelUrl: `${SITE}${ORDER_PATH}?status=cancel&ref=${encodeURIComponent(reference)}`,
    metadata,
  });

  console.log("\n  Send the customer this link:\n");
  console.log("   ", s.redirectUrl);
  // The --uat flag has to survive into the status command, or the check runs
  // against the LIVE gateway, finds nothing, and reports a healthy UAT session
  // as "session not found".
  const envFlag = cfg.live ? "" : "--uat ";
  console.log("\n  The link is good for 24 hours. Then confirm it actually landed:\n");
  console.log(`    node scripts/payment-link.js ${envFlag}--status ${s.sessionId}`);
  console.log("\n  This link does NOT write a ledger row or email an invoice —");
  console.log("  raise that yourself once --status says paid.\n");
})().catch((err) => {
  console.error("\nFAILED:", err.message);
  console.error("\nNothing was charged. 401 means the keys are wrong; 4003 usually means the");
  console.error("merchant account is not enabled for this operation.\n");
  process.exit(1);
});
