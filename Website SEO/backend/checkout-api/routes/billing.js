/**
 * The monthly billing run.
 *
 * Meant to be woken by Cloud Scheduler once a day, not by a browser. It charges
 * every subscription whose next cycle has come due, and reports exactly what
 * happened to each — including the ones it could not charge, which are the
 * interesting ones.
 *
 * THIS ENDPOINT MOVES MONEY, so it refuses to exist unless CRON_KEY is set.
 * There is no default key and no "open in development" branch: an unprotected
 * billing trigger is one curl away from charging every customer we have.
 */

const express = require("express");
const router = express.Router();

const subs = require("../lib/subscriptions");
const ledger = require("../lib/ledger");
const pricing = require("../lib/pricing");

const CRON_KEY = process.env.CRON_KEY || "";
const SITE_ORIGIN = (process.env.SITE_ORIGIN || "https://aiprofitlab.io").replace(/\/+$/, "");

/** Constant-time-ish compare, so the key cannot be guessed a character at a time. */
function keyMatches(given) {
  const a = Buffer.from(String(given || ""));
  const b = Buffer.from(CRON_KEY);
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

router.use((req, res, next) => {
  if (!CRON_KEY) {
    console.error("BILLING: refused — CRON_KEY is not set");
    return res.status(503).json({ error: "billing_disabled" });
  }
  if (!keyMatches(req.get("X-Cron-Key"))) return res.status(403).json({ error: "forbidden" });
  next();
});

/**
 * Charge everything due.
 *
 * `?dry=1` does the whole selection and reports what WOULD be charged without
 * touching the gateway. Run that first, every time, until this has a few real
 * months behind it.
 */
router.post("/run", async (req, res) => {
  const dry = req.query.dry === "1" || req.body?.dry === true;
  const now = new Date();

  let due;
  try {
    due = await loadDue(now);
  } catch (err) {
    console.error("BILLING: could not load subscriptions:", err && err.message);
    return res.status(500).json({ error: "load_failed" });
  }

  const results = [];
  for (const sub of due) {
    if (dry) {
      results.push({ ref: sub.ref, amount: sub.amount, outcome: "dry_run", would_charge: pricing.money(sub.amount) });
      continue;
    }
    const result = await subs.chargeOnce(sub, { now, returnUrl: `${SITE_ORIGIN}/en/order-v4/?sub=${encodeURIComponent(sub.ref)}` });
    const updated = subs.applyResult(sub, result);
    await ledger.update(sub.ref, {
      Subscription: updated.status,
      Notes: result.outcome === "paid" ? "" : `[billing ${result.at}] ${result.outcome}: ${result.why || ""}`.trim(),
    });
    ledger.log("billing", { Ref: sub.ref, outcome: result.outcome, status: updated.status, why: result.why || "" });
    results.push({ ref: sub.ref, amount: sub.amount, outcome: result.outcome, status: updated.status, why: result.why });
  }

  const tally = results.reduce((acc, r) => ({ ...acc, [r.outcome]: (acc[r.outcome] || 0) + 1 }), {});
  console.log(JSON.stringify({ event: "billing_run", dry, due: due.length, tally }));
  res.json({ ok: true, dry, due: due.length, tally, results });
});

/**
 * Subscriptions currently due, read off the ledger.
 *
 * Without a sheet there is nowhere durable to keep a billing schedule, so this
 * returns nothing rather than inventing one. Recurring billing genuinely needs
 * CHECKOUT_SHEET_ID set — logs are fine for recording an order, and useless as
 * a thing to query next month.
 */
async function loadDue(now) {
  if (!ledger.enabled()) {
    console.warn("BILLING: no CHECKOUT_SHEET_ID — there is no durable schedule to read");
    return [];
  }
  const rows = await ledger.allRows();
  return rows
    .map((r) => ({
      ref: r.get("Ref"),
      customerId: r.get("Customer ID"),
      amount: Number(r.get("Monthly baisa")) || 0,
      status: r.get("Subscription"),
      name: r.get("Name"),
      email: r.get("Email"),
      business: r.get("Business"),
      nextChargeAt: r.get("Next charge"),
      anchorDay: Number(r.get("Anchor day")) || undefined,
      cycles: Number(r.get("Cycles")) || 0,
      failures: Number(r.get("Failures")) || 0,
    }))
    .filter((s) => s.amount > 0 && s.customerId && subs.isDue(s, now));
}

module.exports = router;
