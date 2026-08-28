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

/**
 * Meta's `signed_request` — the format used by the deauthorize and data-deletion
 * callbacks. It is NOT the X-Hub-Signature-256 shape above: the signature travels
 * inside a form field rather than a header, and it covers the base64url payload
 * STRING, not the decoded JSON. Signing the decoded object would never match.
 *
 * @returns {object|null} the payload, or null if absent, malformed or unsigned
 */
function parseSignedRequest(signedRequest, appSecret) {
  if (!appSecret) return null; // fail closed, exactly as verify() does
  const parts = String(signedRequest || "").split(".");
  if (parts.length !== 2) return null;

  const [encodedSig, encodedPayload] = parts;
  if (!encodedSig || !encodedPayload) return null;

  let got;
  try {
    got = Buffer.from(encodedSig, "base64url");
  } catch {
    return null;
  }

  const expected = crypto.createHmac("sha256", appSecret).update(encodedPayload).digest();
  if (got.length !== expected.length) return null;
  if (!crypto.timingSafeEqual(got, expected)) return null;

  try {
    const payload = JSON.parse(Buffer.from(encodedPayload, "base64url").toString("utf8"));
    // Meta has only ever sent HMAC-SHA256 here. Anything else is either a new
    // algorithm we have not reviewed or someone probing; both mean "refuse".
    if (payload && payload.algorithm && String(payload.algorithm).toUpperCase() !== "HMAC-SHA256") return null;
    return payload;
  } catch {
    return null;
  }
}

/** The inverse, for tests and for anyone reproducing a callback by hand. */
function makeSignedRequest(payload, appSecret) {
  const encodedPayload = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  const sig = crypto.createHmac("sha256", appSecret).update(encodedPayload).digest().toString("base64url");
  return `${sig}.${encodedPayload}`;
}

/** Constant-time compare for the GET handshake's verify token. */
function safeEqual(a, b) {
  const x = Buffer.from(String(a || ""), "utf8");
  const y = Buffer.from(String(b || ""), "utf8");
  if (x.length !== y.length) return false;
  return crypto.timingSafeEqual(x, y);
}

module.exports = { sign, verify, appsecretProof, safeEqual, parseSignedRequest, makeSignedRequest };
