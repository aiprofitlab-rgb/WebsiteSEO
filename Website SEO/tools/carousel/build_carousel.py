#!/usr/bin/env python3
"""
AI Profit Lab - Instagram carousel builder.

Turns a small JSON deck into upload-ready 1080x1350 PNG slides, a gallery
preview page, and the caption file that goes with the post.

    python3 tools/carousel/build_carousel.py tools/carousel/decks/template.json
    python3 tools/carousel/build_carousel.py <deck>.json --final   # lint hard
    python3 tools/carousel/build_carousel.py <deck>.json --html-only

Output lands in out/carousel/<slug>/ (gitignored - this repo is public and the
PNGs are large binaries that belong in the content folder, not in git).

WHY A GENERATOR AND NOT A CANVA FILE
------------------------------------
The brand rules in IG/CONTENT-OPS.md are mechanical - one amber element per
slide, every number carries a source, cream/teal/ink/amber in fixed ratio. A
generator can *enforce* them; a drag-and-drop editor can only suggest them.
The lint below is the actual point of this tool. The layouts are just the part
you can see.

RENDERING PATH (the only one available on this Mac - see the brand-kit memo)
---------------------------------------------------------------------------
There is no local SVG rasteriser, no poppler and no wkhtmltopdf. Headless
Chrome screenshots are the path that works. Each slide is written as its own
self-contained HTML file at exactly 1080x1350 and shot at device-scale 2, then
downsampled to 1080x1350 with Lanczos. Supersampling is what keeps hairlines
and Marcellus serifs clean; shooting at 1x visibly frays both.

Fonts are base64-inlined, never linked. A file:// page in Chrome loads
relative <img> fine but is unreliable about relative @font-face, and a font
that silently falls back to Helvetica produces a slide that looks *almost*
right - the worst possible failure for something that gets published.
"""

import argparse
import base64
import functools
import html as _html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FONT_CACHE = HERE / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1080, 1350          # 4:5 - the tallest ratio Instagram renders in feed
SCALE = 2                  # shoot at 2160x2700, downsample to spec

# --------------------------------------------------------------------------
# Palette - verbatim from IG/CONTENT-OPS.md section 2, which is itself taken
# from the brand book. Do not introduce a colour that is not on this list.
# --------------------------------------------------------------------------
PALETTE = """
:root{
  --teal-950:#072B22; --teal-900:#0A3D30; --teal:#0F6E56;
  --amber:#BA7517; --amber-bright:#D89234; --amber-pale:#E8C98F;
  /* #BA7517 on cream measures 3.19:1 - fine for display sizes, under the
     4.5:1 floor for anything at body size. Small amber text uses this. */
  --amber-text:#8F5A11;
  --cream:#F1EFE8; --panel:#FAF8F2; --panel-2:#EAE4D5;
  --ink:#232B26; --muted:#5A665D; --line:#DED8C8;
  --line-dark:rgba(241,239,232,.16);
  /* Nahid's picks. Optima is a macOS system font: Chrome finds it locally, so
     this path gets the real thing. The Google Slides template has to fall back
     to Tenor Sans, which is why the two can look slightly different. */
  --display:'Freehand',cursive;
  --sans:Optima,'Tenor Sans',Georgia,serif;
  --mono:Optima,'Tenor Sans',Georgia,serif;
}
"""

# Character budgets. Not arbitrary: these are the counts at which each layout
# starts wrapping into a fourth line or dropping below its designed size on a
# 1080px canvas. The lint warns rather than truncates - you decide.
BUDGETS = {
    "cover.title": 62, "cover.body": 150,
    "text.title": 84,  "text.body": 380,
    "stat.label": 46,  "stat.caption": 120,
    "steps.title": 70, "steps.item": 96,
    "compare.title": 70, "compare.side": 150,
    "quote.text": 190,
    "cta.title": 58,   "cta.note": 120,
}

PLACEHOLDER_RE = re.compile(r"«[^»]*»")


