# Visitor Journey Tracking — Run these prompts in order

Each prompt is self-contained. Paste into a **fresh** conversation, one at a time.
Facts were verified 2026-08-25; prompts 1–5 are independent of each other except where noted.

Run 1 → 2 → 3 as soon as possible (data collection is not retroactive).
Run 6 about two weeks after 2 and 3 are live, once data has accumulated.

---

## PROMPT 1 — Fix the GA4 data leaks (Tier 0)

Working dir: `/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO`

Fix three GA4 tagging holes on aiprofitlab.io. Verified counts of the 375 HTML files
under `public_html/`: 275 use the correct property `G-SLR9GD3MJP`, **94 use a stray
old property `G-2GPVY4Z5KR`** (47 articles in `blog/en/` + 47 in `blog/ar/`), and
**6 have no GA tag at all**:
- public_html/smart-website-offer-en.html
- public_html/smart-website-offer.html
- public_html/en/preview-templates.html
- public_html/en/claim.html
- public_html/en/pay.html   <- this is the live checkout page
- public_html/en/smart-website-offer.html

Do all three:

1. Repoint all 94 stray-property articles to `G-SLR9GD3MJP`.
2. **Fix the root cause.** `tools/v4/legacy.py` line ~151 does
   `re.search(r"gtag/js\?id=([A-Za-z0-9-]+)", head)` — it *preserves* whatever GA ID
   it finds in the existing page head, which is why a previous cleanup got undone by a
   reskin. Make it always emit `G-SLR9GD3MJP` (or refuse any ID that isn't the canonical
   one) so `tools/reskin_articles.py` can never restore the stray again.
3. Add the standard gtag snippet to the 6 untagged pages. The canonical snippet is in
   `tools/v4/kit.py` lines 771-773.

Constraints:
- The article/hub stylesheet is ONE content-hashed file shared by EN and AR. If you
  re-run `tools/reskin_articles.py` you MUST run it for both languages (no `--lang` flag)
  or all 154 Arabic articles point at a deleted stylesheet and render unstyled.
- Verify by re-counting: after the fix, 0 files should contain `G-2GPVY4Z5KR` and
  0 files should lack `gtag/js?id=`.
- Deploy = commit + push to `main`; a GitHub Action FTP-mirrors `Website SEO/public_html/`
  to Hostinger. The git root is one level up at `AI Profit Lab/Website/`.
  Do not push without asking me first.

---

## PROMPT 2 — GA4 console setup: BigQuery export + custom dimensions

I need a precise click-path for the Google Analytics 4 console. No code — I'll do
this in the browser. Property is `G-SLR9GD3MJP` for aiprofitlab.io (a static site,
gtag.js hardcoded, no GTM container). Google Cloud project already in use for other
services: `adroit-minutia-496210-n1`.

Give me exact, current step-by-step instructions for:

1. **Linking GA4 to BigQuery** (free on GA4 standard). Cover: where the link lives in
   Admin, daily vs streaming export and which I should pick, data location choice,
   which events to include, what the dataset/table naming looks like once it lands,
   how long until the first table appears, and what it will cost me at roughly
   3,000–10,000 sessions/month. Confirm whether it is retroactive.

2. **Registering custom dimensions** so my existing custom events are reportable.
   These event parameters are already being sent by the site and need registering as
   event-scoped custom dimensions: `page_path`, `returning`, `scenario`, `demo`,
   `tool`, `method`, `category`, `payment_type`. Tell me the free-tier limit on
   custom dimensions and warn me if I'm near it.

3. **Marking conversions / key events.** These events already fire on the site:
   `begin_checkout`, `add_payment_info`, `purchase`, `generate_lead`, `aiden_open`,
   `aiden_message`, `demo_scenario`, `simulator_preset`, `filter_articles`.
   Tell me which to mark as key events and why.

4. **Enhanced measurement** — tell me which toggles to verify are ON and which to
   turn OFF because I'm about to send the same signal myself (I'm adding my own
   25/50/75/100 scroll milestones and a page-exit dwell event).

5. **Data retention** — where to change it from 2 months to 14 months, and why it
   matters less once BigQuery export is on.

Verify current UI paths against Google's live documentation rather than answering
from memory; the GA4 admin layout changes often.

---

## PROMPT 3 — Install Microsoft Clarity site-wide

Working dir: `/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO`

Add the Microsoft Clarity tracking tag (free session recordings + heatmaps) to
aiprofitlab.io. I will create the Clarity project and give you the project ID — ask
me for it before writing any code.

Site facts:
- 375 static HTML files under `public_html/`, no GTM container; GA4 gtag.js is
  hardcoded into every page head.
- Pages are GENERATED, not hand-edited. The tag must go into the builders so it
  survives a rebuild:
  - `tools/v4/kit.py` (~line 771) — the shared head block for the v4 pages
  - `tools/v4/blog_chrome.py` (~line 394) — the head block for articles + blog hubs
  - Any page not covered by those two needs the tag added directly.
