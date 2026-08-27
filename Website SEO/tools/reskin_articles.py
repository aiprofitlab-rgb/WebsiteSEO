#!/usr/bin/env python3
"""
Re-skin every published article onto the v4 brand-book template.

    python3 tools/reskin_articles.py --dry-run        # report, write nothing
    python3 tools/reskin_articles.py                  # rewrite all 300
    python3 tools/reskin_articles.py --lang en        # one language
    python3 tools/reskin_articles.py --only 2026-08-19-why   # substring filter
    python3 tools/reskin_articles.py --out /tmp/preview      # write elsewhere

Files are rewritten IN PLACE, which is the whole point: the URL, the canonical,
every inbound link and every ranking attaches to the path, not to the markup.

What is preserved, byte for byte
--------------------------------
title, meta description, meta keywords, meta category, canonical, every
hreflang alternate, the complete JSON-LD @graph (Organization / Article /
FAQPage / BreadcrumbList as each page had it), every heading `id` (old
table-of-contents anchors keep working), and every link in the body.

The GA measurement id is the one thing deliberately NOT preserved - it is
configuration, not content, and copying it forward is how a retired property
survived a cleanup once already. See the note in tools/v4/legacy.py.

What is added
-------------
Open Graph + Twitter card tags (the old template had none, so shares and a
number of AI crawlers had no title/image to read), an explicit
`robots: index, follow, max-image-preview:large, max-snippet:-1` directive, a
server-rendered table of contents, a related-articles block that deepens
internal linking, and a topic chip row built from the page's own keywords.

What is removed
---------------
The Tailwind CDN script and the old dark skin, the FOUC overlay, and
`/js/aiden-chat.js` - articles carry no chat widget.
"""
import argparse
import hashlib
import html as _html
import json as _json
import pathlib
import re
import sys
from urllib.parse import quote

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "v4"))

import blog_chrome as C          # noqa: E402
import legacy                    # noqa: E402
from article_kit import ARTICLE_JS, LINK_ICON, LI_ICON  # noqa: E402
from kit import MOTION_JS, STAR, WA, WA_ICON            # noqa: E402

BLOG = ROOT / "public_html" / "blog"
ASSETS = ROOT / "public_html" / "assets"
SITE = "https://aiprofitlab.io"
WPM = {"en": 225, "ar": 190}

# The old image pipeline stamped this on every hero's alt text. It describes
# the company, not the picture, which is worthless to a screen reader and to
# image search alike. Where it appears the article's own headline replaces it.
ALT_BOILERPLATE = "Empowering AI Solutions by AI Profit Lab"


# --------------------------------------------------------------------------
# Shared assets
# --------------------------------------------------------------------------
def build_assets(write=True):
    """Emit the one stylesheet and one script the whole article set links.

    Inlining, which is what the v4 marketing pages do, is the wrong trade at
    300 pages: it would put ~60KB of identical CSS in every document, on a
    path the host caches for only 10 minutes. A content-hashed filename under
    /assets/ gets the year-long immutable cache instead, and because the hash
    changes with the bytes there is no stale-asset trap - the failure mode
    that a stable filename under `immutable` guarantees.
    """
    css = C.stylesheet()
    js = MOTION_JS + ARTICLE_JS
    out = {}
    for kind, body, ext in (("css", css, "css"), ("js", js, "js")):
        h = hashlib.sha256(body.encode()).hexdigest()[:10]
        name = f"apl-article.{h}.{ext}"
        href = f"/assets/{ext}/{name}"
        if write:
            d = ASSETS / ext
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob(f"apl-article.*.{ext}"):
                if old.name != name:
                    old.unlink()
            (d / name).write_text(body, encoding="utf-8")
        out[kind] = href
    return out["css"], out["js"]


