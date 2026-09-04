/**
 * The Thawani e-commerce checkout client.
 *
 * Two calls, both server-side only: create a session, and ask what happened to
 * it. The browser never sees the secret key and never posts a card number
 * anywhere — the buyer types the card on Thawani's own hosted page, and we get
 * them back on /en/order-v4/.
 *
 * This is Thawani's "1st Scenario (only payment without tokenization)" from the
 * mini document: create session -> redirect -> retrieve session. No customer
 * object, no saved cards, no payment intents — for an order with nothing
 * monthly in it.
 *
 * CORRECTED 2026-09-03. An earlier version of this comment said card-on-file
 * was outside our merchant application. That has not been true since the
 * application was revised on 2026-08-25: the monthly subscription is now
 * declared in BOTH the E-commerce KYC and the Merchant Application Form, which
 * clause 5.1 requires (Thawani only permits recurring charges it has
 * specifically allowed) and 23.3(l)(ii) names the Application Form for
 * specifically. Thawani's own written answer, 2026-08-24: saved-card recurring
 * works after ONE OTP at save time, and later charges need no customer present.
 *
 * So the card-on-file path below is contractually covered and is meant to be
 * used. What is still unproven is our code against the LIVE gateway — see the
 * comment above createPaymentIntent.
 *
 * Shapes verified against Thawani's Create Session documentation and a working
 * production integration. See docs/payments-api.md §3.
 */

const CREATE_TIMEOUT_MS = 10_000; // the page gives up at 15s; be back before it does
const READ_TIMEOUT_MS = 8_000;

// Thawani truncates a product name at 40 characters. Catalog names are checked
// at build time by pay.check_services(); the composed names below are not, so
// they are clamped here.
const NAME_MAX = 40;

// VERIFIED against uatcheckout.thawani.om on 2026-08-24, not guessed: an
// eleventh key is rejected outright with
//   {"code":4000,"description":"Invalid information",
//    "data":{"error":[{"field":"metadata","message":"Metadata cant have more than 10 items"}]}}
// and the whole session fails, which would cost a real order. Ten is a hard
// ceiling, so the map below is built to be exactly ten and the test suite
// asserts it — the truncation in metadata() is a backstop, not the plan.
//
// No value-length limit is published. 100 characters is our own cap: long
// enough for any business name we have seen, short enough to stay clear of a
// ceiling we have not been told about.
const META_MAX_KEYS = 10;
const META_MAX_VALUE = 100;

// Amount ceilings, VERIFIED against UAT 2026-08-24 by asking the API to refuse.
// Both sit far above anything we sell (the dearest order is the Operator Stack
// at OMR 2,200), which is what finally answers the open question
// in docs/payments-api.md about per-transaction limits.
//
//   checkout session : "The field UnitAmount must be between 1 and 5000000"
//                      ...per PRODUCT LINE, and a 50-baisa session is refused,
//                      so the floor is 100 baisa.
//   payment intent   : "The field Amount must be between 100 and 9999000"
const SESSION_UNIT_MAX = 5_000_000; // OMR 5,000 per line
const AMOUNT_MIN = 100; // OMR 0.100
const INTENT_AMOUNT_MAX = 9_999_000; // OMR 9,999

// A payment intent expires 30 minutes after creation (verified: created_at vs
// expire_at). A subscription charge must therefore be created and confirmed in
// one run, never created now and confirmed by a later job.
const INTENT_TTL_MS = 30 * 60_000;

function env(name, fallback) {
  const v = process.env[name];
  return v === undefined || v === "" ? fallback : v;
}

function config() {
  const base = env("THAWANI_BASE", "https://uatcheckout.thawani.om").replace(/\/+$/, "");
  const secret = env("THAWANI_SECRET_KEY", "");
  const publishable = env("THAWANI_PUBLISHABLE_KEY", "");
  return {
    base,
    secret,
    publishable,
    live: base.includes("//checkout.thawani.om"),
    // The kill switch, mirroring storefront-offer-api's. Card payment is
    // attempted only when this service can actually take one: both keys
    // present, and PAY_ENABLED not explicitly off.
    //
    // It exists so that switching payments off in a hurry is one env var and a
    // restart, rather than deleting a Traefik route or rebuilding the whole
    // site. A refused session is not a dead end — the checkout page turns any
    // non-200 into its offline handover and tells the buyer, truthfully, that
    // nothing was charged.
    enabled: Boolean(secret && publishable) && env("PAY_ENABLED", "1") !== "0",
  };
}

