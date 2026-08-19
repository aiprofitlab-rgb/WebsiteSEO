# AI Profit Lab — Money Model

*Owner: Nahid Abyari · Last updated: 2026-08-19*
*Model locked 2026-08-13. Live campaign numbers verified 2026-08-19 against `storefront-offer-api/lib/tiers.js`.*

---

## 1. The shape of the model

One low-friction, **one-time** entry offer that a cold stranger can say yes to — then recurring
revenue earned *after* trust exists, never demanded before it.

```
  ATTRACTION / FLAGSHIP        UPSELL 1              UPSELL 2               CONTINUITY
  ─────────────────────        ─────────             ─────────              ──────────
  The Smart Storefront    →    The Command Center →  The Full Autopilot  →  The Growth Desk
  (one-time fee)               (CEO dashboard)       (sales & invoice       (monthly care —
                                                      follow-up)             opt-in, sold last)
```

**The core tension this resolves:** "no monthly fees" is a genuine trust and differentiation
asset against subscription SaaS rivals — so the *entry point stays one-time*. Recurring revenue
comes from the upsell products and the optional care plan, sold once the customer already
trusts him. The Growth Desk is **never bundled into the entry offer.**

**Package ladder** (replaces the old Starter / Growth / Scale naming):
The Storefront → The Command Center → The Full Autopilot → The Growth Desk.

---

## 2. The flagship — The Smart Storefront

A bilingual (Arabic/English) storefront site with an AI sales agent built in, that answers
buyers around the clock and hands the serious ones to the owner's WhatsApp.

**Dream outcome:** never miss a buyer again, look credible instantly, know who's about to buy
before they call — without hiring anyone.

### The six deliverables (each one does a job)

| # | Deliverable | The job it does |
|---|---|---|
| 1 | An employee who never sleeps | Bilingual AI agent answering buyers at 4am, on a Friday, during Eid |
| 2 | Hot leads in your pocket | Serious buyers handed straight to WhatsApp |
| 3 | Built for bulk quotes | A wholesale quote-request flow, not a retail "contact us" box |
| 4 | Know who's about to buy | Short visitor-intelligence summary sent to the owner's phone |
| 5 | Found on Google and ChatGPT | Built for traditional search and AI answers alike (GEO) |
| 6 | Nothing to maintain | A full year of hosting, security and care included |

### The guarantee — "The First Inquiry Promise"

> No real buyer inquiry within 30 days of going live? I rebuild it free until you get one.
> If you still don't, you get your money back.
> — Nahid Abyari

Stronger than a plain refund, and deliberately compensating for having no case studies yet.
It is a **brand device**, not just a term — restate it in the founder's voice wherever the
offer appears.

### Delivery
About a week for a real build. Payment: **50% deposit to hold a seat**, balance on completion.
No payment is taken on the landing page — the agreement and invoice go out by email within one
business day and the client pays after reading them.

---

## 3. The live price ladder (Founding Partner campaign)

Source of truth: `AI Profit Lab/SmartChatBot/storefront-offer-api/lib/tiers.js` — **not** the
web page. The page renders whatever `/status` returns and hardcodes no price.

| Rung | Seats | Price (OMR) |
|---|---|---|
| 1 | 3 | 249 |
| 2 | 7 | 279 |
| 3 | 10 | 299 |
| 4 | 15 | 337 |
| 5 | 20 | 359 |
| 6 | 30 | 399 |
| 7 | 15 | 449 |
| **Total** | **100** | — |

Only the live rung and the next two are ever published. Deposit = **50%** of the tier price.

**A seat is only taken when a deposit has actually cleared.** Submitting the form writes
`Awaiting_Deposit`, a receipt upload writes `Deposit_Submitted`, and only Nahid promoting the
row to `Confirmed` by hand counts toward the counter. That manual gap is the entire reason the
scarcity claim can honestly be called real. **Never fake or animate this number.**