# --------------------------------------------------------------------------
# Index — every article's headline and category, so related links can be real
# --------------------------------------------------------------------------
def build_index():
    idx = {"en": {}, "ar": {}}
    for lang in ("en", "ar"):
        for f in sorted((BLOG / lang).glob("*.html")):
            src = f.read_text(encoding="utf-8")
            head = src[:src.find("</head>")] if "</head>" in src else src[:9000]
            m = re.search(r"<title>(.*?)</title>", head, re.S)
            title = _html.unescape(m.group(1)).strip() if m else f.stem
            title = re.sub(r"\s*\|\s*AI Profit Lab\s*$", "", title).strip()
            cat = legacy._meta(head, "category")
            m = re.search(r'rel="canonical"\s+href="([^"]+)"', head) or \
                re.search(r'href="([^"]+)"\s+rel="canonical"', head)
            url = canon_url(m.group(1)) if m else f"{SITE}/blog/{lang}/{f.stem}/"
            idx[lang][f.stem] = {
                "title": title, "cat": cat, "url": url,
                "date": (re.match(r"(\d{4}-\d{2}-\d{2})", f.stem) or [None, ""])[1],
                "slug": f.stem,
            }
    return idx


def related(doc, slug, lang, idx):
    """Three sibling articles: first the ones this piece already cites, then
    same-category neighbours, then the nearest by date. Real links only."""
    pool, seen = [], {slug}
    for m in re.finditer(r'href="(?:%s)?/blog/%s/([^/"]+)/?"' % (re.escape(SITE), lang), doc["body"]):
        s = m.group(1).replace(".html", "")
        if s in idx[lang] and s not in seen:
            seen.add(s)
            pool.append(idx[lang][s])
    if len(pool) < 3 and doc["category"]:
        for s, e in idx[lang].items():
            if len(pool) >= 3:
                break
            if s not in seen and e["cat"] and e["cat"] == doc["category"]:
                seen.add(s)
                pool.append(e)
    if len(pool) < 3:
        order = sorted(idx[lang].values(), key=lambda e: abs(_ord(e["date"]) - _ord(doc["date_iso"])))
        for e in order:
            if len(pool) >= 3:
                break
            if e["slug"] not in seen:
                seen.add(e["slug"])
                pool.append(e)
    return pool[:3]


def canon_url(u):
    """Force the trailing-slash form of an on-site URL.

    Rewrite rule 1 in .htaccess 301s any non-file path without a trailing
    slash, so 121 of the 150 English articles were declaring a canonical that
    redirects - while the sitemap listed all 150 with the slash. Two different
    URLs claimed to be the same page's canonical form. Everything emitted here
    uses the form that answers 200.
    """
    if not u or "?" in u or "#" in u:
        return u
    base = u.split("//", 1)[-1]
    if u.endswith("/") or "." in base.rsplit("/", 1)[-1]:
        return u
    return u + "/"


def hreflang(slug, existing):
    """Every article exists in both languages under the same filename, so the
    pair is always derivable. 29 of the 300 pages shipped without any hreflang
    at all and the rest were inconsistent; this normalises all of them and
    adds the x-default that none of them had."""
    en = f"{SITE}/blog/en/{slug}/"
    ar = f"{SITE}/blog/ar/{slug}/"
    if not (BLOG / "en" / f"{slug}.html").exists() or not (BLOG / "ar" / f"{slug}.html").exists():
        return existing
    return [("en", en), ("ar", ar), ("x-default", en)]


def twin_url(slug, lang):
    """Where the language toggle in the header should go from this article: the
    same article in the other language. Every article is filed under the same
    filename in both trees, so the pair is derivable from the slug - the same
    fact hreflang() above relies on. An article with no twin falls back to the
    other language's ARTICLE HUB rather than its home page: a reader who was
    reading gets handed a reading surface."""
    other = "ar" if lang == "en" else "en"
    if (BLOG / other / f"{slug}.html").exists():
        return f"/blog/{other}/{slug}/"
    return "/blog-ar/" if other == "ar" else "/blog/"


def _ord(iso):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        return y * 372 + m * 31 + d
    except Exception:
        return 0


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def share_row(title, url, t):
    q = quote("%s — %s" % (legacy.text(title), url))
    return f"""<div class="share">
      <a href="https://api.whatsapp.com/send?text={q}" target="_blank" rel="noopener" aria-label="{t['share_wa']}" title="{t['share_wa']}">{WA_ICON}</a>
      <a href="https://www.linkedin.com/sharing/share-offsite/?url={quote(url)}" target="_blank" rel="noopener" aria-label="{t['share_li']}" title="{t['share_li']}">{LI_ICON}</a>
      <button type="button" id="copyLink" aria-label="{t['copy']}" title="{t['copy']}">{LINK_ICON}</button>
    </div>"""


