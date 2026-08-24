/**
 * The Growth Desk's monthly fee — the recurring half of the business.
 *
 * WHAT IS AND ISN'T SETTLED
 *
 * Thawani's checkout takes ONE payment. Charging the same customer next month
 * means card-on-file: their card is saved during a checkout that carried a
 * `customer_id`, and later charges go through a payment intent against the
 * saved card. Every call in that chain is verified to exist and to accept the
 * shape we send (see lib/thawani.js).
 *
 * The open question is the last step, and it is a big one. Thawani's own mini
 * document says that after confirming an intent you "take the user to OTP URL
 * received on the confirm response". If that happens on EVERY saved-card
 * charge, then Thawani has no unattended recurring billing at all — what it has
 * is one-click repeat payment, which still needs the customer awake and holding
 * their phone. A subscription cannot be built on that without the customer
 * approving each month.
 *
 * So this module is written to be correct under both answers:
 *
 *   - It attempts the charge.
 *   - If the confirm completes, the cycle advances and it is money.
 *   - If the confirm asks for the cardholder, the subscription moves to
 *     NEEDS_ACTION, the customer is sent the OTP link, and NOTHING is reported
 *     as paid. The cycle does not advance.
 *
 * That is the difference between infrastructure that is ready and a billing
 * system that quietly believes it charged people. Until Thawani answers, the
 * honest description of what we have is "the Growth Desk is invoiced monthly",
 * which is what pay.py already says.
 */

const thawani = require("./thawani");
const pricing = require("./pricing");

const STATUS = {
  PENDING_CARD: "Pending_Card", // signed up, no saved card yet
  ACTIVE: "Active",
  NEEDS_ACTION: "Needs_Customer_Action", // an OTP the cardholder must complete
  PAST_DUE: "Past_Due",
  CANCELLED: "Cancelled",
};

// How many consecutive failed cycles before we stop trying and go and talk to
// them. Dunning by machine has a short honest limit.
const MAX_FAILURES = 3;

/** The monthly items in the catalog — today, just the Growth Desk. */
function monthlyItems() {
  return pricing.CATALOG.items.filter((i) => i.kind === "monthly");
}

/** What an order commits the buyer to every month, in baisa. */
function monthlyTotal(itemIds) {
  const ids = new Set(itemIds);
  return monthlyItems()
    .filter((i) => ids.has(i.id))
    .reduce((sum, i) => sum + i.price, 0);
}

/**
 * The next billing date, one month on, anchored to the day the subscription
 * started.
 *
 * The clamp is the whole reason this is a function and not `setMonth(+1)`. A
 * subscription anchored on the 31st has no 31st in September, and JavaScript's
 * answer to `new Date(2026, 8, 31)` is the 1st of October — which silently
 * walks the anchor forward a day every short month until a subscription that
 * started on the 31st is billing on the 3rd. Clamp to the last real day of the
 * target month and keep the original anchor.
 */
function nextCycle(from, anchorDay) {
  const d = new Date(from);
  const anchor = anchorDay || d.getUTCDate();
  const y = d.getUTCFullYear();
  const m = d.getUTCMonth();
  const lastDayOfNextMonth = new Date(Date.UTC(y, m + 2, 0)).getUTCDate();
  return new Date(Date.UTC(y, m + 1, Math.min(anchor, lastDayOfNextMonth), 12, 0, 0));
}

/** Is this subscription due to be charged as of `now`? */
function isDue(sub, now = new Date()) {
  if (sub.status !== STATUS.ACTIVE && sub.status !== STATUS.PAST_DUE) return false;
  if (!sub.nextChargeAt) return false;
  return new Date(sub.nextChargeAt).getTime() <= now.getTime();
}

/**
 * Charge one subscription for one cycle.
 *
 * Returns a plain result rather than throwing, because a billing run is a loop
 * over many subscriptions and one card being dead must not stop the rest.
 *
 * `outcome` is one of: paid | needs_action | no_card | failed | skipped.
 * Only `paid` is money, and only `paid` advances the cycle.
 */
