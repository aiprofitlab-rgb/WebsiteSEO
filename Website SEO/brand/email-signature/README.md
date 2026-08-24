# Email signature — nahid@aiprofitlab.io

Layout: circular founder photo + brand wordmark on the left, hand signature,
name, title, contact block and social icons on the right. ~442 px wide.

## Files

| File | What it is |
|---|---|
| `nahid-signature.html` | The signature itself. This is the thing you copy. |
| `../../tools/build_email_signature_assets.py` | Rebuilds every image below from source. |

Images live in `public_html/assets/email/` and are published to
`https://aiprofitlab.io/assets/email/…` by the FTP deploy on push to `main`:

| Image | Source | Shown at |
|---|---|---|
| `nahid-signature.png` | `~/Desktop/Nahid/AI Profit Lab/signature_luxury_blue.PNG`, green screen keyed out | 240 × 142 |
| `nahid-signature-white.png` | same art flattened onto white (dark-mode fallback) | 240 × 142 |
| `nahid-avatar.png` | `brand/photos/nahid-founder-2026-master.jpeg`, circular crop | 120 × 120 |
| `apl-wordmark.png` | `public_html/assets/brand/wordmark-primary.svg` | 120 × 21 |
| `icon-{whatsapp,linkedin,instagram,youtube,facebook}.png` | the same glyph paths the site footer uses | 28 × 28 |

All images are 2× resolution so they stay sharp on Retina.

**The images must be deployed before the signature renders anywhere.** Until
`https://aiprofitlab.io/assets/email/nahid-signature.png` returns a 200, every
recipient sees broken image boxes.

## Install

### Gmail (web) — do this once, on desktop
1. Open `nahid-signature.html` in Chrome (double-click the file).
2. Click into the page, `Cmd+A`, `Cmd+C`.
3. Gmail → ⚙ → *See all settings* → *General* → *Signature* → *Create new*.
4. Click into the signature box and `Cmd+V`. Do **not** retype anything —
   Gmail keeps the image URLs and the links as pasted.
5. Set it as the default for *New emails* and *On reply/forward*.
6. *Save Changes* at the bottom of the page.

Gmail's mobile apps pick up the desktop signature automatically once you turn
on *Settings → your account → Mobile signature → use desktop signature*.

### Apple Mail
Mail → Settings → Signatures → create one → paste as above. If Mail strips the
formatting, uncheck *Always match my default message font*.

### Outlook (Mac / Windows / web)
Outlook's signature editor also takes a paste from the browser. On Outlook for
Windows, images are pulled from the URLs — they are not embedded — so the
signature stays small.

## Notes

- **Dark mode.** The signature ink is dark navy on a transparent background. A
  few clients (Gmail Android in dark theme, Outlook.com dark) darken the
  backdrop behind it and the strokes get hard to read. If that bothers you,
  edit `nahid-signature.html` and change `nahid-signature.png` to
  `nahid-signature-white.png` — same art on a white plate.
- **Changing the details.** Everything is plain text inside the tags: name,
  `FOUNDER · AI PROFIT LAB`, the email, the phone, the city, the CR line. Edit
  the file, reopen it in Chrome, re-copy, re-paste into Gmail.
- **Adding a channel.** Add a `<td>` in the icons row and drop a matching
  `icon-*.png` into `public_html/assets/email/`. The glyph paths and the
  circle rendering are in the build script.
- **Do not rename the PNGs after the signature is out in the wild** — every
  email already sent points at those URLs.
