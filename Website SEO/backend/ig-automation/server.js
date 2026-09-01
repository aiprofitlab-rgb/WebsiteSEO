/**
 * Instagram comment automation.
 *
 * A follower comments a keyword on a post or reel; they get a DM with the link,
 * a public "check your DMs" reply appears under their comment, and the lead is
 * appended to a Google Sheet. The ManyChat behaviour, self-hosted.
 *
 * Shape follows backend/checkout-api/server.js — same rate limiter, same /health
 * that reports live config, same 404 and unhandled-error handlers. CORS is
 * deliberately absent: no browser ever calls this, only Meta.
 *
 * Deploy: see deploy/DEPLOY.md (Hostinger VPS, Caddy, systemd).
 */

const express = require("express");

const ledger = require("./lib/ledger");
const tokens = require("./lib/tokens");
const rulesLib = require("./lib/rules");
const igClient = require("./lib/ig");
const store = require("./lib/store");
const alert = require("./lib/mail");
const handler = require("./lib/handler");
const webhook = require("./webhook");

const app = express();
app.set("trust proxy", true);

// The raw bytes, kept for the HMAC. A re-serialised object would not produce the
// digest Meta signed — key order and unicode escaping both differ.
app.use(
  express.json({
    limit: "256kb", // Meta batches events; 64kb is tight for a busy post
    verify: (req, _res, buf) => {
      req.rawBody = buf;
    },
  })
);

/** Same in-memory throttle as checkout-api. */
const hits = new Map();
function rateLimit({ windowMs, max, bucket }) {
  return (req, res, next) => {
    const key = `${req.ip}:${bucket}`;
    const now = Date.now();
    const seen = (hits.get(key) || []).filter((t) => now - t < windowMs);
    if (seen.length >= max) return res.sendStatus(429);
    seen.push(now);
    hits.set(key, seen);
    if (hits.size > 5000) hits.clear();
    next();
  };
}

const db = store.open();
const rules = rulesLib.load();

/**
 * The loop breaker's ceiling. Not a rate limit on followers — a bound on us.
 * Whatever starts a loop, this is what makes it stop at a dozen replies under one
 * post rather than a hundred, and it is what wakes someone up when it does.
 */
const cap = (raw, fallback) => {
  const n = Number(raw);
  // A typo must not silently disable the guard, and 0 must survive as 0 — it is
  // the mute switch: every keyword comment is dropped and reported.
  return Number.isFinite(n) && n >= 0 ? n : fallback;
};
const limits = {
  perMediaPerHour: cap(process.env.IG_MAX_REPLIES_PER_MEDIA_PER_HOUR, handler.DEFAULT_LIMITS.perMediaPerHour),
  perAccountPerHour: cap(process.env.IG_MAX_REPLIES_PER_HOUR, handler.DEFAULT_LIMITS.perAccountPerHour),
  windowMs: handler.DEFAULT_LIMITS.windowMs,
};

// Learned from the token on boot, so we can recognise and ignore our own
// comments. IG_USER_ID short-circuits the lookup when it is already known.
let selfId = process.env.IG_USER_ID || "";
let selfUsername = "";

const ig = igClient.create({
  token: () => tokens.current(),
  appSecret: process.env.META_APP_SECRET,
  igUserId: process.env.IG_USER_ID || "",
});

const deps = {
  ig,
  store: db,
  ledger,
  rules,
  alert,
  handleEvent: handler.handleEvent,
  limits,
  get selfId() {
    return selfId;
  },
  get selfUsername() {
    return selfUsername;
  },
};

app.get("/health", (req, res) => {
  const cfg = ig.config();
  res.json({
    ok: true,
    service: "ig-automation",
    account: { id: selfId || null, username: selfUsername || null },
    graph: { base: cfg.base, version: cfg.version, token: cfg.hasToken, appsecret_proof: cfg.hasProof },
    token: { daysLeft: tokens.daysLeft(), file: tokens.file() },
    // Fails loudly in the health check rather than at the first real comment.
    webhook: { verifyToken: Boolean(process.env.IG_VERIFY_TOKEN), appSecret: Boolean(process.env.META_APP_SECRET) },
    rules: { count: (rules.rules || []).length, ids: (rules.rules || []).map((r) => r.id) },
    // The loop guards, visible without reading the source. `selfLoop: "config"`
    // means we are recognising our own replies by their text, which works even
    // when the id checks do not.
    loopGuard: { selfId: Boolean(selfId), selfUsername: Boolean(selfUsername), selfLoop: "config", limits },
    ledger: ledger.enabled() ? "sheet" : "logs",
    store: db.stats(),
  });
});

app.use("/ig", rateLimit({ windowMs: 60_000, max: 600, bucket: "webhook" }), webhook.create(deps));

app.use((req, res) => res.status(404).json({ message: "Not found." }));

app.use((err, req, res, next) => {
  console.error("UNHANDLED:", err);
  res.sendStatus(500);
});

const PORT = process.env.PORT || 8090;

/** Ask Meta who this token belongs to, so the self-comment guard has an ID. */
async function resolveSelf() {
  if (selfId) return;
  try {
    const me = await ig.whoami();
    selfId = String(me.id || "");
    selfUsername = me.username || "";
    console.log(`account resolved: @${selfUsername} (${selfId})`);
  } catch (err) {
    // Not fatal, and no longer dangerous. Recognising our own comments does not
    // depend on this lookup: entry.id in the payload is the account the webhook
    // was raised for, and any comment whose text is one of our own publicReply
    // strings is dropped on sight. Set IG_USER_ID anyway — it is one more way to
    // be sure, and it saves this call on every boot.
    console.error("!! COULD NOT RESOLVE OWN IG ID:", err && err.message);
    console.error("!! the loop guards still hold (entry.id + reply-text match); set IG_USER_ID to remove the doubt");
  }
}

if (require.main === module) {
  app.listen(PORT, async () => {
    console.log(`ig-automation listening on ${PORT}`);

    if (!process.env.META_APP_SECRET) console.error("!! META_APP_SECRET is not set — every webhook POST will be rejected");
    if (!process.env.IG_VERIFY_TOKEN) console.error("!! IG_VERIFY_TOKEN is not set — the Meta handshake will fail");

    const ruleProblems = rulesLib.validate(rules);
    if (ruleProblems.length) console.error(`!! ${ruleProblems.length} RULES PROBLEM(S) — see above. A "reply loop" line means the account will answer itself.`);

    tokens.seed();
    const left = tokens.daysLeft();
    if (left != null) console.log(`token: ${left} days left`);
    if (left != null && left < 7) console.error(`!! TOKEN EXPIRES IN ${left} DAYS — check the refresh cron`);

    await resolveSelf();

    try {
      const ready = await ledger.ensureTab();
      console.log(ready ? `ledger tab ready (${ledger.TAB})` : "ledger: no IG_SHEET_ID, leads go to logs");
    } catch (err) {
      // Never crash-loop on a sheet permission problem — /health must still answer.
      console.error("LEDGER BOOTSTRAP FAILED:", err && err.message);
    }

    // Housekeeping. Expired capture states and long-dead dedupe rows.
    setInterval(() => {
      try {
        const swept = db.sweep();
        if (swept.states || swept.handled) console.log(JSON.stringify({ sweep: swept }));
      } catch (err) {
        console.error("SWEEP FAILED:", err && err.message);
      }
    }, 6 * 60 * 60 * 1000).unref();
  });
}

module.exports = { app, deps };
