# Free website demo landing page

`/en/free-demo/` (file `public_html/en/free-demo.html`, served by `.htaccess` rule 3 like every
`en/<name>.html`). Built 2026-10-25 as the new Google Ads landing page: a visitor watches six real
demos play on one laptop, types their business name onto the seventh screen, and asks for a free
demo homepage in their own brand, delivered within 24 hours by WhatsApp or email. No price on the
page (Nahid's call).

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
| Reveal the gap between now and where they could be | six finished demos, then their screen: "Designing next · Your business · Unveiled <live time>" (hero, the dive's wall, the slip) |
| Ask many times, with value between the asks | header chip, hero bar, "Make mine" after the dive, phone sticky bar, the slip |
| Qualify who gets the free work | "When do you want it live?" (This month / 1-3 months / Just looking), one tap, required, never a blocker |
| Clear CTA + a reason to act now | under the Send button: "Send now, and it's on your WhatsApp by Tue 27 Oct, 9:03 am", the 24-hour promise as a live time (also step 03). No invented scarcity |

Not used: a capacity line ("I make N demos a week"). It is Hormozi's strongest reason-to-act for
a service business, but it needs Nahid's real number before it can go on the page.

Removed in that edit: the hero paragraph, the "You already have everything a website needs"
intertitle, the proof paragraph (now "Not clients · names hidden"), the standalone three-steps
section (now the step list beside the form), two FAQs (free / call, both covered by the deal
chips), and the "Your name" and "What do you sell?" fields (the link field's placeholder asks
for either).

## "24 hours" must not read as "a template"

Nahid worried (2026-10-26) that a 24-hour promise tells visitors the demo is a template with their
name dropped in. The first fix was words: step 02 "I design it from your Instagram", the proof note
"no two alike", a closed FAQ "Is it a template?". Those stay.

On 2026-10-27 he asked for the hero and the animated part to stop implying it too, and for a wow
moment. The old hero was one CSS sample site with a Café/Trading/Boutique/Clinic picker and colour
dots, and the old peak flew "ingredients" into the slots of a skeleton site. Both literally showed a
template. They were replaced by the real work:

- **Hero, "six worlds, one screen".** One laptop that stays put while its screen cuts (a 0.6 s
  wipe) between six real lead preview demos in motion: the vet's cat slow-blinks, smoke rises off the
  bakhoor coal, a hand stirs the rest house's pool, the monkey peeks over the kids' salon wall, the
  café's clay lid lifts, the salon's butterfly opens its wings. The phone turns to each demo's phone
  version, the light behind the laptop takes its colour, and the giant word behind it its trade. A
  story-style segment bar (tap to jump, pause button) and a caption name the trade and place. The
  seventh screen is theirs: "Designing next", their typed name, "Unveiled <live time>". Typing jumps
  to it and holds there; the demos resume 3 s after they leave the field.
- **Peak, "dive in, pull out".** On dark ground a laptop shows the vet demo; the scroll dives into
  its screen until the demo fills the view ("Made for a vet clinic."), then pulls back: it was one of
  seven screens in a 2-3-2 brick, six demos that share nothing plus theirs, which then swaps into the
  centre ("Next: <name>"). On phones the same thing happens with the phone versions inside a phone
  frame. This replaced the demo rail; the rail's note ("Not clients · names hidden · no two alike")
  moved into it. On a desktop wall tile, the pointer plays that demo's clip.

Keep these claims true: the six demos are real pages made from each business's own material, none
are clients, and their names and logos are blurred before capture. Never add a demo whose name or
logo is the hero itself (Malek Al Pizza, Home Hunt, Fitness Hub and Esnad were left out for that).

## Arabic twin

`/free-demo-ar/` (`public_html/free-demo-ar.html`) is generated from this page by
`python3 tools/free-demo/build_free_demo_ar.py`. Re-run it after every English edit; it stops
if an English string it swaps has changed, and `--check` says whether the Arabic file is
stale. The Arabic lines a native speaker has not passed yet are listed in
`build/free-demo-ar-review.html`.

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

- GA4 events: `demo_name_typed`, `demo_world_pick` (a hero segment tapped; `world` = vet,
  perfume, resthouse, kidsalon, cafe, salon or yours), `demo_cta_click`, `demo_form_start`,
  `demo_request`, `demo_request_failed`, plus the site-wide `whatsapp_click`.
  `demo_cta_click` carries `cta_location` = `header`, `hero`, `peak` or `sticky`, so you can see
  which ask works. `demo_request` carries `timeline`. Gone on 2026-10-27 with the sample site:
  `demo_style_change` and the `proof` location. The request no longer sends `trade`/`palette`, so
  the sheet's "Style picked" column stays empty (the script's `clip()` turns a missing field into "").
- Google Ads: `ADS_WHATSAPP` (the existing "Storefront - WhatsApp tap") fires on WhatsApp links.
  `ADS_DEMO` is **empty** until a "Free demo - request" conversion action exists in account
  262-151-3399; paste its `AW-…/…` label there.
- Each sheet row carries first/last touch, click id (gclid) and the GA client id, so a won demo
  can later be imported as an offline conversion.
- Clarity stays on. Every region that renders the typed name carries `data-clarity-mask="true"`.
  Measured 2026-10-25: without those masks Clarity uploaded the business name; with them, a
  typed name, phone and contact name were all absent from its uploads. Add the attribute to any
  new element that shows the name.

## Images and clips

Two steps, both re-runnable:

1. `node tools/free-demo/capture_demo_clips.mjs [vet perfume ...]` records the six demos from their
   live Vercel deployments (dr-mansour-vet-clinic, al-shahama-frankincense, bustan-al-bida-resort,
   peekaboo-kids-salon, dukanah-cafe, sama-beauty-barka) on a paused clock: 3 s, 30 fps, 1280x800,
   plus a 390x844 phone clip of the vet for the phone dive. Before any frame it blurs, in the page,
   each site's brand and logo, every element whose own text names the business (Arabic diacritics
   stripped; `\b` is ASCII-only, so short Arabic names get Arabic-letter lookarounds), the café's
   whole headline (it ends "في دكانة") and the salon's giant "sama" word. Frames go to
   `.tmp/free-demo/clips/`, with a 3x3 sheet per clip (`PEEK=1` writes only the sheets). **Read
   every sheet by eye after a recapture**: a redeploy of a lead site can move a name into a new
   element. Scroll-driven heroes stop before they show a name: the kids' salon at 330 px (its
   headline turns into "بيكابو!" at about 400), and the rest house is recorded after its intro,
   whose leaves fly into the logo.
