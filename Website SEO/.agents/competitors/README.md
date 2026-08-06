# Competitor Data — Single Source of Truth

Created 2026-08-04. Companion to `.agents/product-marketing.md`.

## How this works

Every competitor fact lives in exactly one `.yml` file here. Comparison pages read from
these files. When a competitor changes their pricing, **update the `.yml` and then
propagate to pages** — never edit a claim on a page directly, or the files drift apart.

## Files

| File | What it holds |
|---|---|
| `_us.yml` | **Our own verified pricing and claims. Use these numbers, not memory.** Includes `do_not_publish` and `known_gaps`. |
| `qwiclink.yml` | QwicLink — most direct competitor. Pricing published, high confidence. |
| `nuqta.yml` | Nuqta — strongest credibility competitor (6 named clients, on-prem, dialect models). |
| `4ys.yml` | 4Ys — enterprise ERP platform + proprietary AI. Bespoke pricing. |
| `wiya.yml` | WIYA — press-visible, WhatsApp commerce. **Confidence: low** — press-derived. |
| `others-watchlist.yml` | Qurban Tech, Autonoly, INZINT, VOLIOM, Muscat Audit, Fusion Informatics, Mint Digital + directory targets. |
| `non-agency-alternatives.yml` | Hiring staff, DIY platforms, chatbot SaaS, freelancers, doing nothing. **This is where the deals are actually lost.** |
| `PAGE-PLAN.md` | Prioritised page set with rationale. |
| `pages/` | Page copy, ready to convert to HTML. |

## Field conventions

- `verified:` — date the facts were last checked against the source. Anything older than
  a quarter is suspect.
- `confidence:` — `high` (they publish it), `medium` (inferred from their site),
  `low` (press or third-party derived). **Never publish a `low`-confidence fact.**
- `honest_loss_case:` — where we genuinely lose. Keep these in the pages; they're what
  makes a comparison page credible instead of promotional.
- `do_not_claim:` — hard prohibitions. Violating these creates claims a competitor can
  publicly disprove.

## Three things to know before writing any page

1. **We are not the local price leader.** QwicLink undercuts us roughly 2:1 in year one.
   Never build an argument on price against them.
2. **We publish no named clients or testimonials. Nuqta publishes six.** This is the
   biggest constraint on named-competitor pages — fix the proof gap before publishing them.
3. **"Live in 14–30 days" is stale and wrong.** `.agents/product-marketing.md` says it;
   the live services page says 3–6 / 6–12 / 10–14 weeks. Use the services page.

## Maintenance cadence

- **Quarterly:** re-check QwicLink's pricing page (they publish and will change it);
  re-check whether Nuqta's Al-Dhaki has launched; spot-check the others.
- **When a prospect mentions a competitor:** capture what they said in that competitor's
  `common_complaints`. Real buyer language is worth more than anything on their website.
- **Annually:** full refresh, including a fresh search for new entrants — this market is
  young and moving.

## Open research gaps

- **WIYA** — site is JS-rendered and returned almost nothing to a plain fetch. Needs a
  rendered-browser pass to get real service and pricing detail.
- **Pricing unknown** for Nuqta, 4Ys, WIYA, Qurban Tech, Autonoly. Consider a mystery-shop
  enquiry to establish real ranges — until then, pages must say "pricing on request".
- **No third-party reviews located** for any local competitor (no G2/Capterra presence).
  Review mining isn't available in this market; buyer conversations are the substitute.
- **Our own claims** — several stats on the live site (0.01% error rate, 40% capacity
  increase, 78% overhead reduction, 99.9% uptime) have no source in the repo. Either
  source them or soften them; a competitor page is exactly where an unsourced stat gets challenged.
