/**
 * The Instagram Graph client.
 *
 * Endpoints and API version match the workflows already proven against this
 * account in `IG DM Automation/`, so this is not a guess:
 *   POST /{ig-user-id}/messages   { recipient: { comment_id }, message: { text } }
 *   POST /{comment-id}/replies    { message }
 * Bump IG_API_VERSION when you move; it is one env var, not a code change.
 *
 * NOTHING HERE RETRIES A WRITE. On a timeout we do not know whether Meta
 * accepted the call, and every write in this service is one a duplicate would
 * be visible for: a private reply can only ever be sent once per comment, and a
 * retried public reply posts a second comment under someone's post. A missed DM
 * is recoverable by hand; a double-posted one is not. Failures are logged loudly
 * and recorded against the comment instead.
 */

const { appsecretProof } = require("./signature");

const BASE = process.env.IG_GRAPH_BASE || "https://graph.instagram.com";
const VERSION = process.env.IG_API_VERSION || "v20.0";
const TIMEOUT_MS = Number(process.env.IG_TIMEOUT_MS || 10_000);

/** Meta's code for "this token is dead" — the one worth waking someone up for. */
const TOKEN_ERROR_CODES = new Set([190, 102, 463, 467]);

class IgError extends Error {
  constructor(message, { status, code, subcode, type, fbtrace } = {}) {
    super(message);
    this.name = "IgError";
    this.status = status;
    this.code = code;
    this.subcode = subcode;
    this.type = type;
    this.fbtrace = fbtrace;
    this.tokenProblem = TOKEN_ERROR_CODES.has(Number(code));
  }
}

function create({ token, appSecret, igUserId, fetchImpl = fetch } = {}) {
  const accessToken = () => (typeof token === "function" ? token() : token) || "";
  const me = () => igUserId || "me";

  function url(pathname, params = {}) {
    const t = accessToken();
    const u = new URL(`${BASE}/${VERSION}/${pathname}`.replace(/([^:]\/)\/+/g, "$1"));
    u.searchParams.set("access_token", t);
    // Proves we hold the app secret, so a leaked token alone cannot act as us.
    const proof = appsecretProof(t, appSecret);
    if (proof) u.searchParams.set("appsecret_proof", proof);
    for (const [k, v] of Object.entries(params)) if (v != null) u.searchParams.set(k, String(v));
    return u;
  }

  async function call(method, pathname, { body, params } = {}) {
    if (!accessToken()) throw new IgError("No access token configured", { code: 190 });

    const u = url(pathname, params);
    let res, payload;
    try {
      res = await fetchImpl(u, {
        method,
        headers: body ? { "content-type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
      payload = await res.json().catch(() => ({}));
    } catch (err) {
      throw new IgError(`${method} ${pathname} failed: ${err && err.message}`, { code: "NETWORK" });
    }

    if (!res.ok || payload.error) {
      const e = payload.error || {};
      throw new IgError(e.message || `HTTP ${res.status}`, {
        status: res.status,
        code: e.code,
        subcode: e.error_subcode,
        type: e.type,
        fbtrace: e.fbtrace_id,
      });
    }
    return payload;
  }

  return {
    IgError,

    /** Who this token belongs to. Used on boot to learn our own ID so we can ignore ourselves. */
    whoami: () => call("GET", me(), { params: { fields: "id,username" } }),

    /**
     * The DM. ONE per comment, ever — Meta enforces it — and only within 7 days
     * of the comment. Whatever the follower needs has to be in this one message.
     */
    privateReply: ({ commentId, text }) =>
      call("POST", `${me()}/messages`, {
        body: { recipient: { comment_id: String(commentId) }, message: { text } },
      }),

    /** The visible "Sent! Check your DMs" under the comment. */
    publicReply: ({ commentId, message }) =>
      call("POST", `${String(commentId)}/replies`, { body: { message } }),

    /** A normal DM to a user id. Only legal inside the 24h window after they message us. */
    sendText: ({ igsid, text }) =>
      call("POST", `${me()}/messages`, {
        body: { recipient: { id: String(igsid) }, message: { text } },
      }),

    /** Post metadata, for the CRM row's permalink. Best-effort; never blocks a DM. */
    media: (mediaId) => call("GET", String(mediaId), { params: { fields: "permalink,media_type" } }),

    /**
     * The account's posts and reels, for the admin panel's post picker.
     *
     * Read-only and never on the webhook path — a Graph outage must not be able
     * to stop a DM. `thumbnail_url` is only present on videos, so the panel
     * falls back to `media_url` for images; both are short-lived CDN links,
     * which is fine for a page that is open for minutes.
     */
    mediaList: ({ limit = 50 } = {}) =>
      call("GET", `${me()}/media`, {
        params: { fields: "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp", limit },
      }),

    config: () => ({ base: BASE, version: VERSION, igUserId: igUserId || null, hasToken: Boolean(accessToken()), hasProof: Boolean(appSecret) }),
  };
}

module.exports = { create, IgError, TOKEN_ERROR_CODES };
