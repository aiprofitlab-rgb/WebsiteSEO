# AI Profit Lab — Brand Book

*Owner: Nahid Abyari · Last updated: 2026-08-19*
*Canonical visual system: the teal/amber editorial system. Supersedes the old blue/red/black identity.*

---

## 1. Brand foundation

**Brand name:** AI Profit Lab
**Legal entity:** Lotus Gulf International (لوتس الخليج العالمية ش ش و), CR 1570092 — AI Profit Lab
is a *brand*, not a company. Contracts, invoices, gateways and KYC forms take the legal entity.

**North star:** to become the most trusted AI adoption consultancy in Oman, then the GCC.

**Positioning:** Done-for-you AI automation for trading and distribution SMEs in Oman and the
GCC. We audit the bottleneck, build the system, run it, and train the team — in plain language,
priced in OMR.

**Category code:** consultancy, not SaaS startup. Editorial, considered, human. Not neon,
not gradient-mesh, not "AI startup."

**Official slogan (locked, Nahid-supplied):**
> Every success starts with insight — كل نجاح يبدأ برؤية

---

## 2. Voice

| Pillar | What it means in practice |
|---|---|
| **Plain** | Say it the way you'd say it to a business owner over coffee. No jargon, ever. |
| **Honest** | State what is *not* included as clearly as what is. Never publish a number we can't source. |
| **Founder-voiced** | First person where a person is speaking. Signed work builds trust faster than a logo. |
| **Specific** | "A bilingual AI agent that answers buyers at 4am, on a Friday, during Eid" beats "24/7 availability." |
| **Unhurried** | No fake countdowns, no manufactured panic. Scarcity is only used where it is genuinely real. |

**Recurring trust devices:**
1. The named guarantee, stated in full, in the founder's own voice.
2. The explicit "what's not included" block.
3. Working demo tools used as proof-by-demonstration in place of testimonials we don't have yet.
4. Real numbers only — where a live figure can't be fetched, say so rather than show a made-up one.

**Words to use / avoid:** see `01-persona-and-avatar.md` §6.

---

## 3. Colour palette

Copy-paste tokens (already live in `public_html/en/*-new.html` and `en/smart-storefront.html`):

```css
:root{
  --teal-950:#072B22;   /* deepest ground, footers */
  --teal-900:#0A3D30;   /* dark sections, logo ink */
  --teal:#0F6E56;       /* primary brand teal */
  --amber:#BA7517;      /* primary accent — the one mark */
  --amber-bright:#D89234;/* accent on dark surfaces */
  --amber-pale:#E8C98F; /* soft accent, highlights */
  --cream:#F1EFE8;      /* page ground */
  --panel:#FAF8F2;      /* raised panels */
  --panel-2:#EAE4D5;    /* recessed panels */
  --white:#FFFFFF;
  --ink:#232B26;        /* body text */
  --muted:#5A665D;      /* secondary text */
  --line:#DED8C8;       /* hairlines, borders */
  --wa:#1FAF5E;         /* WhatsApp green — functional only, never decorative */
}
```

**Usage ratio (roughly):** cream/panel grounds ~70% · teal family ~20% · ink/muted text
~8% · amber ~2%. Amber is a *punctuation mark*, not a fill. If a layout has amber in three
places, two of them are wrong.

**Dark surfaces:** `--teal-950` / `--teal-900` grounds, cream `#F1EFE8` ink, `--amber-bright`
for accents (plain `--amber` goes muddy on dark).

---

## 4. Typography

| Role | Latin | Arabic |
|---|---|---|
| Display / headlines | **Marcellus** (Georgia, serif fallback) | **Markazi Text** ⚠️ |
| Body / UI | **IBM Plex Sans** (400/500/600/700) | **IBM Plex Sans Arabic** ⚠️ |
| Numeric / code / labels | **IBM Plex Mono** (500) | IBM Plex Mono |

```html
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
```

⚠️ **The Arabic pairing has not been signed off by a native speaker.** Standing rule: any
Arabic copy or type decision needs a native Arabic reader's check before it ships.

---

## 5. Logo

