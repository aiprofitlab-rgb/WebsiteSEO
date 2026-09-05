/**
 * The two calls the checkout page makes. Contract: docs/payments-api.md §2.
 *
 *   POST /session          start a transaction, get a redirect
 *   GET  /session/:id      what happened to it
 *
 * The browser talks only to this service. It never holds a Thawani key and
 * never posts a card number anywhere.
 */

const express = require("express");
const crypto = require("crypto");

const router = express.Router();

const pricing = require("../lib/pricing");
const thawani = require("../lib/thawani");
const ledger = require("../lib/ledger");
const mail = require("../lib/mail");
const subs = require("../lib/subscriptions");
const heard = require("../lib/heard");

const SITE_ORIGIN = (process.env.SITE_ORIGIN || "https://aiprofitlab.io").replace(/\/+$/, "");
const ORDER_PATH = process.env.ORDER_PATH || "/en/order-v4/";

const str = (v, max) => String(v == null ? "" : v).trim().slice(0, max);
const isEmail = (v) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v);

// The page's own alphabet and shape: APL-YYMMDD-XXXX, no 0/O or 1/I, because
// this gets read down a phone line.
const REF_RE = /^APL-\d{6}-[ACDEFGHJKLMNPQRTUVWXY2346789]{4}$/;
const ALPHABET = "ACDEFGHJKLMNPQRTUVWXY2346789";

function mintRef() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  const stamp = String(d.getFullYear()).slice(2) + p(d.getMonth() + 1) + p(d.getDate());
  let tail = "";
  for (const b of crypto.randomBytes(4)) tail += ALPHABET[b % ALPHABET.length];
  return `APL-${stamp}-${tail}`;
}

/**
 * Idempotency, instance-local.
 *
 * A double-click must not mint two payment sessions for one order. This map is
 * the cheap half of that; the durable half is the ledger, which is checked
 * first when a sheet is configured. Cloud Run can hold several instances, so on
 * a cold second instance the ledger is what saves us — and with no ledger, a
 * double-click that lands on two instances can still produce two sessions. Both
 * would be for the same amount and only one can be paid, so the cost is a
 * confusing portal row, not a double charge.
 */
const recent = new Map();
const RECENT_TTL_MS = 30 * 60_000;

function remember(reference, value) {
  recent.set(reference, { ...value, at: Date.now() });
  if (recent.size > 2000) {
    const cutoff = Date.now() - RECENT_TTL_MS;
    for (const [k, v] of recent) if (v.at < cutoff) recent.delete(k);
  }
}

function recall(reference) {
  const hit = recent.get(reference);
  if (!hit) return null;
  if (Date.now() - hit.at > RECENT_TTL_MS) {
    recent.delete(reference);
    return null;
  }
  return hit;
}

// Sessions already announced, so a page polling every few seconds does not
// send Nahid an email every few seconds.
const announced = new Set();

/**
 * What the buyer is told happens next, per payment plan.
 *
 * Written per plan rather than as one generic line because the three plans owe
 * the buyer genuinely different things, and "we'll be in touch" after someone
 * has just paid OMR 2,200 is not an answer. Keyed by plan id; an unknown plan
 * falls back to the honest generic, which is better than throwing inside a
 * receipt for money we have already taken.
 */
const NEXT_STEP = {
  deposit:
    "Your build slot is held and this comes straight off your price. I'll confirm your brief with you, " +
    "and the balance is invoiced once that brief is agreed — never before.",
  full:
    "Nothing further is owed. I'll be in touch to confirm your brief, and the build starts from there. " +
    "Your three Pay-in-full extras — the Arabic content pass, the Google Business Profile fix and a staff " +
    "training session — are included at no charge.",
  three:
    "That's the first of three payments. The second falls due at go-live and the third thirty days after " +
    "that. Both are invoiced when they arrive — nothing is taken from your card automatically.",
};

/**
 * Rebuild what the buyer's receipt needs to say.
 *
 * Prefers the ledger row, because it is the only place the MONTHLY commitment
 * survives: the Thawani metadata carries build items only (`q.items` is the
 * build list), so a receipt built from metadata alone would silently omit the
 * Growth Desk or the Visibility Desk the buyer just signed up for. With no
 * sheet configured, falls back to recomputing from the metadata — which is
 * complete for everything except that one field, and says nothing rather than
 * guessing about it.
 *
 * Never throws. This runs inside a paid branch; money has already moved, and a
 * receipt that fails to build must not take the owner alert down with it.
 */
