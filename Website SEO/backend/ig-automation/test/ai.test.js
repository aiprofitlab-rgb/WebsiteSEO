/**
 * The fallback brain, on its own.
 *
 * The completion call is faked — what is being proven here is not that OpenAI
 * works, but that nothing it returns can hurt the account. Every test below is
 * some version of "the model said something dangerous; the service said nothing".
 */
const test = require("node:test");
const assert = require("node:assert");

const aiLib = require("../lib/ai");
const aiConfig = require("../lib/aiConfig");

const RULES = {
  rules: [
    { id: "demo", keywords: ["demo", "demos"], dm: { text: "here" }, publicReply: "Sent 📩" },
    { id: "price", keywords: ["price", "سعر"], dm: { text: "here" }, publicReply: "On its way 📩" },
  ],
};

const CFG = aiConfig.withDefaults({
  enabled: true,
  persona: "You are a test.",
  facts: ["A fact."],
  rules: ["A rule."],
});

/** An ai client whose model always returns `reply`, and that records its prompts. */
function fakeAi(reply, { fail } = {}) {
  const seen = [];
  const fetchImpl = async (url, init) => {
    seen.push(JSON.parse(init.body));
    if (fail) return { ok: false, status: fail.status || 500, json: async () => ({ error: { message: fail.message || "boom", code: fail.code } }) };
    return { ok: true, status: 200, json: async () => ({ choices: [{ message: { content: reply } }] }) };
  };
  return { ai: aiLib.create({ apiKey: "sk-test", fetchImpl }), seen };
}

test("a normal answer comes back cleaned up and ready to post", async () => {
  const { ai } = fakeAi("  Happy to help — everything is on the site.  ");
  const out = await ai.replyToComment({ text: "what do you do?", username: "someone", config: CFG, rulesConfig: RULES });
  assert.equal(out, "Happy to help — everything is on the site.");
});

test("a reply containing a live keyword is SUPPRESSED — this is the reply loop, written by a model", async () => {
  // The exact 2026-08-30 failure: we post a sentence, Meta hands it back as a new
  // comment, it matches a rule, and the account answers itself until it is
  // throttled. A generated reply defeats every guard except this one.
  const { ai } = fakeAi("Sure! You can book a demo any time.");
  const out = await ai.replyToComment({ text: "can I see it working?", username: "someone", config: CFG, rulesConfig: RULES });
  assert.equal(out, null, "it contains 'demo', so it must never be sent");
});

test("the suppression is language-aware, because the rules are", async () => {
  const { ai } = fakeAi("كل التفاصيل والسعر على الموقع");
  const out = await ai.replyToComment({ text: "بكم؟", username: "someone", config: CFG, rulesConfig: RULES });
  assert.equal(out, null, "'سعر' is a live keyword");
});

test("SKIP means stay silent, wherever in the reply it appears", async () => {
  for (const raw of ["SKIP", "SKIP — this one needs a human", "  skip  ".toUpperCase()]) {
    const { ai } = fakeAi(raw);
    const out = await ai.replyToDm({ text: "I want a refund", config: CFG, rulesConfig: RULES });
    assert.equal(out, null, `"${raw}" should produce silence`);
  }
});

test("an empty or whitespace answer is silence, not an empty comment", async () => {
  const { ai } = fakeAi("   \n  ");
  assert.equal(await ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES }), null);
});

test("the model's habit of wrapping one-liners in quotes is undone", async () => {
  const { ai } = fakeAi('"Thanks for reaching out!"');
  assert.equal(await ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES }), "Thanks for reaching out!");
});

test("a public comment reply is flattened to one line", async () => {
  const { ai } = fakeAi("Thanks!\n\n- point one\n- point two");
  const out = await ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES });
  assert.ok(!out.includes("\n"), "no line breaks survive into an Instagram comment");
});

test("an over-long reply is trimmed, and trimmed at a sentence end when there is one", async () => {
  const cfg = aiConfig.withDefaults({ enabled: true, comments: { maxChars: 60 } });
  const { ai } = fakeAi("This first sentence is short. And this second one runs on well past the limit we set.");
  const out = await ai.replyToComment({ text: "hi", config: cfg, rulesConfig: RULES });
  assert.ok(out.length <= 60, `got ${out.length} chars`);
  assert.equal(out, "This first sentence is short.");
});

