/**
 * What we hand Thawani about the buyer.
 */
const test = require("node:test");
const assert = require("node:assert");

const pricing = require("../lib/pricing");
const thawani = require("../lib/thawani");

const customer = {
  name: "Khalid Al Balushi",
  business: "Gulf Lotus Trading LLC",
  email: "khalid@gulflotus.om",
  whatsapp: "+968 9123 4567",
  cr: "1234567",
  city: "Muscat",
  notes: "We import kitchen equipment and quote by WhatsApp all day.",
};

function meta(items = ["website", "dashboard", "autopilot"], plan = "deposit") {
  const q = pricing.quote(items, plan);
  return thawani.metadata({
    reference: "APL-260824-KX7M",
    customer,
    quote: q,
    items: q.items.map((i) => i.id),
    priceColumn: "founding",
  });
}

test("customer metadata carries what a human needs to recognise the order", () => {
  const m = meta();
  assert.equal(m.order_id, "APL-260824-KX7M");
  assert.equal(m.customer_name, "Khalid Al Balushi");
  assert.equal(m.customer_email, "khalid@gulflotus.om");
  assert.equal(m.customer_business, "Gulf Lotus Trading LLC");
  assert.equal(m.customer_cr, "1234567");
  assert.equal(m.customer_city, "Muscat");
  assert.equal(m.plan, "deposit");
  assert.equal(m.items, "website,dashboard,autopilot");
  assert.equal(m.order_amount, "100000 of 2200000 baisa (founding)");
});

test("the phone number is sent in the shape Thawani's own example uses", () => {
  assert.equal(meta().customer_phone, "96891234567");
  assert.equal(thawani.phone("+968 9123 4567"), "96891234567");
  assert.equal(thawani.phone("0096891234567"), "96891234567");
  assert.equal(thawani.phone("91234567"), "96891234567", "a bare local number gets its country code");
  assert.equal(thawani.phone(""), "");
});

test("the buyer's free-text notes never reach the payment processor", () => {
  const m = meta();
  const blob = JSON.stringify(m);
  assert.ok(!blob.includes("kitchen equipment"), "notes must stay in the ledger");
});

test("metadata never exceeds Thawani's hard ceiling of ten items", () => {
  // Verified limit, not a guess: an eleventh key fails the whole session, so
  // this asserts the map is BUILT to fit rather than relying on truncation.
  assert.equal(thawani.META_MAX_KEYS, 10);
  const pricingLib = require("../lib/pricing");
  const baskets = [[], ["website"], ["website", "dashboard"], ["website", "dashboard", "autopilot"],
                   ["website", "dashboard", "autopilot", "desk"]];
  for (const p of pricingLib.CATALOG.plans.filter((x) => x.card)) {
    for (const items of baskets) {
      const m = meta(items, p.id);
      assert.ok(Object.keys(m).length <= 10, `${p.id}/${items.join("+")} sent ${Object.keys(m).length} keys`);
      for (const [k, v] of Object.entries(m)) {
        assert.ok(v.length <= thawani.META_MAX_VALUE, `${k} is ${v.length} chars`);
        assert.ok(v.length > 0, `${k} is empty and should have been dropped`);
      }
    }
  }
});

test("a full order with every detail filled in still fits", () => {
  const m = meta(["website", "dashboard", "autopilot", "desk"], "full");
  assert.equal(Object.keys(m).length, 10, "the budget is spent exactly, with nothing truncated away");
});

test("absent optional details are dropped, not sent as empty strings", () => {
  const q = pricing.quote(["website"], "full");
  const m = thawani.metadata({
    reference: "APL-260824-AAAA",
    customer: { name: "A", business: "B", email: "a@b.om", whatsapp: "91234567", cr: "", city: "", notes: "" },
    quote: q,
    items: ["website"],
    priceColumn: "founding",
  });
  assert.ok(!("customer_cr" in m));
  assert.ok(!("customer_city" in m));
});

test("a line-item list that does not sum to the amount due is refused", () => {
  const q = pricing.quote(["website"], "full");
  const broken = { ...q, plan: { ...q.plan, due: "nonsense" } };
  assert.throws(() => thawani.lineItems(broken, pricing.CATALOG), /line items sum to/);
});