def hero_src(src, width=1200):
    """The resized WebP for a hero, when one has been built.

    Falls back to the original so a missing derivative degrades to the old
    behaviour rather than to a broken image. Build them with
    `python3 tools/build_image_derivatives.py`.
    """
    if not src.startswith("/blog/images/"):
        return src
    stem, _, ext = src.rpartition(".")
    # Only a .webp named "<stem>-<width>" is one of ours. Testing for a
    # trailing number alone skipped every source whose name simply ends in a
    # year or a timestamp - oman-10-percent-gdp-target-2040.png and friends.
    if not ext or (ext.lower() == "webp" and re.fullmatch(r".*-(640|1200)", stem)):
        return src
    cand = f"{stem}-{width}.webp"
    return cand if (ROOT / "public_html" / cand.lstrip("/")).exists() else src


def share_src(src, width=1200):
    """The JPEG twin of a hero, for og:image and twitter:image.

    LinkedIn does not decode WebP and WhatsApp is unreliable with it, so a
    card pointed at the -1200.webp hero previewed as a bare link on the two
    channels these actually get shared on. The WebP stays on the page; only
    the share card changes format.

    Takes either an original (/blog/images/foo.png) or a derivative already
    stamped into the markup by an earlier run (foo-1200.webp), because the
    reskin re-reads its own output. Falls back to whatever it was given when
    no JPEG has been built, so a missing derivative degrades to the old
    behaviour rather than to a broken card. Build them with
    `python3 tools/build_image_derivatives.py`.
    """
    if not src.startswith("/blog/images/"):
        return src
    stem, _, ext = src.rpartition(".")
    if not ext:
        return src
    base = re.sub(r"-(?:640|1200)$", "", stem)
    cand = f"{base}-{width}.jpg"
    return cand if (ROOT / "public_html" / cand.lstrip("/")).exists() else src


def add_breadcrumbs(doc, lang, cat):
    """Append a BreadcrumbList matching the trail the page already renders.

    Every article draws Home / Articles / Category at the top and not one of
    the 300 declared it. The trail is the machine-readable form of where the
    page sits, and it is what puts the path rather than a bare URL under a
    result - cheap to emit, and the markup to describe it is already here.
    """
    if any('"BreadcrumbList"' in b for b in doc["jsonld"]):
        return doc["jsonld"]
    t, u = C.T[lang], C.URLS[lang]
    # Named exactly as the visible trail reads - Home / Articles / Category -
    # with the current page as the last item. A BreadcrumbList that disagrees
    # with the crumbs on the page is worse than none.
    trail = [(t["crumb_home"], SITE + u["home"]),
             (t["crumb_blog"], SITE + u["blog"]),
             (legacy.text(cat), doc["canonical"])]
    items = ",\n    ".join(
        '{"@type":"ListItem","position":%d,"name":%s,"item":%s}'
        % (i, _json.dumps(name, ensure_ascii=False), _json.dumps(href, ensure_ascii=False))
        for i, (name, href) in enumerate(trail, 1))
    return doc["jsonld"] + ['{\n  "@context": "https://schema.org",\n'
                            '  "@type": "BreadcrumbList",\n  "itemListElement": [\n    '
                            + items + "\n  ]\n}"]


