# What to send Thawani

Ready to send to **products@thawani.om**, from **nahid.abyari@gmail.com** (the
address registered on the Thawani portal and on the merchant application — not
hello@aiprofitlab.io).

Questions 1 and 2 are the ones that change what we build. The rest are go-live
housekeeping.

---

**Subject:** Lotus Gulf International (CR 1570092) — UAT integration complete, questions before go-live

Dear Thawani team,

Thank you for the credentials and the integration document. Our e-commerce
integration is complete and tested end to end against the UAT environment: we
create a checkout session, redirect to the hosted page, and confirm the result
by retrieving the session. Customer metadata is attached to every transaction.

Merchant details for reference:

- Legal entity: **LOTUS GULF INTERNATIONAL** (Sole Proprietor Company)
- CR number: **1570092**
- Trading brand: AI Profit Lab — https://aiprofitlab.io
- Services requested: E-commerce + Payment link

Before we go live, we would be grateful for clarification on the following.

**1. Recurring / saved-card payments.** One of our products is a monthly
service, so we need to charge a returning customer's saved card each month. We
have tested the tokenization flow on UAT: creating a customer, passing
`customer_id` with `save_card_on_success` on the session, and creating a payment
intent.

Our question is about the final step. Your integration document says that after
confirming a payment intent we should "take the user to the OTP URL received on
the confirm response."

- Does **every** saved-card charge require the cardholder to complete an OTP, or
  can a merchant-initiated charge against a stored card complete without the
  customer being present?
- If unattended recurring charges are possible, is that a feature we need to
  request specifically? Our application was for E-commerce + Payment link, and
  we want to be sure tokenization and recurring billing are enabled on our
  production account.
- Do you offer a subscription or mandate product we should be using instead?

**2. Metadata limit.** We found that `metadata` accepts a maximum of 10 items —
an eleventh causes the whole session to fail with:

```
code 4000 · "Metadata cant have more than 10 items"
```

Could you confirm this limit is intentional and stable? We did not find it in
the documentation, and because it fails the entire session rather than dropping
the extra field, it would cost a live order. Is there also a maximum length for
a metadata **value**?

**3. Amount limits.** From UAT validation messages we understand:

- Checkout session: `unit_amount` between 1 and 5,000,000 baisa per product line
- Payment intent: `amount` between 100 and 9,999,000 baisa

Are these the same in production? Our largest single order is around **OMR
3,400**, so we would like to confirm there is no lower per-transaction or daily
ceiling on a live merchant account that would decline it.

**4. Webhooks.** We currently confirm payments by retrieving the session, and we
would prefer to also receive webhooks. Could you send us:

- how to register our webhook URL,
- the payload format, and
- **how to verify a webhook is genuinely from Thawani** (signature header,
  shared secret, or source IP range)?

We are not willing to act on an unauthenticated callback about money, so the
verification method is the part we need.

**5. Refunds.** Can refunds be issued through the API, or are they done only in
the merchant portal? If the API supports them, please point us to the endpoint.

**6. Test cards.** The test card page in your documentation shows the card
details as images that we could not read. Could you send the test card numbers,
expiry, CVV and OTP in text, including a card that simulates a decline?

**7. Going live.** What is the process for issuing production keys once the
merchant account is approved? Specifically:

- Do we need to register our success and cancel URLs, or our server's IP, in
  advance?
- Is there anything you need to review or approve on our checkout page first?

**8. Settlement and rates.** Please confirm the settlement cycle to our bank
account, and that our rates are the published 1.5% for local debit cards and 2%
for credit and international debit cards.

Thank you very much for your help.

Best regards,

**Nahid Abyari**
Owner, Lotus Gulf International (AI Profit Lab)
nahid.abyari@gmail.com · +968 9924 5250

---

## Why each question is on the list

| # | Why it matters | What changes based on the answer |
|---|---|---|
| 1 | Decides whether the Growth Desk can be a subscription at all | Either the billing runner goes live, or the Desk stays invoiced by hand and the site keeps saying so |
| 2 | Undocumented, and session-fatal | If the limit could move down, the metadata budget has to be re-cut |
| 3 | An OMR 3,400 order is our biggest sale | A lower live ceiling means the three-payment plan becomes mandatory, not optional |
| 4 | We poll today; a verified webhook is faster and cheaper | Without a verification method we keep polling — that is the safe default, not a gap |
| 5 | A refund we cannot issue is a support problem | Portal-only means writing a manual refund procedure |
| 6 | We cannot complete a paid UAT test without them | Blocks the last untested step: does a card actually clear |
| 7 | Avoids discovering a registration requirement on launch day | May add a step to the go-live checklist |
| 8 | Cash-flow planning, and confirms the quoted rates | Affects pricing margins |
