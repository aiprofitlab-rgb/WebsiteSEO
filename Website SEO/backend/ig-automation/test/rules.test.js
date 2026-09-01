/**
 * Comments arrive shouty, mentioned, emoji'd and in Arabic. The matcher has to
 * survive that without matching things it shouldn't.
 */
const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");

const rules = require("../lib/rules");
const config = JSON.parse(require("node:fs").readFileSync(path.join(__dirname, "..", "rules.json"), "utf8"));

const hit = (text) => {
  const m = rules.match(text, config);
  return m && m.rule.id;
};

test("the shipped rules.json is internally consistent", () => {
  assert.deepEqual(rules.validate(config), [], "no missing ids, empty keywords, or shadowed rules");
});

test("case, punctuation and emoji do not stop a match", () => {
  assert.equal(hit("storefront"), "storefront");
  assert.equal(hit("STOREFRONT"), "storefront");
  assert.equal(hit("Storefront!!!"), "storefront");
  assert.equal(hit("storefront 🔥🔥"), "storefront");
  assert.equal(hit("I want the STOREFRONT please"), "storefront");
});

test("a leading @mention is not matched against — handles are not keywords", () => {
  assert.equal(hit("@aiprofitlab storefront"), "storefront");
  assert.equal(hit("@storefront_designs nice work"), null, "the keyword only appears inside a handle");
});

test("a keyword inside a longer word does not match", () => {
  assert.equal(hit("restore the site"), null, "'store' inside 'restore'");
  assert.equal(hit("storefronts"), null, "plural is a different word; add it explicitly if wanted");
  assert.equal(hit("pricing"), "price", "but 'pricing' is its own configured keyword");
});

test("Arabic matches with the definite article, a leading waw, tatweel and diacritics", () => {
  assert.equal(hit("متجر"), "storefront");
  assert.equal(hit("المتجر"), "storefront", "ال prefix");
  assert.equal(hit("والمتجر"), "storefront", "و + ال prefix");
  assert.equal(hit("مـتـجـر"), "storefront", "tatweel-stretched");
  assert.equal(hit("سعر"), "price");
  assert.equal(hit("السعر كم؟"), "price");
});

test("Arabic alef and yeh variants normalise to one form", () => {
  assert.equal(rules.normalise("أسعار"), "اسعار");
  assert.equal(rules.normalise("مصطفى"), "مصطفي");
});

test("zero-width characters pasted in from a notes app do not break matching", () => {
  // Stripped before matching, so an invisible character sitting inside the word
  // rejoins it rather than hiding it. This is the point of the strip.
  assert.equal(hit("store​front"), "storefront", "ZWSP inside the word");
  assert.equal(hit("​storefront​"), "storefront", "ZWSP padding");
  assert.equal(hit("﻿storefront"), "storefront", "a BOM pasted in from a text file");
});

test("ordinary comments match nothing", () => {
  for (const s of ["nice post", "🔥🔥🔥", "", "   ", "where are you based?"]) {
    assert.equal(hit(s), null, `"${s}" should not fire a rule`);
  }
});

test("first matching rule wins, in file order", () => {
  const cfg = {
    rules: [
      { id: "first", keywords: ["go"], dm: { text: "a" } },
      { id: "second", keywords: ["go"], dm: { text: "b" } },
    ],
  };
  assert.equal(rules.match("go", cfg).rule.id, "first");
});

test("a disabled rule is skipped without disturbing the ones after it", () => {
  const cfg = {
    rules: [
      { id: "off", enabled: false, keywords: ["go"], dm: { text: "a" } },
      { id: "on", keywords: ["go"], dm: { text: "b" } },
    ],
  };
  assert.equal(rules.match("go", cfg).rule.id, "on");
});

test("exact and contains modes behave as documented", () => {
  const cfg = { rules: [{ id: "x", match: "exact", keywords: ["go"], dm: { text: "a" } }] };
  assert.ok(rules.match("GO", cfg));
  assert.equal(rules.match("go now", cfg), null);

  const cfg2 = { rules: [{ id: "y", match: "contains", keywords: ["store"], dm: { text: "a" } }] };
  assert.ok(rules.match("restore", cfg2), "contains deliberately matches inside words");
});

test("the DM carries text and link together, because there is only one message", () => {
  const rule = { dm: { text: "Here it is", link: "https://aiprofitlab.io/en/smart-storefront/" } };
  assert.equal(rules.dmText(rule), "Here it is\n\nhttps://aiprofitlab.io/en/smart-storefront/");
  assert.equal(rules.dmText({ dm: { link: "https://x.test" } }), "https://x.test");
  assert.equal(rules.dmText({}), "");
});

