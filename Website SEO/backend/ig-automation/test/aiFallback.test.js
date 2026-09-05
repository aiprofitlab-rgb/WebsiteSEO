/**
 * The fallback inside the flow: what gets offered to it, and what it is not
 * allowed to do.
 *
 * Same arrangement as handler.test.js — a real throwaway SQLite store, because
 * the dedupe and the "did we say this already" guard are the whole point and a
 * fake store would prove neither. The model is a stub returning a fixed string.
 */
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const handler = require("../lib/handler");
const store = require("../lib/store");
const realLedger = require("../lib/ledger");
const aiConfig = require("../lib/aiConfig");

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
    { id: "guide", keywords: ["guide"], dm: { text: "Reply with your email" }, publicReply: "Sent 📩", askEmail: true },
  ],
};

function harness({ reply = "Thanks for asking — it's all on the site.", aiOverrides = {}, config = {}, igOverrides = {} } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ig-ai-"));
  const db = store.open(path.join(dir, "state.sqlite"));

  const calls = { privateReply: [], publicReply: [], sendText: [], media: [] };
  const ig = {
    privateReply: async (a) => (calls.privateReply.push(a), { message_id: "m1" }),
    publicReply: async (a) => (calls.publicReply.push(a), { id: "r1" }),
    sendText: async (a) => (calls.sendText.push(a), { message_id: "m2" }),
    media: async (id) => (calls.media.push(id), { permalink: "https://instagram.com/p/ABC/" }),
    ...igOverrides,
  };

  const asked = { comment: [], dm: [] };
  const ai = {
    configured: () => true,
    replyToComment: async (a) => (asked.comment.push(a), reply),
    replyToDm: async (a) => (asked.dm.push(a), reply),
    ...aiOverrides,
  };

  const appended = [];
  const ledger = {
    STATUS: realLedger.STATUS,
    append: async (r) => (appended.push(r), true),
    update: async () => true,
  };

  return {
    db,
    calls,
    asked,
    appended,
    deps: {
      ig,
      ai,
      store: db,
      ledger,
      rules: RULES,
      aiConfig: aiConfig.withDefaults({ enabled: true, ...config }),
      alert: { tokenRejected: async () => {}, loopSuspected: async () => {} },
      selfId: SELF,
      selfUsername: "aiprofitlab",
    },
  };
}

const comment = (over = {}) => ({
  id: over.id || "17925384756201943",
  text: over.text === undefined ? "so what is it you actually do?" : over.text,
  from: over.from || { id: OTHER, username: "a_follower" },
  media: over.media === undefined ? { id: "17900000000000001" } : over.media,
  ...(over.parent_id ? { parent_id: over.parent_id } : {}),
});
const entry = { id: SELF };

const dm = (over = {}) => ({
  sender: { id: over.senderId || OTHER, username: over.username || "a_follower" },
  message: { mid: over.mid || "mid-1", text: over.text === undefined ? "hey, do you build websites?" : over.text, ...(over.echo ? { is_echo: true } : {}) },
});

// ---------------------------------------------------------------- comments ---

test("a comment matching no keyword now gets a public answer instead of being dropped", async () => {
  const h = harness();
  const out = await handler.handleComment(comment(), entry, h.deps);

  assert.equal(out.action, "ai_replied");
  assert.equal(h.calls.publicReply.length, 1);
  assert.equal(h.calls.publicReply[0].message, "Thanks for asking — it's all on the site.");
  h.db.close();
});

test("the fallback NEVER sends a DM off a comment — Meta allows one private reply per comment, ever", async () => {
  const h = harness();
  await handler.handleComment(comment(), entry, h.deps);
  assert.equal(h.calls.privateReply.length, 0, "the one-shot private reply stays available for a keyword rule");
  h.db.close();
});

test("a keyword still wins — the fallback only ever sees what the rules declined", async () => {
  const h = harness();
  const out = await handler.handleComment(comment({ text: "storefront please" }), entry, h.deps);

  assert.equal(out.action, "sent");
  assert.equal(out.ruleId, "storefront");
  assert.equal(h.asked.comment.length, 0, "the model was never consulted");
  assert.equal(h.calls.privateReply.length, 1);
  h.db.close();
});

test("OUR OWN generated reply, handed back by Meta as a new comment, is recognised and dropped", async () => {
  // The 2026-08-30 loop, in the one form the config-based guard cannot see: the
  // text is not a publicReply string, because no human ever wrote it.
  const h = harness();
  const first = await handler.handleComment(comment(), entry, h.deps);
  assert.equal(first.action, "ai_replied");

  const echo = await handler.handleComment(
    comment({ id: "18000000000000002", text: "Thanks for asking — it's all on the site." }),
    entry,
    h.deps
  );

  assert.equal(echo.action, "drop");
  assert.equal(echo.why, "our own generated reply");
  assert.equal(h.calls.publicReply.length, 1, "exactly one public reply exists — the loop did not start");
  h.db.close();
});

