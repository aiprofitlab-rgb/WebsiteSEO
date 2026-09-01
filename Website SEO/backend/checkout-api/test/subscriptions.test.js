/**
 * The recurring layer. No gateway is touched — chargeOnce() is the only part
 * that talks to Thawani, and it is the part that cannot be tested without a
 * real saved card. Everything around it is pure and is tested here.
 */
const test = require("node:test");
const assert = require("node:assert");

const subs = require("../lib/subscriptions");
const pricing = require("../lib/pricing");

const day = (iso) => new Date(iso + "T12:00:00Z");

test("the Growth Desk is the monthly item, at the published price", () => {
  const monthly = subs.monthlyItems();
  assert.equal(monthly.length, 1);
  assert.equal(monthly[0].id, "desk");
  assert.equal(subs.monthlyTotal(["website", "desk"]), 75 * pricing.OMR);
  assert.equal(subs.monthlyTotal(["website"]), 0, "an order with no monthly item owes nothing monthly");
});

test("a cycle anchored on the 31st does not walk forward through short months", () => {
  // The bug this exists to prevent: new Date(2026, 8, 31) is 1 October, so a
  // naive +1 month turns a 31st anchor into a 1st, then a 2nd, and so on.
  let d = day("2026-01-31");
  const anchor = 31;
  const seen = [];
  for (let i = 0; i < 12; i++) {
    d = subs.nextCycle(d, anchor);
    seen.push(d.toISOString().slice(0, 10));
  }
  assert.deepEqual(seen, [
    "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31", "2026-06-30", "2026-07-31",
    "2026-08-31", "2026-09-30", "2026-10-31", "2026-11-30", "2026-12-31", "2027-01-31",
  ]);
});

test("a February anchor survives a leap year", () => {
  assert.equal(subs.nextCycle(day("2028-01-30"), 30).toISOString().slice(0, 10), "2028-02-29");
  assert.equal(subs.nextCycle(day("2026-01-30"), 30).toISOString().slice(0, 10), "2026-02-28");
});

test("only active or past-due subscriptions with a date in the past are due", () => {
  const base = { nextChargeAt: "2026-08-01T12:00:00Z" };
  const now = day("2026-08-24");
  assert.equal(subs.isDue({ ...base, status: subs.STATUS.ACTIVE }, now), true);
  assert.equal(subs.isDue({ ...base, status: subs.STATUS.PAST_DUE }, now), true);
  assert.equal(subs.isDue({ ...base, status: subs.STATUS.CANCELLED }, now), false);
  assert.equal(subs.isDue({ ...base, status: subs.STATUS.NEEDS_ACTION }, now), false, "an unfinished OTP is not a licence to retry");
  assert.equal(subs.isDue({ ...base, status: subs.STATUS.PENDING_CARD }, now), false);
  assert.equal(subs.isDue({ nextChargeAt: "2026-09-01T12:00:00Z", status: subs.STATUS.ACTIVE }, now), false);
  assert.equal(subs.isDue({ nextChargeAt: null, status: subs.STATUS.ACTIVE }, now), false);
});

test("a paid cycle advances the schedule and clears failures", () => {
  const sub = { ref: "APL-1", status: subs.STATUS.PAST_DUE, failures: 2, cycles: 3,
                anchorDay: 15, nextChargeAt: "2026-08-15T12:00:00Z" };
  const after = subs.applyResult(sub, { outcome: "paid", at: "2026-08-24T09:00:00Z" });
  assert.equal(after.status, subs.STATUS.ACTIVE);
  assert.equal(after.failures, 0);
  assert.equal(after.cycles, 4);
  assert.equal(after.nextChargeAt.slice(0, 10), "2026-09-15", "the next cycle follows the schedule, not the payment date");
});

test("an OTP request is not a payment and must not advance the cycle", () => {
  const sub = { ref: "APL-2", status: subs.STATUS.ACTIVE, cycles: 1, anchorDay: 1,
                nextChargeAt: "2026-08-01T12:00:00Z" };
  const after = subs.applyResult(sub, { outcome: "needs_action", at: "2026-08-24T09:00:00Z", otpUrl: "https://otp" });
  assert.equal(after.status, subs.STATUS.NEEDS_ACTION);
  assert.equal(after.cycles, 1, "no cycle was completed");
  assert.equal(after.nextChargeAt, "2026-08-01T12:00:00Z", "still owed for the same month");
  assert.equal(after.pendingOtpUrl, "https://otp");
});

test("a missing card parks the subscription rather than counting a failure", () => {
  const sub = { ref: "APL-3", status: subs.STATUS.ACTIVE, failures: 0, nextChargeAt: "2026-08-01T12:00:00Z" };
  const after = subs.applyResult(sub, { outcome: "no_card", at: "2026-08-24T09:00:00Z" });
  assert.equal(after.status, subs.STATUS.PENDING_CARD);
  assert.equal(after.failures || 0, 0, "there is nothing to retry against");
});

test("failures accumulate and never advance the cycle", () => {
  let sub = { ref: "APL-4", status: subs.STATUS.ACTIVE, failures: 0, cycles: 2, nextChargeAt: "2026-08-01T12:00:00Z" };
  for (let i = 1; i <= subs.MAX_FAILURES; i++) {
    sub = subs.applyResult(sub, { outcome: "failed", at: "2026-08-24T09:00:00Z", why: "card declined" });
    assert.equal(sub.failures, i);
    assert.equal(sub.cycles, 2);
    assert.equal(sub.nextChargeAt, "2026-08-01T12:00:00Z");
  }
  assert.equal(sub.status, subs.STATUS.PAST_DUE);
});

test("a subscription from an order starts unbilled, awaiting a saved card", () => {
  const sub = subs.fromOrder({
    reference: "APL-260824-KX7M", customerId: "cus_abc",
    itemIds: ["website", "desk"],
    customer: { name: "Khalid", email: "k@g.om", business: "Gulf Lotus" },
    startAt: day("2026-08-24"),
  });
  assert.equal(sub.amount, 75 * pricing.OMR);
  assert.equal(sub.status, subs.STATUS.PENDING_CARD);
  assert.equal(sub.anchorDay, 24);
  assert.equal(sub.nextChargeAt, null, "the Growth Desk bills from go-live, not from checkout");
  assert.equal(sub.cycles, 0);
});

test("an order with no monthly item creates no subscription", () => {
  assert.equal(subs.fromOrder({ reference: "APL-1", customerId: "cus_x", itemIds: ["website", "dashboard"] }), null);
});

test("a subscription below Thawani's floor is skipped, not attempted", async () => {
  const r = await subs.chargeOnce({ ref: "APL-5", customerId: "cus_x", amount: 50, status: subs.STATUS.ACTIVE });
  assert.equal(r.outcome, "skipped");
});

test("a subscription with no customer id cannot be charged", async () => {
  const r = await subs.chargeOnce({ ref: "APL-6", customerId: "", amount: 75000, status: subs.STATUS.ACTIVE });
  assert.equal(r.outcome, "no_card");
});
