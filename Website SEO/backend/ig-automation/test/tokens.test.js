/**
 * The 60-day fuse.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function freshFile() {
  const p = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ig-token-")), "token.json");
  process.env.IG_TOKEN_FILE = p;
  return p;
}

/** The module caches by mtime, so each case gets its own copy. */
function loadTokens() {
  delete require.cache[require.resolve("../lib/tokens")];
  return require("../lib/tokens");
}

const okFetch = (token = "NEW_TOKEN", expires = 5184000) => async () => ({
  ok: true,
  status: 200,
  json: async () => ({ access_token: token, expires_in: expires }),
});
const errFetch = (message, status = 400) => async () => ({
  ok: false,
  status,
  json: async () => ({ error: { message, code: 190 } }),
});

test("the countdown does not flicker across the boundary right after a refresh", () => {
  freshFile();
  const tokens = loadTokens();
  const at = Date.now();
  tokens._write({ access_token: "X", expires_in: 5184000, refreshed_at: new Date(at).toISOString() });

  assert.equal(tokens.daysLeft(at), 60, "the instant it was written");
  assert.equal(tokens.daysLeft(at + 1), 60, "a millisecond later");
  assert.equal(tokens.daysLeft(at + 23 * 3600 * 1000), 60, "23 hours later");
  assert.equal(tokens.daysLeft(at + 25 * 3600 * 1000), 59, "and only then does it tick down");
  assert.equal(tokens.daysLeft(at + 60 * 24 * 3600 * 1000), 0, "zero exactly at expiry");
});

test("seeding writes the env token to the file, and never overwrites a newer one", () => {
  freshFile();
  const tokens = loadTokens();
  process.env.IG_ACCESS_TOKEN = "SEED";

  tokens.seed();
  assert.equal(tokens.current(), "SEED");

  tokens._write({ access_token: "REFRESHED", expires_in: 5184000, refreshed_at: new Date().toISOString() });
  tokens.seed();
  assert.equal(tokens.current(), "REFRESHED", "a stale env var must not clobber a rotated token");
});

test("the token file is written 0600 — it is a credential on a shared box", () => {
  const p = freshFile();
  const tokens = loadTokens();
  tokens._write({ access_token: "X", expires_in: 100 });
  assert.equal(fs.statSync(p).mode & 0o777, 0o600);
});

test("a refresh replaces the token and resets the clock", async () => {
  freshFile();
  const tokens = loadTokens();
  process.env.IG_ACCESS_TOKEN = "OLD";
  tokens.seed();

  const res = await tokens.refresh({ fetchImpl: okFetch() });
  assert.equal(res.ok, true);
  assert.equal(tokens.current(), "NEW_TOKEN");
  // Steady at 60 for the whole first day — not 59 a millisecond after the write.
  assert.equal(tokens.daysLeft(), 60);
  assert.equal(res.daysLeft, tokens.daysLeft(), "refresh and /health must not disagree");
});

test("'not 24 hours old yet' is reported as benign, not as an incident", async () => {
  freshFile();
  const tokens = loadTokens();
  process.env.IG_ACCESS_TOKEN = "OLD";
  tokens.seed();

  const res = await tokens.refresh({ fetchImpl: errFetch("The access token must be at least 24 hours old.") });
  assert.equal(res.ok, false);
  assert.equal(res.reason, "too-soon");
});

test("a rejected refresh keeps the existing token rather than blanking it", async () => {
  freshFile();
  const tokens = loadTokens();
  process.env.IG_ACCESS_TOKEN = "OLD";
  tokens.seed();

  const res = await tokens.refresh({ fetchImpl: errFetch("Error validating access token: Session has expired") });
  assert.equal(res.reason, "rejected");
  assert.equal(tokens.current(), "OLD", "a bad response must not cost us the token we still have");
});

test("a network failure is distinguished from a rejection", async () => {
  freshFile();
  const tokens = loadTokens();
  process.env.IG_ACCESS_TOKEN = "OLD";
  tokens.seed();

  const res = await tokens.refresh({ fetchImpl: async () => { throw new Error("ETIMEDOUT"); } });
  assert.equal(res.reason, "network");
  assert.equal(tokens.current(), "OLD");
});

test("a rotation by the cron is picked up without a restart", async () => {
  const p = freshFile();
  const server = loadTokens(); // stands in for the long-running process
  process.env.IG_ACCESS_TOKEN = "OLD";
  server.seed();
  assert.equal(server.current(), "OLD");

  // A separate process rewrites the file.
  await new Promise((r) => setTimeout(r, 10));
  fs.writeFileSync(p, JSON.stringify({ access_token: "ROTATED", expires_in: 5184000, refreshed_at: new Date().toISOString() }));

  assert.equal(server.current(), "ROTATED", "re-read on mtime change, not cached for the process lifetime");
});

test("days left goes negative once the token is past its expiry", () => {
  freshFile();
  const tokens = loadTokens();
  const longAgo = new Date(Date.now() - 70 * 24 * 3600 * 1000).toISOString();
  tokens._write({ access_token: "STALE", expires_in: 5184000, refreshed_at: longAgo });
  assert.ok(tokens.daysLeft() < 0, "expired tokens report as expired, not as unknown");
});

test("no token at all is reported, not treated as a refresh failure", async () => {
  freshFile();
  const tokens = loadTokens();
  delete process.env.IG_ACCESS_TOKEN;
  const res = await tokens.refresh({ fetchImpl: okFetch() });
  assert.equal(res.reason, "no-token");
});
