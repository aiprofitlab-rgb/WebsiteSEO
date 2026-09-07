# The project brief — `/en/onboarding/`

What a Smart Storefront buyer fills in **after** paying, so we know what site to
build. 103 questions over 11 sections, mostly tap-to-answer, with file uploads.

- **Page** — `public_html/en/onboarding.html` → `/en/onboarding/`. Served by the
  existing `.htaccess` rule 3 (`/en/<name>/` → `en/<name>.html`); no htaccess
  edit was needed. Carries `noindex, follow`, is not in the sitemap allowlist,
  and is skipped by `tools/build_aiden_index.py`.
- **Backend** — `tools/onboarding/brief-apps-script.gs`, a Google Apps Script
  bound to the brief spreadsheet. One row per brief, uploads to a Drive folder,
  and an email to the sheet owner both on submit and on manual edits.

> `/onboarding/` at the document **root** is a different page for a different
> product (the CEO-dashboard intake). Same word, no relationship.

## Turning it on

1. Create a Google Sheet, then **Extensions → Apps Script**, and paste
   `tools/onboarding/brief-apps-script.gs` in whole.
2. Run `setup` once and grant the permissions it asks for. It creates the
   `Briefs` tab, the Drive folder, and the on-change email trigger.
3. **Deploy → New deployment → Web app**, *Execute as: Me*, *Who has access:
   **Anyone***. Not "Anyone with a Google account" — buyers are not signed in,
   and that setting answers them with a login page.
4. Paste the `/exec` URL into `BRIEF_ENDPOINT` near the top of the script block
   in `public_html/en/onboarding.html`, then deploy the site.
5. Open the `/exec` URL in a browser. It should answer
   `{"ok":true,"service":"smart-storefront-brief-intake"}`.

`selfTest()` in the script editor writes a fake row end to end without touching
the site. Delete the row afterwards.

## Things that will bite

- **Editing the script does not redeploy it.** Deploy → *Manage* deployments →
  edit → Version: **New**. A *new deployment* mints a new `/exec` URL, and the
  site keeps posting to the old one.
- **Adding a question needs no change to the Apps Script.** The page sends the
  question labels with every brief, and the script appends any column it has not
  seen before to the END of the header row. Existing rows keep their positions.
- **The row is set to plain-text format before it is written, not after.**
  `setValues` writes the way a person typing would, so a WhatsApp number starting
  `+968` becomes `#ERROR!` and a long numeric id gets rounded. Reformatting
  afterwards does not undo it. Same trap as the CRM sheet.
- **Change emails are throttled to one per 10 minutes.** `onChange` fires per
  change, so tidying twenty cells would otherwise send twenty emails and burn the
  daily `MailApp` quota — after which a real brief's notification is the one that
  fails. A newly submitted brief suppresses the plain notice for 90 seconds and
  sends its own, with the whole brief in the body.
- **Uploads are capped at 12 MB per file and 25 MB per brief**, enforced in the
  page. Over that, the buyer is told to send it on WhatsApp instead.
- **File choices do not survive a page reload.** Answers are autosaved to
  `localStorage`; file contents would blow its ~5 MB quota, so only the names are
  kept and the files step says to pick them last.
- **With `BRIEF_ENDPOINT` empty the page still works** — the review screen falls
  back to WhatsApp, email, clipboard and a downloaded file. A failed POST shows
  the same routes and says plainly that it did not go through. Nothing on this
  page ever claims to have sent something it could not send.

## The OMR 50 add-on

Section 6 offers a logo and visual identity design as a paid extra. It is
**collected as an intent, not charged** — the page says it is added to the
invoice as a separate line and confirmed first. A `Yes` answer puts a
`[+ logo add-on]` tag in the notification email's subject and a starred line in
its body. The figure lives only in the `brandingAddon` field's option labels in
`onboarding.html`; it is not part of the seat ladder in `lib/tiers.js` and must
not be wired to it.
