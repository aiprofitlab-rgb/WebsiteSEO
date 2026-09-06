/**
 * Plan B, on its own.
 *
 * There is no network anywhere in this file and there must never be one: every
 * test either hands load() a fixture directly or gives refresh() a fake fetch.
 * What is being proven is not that aiprofitlab.io serves an index — it does —
 * but that nothing which can go wrong with it reaches the prompt, and that the
 * two things which must never be injected (a figure, a live keyword) cannot be.
 */
const test = require("node:test");
const assert = require("node:assert");

const siteIndex = require("../lib/siteIndex");
const aiConfig = require("../lib/aiConfig");

const URL = "https://aiprofitlab.io/aiden-index.json";

/** The live shape, minus the 347 pages that are not the point of the test. */
const page = (over = {}) => ({
  url: "/blog/en/whatever/",
  lang: "en",
  type: "article",
  title: "Something",
  desc: "",
  headings: [],
  keywords: [],
  ...over,
});

const index = (pages) => ({
  generated: "2026-09-05T08:00:11Z",
  site: "https://aiprofitlab.io",
  count: pages.length,
  pages,
});

/** Built through aiConfig so the defaults under test are the shipped ones. */
const cfg = (over = {}) => aiConfig.withDefaults({ index: { enabled: true, url: URL, ...over } });

const RULES = {
  rules: [{ id: "demo", keywords: ["demo", "تجربة"], dm: { text: "here" }, publicReply: "Sent 📩" }],
};

const ask = (text, over = {}) =>
  siteIndex.lookup(text, { config: cfg(over.config || {}), lang: over.lang || "en", rulesConfig: over.rulesConfig, mediaId: over.mediaId });

test.beforeEach(() => siteIndex.reset());
test.after(() => siteIndex.reset());

/* ---------------------------------------------------------------------------
 * The floor: it can only ever add
 * ------------------------------------------------------------------------- */

test("with nothing ever fetched it offers nothing, and says nothing about it", () => {
  assert.deepEqual(ask("whatsapp automation"), []);
  assert.deepEqual(siteIndex.stats(), { loaded: false, pages: 0 });
});

test("a failed fetch leaves the prompt exactly as it was", async () => {
  const res = await siteIndex.refresh(cfg(), {
    fetchImpl: async () => {
      throw new Error("getaddrinfo ENOTFOUND");
    },
  });
  assert.equal(res.ok, false);
  assert.deepEqual(ask("whatsapp automation"), [], "no cache, no block, no reason a reply does not happen");
});

test("an HTTP error is a failed fetch too, not a page of Cloudflare HTML in the prompt", async () => {
  const res = await siteIndex.refresh(cfg(), { fetchImpl: async () => ({ ok: false, status: 502, json: async () => ({}) }) });
  assert.equal(res.ok, false);
  assert.deepEqual(ask("whatsapp automation"), []);
});

test("a good copy is served stale forever rather than being dropped on a later failure", async () => {
  const pages = [page({ title: "WhatsApp automation for Omani shops", url: "/blog/en/wa/" })];
  await siteIndex.refresh(cfg(), { fetchImpl: async () => ({ ok: true, status: 200, json: async () => index(pages) }) });
  assert.equal(ask("whatsapp automation").length, 1);

  await siteIndex.refresh(cfg(), { fetchImpl: async () => ({ ok: false, status: 500, json: async () => ({}) }) });
  assert.equal(ask("whatsapp automation").length, 1, "the site being down must not make Aiden dumber than it was");
});

test("JSON that is not an index keeps the last good copy", async () => {
  const pages = [page({ title: "WhatsApp automation for Omani shops" })];
  await siteIndex.refresh(cfg(), { fetchImpl: async () => ({ ok: true, status: 200, json: async () => index(pages) }) });

  const res = await siteIndex.refresh(cfg(), { fetchImpl: async () => ({ ok: true, status: 200, json: async () => ({ error: "nope" }) }) });
  assert.equal(res.ok, false);
  assert.equal(ask("whatsapp automation").length, 1);
});

test("disabled is disabled: no fetch, and nothing in the prompt even with a cache loaded", async () => {
  siteIndex.load(index([page({ title: "WhatsApp automation for Omani shops" })]), { url: URL });
  assert.equal(ask("whatsapp automation").length, 1);

  const off = aiConfig.withDefaults({ index: { enabled: false } });
  assert.deepEqual(siteIndex.lookup("whatsapp automation", { config: off, lang: "en" }), []);
  const res = await siteIndex.refresh(off, { fetchImpl: async () => assert.fail("must not reach the network") });
  assert.equal(res.why, "disabled");
});