2. `python3 tools/free-demo/build_free_demo_assets.py` turns `.tmp/free-demo/src/` into hashed files
   in `public_html/assets/free-demo/` (clip MP4 for desktop and `-m` for phones, a first-frame
   poster at 1280 and 640, a wall tile, a 32 px glow, the phone stills, the café pair for the
   sample post) and rewrites the page's `.webp`/`.mp4` references.

Sizes as built 2026-10-27: desktop clips 98-504 KB (the pool's water is the heavy one), phone clips
37-147 KB, the first-paint poster 35 KB (14 KB on phones). Only the current clip and the next are
fetched, after `load` (or 4 s); never with reduced motion or Save-Data, and iOS Low Power Mode just
keeps the posters.

Hashes are in the filenames because `.htaccess` caches images for a year as `immutable`; hashed
MP4s (`name.<8 hex>.mp4`) got the same rule on 2026-10-27, and `.gitignore`'s `*.mp4` has an
exception for `public_html/assets/free-demo/` (the deploy uploads what git tracks).

## Motion traps hit while building (GSAP 3.15)

- Anything scrubbed that is not a transform is derived from the timeline's playhead in `paint()`,
  never tweened: the laptop lid around the centre screen (`--bz`), the other six screens, the
  captions, the heading, "Made for…" and "Next". ScrollTrigger's refresh jumps the playhead to the
  end and back, and a tweened CSS variable kept whatever value the rewind left it on.
- The dive is one transform: the cluster scales around the centre screen, whose centre is set as a
  px `transformOrigin` from `offsetLeft/Top` (layout values that ignore GSAP's transforms). The
  scale values are functions re-read on every refresh, so a resize mid-way recomputes the dive.
- GSAP folds a CSS `translate` into fixed pixels, so the cluster is centred with `left/top: calc()`,
  not `translate`.
- The hero's two layers per screen need their stacking order from the first paint (layer A in
  front). Without it the second layer, loaded ahead with the next demo, showed through: the laptop
  played the bakhoor demo while the caption said "vet".
- `.peak` has `overflow-x: clip` and the pin has `overflow: hidden`: the cluster is scaled far past
  the viewport during the dive, and mobile Chrome widens the layout to fit anything that pokes out
  sideways. `clip`, not `hidden`, on `.peak`, so the pin keeps working. Measure overflow with
  `isMobile` on and compare `scrollWidth` to the *requested* width.
- Reveals use `opacity`, not `autoAlpha`: `visibility:hidden` removed the FAQ toggles and the
  form's fields from the tab order until they scrolled in.
- The hero entrance moves the giant word's container with `y`; the scroll exit moves it with
  `yPercent`; the word swap moves the inner span. Three properties, so none records another's
  mid-animation value as its start.

## Not done

- The Arabic twin is live, but most of its lines still await the native reviewer (see
  `build/free-demo-ar-review.html`). No Arabic ad group points at it yet.
- `noindex` for now: ad traffic only. Indexing it is a choice to make, not a fix.
