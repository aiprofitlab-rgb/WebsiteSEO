/**
 * Instagram comment automation.
 *
 * A follower comments a keyword on a post or reel; they get a DM with the link,
 * a public "check your DMs" reply appears under their comment, and the lead is
 * appended to a Google Sheet. The ManyChat behaviour, self-hosted.
 *
 * Anything the keywords do NOT want — a comment matching nothing, a DM that is
 * not the email address the capture flow asked for — falls through to the AI
 * fallback, which answers comments in public and DMs in private. Keywords always
 * win; the fallback is strictly the second half. It turns itself off completely
 * without an OPENAI_API_KEY, and ai.json is where its persona and caps live.
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
const rulesStore = require("./lib/rulesStore");
const aiConfig = require("./lib/aiConfig");
const aiClient = require("./lib/ai");
const igClient = require("./lib/ig");
const store = require("./lib/store");
const files = require("./lib/files");
const auth = require("./lib/auth");
const oauth = require("./lib/oauth");
const alert = require("./lib/mail");
const handler = require("./lib/handler");
const webhook = require("./webhook");
const admin = require("./admin/router");

const app = express();
app.set("trust proxy", true);

// The raw bytes, kept for the HMAC. A re-serialised object would not produce the
// digest Meta signed — key order and unicode escaping both differ.
const parseWebhookJson = express.json({
  limit: "256kb", // Meta batches events; 64kb is tight for a busy post
  verify: (req, _res, buf) => {
    req.rawBody = buf;
  },
});

// Everything except the panel. A body parser is not reusable across these two:
// the first one to run claims the body, so a global parser here would silently
// impose Meta's 256kb limit on a 25MB file upload and hand /admin's routes a
// pre-parsed body whose own limits could never apply. The panel's routes each
// declare their own parser instead.
app.use((req, res, next) => (req.path.startsWith("/admin") ? next() : parseWebhookJson(req, res, next)));

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

// Copy the repo's rules.json into the writable location the first time only.
// After that the panel owns it, and a deploy must never roll a live campaign
// back to whatever is in git. See lib/rulesStore.js.
rulesStore.seed();
aiConfig.seed();

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

/**
 * The fallback brain. Constructed unconditionally — it reports itself as not
 * configured when there is no key, and handler.js checks that before every use.
 * Building it anyway keeps the wiring in one shape instead of two.
 */
const ai = aiClient.create({ apiKey: () => process.env.OPENAI_API_KEY });

const deps = {
  ig,
  ai,
  store: db,
  ledger,
  files,
  tokens,
  alert,
  handleEvent: handler.handleEvent,
  limits,
  /**
   * Read through the store, never captured once at boot. This is what makes a
   * save in the admin panel take effect on the very next comment instead of on
   * the next `systemctl restart` — and it picks up a rules file edited by hand
   * over SSH the same way, since the store re-stats before it re-parses.
   */
  get rules() {
    return rulesStore.current();
  },
  /**
   * Read through on every event, for the same reason `rules` is: editing
   * /var/lib/ig-automation/ai.json over SSH should change the next reply, not
   * wait for a restart. aiConfig re-stats before it re-parses.
   */
  get aiConfig() {
    return aiConfig.current();
  },
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
    rules: {
      count: (deps.rules.rules || []).length,
      ids: (deps.rules.rules || []).map((r) => r.id),
      file: rulesStore.file(),
    },
    admin: { configured: auth.configured(), files: files.list().length },
    // The fallback, at a glance. `key` false is the single most likely reason
    // for "the AI stopped answering", and it is invisible everywhere else.
    ai: (() => {
      const c = deps.aiConfig;
      return {
        key: ai.configured(),
        enabled: Boolean(c.enabled),
        comments: Boolean(c.enabled && c.comments.enabled),
        dms: Boolean(c.enabled && c.dms.enabled),
        model: c.model,
        caps: { comments: c.comments, dms: c.dms },
        file: aiConfig.file(),
      };
    })(),
    // The redirect URI is here because it must match the dashboard byte for
    // byte, and reading it back off the running service is the only way to be
    // sure IG_PUBLIC_BASE did not quietly make it something else.
    oauth: oauth.configured()
      ? { configured: true, redirectUri: oauth.redirectUri(), scopes: oauth.SCOPES }
      : { configured: false },
    // The loop guards, visible without reading the source. `selfLoop: "config"`
    // means we are recognising our own replies by their text, which works even
    // when the id checks do not.
    loopGuard: { selfId: Boolean(selfId), selfUsername: Boolean(selfUsername), selfLoop: "config", limits },
    ledger: ledger.enabled() ? "sheet" : "logs",
    store: db.stats(),
  });
});

