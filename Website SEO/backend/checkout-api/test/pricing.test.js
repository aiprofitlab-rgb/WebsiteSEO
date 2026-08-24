/**
 * The published figures, recomputed from the shipped table.
 *
 * This is the same list pay.py checks itself against in its __main__ block. If
 * a price moves in pay.py and catalog.json is not re-exported, these fail —
 * which is the point: the service must reach the number the buyer was shown.
 */
const test = require("node:test");
const assert = require("node:assert");

const pricing = require("../lib/pricing");
const thawani = require("../lib/thawani");

const OMR = pricing.OMR;
const base = ["website"];
const stack = ["website", "dashboard", "autopilot"];

test("published figures", () => {
  assert.equal(pricing.quote(base, "full").total, 950 * OMR, "Smart Website, paid in full");
  assert.equal(pricing.quote(base, "proof").total, 1150 * OMR, "Smart Website, pay on proof");
  assert.equal(pricing.quote(base, "three").total, 1020 * OMR, "Smart Website, three payments");
  assert.equal(pricing.quote(base, "three").due, 340 * OMR, "first of three");
  assert.equal(pricing.quote(base, "three").later, 340 * OMR, "each later payment");
  assert.equal(pricing.quote(base, "deposit").due, 100 * OMR, "deposit today");
  assert.equal(pricing.quote(base, "deposit").balance, 850 * OMR, "deposit balance");
  assert.equal(pricing.quote(stack, "full").total, 2200 * OMR, "Operator Stack in full");
  assert.equal(pricing.quote(stack, "full").saving, 300 * OMR, "Stack saving against the parts");
});

test("instalments always sum to the total", () => {
  for (const items of [base, ["website", "dashboard"], stack, ["website", "autopilot", "desk"]]) {
    const q = pricing.quote(items, "three");
    assert.equal(q.due + q.later * (q.plan.split - 1), q.total, `instalments for ${items.join("+")}`);
    assert.equal(q.later % OMR, 0, "later instalments are whole rials");
  }
});

test("the monthly item is never part of what is charged", () => {
  const withDesk = pricing.quote(["website", "desk"], "full");
  const without = pricing.quote(["website"], "full");
  assert.equal(withDesk.total, without.total);
  assert.equal(withDesk.monthly.length, 1);
  assert.equal(thawani.lineItems(withDesk, pricing.CATALOG).length, 1);
});

test("the base item is charged even if the browser omits it", () => {
  assert.equal(pricing.quote([], "full").total, 950 * OMR);
});

test("every line-item list sums to exactly what is due", () => {
  const plans = pricing.CATALOG.plans.filter((p) => p.card);
  const baskets = [[], base, ["website", "dashboard"], ["website", "autopilot"], stack, [...stack, "desk"]];
  for (const p of plans) {
    for (const items of baskets) {
      const q = pricing.quote(items, p.id);
      const lines = thawani.lineItems(q, pricing.CATALOG);
      const sum = lines.reduce((n, l) => n + l.unit_amount * l.quantity, 0);
      assert.equal(sum, q.due, `${p.id} / ${items.join("+") || "base only"}`);
      for (const l of lines) {
        assert.ok(l.name.length <= pricing.CATALOG.name_max, `"${l.name}" is over ${pricing.CATALOG.name_max} chars`);
        assert.ok(Number.isInteger(l.unit_amount) && l.unit_amount > 0, "integer baisa above zero");
      }
    }
  }
});

test("a full-price order is itemised, a part payment is one line", () => {
  assert.equal(thawani.lineItems(pricing.quote(stack, "full"), pricing.CATALOG)[0].name, "The Operator Stack");
  assert.equal(thawani.lineItems(pricing.quote(stack, "deposit"), pricing.CATALOG).length, 1);
  assert.equal(thawani.lineItems(pricing.quote(stack, "three"), pricing.CATALOG).length, 1);
  const unbundled = thawani.lineItems(pricing.quote(["website", "dashboard"], "full"), pricing.CATALOG);
  assert.equal(unbundled.length, 2);
});

test("money formatting", () => {
  assert.equal(pricing.money(950 * OMR), "OMR 950");
  assert.equal(pricing.money(2200 * OMR), "OMR 2,200");
  assert.equal(pricing.money(500), "OMR 0.500");
  assert.equal(pricing.money(0), "OMR 0");
});
