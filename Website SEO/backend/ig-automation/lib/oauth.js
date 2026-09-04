/**
 * Instagram Business Login — the consent screen, and what happens after it.
 *
 * WHY THIS EXISTS AT ALL. Nothing in the running service needs it: the token
 * arrives from the App Dashboard's generator and is kept alive by
 * ig-token-refresh.timer, which is a better arrangement for a single-account
 * automation than an interactive login. This module exists because App Review
 * asks to SEE the consent screen — a submission whose screencast starts with an
 * already-connected account is rejected — and because "confirm that your app can
 * be loaded and tested externally" is answered best by a URL a reviewer in
 * another country can open and complete themselves.
 *
 * THE FLOW IS READ-ONLY. It exchanges the code, asks Meta who it belongs to,
 * renders the answer, and throws the token away. It is deliberately NOT a way to
 * install a token, and that is the most important decision in this file:
 *
 *   The callback URL is public, and a Meta reviewer WILL complete this flow with
 *   their own Instagram account — that is the entire point of handing it to
 *   them. If completing it wrote token.json, the reviewer's login would replace
 *   the live token and the automation would start answering comments as them,
 *   mid-review. Every other write in this service is guarded by an HMAC Meta
 *   signs; this one cannot be, because the person arriving is a stranger by
 *   design. So it stores nothing. To rotate the real token, write token.json.
 *
 * The three calls, in the order Meta requires them:
 *   1. GET  instagram.com/oauth/authorize        -> the consent screen, ?code=
 *   2. POST api.instagram.com/oauth/access_token -> a 1-hour token
 *   3. GET  graph.instagram.com/access_token     -> the 60-day one
 * Step 3 is not optional for a truthful demo: the short-lived token cannot be
 * refreshed, so a video that stops at step 2 shows a login that would be dead
 * within the hour.
 */

const crypto = require("node:crypto");

const igClient = require("./ig");

const AUTHORIZE = "https://www.instagram.com/oauth/authorize";
const TOKEN = "https://api.instagram.com/oauth/access_token";
const GRAPH = process.env.IG_GRAPH_BASE || "https://graph.instagram.com";
const TIMEOUT_MS = Number(process.env.IG_TIMEOUT_MS || 10_000);

/**
 * Exactly the three permissions the App Review submission asks for, in the
 * order they are listed there. This array is the only place they are written
 * down, so the consent screen in the screencast cannot drift from the request
 * the reviewer is reading — a mismatch between the two is a rejection.
 */
const SCOPES = ["instagram_business_basic", "instagram_business_manage_comments", "instagram_business_manage_messages"];

/**
 * Instagram Login has its own app id and secret, shown under Instagram -> API
 * setup with Instagram business login. For most apps the secret is the same
 * value already in META_APP_SECRET (it is what signs the webhook payloads), so
 * that is the fallback — but they are separate fields in the dashboard, and an
 * app configured with both gets a 400 on the token exchange if we guess. Hence
 * an override that costs nothing until it is needed.
 */
const appId = () => process.env.IG_APP_ID || "";
const appSecret = () => process.env.IG_APP_SECRET || process.env.META_APP_SECRET || "";

/**
 * Must match a URI registered in the dashboard BYTE FOR BYTE, including the
 * trailing slash it does not have — Meta compares strings, not URLs. It is also
 * sent again at step 2, where a mismatch with step 1 is the other 400.
 */
const redirectUri = () =>
  process.env.IG_OAUTH_REDIRECT_URI ||
  `${String(process.env.IG_PUBLIC_BASE || "https://hooks.aiprofitlab.io").replace(/\/+$/, "")}/ig/oauth/callback`;

/** Unconfigured means the routes are not mounted, the same way the panel works. */
const configured = () => Boolean(appId() && appSecret());

/* ---------------------------------------------------------------------------
 * state
 * ------------------------------------------------------------------------- */

/**
 * A signed nonce, round-tripped through Instagram and back.
 *
 * With nothing persisted there is no CSRF to speak of — the worst a forged
 * callback achieves is rendering a page about somebody else's account — so this
 * is not load-bearing. It is here because `state` is checked by App Review, and
 * because a callback that arrives without one is worth a line in the journal.
 * Keyed off the app secret so there is no fourth secret to lose.
 */
function signState(now = Date.now()) {
  const payload = Buffer.from(JSON.stringify({ n: crypto.randomBytes(8).toString("hex"), t: now }), "utf8").toString("base64url");
  const sig = crypto.createHmac("sha256", appSecret()).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}

/** @returns {boolean} true only for a signature we made, less than an hour ago. */
function checkState(state, now = Date.now()) {
  const [payload, sig] = String(state || "").split(".");
  if (!payload || !sig) return false;

  const expected = crypto.createHmac("sha256", appSecret()).update(payload).digest();
  let got;
  try {
    got = Buffer.from(sig, "base64url");
  } catch {
    return false;
  }
  if (got.length !== expected.length || !crypto.timingSafeEqual(got, expected)) return false;

  try {
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return Number.isFinite(claims.t) && now - claims.t < 3600_000;
  } catch {
    return false;
  }
}

/* ---------------------------------------------------------------------------
 * The three calls
 * ------------------------------------------------------------------------- */

