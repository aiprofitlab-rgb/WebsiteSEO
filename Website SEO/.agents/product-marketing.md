# Product Marketing Context

*Last updated: 2026-07-03*
*Status: V1 auto-drafted from codebase (llms.txt, GEMINI.md, about-en.html, en/index.html). Review and correct — see "Open Questions" at the end.*

## Product Overview
**One-liner:** AI automation agency that builds simple, affordable automation systems for SMEs in Oman and the GCC.
**What it does:** AI Profit Lab designs and implements custom AI/automation workflows (WhatsApp AI receptionist, missed-call recovery, lead capture, sales & invoice automation, CEO dashboards) that replace repetitive manual admin work with 24/7 automated systems.
**Delivery timeline (corrected 2026-08-04):** live services page states **3–6 weeks (Starter), 6–12 weeks (Growth), 10–14 weeks (Scale)**; About page says "first version in days, not months." ⚠️ The previously stated "14–30 days" was **not found anywhere on the live site** — do not use it in copy.
**Product category:** AI automation / business process automation consulting (not a self-serve SaaS product — a done-for-you service/implementation).
**Product type:** Service / consulting + custom software builds (built on enterprise automation platforms — GoHighLevel branding appears in assets — plus custom API integrations).
**Business model:** Setup fee + monthly managed retainer; sales driven by a free 30-minute "AI Strategy Call" audit booked via a multi-step qualification form.
**Actual published pricing (verified 2026-08-04 from `services-en.html`):** Starter OMR 500 setup + OMR 75/mo (annual prepay OMR 750) · Growth OMR 1,200 + OMR 150/mo (annual OMR 1,500) · Scale OMR 2,500 + OMR 300/mo (annual OMR 3,000). Standalone products: website OMR 800 + optional OMR 100/mo · dashboard OMR 300 + optional OMR 50/mo · Arabic chatbot add-on OMR 150 · custom automation OMR 200 each · staff training OMR 100/session. ⚠️ Quoting "from OMR 75/month" alone understates first-year cost (~OMR 1,400) — always state the setup fee.

## Target Audience
**Target companies:** SMEs in Oman and the wider GCC (UAE, Saudi Arabia, Qatar, Kuwait, Bahrain) — local and expat-owned businesses, not enterprise/Silicon-Valley-scale companies.
**Decision-makers:** Business owners / managers, not technical staff — copy is explicitly "non-technical," aimed at people who don't want to write code or learn jargon.
**Primary use case:** Eliminating time lost to repetitive administrative tasks (WhatsApp replies, manual data entry, lead follow-up) that cost the business missed messages, forgotten leads, and lost sales.
**Jobs to be done:**
- Stop losing leads/sales to missed WhatsApp messages and missed calls
- Replace or avoid hiring additional administrative staff
- Get visibility into business performance without building it themselves (CEO Dashboard)
**Use cases:**
- WhatsApp AI receptionist (auto-replying to customer inquiries 24/7)
- Missed-call recovery/follow-up automation
- Sales & invoice automation
- Lead capture and nurturing automation
- Executive/CEO dashboards for business visibility
- Campaign ROI simulation and reporting

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| Owner/Founder (primary buyer) | Profit, time back, simplicity | Wearing too many hats, can't afford enterprise tools or a full admin team | "Save your time, grow your profits" — a system live in days, priced in OMR |
| Operations/Office Manager | Fewer repetitive tasks, fewer errors | Manually entering data, chasing leads, answering the same questions | 24/7 automation with near-zero error rate (0.01% vs 4–6% human) |

## Problems & Pain Points
**Core problem:** Business owners across the GCC are "drowning in repetitive work" — answering the same WhatsApp questions, manually entering customer data, chasing leads — hours every week that should go toward growing the business.
**Why alternatives fall short:**
- Big tech / enterprise automation platforms are expensive, complicated, and built for huge corporations, not local SMEs
- Hiring more administrative staff costs OMR 350–500/month plus visa, insurance, and paid leave, and still only covers 8 hours/day, 5 days/week, with a 4–6% error rate
**What it costs them:** Missed messages, forgotten leads, wasted hours, lost sales — framed with a concrete example: recovering 3 lost clients at OMR 200 each = OMR 600/month in immediate revenue lift.
**Emotional tension:** Overwhelm and distrust of "tech" — fear of being oversold complicated, jargon-heavy solutions they won't understand or maintain.

