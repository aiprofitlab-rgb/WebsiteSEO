# Recurring billing — what exists, and the one question that decides it

Three things we sell recur: the Growth Desk (OMR 75/month), the Assigned Admin
(OMR 37/month, taken on the checkout by ticking a sentence) and the Visibility
Desk (OMR 97/month, sold only by the checkout's upsell). A buyer can take more
than one, and the subscription bills their **sum** under a label naming all of
them. Everything else we sell is a one-off build. This is the infrastructure
for charging those fees, and an honest account of what is proven and what
is not.

## The short version

**Thawani can save a card. Whether it can charge that card *unattended* is
unconfirmed, and that single answer decides whether we have subscriptions or
one-click repeat payments.**

Ask Thawani. Until they answer, `pay.py` correctly says a monthly item is
invoiced monthly, and nothing on the site claims otherwise.

## What is verified (UAT, 2026-08-24)

| Step | Call | Result |
|---|---|---|
| Create a customer | `POST /customers` | `code 2001`, `cus_J1q3bOm816NL5xUl` |
| Save their card | `POST /checkout/session` with `customer_id` + `save_card_on_success: true` | accepted, and **echoed back true** on retrieve |
| List saved cards | `GET /payment_methods?customer_id=…` | `code 4003` when none — an ordinary state, not an error |
| Create an intent | `POST /payment_intents` | `code 2001`, `pi_…`, `status: requires_payment_method` |

Amount limits, found by asking the API to refuse:

- **Checkout session**: `unit_amount` between **1 and 5,000,000 baisa** (OMR 5,000) *per product line*; a 50-baisa session is refused, so the floor is 100 baisa.
- **Payment intent**: `amount` between **100 and 9,999,000 baisa** (OMR 0.100–9,999).

Both sit far above anything we sell. The dearest thing in the catalog is the
Operator Stack at OMR 2,200. **This closes the open
"per-transaction ceiling" question in `docs/payments-api.md`.**

A payment intent **expires 30 minutes** after creation, so it must be created
and confirmed in one run — never created by one job and confirmed by a later one.

## The unverified step, and why it matters

Thawani's own mini document describes the saved-card flow as ending:

> take the payment intent ID and do it on confirmation … **then take the user to
> OTP URL received on the confirm response.**

If an OTP is required on *every* saved-card charge, Thawani does not offer
unattended recurring billing. What it offers is one-click repeat payment, which
still needs the customer awake, holding their phone, at the moment we bill. You
cannot build a subscription on that without asking the customer to approve every
month.

Confirming an intent needs a real saved card, and saving a card needs somebody to
actually pay on the hosted page — so this cannot be settled from a terminal. It
is question 1 on the list to Thawani.

## How the code handles not knowing

`lib/subscriptions.js` is written to be correct under either answer:

- **Confirm completes** → the cycle advances, `cycles` increments, `nextChargeAt`
  moves on a month. That is money.
- **Confirm asks for the cardholder** → status becomes `Needs_Customer_Action`,
  the OTP link is stored, and **the cycle does not advance**. Nothing is reported
  as paid, because nothing was paid.

The outcomes are `paid | needs_action | no_card | failed | skipped`, and only
`paid` is money. A subscription that wrongly believes it charged someone is worse
than one that asks a human to look.

## The billing run

`POST /billing/run` — woken by Cloud Scheduler once a day, never by a browser.

- **Refuses to exist without `CRON_KEY`.** No default, no "open in development"
  branch: an unprotected billing trigger is one curl away from charging every
  customer we have. Verified: 503 with no key set, 403 on a near-miss key.
- `?dry=1` selects and reports what *would* be charged without touching the
  gateway. Run that first, every time, until this has real months behind it.
- Never mounted in CORS. No page should ever call it.

**Recurring billing needs `CHECKOUT_SHEET_ID` set.** Logs are fine for recording
an order and useless as a thing to query next month, so with no sheet the runner
reports zero due rather than inventing a schedule.

## The schedule arithmetic

`nextCycle()` clamps to the last real day of the target month. This is not
fussiness: `new Date(2026, 8, 31)` is the 1st of October, so a naive month-add
turns a 31st anchor into a 1st, then a 2nd, and a subscription that started on
the 31st ends up billing on the 3rd. The anchor day is stored and clamped, never
walked. Tested across twelve months and a leap year.

## What a signup does today

An order containing a monthly item now:

1. creates a Thawani customer (`apl-<reference>`),
2. stores `cus_…` on the order **the moment it exists** — it is the only handle
   on the saved card, and losing it means asking the buyer to sign up again,
3. sends the checkout session with `customer_id` and `save_card_on_success: true`,
   so the card is kept when they pay,
4. records the subscription as `Pending_Card` with **no** `nextChargeAt` — a
   monthly item bills from go-live, not from the day a deposit is paid.

If customer creation fails, the order **carries on** as a plain session. Taking
the build payment and invoicing the monthly items by hand is a worse month for
Nahid; losing the whole order is worse for everyone.

## A trap worth knowing

**Thawani silently ignores unknown fields.** A session posted with
`totally_made_up_field_xyz` still returns `2004 Session generated successfully`.
A typo in a field name does not error — it quietly does nothing, and you find out
next month when there is no card to charge.

The only way to prove a field landed is to read it back off the retrieved
session. That is how `save_card_on_success` was confirmed real, and it is the
check to repeat for any field added later.