const clamp = (v, max) => String(v == null ? "" : v).trim().slice(0, max);
const name40 = (v) => clamp(v, NAME_MAX);

/**
 * Digits only, no plus, no spaces — the shape Thawani's own example uses
 * ("96891234567"). A leading 00 international prefix becomes nothing, and a
 * bare local 8-digit Omani number gets its country code, because a phone
 * number that cannot be dialled is worse than no phone number in a payment
 * record someone will read back to a buyer.
 */
function phone(raw) {
  let d = String(raw || "").replace(/\D+/g, "");
  if (d.startsWith("00")) d = d.slice(2);
  if (d.length === 8) d = "968" + d;
  return d;
}

/**
 * The customer metadata that rides along with the transaction.
 *
 * This is what makes a Thawani portal row recognisable as an order: without it
 * a payment is an amount and a timestamp, and reconciling it against a WhatsApp
 * conversation is guesswork. `order_id` is the same reference the buyer sees on
 * the checkout, quotes on WhatsApp, and lands on at /en/order-v4/ — one string
 * tying the page, the ledger and the Thawani record together.
 *
 * Ten keys is the whole budget, so the three figures that describe the money
 * share one: what is being taken now, what it is part of, and which published
 * price column produced it. That reads perfectly well in a portal row, and it
 * buys back the two slots that would otherwise have pushed the buyer's CR
 * number and city off the end.
 *
 * Ordered by what a human needs first, because the tail is what gets dropped if
 * the ceiling ever moves down.
 *
 * The buyer's free-text `notes` is deliberately NOT sent. It is unbounded prose
 * typed into a form, it can carry anything, and Thawani is a payment processor,
 * not our CRM — it goes to the ledger, which is where we read it.
 */
function metadata({ reference, customer, quote, items }) {
  const pairs = [
    ["order_id", reference],
    ["customer_name", customer.name],
    ["customer_email", customer.email],
    ["customer_phone", phone(customer.whatsapp)],
    ["customer_business", customer.business],
    ["customer_cr", customer.cr],
    ["customer_city", customer.city],
    ["plan", quote.plan.id],
    ["items", items.join(",")],
    ["order_amount", `${quote.due} of ${quote.total} baisa`],
  ];

  const out = {};
  for (const [k, v] of pairs) {
    const value = clamp(v, META_MAX_VALUE);
    if (!value) continue; // an empty CR or city is absence, not an empty string
    if (Object.keys(out).length >= META_MAX_KEYS) break;
    out[k] = value;
  }
  return out;
}

/**
 * The products array Thawani charges.
 *
 * THE INVARIANT: these lines must sum to exactly what the buyer agreed to pay
 * now. Thawani charges the sum of the products, not any total we declare, so a
 * line-item list that merely *describes* the order would charge the wrong
 * amount. An order paid in full is itemised because the buyer should recognise
 * their own basket on the hosted page; every other plan is paying a slice of a
 * total, and a slice has no itemisation — it gets one honest line.
 *
 * The Growth Desk never appears. It is monthly, checkout takes a single
 * payment, and it is invoiced from go-live — see pay.py.
 */
function lineItems(q, catalog) {
  const out = [];

  if (q.plan.due === "total") {
    if (q.bundled) {
      out.push({ name: name40(catalog.bundle.name), unit_amount: catalog.bundle.price, quantity: 1 });
    } else {
      for (const i of q.items) out.push({ name: name40(i.name), unit_amount: i.price, quantity: 1 });
    }
    if (q.surcharge > 0) {
      out.push({ name: name40(`${q.plan.label} — added`), unit_amount: q.surcharge, quantity: 1 });
    }
  } else if (q.plan.due === "deposit") {
    out.push({ name: name40("Build slot deposit"), unit_amount: q.due, quantity: 1 });
  } else if (q.plan.due === "first") {
    out.push({ name: name40(`First of ${q.plan.split} payments`), unit_amount: q.due, quantity: 1 });
  }

  const sum = out.reduce((n, l) => n + l.unit_amount * l.quantity, 0);
  if (!out.length || sum !== q.due) {
    // Not a validation failure — a bug. Refuse loudly rather than take a
    // number nobody agreed to.
    throw new Error(`line items sum to ${sum}, order is due ${q.due}`);
  }
  for (const l of out) {
    if (!Number.isInteger(l.unit_amount) || l.unit_amount <= 0) {
      throw new Error(`non-integer or empty unit_amount: ${l.name} = ${l.unit_amount}`);
    }
  }
  return out;
}

