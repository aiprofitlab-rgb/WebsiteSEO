#!/usr/bin/env python3
"""
Build the v4 page set into public_html/en/.

    python3 tools/build_v4.py            # build every page
    python3 tools/build_v4.py index-v4   # build one

Existing pages are never touched: this writes only *-v4.html files, which are
new names. Each output is self-contained (inlined CSS + JS) - see the note at
the top of tools/v4/kit.py for why that beats a shared stylesheet here.
"""
import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "public_html" / "en"
sys.path.insert(0, str(HERE / "v4"))
sys.path.insert(0, str(HERE))

import aiden_version  # noqa: E402
import kit  # noqa: E402

MODULES = ["page_home", "page_services", "page_process", "page_about", "page_contact",
           "page_blog", "page_article", "page_simulator", "page_demo"]


def render(mod):
    m = importlib.import_module(mod)
    meta = m.META
    path = f"/en/{meta['slug']}/"

    css = kit.TOKENS + kit.SKIP_CSS + kit.BASE_CSS + getattr(m, "CSS", "")
    js = kit.MOTION_JS
    head_extra = ""

    if meta.get("hero"):
        import hero as hero_mod
        import _ported_js
        css += hero_mod.HERO_CSS
        js += _ported_js.CINE_JS
        # Frame 0 is the LCP image on the homepage. ?v= must match ASSET_V in
        # the scrub script, which is why both are bumped by the frame builder.
        head_extra = ('<link rel="preload" as="image" '
                      'href="/assets/cinematic/poster.webp?v=20260817" fetchpriority="high">')
    if meta.get("calc"):
        import _ported_js
        js += _ported_js.CALC_JS

    schema = ""
    if meta.get("schema"):
        schema = '<script type="application/ld+json">\n' + meta["schema"] + "\n</script>"

    html = (
        kit.HEAD
        .replace("{{TITLE}}", meta["title"])
        .replace("{{DESC}}", meta["desc"])
        .replace("{{PATH}}", path)
        .replace("{{HEADEXTRA}}", head_extra)
        .replace("{{SCHEMA}}", schema)
        .replace("{{CSS}}", css)
        + kit.header(meta["nav"])
        + m.body()
        + kit.pager(*meta["next"])
        + kit.FOOTER
        # Aiden runs on every page except the articles; an article is a reading
        # surface and the launcher competes with it. Default is on, so a new
        # page gets the widget unless it opts out.
        + kit.TAIL.replace("{{JS}}", js + getattr(m, "JS", ""))
                  .replace("{{AIDEN}}", kit.AIDEN_TAG.replace("{{VER}}", aiden_version.token())
                           if meta.get("aiden", True) else "")
    )

    dest = OUT / (meta["slug"] + ".html")
    dest.write_text(html, encoding="utf-8")
    return dest, len(html)


if __name__ == "__main__":
    want = sys.argv[1:]
    built = []
    for mod in MODULES:
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            print(f"  .. {mod} not written yet, skipping")
            continue
        if want and m.META["slug"] not in want:
            continue
        dest, n = render(mod)
        built.append(dest)
        print(f"  ok {dest.relative_to(ROOT)}  {n/1024:.0f} KB")
    if not built:
        print("nothing built")