test("recognising our own words survives an @mention, casing and stray whitespace", async () => {
  const h = harness();
  await handler.handleComment(comment(), entry, h.deps);

  const echo = await handler.handleComment(
    comment({ id: "18000000000000003", text: "@nahid_aby   THANKS FOR ASKING — IT'S ALL ON THE SITE." }),
    entry,
    h.deps
  );
  assert.equal(echo.why, "our own generated reply");
  h.db.close();
});

test("a reply to a comment is left alone by default — a thread is where a loop hides", async () => {
  const h = harness();
  const out = await handler.handleComment(comment({ parent_id: "17900000000000009" }), entry, h.deps);

  assert.equal(out.action, "drop");
  assert.match(out.why, /top-level/);
  assert.equal(h.calls.publicReply.length, 0);
  h.db.close();
});

test("a redelivered comment is answered once, not twice", async () => {
  const h = harness();
  const c = comment();
  await handler.handleComment(c, entry, h.deps);
  const retry = await handler.handleComment(c, entry, h.deps);

  assert.equal(retry.action, "drop");
  assert.equal(retry.why, "already handled");
  assert.equal(h.calls.publicReply.length, 1);
  h.db.close();
});

test("the AI's own per-post cap stops it, and counts only replies that actually went out", async () => {
  const h = harness({ config: { comments: { maxPerMediaPerHour: 2 } } });

  for (let i = 0; i < 2; i++) {
    const out = await handler.handleComment(comment({ id: `1800000000000010${i}`, text: `question number ${i}` }), entry, h.deps);
    assert.equal(out.action, "ai_replied");
  }
  const third = await handler.handleComment(comment({ id: "18000000000000199", text: "one more question" }), entry, h.deps);

  assert.equal(third.action, "throttled");
  assert.equal(h.calls.publicReply.length, 2);
  h.db.close();
});

test("a comment the model declines to answer does not use up the cap", async () => {
  const h = harness({ reply: null, config: { comments: { maxPerMediaPerHour: 1 } } });

  const skipped = await handler.handleComment(comment({ id: "18000000000000200" }), entry, h.deps);
  assert.equal(skipped.action, "skipped");
  assert.equal(h.calls.publicReply.length, 0);

  // The cap is 1 and nothing has been posted, so the next real question must
  // still get through. Counting declines would let a spam wave mute the account.
  h.deps.ai.replyToComment = async () => "A real answer.";
  const answered = await handler.handleComment(comment({ id: "18000000000000201", text: "a genuine question" }), entry, h.deps);
  assert.equal(answered.action, "ai_replied");
  h.db.close();
});

test("the shared loop breaker still bounds the fallback, whatever its own caps say", async () => {
  const h = harness({ config: { comments: { maxPerMediaPerHour: 999, maxPerHour: 999 } } });
  h.deps.limits = { perMediaPerHour: 1, perAccountPerHour: 1, windowMs: 3600000 };

  await handler.handleComment(comment({ id: "18000000000000300" }), entry, h.deps);
  const out = await handler.handleComment(comment({ id: "18000000000000301", text: "another one" }), entry, h.deps);

  assert.equal(out.action, "throttled");
  h.db.close();
});

test("an OpenAI outage is a quiet non-event — no comment, no crash", async () => {
  const h = harness({ aiOverrides: { replyToComment: async () => { throw Object.assign(new Error("boom"), { code: "NETWORK" }); } } });
  const out = await handler.handleComment(comment(), entry, h.deps);

  assert.equal(out.action, "error");
  assert.equal(h.calls.publicReply.length, 0);
  h.db.close();
});

test("with enabled:false the service behaves exactly as it did before the fallback existed", async () => {
  const h = harness({ config: { enabled: false } });
  h.deps.aiConfig = aiConfig.withDefaults({ enabled: false });

  const out = await handler.handleComment(comment(), entry, h.deps);
  assert.equal(out.action, "drop");
  assert.equal(out.why, "no keyword");
  assert.equal(h.asked.comment.length, 0);
  h.db.close();
});

test("with no deps.ai at all, nothing changed — this is what keeps the original tests honest", async () => {
  const h = harness();
  delete h.deps.ai;
  const out = await handler.handleComment(comment(), entry, h.deps);
  assert.equal(out.action, "drop");
  assert.equal(out.why, "no keyword");
  h.db.close();
});

