# Free website demo landing page

`/en/free-demo/` (file `public_html/en/free-demo.html`, served by `.htaccess` rule 3 like every
`en/<name>.html`). Built 2026-10-25 as the new Google Ads landing page: a visitor types their
business name, sees it on a sample website, and asks for a free demo homepage in their own brand,
delivered within 24 hours by WhatsApp or email. No price on the page (Nahid's call).

## The offer, as the page states it

- Free: no payment, no card, no deposit.
- Within 24 hours, in English and Arabic.
- No call. It arrives by the channel the visitor picks, and nobody chases them.
- The one condition (a required checkbox): the finished design may be posted on
  @ai.profit.lab.gcc as a sample, **with the business name, logo and contact details removed**.
  The page promises it comes down on request.

If any of these change, change the hero headline and trust line, the deal chips, the FAQ and the
slip together.

## How the page is written (2026-10-25 edit, after Alex Hormozi's lead-magnet video)

Nahid asked for the page to follow "Watch This To Generate 1000s of Leads" (Hormozi,
youtu.be/Mst4hreQYl0) and to **show, not make people read**. That cut the always-visible words
from 575 to 342, which are now labels, buttons, captions and the form; the closed FAQ answers
went from 191 to 100. Keep it that way: a new idea goes in as something to look at, not a
paragraph.

| Hormozi's point | Where it lives on the page |
|---|---|
| Name the free thing as result + time frame | h1 "See your new website in 24 hours. Free." |
| Reveal the gap between now and where they could be | peak heading "Your Instagram today. Your website tomorrow." over the assembly |
| Ask many times, with value between the asks | header chip, hero bar, "Make mine" after the assembly, "Get one for my business" under the proof, phone sticky bar, the slip |
| Qualify who gets the free work | "When do you want it live?" (This month / 1-3 months / Just looking), one tap, required, never a blocker |
| Clear CTA + a reason to act now | under the Send button: "Send now, and it's on your WhatsApp by Tue 27 Oct, 9:03 am", the 24-hour promise as a live time (also step 03). No invented scarcity |

Not used: a capacity line ("I make N demos a week"). It is Hormozi's strongest reason-to-act for
a service business, but it needs Nahid's real number before it can go on the page.

Removed in that edit: the hero paragraph, the "You already have everything a website needs"
intertitle, the proof paragraph (now "Not clients · names hidden"), the standalone three-steps
section (now the step list beside the form), two FAQs (free / call, both covered by the deal
chips), and the "Your name" and "What do you sell?" fields (the link field's placeholder asks
for either).

## Where a request goes

The form posts `text/plain` JSON to a Google Apps Script web app:

| | |
|---|---|
| Sheet | "Free demo requests", id `10GIRwi7GqSZZuhTnj-3kVaIO80ZNEHqlgin5uVRAiWY`, tab `Requests` |
| Script | id `1GGUkj0LvdBGwPuMOYk2CmHFKaIbRoSKm9eaMj6_1g0AeQu5_2uYRSGBs`, source of record `tools/free-demo/free-demo-apps-script.gs` |
| Deployment | `AKfycbyS5sr2u44PgGtGu7TE3rzqSkutve39G4-AWA9Iu0Bx8GGucj1jgr41ioRwBVDh7EtA` (= `DEMO_ENDPOINT` in the page) |
| Logos | Drive folder "Free demo logos" |

Each request: one row (with a **Due by** column = received + 24h, Muscat time), an email to the
script owner with a `wa.me` link to the lead, and, when the visitor chose email, a short
confirmation to them from the owner's Gmail with `replyTo: hello@aiprofitlab.io`.

**Timeline** (the qualifier answer) is the last column, and the owner email shows it as
"WANTS IT" under the due time. New columns only ever go on the end: `ensureSheet()` extends an
existing tab's header in place. The **Sells** and **Name** columns stay but are empty from
2026-10-25 on, because the page no longer asks for them.

**Pending as of 2026-10-25:** the repo copy has the Timeline column, but the live script does
not yet. The push was not run (auto mode treats it as a production deploy). Until it is, the
script ignores the `timeline` field and saves everything else. Run the push and redeploy below
before the page goes live. The live copy matched the repo copy apart from this edit on
2026-10-25.

**The script must be authorised once by its owner** (open the sheet, Extensions > Apps Script,
run `setup`). Before that, the `/exec` URL answers "access denied" and every request fails. The
page then keeps the visitor's details on screen with email and WhatsApp links pre-filled with the
request. It never shows "Received" for a request the sheet did not save.

Script edits: put the file in a clasp folder (`.clasp.json` with the script id above), then
`npx @google/clasp@2.4.2 push -f`, `version`, and `deploy -i <deployment id> -V <n>`. A new
deployment would change the URL; redeploying the same id keeps it.

## Tracking

- GA4 events: `demo_name_typed`, `demo_style_change`, `demo_cta_click`, `demo_form_start`,
  `demo_request`, `demo_request_failed`, plus the site-wide `whatsapp_click`.
  `demo_cta_click` carries `cta_location` = `header`, `hero`, `peak`, `proof` or `sticky`, so you
  can see which ask works. `demo_request` carries `timeline`.
- Google Ads: `ADS_WHATSAPP` (the existing "Storefront - WhatsApp tap") fires on WhatsApp links.
  `ADS_DEMO` is **empty** until a "Free demo - request" conversion action exists in account
  262-151-3399; paste its `AW-…/…` label there.
- Each sheet row carries first/last touch, click id (gclid) and the GA client id, so a won demo
  can later be imported as an offline conversion.
- Clarity stays on. Every region that renders the typed name carries `data-clarity-mask="true"`.
  Measured 2026-10-25: without those masks Clarity uploaded the business name; with them, a
  typed name, phone and contact name were all absent from its uploads. Add the attribute to any
  new element that shows the name.

## Images

`python3 tools/free-demo/build_free_demo_assets.py` turns the originals in `.tmp/free-demo/src/`
(gitignored) into hashed WebP files in `public_html/assets/free-demo/` and rewrites the page's
references. Hashes are in the filenames because `.htaccess` caches every image for a year as
`immutable`.

- 16 sample photos (café, trading, boutique, clinic; 4 each) were generated with kie.ai seedream
  for the sample websites. They show no real business.
- 12 proof screenshots are lead preview sites (perfume, rest house, vet, café, ladies' salon,
  kids' salon) captured with names and logos blurred **in the page before capture**. Filenames
  carry the trade, never the business. Malek Al Pizza, Home Hunt, Fitness Hub and Esnad were
  left out because their name or logo IS the hero. Re-check by eye after any recapture.

## Motion traps hit while building (GSAP 3.15)

- The peak's slot fill (`--on`) and colour (`--paint`) are computed from the timeline's playhead
  in `fill()`, not tweened. Tweening the CSS variables left the site complete at progress 0:
  ScrollTrigger's refresh jumps the playhead to the end and back, and the rewind wrote "0" then
  "1". The flying cards are `fromTo` with `immediateRender:false, lazy:false` for the same reason.
- GSAP folds a CSS `translate` into fixed pixels, so the flying cards and the peak phone are
  centred with `xPercent/yPercent` (the `.gs` class drops the CSS translate).
- Draggable `type:"scrollLeft"` wraps the rail's children in a block div; the cards live in
  `.rail-track` so they stay a row.
- Reveals use `opacity`, not `autoAlpha`: `visibility:hidden` removed the FAQ toggles and the
  form's fields from the tab order until they scrolled in.
- `.peak` has `overflow-x: clip`. The peak phone waits at `x: 70` before it slides in, and on phones
  Chrome widened the whole layout to fit it, about 34px of sideways scroll at 320px. `body`'s
  `overflow-x` does not stop that. Use `clip`, not `hidden`, so the pin keeps working. Measure
  overflow with `isMobile` on and compare `scrollWidth` to the *requested* width: mobile
  `innerWidth` grows with the overflow, so `scrollWidth - innerWidth` reads 0 and hides it.

## Not done

- No Arabic version yet. An Arabic ad group needs one (and the Arabic in the mock phone is
  limited to strings harvested from the reviewed Arabic site).
- `noindex` for now: ad traffic only. Indexing it is a choice to make, not a fix.