# ==========================================================================
# Fonts
# ==========================================================================
def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _fetch_plex_sans() -> None:
    """Cache Freehand from Google Fonts.

    Optima is a system font on this Mac and needs no fetching. Freehand is a
    Google Font and is not installed, so it comes down once and stays cached.
    curl, not urllib - Python's TLS stack fails verification on this machine.
    """
    FONT_CACHE.mkdir(exist_ok=True)
    if (FONT_CACHE / "Freehand.ttf").exists():
        return
    url = "https://fonts.googleapis.com/css2?family=Freehand"
    try:
        css = subprocess.run(["curl", "-sS", url], check=True,
                             capture_output=True, text=True, timeout=30).stdout
    except Exception as exc:                                   # noqa: BLE001
        print(f"  ! could not reach Google Fonts ({exc}).", file=sys.stderr)
        print("  ! titles will fall back to a system cursive and will NOT look right.",
              file=sys.stderr)
        return
    m = re.search(r"src:\s*url\((https://[^)]+)\)", css)
    if m:
        dest = FONT_CACHE / "Freehand.ttf"
        subprocess.run(["curl", "-sS", "-o", str(dest), m.group(1)], check=True,
                       timeout=30)
        print(f"  fetched {dest.name}")


@functools.lru_cache(maxsize=1)
def font_face_css() -> str:
    """Base64 blob for every face, built once. Without the cache this runs per
    slide and the build spends most of its time re-encoding the same fonts."""
    _fetch_plex_sans()
    faces = []
    freehand = FONT_CACHE / "Freehand.ttf"
    if freehand.exists():
        faces.append("@font-face{font-family:'Freehand';font-weight:400;"
                     "font-style:normal;src:url(data:font/ttf;base64,"
                     f"{_b64(freehand)}) format('truetype')}}")
    return "\n".join(faces)


# ==========================================================================
# Text handling
# ==========================================================================
def rich(text: str) -> str:
    """Escape, then apply the two bits of markup a deck is allowed to use.

    *word*  -> the slide's single amber accent
    \n      -> line break

    Amber is a signature, not decoration (CONTENT-OPS section 2). The lint
    enforces at most one *...* per slide; the markup exists so you can put it
    on the word that carries the meaning rather than on a whole line.
    """
    out = _html.escape(text or "")
    out = re.sub(r"\*([^*]+)\*", r'<span class="hot">\1</span>', out)
    out = PLACEHOLDER_RE.sub(lambda m: f'<span class="ph">{m.group(0)}</span>', out)
    return out.replace("\n", "<br>")


def plain(text: str) -> str:
    return re.sub(r"\*([^*]+)\*", r"\1", text or "")


# ==========================================================================
# Slide layouts
# ==========================================================================
def _kicker(s):
    k = s.get("kicker")
    return f'<p class="kicker">{rich(k)}</p>' if k else ""


def _note(s):
    n = s.get("note")
    return f'<p class="note"><i>&#8627;</i>{rich(n)}</p>' if n else ""


def layout_cover(s):
    return f"""<div class="l-cover">
  {_kicker(s)}
  <div class="rule-accent"></div>
  <h1>{rich(s.get('title',''))}</h1>
  {f'<p class="lede">{rich(s["body"])}</p>' if s.get("body") else ""}
</div>"""


def layout_text(s):
    return f"""<div class="l-text">
  {_kicker(s)}
  <h2>{rich(s.get('title',''))}</h2>
  {f'<p class="body">{rich(s["body"])}</p>' if s.get("body") else ""}
  {_note(s)}
</div>"""


def layout_stat(s):
    st = s.get("stat", {})
    unit = f'<i class="unit">{rich(st.get("unit",""))}</i>' if st.get("unit") else ""
    return f"""<div class="l-stat">
  <p class="kicker">{rich(st.get('label',''))}</p>
  <p class="figure">{rich(st.get('value',''))}{unit}</p>
  <p class="body">{rich(st.get('caption',''))}</p>
  <p class="source">{rich(st.get('source',''))}</p>
</div>"""


def layout_steps(s):
    items = ""
    for i, item in enumerate(s.get("items", []), 1):
        items += (f'<li><span class="n">{i:02d}</span>'
                  f'<span class="t">{rich(item)}</span></li>')
    return f"""<div class="l-steps">
  {_kicker(s)}
  <h2>{rich(s.get('title',''))}</h2>
  <ol class="steps">{items}</ol>
  {_note(s)}
</div>"""


