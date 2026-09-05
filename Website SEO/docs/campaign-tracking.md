# Campaign tracking — flyers, ads and outreach

Built 2026-09-05 for the Smart Storefront launch. This is the layer that answers
**"which channel produced this buyer"**, and it is deliberately separate from the
behavioural measurement that was already in place.

## What was already live (unchanged by this work)

All ~368 pages carry, and have since 2026-08-25:

| Thing | Where | What it gives you |
|---|---|---|
| GA4 `G-SLR9GD3MJP` | every page head | sessions, pages, events |
| Microsoft Clarity `y7wcjlyamc` | every page head | session recordings, heatmaps, rage clicks |
| `/js/apl-analytics.js` | every page, `defer` | `scroll_depth` 25/50/75/100, `page_exit` (dwell, max scroll, exit intent), `cta_click`, `outbound_click`, and the `page_type` / `content_language` / `article_slug` dimensions every other event inherits |
| BigQuery export | dataset `analytics_529946999` | raw per-event data, from 2026-08-25 onward, not retroactive |

Funnel events already fire from the pages themselves: `claim_submitted`,
`seat_payment_started`, `seat_paid`, `view_promotion`, `add_to_cart`,
`receipt_uploaded`, plus `roast_*` on the quiz.

**None of that told you where anybody came from.** That is what this adds.

## The three parameters, and the one that was missing

```
utm_source    WHERE it was seen        flyer, linkedin, whatsapp, instagram
utm_medium    WHAT KIND of placement   print, outreach, social, paid_social
utm_campaign  WHICH push               smart_storefront_launch
utm_content   WHICH VARIANT            batch1, reel_a, card_back
```

**GA4 needs `utm_medium` to put a session in a channel.** Source alone gets the visit
filed under "Unassigned", which is the bucket nobody reads.

The printed flyer encodes `https://aiprofitlab.io/en/smart-storefront/?utm_source=flyer`
and nothing else — verified in the QR asserts in
`Core4/ColdOutreach/Smart Website Campaign/smart-storefront-flyer/source/finalize_30cm.py`.
That artwork is baked into a 4252×1890 master and cannot be changed for a batch already
printed, so **the storefront page patches it on arrival**: a small synchronous script
in the head, above the gtag snippet, fills in `utm_medium=print` and
`utm_campaign=smart_storefront_launch` when they are absent. It only ever *adds* missing
keys, so any future link that carries its own medium wins.

That block exists twice — in `public_html/en/smart-storefront.html` and in the
`HEAD` string of `tools/build_smart_storefront_ar.py`. **Keep the two tables identical.**

### Never hand out an untagged link again

```bash
python3 tools/campaign_link.py --list
python3 tools/campaign_link.py linkedin_dm --content batch1
python3 tools/campaign_link.py whatsapp --content warm_list --ar
```

Every preset carries a medium. That is the whole point of the table.

## First touch vs last touch

`/js/apl-analytics.js` keeps two touches in `localStorage` under `apl_attr`:

- **first** — written once, **never overwritten**. The channel that introduced this person.
- **last** — the most recent *campaign or referred* visit. A direct visit deliberately
  does not overwrite it (the same "last non-direct" rule GA4 uses), or every returning
  visitor would decay to `direct` and every channel would look useless.

This is the single most important part. Somebody scans the flyer on Tuesday, thinks about
it, and comes back on Friday through a Google search. GA4's default reporting calls that a
Google conversion and the flyer looks worthless. The ledger now records both, so it does not.

A click id alone (`fbclid`, `gclid`, `li_fat_id`, `ttclid`, `msclkid`…) is enough to
attribute a paid click even when the UTMs were stripped by a shortener or an in-app browser.

## What now lands in the ledger

`Seat_Claims` grew 13 columns, appended at the end (the sheet is live — columns may only
ever be appended, or every existing row is relabelled):

```
First source | First medium | First campaign | First seen at
Last source  | Last medium  | Last campaign  | Landing page
Click ID     | Touches      | Days to claim
GA client ID | GA session ID
```