- Rebuild order after editing builders:
  1. `python3 tools/build_v4.py`  (builds BOTH languages)
  2. `python3 tools/reskin_articles.py`  (NO --lang flag — see trap below)
  3. `python3 tools/reskin_blog_hubs.py`  (NO --lang flag)
- **The trap:** the article/hub stylesheet is one content-hashed file shared by EN and
  AR. Running the reskin for one language only leaves the other language's 154 articles
  pointing at a deleted stylesheet — they render unstyled and nothing errors.
- `tools/reskin_articles.py` must stay idempotent — re-running it must not stack a
  second copy of the tag. Verify by hashing all output files, running it twice, and
  hashing again; the hashes must match.

Also do:
- Turn on Clarity's GA4 integration so I can jump from a GA4 segment to the recordings,
  and tell me where that setting lives.
- Confirm Clarity's input-masking default and leave it at the strictest setting —
  the site has a checkout page (`public_html/en/pay.html`) and contact forms.
- Tell me the perf cost of the tag and whether it should be `async` or `defer`.

Do not push to `main` without asking me first.

---

## PROMPT 4 — Build `apl-analytics.js` (the instrumentation layer)

Working dir: `/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO`

Build a single shared analytics script for aiprofitlab.io so future tracking changes
are a one-file edit instead of a 375-page rebuild.

Create `public_html/js/apl-analytics.js`, content-hash-versioned exactly the way
`public_html/js/aiden-chat.js` already is (see `tools/aiden_version.py` and
`tools/add_aiden_widget.py` for the existing pattern — mirror it, don't reinvent it).

It must send to the existing GA4 property `G-SLR9GD3MJP` via the global `gtag()`
that every page already loads. Guard every call — `typeof gtag === "function"` —
the way the existing v4 builders do.

Events to add:

1. **`page_exit`** — fire on `visibilitychange` → hidden, using `navigator.sendBeacon`
   semantics so it survives unload. Params: `dwell_seconds` (real time on page),
   `max_scroll` (0-100), `page_type`, `exit_intent`. This is the number GA4's built-in
   engaged-time is worst at measuring on the LAST page of a session — which is exactly
   the drop-off page I care about. Fire once per page, not on every tab switch.

2. **Scroll milestones** at 25/50/75/100. GA4 enhanced measurement only reports 90.
   Each milestone fires at most once per page view.

3. **Page context on every event** — set `page_type`, `content_language` (en/ar) and,
   on articles, the article slug, as GA4 custom dimensions. **Reuse the `pageType()`
   classifier that already exists** in `public_html/js/aiden-chat.js` (~line 155) —
   extract it to a shared place rather than writing a second copy that drifts.

4. **Outbound / CTA clicks**: the WhatsApp FAB (`.fab`), all `tel:` links, all
   `mailto:` links, and clicks on any link leaving the domain.

Wiring:
- Add the script tag to the builders, not to the HTML files:
  `tools/v4/kit.py` (~line 771) and `tools/v4/blog_chrome.py` (~line 394).
- Rebuild: `python3 tools/build_v4.py`, then `python3 tools/reskin_articles.py` and
  `python3 tools/reskin_blog_hubs.py` **both with no --lang flag** — the article
  stylesheet is one content-hashed file shared by EN and AR, and a one-language run
  leaves the other language's 154 articles pointing at a deleted stylesheet.
- Verify the reskin stays idempotent: hash all outputs, run twice, hash again, compare.

Existing events that must keep working untouched (they fire from the v4 page builders):
`begin_checkout`, `add_payment_info` (page_checkout.py), `purchase` (page_order.py),
`generate_lead` (contact/checkout/simulators), `demo_scenario`, `demo_tab`,
`simulator_preset`, `simulator_tab`, `filter_articles`, `aiden_open`, `aiden_message`.

Do not push to `main` without asking me first.

---

## PROMPT 5 — Stitch Aiden to GA4 (two repos)

This change spans TWO repos and needs both deployed:

**A. Widget** — `public_html/js/aiden-chat.js` in
`/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO`

**B. Backend** — `/Users/nahid/Desktop/Nahid/AI Profit Lab/SmartChatBot/aiden-backend`
(separate GitHub repo, runs on Google Cloud Run, service `aiden-backend`,
region `us-central1`, project `adroit-minutia-496210-n1`).
Redeploy: `gcloud run deploy aiden-backend --source . --region us-central1` (~4 min).
Deploy from the WORKING TREE — `knowledge/` and `memory/` are untracked locally but
are hard `require()`s.

**The problem:** Aiden and GA4 describe the same visitors and cannot be joined.
The widget already computes, on every page load, a rich journey profile — a persistent
`visitor_*` id in localStorage, a per-tab page trail (`aidenJourney`, up to 20 pages),
seconds on page, max scroll depth, external referrer, visit count, days since last
visit, and the last 25 pages seen across all visits (see `visitorId()`, `trackJourney()`,
`trackPagesSeen()`, `behaviour()` around lines 80-220, and the `payload()` function
around line 1059). All of it is sent to the backend, which logs a row per message to
the `Aiden_Chat` Google Sheet tab via `routes/chat.js` (~line 217, `addRow`).

But **none of it is transmitted unless the visitor actually sends a chat message** —
for everyone who doesn't chat, it's computed and thrown away on unload.

Do three things:

1. **Widget → backend:** read GA4's `client_id` and `session_id` (via
   `gtag('get', 'G-SLR9GD3MJP', 'client_id', cb)`, which is async — handle that
   cleanly and never block the chat if it fails) and add them to the POST payload
   in `payload()`.