def layout_compare(s):
    c = s.get("compare", {})
    before, after = c.get("before", {}), c.get("after", {})
    return f"""<div class="l-compare">
  {_kicker(s)}
  <h2>{rich(s.get('title',''))}</h2>
  <div class="panes">
    <div class="pane before">
      <p class="tag">{rich(before.get('label','Before'))}</p>
      <p>{rich(before.get('text',''))}</p>
    </div>
    <div class="arrow">&#8595;</div>
    <div class="pane after">
      <p class="tag">{rich(after.get('label','After'))}</p>
      <p>{rich(after.get('text',''))}</p>
    </div>
  </div>
</div>"""


def layout_quote(s):
    q = s.get("quote", {})
    return f"""<div class="l-quote">
  <p class="mark">&#8220;</p>
  <blockquote>{rich(q.get('text',''))}</blockquote>
  <p class="attrib">{rich(q.get('attrib',''))}</p>
</div>"""


def layout_cta(s):
    c = s.get("cta", {})
    kw = (f'<p class="keyword">{rich(c.get("keyword",""))}</p>'
          if c.get("keyword") else "")
    return f"""<div class="l-cta">
  {_kicker(s)}
  <h2>{rich(s.get('title',''))}</h2>
  {f'<p class="body">{rich(c["line"])}</p>' if c.get("line") else ""}
  {kw}
  {f'<p class="note-cta">{rich(c["note"])}</p>' if c.get("note") else ""}
</div>"""


LAYOUTS = {
    "cover": layout_cover, "text": layout_text, "stat": layout_stat,
    "steps": layout_steps, "compare": layout_compare, "quote": layout_quote,
    "cta": layout_cta,
}
# Cover and CTA are the two dark slides by default: they open and close the
# swipe, and the teal ground is what makes the set read as one object in a grid.
DARK_BY_DEFAULT = {"cover", "cta"}


# ==========================================================================
# Frame
# ==========================================================================
def slide_html(deck, s, index, total):
    """One slide. Minimal chrome, per Nahid: no wordmark, no series/counter
    header, no swipe cue - just the ground, four corner ticks and the type."""
    kind = s.get("type", "text")
    if kind not in LAYOUTS:
        raise SystemExit(f"slide {index}: unknown type {kind!r}. "
                         f"Known types: {', '.join(sorted(LAYOUTS))}")
    dark = s.get("ground", "dark" if kind in DARK_BY_DEFAULT else "light") == "dark"
    return f"""<div class="slide {'dark' if dark else 'light'}" data-i="{index}">
  <div class="grain"></div>
  <svg class="ticks" viewBox="0 0 {W} {H}" aria-hidden="true">
    <path d="M56 96 V56 H96 M{W-96} 56 H{W-56} V96 M{W-56} {H-96} V{H-56} H{W-96} M96 {H-56} H56 V{H-96}"/>
  </svg>
  <main class="stage">{LAYOUTS[kind](s)}</main>
</div>"""


def base_css():
    return PALETTE + f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#3A3A38}}
.slide{{
  position:relative;width:{W}px;height:{H}px;overflow:hidden;
  /* minmax(0,1fr) - a plain 1fr lets long copy blow the row out past the
     canvas instead of wrapping. Same trap as the v4 page grids. */
  display:grid;grid-template-rows:minmax(0,1fr);
  padding:76px 88px 84px;font-family:var(--sans);
  background:var(--cream);color:var(--ink);
}}
.slide.dark{{background:var(--teal-900);color:var(--cream)}}

/* Paper grain at 3.8%: texture on a large flat field, not a visible pattern. */
.grain{{
  position:absolute;inset:0;pointer-events:none;opacity:.038;z-index:2;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E");
}}
/* Crop marks. The blueprint/consulting-document grammar, cheapest possible
   expression of it: four corner ticks, no box. */
.ticks{{position:absolute;inset:0;width:100%;height:100%;z-index:1;fill:none;
  stroke:var(--line);stroke-width:2}}