`GA client ID` is the join key — every row in the BigQuery export is filed under it, so a
claim carrying it can be joined to everything that buyer read *before* they filled the form in.

### The bug this fixed on the way past

`lib/sheet.js` writes with `valueInputOption: "USER_ENTERED"`, which parses every cell as
though a person had typed it. It had **no text guard**, so:

- A prospect typing `+968 9924 5250` stored as `#ERROR! (Formula parse error.)` — the
  phone number, which is how Nahid contacts them, destroyed silently.
- A GA4 client id (`1974159239.1787684904`) would have stored as the rounded float
  `1974159239.17876`, unjoinable.
- A visitor could write a live formula into the ledger through a crafted `utm_source`.

Every non-numeric, non-date cell now goes through `asText()`. Money columns stay numeric so
the sheet's own sums keep working; timestamps stay dates so it still sorts. Covered by
`test/attribution.test.js` — the sibling Aiden CRM sheet had the identical bug found live
on 2026-08-25, and it is documented in the `crm-sheet-user-entered-trap` note.

## The question the code cannot answer: "how did you hear about us?"

Added 2026-09-05, Nahid's call, in the same session as everything above and for the
reason above: **everything on this page can only see what arrived through a link.**
It is blind to a flyer handed over in person, a name passed on in a meeting, a WhatsApp
forward that stripped the query string, and — the expensive one — anyone who heard the
brand out loud and then typed it into Google, which lands as `Last source: google` and
looks exactly like search doing work it did not do.

So every buyer is now asked, on **both** forms that take money:

| Form | Pages | Ledger | Column |
|---|---|---|---|
| Storefront claim | `/en/smart-storefront/`, `/smart-storefront-ar/` | `Seat_Claims` | `Notes` |
| Checkout | `/en/checkout/`, `/checkout-ar/` | `Checkout_Orders` | `Notes` |

The Silent Buyer Test form on `/en/contact/` is deliberately **not** included: it posts
nothing to a server, it only opens a pre-written WhatsApp message, so there is no cell
for an answer to land in.

**A dropdown, and the value is a stable id — never the label.** That is the whole design.
The Arabic page shows `منشور مطبوع` and posts `flyer`, exactly as the English one does, so
the printed flyer is *one* row in the count instead of two; and a label can be reworded on
either page without splitting last month's numbers. The mapping back to one English label
happens server-side, in `lib/heard.js` — which exists **twice**, once in each service
(`storefront-offer-api/lib/heard.js` and `backend/checkout-api/lib/heard.js`). Keep the ids
identical across those two files and the four `<select>` blocks, or the two ledgers cannot
be counted together. The ids today:

```
flyer  google  ai  instagram  linkedin  whatsapp  referral  inperson  other
```

Two answers — `referral` and `other` — open one more box, because "someone recommended
you" names a person who is already selling for us and "somewhere else" is worthless
without the else. The box is **emptied when it closes**, so a name typed under a
recommendation cannot survive a change of mind and be filed against Google search.

**Required in the browser, optional at the server.** The form will not submit without an
answer; both services accept a claim or an order that carries none. A page cached from
before this shipped must still be able to buy, and a lost lead costs more than a blank
cell — the same rule the thirteen columns above already follow.

**The prefix is load-bearing.** Every answer is written as `Heard about us: <label>`, so
the column can be filtered on one string, and — since it is the first thing in the cell —
Sheets can never read what the buyer typed as a formula.

Where the four `<select>` blocks live, because none of them share a file:

- `tools/v4/page_checkout.py` → `HEARD` + `heard_field()`, rendered into **both**
  checkouts (the Arabic one calls the same function).
- `public_html/en/smart-storefront.html` → hand-written, in `#claimForm`.
- `tools/build_smart_storefront_ar.py` → the `BODY` string. Same duplication rule as the
  UTM-correction block above: **keep the two tables identical.**