2. **Backend → sheet:** accept the two new fields in `routes/chat.js` and add them as
   columns on the `Aiden_Chat` row. The row currently has 14 columns starting at
   `new Date().toISOString(), sessionId, page, lang, country, visitorType, industry,
   email, phone, userMessage, reply, title, sources, messageCount`. Append, don't
   reorder — the sheet has existing rows. Sanitize both fields with the existing
   `clean()` helper; they're browser-supplied.

3. **Richer GA4 events from the widget.** It currently fires only `aiden_open` and
   `aiden_message` via the `track()` helper at line ~1117. Add: `aiden_first_message`
   (first message of a session only), `aiden_lead_captured` (when the widget captures
   an email or phone), and put the session's message count on `aiden_message` so I can
   see conversation depth. Send `page_type` on all of them.

**Critical deploy rule:** after editing the widget, run
`python3 tools/add_aiden_widget.py` to re-stamp the `?v=<hash>` on all 47 pages that
load it, or the edit never reaches anyone. Deploy the WEBSITE FIRST, then the backend.

Verify end to end: load a page, send Aiden a message, then confirm the new columns
actually appear in the `Aiden_Chat` sheet with real values (not empty strings).

Do not push or deploy without asking me first.

---

## PROMPT 6 — Build the journey report (run ~2 weeks after prompts 2-5 are live)

Working dir: `/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO`

Build `tools/build_journey_report.py` — queries the GA4 BigQuery export and emits a
local HTML dashboard of visitor journeys for aiprofitlab.io.

Data sources:
- **GA4 BigQuery export**, property `G-SLR9GD3MJP`, GCP project
  `adroit-minutia-496210-n1`. Ask me for the exact dataset name before writing queries.
  Raw event rows give: `user_pseudo_id`, `ga_session_id`, `event_name`,
  `event_timestamp`, `page_location`, `page_referrer`, `engagement_time_msec`, plus
  my custom params.
- **Custom events now on the site:** `page_exit` (with `dwell_seconds`, `max_scroll`,
  `page_type`), scroll milestones at 25/50/75/100, `begin_checkout`,
  `add_payment_info`, `purchase`, `generate_lead`, `aiden_open`, `aiden_message`,
  `aiden_first_message`, `aiden_lead_captured`, `demo_scenario`, `simulator_preset`,
  `filter_articles`.
- **Aiden_Chat Google Sheet** — one row per chat message, now carrying GA4 `client_id`
  and `session_id` columns so transcripts join to GA4 sessions on `user_pseudo_id`.

The report must answer:
1. **Session reconstruction** — for each session: landing page, ordered page sequence
   with dwell seconds per page, scroll depth per page, exit page, total duration.
2. **Aiden touchpoints** — which page they were on when they opened Aiden, how many
   pages preceded it, what they asked (joined from the sheet), and what they did after.
3. **Drop-off analysis** — ranked exit pages, exit rate per page, and for each: median
   dwell and median scroll depth before exit. Separate "read fully then left" from
   "bounced in 5 seconds" — they mean opposite things for content.
4. **Content performance** — per article: entrances, median dwell, scroll completion
   rate, onward click rate, and how often it precedes an Aiden open or a `generate_lead`.
5. **Path to conversion** — the page sequences that precede `generate_lead` /
   `begin_checkout` / `purchase`, and how they differ from sessions that don't convert.

Requirements:
- Segment EN vs AR, and mobile vs desktop.
- Output a self-contained HTML file (charts inline, no CDN) written to `out/`.
- Print the BigQuery bytes-scanned estimate before running, and use partition filters
  on `_TABLE_SUFFIX` so I don't scan the whole export every run.
- Cache query results locally so re-rendering the HTML doesn't re-bill the query.
- Match the existing conventions in `tools/` — read a couple of the existing scripts
  first (`tools/build_aiden_index.py`, `run_sitemap.py`) rather than inventing a style.

State clearly which numbers are measured and which are inferred, and flag anything
the data genuinely cannot answer.
