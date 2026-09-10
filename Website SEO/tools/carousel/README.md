# Instagram carousel template

Two ways to make the same carousel.

**Edit in Google Slides** — `build_gslides.py` writes a .pptx that Drive
converts into a native Google Slides deck. This is the one to use day to day.

```bash
python3 tools/carousel/build_gslides.py     # -> out/carousel/AI-Profit-Lab-Carousel-Template.pptx
python3 tools/carousel/preview_pptx.py out/carousel/AI-Profit-Lab-Carousel-Template.pptx
```

To get it into Drive: upload the .pptx to Google Drive, then right-click ▸
Open with ▸ Google Slides. It converts with fonts, colours and speaker notes
intact. Then File ▸ Make a copy for every new post. (It cannot be uploaded
from here — the connector needs the file inline as base64 and a real .pptx is
too large to pass through.)

`preview_pptx.py` exists because nothing on this Mac renders a .pptx:
LibreOffice is not installed, Keynote will not open one over AppleScript, and
QuickLook has no generator for it. It reads the saved file back and redraws it
in Chrome, so a deck never ships unlooked-at.

**Edit in JSON** — `build_carousel.py` turns a deck file into upload-ready
1080×1350 PNGs, a preview page, and the caption. Higher fidelity output and it
carries the lint, but you edit text in a JSON file.

```bash
# copy the template, rewrite the text, build
cp tools/carousel/decks/template.json tools/carousel/decks/quote-followup.json
python3 tools/carousel/build_carousel.py tools/carousel/decks/quote-followup.json

# before posting — refuses to build while any «placeholder» or brand-rule
# problem is left
python3 tools/carousel/build_carousel.py tools/carousel/decks/quote-followup.json --final

# fast iteration
python3 tools/carousel/build_carousel.py <deck>.json --html-only   # preview page, no PNGs (~1s)
python3 tools/carousel/build_carousel.py <deck>.json --slide 3     # re-shoot one slide
```

Output: `out/carousel/<slug>/` — `slide-01.png…` (upload in order),
`carousel.html` (all slides at 42%, open it in a browser to review the set the
way the grid will show it), `caption.txt`.

`out/carousel/` is gitignored. This repo is public and the PNGs are large
binaries — move the finished set to the IG content folder.

## Slide types

| type | carries | notes |
|---|---|---|
| `cover` | `kicker`, `title`, `body` | dark ground. Amber is the short rule above the title |
| `text` | `kicker`, `title`, `body`, `note` | the workhorse. `note` is the margin annotation |
| `stat` | `stat{label,value,unit,caption,source}` | **`source` is mandatory** — see below |
| `steps` | `kicker`, `title`, `items[]`, `note` | 3–5 items. Numerals are teal, not amber |
| `compare` | `compare{before{label,text},after{label,text}}` | before = panel, after = teal |
| `quote` | `quote{text,attrib}` | pull quote. Attribute it, always |
| `cta` | `kicker`, `title`, `cta{line,keyword,note}` | dark ground. The keyword box is the amber |

Any slide takes `"ground": "dark"` or `"light"` to override its default.
`cover` and `cta` are dark by default — they open and close the swipe, and the
teal ground is what makes the set read as one object in the profile grid.

## Markup inside deck text

- `*word*` → the slide's amber accent. **One per slide.**
- `\n` → line break.
- `«...»` → an unfilled placeholder. Renders visibly dashed so you can't miss
  one, and `--final` refuses to build while any remain.

## What the lint enforces, and why

These are the rules from `IG/CONTENT-OPS.md` §2 and §4 — the file is canonical,
this tool just makes the rules mechanical.

- **One amber element per slide.** Amber is a signature, not decoration. If two
  numbers on a slide are amber, one of them is wrong. A `stat` slide already
  spends its amber on the figure, so it may not also carry a `*...*` accent.
- **Every number carries a source.** A `stat` without a `source` line does not
  build. Every diagnostic claim on this account traces to something you
  observed — your audit, client work, logs. Never an imported statistic.
- **Arabic needs a human.** A deck with `"dir": "rtl"` does not build until it
  also carries `"arabic_checked": true`, which you set only after a native
  speaker has read it. No machine translation, no exceptions.
- **Copy budgets** (warnings, not blocks): the character counts at which each
  layout starts wrapping badly or dropping a size. It tells you the count and
  the budget; the call is yours.
- **Shape**: 6–8 slides, cover first, cta last.

## Palette and type

Palette comes straight from the brand book via `IG/CONTENT-OPS.md`: teal
`#0A3D30`, brand teal `#0F6E56`, amber `#BA7517`, cream `#F1EFE8`, ink
`#232B26`. Do not add a colour that is not on that list.

Type is Nahid's pick, and it is **not** the brand book's Marcellus / IBM Plex
pairing: titles are **Freehand**, body is **Optima**. There is one unavoidable
split between the two builders:

| | titles | body |
|---|---|---|
| PNG builder (local Chrome) | Freehand | **Optima** — a macOS system font, so it renders for real |
| Slides template | Freehand | **Tenor Sans** — the stand-in |

Google Slides can only use fonts from its own picker, which is Google Fonts
plus a few legacy web faces. Optima is in neither, so a deck that names it
renders as Arial in the browser for everyone. Tenor Sans is the closest
humanist face Slides can actually serve. To make both builders match, set
`--sans` in `build_carousel.py` to Tenor Sans.

There is no wordmark, no series/counter header and no swipe cue on any slide —
minimal chrome, by request. What carries the brand without words is the ground,
the four corner ticks, and the single amber accent.

## Rendering notes

Freehand is a Google Font and is not installed system-wide, so the first run
curls it into `tools/carousel/fonts/` and caches it. If that fetch fails the
build says so loudly rather than silently falling back to a system cursive.
Optima needs no fetching — it ships with macOS at
`/System/Library/Fonts/Optima.ttc`.

Freehand and Tenor Sans are also copied into `~/Library/Fonts/` so Keynote,
Preview and Pages show the deck correctly. Delete those two files to undo it.

`build_gslides.py` measures every string against the real TTFs (PIL) and
shrinks the size until it fits its box. Freehand is about 26% narrower than
Tenor Sans at the same point size, so no single hardcoded scale works for
both.

Slides are shot with headless Chrome at device-scale 2 and downsampled to
1080×1350 with Lanczos — supersampling is what keeps the hairlines and the
Marcellus serifs clean. There is no other rasteriser on this machine.

Fonts and the logo are base64-inlined into each temporary slide file rather
than linked: a `file://` page in Chrome is unreliable about relative
`@font-face`, and a font that quietly falls back produces a slide that looks
*almost* right, which is the worst way for something published to fail.