## Competitive Landscape

*Named competitors researched 2026-08-04. Full profiles: `.agents/competitors/*.yml`. Page plan: `.agents/competitors/PAGE-PLAN.md`.*

**Direct — named local competitors (Oman):**
| Competitor | Model | Pricing | Threat |
|---|---|---|---|
| [QwicLink](https://www.qwiclink.com/) | Self-serve CRM + messaging automation for Omani service businesses | **Published:** OMR 15 / 29 / 49 per month + small setup | **High** — same ICP, undercuts us ~2:1 |
| [Nuqta](https://nuqtai.com/en) | Applied AI lab: Gulf-Arabic dialect models, on-premise private AI, model handover | Not published | **High** — publishes 6 named clients; deeper Arabic |
| [WIYA](https://wiya.ai/en) | WhatsApp storefront with in-chat payments/invoicing; secure local GPT | Not published | **Med-high** — strong national press presence |
| [4Ys](https://4ys.org/) | Enterprise platform: ERP/CRM/HR/POS (120+ modules) + own AI models | Bespoke | **Medium** — different weight class |
| [Qurban Tech](https://qurbantech.com/services/ai-engineering-oman) | Agentic AI engineering, Muscat/Salalah/Sohar | Not published | Medium |
| Autonoly, INZINT, VOLIOM, Muscat Audit | Platform / on-prem / analytics / finance-automation angles | Not published | Low–medium |

**Secondary:** Hiring additional administrative/customer-service staff — OMR 350–500/mo plus visa, insurance, leave, covering ~40 of 168 hours. **Note:** the site's replace-a-human framing is a strategic risk with Omani owners; recommended reframe to *capacity, not replacement* — see `.agents/competitors/pages/02-vs-hiring-admin-staff.md`.
**Also direct:** DIY platforms (Zapier/Make/n8n), chatbot SaaS (ManyChat/Tidio), and freelancers — see `non-agency-alternatives.yml`.
**Indirect:** Doing nothing — still the largest single competitor.

### ⚠️ Three competitive realities that change positioning
1. **We are not the affordable option locally.** QwicLink's AI tier ≈ OMR 617 year one vs our Starter ≈ OMR 1,400. The "affordable for GCC SMEs" claim holds against *enterprise/global* tools and against hiring — **not** against local rivals. Differentiate on done-for-you scope.
2. **Our proof gap is the binding constraint.** We publish zero named clients or testimonials; Nuqta publishes six. Do not publish named-competitor "vs" pages until 2–3 references exist.
3. **Several headline stats are unsourced** (0.01% error rate, 40% capacity gain, 78% overhead cut, 99.9% uptime). Source or soften before using them anywhere a competitor might challenge them.

## Differentiation
**Key differentiators:**
- Priced and positioned specifically for GCC SME budgets (OMR pricing, not USD/Silicon Valley pricing)
- No-jargon, plain-language approach — explicitly "no tech jargon, no pressure"
- Fast time-to-value: first version live in days, full system in 14–30 days
- Deep GCC/Omani market and regulatory context (Muscat AI Special Zone, Royal Decree 50/2026, Vision 2040, In-Country Value)
- Real human support — "no bots, no ticket systems" for support (ironic given the product sells chat automation to *its* customers, but the positioning is deliberate)
**How we do it differently:** Discover → Build → Support framework: a deep-dive audit of the business's actual bottlenecks, custom API integrations connecting CRM/lead-gen/communication channels, then live monitoring and team training post-launch.
**Why that's better:** Businesses get an enterprise-grade outcome (24/7 automated operations, ~78% lower overhead than hiring) without enterprise complexity or cost.
**Why customers choose us:** Founder-led, GCC-focused, transparent OMR pricing, and a low-friction entry point (free 30-minute strategy call, not a sales pitch).

## Objections
| Objection | Response |
|-----------|----------|
| "AI/automation is too expensive for a business my size" | Reframed directly on the homepage: OMR 75/mo automation vs. OMR 350+/mo for a human admin, with a side-by-side cost/availability/error-rate table |
| "This sounds too technical / I won't understand or maintain it" | Explicit "No Jargon" principle; team explains everything simply and trains staff post-launch |
| "How do I know this will actually pay for itself?" | ROI framing baked into the pitch (e.g., 3 recovered clients = OMR 600/month), plus a Campaign ROI Simulator and free strategy-call audit to map it out before buying |

**Anti-persona:** Enterprise/large corporates needing deep custom software engineering at scale, and businesses wanting a pure self-serve/DIY SaaS tool rather than a done-for-you build (not yet confirmed — see Open Questions).

## Switching Dynamics
**Push:** Mounting hours lost weekly to repetitive manual work; visible cost of missed leads/sales; frustration with existing admin overhead (salary, visa, insurance, leave).
**Pull:** Concrete, GCC-priced alternative with fast implementation (days, not months), plain-language sales process, and a free no-pressure strategy call.
**Habit:** Comfort/familiarity with existing manual processes or existing admin staff; uncertainty about how to even start with "AI."
**Anxiety:** Fear of being sold something overly technical or oversized for their business; concern that automation won't reflect local language/culture/regulatory needs (Oman-specific compliance, Arabic-language support).

## Customer Language
**How they describe the problem:**
- "Losing 20+ hours a week to repetitive administrative tasks"
- "Missed messages, forgotten leads, wasted hours, lost sales"
**How they describe us:** *(not yet captured — needs real customer quotes/testimonials)*
**Words to use:** simple, honest, fair pricing, no jargon, real people, results, save time, grow profits.
**Words to avoid:** complicated technical/enterprise jargon, anything implying "Silicon Valley" pricing or scale.
**Glossary:**
| Term | Meaning |
|------|---------|
| AI DEN / Aiden | The site's own AI chat widget/assistant used on the site itself |
| ICV | In-Country Value — Omani government initiative around local economic development the company aligns its positioning with |
| Muscat AI Special Zone | Regulatory/economic zone referenced in the site's Oman-market positioning (Royal Decree 50/2026) |

## Brand Voice
**Tone:** Warm, plain-spoken, reassuring — explicitly anti-jargon and anti-hype.
**Style:** Direct and conversational, founder-voiced (first-person message from Nahid Abyari on the About page), practical/ROI-driven rather than abstract.
**Personality:** Honest, approachable, locally-rooted (GCC-focused), fast-moving, no-nonsense.

## Proof Points
**Metrics:** ~40% increase in average operational capacity; ~78% lower monthly overhead vs. hiring an admin; 24/7/365 availability with ~0.01% error rate; 99.9% uptime target; 14–30 day implementation window.
**Customers:** *(no named customers/logos found in current site content — see Open Questions)*
**Testimonials:** *(none captured yet in the crawled pages — site does prompt for Google Reviews, but no on-site quotes found)*
**Value themes:**
| Theme | Proof |
|-------|-------|
| Cost savings vs. hiring | OMR 75–300/mo automation vs. OMR 350–500/mo human admin (site's own comparison table) |
| Time savings | "20+ hours a week" reclaimed from repetitive admin tasks |
| Speed to value | First version live in days; full implementation in 14–30 days |
| Local relevance | GCC-only focus, OMR pricing, Arabic + English site, Oman regulatory alignment |

## Goals
**Primary business goal:** Book free 30-minute AI Strategy Call audits that convert into monthly automation retainers.
**Conversion action:** Complete the 4-step "AI Strategy Call Audit" form (contact details → business snapshot → pain points/goals → readiness/budget/timeline) to book a call.
**Current metrics:** *(not available in repo — site includes a GTmetrix-flagged performance issue: 1.2s TTFB / 1.7s LCP per `GEMINI.md`, unrelated to marketing metrics)*

---

## Open Questions (please review/fill in)
1. ~~Are there any named direct competitors in the Oman/GCC AI-automation space worth tracking?~~ **✅ Answered 2026-08-04** — six named local competitors researched and profiled in `.agents/competitors/`. See Competitive Landscape above.
2. **🔴 NOW THE HIGHEST-PRIORITY GAP.** Do you have real customer testimonials/quotes or case studies to add to Proof Points? (Site currently only asks visitors to leave a Google Review.) Nuqta publishes six named clients; we publish none. This blocks the named-competitor comparison pages and weakens every page on the site.
3. Who is explicitly *not* a good fit — e.g. minimum company size, industries you turn away, budget floor?
4. Any specific verbatim quotes from sales calls/WhatsApp that describe how customers talk about their problem or about you?
5. Is GoHighLevel (or another platform) the actual delivery backend worth naming internally, or should that stay unstated externally?
6. Current traffic/conversion metrics (Search Console, GA4, call-booking rate) if you want them tracked here for future reference.
