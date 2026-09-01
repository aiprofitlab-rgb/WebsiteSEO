# The checkout API — contract, and how to switch it on

The v4 checkout is built and shipping, and **the server that takes the money is
now written** — `backend/checkout-api/`, running against Thawani's UAT
environment. What is still missing is merchant approval and live keys.

This is the contract the front end calls and the server satisfies.

Nothing here is guesswork about Thawani. The request shapes were read off a
production integration, cross-checked against Thawani's own Create Session
documentation, and since 2026-08-24 **exercised against `uatcheckout.thawani.om`
with the UAT credentials from the Thawani Mini Document**. Findings from that
run are marked *verified UAT*. What is still not verified is called out as such.

---

## 1. Where things stand

| Piece | State |
|---|---|
| `public_html/en/checkout-v4.html` | built, `noindex`, reachable at `/en/checkout-v4/` |
| `public_html/en/order-v4.html` | built, `noindex`, reachable at `/en/order-v4/` |
| `public_html/terms.html` | live and indexable at `/terms/` |
| Pricing table | `tools/v4/pay.py` — one source of truth |
| Card gateway | **off** (`pay.PAY_LIVE = False`, `pay.PAY_API = ""`) |
| Checkout API | **written**, `backend/checkout-api/`, not deployed |
| Price table shipped to it | `backend/checkout-api/catalog.json`, exported by the build |
| UAT round trip | session created, metadata round-tripped, status read back |
| Card-on-file | customer + `save_card_on_success` verified; charge step unproven |
| Billing runner | `POST /billing/run`, `CRON_KEY`-locked, needs a sheet |

With the gateway off, the checkout is fully functional: it prices the order,
stamps it with a reference, and hands the whole thing to WhatsApp or email. No
copy anywhere claims a card can be taken. That is deliberate — see the header
comment in `tools/v4/pay.py`.

---

## 2. The two calls the front end makes

The browser talks **only** to our own API. It never sees a Thawani key, and
never posts a card number anywhere — the buyer types the card on Thawani's own
hosted page.

### `POST {PAY_API}/session`

Body — exactly what `order()` in `page_checkout.py` builds:

```json
{
  "reference": "APL-260820-KX7M",
  "items": ["dashboard", "autopilot", "desk"],
  "plan": "deposit",
  "currency": "OMR",
  "quoted_due": 100000,
  "quoted_total": 2200000,
  "customer": {
    "name": "Khalid Al Balushi",
    "business": "Gulf Lotus Trading LLC",
    "email": "khalid@gulflotus.om",
    "whatsapp": "+968 9123 4567",
    "cr": "1234567",
    "city": "Muscat",
    "notes": "…"
  },
  "page": "/en/checkout-v4/?plan=deposit"
}
```

All money is **integer baisa** (1 OMR = 1000 baisa).

`quoted_due` and `quoted_total` are what the buyer was *shown*. The server
**must recompute both from its own copy of the price table and refuse the
session if they disagree** — never charge the client's number, and never
silently substitute its own. A mismatch means the deployed page and the
deployed server are on different price tables, which is worth stopping for.

Response, 200:

```json
{
  "redirect_url": "https://checkout.thawani.om/pay/<session_id>?key=<publishable_key>",
  "session_id":   "<session_id>",
  "reference":    "APL-260820-KX7M"
}
```

Any non-200, or a 200 without `redirect_url`, drops the page into its offline
handover — the buyer is told nothing was charged and the order goes to WhatsApp
instead. Send `{"message": "…"}` on failure; it is shown to the buyer, so write
it for a buyer.

The page also gives up after **15 seconds** and falls back the same way. A
slow server therefore costs an order, not a hang.

### `GET {PAY_API}/session/{session_id}`

Called by `/en/order-v4/` after the redirect back.

```json
{
  "payment_status": "paid",
  "reference": "APL-260820-KX7M",
  "amount": 100000,
  "amount_display": "OMR 100"
}
```