async function buyerReceipt(reference, meta, amountDisplay) {
  const planId = meta.plan || "";
  const p = pricing.plan(planId);

  let itemNames = [];
  let monthly = [];
  let balanceDisplay = "";

  const row = await ledger.findByRef(reference);
  if (row) {
    itemNames = (row.get("Items") || "").split(" | ").filter(Boolean);
    monthly = (row.get("Monthly") || "").split(" | ").filter(Boolean);
    const due = Number(row.get("Due baisa"));
    const total = Number(row.get("Total baisa"));
    if (Number.isFinite(due) && Number.isFinite(total) && total > due) {
      balanceDisplay = pricing.money(total - due);
    }
  } else {
    // Metadata-only path. `items` is build items by id; monthly is unrecoverable
    // from here, so it stays empty rather than being invented.
    const ids = String(meta.items || "").split(",").map((s) => s.trim()).filter(Boolean);
    itemNames = ids.map((id) => (pricing.item(id) || {}).name).filter(Boolean);
    try {
      const q = pricing.quote(ids, planId);
      if (q.balance > 0) balanceDisplay = pricing.money(q.balance);
    } catch {
      // An unknown plan or item id. The figures above are already right; the
      // balance line is simply left off.
    }
  }

  return {
    reference,
    amountDisplay,
    planLabel: p ? p.label : "",
    itemNames,
    monthly,
    balanceDisplay,
    nextStep: NEXT_STEP[planId] || "I'll be in touch to confirm your brief and what happens from here.",
  };
}

/**
 * A message written for the BUYER. It is rendered on the checkout under the
 * offline handover, so it says what happened to them, never what broke.
 */
const BUYER = {
  invalid: "Some of your details are missing or look wrong. Check them and try again.",
  mismatch:
    "Our prices changed while you were on this page, so we have not taken a payment. " +
    "Refresh to see the current price, or send us the order and we will confirm it by hand.",
  notCard: "This payment plan is invoiced rather than paid by card.",
  nothingDue: "There is nothing to pay today on this plan.",
  gateway: "We could not open the secure payment page just now. Nothing has been charged.",
};