// -------------------------------------------------------------------- DMs ---

test("an ordinary DM is answered instead of being silently binned", async () => {
  const h = harness();
  const out = await handler.handleMessage(dm(), entry, h.deps);

  assert.equal(out.action, "ai_replied");
  assert.equal(h.calls.sendText.length, 1);
  assert.equal(h.calls.sendText[0].igsid, OTHER);
  h.db.close();
});

test("email capture is NOT interrupted by the fallback — that person was asked a question", async () => {
  const h = harness();
  h.db.setState(OTHER, { state: "awaiting_email", ruleId: "guide", commentId: "c1" });

  const out = await handler.handleMessage(dm({ text: "me@example.com" }), entry, h.deps);
  assert.equal(out.action, "email_captured");
  assert.equal(h.asked.dm.length, 0, "the model never saw it");
  h.db.close();
});

test("once the email is captured, the next message falls through to the fallback", async () => {
  const h = harness();
  h.db.setState(OTHER, { state: "awaiting_email", ruleId: "guide", commentId: "c1" });
  await handler.handleMessage(dm({ mid: "mid-a", text: "me@example.com" }), entry, h.deps);

  const out = await handler.handleMessage(dm({ mid: "mid-b", text: "great — and how long does setup take?" }), entry, h.deps);
  assert.equal(out.action, "ai_replied");
  h.db.close();
});

test("the model is given the thread, and its own answer is in it next time", async () => {
  const h = harness();
  await handler.handleMessage(dm({ mid: "mid-1", text: "hello" }), entry, h.deps);
  await handler.handleMessage(dm({ mid: "mid-2", text: "do you do arabic?" }), entry, h.deps);

  assert.equal(h.asked.dm[0].history.length, 0, "nothing to remember on the first message");
  assert.deepEqual(
    h.asked.dm[1].history.map((t) => [t.role, t.text]),
    [
      ["user", "hello"],
      ["assistant", "Thanks for asking — it's all on the site."],
    ],
    "the second call sees the first exchange, and does not see the current message twice"
  );
  h.db.close();
});

test("our own echoed DM is still ignored — the fallback must not answer itself", async () => {
  const h = harness();
  const out = await handler.handleMessage(dm({ echo: true }), entry, h.deps);
  assert.equal(out.action, "drop");
  assert.equal(out.why, "echo");
  assert.equal(h.calls.sendText.length, 0);
  h.db.close();
});

test("a redelivered DM is answered once", async () => {
  const h = harness();
  const m = dm();
  await handler.handleMessage(m, entry, h.deps);
  const retry = await handler.handleMessage(m, entry, h.deps);

  assert.equal(retry.why, "already handled");
  assert.equal(h.calls.sendText.length, 1);
  h.db.close();
});

test("a send that fails outside Meta's 24h window is logged, not retried into a loop", async () => {
  const h = harness({
    igOverrides: {
      sendText: async () => {
        throw Object.assign(new Error("This message is sent outside of allowed window"), { code: 10 });
      },
    },
  });
  const out = await handler.handleMessage(dm(), entry, h.deps);
  assert.equal(out.action, "failed");
  h.db.close();
});

test("the DM cap bounds the hour", async () => {
  const h = harness({ config: { dms: { maxPerHour: 1 } } });
  await handler.handleMessage(dm({ mid: "mid-1" }), entry, h.deps);
  const out = await handler.handleMessage(dm({ mid: "mid-2", text: "another" }), entry, h.deps);

  assert.equal(out.action, "throttled");
  assert.equal(h.calls.sendText.length, 1);
  h.db.close();
});

test("a whole webhook body mixing a keyword comment, a stray comment and a DM does all three", async () => {
  const h = harness();
  const results = await handler.handleEvent(
    {
      object: "instagram",
      entry: [
        {
          id: SELF,
          changes: [
            { field: "comments", value: comment({ id: "c-key", text: "storefront" }) },
            { field: "comments", value: comment({ id: "c-ai", text: "is this available in oman?" }) },
          ],
          messaging: [dm({ mid: "mid-z", text: "hi there" })],
        },
      ],
    },
    h.deps
  );

  assert.deepEqual(results.map((r) => r.action), ["sent", "ai_replied", "ai_replied"]);
  assert.equal(h.calls.privateReply.length, 1, "one DM, from the keyword rule only");
  assert.equal(h.calls.publicReply.length, 2, "the keyword's fixed reply and the AI's");
  assert.equal(h.calls.sendText.length, 1, "and the DM answer");
  h.db.close();
});
