# checkout-api

Creates Thawani payment sessions for `/en/checkout-v4/`, and tells
`/en/order-v4/` what happened to them. The contract is
[`docs/payments-api.md`](../../docs/payments-api.md); this is the server that
satisfies it.

The browser talks only to this service. It never holds a Thawani key and never
posts a card number anywhere — the buyer types their card on Thawani's own
hosted page.

## Run it against UAT

```bash
npm install
npm test                 # 16 tests, including a live parity check against pay.py
npm run smoke            # a real session on uatcheckout.thawani.om
npm run dev              # the service itself, on :8080
```

`npm run smoke` prints the redirect URL and everything we told Thawani about the
buyer. Open the URL, pay with a [Thawani test card][cards], then:

```bash
npm run smoke -- status <session_id>
```

Other baskets: `npm run smoke -- full stack`, `npm run smoke -- three base`.

[cards]: https://thawani-technologies.stoplight.io/docs/thawani-ecommerce-api

## What it does with an order

1. **Validates** it. Name, business, email and phone are required; items must be
   in the catalog; the plan must be one that takes a card (Pay on Proof is
   invoiced, and is refused here on purpose).
2. **Re-prices it from its own table** and refuses on disagreement. The browser's
   `quoted_due` / `quoted_total` are never charged — they are only ever compared.
   A mismatch means the deployed page and this service were built from different
   price tables, and that is worth stopping for.
3. **Writes the order to the ledger before calling Thawani**, so a gateway
   failure leaves an order behind instead of a silence.
4. **Creates the Thawani session** with the customer metadata below, and returns
   the redirect.
5. On `GET /session/:id`, asks Thawani, updates the ledger, emails Nahid the
   first time a session reads back `paid`, and returns four public fields.

Only `paid` is money. The return redirect is not proof of anything — a buyer can
type the success URL.

## The customer metadata

This is what turns a Thawani portal row from an amount and a timestamp into a
recognisable order. Ten keys, sent on every session:

| key | example |
|---|---|
| `order_id` | `APL-260824-ACKY` |
| `customer_name` | `Khalid Al Balushi` |
| `customer_email` | `khalid@gulflotus.om` |
| `customer_phone` | `96891234567` |
| `customer_business` | `Gulf Lotus Trading LLC` |
| `customer_cr` | `1234567` |
| `customer_city` | `Muscat` |
| `plan` | `deposit` |
| `items` | `website,dashboard,autopilot` |
| `order_amount` | `100000 of 2200000 baisa` |

**Ten is a hard ceiling**, verified against UAT on 2026-08-24 — an eleventh key
fails the entire session with `Metadata cant have more than 10 items`, which
would cost a real order. That is why the three money figures share one key
rather than taking three. `lib/thawani.js` truncates as a backstop and the test
suite asserts every basket fits without needing it.

The buyer's free-text **notes are deliberately not sent**. Unbounded prose typed
into a form, on a payment processor that is not our CRM. It goes to the ledger,
which is where we read it.

`order_id` is the same reference the buyer sees on the checkout, quotes on
WhatsApp, and lands on at `/en/order-v4/` — one string tying the page, the
ledger and the Thawani record together. It is also sent as
`client_reference_id`, so it comes back on every retrieve.

## Recurring

The Growth Desk is OMR 75/month and is **not** charged at checkout. An order
containing it creates a Thawani customer and saves the buyer's card, so it
*can* be charged later. See **[SUBSCRIPTIONS.md](SUBSCRIPTIONS.md)** — including
the one unanswered question that decides whether real subscriptions are possible
on Thawani at all.

`POST /billing/run` is the monthly runner. It refuses to exist without
`CRON_KEY`, and `?dry=1` reports what would be charged without touching the
gateway.

## Prices

`catalog.json` is **generated** — `tools/v4/export_catalog.py` writes it out of
`tools/v4/pay.py`, and `tools/build_v4.py` runs the exporter on every build.
Never hand-edit it. Change a price in `pay.py`, rebuild, and the exporter says
out loud when the file moved, because that is the moment this service needs
redeploying.

`lib/pricing.js` is a port of `pay.quote()`, and `test/parity.test.js` runs
`pay.py` itself and compares all 32 basket × plan combinations across all seven
money fields. A port that drifts silently is a port that charges the wrong
number.

Money is **integer baisa** end to end (1 OMR = 1000 baisa). Thawani's
`unit_amount` rejects decimals. There is no float anywhere in the pricing path.

## The line-item invariant

Thawani charges the **sum of the products array**, not any total we declare. So
the lines must sum to exactly what is due, and `lib/thawani.js` throws rather
than send a list that does not. An order paid in full is itemised, because the
buyer should recognise their own basket on the hosted page; every other plan is
paying a slice of a total, and a slice gets one honest line.

The Growth Desk never appears — it is monthly, checkout takes a single payment,
and it is invoiced from go-live.

## The ledger is optional

With `CHECKOUT_SHEET_ID` set, orders go to a Google Sheet tab
(`Checkout_Orders`, created on boot) using the Cloud Run runtime service
account — the same pattern as the Smart Storefront's ledger.

Without it, every order still lands in the logs as one line of JSON, greppable
by reference. The guarantee that matters is that an order is recorded before a
payment session exists, and that holds either way. A spreadsheet being
unreachable never fails a checkout.

## Deploy

```bash
gcloud run deploy checkout-api --source . --region me-central1 \
  --project aiprofitlab-offer --allow-unauthenticated
```

`--source` because there is no local Docker on this Mac. Quote the whole value
on `--set-env-vars` — zsh eats the commas. Health check is **`/health`**, not
`/healthz`: Cloud Run's frontend intercepts that path and answers it with its
own 404 before the request reaches the container.

Environment: see `.env.example`. `THAWANI_SECRET_KEY` is server-only and must
never reach a browser; `THAWANI_PUBLISHABLE_KEY` appears in the redirect URL and
is meant to be seen. Two different keys — do not swap them.

Then, in `tools/v4/pay.py`, set `PAY_LIVE = True` and `PAY_API` to the service
URL, and rebuild. That one edit switches the checkout button, the note under it,
the services page and the contact FAQ together, so none can be left saying the
old thing.

## Verified, and not

Verified against `uatcheckout.thawani.om` on 2026-08-24:

- create session → `code: 2004`, `data.session_id` + `data.invoice`
- retrieve session → `code: 2000`, `data.payment_status`, `client_reference_id`,
  `total_amount`, and the full `metadata` object round-tripping intact
- metadata ceiling of 10 items, enforced, session-fatal
- a session expires 24h after creation (`expire_at`), `mode: "payment"`
- session creation accepts an OMR 2,200 order
- amount limits: session `unit_amount` 1–5,000,000 baisa per line (floor 100
  baisa on the session); payment intent `amount` 100–9,999,000 baisa
- card-on-file: `POST /customers` works, and `save_card_on_success` is real —
  confirmed by reading it back off the session, because **Thawani silently
  ignores unknown fields** and an accepted request proves nothing on its own
- a payment intent expires 30 minutes after creation

**Not verified:** whether a saved-card charge completes unattended or needs the
cardholder to finish an OTP every time — the question that decides whether the
Growth Desk can be a subscription. Also: that a card actually *clears* at OMR 2,200 — creation
accepting the amount is not the acquirer accepting the payment, and that needs a
paid test. Webhooks are not implemented (the signature scheme is unconfirmed, and
trusting an unauthenticated callback about money is not worth the convenience);
`GET /session/:id` polling is the source of truth. Refunds are done in the
portal.
