/**
 * The AI Profit Lab checkout API.
 *
 * Creates Thawani payment sessions for /en/checkout-v4/ and answers
 * /en/order-v4/ when the buyer comes back. The contract it satisfies is
 * docs/payments-api.md; the price table it re-prices from is catalog.json,
 * exported out of tools/v4/pay.py so the page and this service cannot drift.
 *
 * Deploy:
 *   gcloud run deploy checkout-api --source . --region me-central1 \
 *     --project aiprofitlab-offer --allow-unauthenticated
 */

const express = require("express");
const cors = require("cors");

const ledger = require("./lib/ledger");
const thawani = require("./lib/thawani");
const pricing = require("./lib/pricing");
const sessionRoute = require("./routes/session");
const billingRoute = require("./routes/billing");

const app = express();
app.set("trust proxy", true);

// An allowlist, not "*". This endpoint mints payment sessions; an open CORS
// policy invites strangers to mint them from anywhere.
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || "https://aiprofitlab.io,https://www.aiprofitlab.io")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

app.use(
  cors({
    origin(origin, cb) {
      // No origin: curl, health checks, server-to-server. Browsers always send one.
      if (!origin || ALLOWED_ORIGINS.includes(origin)) return cb(null, true);
      return cb(null, false);
    },
  })
);

app.use(express.json({ limit: "64kb" }));

/** Small in-memory throttle, same shape as the storefront API's. */
const hits = new Map();
function rateLimit({ windowMs, max, bucket }) {
  return (req, res, next) => {
    const key = `${req.ip}:${bucket}`;
    const now = Date.now();
    const seen = (hits.get(key) || []).filter((t) => now - t < windowMs);
    if (seen.length >= max) return res.status(429).json({ message: "Too many attempts. Wait a minute and try again." });
    seen.push(now);
    hits.set(key, seen);
    if (hits.size > 5000) hits.clear();
    next();
  };
}

// Not /healthz — Cloud Run's frontend intercepts that path and answers it with
// its own 404 before the request reaches the container.
app.get("/health", (req, res) => {
  const cfg = thawani.config();
  res.json({
    ok: true,
    service: "checkout-api",
    thawani: {
      base: cfg.base,
      env: cfg.live ? "live" : "uat",
      keys: Boolean(cfg.secret && cfg.publishable),
      // The single field to check after a deploy: false here means the checkout
      // is handing every buyer to WhatsApp, whatever the keys say.
      accepting_cards: cfg.enabled,
    },
    ledger: ledger.enabled() ? "sheet" : "logs",
    // Reported because this is the failure that hides. lib/mail.js logs and
    // moves on with no key, and both sends are inside a Promise.allSettled, so
    // a buyer can pay OMR 950 and get silence while every other signal here
    // still says the service is healthy. If this says DISABLED, cards should
    // not be on.
    email: process.env.RESEND_API_KEY ? "armed" : "DISABLED (no RESEND_API_KEY)",
    billing: process.env.CRON_KEY ? "armed" : "disabled (no CRON_KEY)",
    catalog: { items: pricing.CATALOG.items.length },
  });
});

// POST is the expensive one and the one worth abusing; GET is polled by a page
// that is legitimately waiting for a payment to settle.
app.post("/session", rateLimit({ windowMs: 10 * 60_000, max: 10, bucket: "create" }));
app.use("/session", rateLimit({ windowMs: 60_000, max: 120, bucket: "read" }), sessionRoute);

// Woken by Cloud Scheduler, not by a browser. Guarded by CRON_KEY inside the
// router, and never listed in CORS — no page should ever call this.
app.use("/billing", rateLimit({ windowMs: 60_000, max: 20, bucket: "billing" }), billingRoute);

app.use((req, res) => res.status(404).json({ message: "Not found." }));

app.use((err, req, res, next) => {
  console.error("UNHANDLED:", err);
  res.status(500).json({ message: "Something went wrong. Nothing has been charged." });
});

const PORT = process.env.PORT || 8080;

if (require.main === module) {
  app.listen(PORT, async () => {
    const cfg = thawani.config();
    console.log(`checkout-api listening on ${PORT} -> ${cfg.base} (${cfg.live ? "LIVE" : "uat"})`);
    if (!cfg.secret || !cfg.publishable) {
      console.error("!! THAWANI keys are not set — every /session call will fail");
    }
    try {
      const ready = await ledger.ensureTab();
      console.log(ready ? "ledger tab ready" : "ledger: no CHECKOUT_SHEET_ID, orders go to logs");
    } catch (err) {
      // Don't crash-loop on a sheet permission problem — /health should still
      // answer so the revision goes live and the logs are readable.
      console.error("LEDGER BOOTSTRAP FAILED:", err && err.message);
    }
  });
}

module.exports = app;