Tests: `test_heard_about.js` (22, both checkouts), the seven new checks in
`test_claim_attribution.js`, `backend/checkout-api` `npm test` = **49** (was 38),
`storefront-offer-api` `npm test` = **107** (was 100).

## Meta Pixel — built, and OFF

`var META_PIXEL_ID = '';` near the bottom of `/js/apl-analytics.js`. Empty means **not one
byte** goes to Meta and no request is made. To turn it on:

1. Paste the pixel id from Meta Events Manager (Data sources → your pixel, 15–16 digits).
2. `python3 tools/stamp_analytics_version.py`
3. Commit and push.

It needs no page edits. It listens to the `dataLayer` that gtag already pushes to and
translates: `claim_submitted` → `Lead`, `seat_payment_started` → `InitiateCheckout`,
`seat_paid` → `Purchase` (with `value` and `currency: OMR`), `add_to_cart` → `AddToCart`.
Scroll and page events are deliberately **not** forwarded — training Meta's optimiser on
people who scroll burns budget finding more people who scroll.

## The cache trap

`.htaccess` serves every `.js` as `max-age=31536000, immutable`. A stable filename means an
edited script never reaches a returning visitor — or a CDN edge — for a **year**. The `?v=`
token is a content hash, so after **any** edit to `apl-analytics.js`:

```bash
python3 tools/stamp_analytics_version.py          # rewrite every page
python3 tools/stamp_analytics_version.py --check  # exit 1 if any are stale
```

`tools/v4/kit.py` computes the token, so build_v4 and the reskins are always right.
`tools/build_smart_storefront_ar.py` used to **hardcode** it; that was fixed here, and it
now computes it the same way. The stamper exists for the hand-maintained pages no builder
owns — `en/smart-storefront.html` and `en/pay.html` among them.

## Tests

```bash
node test_attribution.js            # 33 unit checks, no browser
node test_attribution_browser.js    # 16 real-browser checks, EN + AR   (needs the server below)
node test_claim_attribution.js      # 25 checks: the claim form actually posts it, EN + AR
node test_heard_about.js            # 22 checks: the checkout's question gates, EN + AR

python3 -m http.server 8777 --directory public_html   # for the three browser tests
```

Backends: `npm test` in `SmartChatBot/storefront-offer-api` — **107 tests** (was 100);
in `Website SEO/backend/checkout-api` — **49 tests** (was 38).

## Still owed

- **A Meta Pixel ID.** The slot is built and dark.
- **Offline conversion import.** The real conversion — `Status = Confirmed` — is set by
  hand in the sheet days after payment. No ad platform can optimise toward it until it is
  fed back. This matters more than the pixel itself once spend starts.
- **A consent decision.** See the PDPL note below.
- **GA4 custom definitions.** `first_source`, `first_medium`, `first_campaign` are sent as
  **user-scoped** properties. They are collected either way, but are not queryable in
  reports until registered in Admin → Custom definitions. That is a console step, and the
  console cannot be reached from this machine (GA4 and GCP are under different Google
  accounts — see the `ga4-bigquery-export` note).

## Oman PDPL

Royal Decree 6/2022. The transitional period **ended 5 February 2026**, so enforcement is
active now, overseen by MTCIT. It requires express consent to process personal data, and
the fine bands are up to OMR 2,000 for regulatory violations and up to OMR 500,000 for
**data-transfer** breaches.

Where the site stands:

- **The claim form is the well-handled part.** It has a required consent checkbox and the
  API rejects a claim without it (`consent_required`).
- **The analytics layer is the exposure.** GA4, Clarity and (once enabled) Meta all send
  data outside Oman with no notice and no consent gate — and cross-border transfer is the
  band carrying the OMR 500,000 ceiling.
- **Clarity is the sharpest edge**, because session replay can capture what people type.
  Its input-masking setting is a dashboard option that **cannot be verified from this
  machine** — check it in the Clarity console before spend starts.

This is a decision, not a task: adding Google Consent Mode v2 plus a banner costs some data
volume and is a real build. Nothing here is legal advice.