/**
 * The OAuth routes live under /ig but must not share the webhook's allowance.
 * 600/min is sized for Meta batching comment events at us; a login endpoint that
 * makes three upstream calls per request is a different shape of thing, and one
 * person signing in needs two. Registered before the webhook router so it runs
 * first, and scoped to the path so it cannot throttle a real event.
 */
app.use("/ig/oauth", rateLimit({ windowMs: 60_000, max: 30, bucket: "oauth" }));

app.use("/ig", rateLimit({ windowMs: 60_000, max: 600, bucket: "webhook" }), webhook.create(deps));

/**
 * The public download for an uploaded file.
 *
 * This URL is the one thing in the service a stranger is MEANT to reach: it is
 * what the DM links to. So it is unauthenticated, and everything that makes
 * that safe is upstream — the id is 16 random bytes, the directory is never
 * listed, and lib/files.js only ever accepts passive file types, because this
 * is a subdomain of the brand and an uploaded .html would be a same-origin
 * script wearing it.
 *
 * The filename in the path is cosmetic; only the id is looked up. That way a
 * renamed file keeps working and a crafted path cannot escape the directory.
 */
app.get("/f/:id/:name?", rateLimit({ windowMs: 60_000, max: 240, bucket: "files" }), (req, res) => {
  const hit = files.find(req.params.id);
  if (!hit) return res.status(404).type("text/plain").send("Not found.");
  res.setHeader("Content-Type", hit.mime);
  res.setHeader("X-Content-Type-Options", "nosniff");
  const type = files.TYPES[hit.ext];
  res.setHeader(
    "Content-Disposition",
    `${type && type.inline ? "inline" : "attachment"}; filename="${hit.name.replace(/"/g, "")}"`
  );
  // The id is content-addressed by construction — a new upload is a new id — so
  // this can be cached hard. A file that changes gets a new URL and the rule
  // that points at it is re-saved.
  res.setHeader("Cache-Control", "public, max-age=86400");
  res.sendFile(hit.path);
});

/**
 * The admin panel.
 *
 * Not mounted at all when no password is configured. An unconfigured admin
 * surface on a public hostname is worse than a missing feature, so the failure
 * mode is 404 rather than "open".
 */
if (auth.configured()) {
  app.use("/admin", rateLimit({ windowMs: 60_000, max: 300, bucket: "admin" }), admin.create(deps));
  app.use("/admin", express.static(require("node:path").join(__dirname, "admin", "public"), { index: "index.html" }));
} else {
  console.warn("!! admin panel DISABLED — set IG_ADMIN_PASSWORD_HASH (scripts/set-admin-password.js) to enable it");
}

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

    if (process.env.IG_ADMIN_PASSWORD && !process.env.IG_ADMIN_PASSWORD_HASH) {
      console.warn("!! IG_ADMIN_PASSWORD is a plaintext password in the environment — fine locally, wrong on the VPS.");
      console.warn("!! Run scripts/set-admin-password.js and use IG_ADMIN_PASSWORD_HASH instead.");
    }
    if (!process.env.META_APP_SECRET) console.error("!! META_APP_SECRET is not set — every webhook POST will be rejected");
    if (!process.env.IG_VERIFY_TOKEN) console.error("!! IG_VERIFY_TOKEN is not set — the Meta handshake will fail");

    const ruleProblems = rulesLib.validate(deps.rules);
    if (ruleProblems.length) console.error(`!! ${ruleProblems.length} RULES PROBLEM(S) — see above. A "reply loop" line means the account will answer itself.`);

    console.log(`rules: ${rulesStore.file()}`);

    // Said out loud on every boot, because the two ways this silently does
    // nothing — no key, or `enabled: false` in the config — look identical from
    // the outside and are both one line to fix.
    const aic = deps.aiConfig;
    if (!ai.configured()) {
      console.warn("!! AI fallback OFF — no OPENAI_API_KEY. Keyword rules are unaffected.");
    } else if (!aic.enabled) {
      console.warn(`!! AI fallback OFF — "enabled": false in ${aiConfig.file()}`);
    } else {
      console.log(
        `ai fallback: ${aic.model} · comments ${aic.comments.enabled ? `on (max ${aic.comments.maxPerMediaPerHour}/post/h, ${aic.comments.maxPerHour}/h)` : "off"} · dms ${aic.dms.enabled ? `on (max ${aic.dms.maxPerHour}/h)` : "off"} · ${aiConfig.file()}`
      );
    }
    console.log(`uploads: ${files.dir()} (public base ${files.publicBase()})`);

    // Printed rather than left to be looked up: this exact string has to be in
    // the dashboard's OAuth redirect list, and a mismatch is a 400 at the last
    // step of the flow with nothing in our own logs to explain it.
    if (oauth.configured()) console.log(`oauth: redirect_uri ${oauth.redirectUri()}`);
    else console.warn("!! Instagram Business Login DISABLED — set IG_APP_ID (and IG_APP_SECRET) to enable /ig/oauth/start");

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
