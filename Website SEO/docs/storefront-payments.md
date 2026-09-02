# The Smart Storefront seat payment — how a claim becomes money

The flyer campaign at `/en/smart-storefront/` used to end with a form that
dropped the buyer on a page whose only control was **"Upload a receipt"**, under
a promise of an invoice "within one business day". Somebody who has just typed
their details into a page reached from a printed flyer is at their most willing
right then; asking them to wait a day for the document they need in order to
pay was the most expensive sentence in the flow.

That flow now ends on a page that can take the money, and the invoice is sent by
the server the moment the seat is claimed.

This is a different service from the v4 checkout in
[`payments-api.md`](payments-api.md) — same gateway, same legal entity, separate
ledger and separate prices. See "Two payment paths" at the bottom.

---

## 1. Where things stand

| Piece | State |
|---|---|
| `public_html/en/pay.html` → `/en/pay/` | built, `noindex` |
| `/en/claim/` | 301 → `/en/pay/` (`.htaccess` §2b-ii); `en/claim.html` stays on disk |
| Proforma invoice on claim (PDF, emailed) | built, **needs `RESEND_API_KEY` on the service** |
| Paid invoice on payment (PDF, emailed) | built, fires only when the gateway reads back `paid` |
| Card payment | **off** — no Thawani keys on the service yet |
| Bank transfer + receipt upload | live, unchanged |
| Tests | `npm test` in the API — 58 pass |

Service: `storefront-offer-api`, a **systemd service on the Hostinger VPS**
(port 8092, behind Traefik at `https://offer.aiprofitlab.io`) since 2026-09-02.
Source: `AI Profit Lab/SmartChatBot/storefront-offer-api/` (a sibling of
`aiden-backend`, **not** in the website repo, and **not a git repo** — the
working tree is the only copy). The runbook is `deploy/DEPLOY.md` there.

It ran on Cloud Run (project `aiprofitlab-offer`, region `me-central1`) until
that date; the Cloud Run service was kept running in parallel for the cutover.
The tree still deploys to Cloud Run unchanged, which is what made that possible.

---

## 2. The flow

```
form on /en/smart-storefront/
   POST /claim ────────────────► row written  Status = Awaiting_Deposit
                                 PF-YYYY-NNNN proforma PDF rendered
                                 → buyer: "Your seat is held" + PDF attached
                                 → Nahid: new claim alert
   redirect ──► /en/pay/?ref=SS-XXXXXX&new=1
                   GET /claim/:ref ──► price, deposit, status, canPayByCard

  ┌── card on ─────────────────────────────────────────────────────────┐
  │  POST /pay/session ──► Thawani session ──► redirect to their page  │
  │  buyer pays ──► back to /en/pay/?ref=…&status=success              │
  │  GET /pay/status/:ref (polled) ──► gateway says "paid"             │
  │        → Status = Confirmed, INV-YYYY-NNNN allocated               │
  │        → buyer: paid invoice PDF · Nahid: payment-landed alert     │
  └────────────────────────────────────────────────────────────────────┘

  ┌── card off (today) ────────────────────────────────────────────────┐
  │  buyer replies to the invoice email · Nahid sends transfer details │
  │  POST /claim/:ref/receipt ──► Status = Deposit_Submitted           │
  │  Nahid sets Confirmed by hand once the transfer lands              │
  └────────────────────────────────────────────────────────────────────┘
```

**Only a gateway reading back `paid` confirms a seat automatically.** A
`?status=success` in the URL is not a receipt — a buyer can type it — so the page
sits on "confirming your payment" until `/pay/status/:ref` says otherwise, and
never claims a payment failed when what actually happened is that we could not
reach the gateway. A receipt photo still waits for Nahid. That gap is the reason
the public seat counter can honestly be called real.

---

## 3. Two invoice series, on purpose

| | allocated | gapless? | what it is |
|---|---|---|---|
| `PF-YYYY-NNNN` | at claim | no | a request for payment. A claim that never pays never becomes an invoice, so gaps are correct. |
| `INV-YYYY-NNNN` | at payment | **yes** | the accounting record and the receipt. Numbers are never burned by an abandoned claim. |

Both are issued by **Lotus Gulf International**, CR 1570092, TIN 2317725 — the
legal entity, never the brand. There is no VAT line and no VAT number, because
there is no registration; the document says so in words rather than printing a
0% line, which would imply a registration that does not exist.

**No bank details are printed on either PDF, or in any email.** An IBAN on a
document reachable from a stranger's printed flyer is how impersonation starts.
Transfer details are sent by Nahid, by hand, to someone he has spoken to.

---

## 4. Switching card payment on

One thing is missing: Thawani keys on the service. Everything else is deployed
and waiting for them.

```sh
sudo nano /etc/storefront-offer-api/.env
#   THAWANI_SECRET_KEY=<secret>
#   THAWANI_PUBLISHABLE_KEY=<publishable>
#   THAWANI_BASE=https://checkout.thawani.om
sudo systemctl restart storefront-offer-api
```

