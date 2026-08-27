/**
 * Dedupe and conversation state — both must be durable, and claim() must be
 * a race nobody can win twice.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const store = require("../lib/store");

const tmp = (name = "state.sqlite") => path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ig-store-")), name);

test("only the first claim on a comment wins", () => {
  const db = store.open(tmp());
  assert.equal(db.claim("C1"), true);
  assert.equal(db.claim("C1"), false);
  assert.equal(db.claim("C1"), false);
  assert.equal(db.claim("C2"), true, "a different comment is unaffected");
  db.close();
});

test("a claim outlives the process", () => {
  const file = tmp();
  const a = store.open(file);
  a.claim("C1");
  a.finish("C1", "sent");
  a.close();

  const b = store.open(file);
  assert.equal(b.claim("C1"), false, "a Meta retry after a restart still loses");
  assert.equal(b.handled("C1").status, "sent");
  b.close();
});

test("an empty comment id is never claimable", () => {
  const db = store.open(tmp());
  assert.equal(db.claim(""), false);
  assert.equal(db.claim(null), false);
  assert.equal(db.claim(undefined), false);
  db.close();
});

test("outcomes are recorded, so a failure does not read as a success", () => {
  const db = store.open(tmp());
  db.claim("C1", { ruleId: "storefront", username: "someone" });
  assert.equal(db.handled("C1").status, "processing");

  db.finish("C1", "failed", "Recipient not found");
  const row = db.handled("C1");
  assert.equal(row.status, "failed");
  assert.equal(row.notes, "Recipient not found");
  assert.equal(row.rule_id, "storefront");
  assert.ok(row.finished_at >= row.claimed_at);
  db.close();
});

test("a claim that never finished shows up as stuck", () => {
  const now = Date.now();
  const db = store.open(tmp());
  db.claim("C_OLD", {}, now - 60 * 60_000);
  db.claim("C_NEW", {}, now);
  db.finish("C_NEW", "sent", "", now);

  const stuck = db.stuck(10 * 60_000, now);
  assert.equal(stuck.length, 1);
  assert.equal(stuck[0].comment_id, "C_OLD");
  db.close();
});

test("release gives a claim back, for a crash before any call was made", () => {
  const db = store.open(tmp());
  db.claim("C1");
  db.release("C1");
  assert.equal(db.claim("C1"), true);
  db.close();
});

test("conversation state upserts rather than duplicating", () => {
  const db = store.open(tmp());
  db.setState("IG1", { state: "awaiting_email", ruleId: "guide", commentId: "C1" });
  db.setState("IG1", { state: "awaiting_email", ruleId: "lead", commentId: "C2" });

  const row = db.getState("IG1");
  assert.equal(row.rule_id, "lead");
  assert.equal(row.comment_id, "C2");
  assert.equal(db.stats().openConversations, 1);
  db.close();
});

test("state reads as gone once the 24h window closes, and sweeps away after", () => {
  const now = Date.now();
  const db = store.open(tmp());
  db.setState("IG1", { state: "awaiting_email" }, now);

  assert.ok(db.getState("IG1", now));
  assert.equal(db.getState("IG1", now + 25 * 3600 * 1000), null, "expired");

  assert.equal(db.sweep(now).states, 0, "not yet");
  assert.equal(db.sweep(now + 25 * 3600 * 1000).states, 1, "now reclaimed");
  db.close();
});

test("the sweep keeps dedupe rows long enough that no plausible retry gets through", () => {
  const now = Date.now();
  const db = store.open(tmp());
  db.claim("RECENT", {}, now - 7 * 24 * 3600 * 1000);
  db.claim("ANCIENT", {}, now - 90 * 24 * 3600 * 1000);

  assert.equal(db.sweep(now).handled, 1);
  assert.equal(db.claim("RECENT", {}, now), false, "a week-old comment is still deduped");
  assert.equal(db.handled("ANCIENT"), null);
  db.close();
});

test("clearState removes it immediately", () => {
  const db = store.open(tmp());
  db.setState("IG1", { state: "awaiting_email" });
  db.clearState("IG1");
  assert.equal(db.getState("IG1"), null);
  db.close();
});

test("the database directory is created if it does not exist", () => {
  const nested = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ig-mk-")), "var", "lib", "ig", "state.sqlite");
  const db = store.open(nested);
  assert.ok(fs.existsSync(nested));
  db.close();
});