router.post("/", async (req, res) => {
  const body = req.body || {};
  const cfg = thawani.config();

  // ---------------------------------------------------------------- shape --
  const customer = {
    name: str(body.customer && body.customer.name, 120),
    business: str(body.customer && body.customer.business, 160),
    email: str(body.customer && body.customer.email, 160),
    whatsapp: str(body.customer && body.customer.whatsapp, 40),
    cr: str(body.customer && body.customer.cr, 40),
    city: str(body.customer && body.customer.city, 80),
    notes: str(body.customer && body.customer.notes, 2000),
    // Self-reported attribution: an id from the page's own list, plus the free
    // text two of those answers open. Both untrusted, both length-capped, and
    // neither is in the `missing` check below — a buyer on a page cached before
    // this field existed must still be able to pay. See lib/heard.js.
    heardAbout: str(body.customer && body.customer.heardAbout, 40),
    heardDetail: str(body.customer && body.customer.heardDetail, 200),
  };

  // Folded into the note the buyer wrote, because that is the column Nahid
  // reads. Done once, here, so every later writer of Notes — the gateway-failure
  // path below included — carries it without having to know about it.
  customer.notes = heard.prepend(customer.notes, customer.heardAbout, customer.heardDetail);

  const missing = ["name", "business", "email", "whatsapp"].filter((k) => !customer[k]);
  if (missing.length || !isEmail(customer.email)) {
    return res.status(400).json({ message: BUYER.invalid, fields: missing.length ? missing : ["email"] });
  }

  const itemIds = Array.isArray(body.items) ? body.items.map((i) => str(i, 40)) : [];
  const unknown = itemIds.filter((id) => !pricing.item(id));
  if (unknown.length) {
    console.error("SESSION: unknown items", unknown);
    return res.status(400).json({ message: BUYER.invalid });
  }

  // The kill switch, checked before anything is written or priced. Nothing the
  // buyer did caused this, so they get the offline handover and the truth.
  if (!cfg.enabled) {
    console.error("SESSION: refused — payments are switched off (PAY_ENABLED / missing keys)");
    return res.status(503).json({ message: BUYER.gateway });
  }

  const p = pricing.plan(str(body.plan, 40));
  if (!p) {
    console.error("SESSION: unknown plan", body.plan);
    return res.status(400).json({ message: BUYER.invalid });
  }
  if (!p.card) return res.status(400).json({ message: BUYER.notCard });

  // A reference the buyer has already been shown is worth keeping — it is on
  // their screen and in the WhatsApp message they may already have drafted.
  // Anything that isn't one of ours gets replaced rather than trusted.
  const clientRef = str(body.reference, 40).toUpperCase();
  const reference = REF_RE.test(clientRef) ? clientRef : mintRef();

  // ------------------------------------------------------------- re-price --
  // Never charge the browser's number. Recompute from our own table and refuse
  // on disagreement — a mismatch means the deployed page and this service were
  // built from different price tables, which is a bug, not a rounding argument.
  let q;
  try {
    q = pricing.quote(itemIds, p.id);
  } catch (err) {
    console.error("SESSION: quote failed", reference, err.message);
    return res.status(400).json({ message: BUYER.invalid });
  }

  const quotedDue = Number(body.quoted_due);
  const quotedTotal = Number(body.quoted_total);
  if (quotedDue !== q.due || quotedTotal !== q.total) {
    console.error(
      `PRICE MISMATCH ${reference}: page quoted due=${quotedDue} total=${quotedTotal}; ` +
        `server says due=${q.due} total=${q.total}; items=${itemIds.join(",")} plan=${p.id}`
    );
    return res.status(409).json({ message: BUYER.mismatch });
  }

  if (q.due <= 0) return res.status(400).json({ message: BUYER.nothingDue });

  // --------------------------------------------------------- idempotency --
  const seen = recall(reference);
  if (seen) {
    return res.json({ redirect_url: seen.redirectUrl, session_id: seen.sessionId, reference });
  }
  const priorRow = await ledger.findByRef(reference);
  if (priorRow && priorRow.get("Session ID")) {
    const sessionId = priorRow.get("Session ID");
    const redirectUrl = `${cfg.base}/pay/${sessionId}?key=${cfg.publishable}`;
    remember(reference, { sessionId, redirectUrl });
    return res.json({ redirect_url: redirectUrl, session_id: sessionId, reference });
  }

  // ----------------------------------------------------------- the record --
  // Written BEFORE the gateway call, so a failure leaves an order behind
  // instead of a silence.
  const record = {
    Timestamp: new Date().toISOString(),
    Ref: reference,
    Status: ledger.STATUS.CREATED,
    Plan: p.label,
    Items: q.items.map((i) => i.name).join(" | "),
    "Due baisa": q.due,
    "Total baisa": q.total,
    "Due OMR": pricing.omr(q.due),
    "Total OMR": pricing.omr(q.total),
    Name: customer.name,
    Business: customer.business,
    Email: customer.email,
    WhatsApp: customer.whatsapp,
    CR: customer.cr,
    City: customer.city,
    Notes: customer.notes,
    Monthly: q.monthly.map((i) => `${i.name} @ ${pricing.money(i.price)}/mo`).join(" | "),
    "Session ID": "",
    Invoice: "",
    Page: str(body.page, 200),
    "Thawani env": cfg.live ? "live" : "uat",
    "Customer ID": "",
    "Monthly baisa": subs.monthlyTotal(itemIds) || "",
    Subscription: "",
  };
  await ledger.append(record);

  // -------------------------------------------------------- the gateway ---
  try {
    // ------------------------------------------------------------ recurring --
    // An order carrying a monthly item needs the buyer's card kept, or there is
    // nothing to charge next month. That means a Thawani customer, and the
    // customer id must be stored the moment it exists — it is the only handle
    // on the saved card, and losing it means asking the buyer to sign up again.
    //
    // If this fails we deliberately CARRY ON with a plain session: taking the
    // build payment and invoicing the Growth Desk by hand is a worse month for
    // Nahid, but losing the whole order is worse for everyone.
    let customerId = "";
    if (q.monthly.length) {
      try {
        const created = await thawani.createCustomer(`apl-${reference}`);
        customerId = created.customerId;
        await ledger.update(reference, { "Customer ID": customerId, Subscription: subs.STATUS.PENDING_CARD });
      } catch (err) {
        console.error("CUSTOMER CREATE FAILED (continuing without card-on-file):", reference, err && err.message);
      }
    }

    const products = thawani.lineItems(q, pricing.CATALOG);
    const metadata = thawani.metadata({
      reference,
      customer,
      quote: q,
      items: q.items.map((i) => i.id),
    });

    const session = await thawani.createSession({
      reference,
      products,
      // Absolute https URLs, and both carry the reference: the redirect back
      // carries no body, so the reference in the URL is all /en/order-v4/ has.
      successUrl: `${SITE_ORIGIN}${ORDER_PATH}?status=success&ref=${encodeURIComponent(reference)}`,
      cancelUrl: `${SITE_ORIGIN}${ORDER_PATH}?status=cancel&ref=${encodeURIComponent(reference)}`,
      metadata,
      customerId,
      saveCard: Boolean(customerId),
    });

    remember(reference, { sessionId: session.sessionId, redirectUrl: session.redirectUrl });
    await ledger.update(reference, {
      Status: ledger.STATUS.PENDING,
      "Session ID": session.sessionId,
      Invoice: session.invoice || "",
    });

    console.log(
      JSON.stringify({
        event: "session_created",
        ref: reference,
        session: session.sessionId,
        due: q.due,
        plan: p.id,
        metadata_keys: Object.keys(metadata),
        customer_id: customerId || null,
        monthly: q.monthly.length ? subs.monthlyTotal(itemIds) : 0,
      })
    );

    return res.json({
      redirect_url: session.redirectUrl,
      session_id: session.sessionId,
      reference,
    });
  } catch (err) {
    console.error("SESSION CREATE FAILED:", reference, err && err.message, err && err.thawani ? JSON.stringify(err.thawani) : "");
    await ledger.update(reference, { Status: ledger.STATUS.FAILED, Notes: `${customer.notes}\n[gateway] ${err && err.message}`.trim() });
    mail
      .gatewayFailed({ reference, why: (err && err.message) || "unknown", amountDisplay: pricing.money(q.due), customer })
      .catch(() => {});
    // The page turns any non-200 into its offline handover and tells the buyer
    // nothing was charged, which is true.
    return res.status(502).json({ message: BUYER.gateway });
  }
});

