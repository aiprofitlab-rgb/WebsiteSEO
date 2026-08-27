/**
 * X-Hub-Signature-256 verification.
 *
 * Nothing else authenticates this endpoint. The callback URL is public, Meta
 * publishes the payload shape, and the only thing separating a real comment
 * event from a stranger POSTing one is this HMAC. So it fails CLOSED: no
 * secret configured means every POST is rejected, rather than every POST being
 * trusted.
 *
 * It needs the exact bytes Meta signed, not a re-serialised object — key order
 * and unicode escaping would both change the digest. server.js captures them
 * via express.json({ verify }).
 */

const crypto = require("node:crypto");

/** The header value Meta would send for this body. Used by tests and the replay script. */
function sign(rawBody, appSecret) {
  const buf = Buffer.isBuffer(rawBody) ? rawBody : Buffer.from(String(rawBody), "utf8");
  return "sha256=" + crypto.createHmac("sha256", appSecret).update(buf).digest("hex");
}

/**
 * True only for a well-formed header whose digest matches.
 * @param {Buffer} rawBody exact bytes as received
 * @param {string} header  value of X-Hub-Signature-256
 * @param {string} appSecret META_APP_SECRET
 */
function verify(rawBody, header, appSecret) {
  if (!appSecret) return false; // fail closed: unconfigured is not "allow"
  if (!header || !rawBody || !rawBody.length) return false;

  const m = /^sha256=([a-f0-9]{64})$/i.exec(String(header).trim());
  if (!m) return false;

  const expected = crypto.createHmac("sha256", appSecret).update(rawBody).digest();
  const got = Buffer.from(m[1], "hex");

  // Lengths are equal by construction (the regex fixes 64 hex chars), but
  // timingSafeEqual throws rather than returns on a mismatch, so check anyway.
  if (got.length !== expected.length) return false;
  return crypto.timingSafeEqual(got, expected);
}

/**
 * appsecret_proof — Meta's second factor on Graph calls. Proves the caller
 * holds the app secret, so a stolen access token alone is not enough to use
 * the API as us.
 */
function appsecretProof(accessToken, appSecret) {
  if (!accessToken || !appSecret) return "";
  return crypto.createHmac("sha256", appSecret).update(accessToken).digest("hex");
}

/** Constant-time compare for the GET handshake's verify token. */
function safeEqual(a, b) {
  const x = Buffer.from(String(a || ""), "utf8");
  const y = Buffer.from(String(b || ""), "utf8");
  if (x.length !== y.length) return false;
  return crypto.timingSafeEqual(x, y);
}

module.exports = { sign, verify, appsecretProof, safeEqual };
