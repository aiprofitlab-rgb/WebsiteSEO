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

/* ---------------------------------------------------------------------------
 * Post targeting and the forbidden list
 * ------------------------------------------------------------------------- */

/** The live shape: each rule scoped to the one post its campaign runs on. */
const SCOPED_RULES = {
  rules: [
    { id: "demo", keywords: ["demo", "demos"], media: { mode: "only", ids: ["post_A"] }, dm: { text: "here" }, publicReply: "Sent 📩" },
    { id: "price", keywords: ["price"], media: { mode: "only", ids: ["post_B"] }, dm: { text: "here" }, publicReply: "On its way 📩" },
  ],
};

test("a keyword scoped to another post is not forbidden here — the ban follows the rule's scope", async () => {
  // With every live rule scoped to a single post, an unscoped ban left the model
  // unable to name its own product anywhere. The matcher was always scope-aware;
  // only the prompt was not, so the two disagreed and the prompt was the stricter.
  const { ai, seen } = fakeAi("The Smart Storefront demo is on the site.");
  const out = await ai.replyToComment({ text: "what do you do?", config: CFG, rulesConfig: SCOPED_RULES, mediaId: "post_C" });

  assert.equal(out, "The Smart Storefront demo is on the site.", "no rule can fire on post_C, so nothing needed suppressing");
  assert.ok(!seen[0].messages[0].content.includes("NEVER use any of these words"), "and nothing needed forbidding either");
});

test("on the post the rule IS scoped to, both the ban and the suppression come back", async () => {
  const { ai, seen } = fakeAi("Sure — the demo is on the site.");
  const out = await ai.replyToComment({ text: "can I see it?", config: CFG, rulesConfig: SCOPED_RULES, mediaId: "post_A" });

  assert.equal(out, null, "under post_A a reply saying 'demo' would answer itself");
  const prompt = seen[0].messages[0].content;
  assert.match(prompt, /NEVER use any of these words.*demo/);
  assert.ok(!prompt.includes("price"), "post_B's keyword is still irrelevant here");
});

test("a DM only has to avoid unscoped keywords, because only those could collide", async () => {
  const { ai, seen } = fakeAi("Happy to help — the demo is on the site.");
  const out = await ai.replyToDm({ text: "hey", history: [], config: CFG, rulesConfig: SCOPED_RULES });

  assert.equal(out, "Happy to help — the demo is on the site.", "a DM is under no post");
  assert.ok(!seen[0].messages[0].content.includes("NEVER use any of these words"));
});

test("with no post context at all, every keyword is still named — the cautious default", async () => {
  assert.deepEqual(aiLib.liveKeywords(SCOPED_RULES), ["demo", "demos", "price"]);
  assert.deepEqual(aiLib.liveKeywords(SCOPED_RULES, "post_A"), ["demo", "demos"]);
  assert.deepEqual(aiLib.liveKeywords(SCOPED_RULES, ""), []);
});

/* ---------------------------------------------------------------------------
 * Plan B: the site index in the prompt
 *
 * lib/siteIndex.js is tested on its own in test/siteIndex.test.js. What matters
 * here is only the join: that a block appears where it should, that it carries
 * the framing, and above all that every way retrieval can fail leaves this file
 * assembling exactly the prompt it assembled before retrieval existed.
 * ------------------------------------------------------------------------- */

const siteIndex = require("../lib/siteIndex");

const INDEXED = aiConfig.withDefaults({
  enabled: true,
  persona: "You are a test.",
  facts: ["A fact."],
  rules: ["A rule."],
  index: { enabled: true, url: "https://aiprofitlab.io/aiden-index.json" },
});

const INDEX_PAYLOAD = {
  generated: "2026-09-05T08:00:11Z",
  site: "https://aiprofitlab.io",
  pages: [
    { url: "/blog/en/receptionist/", lang: "en", type: "article", title: "The AI receptionist explained", desc: "What one is.", keywords: [] },
    { url: "/blog/ar/receptionist/", lang: "ar", type: "article", title: "موظف الاستقبال الذكي", desc: "ما هو ولماذا.", keywords: [] },
  ],
};

test.afterEach(() => siteIndex.reset());