`THAWANI_BASE` is `https://uatcheckout.thawani.om` for testing and
`https://checkout.thawani.om` when live. **Never point the live site at UAT** —
UAT takes test cards, so a "payment" there would confirm a real seat and move
the public counter for nothing.

That one change makes the card button appear in three places at once, because
none of them holds an opinion of its own:

- the note under the claim form (`/status` → `pay.card`)
- the pay button on `/en/pay/` (`/claim/:ref` → `canPayByCard`)
- the "pay the deposit" button inside the claim email (`payEnabled`)

**Kill switch:** `PAY_ENABLED=0` hides the card route everywhere without
deleting credentials. `PAY_ENABLED=1` (or unset) restores it.

## 4b. Receipts

A deposit receipt is a photograph of somebody's bank transfer, carrying their
name and account number. On Cloud Run it went to a private GCS bucket and the
ledger stored a Cloud Console link, so Google's own login was the gate. Off GCP
neither half exists, so both were replaced on 2026-09-02:

- the file goes to `RECEIPTS_DIR` on the VPS, written `0600` in a `0700`
  directory under `/var/lib` — **never** under `/opt`, which a redeploy
  overwrites;
- the ledger stores `https://offer.aiprofitlab.io/receipts/<ref>/<file>`, which
  requires a password (`lib/auth.js` — scrypt, an HMAC session cookie, per-IP
  lockout; ported from the IG automation's admin panel).

**This is deliberately not the IG automation's `/f/<random>/` pattern.** That
one is public by design because Meta allows exactly one private reply per
comment, so a link is the only way to attach anything. Nothing about that
reasoning transfers to bank details.

Two consequences worth keeping in mind:

- **No password ⇒ no viewing routes at all.** Not "mounted without a password".
  Uploads still work and still land on disk, so setting it late loses nothing.
- **The VPS disk is the only copy.** There is no bucket behind it any more and
  the box has no backup, so losing the disk loses the receipts. Known and
  accepted (Nahid, 2026-09-02); the smallest fix is a nightly `rsync` of that
  directory off the box.

Redeploying the service:

```sh
cd "AI Profit Lab/SmartChatBot/storefront-offer-api"
rsync -av --delete --exclude node_modules --exclude .env --exclude sa.json \
  --exclude '.receipts' --exclude '.DS_Store' ./ root@187.127.116.171:/opt/storefront-offer-api/
ssh root@187.127.116.171 \
  'cd /opt/storefront-offer-api && sudo -u offerbot npm ci --omit=dev && systemctl restart storefront-offer-api'
```

Full detail, including the traps, in that service's `deploy/DEPLOY.md`.

### Environment

| Var | Set? | Note |
|---|---|---|
| `SHEET_ID` | yes | the `Seat_Claims` ledger |
| `GOOGLE_APPLICATION_CREDENTIALS` | yes | key file for `offer-api@aiprofitlab-offer…`, **that account specifically** — it is the one shared as a writer on the sheet. Empty on Cloud Run, which used the attached identity |
| `RECEIPTS_DIR` | yes | `/var/lib/storefront-offer-api/receipts`. Was a private GCS bucket; see below |
| `PUBLIC_BASE` | yes | `https://offer.aiprofitlab.io` — the origin in the receipt link stored in the ledger |
| `OFFER_ADMIN_PASSWORD_HASH` | yes | unlocks receipt viewing. **Unset ⇒ the viewing routes are not mounted at all** |
| `ALLOWED_ORIGINS` | yes | browser origins, not this API's own host — unchanged by the move |
| `SITE_ORIGIN`, `OWNER_EMAIL` | yes | |
| `PAY_PATH` | `/en/pay/` | where the buyer is sent back to; defaults to this |
| `RESEND_API_KEY` | **needed** | without it every email is logged and skipped — a claim is never lost because email is down, but no invoice arrives either |
| `THAWANI_SECRET_KEY` / `_PUBLISHABLE_KEY` | **needed for cards** | secret is server-side only; publishable appears in the redirect URL. Two different keys — do not swap them. |
| `THAWANI_BASE` | | UAT by default |
| `PAY_ENABLED` | | `0` to switch cards off in a hurry |

---

## 5. Two payment paths, kept separate

| | Smart Storefront seat | v4 checkout |
|---|---|---|
| Page | `/en/smart-storefront/` → `/en/pay/` | `/en/services/` → `/en/checkout/` |
| Prices | `lib/tiers.js` (the seat ladder) | `tools/v4/pay.py` |
| Ledger | Google Sheet `Seat_Claims` | `backend/checkout-api` |
| Service | `storefront-offer-api` (Cloud Run) | `backend/checkout-api` (not deployed) |

Same Thawani merchant account underneath. They are deliberately not merged —
the campaign ladder is a scarcity offer with its own arithmetic, and folding it
into the standing price list would break both. The collision only matters if
both go live *and indexed*; the storefront pages are `noindex` while the flyer
campaign runs.