test("the default config is OFF, so an install that has not been configured is untouched", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation for Omani shops" })]), { url: URL });
  // What a live /var/lib/ig-automation/ai.json with no `index` block produces.
  assert.deepEqual(siteIndex.lookup("whatsapp automation", { config: aiConfig.withDefaults({}), lang: "en" }), []);
});

test("lookup is synchronous — a function that cannot await cannot fetch on the reply path", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation for Omani shops" })]), { url: URL });
  const out = ask("whatsapp automation");
  assert.ok(Array.isArray(out), "an array, not a promise");
});

/* ---------------------------------------------------------------------------
 * Matching
 * ------------------------------------------------------------------------- */

test("a title word is enough on its own; a single keyword-list word is not", () => {
  siteIndex.load(
    index([
      page({ title: "The AI receptionist explained", url: "/blog/en/receptionist/" }),
      page({ title: "Something else entirely", url: "/blog/en/else/", keywords: ["receptionist"] }),
    ]),
    { url: URL }
  );
  const out = ask("what is an ai receptionist?");
  assert.equal(out.length, 1, "one strong noun in a title is a match; the same word buried in a keyword list is noise");
  assert.match(out[0], /receptionist\//);
});

test("two words from anywhere also clear the bar, and the bar is configurable", () => {
  siteIndex.load(index([page({ title: "Untitled", url: "/blog/en/x/", keywords: ["bookings", "clinic"] })]), { url: URL });
  assert.equal(ask("can you take clinic bookings?").length, 1);
  assert.equal(ask("can you take clinic bookings?", { config: { minScore: 5 } }).length, 0);
});

test("nothing good enough means nothing at all", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation for Omani shops", url: "/blog/en/wa/" })]), { url: URL });
  assert.deepEqual(ask("nice 👏"), [], "an empty list is what leaves the prompt exactly as it is");
});

test("the plural and the definite article are folded off both sides, or nothing ever matches", () => {
  siteIndex.load(
    index([
      page({ title: "Running a clinic on autopilot", url: "/blog/en/clinic/", keywords: ["bookings"] }),
      page({ title: "المطاعم في مسقط", url: "/blog/ar/food/", lang: "ar", keywords: ["حجوزات"] }),
    ]),
    { url: URL }
  );
  assert.equal(ask("do you do clinics and booking?").length, 1, "clinics -> clinic, bookings -> booking");
  assert.equal(ask("هل تعملون مع مطاعم؟", { lang: "ar" }).length, 1, "المطاعم -> مطاعم");
});

test("the same question always produces the same block", () => {
  const pages = ["a", "b", "c", "d"].map((k) => page({ title: `WhatsApp automation ${k}`, url: `/blog/en/${k}/` }));
  siteIndex.load(index(pages), { url: URL });
  assert.deepEqual(ask("whatsapp automation"), ask("whatsapp automation"));
});

test("only the configured types are retrieved — the core pages stay hand-written in `facts`", () => {
  siteIndex.load(
    index([
      page({ title: "WhatsApp automation, the service", url: "/en/services/", type: "services" }),
      page({ title: "WhatsApp automation, the article", url: "/blog/en/wa/", type: "article" }),
    ]),
    { url: URL }
  );
  const out = ask("whatsapp automation");
  assert.equal(out.length, 1);
  assert.match(out[0], /blog/, "/en/services/ has to be right, so a person writes it, not a description tag");

  assert.equal(ask("whatsapp automation", { config: { types: ["article", "services"] } }).length, 2, "and the list is config, not code");
});

test("the url in the block is absolute — a bare path is a link nobody can tap", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation for shops", url: "/blog/en/wa/" })]), { url: URL });
  assert.match(ask("whatsapp automation")[0], /https:\/\/aiprofitlab\.io\/blog\/en\/wa\//);
});

/* ---------------------------------------------------------------------------
 * Language
 * ------------------------------------------------------------------------- */