test("a matching article turns up under the facts and above the rules, where it can be overruled", async () => {
  siteIndex.load(INDEX_PAYLOAD, { url: "https://aiprofitlab.io/aiden-index.json" });
  const { ai, seen } = fakeAi("fine");
  await ai.replyToComment({ text: "what is an ai receptionist?", config: INDEXED, rulesConfig: RULES });

  const lines = seen[0].messages[0].content.split("\n");
  const facts = lines.findIndex((l) => l.startsWith("What you know:"));
  const block = lines.findIndex((l) => l.startsWith("Reference material"));
  const rules = lines.findIndex((l) => l.startsWith("How to answer:"));

  assert.ok(block > facts && block < rules, `facts ${facts}, reference ${block}, rules ${rules}`);
  assert.match(seen[0].messages[0].content, /https:\/\/aiprofitlab\.io\/blog\/en\/receptionist\//);
  // It is machine-selected off our own site rather than typed by a stranger, but
  // it is still text arriving from outside the prompt.
  assert.match(seen[0].messages[0].content, /every rule below overrides them/);
});

test("nothing retrieved is the prompt this file built before retrieval existed", async () => {
  siteIndex.load(INDEX_PAYLOAD, { url: "https://aiprofitlab.io/aiden-index.json" });
  const { ai, seen } = fakeAi("fine");
  await ai.replyToComment({ text: "nice 👏", config: INDEXED, rulesConfig: RULES });

  const withIndex = seen[0].messages[0].content;
  const without = aiLib.systemPrompt(INDEXED, {
    surface: "comment",
    maxChars: Number(INDEXED.comments.maxChars),
    forbidden: aiLib.liveKeywords(RULES, ""),
    language: aiLib.languageInstruction("nice 👏"),
  });
  assert.equal(withIndex, without, "byte for byte, or this feature is not additive");
});

test("a fetch that never succeeded costs the model some reading and nothing else", async () => {
  await siteIndex.refresh(INDEXED, {
    fetchImpl: async () => {
      throw new Error("ENOTFOUND");
    },
  });
  const { ai, seen } = fakeAi("Happy to help — it is all on the site.");
  const out = await ai.replyToComment({ text: "what is an ai receptionist?", config: INDEXED, rulesConfig: RULES });

  assert.equal(out, "Happy to help — it is all on the site.", "the reply still happens; that is the whole point");
  assert.ok(!seen[0].messages[0].content.includes("Reference material"));
});

test("the script of the message picks the language of the reference, not the model", async () => {
  siteIndex.load(INDEX_PAYLOAD, { url: "https://aiprofitlab.io/aiden-index.json" });

  const ar = fakeAi("تمام");
  await ar.ai.replyToComment({ text: "ما هو موظف الاستقبال؟", config: INDEXED, rulesConfig: RULES });
  assert.match(ar.seen[0].messages[0].content, /\/blog\/ar\/receptionist\//);
  assert.ok(!ar.seen[0].messages[0].content.includes("/blog/en/receptionist/"));

  const en = fakeAi("fine");
  await en.ai.replyToComment({ text: "what is an ai receptionist?", config: INDEXED, rulesConfig: RULES });
  assert.match(en.seen[0].messages[0].content, /\/blog\/en\/receptionist\//);
  assert.ok(!en.seen[0].messages[0].content.includes("/blog/ar/receptionist/"));
});

test("a DM gets the same treatment, with the empty media id vet() will use", async () => {
  siteIndex.load(INDEX_PAYLOAD, { url: "https://aiprofitlab.io/aiden-index.json" });
  const { ai, seen } = fakeAi("ok");
  await ai.replyToDm({ text: "what is an ai receptionist?", history: [], config: INDEXED, rulesConfig: RULES });
  assert.match(seen[0].messages[0].content, /\/blog\/en\/receptionist\//);
});

test("the block can never hand the model a word its own answer would be suppressed for", async () => {
  // "demo" is a live keyword in RULES. A title carrying it is the trap: the model
  // repeats what it is shown, vet() then bins the reply, and the follower sees
  // nothing at all.
  siteIndex.load(
    {
      site: "https://aiprofitlab.io",
      pages: [
        { url: "/blog/en/demo/", lang: "en", type: "article", title: "Book a demo of the receptionist", desc: "", keywords: [] },
        { url: "/blog/en/receptionist/", lang: "en", type: "article", title: "The AI receptionist explained", desc: "", keywords: [] },
      ],
    },
    { url: "https://aiprofitlab.io/aiden-index.json" }
  );
  const { ai, seen } = fakeAi("fine");
  await ai.replyToComment({ text: "what is an ai receptionist?", config: INDEXED, rulesConfig: RULES, mediaId: "" });

  const prompt = seen[0].messages[0].content;
  assert.match(prompt, /\/blog\/en\/receptionist\//);
  assert.ok(!prompt.includes("/blog/en/demo/"), "the one with a forbidden word in its title never got offered");
});