async function chargeOnce(sub, { now = new Date(), returnUrl } = {}) {
  const base = { ref: sub.ref, amount: sub.amount, outcome: "failed", at: now.toISOString() };

  if (sub.status === STATUS.CANCELLED) return { ...base, outcome: "skipped", why: "cancelled" };
  if (!sub.customerId) return { ...base, outcome: "no_card", why: "no thawani customer on this subscription" };
  if (!Number.isInteger(sub.amount) || sub.amount < thawani.AMOUNT_MIN) {
    return { ...base, outcome: "skipped", why: `amount ${sub.amount} is below Thawani's floor` };
  }

  let cards;
  try {
    cards = await thawani.listPaymentMethods(sub.customerId);
  } catch (err) {
    return { ...base, why: `listing saved cards failed: ${err.message}` };
  }
  if (!cards.length) {
    return { ...base, outcome: "no_card", why: "customer has no saved card" };
  }

  // Newest usable card. A customer who re-saved after their old one expired
  // should be charged on the new one, not the dead one.
  const card = cards[cards.length - 1];
  const cardId = card.id || card.payment_method_id;
  if (!cardId) return { ...base, why: "saved card has no id" };

  try {
    // Created and confirmed in one go — an intent lives 30 minutes, so it must
    // never be created by one run and confirmed by a later one.
    const intent = await thawani.createPaymentIntent({
      amount: sub.amount,
      returnUrl,
      reference: sub.ref,
      paymentMethodId: cardId,
      customerId: sub.customerId,
      metadata: {
        order_id: sub.ref,
        customer_name: sub.name || "",
        customer_email: sub.email || "",
        plan: "growth_desk_monthly",
        cycle: String((sub.cycles || 0) + 1),
      },
    });

    const confirmed = await thawani.confirmPaymentIntent(intent.id);
    const read = thawani.readIntent(confirmed);

    if (read.paid) {
      return { ...base, outcome: "paid", intentId: intent.id, status: read.status };
    }
    if (read.needsCustomer) {
      // NOT a failure and NOT a payment. The cardholder has to finish it.
      return {
        ...base,
        outcome: "needs_action",
        intentId: intent.id,
        otpUrl: read.otpUrl,
        status: read.status,
        why: "Thawani asked for the cardholder to authorise this charge",
      };
    }
    return { ...base, intentId: intent.id, status: read.status, why: `intent ended as ${read.status}` };
  } catch (err) {
    return { ...base, why: err.message };
  }
}

/**
 * Apply a charge result to a subscription. Pure — it returns the new state
 * rather than writing anything, so it is testable without a ledger or a
 * gateway.
 */
function applyResult(sub, result) {
  const next = { ...sub };
  next.lastAttemptAt = result.at;

  if (result.outcome === "paid") {
    next.status = STATUS.ACTIVE;
    next.failures = 0;
    next.cycles = (sub.cycles || 0) + 1;
    next.lastChargeAt = result.at;
    next.nextChargeAt = nextCycle(new Date(sub.nextChargeAt || result.at), sub.anchorDay).toISOString();
    return next;
  }

  if (result.outcome === "needs_action") {
    // The cycle deliberately does NOT advance: nothing has been paid.
    next.status = STATUS.NEEDS_ACTION;
    next.pendingOtpUrl = result.otpUrl || "";
    return next;
  }

  if (result.outcome === "no_card") {
    next.status = STATUS.PENDING_CARD;
    return next;
  }

  if (result.outcome === "skipped") return next;

  next.failures = (sub.failures || 0) + 1;
  next.status = next.failures >= MAX_FAILURES ? STATUS.PAST_DUE : STATUS.PAST_DUE;
  return next;
}

/** A new subscription, from a checkout order that included a monthly item. */
function fromOrder({ reference, customerId, itemIds, customer, startAt = new Date() }) {
  const amount = monthlyTotal(itemIds);
  if (!amount) return null;
  const anchorDay = startAt.getUTCDate();
  return {
    ref: reference,
    customerId: customerId || "",
    amount,
    amountDisplay: pricing.money(amount),
    status: customerId ? STATUS.PENDING_CARD : STATUS.PENDING_CARD,
    name: (customer && customer.name) || "",
    email: (customer && customer.email) || "",
    business: (customer && customer.business) || "",
    anchorDay,
    startedAt: startAt.toISOString(),
    // The first monthly charge falls a month after go-live, not at checkout.
    // pay.py is explicit that the Growth Desk is "invoiced monthly from
    // go-live", and the build is not live on the day the deposit is paid.
    nextChargeAt: null,
    cycles: 0,
    failures: 0,
  };
}

module.exports = {
  STATUS,
  MAX_FAILURES,
  monthlyItems,
  monthlyTotal,
  nextCycle,
  isDue,
  chargeOnce,
  applyResult,
  fromOrder,
};