test("an Arabic message only ever gets Arabic pages, and an English one only English", () => {
  siteIndex.load(
    index([
      page({ title: "WhatsApp automation for Omani shops", url: "/blog/en/wa/", lang: "en", keywords: ["whatsapp", "automation"] }),
      page({ title: "أتمتة واتساب للمتاجر العمانية", url: "/blog/ar/wa/", lang: "ar", keywords: ["واتساب", "أتمتة"] }),
    ]),
    { url: URL }
  );

  const ar = ask("أتمتة واتساب", { lang: "ar" });
  assert.equal(ar.length, 1);
  assert.match(ar[0], /\/ar\//);

  const en = ask("whatsapp automation", { lang: "en" });
  assert.equal(en.length, 1);
  assert.match(en[0], /\/en\//);
});

/* ---------------------------------------------------------------------------
 * The scrubbers
 * ------------------------------------------------------------------------- */

test("an entry carrying a currency figure never enters memory at all", () => {
  const res = siteIndex.load(
    index([
      page({ title: "Oman PDPL explained", url: "/blog/en/pdpl/", desc: "The fine for getting this wrong is OMR 50,000." }),
      page({ title: "Oman PDPL, the short version", url: "/blog/en/pdpl-short/", desc: "What the law asks of you." }),
    ]),
    { url: URL }
  );
  assert.equal(res.pages, 1);
  assert.equal(res.dropped.figure, 1);

  const out = ask("tell me about pdpl");
  assert.equal(out.length, 1);
  assert.match(out[0], /pdpl-short/, "OMR 50,000 is a fine, not our price, and the model cannot tell the difference");
});

test("every way this site writes a figure is caught, in both languages", () => {
  for (const bad of [
    "OMR 50,000 for a breach",
    "Is $2,000 worth it?",
    "٥٠٠ ألف ريال غرامة",
    "2،000 دولار",
    "25 ريالا في الشهر",
    "cut response time by 42%",
    "خفض التكاليف بنسبة ٣٠٪",
    "a 4.2x return",
    "3 أضعاف المبيعات",
    "126,000 missed calls",
  ]) {
    assert.ok(siteIndex.carriesAFigure(bad), `"${bad}" must be caught`);
  }
  for (const fine of ["Oman Vision 2040", "WhatsApp automation in 2026", "5 tasks to stop doing by hand", "AI for SMEs"]) {
    assert.ok(!siteIndex.carriesAFigure(fine), `"${fine}" is a date or a list, not a claim`);
  }
});

test("a page merely ABOUT what things cost is kept out too, figure or no figure", () => {
  // This one has no number anywhere and is exactly what got retrieved for "how
  // much does it cost?" before the second scrubber existed.
  const res = siteIndex.load(
    index([
      page({ title: "How much does AI automation cost for B2B companies?", url: "/blog/en/cost/" }),
      page({ title: "ما هي تكلفة أتمتة الذكاء الاصطناعي؟", url: "/blog/ar/cost/", lang: "ar" }),
      page({ title: "What AI automation actually does", url: "/blog/en/what/" }),
    ]),
    { url: URL }
  );
  assert.equal(res.dropped.money, 2);
  assert.equal(res.pages, 1);
  assert.deepEqual(ask("how much does it cost?"), [], "money is a handover to Nahid, and a pricing guide is not a handover");
});

test("headings are read and thrown away — they are where the numbers live", () => {
  siteIndex.load(
    index([
      page({
        title: "The AI receptionist explained",
        url: "/blog/en/receptionist/",
        desc: "What one is and what it does all night.",
        headings: ["The $126,000 Problem Hiding in Your Missed Calls", "Cut response time 90%"],
      }),
    ]),
    { url: URL }
  );
  const out = ask("what is an ai receptionist?");
  assert.equal(out.length, 1, "a figure in a heading does not disqualify the page — it is simply never injected");
  assert.ok(!out[0].includes("126,000"), "and it must not reach the prompt");
  assert.ok(!out[0].includes("90%"));
});

/* ---------------------------------------------------------------------------
 * The forbidden words
 * ------------------------------------------------------------------------- */

test("an entry containing a live keyword is dropped — parroting it would suppress the whole reply", () => {
  siteIndex.load(
    index([
      page({ title: "Book a demo of the booking flow", url: "/blog/en/demo/", keywords: ["bookings"] }),
      page({ title: "How online booking works", url: "/blog/en/booking/", keywords: ["bookings"] }),
    ]),
    { url: URL }
  );
  const out = ask("how does online booking work?", { rulesConfig: RULES, mediaId: "" });
  assert.equal(out.length, 1);
  assert.match(out[0], /\/booking\//, "the title saying 'demo' would have been parroted, and vet() would have binned the answer");
});

test("the drop follows the rule's scope, exactly like the forbidden list and vet() do", () => {
  const scoped = { rules: [{ id: "demo", keywords: ["demo"], media: { mode: "only", ids: ["post_A"] }, dm: { text: "x" }, publicReply: "y" }] };
  siteIndex.load(index([page({ title: "Book a demo of the booking flow", url: "/blog/en/demo/", keywords: ["bookings"] })]), { url: URL });

  assert.equal(ask("how does online booking work?", { rulesConfig: scoped, mediaId: "post_A" }).length, 0, "here the word is banned");
  assert.equal(ask("how does online booking work?", { rulesConfig: scoped, mediaId: "post_C" }).length, 1, "here no rule can fire, so nothing needs dropping");
});

test("the Arabic keyword drop works the same way, because the matcher does", () => {
  siteIndex.load(index([page({ title: "تجربة الذكاء الاصطناعي في مسقط", url: "/blog/ar/x/", lang: "ar", keywords: ["مسقط"] })]), { url: URL });
  assert.equal(ask("الذكاء الاصطناعي في مسقط", { lang: "ar", rulesConfig: RULES, mediaId: "" }).length, 0);
});

/* ---------------------------------------------------------------------------
 * The caps
 * ------------------------------------------------------------------------- */

test("the page cap holds", () => {
  const pages = ["a", "b", "c", "d", "e"].map((k) => page({ title: `WhatsApp automation ${k}`, url: `/blog/en/${k}/` }));
  siteIndex.load(index(pages), { url: URL });

  assert.equal(ask("whatsapp automation").length, 3, "the shipped default");
  assert.equal(ask("whatsapp automation", { config: { maxPages: 1 } }).length, 1);
  assert.equal(ask("whatsapp automation", { config: { maxPages: 0 } }).length, 0);
});

test("the character cap holds, newlines included", () => {
  const pages = ["a", "b", "c", "d"].map((k) =>
    page({ title: `WhatsApp automation ${k}`, url: `/blog/en/${k}/`, desc: "x".repeat(400) })
  );
  siteIndex.load(index(pages), { url: URL });

  for (const maxChars of [1000, 300, 120]) {
    const out = ask("whatsapp automation", { config: { maxChars } });
    const block = out.join("\n");
    assert.ok(block.length <= maxChars, `${block.length} chars against a cap of ${maxChars}`);
  }
});

test("a description is cut to fit rather than the whole entry being dropped", () => {
  siteIndex.load(
    index([page({ title: "WhatsApp automation", url: "/blog/en/a/", desc: `${"word ".repeat(80)}end.` })]),
    { url: URL }
  );
  const out = ask("whatsapp automation", { config: { maxChars: 200 } });
  assert.equal(out.length, 1);
  assert.ok(out[0].length <= 200);
  assert.ok(out[0].endsWith("…"), "cut, and visibly cut");
});

test("no budget at all is not a half-written entry", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation", url: "/blog/en/a/" })]), { url: URL });
  assert.deepEqual(ask("whatsapp automation", { config: { maxChars: 10 } }), []);
});

/* ---------------------------------------------------------------------------
 * Housekeeping
 * ------------------------------------------------------------------------- */

test("two callers asking at once share one download", async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls++;
    return { ok: true, status: 200, json: async () => index([page({ title: "WhatsApp automation" })]) };
  };
  const c = cfg();
  await Promise.all([siteIndex.refresh(c, { fetchImpl }), siteIndex.refresh(c, { fetchImpl })]);
  assert.equal(calls, 1, "a boot fetch and the first timer tick must not both pull 700KB");
});

test("stats say the two things worth knowing: how many, and how old", () => {
  siteIndex.load(index([page({ title: "WhatsApp automation" }), page({ title: "Is $2,000 worth it?" })]), { url: URL });
  const s = siteIndex.stats();
  assert.equal(s.loaded, true);
  assert.equal(s.pages, 1);
  assert.equal(s.seen, 2);
  assert.equal(s.dropped.figure, 1);
  assert.equal(s.generated, "2026-09-05T08:00:11Z");
  assert.equal(s.ageMinutes, 0);
});
