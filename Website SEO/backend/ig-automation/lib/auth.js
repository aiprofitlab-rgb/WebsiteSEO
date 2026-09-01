/**
 * Who is allowed to change the rules.
 *
 * The webhook authenticates itself with Meta's HMAC and needs no login. The
 * admin panel is the opposite problem: a browser, a person, a password, and a
 * form that can rewrite what the account says to every follower who comments.
 * It sits on the same public hostname as the webhook, so it gets a real gate.
 *
 * One password, not accounts. There is exactly one operator and inventing a
 * user table for him would add a login flow, a reset flow and a second thing to
 * back up, to protect against nothing that a strong password does not.
 *
 * Three properties worth stating, because each is a thing that is usually got
 * wrong in a hand-rolled panel:
 *
 *   FAILS CLOSED. No password configured means the panel is not mounted at all
 *   — not "mounted with no password". An unconfigured admin surface on a public
 *   URL is strictly worse than a missing feature.
 *
 *   THE PASSWORD IS NEVER STORED. scrypt with a per-install salt, and a
 *   constant-time compare. Plaintext in an env var is accepted only as a
 *   convenience for a local run, and boots with a warning.
 *
 *   THE SESSION IS SIGNED, NOT LOOKED UP. A stateless HMAC cookie keeps
 *   restarts from logging you out and needs no session table — and the key is
 *   derived from the password hash, so changing the password invalidates every
 *   cookie that was ever issued.
 */

const crypto = require("node:crypto");

const COOKIE = "ig_admin";
const SCRYPT = { N: 16384, r: 8, p: 1, keylen: 32 };
const DEFAULT_HOURS = 12;

/* ---------------------------------------------------------------------------
 * The password
 * ------------------------------------------------------------------------- */

/** `scrypt$N$r$p$salt$key`, all base64. Produced by scripts/set-admin-password.js. */
function hash(password, salt = crypto.randomBytes(16)) {
  const key = crypto.scryptSync(String(password), salt, SCRYPT.keylen, { N: SCRYPT.N, r: SCRYPT.r, p: SCRYPT.p });
  return `scrypt$${SCRYPT.N}$${SCRYPT.r}$${SCRYPT.p}$${salt.toString("base64")}$${key.toString("base64")}`;
}

function verifyPassword(password, stored) {
  const parts = String(stored || "").split("$");
  if (parts.length !== 6 || parts[0] !== "scrypt") return false;
  const [, N, r, p, saltB64, keyB64] = parts;

  let expected, salt;
  try {
    expected = Buffer.from(keyB64, "base64");
    salt = Buffer.from(saltB64, "base64");
  } catch {
    return false;
  }
  if (!expected.length || !salt.length) return false;

  let got;
  try {
    got = crypto.scryptSync(String(password == null ? "" : password), salt, expected.length, {
      N: Number(N),
      r: Number(r),
      p: Number(p),
      // scrypt with N=16384,r=8 needs ~16MB; node's default cap is 32MB but the
      // parameters come from a config file, so give the check headroom rather
      // than letting a legitimate login throw.
      maxmem: 256 * 1024 * 1024,
    });
  } catch {
    return false;
  }
  if (got.length !== expected.length) return false;
  return crypto.timingSafeEqual(got, expected);
}

/**
 * The configured hash, whatever form it was supplied in.
 * IG_ADMIN_PASSWORD (plaintext) is hashed on the spot, with a fixed salt so the
 * value — and therefore every session cookie — stays stable across restarts.
 */
let derived = null;
function storedHash() {
  const explicit = process.env.IG_ADMIN_PASSWORD_HASH;
  if (explicit) return explicit;

  const plain = process.env.IG_ADMIN_PASSWORD;
  if (!plain) return "";
  if (!derived || derived.plain !== plain) {
    derived = { plain, value: hash(plain, crypto.createHash("sha256").update(`ig-admin-salt:${plain}`).digest().subarray(0, 16)) };
  }
  return derived.value;
}

const configured = () => Boolean(storedHash());

/* ---------------------------------------------------------------------------
 * The session cookie
 * ------------------------------------------------------------------------- */

/**
 * Derived, never configured separately.
 *
 * Two consequences, both wanted: there is no fourth secret to lose, and a
 * password change is also a global logout, because the key that signed the old
 * cookies no longer exists.
 */
function sessionKey() {
  return crypto.createHmac("sha256", `${storedHash()}|${process.env.META_APP_SECRET || ""}`).update("ig-admin-session-v1").digest();
}

const ttlMs = () => Math.max(1, Number(process.env.IG_ADMIN_SESSION_HOURS || DEFAULT_HOURS)) * 3600_000;

function issue(now = Date.now()) {
  const payload = Buffer.from(JSON.stringify({ iat: now, exp: now + ttlMs() }), "utf8").toString("base64url");
  const sig = crypto.createHmac("sha256", sessionKey()).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}