`payment_status` is passed through from Thawani: `paid`, `unpaid`, or
`cancelled`. The page only says "payment received" — and only fires the GA4
`purchase` event — when this returns `paid`. Until this endpoint exists, every
successful return sits on "confirming your payment", which is true.

This endpoint is read by an anonymous browser, so it must return **only** the
four fields above. No customer object, no Thawani payload, no other order's
data. Treat `session_id` as a bearer token for one order and nothing more.

---

## 3. Talking to Thawani

Base URLs:

| Environment | Base |
|---|---|
| UAT | `https://uatcheckout.thawani.om` |
| Production | `https://checkout.thawani.om` |

### Create a session

```
POST {base}/api/v1/checkout/session
Content-Type: application/json
Thawani-Api-Key: {SECRET_KEY}
```

```json
{
  "client_reference_id": "APL-260820-KX7M",
  "products": [
    {"name": "The Smart Website", "unit_amount": 950000, "quantity": 1}
  ],
  "success_url": "https://aiprofitlab.io/en/order-v4/?status=success&ref=APL-260820-KX7M&session={session_id}",
  "cancel_url":  "https://aiprofitlab.io/en/order-v4/?status=cancel&ref=APL-260820-KX7M",
  "metadata": {
    "order_id": "APL-260820-KX7M",
    "customer_name": "Khalid Al Balushi",
    "customer_email": "khalid@gulflotus.om",
    "customer_phone": "96891234567",
    "customer_business": "Gulf Lotus Trading LLC",
    "customer_cr": "1234567",
    "customer_city": "Muscat",
    "plan": "deposit",
    "items": "website,dashboard,autopilot",
    "order_amount": "100000 of 2200000 baisa"
  }
}
```

Constraints that bite:

- **`metadata` takes at most 10 items** — *verified UAT*, the hard way. An
  eleventh key does not get dropped; it fails the whole session:

  ```json
  {"success": false, "code": 4000, "description": "Invalid information",
   "data": {"error": [{"field": "metadata",
                       "message": "Metadata cant have more than 10 items"}]}}
  ```

  A session that fails is an order that falls back to WhatsApp, so the ten keys
  are a budget to spend deliberately, not a limit to discover in production.
  That is why the three money figures share one `order_amount` key instead of
  taking three slots — it buys back room for the buyer's CR number and city.
  No value-length limit is published; `lib/thawani.js` caps values at 100
  characters on its own judgement.

- **The metadata round-trips intact** — *verified UAT*. `GET
  /checkout/session/{id}` returns the full object, which is what lets the
  payment-landed alert name the buyer without consulting the ledger at all.

- The buyer's free-text `notes` is **not** sent. It is unbounded prose typed
  into a form, and Thawani is a payment processor, not our CRM. It goes to the
  ledger.

- **`unit_amount` is an integer number of baisa.** 20 OMR is `20000`. Decimals
  are rejected. This is why `pay.py` holds every price as baisa and never
  divides — build the line items with integer arithmetic on the server too.
- **`name` is truncated at 40 characters.** `pay.check_services()` already
  fails the build if any catalog name grows past 40, so the names in
  `pay.CATALOG` are safe to send as-is.
- `success_url` / `cancel_url` must be absolute `https://` URLs. Put the
  reference in them — the redirect back carries no body.
- A session is **single-use and expires after 24 hours** — *verified UAT*: the
  response carries `expire_at` exactly 24h out, and `mode: "payment"`.

- **The products array is what gets charged**, not any total we declare. So the
  lines must sum to exactly the amount due. An order paid in full is itemised;
  a deposit or an instalment is one honest line, because a slice of a total has
  no itemisation. `lib/thawani.js` throws rather than send a list that does not
  add up.

Success response carries `code: 2004`:

```json
{"success": true, "code": 2004, "data": {"session_id": "…", "invoice": "…"}}
```