test("with no sentence end to cut at, it truncates with an ellipsis rather than mid-word forever", async () => {
  const cfg = aiConfig.withDefaults({ enabled: true, comments: { maxChars: 30 } });
  const { ai } = fakeAi("a".repeat(200));
  const out = await ai.replyToComment({ text: "hi", config: cfg, rulesConfig: RULES });
  assert.ok(out.length <= 30, `got ${out.length} — the ellipsis must fit INSIDE the cap, not extend it`);
  assert.ok(out.endsWith("…"));
});

test("the live keywords are named in the prompt, so the check rarely has to fire", async () => {
  const { ai, seen } = fakeAi("fine");
  await ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES });
  const system = seen[0].messages[0].content;
  assert.match(system, /NEVER use any of these words/);
  assert.match(system, /demo/);
  assert.match(system, /سعر/);
});

test("DM history is passed through in the model's own format, oldest first", async () => {
  const { ai, seen } = fakeAi("ok");
  await ai.replyToDm({
    text: "and how long does it take?",
    username: "someone",
    history: [
      { role: "user", text: "hello" },
      { role: "assistant", text: "hi there" },
    ],
    config: CFG,
    rulesConfig: RULES,
  });
  const msgs = seen[0].messages;
  const tail = msgs.slice(-3);
  assert.deepEqual(
    tail.map((m) => [m.role, m.content]),
    [
      ["user", "hello"],
      ["assistant", "hi there"],
      ["user", "and how long does it take?"],
    ]
  );
});

test("a comment gets a tighter token budget than a DM", async () => {
  const c = fakeAi("x");
  await c.ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES });
  const d = fakeAi("x");
  await d.ai.replyToDm({ text: "hi", config: CFG, rulesConfig: RULES });
  assert.ok(c.seen[0].max_tokens < d.seen[0].max_tokens);
});

test("an upstream failure throws with the code, so the caller can tell a 429 from a bad key", async () => {
  const { ai } = fakeAi(null, { fail: { status: 429, message: "Rate limit reached", code: "rate_limit_exceeded" } });
  await assert.rejects(() => ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES }), (err) => {
    assert.equal(err.name, "AiError");
    assert.equal(err.status, 429);
    assert.equal(err.code, "rate_limit_exceeded");
    return true;
  });
});

test("with no API key it reports itself unconfigured and refuses rather than calling out", async () => {
  const ai = aiLib.create({ apiKey: "", fetchImpl: async () => assert.fail("must not reach the network") });
  assert.equal(ai.configured(), false);
  await assert.rejects(() => ai.replyToComment({ text: "hi", config: CFG, rulesConfig: RULES }), /NO_KEY|No OPENAI_API_KEY/);
});

test("the reply language is decided from the message, not left to the model", async () => {
  // The first live test answered "do you work with businesses outside oman?" in
  // Arabic, because the forbidden-words list makes the system prompt visibly
  // bilingual. The script of the incoming text is a fact, so it is asserted.
  const en = fakeAi("fine");
  await en.ai.replyToComment({ text: "do you work outside oman?", config: CFG, rulesConfig: RULES });
  assert.match(en.seen[0].messages[0].content, /wrote in ENGLISH/);

  const ar = fakeAi("تمام");
  await ar.ai.replyToComment({ text: "هل تعملون بالعربي؟", config: CFG, rulesConfig: RULES });
  assert.match(ar.seen[0].messages[0].content, /wrote in ARABIC/);
});

test("one Arabic word in an otherwise English sentence still counts as Arabic", async () => {
  // "أوكي thanks" — people open in their own language and code-switch after.
  assert.match(aiLib.languageInstruction("أوكي thanks"), /ARABIC/);
  assert.match(aiLib.languageInstruction("thanks!"), /ENGLISH/);
});

test("the language line is the LAST instruction, where a model is least likely to drop it", async () => {
  const { ai, seen } = fakeAi("fine");
  await ai.replyToComment({ text: "hello", config: CFG, rulesConfig: RULES });
  const lines = seen[0].messages[0].content.split("\n").filter(Boolean);
  const lang = lines.findIndex((l) => l.includes("wrote in ENGLISH"));
  const forbidden = lines.findIndex((l) => l.includes("NEVER use any of these words"));
  assert.ok(lang > forbidden, "it must come after the Arabic keyword list that misleads it");
});
