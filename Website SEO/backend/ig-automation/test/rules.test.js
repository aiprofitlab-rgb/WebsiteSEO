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