Anything other than `2004` is a failure; `description` holds the reason. Log it
with the reference and return a buyer-readable `message`.

Then redirect the buyer to:

```
{base}/pay/{session_id}?key={PUBLISHABLE_KEY}
```

Note the two different keys: the **secret** key authenticates the API call
server-side and must never leave the server; the **publishable** key appears in
the redirect URL and is meant to be seen.

### Check a payment

```
GET {base}/api/v1/checkout/session/{session_id}
Thawani-Api-Key: {SECRET_KEY}
```

`data.payment_status` is `paid` / `unpaid` / `cancelled`. Success here is
`code: 2000`, not 2004 — *verified UAT*. The response also carries
`client_reference_id`, `total_amount`, `invoice` and the full `metadata`, which
between them are enough to identify an order with no local state at all.

**Do not treat the return redirect as proof of payment** — always ask this
endpoint. `/en/order-v4/` is built on that assumption and will not claim a
payment succeeded without it.

### Recurring payments

The Growth Desk's monthly fee needs card-on-file, which is Thawani's 2nd
scenario. Create a customer, pass `customer_id` and `save_card_on_success: true`
on the session, then charge later through a payment intent against the saved
card. The infrastructure for this is built —
`backend/checkout-api/SUBSCRIPTIONS.md` has the verified call-by-call detail
and the one open question, which is whether a saved-card charge needs the
cardholder to complete an OTP every time. If it does, Thawani offers one-click
repeat payment rather than unattended subscriptions.

**A trap that applies to every call on this page: Thawani silently ignores
unknown fields.** A session posted with `totally_made_up_field_xyz` still
returns `2004 Session generated successfully` — *verified UAT*. A misspelled
field name does not error, it quietly does nothing. The only proof a field
landed is reading it back off the retrieved session.

### Not verified

- **Webhooks.** Thawani's docs list them, but the signature scheme is
  unconfirmed and the service does not implement them — trusting an
  unauthenticated callback about money is not worth the convenience. `GET
  /session/{id}` polling is the source of truth; reconcile against the Thawani
  merchant portal daily.
- ~~**Per-transaction ceilings.**~~ **Settled** — *verified UAT* by asking the
  API to refuse. Checkout session: `unit_amount` between **1 and 5,000,000
  baisa** (OMR 5,000) per product line, with a floor of 100 baisa on the
  session. Payment intent: `amount` between **100 and 9,999,000 baisa**
  (OMR 0.100–9,999). Both sit far above the dearest thing we sell (the
  Operator Stack, OMR 2,200), so a single card payment for a
  whole order is within limits. What is still unproven is whether an *acquirer*
  approves a charge that size — creation accepting the amount is not the bank
  accepting the payment, and only a paid test shows that.
- **Refunds via API.** Not checked. Assume refunds are done in the portal.

---

## 4. What the server does

All six of these are implemented in `backend/checkout-api/` — see its README.

1. Validates the body. Rejects anything without a name, business, email and
   phone, anything whose `items` are not in the catalog, and Pay on Proof,
   which is invoiced rather than charged.
2. **Re-prices the order from its own table** and compares against
   `quoted_due` / `quoted_total`. Refuses on mismatch, with a 409 and a
   buyer-readable message. `lib/pricing.js` is the port of `pay.quote()`, and
   `test/parity.test.js` runs `pay.py` itself over all 32 basket × plan
   combinations to prove the two have not drifted.
3. Writes the order to the ledger *before* calling Thawani, so an order exists
   even if the gateway call fails. A Google Sheet when `CHECKOUT_SHEET_ID` is
   set — same pattern as `storefront-offer-api/lib/sheet.js` — and one line of
   JSON on stdout either way, so the guarantee holds with no sheet at all.
4. Creates the Thawani session with the ten metadata keys, stores `session_id`
   and `invoice` against the order, returns the redirect. Idempotent on
   `reference`, so a double-click reuses the session it already made.
