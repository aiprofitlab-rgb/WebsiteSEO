/**
 * The flow itself: guards, the one-shot DM, and the email capture.
 *
 * The store is REAL (a throwaway SQLite file) because dedupe is the thing most
 * worth proving and a fake would prove nothing. Instagram and Sheets are fakes.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const handler = require("../lib/handler");
const store = require("../lib/store");
const realLedger = require("../lib/ledger");

const SELF = "17841400000000000";
const OTHER = "78412345678901234";

const RULES = {
  rules: [
    {
      id: "storefront",
      keywords: ["storefront"],
      dm: { text: "Here it is", link: "https://aiprofitlab.io/en/smart-storefront/" },
      publicReply: "Sent! Check your DMs 📩",
    },
    {
      id: "guide",
      keywords: ["guide"],
      dm: { text: "Reply with your email" },
      publicReply: "Sent 📩",
      askEmail: true,
    },
  ],
};

function harness({ igOverrides = {} } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ig-handler-"));
  const db = store.open(path.join(dir, "state.sqlite"));

  const calls = { privateReply: [], publicReply: [], sendText: [], media: [] };
  const ig = {
    privateReply: async (a) => (calls.privateReply.push(a), { message_id: "m1" }),
    publicReply: async (a) => (calls.publicReply.push(a), { id: "r1" }),
    sendText: async (a) => (calls.sendText.push(a), { message_id: "m2" }),
    media: async (id) => (calls.media.push(id), { permalink: "https://instagram.com/p/ABC/" }),
    ...igOverrides,
  };

  const appended = [];
  const updated = [];
  const ledger = {
    STATUS: realLedger.STATUS,
    append: async (r) => (appended.push(r), true),
    update: async (id, patch) => (updated.push({ id, patch }), true),
  };

  const alerts = [];
  const alert = { tokenRejected: async (a) => alerts.push(a), tokenRefreshFailed: async (a) => alerts.push(a) };

  return { db, ig, ledger, calls, appended, updated, alerts, deps: { ig, store: db, ledger, rules: RULES, alert, selfId: SELF } };
}

const comment = (over = {}) => ({
  id: over.id || "17925384756201943",
  text: over.text === undefined ? "storefront" : over.text,
  from: over.from || { id: OTHER, username: "a_follower" },
  media: over.media || { id: "17900000000000001" },
});
const entry = { id: SELF };

test("a keyword comment gets one DM, one public reply and one CRM row", async () => {
  const h = harness();
  const out = await handler.handleComment(comment(), entry, h.deps);

  assert.equal(out.action, "sent");
  assert.equal(h.calls.privateReply.length, 1);
  assert.equal(h.calls.privateReply[0].commentId, "17925384756201943");
  assert.match(h.calls.privateReply[0].text, /smart-storefront/, "the link is in the one message we get");
  assert.equal(h.calls.publicReply.length, 1);
  assert.equal(h.appended.length, 1);
  assert.equal(h.appended[0].Rule, "storefront");
  assert.equal(h.appended[0].Status, realLedger.STATUS.SENT);
  assert.equal(h.appended[0].Permalink, "https://instagram.com/p/ABC/");
  h.db.close();
});

test("our own comment is ignored — otherwise the public reply answers itself forever", async () => {
  const h = harness();
  const out = await handler.handleComment(comment({ from: { id: SELF, username: "aiprofitlab" }, text: "storefront" }), entry, h.deps);

  assert.equal(out.action, "drop");
  assert.equal(out.why, "our own comment");
  assert.equal(h.calls.privateReply.length, 0, "no DM");
  assert.equal(h.calls.publicReply.length, 0, "and critically, no second public comment");
  h.db.close();
});

test("a redelivered comment is dropped — the one private reply is never spent twice", async () => {
  const h = harness();
  const c = comment();

  const first = await handler.handleComment(c, entry, h.deps);
  const retry = await handler.handleComment(c, entry, h.deps);
  const retryAgain = await handler.handleComment(c, entry, h.deps);

  assert.equal(first.action, "sent");
  assert.equal(retry.why, "already handled");
  assert.equal(retryAgain.why, "already handled");
  assert.equal(h.calls.privateReply.length, 1, "exactly one DM across three deliveries");
  assert.equal(h.calls.publicReply.length, 1);
  assert.equal(h.appended.length, 1, "and exactly one lead row");
  h.db.close();
});

test("dedupe survives a restart, because a Meta retry can arrive after one", async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ig-restart-"));
  const file = path.join(dir, "state.sqlite");

  const h1 = harness();
  h1.db.close();
  const db1 = store.open(file);
  await handler.handleComment(comment(), entry, { ...h1.deps, store: db1 });
  assert.equal(h1.calls.privateReply.length, 1);
  db1.close();

  const db2 = store.open(file); // "restart"
  const out = await handler.handleComment(comment(), entry, { ...h1.deps, store: db2 });
  assert.equal(out.why, "already handled");
  assert.equal(h1.calls.privateReply.length, 1, "still one");
  db2.close();
});

test("a non-keyword comment costs nothing and is not recorded", async () => {
  const h = harness();
  const out = await handler.handleComment(comment({ text: "great reel 🔥" }), entry, h.deps);

  assert.equal(out.why, "no keyword");
  assert.equal(h.appended.length, 0);
  assert.equal(h.db.handled("17925384756201943"), null, "dedupe table stays clean of ordinary traffic");
  h.db.close();
});

test("if the DM fails, no public reply is posted — it would be a lie", async () => {
  const err = Object.assign(new Error("Recipient not found"), { code: 100 });
  const h = harness({ igOverrides: { privateReply: async () => { throw err; } } });

  const out = await handler.handleComment(comment(), entry, h.deps);

  assert.equal(out.action, "failed");
  assert.equal(h.calls.publicReply.length, 0, 'no "check your DMs" without a DM');
  assert.equal(h.appended.length, 1, "but the attempt is still recorded");
  assert.equal(h.appended[0].Status, realLedger.STATUS.FAILED);
  assert.match(h.appended[0].Notes, /Recipient not found/);
  assert.equal(h.db.handled(comment().id).status, "failed");
  h.db.close();
});

test("a token error during traffic raises an alert, not just a log line", async () => {
  const err = Object.assign(new Error("Error validating access token"), { code: 190, tokenProblem: true });
  const h = harness({ igOverrides: { privateReply: async () => { throw err; } } });

  await handler.handleComment(comment(), entry, h.deps);

  assert.equal(h.alerts.length, 1);
  assert.equal(h.alerts[0].code, 190);
  h.db.close();
});

test("a failed public reply does not lose the lead", async () => {
  const h = harness({ igOverrides: { publicReply: async () => { throw Object.assign(new Error("rate limited"), { code: 4 }); } } });

  const out = await handler.handleComment(comment(), entry, h.deps);

  assert.equal(out.action, "sent", "the DM is what matters");
  assert.equal(h.appended[0]["Public reply"], "failed");
  assert.equal(h.appended[0].Status, realLedger.STATUS.SENT);
  h.db.close();
});

test("a failed permalink lookup does not lose the lead either", async () => {
  const h = harness({ igOverrides: { media: async () => { throw new Error("nope"); } } });
  const out = await handler.handleComment(comment(), entry, h.deps);
  assert.equal(out.action, "sent");
  assert.equal(h.appended[0].Permalink, "");
  h.db.close();
});

test("an askEmail rule arms the conversation, and the reply backfills the CRM row", async () => {
  const h = harness();
  await handler.handleComment(comment({ text: "guide please" }), entry, h.deps);

  assert.equal(h.appended[0].Status, realLedger.STATUS.AWAITING_EMAIL);
  assert.equal(h.db.getState(OTHER).state, "awaiting_email");

  const out = await handler.handleMessage(
    { sender: { id: OTHER }, message: { mid: "m", text: "sure, it's Khalid@GulfLotus.om" } },
    entry,
    h.deps
  );

  assert.equal(out.action, "email_captured");
  assert.equal(out.email, "khalid@gulflotus.om", "normalised to lowercase");
  assert.equal(h.updated.length, 1);
  assert.equal(h.updated[0].id, "17925384756201943", "keyed on the comment id");
  assert.equal(h.updated[0].patch.Email, "khalid@gulflotus.om");
  assert.equal(h.db.getState(OTHER), null, "state cleared");
  h.db.close();
});

test("an echo of our own DM is ignored — the loop this prevents is infinite", async () => {
  const h = harness();
  h.db.setState(OTHER, { state: "awaiting_email", commentId: "C1", ruleId: "guide" });

  const echo = await handler.handleMessage({ sender: { id: SELF }, message: { text: "a@b.com", is_echo: true } }, entry, h.deps);
  assert.equal(echo.why, "echo");

  const self = await handler.handleMessage({ sender: { id: SELF }, message: { text: "a@b.com" } }, entry, h.deps);
  assert.equal(self.why, "our own message");

  assert.equal(h.updated.length, 0);
  h.db.close();
});

test("a DM from someone we are not expecting is ignored", async () => {
  const h = harness();
  const out = await handler.handleMessage({ sender: { id: OTHER }, message: { text: "hello@example.com" } }, entry, h.deps);
  assert.equal(out.why, "not awaiting email");
  assert.equal(h.updated.length, 0, "we do not harvest emails from unrelated DMs");
  h.db.close();
});

test("a reply with no email asks once and stays armed", async () => {
  const h = harness();
  h.db.setState(OTHER, { state: "awaiting_email", commentId: "C1", ruleId: "guide" });

  const out = await handler.handleMessage({ sender: { id: OTHER }, message: { text: "what is it about?" } }, entry, h.deps);

  assert.equal(out.action, "clarify");
  assert.equal(h.calls.sendText.length, 1);
  assert.ok(h.db.getState(OTHER), "still armed, so their next reply is caught");
  h.db.close();
});

test("capture expires with Meta's 24h messaging window", async () => {
  const h = harness();
  const now = Date.now();
  h.db.setState(OTHER, { state: "awaiting_email", commentId: "C1" }, now);

  const out = await handler.handleMessage(
    { sender: { id: OTHER }, message: { text: "a@b.com" } },
    entry,
    { ...h.deps, now: now + 25 * 60 * 60 * 1000 }
  );
  assert.equal(out.why, "not awaiting email");
  h.db.close();
});

test("handleEvent walks a batched body and one bad event does not abandon the rest", async () => {
  const h = harness();
  let n = 0;
  const ig = {
    ...h.ig,
    privateReply: async (a) => {
      n += 1;
      if (n === 1) throw Object.assign(new Error("boom"), { code: 1 });
      return h.ig.privateReply(a);
    },
  };

  const results = await handler.handleEvent(
    {
      object: "instagram",
      entry: [
        { id: SELF, changes: [{ field: "comments", value: comment({ id: "C1" }) }, { field: "comments", value: comment({ id: "C2" }) }] },
        { id: SELF, changes: [{ field: "mentions", value: {} }] },
      ],
    },
    { ...h.deps, ig }
  );

  assert.equal(results.length, 3);
  assert.equal(results[0].action, "failed");
  assert.equal(results[1].action, "sent", "the second comment still went out");
  assert.equal(results[2].why, "field mentions");
  h.db.close();
});

test("a body that is not an instagram event is ignored entirely", async () => {
  const h = harness();
  assert.deepEqual(await handler.handleEvent({ object: "whatsapp_business_account", entry: [] }, h.deps), []);
  assert.deepEqual(await handler.handleEvent(null, h.deps), []);
  assert.deepEqual(await handler.handleEvent({}, h.deps), []);
  h.db.close();
});

test("a very long comment is clipped before it reaches the sheet", async () => {
  const h = harness();
  await handler.handleComment(comment({ text: "storefront " + "x".repeat(5000) }), entry, h.deps);
  assert.ok(h.appended[0]["Comment text"].length <= 500);
  h.db.close();
});