async function call(method, path, body) {
  const cfg = config();
  if (!cfg.secret) throw new Error("THAWANI_SECRET_KEY is not set");

  const res = await fetch(`${cfg.base}/api/v1${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Thawani-Api-Key": cfg.secret,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: AbortSignal.timeout(method === "POST" ? CREATE_TIMEOUT_MS : READ_TIMEOUT_MS),
  });

  const text = await res.text();
  let payload = null;
  try {
    payload = JSON.parse(text);
  } catch {
    throw new Error(`thawani returned non-JSON (${res.status}): ${text.slice(0, 200)}`);
  }

  // Success is code 2004 on create, 2000 on read. Anything else is a failure
  // carrying its reason in `description` — surface it to the log, never to the
  // buyer, because it is written for us.
  if (!payload.success) {
    const why = payload.description || payload.message || `http ${res.status}`;
    const err = new Error(`thawani ${method} ${path} failed: ${why}`);
    err.thawani = payload;
    throw err;
  }
  return payload;
}

/**
 * Create a checkout session. Returns the URL to send the buyer to.
 *
 * The redirect carries the PUBLISHABLE key, which is meant to be seen; the
 * secret key that authenticated this call must never leave the server.
 */
async function createSession({ reference, products, successUrl, cancelUrl, metadata: meta, customerId, saveCard }) {
  const cfg = config();

  // WATCH OUT: Thawani SILENTLY IGNORES unknown fields — a session posted with
  // `totally_made_up_field_xyz` still returns 2004 (verified UAT). A typo in a
  // field name here does not error, it just quietly does nothing. Both fields
  // below were confirmed real by reading them back off the retrieved session,
  // which is the only way to prove one landed.
  const body = {
    client_reference_id: reference,
    products,
    success_url: successUrl,
    cancel_url: cancelUrl,
    metadata: meta,
  };
  if (customerId) {
    body.customer_id = customerId;
    // Without this the card is not kept, and there is nothing to charge next
    // month. Verified honoured: the retrieved session echoes it back true.
    body.save_card_on_success = Boolean(saveCard);
  }

  const payload = await call("POST", "/checkout/session", body);

  if (payload.code !== 2004 || !payload.data || !payload.data.session_id) {
    const err = new Error(`thawani create session: unexpected code ${payload.code}`);
    err.thawani = payload;
    throw err;
  }

  return {
    sessionId: payload.data.session_id,
    invoice: payload.data.invoice || null,
    redirectUrl: `${cfg.base}/pay/${payload.data.session_id}?key=${cfg.publishable}`,
  };
}

/**
 * What actually happened to a session.
 *
 * The return redirect is NOT proof of payment — a buyer can type the success
 * URL. This is the only thing that decides whether money moved.
 */
async function retrieveSession(sessionId) {
  const payload = await call("GET", `/checkout/session/${encodeURIComponent(sessionId)}`);
  const d = payload.data || {};
  return {
    sessionId: d.session_id || sessionId,
    paymentStatus: d.payment_status || "unpaid",
    reference: d.client_reference_id || null,
    totalAmount: typeof d.total_amount === "number" ? d.total_amount : null,
    invoice: d.invoice || null,
    metadata: d.metadata || {},
  };
}

/* -------------------------------------------------------------------------
 * Card-on-file — Thawani's "2nd Scenario (saved card payment)".
 *
 * This is the only route to charging a customer again without sending them
 * back through a hosted checkout, and therefore the only possible basis for
 * the Growth Desk's monthly fee. Each call below is verified to exist and to
 * accept the shape used here against UAT; what is NOT verified is the last
 * step, because confirming an intent needs a real saved card, and saving a
 * card needs somebody to actually pay on the hosted page. See
 * lib/subscriptions.js for what that unknown means in practice.
 * ---------------------------------------------------------------------- */

/**
 * A Thawani customer, created once per buyer and stored against them forever.
 * `client_customer_id` is our handle — pass the order reference's owner, not a
 * random string, or a second visit creates a second customer and the saved
 * card becomes unreachable.
 */
async function createCustomer(clientCustomerId) {
  const payload = await call("POST", "/customers", { client_customer_id: clamp(clientCustomerId, 100) });
  const id = payload.data && payload.data.id;
  if (!id) {
    const err = new Error("thawani create customer: no id in response");
    err.thawani = payload;
    throw err;
  }
  return { customerId: id, clientCustomerId: payload.data.customer_client_id || clientCustomerId };
}

/**
 * The cards this customer has saved. Returns [] rather than throwing on
 * "Payment method not found" (code 4003) — a customer with no card yet is an
 * ordinary state, not an error, and it is exactly the state a subscription is
 * in between signing up and paying the first invoice.
 */
async function listPaymentMethods(customerId) {
  try {
    const payload = await call("GET", `/payment_methods?customer_id=${encodeURIComponent(customerId)}`);
    const data = payload.data;
    return Array.isArray(data) ? data : data ? [data] : [];
  } catch (err) {
    if (err.thawani && err.thawani.code === 4003) return [];
    throw err;
  }
}

/**
 * Create then confirm an intent against a saved card.
 *
 * VERIFIED: `amount` (integer baisa) and `return_url` are the required fields;
 * `products` is NOT how an intent is priced. A fresh intent comes back
 * `status: "requires_payment_method"` with `next_action: null` and 30 minutes
 * to live.
 *
 * NOT VERIFIED, and the whole question hanging over subscriptions: whether
 * confirming against a saved card completes on its own, or comes back with an
 * OTP url in `next_action` that only the cardholder can finish. Thawani's own
 * mini document says "take the user to OTP URL received on the confirm
 * response", which reads as customer-present every time. The caller is written
 * to handle BOTH, and to never report an unconfirmed charge as money.
 */
async function createPaymentIntent({ amount, returnUrl, reference, paymentMethodId, customerId, metadata: meta }) {
  if (!Number.isInteger(amount) || amount < AMOUNT_MIN || amount > INTENT_AMOUNT_MAX) {
    throw new Error(`intent amount ${amount} is outside Thawani's ${AMOUNT_MIN}-${INTENT_AMOUNT_MAX} baisa range`);
  }
  const payload = await call("POST", "/payment_intents", {
    amount,
    return_url: returnUrl,
    client_reference_id: reference,
    payment_method_id: paymentMethodId,
    customer_id: customerId,
    metadata: meta,
  });
  return payload.data;
}