/**
 * The status of one session, read by an anonymous browser after the redirect
 * back. FOUR FIELDS ONLY — no customer object, no Thawani payload, no other
 * order. A session id is a bearer token for one order and nothing more.
 */
router.get("/:id", async (req, res) => {
  const sessionId = str(req.params.id, 120);
  res.set("Cache-Control", "no-store");

  try {
    const s = await thawani.retrieveSession(sessionId);
    const reference = s.reference || "";
    const amount = typeof s.totalAmount === "number" ? s.totalAmount : null;

    if (s.paymentStatus === "paid" && !announced.has(sessionId)) {
      announced.add(sessionId);
      if (announced.size > 5000) announced.clear();

      await ledger.update(reference, { Status: ledger.STATUS.PAID });

      // The customer details come back from Thawani's own record of the
      // transaction — this is exactly what the metadata was attached for, and
      // it means the alert is complete even if the ledger is not configured.
      const m = s.metadata || {};

      // The buyer's own receipt. Fired before the owner alert because this is
      // the one somebody is actually waiting for, and wrapped end to end: a
      // receipt that cannot be built must never stop Nahid being told that
      // money landed.
      if (m.customer_email) {
        buyerReceipt(reference || m.order_id || sessionId, m, amount === null ? "" : pricing.money(amount))
          .then((r) => mail.orderConfirmed({ ...r, customer: { email: m.customer_email } }))
          .catch((err) => console.error("BUYER RECEIPT FAILED:", reference, err && err.message));
      } else {
        console.error("BUYER RECEIPT SKIPPED: no customer_email in metadata", reference);
      }

      mail
        .paymentLanded({
          reference: reference || m.order_id || sessionId,
          amountDisplay: amount === null ? "" : pricing.money(amount),
          plan: m.plan || "",
          customer: {
            name: m.customer_name || "",
            business: m.customer_business || "",
            email: m.customer_email || "",
            whatsapp: m.customer_phone || "",
            cr: m.customer_cr || "",
            city: m.customer_city || "",
            notes: "",
          },
          sessionId,
          env: thawani.config().live ? "live" : "uat",
        })
        .catch(() => {});
    } else if (s.paymentStatus === "cancelled" && reference) {
      await ledger.update(reference, { Status: ledger.STATUS.CANCELLED });
    }

    return res.json({
      payment_status: s.paymentStatus,
      reference,
      amount,
      amount_display: amount === null ? "" : pricing.money(amount),
    });
  } catch (err) {
    console.error("SESSION LOOKUP FAILED:", sessionId, err && err.message);
    // Say nothing rather than guess. /en/order-v4/ sits on "confirming your
    // payment" for anything that isn't an explicit paid, which is honest.
    return res.status(502).json({ message: "We could not confirm this payment yet." });
  }
});

module.exports = router;
// Exported for the tests. The receipt is assembled from two different sources
// depending on whether a sheet is configured, and the metadata-only path is the
// one that silently loses the monthly commitment — worth pinning down.
module.exports.buyerReceipt = buyerReceipt;
module.exports.NEXT_STEP = NEXT_STEP;