/** @returns {{iat: number, exp: number}|null} */
function readToken(token, now = Date.now()) {
  if (!configured()) return null;
  const [payload, sig] = String(token || "").split(".");
  if (!payload || !sig) return null;

  const expected = crypto.createHmac("sha256", sessionKey()).update(payload).digest();
  let got;
  try {
    got = Buffer.from(sig, "base64url");
  } catch {
    return null;
  }
  if (got.length !== expected.length || !crypto.timingSafeEqual(got, expected)) return null;

  try {
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    if (!claims || typeof claims.exp !== "number" || claims.exp <= now) return null;
    return claims;
  } catch {
    return null;
  }
}

/** No cookie-parser dependency for one cookie. */
function fromRequest(req) {
  const header = req.headers && req.headers.cookie;
  if (!header) return "";
  for (const part of String(header).split(";")) {
    const eq = part.indexOf("=");
    if (eq < 0) continue;
    if (part.slice(0, eq).trim() === COOKIE) return decodeURIComponent(part.slice(eq + 1).trim());
  }
  return "";
}

function setCookie(res, value, { maxAgeMs = ttlMs(), secure = true } = {}) {
  const bits = [
    `${COOKIE}=${encodeURIComponent(value)}`,
    "Path=/admin",
    "HttpOnly",
    // Strict, not Lax: nothing links into the panel from anywhere else, and it
    // is most of a CSRF defence for free.
    "SameSite=Strict",
    `Max-Age=${Math.floor(maxAgeMs / 1000)}`,
  ];
  if (secure) bits.push("Secure");
  res.append("Set-Cookie", bits.join("; "));
}

function clearCookie(res, { secure = true } = {}) {
  const bits = [`${COOKIE}=`, "Path=/admin", "HttpOnly", "SameSite=Strict", "Max-Age=0"];
  if (secure) bits.push("Secure");
  res.append("Set-Cookie", bits.join("; "));
}

/* ---------------------------------------------------------------------------
 * Guessing the password
 * ------------------------------------------------------------------------- */

/**
 * Per-IP lockout on failed logins.
 *
 * scrypt already makes each guess cost ~100ms, which is most of the defence;
 * this is what stops a patient attacker from spending a week on it, and what
 * makes the attempt visible in the journal.
 */
const failures = new Map();
const LOCK_AFTER = Number(process.env.IG_ADMIN_LOCK_AFTER || 8);
const LOCK_MS = Number(process.env.IG_ADMIN_LOCK_MINUTES || 15) * 60_000;

function lockedFor(ip, now = Date.now()) {
  const rec = failures.get(ip);
  if (!rec || rec.until <= now) return 0;
  return rec.until - now;
}

function recordFailure(ip, now = Date.now()) {
  const rec = failures.get(ip) || { count: 0, until: 0 };
  if (rec.until && rec.until <= now) rec.count = 0;
  rec.count += 1;
  if (rec.count >= LOCK_AFTER) {
    rec.until = now + LOCK_MS;
    rec.count = 0;
    console.warn(`ADMIN LOGIN LOCKED for ${ip} — ${LOCK_AFTER} failed attempts`);
  }
  failures.set(ip, rec);
  if (failures.size > 1000) failures.clear();
}

const clearFailures = (ip) => failures.delete(ip);

/**
 * Express guard. 401 with a JSON body for the API; the SPA turns that into the
 * login screen rather than a redirect, so a stale tab does not lose its work.
 */
function requireAuth(req, res, next) {
  if (!configured()) return res.status(503).json({ message: "Admin panel is not configured." });
  const claims = readToken(fromRequest(req));
  if (!claims) return res.status(401).json({ message: "Sign in." });
  req.admin = claims;
  next();
}

/**
 * Same-origin check for anything that writes.
 *
 * SameSite=Strict already blocks the cross-site form post, but only in browsers
 * that honour it, and only while nothing else on the host can be tricked into
 * making the request. This is the belt to that pair of braces: a state-changing
 * call must either declare an Origin we recognise or none at all (curl, which
 * has no ambient cookie to abuse in the first place).
 */
function sameOrigin(req, res, next) {
  const origin = req.get("origin");
  if (!origin) return next();
  let host;
  try {
    host = new URL(origin).host;
  } catch {
    return res.status(403).json({ message: "Bad origin." });
  }
  if (host !== req.get("host")) {
    console.warn("ADMIN CROSS-ORIGIN WRITE REFUSED from", origin);
    return res.status(403).json({ message: "Cross-origin request refused." });
  }
  next();
}

module.exports = {
  COOKIE,
  hash,
  verifyPassword,
  storedHash,
  configured,
  issue,
  readToken,
  fromRequest,
  setCookie,
  clearCookie,
  requireAuth,
  sameOrigin,
  lockedFor,
  recordFailure,
  clearFailures,
  ttlMs,
  _resetLocks: () => failures.clear(),
};
