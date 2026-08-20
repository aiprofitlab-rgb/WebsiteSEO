# The checkout API — contract, and how to switch it on

The v4 checkout is built and shipping; the server that takes the money is not,
because the Thawani merchant account is still in application. This is the
contract the front end already calls, plus everything needed to write the
server once the keys arrive.

Nothing here is guesswork about Thawani: the request shapes below were read off
a production WooCommerce integration and cross-checked against Thawani's own
Create Session documentation. What is *not* verified is called out as such.

---

## 1. Where things stand

| Piece | State |
|---|---|
| `public_html/en/checkout-v4.html` | built, `noindex`, reachable at `/en/checkout-v4/` |
| `public_html/en/order-v4.html` | built, `noindex`, reachable at `/en/order-v4/` |
| `public_html/terms.html` | live and indexable at `/terms/` |
| Pricing table | `tools/v4/pay.py` — one source of truth |
| Card gateway | **off** (`pay.PAY_LIVE = False`, `pay.PAY_API = ""`) |
| Checkout API | not written |

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
  "founding": true,
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
    "customer_name": "Khalid Al Balushi",
    "customer_email": "khalid@gulflotus.om",
    "customer_phone": "96891234567",
    "order_id": "APL-260820-KX7M"
  }
}
```

Constraints that bite:

- **`unit_amount` is an integer number of baisa.** 20 OMR is `20000`. Decimals
  are rejected. This is why `pay.py` holds every price as baisa and never
  divides — build the line items with integer arithmetic on the server too.
- **`name` is truncated at 40 characters.** `pay.check_services()` already
  fails the build if any catalog name grows past 40, so the names in
  `pay.CATALOG` are safe to send as-is.
- `success_url` / `cancel_url` must be absolute `https://` URLs. Put the
  reference in them — the redirect back carries no body.
- A session is **single-use and expires after 24 hours** by default.

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

`data.payment_status` is `paid` / `unpaid` / `cancelled`.

**Do not treat the return redirect as proof of payment** — always ask this
endpoint. `/en/order-v4/` is built on that assumption and will not claim a
payment succeeded without it.

### Not verified

- **Webhooks.** Thawani's docs list them, but the integration read for this
  document polls the session endpoint instead. Until a webhook is confirmed
  working, treat the `GET /session/{id}` check as the source of truth, and
  reconcile against the Thawani merchant portal daily.
- **Per-transaction ceilings.** No published limit was found. Ask Thawani
  directly before relying on a single OMR 2,200 or OMR 3,400 card payment —
  if there is a ceiling, the slot deposit and the three-payment plan are
  already the way around it.
- **Refunds via API.** Not checked. Assume refunds are done in the portal.

---

## 4. What the server has to do

1. Validate the body. Reject anything without a name, business, email and
   phone, and anything whose `items` are not in the catalog.
2. **Re-price the order from its own table.** Port `pay.quote()` — the same
   function the page runs — and compare against `quoted_due` / `quoted_total`.
   Refuse on mismatch.
3. Write the order to a ledger *before* calling Thawani, so an order exists even
   if the gateway call fails. The Smart Storefront's Google Sheet ledger
   (`storefront-offer-api/lib/sheet.js`) is the working precedent.
4. Create the Thawani session, store `session_id` and `invoice` against the
   order, return the redirect.
5. On `GET /session/{id}`, ask Thawani, update the ledger, and return the four
   public fields.
6. Notify — an email and a WhatsApp to Nahid the moment a payment lands. An
   order nobody sees is worse than no order.

**Only a `paid` status is money.** Mirror the Smart Storefront's rule: nothing
counts until it is confirmed, and Nahid stays in the loop by hand.

### Environment

```
THAWANI_SECRET_KEY=…       # server only, never sent to a browser
THAWANI_PUBLISHABLE_KEY=…  # appears in the redirect URL
THAWANI_BASE=https://uatcheckout.thawani.om
SITE_ORIGIN=https://aiprofitlab.io
ALLOWED_ORIGINS=https://aiprofitlab.io
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