test("validate names the specific problem rather than just failing", () => {
  const problems = rules.validate({
    rules: [
      { id: "a", keywords: ["go"], dm: { text: "hi" } },
      { id: "a", keywords: [], match: "fuzzy" },
      { id: "c", keywords: ["go"], dm: { text: "hi" } },
    ],
  });
  assert.ok(problems.some((p) => p.includes("duplicate id")));
  assert.ok(problems.some((p) => p.includes("no keywords")));
  assert.ok(problems.some((p) => p.includes("unknown match mode")));
  assert.ok(problems.some((p) => p.includes("shadowed")), "rule c can never fire");
});

/* ---------------------------------------------------------------------------
 * Post targeting
 * ------------------------------------------------------------------------- */

const scoped = {
  rules: [
    { id: "reel", keywords: ["guide"], media: { mode: "only", ids: ["111", "222"] }, dm: { text: "reel guide" }, publicReply: "On its way 📩" },
    { id: "any", keywords: ["guide"], dm: { text: "generic guide" }, publicReply: "Sent 📩" },
  ],
};

test("post targeting picks the rule, and first-match-wins means first match that can fire HERE", () => {
  assert.equal(rules.match("guide", scoped, { mediaId: "111" }).rule.id, "reel");
  assert.equal(rules.match("guide", scoped, { mediaId: "999" }).rule.id, "any", "the targeted rule is invisible off its posts");
  assert.equal(rules.match("guide", scoped).rule.id, "reel", "with no post context, every rule is still considered");
});

test("a comment with no media id cannot trigger a rule that was narrowed to specific posts", () => {
  const onlyScoped = { rules: [scoped.rules[0]] };
  assert.equal(rules.match("guide", onlyScoped, { mediaId: "" }), null);
  assert.equal(rules.match("guide", onlyScoped, { mediaId: null }), null);
  assert.equal(rules.match("guide", onlyScoped, { mediaId: "222" }).rule.id, "reel");
});

test("rules on different posts do not shadow each other — that is the point of targeting", () => {
  const apart = {
    rules: [
      { id: "a", keywords: ["guide"], media: { mode: "only", ids: ["111"] }, dm: { text: "a" } },
      { id: "b", keywords: ["guide"], media: { mode: "only", ids: ["222"] }, dm: { text: "b" } },
    ],
  };
  assert.deepEqual(rules.validate(apart), []);

  const overlapping = JSON.parse(JSON.stringify(apart));
  overlapping.rules[1].media.ids = ["111", "222"];
  assert.ok(rules.validate(overlapping).some((p) => p.includes("shadowed")), "sharing one post is enough to shadow");
});

test("a public reply is only checked against the rules that run where it will appear", () => {
  const safe = {
    rules: [
      { id: "a", keywords: ["guide"], media: { mode: "only", ids: ["111"] }, dm: { text: "a" }, publicReply: "Sent 📩" },
      { id: "b", keywords: ["sent"], media: { mode: "only", ids: ["222"] }, dm: { text: "b" }, publicReply: "Done 📩" },
    ],
  };
  assert.deepEqual(rules.validate(safe), [], "rule a's reply lands on post 111, where rule b does not run");

  const unsafe = JSON.parse(JSON.stringify(safe));
  unsafe.rules[1].media.ids = ["111"];
  assert.ok(rules.validate(unsafe).some((p) => p.includes("reply loop")));
});

test("targeting turned on with nothing selected is an error, not a rule that quietly never fires", () => {
  const empty = { rules: [{ id: "a", keywords: ["guide"], media: { mode: "only", ids: [] }, dm: { text: "a" } }] };
  const problems = rules.inspect(empty);
  assert.ok(problems.some((p) => p.severity === "error" && /no posts are selected/.test(p.message)));
});

test("inspect separates what blocks a save from what is merely worth knowing", () => {
  const config = {
    rules: [
      { id: "a", keywords: ["guide"], dm: { text: "hi" } },
      { id: "b", keywords: ["guide"], dm: { text: "hi" } },
      { id: "c", keywords: ["price"], dm: { link: "aiprofitlab.io/pricing" } },
    ],
  };
  const problems = rules.inspect(config);
  assert.equal(problems.find((p) => /shadowed/.test(p.message)).severity, "warn");
  assert.equal(problems.find((p) => /not an http/.test(p.message)).severity, "error");
  assert.equal(rules.isSafeToSave(config), false);
});

test("an attached file rides inside the one message Meta allows", () => {
  const rule = { dm: { text: "Here it is", link: "https://aiprofitlab.io/x/" } };
  assert.equal(
    rules.dmText(rule, { fileUrl: "https://hooks.aiprofitlab.io/f/abc/guide.pdf" }),
    "Here it is\n\nhttps://aiprofitlab.io/x/\n\nhttps://hooks.aiprofitlab.io/f/abc/guide.pdf"
  );
  assert.equal(rules.dmText(rule, {}), "Here it is\n\nhttps://aiprofitlab.io/x/", "a missing file just drops out");
  assert.equal(rules.hasPayload({ dm: { fileId: "abc" } }), true, "a file alone is a payload");
  assert.equal(rules.hasPayload({ dm: { text: "  " } }), false);
});
