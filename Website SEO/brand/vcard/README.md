# Contact QR — Nahid Abyari

Scan it and the phone opens its **add contact** sheet already filled in. One tap
on Save and you are in their address book. The whole vCard is encoded *inside*
the QR, so it works with no signal, no landing page, and nothing to keep alive.

Rebuild everything with:

    python3 tools/build_vcard_qr.py            # what is committed here
    python3 tools/build_vcard_qr.py --no-photo # drops PHOTO: 441B, 81 modules

## Files

| File | Use it for |
|---|---|
| `qr-cream.png` / `.svg` | **The default.** Deep green modules and gold eyes on brand cream. |
| `qr-dark.png` / `.svg` | Cream modules on near-black, pale gold eyes. For dark layouts. |
| `qr-mono.png` / `.svg` | Flat black on white, square modules, no mark. Give this to a print vendor who wants pure contrast, or use it anywhere the coloured one has to survive a fax-grade reproduction. |
| `card-cream.png` / `card-dark.png` | Finished 1080×1350 cards — wordmark, QR, name, title, caption. Post as-is to WhatsApp, LinkedIn or Instagram, or print. |
| `nahid-abyari.vcf` | The same contact as a file, for AirDropping or attaching to an email. |
| `icon-reversed.png` | Build artifact: the brand mark recoloured for dark grounds. |
| `fonts/` | Marcellus + IBM Plex Mono (both OFL), vendored so the build is reproducible offline. |

Use the **SVG** for anything printed and the PNG for screens. The PNGs are
2328 px, which is 300 dpi at 197 mm.

## What is in the card

Name, `Founder`, `AI Profit Lab`, the mobile, `nahid@aiprofitlab.io`,
`aiprofitlab.io`, Muscat / Oman, and LinkedIn, Instagram and WhatsApp as
labelled links. It is vCard **3.0** — not 4.0 — because 3.0 is what iOS Contacts
and Google Contacts both import cleanly.

Two things worth knowing:

- **The photo probably will not show up.** `PHOTO;VALUE=URI` points at the
  avatar on aiprofitlab.io, and both iOS and Android are inconsistent about
  fetching a remote photo on import — many builds just ignore it. Embedding the
  image instead would blow the QR far past a scannable size, so a URI is the
  only option. It costs 70 bytes and 8 extra modules; `--no-photo` buys those
  back if you would rather have the sparser code.
- **WhatsApp is a link, not a button.** It imports as a labelled URL
  (`wa.me/96899245250`). Tapping it opens WhatsApp; it does not become a native
  WhatsApp row in the contact.

## Printing it

The symbol is **89 modules** across plus a 4-module quiet zone each side, so:

| Printed width | Module size | Verdict |
|---|---|---|
| 50 mm | 0.52 mm | Comfortable. Use this on a card back or a flyer. |
| 40 mm | 0.41 mm | Fine for a phone held at normal distance. |
| 35 mm | 0.36 mm | Floor. Do not go below this. |

**Never crop the quiet zone.** The pale margin around the code is part of it —
place the QR on flat cream or flat near-black, not over a photo or a gradient.

## Why it looks the way it does

Three decisions in `tools/build_vcard_qr.py` are load-bearing, and all three were
arrived at by decoding the output rather than by eye. If you restyle this, keep
them:

1. **The finder eyes are square.** Rounding them looks better and breaks the
   code. A scanner locates a symbol by the 1:1:3:1:1 dark:light run ratio across
   a finder pattern, and rounded corners skew that ratio on every off-centre
   scanline. A corner radius of even 0.9 modules stopped it decoding at every
   size tested. The brand shows up in the eye *colour* instead.
2. **The eye colour has to binarise to the same side as the data modules.** The
   first cut used `#D89234` gold on the dark card. It sits at luminance 0.354
   against a 0.436 midpoint, so scanners read those eyes as background and the
   finder pattern inverts. The dark card uses pale gold `#E8C98F` (0.609) for
   that reason alone. On cream, `#BA7517` (0.232 against a 0.449 midpoint) is
   safely on the dark side.
3. **The area behind the centre mark is cleared, not painted over.** Those
   modules are skipped entirely, so the mark sits on plain ground. An earlier
   version pasted the opaque cream-tile logo onto the dark card, which put a
   solid ~11×11-module blot in the middle of the symbol and stopped it decoding
   at every scale, inverted or not.

Rounded *data* modules are safe — verified at zero misread modules — which is
where the softness in the code comes from.

## Changing the details

Everything is plain text at the top of `tools/build_vcard_qr.py`, in `LINES`.
Edit, re-run, done. Two cautions:

- Adding fields grows the symbol. At 511 bytes it is a version 18 code; there is
  headroom to about 620 bytes before it steps up to version 20 and the modules
  get meaningfully smaller for a given printed size.
- Re-run the checks after any edit. The decode harness used to validate this set
  is not committed — it needs `zxing-cpp`, which is not a project dependency:

      python3 -m venv /tmp/qrvenv && /tmp/qrvenv/bin/pip install zxing-cpp pillow
      # then decode each output and compare against nahid-abyari.vcf

  Do not trust OpenCV's `QRCodeDetector` for this. It fails on perfectly good
  version-18 symbols and cannot read inverted codes at all, which sent this
  build down a false trail twice.
