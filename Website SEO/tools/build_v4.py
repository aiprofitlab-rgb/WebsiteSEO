#!/usr/bin/env python3
"""
Build the v4 page set, in both languages.

    python3 tools/build_v4.py                # every page, English and Arabic
    python3 tools/build_v4.py services       # that page in both languages
    python3 tools/build_v4.py --lang ar      # the Arabic set only

Each output is self-contained (inlined CSS + JS) - see the note at the top of
tools/v4/kit.py for why that beats a shared stylesheet here.

The Arabic modules live in tools/v4/ar/ and import their CSS from the English
module of the same page, so the two languages cannot drift apart visually: an
Arabic page is the same components, the same copy structure and the same
figures, with translated strings and the RTL layer from tools/v4/rtl.py
appended last. Where a page carries an SVG diagram whose reading direction
matters, the Arabic module authors a mirrored one - that is the only markup
either side duplicates on purpose.
"""
import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "public_html" / "en"
sys.path.insert(0, str(HERE / "v4"))
sys.path.insert(0, str(HERE / "v4" / "ar"))
sys.path.insert(0, str(HERE))

import aiden_version  # noqa: E402
import kit  # noqa: E402
import rtl  # noqa: E402

# page_blog and page_article are deliberately absent. Both were pattern
# references built before the corpus migration: the real article hub is
# regenerated from all 150 published pieces by tools/reskin_blog_hubs.py, and
# the reference article is a rewrite of a piece that tools/reskin_articles.py
# now re-skins in place. Publishing either would duplicate a live URL.
MODULES = ["page_home", "page_services", "page_process", "page_about", "page_contact",
           "page_simulator", "page_demo", "page_checkout", "page_order"]

# Same nine pages, the Arabic side. Added 2026-08-21, replacing the old dark
# skin on the five core Arabic URLs and introducing four pages Arabic never
# had. Names are suffixed rather than shadowed because both sets sit on
# sys.path and an Arabic module imports its English twin for the CSS.
MODULES_AR = [m + "_ar" for m in MODULES]


def render(mod, lang="en"):
    m = importlib.import_module(mod)
    meta = m.META
    rel, path, other = kit.pages(lang)[meta["slug"]]

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
        js += _ported_js.calc_js(lang)

    # Every page carries the shared Organization node, so twenty-two URLs
    # consolidate into one entity instead of twenty-two anonymous ones; the
    # two homepages also carry the WebSite node. The page's own node, if it
    # has one, joins them in the same @graph.
    nodes = [kit.ORG_NODE]
    if path in ("/", "/ar/"):
        nodes.append(kit.WEBSITE_NODE)
    if meta.get("schema"):
        nodes.append(meta["schema"])
    schema = '<script type="application/ld+json">\n' + kit.graph(nodes) + "\n</script>"

    # The RTL layer is appended AFTER the page's own CSS so it wins on a
    # specificity tie without any !important - see tools/v4/rtl.py.
    if lang == "ar":
        css += rtl.CORE_RTL_CSS

    html = (
        kit.head_html(lang)
        .replace("{{TITLE}}", meta["title"])
        .replace("{{DESC}}", meta["desc"])
        .replace("{{ROBOTS}}", kit.ROBOTS_NONE if meta.get("noindex")
                 else kit.ROBOTS_INDEX)
        .replace("{{PATH}}", path)
        .replace("{{ALTERNATES}}", kit.alternates(path, other, lang))
        .replace("{{HEADEXTRA}}", head_extra)
        .replace("{{SCHEMA}}", schema)
        .replace("{{CSS}}", css)
        # `other` is the third field of the PAGES row - the twin URL that also
        # feeds {{ALTERNATES}} above, so the visible toggle and the hreflang
        # alternate are the same string by construction.
        + kit.header(meta["nav"], lang, other)
        + m.body()
        + kit.pager(*meta["next"], lang=lang)
        + kit.footer(lang)
        # Aiden runs on every page except the articles; an article is a reading
        # surface and the launcher competes with it. Default is on, so a new
        # page gets the widget unless it opts out.
        + kit.TAIL.replace("{{JS}}", js + getattr(m, "JS", ""))
                  .replace("{{AIDEN}}", kit.AIDEN_TAG.replace("{{VER}}", aiden_version.token())
                           if meta.get("aiden", True) else "")
    )

    dest = ROOT / "public_html" / rel
    dest.write_text(html, encoding="utf-8")
    return dest, len(html)


if __name__ == "__main__":
    argv = sys.argv[1:]
    langs = ["en", "ar"]
    if "--lang" in argv:
        i = argv.index("--lang")
        langs = [argv[i + 1]]
        del argv[i:i + 2]
    want = argv
    built = []

    for lang in langs:
        mods = MODULES_AR if lang == "ar" else MODULES
        print(f"[{lang}]")
        for mod in mods:
            try:
                m = importlib.import_module(mod)
            except ModuleNotFoundError:
                print(f"  .. {mod} not written yet, skipping")
                continue
            if want and m.META["slug"] not in want:
                continue
            dest, n = render(mod, lang)
            built.append(dest)
            print(f"  ok {dest.relative_to(ROOT)}  {n/1024:.0f} KB")
    if not built:
        print("nothing built")

    # ----------------------------------------------------------------------
    # Anti-drift check: the price table on the services page is hand-written
    # markup, while the checkout computes from tools/v4/pay.py. Two copies of
    # every figure therefore exist, so the build asserts they still agree. This
    # runs against the file on disk rather than the freshly rendered string, so
    # it also catches "I edited pay.py and rebuilt only the checkout".
    # ----------------------------------------------------------------------
    import pay  # noqa: E402
    failed = False
    for lang in langs:
        svc = ROOT / "public_html" / kit.pages(lang)["services"][0]
        if not svc.exists():
            print(f"  !! {lang} services page not built; prices not checked")
            continue
        problems = pay.check_services(svc.read_text(encoding="utf-8"), lang)
        if problems:
            failed = True
            print(f"\n  PRICE MISMATCH - pay.py and {svc.relative_to(ROOT)} disagree:")
            for pr in problems:
                print("    x " + pr)
        else:
            print(f"  ok prices in pay.py match {svc.relative_to(ROOT)}")
    if failed:
        sys.exit(1)

    # ----------------------------------------------------------------------
    # Ship the same table to the checkout server.
    #
    # backend/checkout-api/ re-prices every order from its own copy - it must
    # never charge the number the browser sent - so it needs the price table
    # too. Exporting it here means a price cannot be changed in pay.py and
    # rebuilt into the pages while the service keeps quoting the old one; the
    # only remaining step is redeploying the service, which the exporter says
    # out loud when the file actually changed.
    # ----------------------------------------------------------------------
    import export_catalog  # noqa: E402
    dest, changed = export_catalog.write()
    print(f"  {'NEW' if changed else 'ok '} {dest.relative_to(ROOT)}"
          + ("  <- prices moved: redeploy checkout-api" if changed else ""))
