# Brand discovery questionnaire and brand book

A questionnaire you can send to any company. About 20–25 minutes, 7 parts, 22 short
screens, in English and Arabic. As the company answers, a brand sheet fills in beside the
questions. What they get from it is a **brand book**: the kind of logo that suits them, a
first draft of their name as a logo, their colours, fonts and voice. You make the book
from their brief with one command, check it, and send it yourself. Nothing is sent to
them automatically.

Until 2026-11-13 this was an intake for paying brand clients: it also asked for
deliverables, deadline, budget and who approves the work, and it ended with a kickoff
call. Those four questions are gone. Their Sheet columns stay, empty on new rows.

## URLs

| Language | URL | File |
|---|---|---|
| English | https://aiprofitlab.io/en/brand-discovery/ | `public_html/en/brand-discovery.html` |
| Arabic | https://aiprofitlab.io/ar/brand-discovery/ | `public_html/ar/brand-discovery/index.html` |

Both are `noindex`, in no sitemap and in no nav. Clarity is off. The company can switch
language on the page. The Arabic is unreviewed and the page says so.

## Personal links

Add these to either URL. Each fills an empty answer only, so someone who has already
started is never overwritten.

| Parameter | Does | Example |
|---|---|---|
| `b` | Business name, and "Prepared for …" on the welcome screen | `b=Nakheel%20Roastery` |
| `n` | Contact name | `n=Sara` |
| `ig` | Instagram handles, comma separated (fills "Social media handles") | `ig=nakheel.roastery` |

    https://aiprofitlab.io/en/brand-discovery/?b=Nakheel%20Roastery&n=Sara&ig=nakheel.roastery

## What happens when they press Send

Same backend as before (`tools/brand-discovery/brand-discovery-apps-script.gs`, the
"Brand discovery briefs" Sheet): one row per brief, uploaded files in a Drive folder, and
an email to you with the brief attached as `brand-discovery-<name>.md`.

The `.md` now ends with the raw answers inside an HTML comment
(`<!-- brand-book-data … -->`). That is what the brand book tool reads. It also shows at
the bottom of the email and the "Full brief" cell, where it can be ignored. The company's
own PDF and "Copy answers" don't carry it. The Apps Script did not change.

## Making the brand book

1. Save the `.md` attachment from the notification email (for example to Downloads).
2. Run:

       python3 tools/brand-discovery/build_brand_book.py ~/Downloads/brand-discovery-<name>.md

3. Open `.tmp/brand-books/<name>/review-notes.md` first. It is for you only. It covers
   the logo scores, the palette, the monogram initials, an Arabic spelling to confirm,
   unanswered questions, and a reminder to look at their uploaded files. For a refresh or
   rebrand, look at their current logo in Drive, because the draft doesn't see it.
4. Read every page of `brand-book.html` in Chrome. To change wording, edit the HTML,
   then reprint:

       python3 tools/brand-discovery/build_brand_book.py --reprint .tmp/brand-books/<name>/brand-book.html

5. Send `brand-book.pdf` to the company.

`--sample` builds the fictional sample in `tools/brand-discovery/sample-brief.json`, so
you can see what a company receives. A `.json` file holding the answers works as input too.

Output goes to `.tmp/`, which is gitignored. Keep it that way: this repo is public, and a
brand book carries the company's name, email and phone.

## What is in the book

About 15–17 A4 landscape pages, in the company's own colours and fonts. Pages with
nothing to show are left out.

Cover · contents · who we are · story and values · who we serve · where we stand ·
character · personality and voice · **logo type** · **draft logo** · using the logo ·
colour · typography · look and feel · where people will see you · before this is final ·
back page (prepared by AI Profit Lab, with the legal entity).

The book is in English. It quotes Arabic answers as the company wrote them and uses
Arabic fonts for them.

## How it decides

Everything is a fixed rule over the answers, so the same brief always gives the same book.
Nothing goes to an AI and no credits are spent.

- **Logo type:** each of the six kinds (wordmark, monogram, symbol + name, symbol only,
  badge, character) collects points:
  - +3 for each kind the company picked itself;
  - points for the length of the name;
  - points for where they are seen (profile pictures favour a monogram; signs, vehicles
    and uniforms favour bold shapes; packaging favours a badge);
  - points for the characters (archetypes) they chose, their price position, their
    classic/modern, simple/ornate and serious/playful sliders, and English + Arabic.

  The top score wins. The book prints the reasons and the score of every kind. It also
  names a compact version for small spaces (a monogram, or the symbol alone). It adds a
  badge when packaging or a storefront makes one useful.
- **Draft logo:** their name set in the lettering they picked, in their colours, on paper,
  on the main colour and on ink, plus the monogram, the badge and the English + Arabic
  pair where relevant.
  - It is **typeset, not drawn**, and the book says so.
  - A symbol or character is never invented. Where one is recommended, the draft shows a
    marked empty box instead.
- **Colour:** their picked colours, adjusted for their "soft & muted / bright & bold" and
  "warm / cool" answers.
  - A hex code typed in "Anything specific about colour?" is kept exactly.
  - A deep shade, a tint, ink and paper are derived from the main colour.
  - With no colours picked, the main colour is suggested from their leading character,
    and the book says so.
  - A light main colour (yellow, sand) is not used for the logo on white. The deep shade
    is used there instead.
- **Fonts:** the lettering they picked, matched to free Google Fonts, with an Arabic
  partner (for example classic serif → Cormorant Garamond + Source Sans 3, Amiri +
  Noto Naskh Arabic). The fonts are downloaded once into `.tmp/brand-books/_fonts/` and
  embedded, so Arabic prints properly shaped.
- **Voice:** each of the three voice sliders gives a principle plus a "do / don't" pair of
  example sentences, marked as tone examples only.

## Editing

- **The form:** edit only `tools/brand-discovery/brand-discovery.src.html`, then run
  `python3 tools/brand-discovery/build_brand_discovery.py`. The English question label is
  the Sheet column, so renaming one starts a new column.
- **The book:** `tools/brand-discovery/build_brand_book.py`. The option tables at the top
  (colours, characters, logo kinds, lettering, this-or-that, sliders, channels) must match
  the form. The tool checks them against the form's source on every run and stops with a
  clear message if a key was added, renamed or removed there.

## Limits

- Briefs sent before 2026-11-13 have no data block. The tool says so. Make a `.json` of
  the answers instead, keyed like the form.
- Uploaded files (their current logo, references) stay in Drive. The book lists reference
  links but doesn't use the images.
- No Arabic edition of the book yet.
- The PDF needs Google Chrome installed (it prints headless). Without Chrome you get the
  HTML only: print it from a browser (landscape, no margins, background graphics on).