.slide.dark .ticks{{stroke:var(--line-dark)}}
.slide>.stage{{position:relative;z-index:3;display:flex;align-items:center}}
.stage>div{{width:100%}}

/* ---- shared type ---- */
.kicker{{font-family:var(--mono);font-size:23px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--muted);margin-bottom:30px}}
.slide.dark .kicker{{color:var(--amber-pale)}}
h1,h2{{font-family:var(--display);font-weight:400;line-height:1.06;
  letter-spacing:-.01em;text-wrap:balance}}
h1{{font-size:96px}}
h2{{font-size:66px}}
.body{{font-size:35px;line-height:1.55;margin-top:34px;max-width:22em}}
.lede{{font-size:33px;line-height:1.5;margin-top:36px;opacity:.85;max-width:22em}}
.hot{{color:var(--amber)}}
.slide.dark .hot{{color:var(--amber-bright)}}
.ph{{color:var(--muted);border-bottom:2px dashed var(--line);padding-bottom:2px}}
.slide.dark .ph{{color:var(--amber-pale);border-color:var(--line-dark)}}
/* A dark pane inside a light slide: .slide.dark does not match, so the
   placeholder tint has to be restated or it goes muted-on-teal. */
.after .ph{{color:var(--amber-pale);border-color:var(--line-dark)}}
/* The figure IS the slide's amber. An unfilled one stays amber, just dimmed -
   otherwise the template previews with a grey number and reads as broken. */
.l-stat .figure .ph{{color:inherit;opacity:.5;border-color:currentColor}}
.note{{display:flex;gap:14px;font-family:var(--mono);font-size:23px;
  line-height:1.5;color:var(--muted);margin-top:44px;max-width:26em}}
.note i{{font-style:normal;color:var(--amber-text)}}

/* ---- cover ---- */
.rule-accent{{width:104px;height:5px;background:var(--amber-bright);margin-bottom:34px}}
.l-cover h1{{max-width:11em}}

/* ---- stat ---- */
.l-stat .figure{{font-family:var(--mono);font-weight:600;font-size:230px;
  line-height:.9;color:var(--amber);letter-spacing:-.03em}}
.l-stat .unit{{font-style:normal;font-size:96px;padding-left:12px}}
.l-stat .body{{margin-top:38px;font-size:38px;max-width:20em}}
.l-stat .source{{font-family:var(--mono);font-size:21px;line-height:1.45;
  color:var(--muted);margin-top:40px;padding-top:22px;
  border-top:1px solid var(--line);max-width:28em}}

/* ---- steps ---- */
.steps{{list-style:none;margin-top:44px}}
.steps li{{display:flex;gap:30px;align-items:baseline;padding:26px 0;
  border-top:1px solid var(--line)}}
.steps li:last-child{{border-bottom:1px solid var(--line)}}
.slide.dark .steps li{{border-color:var(--line-dark)}}
.steps .n{{font-family:var(--mono);font-size:26px;color:var(--teal);
  letter-spacing:.08em;flex:0 0 auto}}
.slide.dark .steps .n{{color:var(--amber-pale)}}
.steps .t{{font-size:32px;line-height:1.4}}

/* ---- compare ---- */
.panes{{margin-top:40px}}
.pane{{padding:34px 38px}}
.pane p:not(.tag){{font-size:31px;line-height:1.45}}
.pane .tag{{font-family:var(--mono);font-size:21px;letter-spacing:.2em;
  text-transform:uppercase;margin-bottom:16px}}
.before{{background:var(--panel-2);color:var(--ink)}}
.before .tag{{color:var(--muted)}}
.after{{background:var(--teal-900);color:var(--cream)}}
.after .tag{{color:var(--amber-pale)}}
.arrow{{text-align:center;font-size:38px;color:var(--amber);padding:14px 0}}

/* ---- quote ---- */
.l-quote .mark{{font-family:var(--display);font-size:150px;line-height:.5;
  color:var(--amber-pale);height:64px}}
.l-quote blockquote{{font-family:var(--display);font-size:60px;line-height:1.22;
  margin-top:20px;max-width:15em}}
