# Issuing an invoice by hand

For every customer who pays: copy a JSON, change the name and the numbers, run one
command, attach the PDF.

```sh
cp invoices/customers/_blank.json invoices/customers/acme.json
# edit acme.json — name, line items, amounts
python3 tools/invoice.py invoices/customers/acme.json --send
```

```
Issued LGI-2026-0001 — OMR 1,075.00 — Acme Trading LLC
  invoices/out/LGI-2026-0001.pdf

  LGI-2026-0001   OMR 1,075.00
  to:  owner@acme.om
  bcc: hello@aiprofitlab.io
  Send? [y/N] y
  sent to owner@acme.om (bcc hello@aiprofitlab.io) — 4f2a…
```

That is the whole thing. The rest of this page is why it behaves the way it does.

---

## 1. This is not the storefront invoicer

Two systems issue invoices for this company, and they do different jobs.

| | this one | the storefront one |
|---|---|---|
| Where | `tools/invoice.py`, on your Mac | `storefront-offer-api`, on Cloud Run |
| Trigger | you run it | a seat claim or a payment landing |
| Covers | anything — any service, any amount, any customer | Smart Storefront seats only |
| Line items | whatever you type | hard-coded: seat, 50% deposit, balance |
| Series | `LGI-YYYY-NNNN` | `INV-YYYY-NNNN` and `PF-YYYY-NNNN` |
| Code | `invoices/template.html` | `SmartChatBot/storefront-offer-api/lib/invoice.js` |

Use this one for everything that is not a storefront seat. See
[`storefront-payments.md`](storefront-payments.md) for the other.

**They look identical on purpose.** Same issuer block, same palette, same VAT wording,
same footer. If you restyle one, look at the other — a customer who gets both should not
wonder whether they are dealing with the same company.

---

## 2. Why the series are separate

This script counts off `invoices/register.json`, on your Mac. The storefront service
counts off the `Seat_Claims` Google Sheet, from Cloud Run. Neither can see the other.

Sharing one `INV-` series would therefore eventually allocate the same number twice — a
seat confirming itself at the same moment you issue an invoice here, and two customers
holding a document numbered `INV-2026-0008`. `LGI-` costs nothing and makes that
impossible. Your accountant gets two clean sequences instead of one corrupt one.

Numbers restart at `0001` each calendar year; that is what the year in the number is for.
Proformas count separately, as `LGI-PF-YYYY-NNNN`.

---

## 3. The customer JSON

Only `buyer.name` and `items` are required. Everything else appears if you supply it and
is silently left off the page if you do not.

```jsonc
{
  "kind": "invoice",              // or "proforma" — a request for payment, not a receipt
  "date": "2026-08-25",           // optional; defaults to today, on Muscat's clock

  "buyer": {
    "name":    "Acme Trading LLC",       // required
    "attn":    "Mr. Salim Al Balushi",
    "cr":      "1234567",
    "address": "Al Khuwair, Muscat",
    "email":   "owner@acme.om",
    "phone":   "+968 9000 0000"
  },

  "reference": "SS-8F2K1A",       // your own reference, printed in the grey strip
  "terms":     "Due within 7 days", // defaults to "Due on receipt" when unpaid

  "items": [
    { "title": "The Smart Website",
      "note":  "Optional line of small print under the title.",
      "amount": 950 },

    { "title": "The Growth Desk",   // qty × unit: the Qty and Unit price
      "qty": 3, "unit": 75 }        // columns appear only if some line uses them
  ],

  "discount":    { "label": "Agreed discount",            "amount": 150 },
  "already_paid":{ "label": "Deposit paid 12 Aug 2026",   "amount": 100 },

  "paid": {                        // present = this document is a receipt
    "amount": 1075,                //   must equal the total exactly
    "date":   "2026-08-25",
    "method": "card",
    "reference": "checkout_xxx"
  },

  "pay_url": "https://…",          // only used when unpaid; adds the card instructions
  "notes":   "Free text. Line breaks survive."
}
```

Amounts are in **OMR**, written as ordinary numbers. Internally everything is integer
baisa, so nothing ever drifts to `OMR 949.9999998`.

The arithmetic on the page is always:

```
subtotal (sum of line items)  −  discount  −  already_paid  =  total
```

A **part payment** is not `paid` with a smaller number — the script refuses that, because
the document would no longer add up in front of the customer. Put what has already been
received in `already_paid`, and the total becomes the balance.

---

## 4. Running it

```sh
python3 tools/invoice.py invoices/customers/acme.json         # issue, PDF only
python3 tools/invoice.py invoices/customers/acme.json --send  # issue AND email it
python3 tools/invoice.py invoices/customers/acme.json --dry   # preview, no number burnt
python3 tools/invoice.py --list                               # everything issued so far
python3 tools/invoice.py --refresh-fonts                      # re-embed the brand faces
```

Both a `.pdf` and the `.html` it came from land in `invoices/out/`. The HTML is
standalone — fonts and logo are carried inside it — so it survives being archived.

**Re-running is safe.** The first run writes the allocated number back into the customer
JSON. Every run after that regenerates *that same invoice* instead of taking the next
number, so fixing a typo costs nothing. To deliberately issue a second, different
invoice to the same customer, copy the file and delete the `"number"` line.