/** Step 1: where to send the browser. */
function authorizeUrl({ state = signState() } = {}) {
  const u = new URL(AUTHORIZE);
  u.searchParams.set("client_id", appId());
  u.searchParams.set("redirect_uri", redirectUri());
  u.searchParams.set("response_type", "code");
  // Comma-separated, not space-separated. Instagram is the odd one out here and
  // a space-separated list is silently treated as one unknown scope.
  u.searchParams.set("scope", SCOPES.join(","));
  if (state) u.searchParams.set("state", state);
  return u.toString();
}

class OAuthError extends Error {
  constructor(message, { step, status, code } = {}) {
    super(message);
    this.name = "OAuthError";
    this.step = step;
    this.status = status;
    this.code = code;
  }
}

async function json(res) {
  return res.json().catch(() => ({}));
}

/** Meta's error shapes differ by endpoint; this reads all three of them. */
function errorMessage(body, status) {
  if (!body) return `HTTP ${status}`;
  if (body.error && typeof body.error === "object") return body.error.message || `HTTP ${status}`;
  // api.instagram.com uses flat fields rather than a nested error object.
  return body.error_message || body.error_description || body.error || `HTTP ${status}`;
}

/**
 * Step 2: the authorization code becomes a token that lives one hour.
 *
 * Instagram redirects to `…?code=AQB…#_`. The fragment never reaches the
 * server, but it does reach anyone who copies the URL out of the address bar to
 * retry by hand, and a code with `#_` glued to it fails with an error that says
 * nothing about why. Stripped here so that path works too.
 */
async function exchangeCode(code, { fetchImpl = fetch } = {}) {
  const body = new URLSearchParams({
    client_id: appId(),
    client_secret: appSecret(),
    grant_type: "authorization_code",
    redirect_uri: redirectUri(),
    code: String(code || "").replace(/#_$/, ""),
  });

  let res, payload;
  try {
    res = await fetchImpl(TOKEN, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    payload = await json(res);
  } catch (err) {
    throw new OAuthError(`Token exchange failed: ${err && err.message}`, { step: "exchange", code: "NETWORK" });
  }

  // Two shapes in the wild: the current one wraps a single result in `data`,
  // the older one is flat. Reading both means a Graph version bump does not
  // turn into a blank success page.
  const first = Array.isArray(payload.data) && payload.data.length ? payload.data[0] : payload;
  if (!res.ok || !first || !first.access_token) {
    throw new OAuthError(errorMessage(payload, res.status), { step: "exchange", status: res.status });
  }

  return {
    accessToken: first.access_token,
    userId: first.user_id != null ? String(first.user_id) : "",
    // What the person actually ticked, which can be fewer than we asked for.
    permissions: String(first.permissions || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean),
  };
}

/** Step 3: one hour becomes sixty days. */
async function longLived(shortToken, { fetchImpl = fetch } = {}) {
  const u = new URL(`${GRAPH}/access_token`);
  u.searchParams.set("grant_type", "ig_exchange_token");
  u.searchParams.set("client_secret", appSecret());
  u.searchParams.set("access_token", shortToken);

  let res, payload;
  try {
    res = await fetchImpl(u, { method: "GET", signal: AbortSignal.timeout(TIMEOUT_MS) });
    payload = await json(res);
  } catch (err) {
    throw new OAuthError(`Long-lived exchange failed: ${err && err.message}`, { step: "long-lived", code: "NETWORK" });
  }
  if (!res.ok || !payload.access_token) {
    throw new OAuthError(errorMessage(payload, res.status), { step: "long-lived", status: res.status });
  }
  return { accessToken: payload.access_token, expiresIn: Number(payload.expires_in) || 0 };
}

/**
 * The whole flow, as one call: code in, a description of the connected account
 * out. The token is used once to ask `me?fields=id,username` and is not part of
 * the return value — nothing downstream should be able to store it by accident.
 */
async function connect(code, { fetchImpl = fetch } = {}) {
  const short = await exchangeCode(code, { fetchImpl });
  const long = await longLived(short.accessToken, { fetchImpl });

  // The same client the service uses, pointed at the new token, so the proof
  // and error handling are the ones already proven against this account.
  const ig = igClient.create({ token: long.accessToken, appSecret: appSecret(), fetchImpl });

  let account = { id: short.userId, username: "" };
  try {
    const me = await ig.whoami();
    account = { id: String(me.id || short.userId || ""), username: me.username || "" };
  } catch (err) {
    // A username is decoration; a working token is the claim being made. Losing
    // the lookup should not turn a successful login into an error page.
    console.error("OAUTH WHOAMI FAILED:", err && err.message);
  }

  return {
    account,
    // Granted, not requested. If someone unticks a permission on the consent
    // screen this is where it shows, which is exactly what makes it worth
    // putting on the page.
    permissions: short.permissions.length ? short.permissions : SCOPES,
    expiresInDays: long.expiresIn ? Math.round(long.expiresIn / 86400) : null,
    /** Whether this is the account the service is actually configured to run as. */
    isConfiguredAccount: Boolean(process.env.IG_USER_ID) && String(process.env.IG_USER_ID) === account.id,
  };
}

module.exports = {
  SCOPES,
  OAuthError,
  configured,
  appId,
  redirectUri,
  authorizeUrl,
  signState,
  checkState,
  exchangeCode,
  longLived,
  connect,
};