.l-quote .attrib{{font-family:var(--mono);font-size:23px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);margin-top:46px}}
.slide.dark .l-quote .attrib{{color:var(--amber-pale)}}

/* ---- cta ---- */
.l-cta .keyword{{display:inline-block;margin-top:44px;padding:20px 34px;
  border:2px solid var(--amber-bright);color:var(--amber-bright);
  font-family:var(--mono);font-size:34px;letter-spacing:.16em;
  text-transform:uppercase}}
.l-cta .note-cta{{font-family:var(--mono);font-size:23px;line-height:1.5;
  color:var(--amber-pale);margin-top:38px;max-width:26em}}

/* ---- RTL ---- */
[dir=rtl] .slide{{text-align:right}}
[dir=rtl] .steps li{{flex-direction:row-reverse}}
[dir=rtl] .note{{flex-direction:row-reverse}}
"""


def page(deck, inner, extra_css=""):
    d = deck.get("dir", "ltr")
    return f"""<!doctype html>
<html lang="{deck.get('lang','en')}" dir="{d}"><head><meta charset="utf-8">
<title>{_html.escape(deck.get('slug','carousel'))}</title>
<style>{font_face_css()}
{base_css()}
{extra_css}</style></head><body>{inner}</body></html>"""


# ==========================================================================
# Lint - the reason this tool exists
# ==========================================================================
def lint(deck, final):
    problems, notes = [], []
    slides = deck["slides"]
    if not 3 <= len(slides) <= 10:
        notes.append(f"{len(slides)} slides. Instagram allows 10; 6-8 is the "
                     "range that holds swipe-through.")
    if slides and slides[0].get("type") != "cover":
        notes.append("slide 1 is not a cover. The first frame is the whole post's hook.")
    if slides and slides[-1].get("type") != "cta":
        notes.append("last slide is not a cta. A carousel without an ask is a brochure.")

    for i, s in enumerate(slides, 1):
        kind = s.get("type", "text")
        blob = json.dumps(s, ensure_ascii=False)

        # One amber element per slide. A stat slide spends its amber on the
        # figure, so it may not also carry an accent word.
        accents = len(re.findall(r"\*[^*]+\*", blob))
        if accents > 1:
            problems.append(f"slide {i}: {accents} amber accents (*...*). "
                            "One per slide - if two numbers are amber, one is wrong.")
        if kind == "stat" and accents:
            problems.append(f"slide {i}: a stat slide already spends its amber on "
                            "the figure. Remove the *...* accent.")

        # Every number traces to something observed (CONTENT-OPS section 4).
        if kind == "stat":
            st = s.get("stat", {})
            if not st.get("source", "").strip():
                problems.append(f"slide {i}: stat has no source. Every number on this "
                                "account traces to your own audit, client work or logs.")
            if not st.get("value", "").strip():
                problems.append(f"slide {i}: stat has no value.")

        # Placeholders
        if final:
            for m in PLACEHOLDER_RE.findall(blob):
                problems.append(f"slide {i}: unfilled placeholder {m}")

        # Overset copy
        for field, budget in BUDGETS.items():
            k, prop = field.split(".")
            if k != kind:
                continue
            if prop == "item":
                for j, item in enumerate(s.get("items", []), 1):
                    if len(plain(item)) > budget:
                        notes.append(f"slide {i} item {j}: {len(plain(item))} chars "
                                     f"(budget {budget}) - it will crowd.")
            elif prop == "side":
                for side in ("before", "after"):
                    t = s.get("compare", {}).get(side, {}).get("text", "")
                    if len(plain(t)) > budget:
                        notes.append(f"slide {i} {side}: {len(plain(t))} chars "
                                     f"(budget {budget}).")
            else:
                val = (s.get(prop) or s.get(kind, {}).get(prop)
                       or s.get("quote", {}).get(prop) or "")
                if isinstance(val, str) and len(plain(val)) > budget:
                    notes.append(f"slide {i} {prop}: {len(plain(val))} chars "
                                 f"(budget {budget}) - it will shrink or wrap long.")

    cap = deck.get("caption", {})
    if final and PLACEHOLDER_RE.search(json.dumps(cap, ensure_ascii=False)):
        problems.append("caption still has unfilled placeholders.")
    if deck.get("dir") == "rtl" and not deck.get("arabic_checked"):
        problems.append('Arabic deck without "arabic_checked": true. A native '
                        "speaker checks every Arabic caption before it goes out - "
                        "no exceptions, no machine translation (CONTENT-OPS s.4).")
    return problems, notes


# ==========================================================================
# Render
# ==========================================================================
def shoot(html_path: Path, png_path: Path):
    subprocess.run([
        CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
        f"--screenshot={png_path}", f"--window-size={W},{H}",
        f"--force-device-scale-factor={SCALE}",
        "--virtual-time-budget=1200", "--no-sandbox",
        html_path.as_uri(),
    ], check=True, capture_output=True)
    with Image.open(png_path) as im:
        if im.size != (W, H):
            im.convert("RGB").resize((W, H), Image.LANCZOS).save(png_path, optimize=True)


def caption_text(deck):
    c = deck.get("caption", {})
    parts = [plain(c.get("hook", "")), "", plain(c.get("body", "")), "",
             plain(c.get("cta", ""))]
    tags = c.get("hashtags", [])
    if tags:
        parts += ["", " ".join(t if t.startswith("#") else "#" + t for t in tags)]
    return "\n".join(parts).strip() + "\n"


def build(deck_path: Path, final: bool, html_only: bool, only: int = 0):
    deck = json.loads(deck_path.read_text(encoding="utf-8"))
    slug = deck.get("slug") or deck_path.stem
    out = REPO / "out" / "carousel" / slug
    out.mkdir(parents=True, exist_ok=True)
    slides = deck["slides"]
    total = len(slides)

    problems, notes = lint(deck, final)
    for n in notes:
        print(f"  note: {n}")
    for p in problems:
        print(f"  PROBLEM: {p}", file=sys.stderr)
    if problems and final:
        raise SystemExit("\n--final refuses to build with problems outstanding.")

    print(f"  fonts + logo inlining...")
    gallery = "".join(slide_html(deck, s, i, total) for i, s in enumerate(slides, 1))
    (out / "carousel.html").write_text(
        page(deck, f'<div class="gallery">{gallery}</div>',
             extra_css=".gallery{display:flex;flex-wrap:wrap;gap:28px;padding:28px;"
                       "zoom:.42}.slide{outline:1px solid rgba(0,0,0,.25)}"),
        encoding="utf-8")
    (out / "caption.txt").write_text(caption_text(deck), encoding="utf-8")

    if not html_only:
        with tempfile.TemporaryDirectory() as tmp:
            for i, s in enumerate(slides, 1):
                if only and i != only:
                    continue
                one = Path(tmp) / f"slide-{i:02d}.html"
                one.write_text(page(deck, slide_html(deck, s, i, total)), encoding="utf-8")
                png = out / f"slide-{i:02d}.png"
                shoot(one, png)
                print(f"  slide-{i:02d}.png  [{s.get('type','text')}]")

    print(f"\n  -> {out}")
    print("     carousel.html   gallery preview, all slides at 42%")
    print("     slide-NN.png    1080x1350, upload in this order")
    print("     caption.txt     paste as the post caption")
    if problems:
        print(f"\n  {len(problems)} problem(s) above still need fixing before posting.")


def main():
    ap = argparse.ArgumentParser(description="Build an AI Profit Lab Instagram carousel.")
    ap.add_argument("deck", type=Path, help="path to a deck JSON")
    ap.add_argument("--final", action="store_true",
                    help="refuse to build while placeholders or brand-rule problems remain")
    ap.add_argument("--html-only", action="store_true",
                    help="skip the Chrome screenshots, write the preview page only")
    ap.add_argument("--slide", type=int, default=0, metavar="N",
                    help="re-shoot slide N only, keeping the rest as they are")
    a = ap.parse_args()
    if not a.deck.exists():
        raise SystemExit(f"no such deck: {a.deck}")
    print(f"building {a.deck.name}")
    build(a.deck, a.final, a.html_only, a.slide)


if __name__ == "__main__":
    main()
