/**
 * The buyer's receipt.
 *
 * These run with no CHECKOUT_SHEET_ID, so every case here exercises the
 * METADATA-ONLY path — which is the one that has to hold up on a fresh deploy
 * before a ledger sheet is attached, and the one where a mistake means a
 * customer who paid four figures is told the wrong thing about what they owe.
 */

const test = require("node:test");
const assert = require("node:assert/strict");

const session = require("../routes/session");
const pricing = require("../lib/pricing");

const { buyerReceipt, NEXT_STEP } = session;

// The shape Thawani hands back on retrieve — build item ids only, because
// `q.items` is the build list. This is exactly why monthly cannot be recovered.
const meta = (over = {}) => ({
  order_id: "APL-260903-AHPF",
  customer_email: "khalid@gulflotus.om",
  plan: "deposit",
  items: "website,dashboard,autopilot",
  ...over,
});

test("a deposit receipt names the balance still to come", async () => {
  const r = await buyerReceipt("APL-260903-AHPF", meta(), "OMR 100");

  assert.equal(r.planLabel, "Reserve a build slot");
  assert.equal(r.amountDisplay, "OMR 100");
  // Operator Stack is 2,200; 100 down leaves 2,100.
  assert.equal(r.balanceDisplay, "OMR 2,100");
  assert.deepEqual(r.itemNames, ["The Smart Website", "The Live Owner Dashboard", "The Full Autopilot"]);
});

test("a paid-in-full receipt promises no balance at all", async () => {
  const r = await buyerReceipt("APL-260903-AHPF", meta({ plan: "full" }), "OMR 2,200");

  assert.equal(r.planLabel, "Pay in full");
  // The whole point of the plan. A balance line here would be a lie that costs
  // a support conversation at best.
  assert.equal(r.balanceDisplay, "");
  assert.match(r.nextStep, /Nothing further is owed/);
});

test("a three-payment receipt says what the other two are", async () => {
  const q = pricing.quote(["website"], "three");
  const r = await buyerReceipt("APL-260903-AHPF", meta({ plan: "three", items: "website" }), pricing.money(q.due));

  assert.equal(r.planLabel, "Three payments");
  assert.equal(r.balanceDisplay, pricing.money(q.balance));
  assert.match(r.nextStep, /nothing is taken from your card automatically/);
});

test("the monthly commitment is left empty rather than invented when there is no ledger", async () => {
  // The buyer took the Visibility Desk upsell, but metadata carries build items
  // only. Saying nothing is correct; guessing is not.
  const r = await buyerReceipt("APL-260903-AHPF", meta(), "OMR 100");
  assert.deepEqual(r.monthly, []);
});

test("an unknown plan still produces a sendable receipt", async () => {
  // Money has already moved by the time this runs. Throwing is not an option.
  const r = await buyerReceipt("APL-260903-AHPF", meta({ plan: "nonsense" }), "OMR 100");

  assert.equal(r.planLabel, "");
  assert.equal(r.balanceDisplay, "");
  assert.equal(r.nextStep, "I'll be in touch to confirm your brief and what happens from here.");
});

test("an unknown item id is dropped, not rendered as a blank bullet", async () => {
  const r = await buyerReceipt("APL-260903-AHPF", meta({ items: "website,made_up_thing" }), "OMR 100");
  assert.deepEqual(r.itemNames, ["The Smart Website"]);
});

test("every card-taking plan has its own next step", () => {
  // A generic "we'll be in touch" after a four-figure payment is the failure
  // this table exists to prevent, so every plan that can reach a receipt needs
  // a real entry.
  for (const p of pricing.CATALOG.plans.filter((x) => x.card)) {
    assert.ok(NEXT_STEP[p.id], `plan ${p.id} takes a card but has no next step`);
  }
});

/* ------------------------------------------------------------ kill switch -- */

const thawani = require("../lib/thawani");

test("cards are offered only when this service can actually take one", () => {
  const restore = { ...process.env };
  const enabled = () => thawani.config().enabled;

  process.env.THAWANI_SECRET_KEY = "s";
  process.env.THAWANI_PUBLISHABLE_KEY = "p";
  delete process.env.PAY_ENABLED;
  assert.equal(enabled(), true, "both keys and no override should accept cards");

  process.env.PAY_ENABLED = "0";
  assert.equal(enabled(), false, "PAY_ENABLED=0 must win even with valid keys");

  process.env.PAY_ENABLED = "1";
  process.env.THAWANI_SECRET_KEY = "";
  assert.equal(enabled(), false, "a missing secret key cannot take a card");

  process.env = restore;
});