async function confirmPaymentIntent(intentId) {
  const payload = await call("POST", `/payment_intents/${encodeURIComponent(intentId)}/confirm`, {});
  return payload.data;
}

/**
 * What a confirm response actually means.
 *
 * Deliberately conservative: anything that is not an explicit success is
 * treated as "not money yet". A subscription that wrongly believes it charged
 * is worse than one that asks a human to look.
 */
function readIntent(data) {
  const status = (data && data.status) || "unknown";
  const next = (data && data.next_action) || null;
  const otpUrl = next && (next.url || next.otp_url || next.redirect_url) ? next.url || next.otp_url || next.redirect_url : null;
  return {
    status,
    paid: status === "succeeded",
    needsCustomer: Boolean(otpUrl) || status === "requires_action" || status === "requires_confirmation",
    otpUrl,
    raw: data,
  };
}

module.exports = {
  config,
  metadata,
  lineItems,
  createSession,
  retrieveSession,
  createCustomer,
  listPaymentMethods,
  createPaymentIntent,
  confirmPaymentIntent,
  readIntent,
  phone,
  NAME_MAX,
  META_MAX_KEYS,
  META_MAX_VALUE,
  SESSION_UNIT_MAX,
  AMOUNT_MIN,
  INTENT_AMOUNT_MAX,
  INTENT_TTL_MS,
};