### The pledge rebates — pay less, later

Ticked *after* the site is live. Nothing is deducted up front; nothing is clawed back.

| Pledge | Rebate |
|---|---|
| A video testimonial (phone-filmed, two minutes, their own words) | 15% |
| A LinkedIn endorsement + a Google Maps review, both public and in their name | 5% |
| One social post in an agreed format | 10% |
| An introduction to another owner **who actually orders** | 20% |
| **All four** | **50% back** |

Rebates are **post-delivery, uncapped**, and the server recomputes the percentage from pledge
*ids* so a tampered form can't buy a discount.

**Why give away half the margin:** a real testimonial from a real distributor is currently
worth more than the margin. This *is* the Founding Partner mechanism — trading margin and risk
on a capped early cohort to manufacture the first publishable case studies, which is the
binding constraint on all future marketing (see `01-persona-and-avatar.md` §4).

**The exchange:** reduced price and/or a stronger guarantee, for case-study rights, a specific
testimonial, and one warm introduction to a peer business.

---

## 4. The standing service ladder (still live on the site)

Verified 2026-08-04 from `services-en.html`. These co-exist with the Storefront campaign.

| Plan | Setup (OMR) | Monthly (OMR) | Annual prepay | Year one | Delivery |
|---|---|---|---|---|---|
| Starter | 500 | 75 | 750 | 1,400 (monthly) / 1,250 (prepay) | 3–6 weeks |
| Growth | 1,200 | 150 | 1,500 | 3,000 / 2,700 | 6–12 weeks |
| Scale | 2,500 | 300 | 3,000 | 6,100 / 5,500 | 10–14 weeks |

**Standalone products:** website with built-in AI 800 + optional 100/mo · custom dashboard
300 + optional 50/mo · Arabic-optimized chatbot add-on 150 · custom automation 200 each ·
staff training 100 per 2-hour session.

**Entry point:** free 30-minute AI Strategy Call.

⚠️ **Never quote "from OMR 75/month" alone** — it understates year one (~OMR 1,400). Always
state the setup fee.
⚠️ **"Live within 14–30 days" is stale and wrong.** The live site states 3–6 / 6–12 / 10–14
weeks by plan. Do not use it.

---

## 5. Unit economics context

| Alternative | Cost |
|---|---|
| Hiring an admin | OMR 350–500/month **plus** visa, insurance, paid leave — covering ~40 of 168 hours |
| QwicLink Auto-Pilot | OMR 49/month + 29 setup (≈ OMR 617 year one) |
| Our Starter | OMR 75/month + 500 setup (≈ OMR 1,400 year one) |

We are roughly **2.3× QwicLink**. Argue done-for-you scope, never price, against local rivals.

---

## 6. The campaign stack (three pieces that must stay in sync)

1. **Page** — `public_html/en/smart-storefront.html` → `/en/smart-storefront/`, plus
   `en/claim.html` → `/en/claim/?ref=…`. Ships `noindex` while it runs beside the older
   `/en/smart-website-offer/`.
2. **API** — `storefront-offer-api` on Cloud Run, project `aiprofitlab-offer`, region
   `me-central1`. Source at `AI Profit Lab/SmartChatBot/storefront-offer-api/`.
   Changing a price = edit `lib/tiers.js` and redeploy.
3. **Ledger** — Google Sheet `Seat_Claims` tab, owned by ai.profit.lab2026@gmail.com.

If these three drift apart, the page lies. The page's entire pitch is that its numbers are real.

---

## 7. Open items — Nahid's call, not to be guessed

- Final OMR pricing for The Command Center, The Full Autopilot and The Growth Desk.
- Exact Founding Partner cohort size beyond the published rungs.
- Whether the standing Starter/Growth/Scale ladder is retired, repriced, or kept alongside the
  new package names.

Related docs: `01-persona-and-avatar.md`, `02-brand-book.md`.