**A number, once issued, is spent.** If you cancel an invoice, do not delete its line
from the register — leave it and issue a credit or a corrected one. A gap in an
accounting sequence is a question you will be asked.

---

## 5. What is never on the document

Three rules, all of them already enforced by the template. Do not talk yourself out of
them for one convenient customer.

- **The issuer is the legal entity.** Lotus Gulf International, CR 1570092, TIN 2317725.
  "AI Profit Lab" is the trading name printed on top of it. Every financial document asks
  for the former.
- **No VAT line.** The company is below Oman's OMR 38,500 threshold and is not
  registered. The document says so in words. A `VAT 0%` line would imply a registration
  that does not exist.
- **No bank details.** Not on the PDF, not in the covering email. An IBAN on a document
  that can be forwarded is how impersonation starts. Send transfer details yourself, to
  someone you have spoken to.

---

## 6. Sending it

`--send` emails the PDF from **hello@aiprofitlab.io** through Resend, blind-copied to the
same address so you always hold a copy of exactly what the customer received.

### One-time setup

Create a key at [resend.com/api-keys](https://resend.com/api-keys) with **sending access
only** — it never needs to read or manage domains. Then:

```sh
cp invoices/.env.example invoices/.env
# put the key in it:  RESEND_API_KEY=re_...
```

`invoices/.env` is gitignored. Nothing else is needed: `aiprofitlab.io` is already
DKIM-verified for Resend (`resend._domainkey.aiprofitlab.io` is live), which is why the
other two services already send as this address.

### The safety rules, and why each exists

- **Nothing sends without `--send`.** Issuing a PDF and mailing a customer are different
  decisions.
- **A prompt shows the number, the amount and the recipient** before anything leaves. The
  amount is the thing worth reading twice. `--yes` skips it for scripted use.
- **`--dry --send` is refused outright.** A dry run must never reach a customer.
- **An invoice is emailed once.** The register records who it went to and when; sending
  the same number again needs `--resend-email`. Two copies of one invoice make a customer
  wonder whether they owe it twice.
- **A missing key fails before the prompt**, not after you have said yes.
- **Nothing is recorded as sent unless Resend returned a message id.** A failed send
  leaves the invoice issued and unsent, which is the truth.
- **In a non-interactive shell it refuses rather than assuming yes.**

### What the email says

Short, and the same shape every time: what is attached, what it comes to, whether anything
is owed, and an offer to reissue it if something looks wrong. If the invoice carries a
`pay_url` the card link appears; if not, it says to reply for transfer details.

**No bank details, exactly as on the PDF.** The email says "reply and I will send them" —
that reply goes to hello@aiprofitlab.io, which is a real Hostinger mailbox, and you answer
a person you have spoken to.

### Deliverability

DKIM passes and is aligned, and DMARC is `p=none`, so mail from Resend will be delivered.
SPF for the root domain currently covers only Hostinger
(`v=spf1 include:_spf.mail.hostinger.com ~all`) and not Resend, so SPF alone does not
authorise these sends — DMARC passes on DKIM instead. It is worth adding Resend to SPF;
take the exact record from the domain page in the Resend dashboard rather than guessing at
one, because the right value depends on whether the domain is set up for root or subdomain
sending.

The Gmail connector cannot do this job: its send has no "from" field, so it can only send
as `ai.profit.lab2026@gmail.com`, not as hello@aiprofitlab.io.

---

## 7. Gotchas

**This repo is public.** `invoices/customers/`, `invoices/out/`, `register.json` and
`invoices/.env` are gitignored for that reason — a committed invoice publishes a real customer's name, CR
number, phone and what they paid. Check `git status` before committing anything under
`invoices/`. Only the template, the script and the two `_` placeholder specs are tracked.

**Back up `register.json` somewhere off this Mac.** It is the only record of which
numbers have been issued, and it is deliberately not in git. Losing it means reissuing a
number someone already holds.

**Headless Chrome writes the PDF and then sometimes does not exit.** The script watches
for the file rather than waiting on the process, and kills Chrome once the PDF stops
growing. That is why it takes about two seconds and not sixty.

**Fonts are base64-embedded** in `invoices/assets/fonts.css` so an invoice renders the
same offline, on any machine, in five years. `--refresh-fonts` rebuilds it (latin subsets
only). Python's `urllib` cannot do TLS on this Mac, so it goes through `curl`.

**Two decimals, not three.** `DECIMALS` at the top of `tools/invoice.py`. Oman's rial
formally carries three (1000 baisa), but the storefront invoicer prints two, and one
company should not print money two ways. Change both or neither. The script refuses to
round: an amount that needs the third decimal is an error, not a quiet `.00`.

**Editing the design.** `invoices/template.html`, which is ordinary HTML and CSS. You can
also duplicate it and fill it in by hand — the placeholders are visible, the `<!--IF:…-->`
blocks are deletable, and Chrome's Cmd-P → Save as PDF gives the same page. If you do
that, assign the number yourself and add it to the register so the script never reissues
it.