**Wordmark:** "AI Profit Lab" set in Marcellus, ink Teal Deep `#0A3D30` on light surfaces /
cream `#EDE8DC` on dark. The tittle of the "i" in **Profit** is recolored amber
(`#BA7517` light · `#D89234` dark) — that dot is the brand's single mark, echoing a
WhatsApp-style online-status dot. Letterforms are outlined to real SVG paths (no font
dependency in the files).

**Icon:** an "AI" monogram with the same amber dot as a corner badge — for favicons and
avatars, legible down to 24px.

### Asset manifest — `brand/logo/` (repo root, outside `public_html/`, does **not** deploy)

| File | Surface |
|---|---|
| `wordmark-primary.svg/.png` | default, light surfaces |
| `wordmark-on-cream.svg/.png` | cream `#F1EFE8` ground |
| `wordmark-on-dark.svg/.png` | dark teal ground |
| `wordmark-reversed.svg/.png` | reversed / knockout |
| `wordmark-mono-ink.svg/.png` | one-colour, print, fax, stamp |
| `icon-transparent.svg/.png` | monogram, transparent |
| `icon-on-cream.svg/.png` | monogram on cream |
| `icon-on-dark.svg/.png` | monogram on dark |

**Web copies:** `public_html/en/logo/wordmark-cream.svg` and `wordmark-dark.svg` — transparent
variants with the background `<rect>` stripped and a CSS pulse on the amber dot (animates even
through a plain `<img>`). ⚠️ The originals in `brand/logo/` bake in a background rect matching
one surface only — dropping `wordmark-on-dark.svg` onto the `#072B22` footer shows a
`#0A1613` patch. Use the `en/logo/` copies on the site.

**Note:** the live site still uses the legacy `public_html/logo.webp` (260×40, black ground,
blue "A" / red "I"). Swapping it to the new wordmark is Nahid's call and has not been made.

### Rules
- Clear space: at least the height of the "A" on all four sides.
- Minimum size: wordmark 120px wide on screen; icon 24px.
- Never: recolour the dot, stretch, rotate, add shadows/glows/gradients, place the wordmark on
  a busy photo, or re-typeset it in another font.

---

## 6. Imagery & layout

- **Editorial, not stock-corporate.** Real warehouses, real paperwork, real hands — not
  glass-tower handshakes or glowing blue brains.
- Generous whitespace on cream; type does the work.
- Hairline rules `--line` instead of heavy boxes.
- The `✼` asterism is used as a section divider throughout the current pages — keep it.
- Founder photography lives in `brand/photos/`.

---

## 7. Bilingual (EN/AR) rules

- EN/AR parity is required on customer-facing pages.
- Mechanism used in the Brand Playbook artifact: a fixed EN/AR toggle flips `dir`/`lang` on the
  root and swaps `.en`/`.ar` sibling spans via CSS.
- **RTL gotcha, learned the hard way:** isolate bare numeric, code and phone strings with
  `dir="ltr"` before trusting them in an RTL flow. Phone numbers reverse their digit groups,
  and hex codes that start with a *letter* (`#BA7517`) throw the `#` to the end while codes
  starting with a digit don't.
- Every AI-drafted Arabic page carries a visible disclosure until a native speaker reviews it.

---

## 8. Standard blocks

**Founder signature:**
> Nahid Abyari · Founder, AI Profit Lab
> hello@aiprofitlab.io · +968 9924 5250 · aiprofitlab.io

**Legal footer:**
> © 2026 AI Profit Lab — a brand of Lotus Gulf International (CR 1570092)
> South Al Khuwair, Bousher, Muscat, Oman · Not VAT registered (TIN 2317725)

**Email addresses:** `hello@aiprofitlab.io` is the customer-support channel.
`nahid.abyari@gmail.com` is the CR e-mail and the Thawani portal account — use it on
gateway/KYC forms only.

**Proposal structure (precedent):** masthead → eyebrow → title → deck → rule → Problem /
Objective → Solution → How It Works → Pricing → Delivery → What's Included **and explicitly
Not Included** → Next Steps → signature → validity footer.

---

## 9. Live references

- Bilingual Brand Playbook (v2, EN/AR): https://claude.ai/code/artifact/8193bf57-701b-4477-be35-80c8c32eb196
- Logomark showcase & rationale: https://claude.ai/code/artifact/671f2e80-37f3-4ccb-8bf7-b43036eb396e

Related docs: `01-persona-and-avatar.md`, `03-money-model.md`.