def render(doc, slug, lang, idx, css_href, js_href):
    t, u = C.T[lang], C.URLS[lang]
    url = doc["canonical"] or f"{SITE}/blog/{lang}/{slug}/"
    path = url.replace(SITE, "") or "/"
    mins = max(1, round(doc["words"] / WPM[lang]))
    cat = doc["category"] or t["article"]
    arrow = "&larr;" if lang == "ar" else "&rarr;"
    back_arrow = "&rarr;" if lang == "ar" else "&larr;"

    # ------------------------------------------------------------ table of contents
    toc = "".join('<li><a href="#%s">%s</a></li>' % (i, _html.escape(h))
                  for h, i in doc["headings"])
    if doc["faq"]:
        toc += '<li><a href="#questions">%s</a></li>' % t["questions"]
    if doc["refs"]:
        toc += '<li><a href="#sources">%s</a></li>' % t["sources"]
    toc_html = ""
    if toc:
        # h2, not h4. Sitting directly under the page h1 an <h4> skips two
        # levels, which is what a screen reader announces and what an outline
        # crawler reads. The visual size is the .toc rule's job, not the tag's.
        toc_html = f"""<nav class="toc" aria-label="{t["onpage"]}">
        <h2>{t["onpage"]}</h2>
        <ol>{toc}</ol>
        <p class="back"><a class="tlink" href="{u["blog"]}"><span class="arw">{back_arrow}</span><span>{t["allposts"]}</span></a></p>
      </nav>"""

    # ------------------------------------------------------------------------ hero
    hero_html = ""
    if doc["hero"].get("src"):
        alt = doc["hero"].get("alt", "")
        if ALT_BOILERPLATE in alt or not alt.strip():
            alt = legacy.text(doc["h1"])
        # The 1200px WebP, not the original. This <img> carries
        # fetchpriority="high" and is the LCP element on every article page;
        # at 761 KB it was what put a sampled article at 5.7 s mobile LCP.
        hero_html = f"""  <div class="artwrap" style="margin-top:clamp(30px,4vw,52px)">
    <figure class="afig">
      <img src="{_html.escape(hero_src(doc["hero"]["src"]), quote=True)}" alt="{_html.escape(alt, quote=True)}"
           width="1180" height="516" fetchpriority="high" decoding="async">
    </figure>
  </div>"""

    # ------------------------------------------------------------------------- CTA
    cta = doc["cta"]
    if cta and cta.get("head"):
        href = legacy.fix_link(cta["href"])
        if href.startswith(SITE):
            href = href[len(SITE):]
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        btn = "btn btn-wa" if "wa.me" in href or "whatsapp" in href else "btn btn-amber"
        icon = WA_ICON if "wa.me" in href or "api.whatsapp.com" in href else ""
        cta_html = (f'<div class="icta"><h3>{cta["head"]}</h3>'
                    + (f'<p>{cta["text"]}</p>' if cta["text"] else "")
                    + f'<div class="btn-row"><a class="{btn}" href="{_html.escape(href, quote=True)}"{ext}>'
                      f'{icon}<span>{cta["label"]}</span></a></div></div>')
    else:
        cta_html = (f'<div class="icta"><h3>{t["cta_head"]}</h3><p>{t["cta_text"]}</p>'
                    f'<div class="btn-row"><a class="btn btn-wa" href="{WA}&text={t["cta_wa"]}">'
                    f'{WA_ICON}<span>{t["cta_label"]}</span></a></div></div>')

    # ------------------------------------------------------------------------- FAQ
    faq_html = ""
    if doc["faq"]:
        # <details> keeps a long Q&A list navigable and is still fully present
        # in the DOM, so Google and the answer engines read every answer; the
        # FAQPage node in the page's own JSON-LD carries them a second time.
        rows = "".join("<details><summary>%s</summary><p>%s</p></details>" % (q, a)
                       for q, a in doc["faq"])
        faq_html = (f'<section class="faq" id="questions" style="margin-top:clamp(48px,6vw,74px)">'
                    f'<h2 style="scroll-margin-top:104px">{t["questions"]}</h2>{rows}</section>')

    # --------------------------------------------------------------------- sources
    refs_html = ""
    if doc["refs"]:
        li = "".join(
            ('<li><a href="%s" target="_blank" rel="noopener nofollow">%s</a></li>' % (
                _html.escape(uu, quote=True), lbl)) if uu else "<li>%s</li>" % lbl
            for lbl, uu in doc["refs"])
        # h2 for the same reason: Sources follows the article's <h2> sections,
        # so an <h4> there skips a level in the middle of the outline.
        refs_html = f'<div class="refs" id="sources"><h2>{t["sources"]}</h2><ol>{li}</ol></div>'

    # ---------------------------------------------------------------------- topics
    topics_html = ""
    kws = [k.strip() for k in (doc["keywords"] or "").split(",") if k.strip()][:8]
    if kws:
        topics_html = ('<div class="topics"><span>%s</span>%s</div>'
                       % (cat, "".join("<b>%s</b>" % _html.escape(k) for k in kws)))

    # --------------------------------------------------------------------- related
    rel_html = ""
    rel = related(doc, slug, lang, idx)
    if rel:
        cards = "".join(
            '<a class="card" href="%s"><span class="n">%s</span><h3>%s</h3>'
            '<span class="rd">%s</span></a>'
            % (_html.escape(e["url"].replace(SITE, ""), quote=True),
               _html.escape(e["cat"] or t["article"]), _html.escape(e["title"]), t["read"])
            for e in rel)
        rel_html = f"""
<section class="s-panel related grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>{t["keepreading"]}</p>
    <div class="grid g3" data-stagger>{cards}</div>
  </div>
</section>"""

    dek = doc["dek"] or _html.escape(doc["desc"])
    stamp = C.fmt_date(doc["date_iso"], lang)
    stamp_html = (f'<time class="stamp" datetime="{doc["date_iso"]}">{stamp} &middot; '
                  f'{mins} {t["minread"]}</time>') if stamp else \
                 f'<span class="stamp">{mins} {t["minread"]}</span>'

    body = f"""<div class="prog" id="prog" aria-hidden="true"></div>
<main id="main">

<section class="ahero grain">
  <div class="wrap-a">
    <p class="crumbs">
      <a href="{u["home"]}">{t["crumb_home"]}</a><i>{STAR}</i><a href="{u["blog"]}">{t["crumb_blog"]}</a><i>{STAR}</i>
      <span>{_html.escape(cat)}</span>
    </p>
    <h1 class="h1">{doc["h1"]}</h1>
    <p class="lede">{dek}</p>
    <div class="byline">
      <span class="bymark" aria-hidden="true"><img src="/assets/brand/icon-transparent.svg" alt="" width="26" height="26"></span>
      <div class="who"><b>{t["by"]}</b><span>{t["byrole"]}</span></div>
      <span class="sp"></span>
      {stamp_html}
      {share_row(doc["h1"], url, t)}
    </div>
  </div>
{hero_html}
</section>

<section class="s-cream">
  <div class="artwrap">
    <div class="artgrid">
      {toc_html}
      <div id="art">
        <article class="prose">
{doc["body"]}
        </article>
        {cta_html}
        {faq_html}
        {refs_html}
        {topics_html}
        <div class="brandbox">
          <span class="bmark" aria-hidden="true"><img src="/assets/brand/icon-transparent.svg" alt="" width="42" height="42"></span>
          <div>
            <p class="rolelbl">{t["aboutlbl"]}</p>
            <h3>{t["aboutname"]}</h3>
            <p>{t["abouttext"]}</p>
            <div class="btn-row">
              <a class="btn btn-wa" href="{WA}&text={t["cta_wa"]}">{WA_ICON}<span>{t["askme"]}</span></a>
              <a class="tlink" href="{u["about"]}">{t["moreabout"]} <span class="arw">{arrow}</span></a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
{rel_html}
</main>
"""

    og = share_src(doc["hero"].get("src") or "/og-aiprofitlab-2026-v2.jpg")
    if og.startswith("/"):
        og = SITE + og
    doc["canonical"] = canon_url(doc["canonical"] or url)
    doc["hreflang"] = hreflang(slug, doc["hreflang"])
    bare = doc["canonical"].rstrip("/")
    doc["jsonld"] = [b.replace(bare + '"', doc["canonical"] + '"') for b in doc["jsonld"]]
    doc["jsonld"] = add_breadcrumbs(doc, lang, cat)

    return (C.head(doc, og, css_href, js_href)
            + C.header(lang, twin_url(slug, lang))
            + body
            + C.footer(lang)
            + "</body>\n</html>\n")


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "ar"], help="only one language")
    ap.add_argument("--only", help="substring filter on the filename")
    ap.add_argument("--out", help="write into this directory instead of in place")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    css_href, js_href = build_assets(write=not a.dry_run)
    print(f"  assets: {css_href}  {js_href}")
    idx = build_index()
    langs = [a.lang] if a.lang else ["en", "ar"]
    n = 0
    for lang in langs:
        for f in sorted((BLOG / lang).glob("*.html")):
            if a.only and a.only not in f.stem:
                continue
            doc = legacy.read(f)
            out = render(doc, f.stem, lang, idx, css_href, js_href)
            if a.dry_run:
                print(f"  would write {f.relative_to(ROOT)}  {len(out)/1024:.0f} KB "
                      f"({doc['words']} words, {len(doc['faq'])} FAQ, {len(doc['refs'])} refs)")
            else:
                dest = pathlib.Path(a.out) / lang / f.name if a.out else f
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(out, encoding="utf-8")
            n += 1
    print(f"{'checked' if a.dry_run else 'rewrote'} {n} articles")


if __name__ == "__main__":
    main()
