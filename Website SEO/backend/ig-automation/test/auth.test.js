/**
 * The gate on the panel.
 *
 * The password is the only thing between a public hostname and a form that can
 * rewrite what the account says to every follower, so each property below is
 * one that a hand-rolled login usually gets wrong.
 */
const test = require("node:test");
const assert = require("node:assert");

const auth = require("../lib/auth");

function withPassword(password, fn) {
  const before = { hash: process.env.IG_ADMIN_PASSWORD_HASH, plain: process.env.IG_ADMIN_PASSWORD };
  process.env.IG_ADMIN_PASSWORD_HASH = auth.hash(password);
  delete process.env.IG_ADMIN_PASSWORD;
  try {
    return fn();
  } finally {
    if (before.hash === undefined) delete process.env.IG_ADMIN_PASSWORD_HASH;
    else process.env.IG_ADMIN_PASSWORD_HASH = before.hash;
    if (before.plain !== undefined) process.env.IG_ADMIN_PASSWORD = before.plain;
  }
}

test("the password is salted per install — the same password hashes differently every time", () => {
  const a = auth.hash("correct-horse-battery");
  const b = auth.hash("correct-horse-battery");
  assert.notEqual(a, b);
  assert.ok(auth.verifyPassword("correct-horse-battery", a));
  assert.ok(auth.verifyPassword("correct-horse-battery", b));
  assert.equal(auth.verifyPassword("correct-horse-batterY", a), false);
});

test("a malformed or empty stored hash verifies nothing, rather than everything", () => {
  for (const stored of ["", null, "hunter2", "scrypt$1$2$3", "scrypt$16384$8$1$$"]) {
    assert.equal(auth.verifyPassword("anything", stored), false, `stored: ${stored}`);
    assert.equal(auth.verifyPassword("", stored), false);
  }
});

test("no password configured means the panel is off, not open", () => {
  const before = process.env.IG_ADMIN_PASSWORD_HASH;
  delete process.env.IG_ADMIN_PASSWORD_HASH;
  delete process.env.IG_ADMIN_PASSWORD;
  assert.equal(auth.configured(), false);
  assert.equal(auth.readToken(auth.issue()), null, "a cookie minted with no password must not authenticate");
  if (before) process.env.IG_ADMIN_PASSWORD_HASH = before;
});

test("a session cookie round-trips, and a tampered one does not", () => {
  withPassword("a-long-enough-password", () => {
    const token = auth.issue();
    assert.ok(auth.readToken(token));
    assert.equal(auth.readToken(token.slice(0, -2) + "xx"), null, "signature");

    const [payload, sig] = token.split(".");
    const forged = Buffer.from(JSON.stringify({ iat: 0, exp: Date.now() + 1e9 }), "utf8").toString("base64url");
    assert.equal(auth.readToken(`${forged}.${sig}`), null, "payload swapped under a valid signature");
    assert.equal(auth.readToken(payload), null, "no signature at all");
  });
});

test("an expired cookie is refused even though its signature is perfect", () => {
  withPassword("a-long-enough-password", () => {
    const token = auth.issue(Date.now() - 48 * 3600_000);
    assert.equal(auth.readToken(token), null);
  });
});

test("changing the password invalidates every cookie ever issued", () => {
  let token;
  withPassword("the-first-password", () => {
    token = auth.issue();
    assert.ok(auth.readToken(token));
  });
  withPassword("the-second-password", () => {
    assert.equal(auth.readToken(token), null);
  });
});

test("the cookie is read out of a header with other cookies in it", () => {
  withPassword("a-long-enough-password", () => {
    const token = auth.issue();
    const req = { headers: { cookie: `_ga=GA1.1.2; ig_admin=${encodeURIComponent(token)}; other=x` } };
    assert.equal(auth.fromRequest(req), token);
    assert.equal(auth.fromRequest({ headers: {} }), "");
  });
});

test("repeated wrong guesses lock the IP out", () => {
  auth._resetLocks();
  const ip = "203.0.113.9";
  assert.equal(auth.lockedFor(ip), 0);
  for (let i = 0; i < 8; i++) auth.recordFailure(ip);
  assert.ok(auth.lockedFor(ip) > 0);
  assert.equal(auth.lockedFor("203.0.113.10"), 0, "the lockout is per IP, not global");
  auth.clearFailures(ip);
  assert.equal(auth.lockedFor(ip), 0);
});

test("a write from another origin is refused; one with no Origin header is allowed through", () => {
  const run = (origin, host) => {
    let status = 200;
    const req = { get: (h) => (h.toLowerCase() === "origin" ? origin : host) };
    const res = { status: (s) => ((status = s), res), json: () => res };
    let passed = false;
    auth.sameOrigin(req, res, () => (passed = true));
    return { status, passed };
  };
  assert.equal(run("https://hooks.aiprofitlab.io", "hooks.aiprofitlab.io").passed, true);
  assert.equal(run("https://evil.test", "hooks.aiprofitlab.io").status, 403);
  assert.equal(run(undefined, "hooks.aiprofitlab.io").passed, true, "curl has no ambient cookie to abuse");
  assert.equal(run("not a url", "hooks.aiprofitlab.io").status, 403);
});