5. On `GET /session/{id}`, asks Thawani, updates the ledger, and returns the
   four public fields and nothing else.
6. Notifies — an email to Nahid the first time a session reads back `paid`,
   naming the buyer from the metadata Thawani hands back. An order nobody sees
   is worse than no order.

**Only a `paid` status is money.** Mirror the Smart Storefront's rule: nothing
counts until it is confirmed, and Nahid stays in the loop by hand.

### The price table gets there by export, not by hand

`tools/v4/export_catalog.py` writes `backend/checkout-api/catalog.json` straight
out of `pay.py`, and `tools/build_v4.py` runs it on every build. The arithmetic
is ported; the numbers are transported. Change a price and the exporter says out
loud that the file moved — which is the moment the service needs redeploying.

### Environment

See `backend/checkout-api/.env.example`. The UAT keys from the Thawani Mini
Document are in `.env.uat`, which is gitignored — `npm run smoke` uses it to put
a real session through UAT from this machine.

```
THAWANI_SECRET_KEY=…       # server only, never sent to a browser
THAWANI_PUBLISHABLE_KEY=…  # appears in the redirect URL
THAWANI_BASE=https://uatcheckout.thawani.om
SITE_ORIGIN=https://aiprofitlab.io
ALLOWED_ORIGINS=https://aiprofitlab.io
CHECKOUT_SHEET_ID=…        # optional; without it, orders go to the logs
RESEND_API_KEY=…           # optional; without it, alerts are logged and skipped
```

CORS must be an allowlist of exactly that origin — this endpoint creates
payment sessions, so an open `*` invites strangers to mint them. Rate-limit
`POST /session` per IP, and make it idempotent on `reference` so a double-click
does not create two sessions.

Deploy alongside the existing service:

```
gcloud run deploy checkout-api --source . --region me-central1 --project aiprofitlab-offer
```

(`--source` because there is no local Docker on this Mac. Watch the zsh comma
escaping on `--set-env-vars` — quote the whole value.)

---

## 5. Switching it on

In `tools/v4/pay.py`:

```python
PAY_LIVE    = True
PAY_API     = "https://checkout-api-….me-central1.run.app"
THAWANI_ENV = "live"          # "uat" shows a TEST MODE banner on the checkout
```

Then `python3 tools/build_v4.py` and deploy. That one edit changes, in the same
build:

- the checkout button, from "Reserve my slot" to "Pay OMR 100 securely"
- the note under it, to the hosted-payment-page wording
- the services page, from "paid up front by bank transfer" to "by card or bank transfer"
- the contact FAQ answer about how to pay

Because it is one switch, none of those four can be left saying the old thing.

### Before flipping it

- [ ] Thawani merchant account approved, live keys issued
- [ ] `npm test` green in `backend/checkout-api/` (the parity check is the one
      that matters — it proves the service prices an order the way the page did)
- [ ] `checkout-api` deployed, `GET /health` answering
      (**not** `/healthz` — Cloud Run's frontend intercepts that path)
- [ ] A full UAT run: pay, land on `/en/order-v4/?status=success`, see it turn
      from "confirming" to "payment received"
- [ ] A cancelled run: land on `?status=cancel`, "Pick up where I left off"
      restores the configuration
- [ ] A refused-card run: page falls back to the WhatsApp handover, and says
      plainly that nothing was charged
- [ ] `/terms/`, `/refund-policy/` and `/privacy/` all live and linked in the
      footer of every page
- [ ] The v4 set's `noindex` removed *and* the pages it replaces given
      `noindex` **in the same deploy** — see `kit.HEAD`
- [ ] Decide what happens to the Smart Storefront seat-ladder prices, which are
      a different price model on the same site

### After flipping it

Watch the first live payment end to end before telling anyone the page exists.
HTML propagates in about ten minutes (`max-age=600`), so a wrong switch is ten
minutes from being fixed — but a wrong *charge* is not.
