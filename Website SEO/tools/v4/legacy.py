#!/usr/bin/env python3
"""
Legacy article reader — parses one `public_html/blog/{en,ar}/*.html` page as it
was published on the old dark/Tailwind skin and returns its content as data.

Nothing here renders. `reskin_articles.py` pours what this returns into the v4
article system in `article_kit.py`, which is the shape that module was written
for ("so that the migration script can map an old article's DOM onto named
components once").

Two rules govern every extraction below:

  1. Never invent. If a field is absent in the source it comes back empty and
     the renderer decides on a neutral fallback. No dates, authors, statistics
     or categories are synthesised.
  2. Never lose an addressable thing. Heading ids, canonical, hreflang, the
     JSON-LD graph and every in-prose link survive byte-identical, because
     each of them is either an anchor someone already linked to or a signal
     Google and the answer engines already read.
"""
import html as _html
import json as _json
import re
import sys as _sys

import kit

# --------------------------------------------------------------------------
# Small HTML utilities. A real parser would be nicer, but bs4 is not installed
# on this machine and the corpus is machine-generated and regular, so a
# depth-counting scanner is both sufficient and dependency-free.
# --------------------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

_ATTR_RX = re.compile(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?""")


def attrs(s):
    """Attribute string -> dict of DECODED values. Bare attributes map to ''.

    The unescape is load-bearing, not tidiness. `_open()` escapes every value
    on the way out, so reading them raw made one round trip through this
    module add an escaping level: a WhatsApp href written `?phone=..&amp;text=`
    came back `&amp;amp;text=`, and the next run `&amp;amp;amp;text=`. Twelve
    re-skins stacked twelve of them, and since a browser decodes exactly one,
    WhatsApp received a parameter called `amp;amp;...text` and ignored it -
    every CTA in the corpus opened an empty compose box while still passing
    every link checker, because the phone number survived. Decoding here means
    the escape on the way out is idempotent.
    """
    out = {}
    for m in _ATTR_RX.finditer(s or ""):
        out[m.group(1).lower()] = _html.unescape(
            m.group(2) or m.group(3) or m.group(4) or "")
    return out


def element(s, tag, start=0, where=None):
    """Find the first `<tag ...>` at/after `start` whose attributes satisfy
    `where(attrdict)`, and return (open_start, inner_start, inner_end, end).

    Depth-aware, so a nested <div> inside a <div> does not close it early.
    Returns None when there is no such element.
    """
    op = re.compile(r"<%s\b([^>]*)>" % tag, re.I)
    both = re.compile(r"<(/?)%s\b([^>]*?)>" % tag, re.I)
    pos = start
    while True:
        m = op.search(s, pos)
        if not m:
            return None
        if where and not where(attrs(m.group(1))):
            pos = m.end()
            continue
        if tag.lower() in VOID or m.group(1).rstrip().endswith("/"):
            return (m.start(), m.end(), m.end(), m.end())
        depth, p = 0, m.start()
        while True:
            n = both.search(s, p)
            if not n:
                return None
            if n.group(1) == "/":
                depth -= 1
                if depth == 0:
                    return (m.start(), m.end(), n.start(), n.end())
            elif not n.group(2).rstrip().endswith("/"):
                depth += 1
            p = n.end()


def inner(s, tag, start=0, where=None):
    sp = element(s, tag, start, where)
    return s[sp[1]:sp[2]] if sp else None


def cut(s, tag, where=None, start=0):
    """Remove the first matching element and return (remainder, removed_inner)."""
    sp = element(s, tag, start, where)
    if not sp:
        return s, None
    return s[:sp[0]] + s[sp[3]:], s[sp[1]:sp[2]]


def text(h):
    """Markup -> plain text, entities resolved, whitespace collapsed."""
    h = re.sub(r"<[^>]+>", " ", h or "")
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def has(cls, *names):
    toks = (cls or "").split()
    return any(n in toks for n in names)


# --------------------------------------------------------------------------
# Head
# --------------------------------------------------------------------------
def _meta(s, name):
    """<meta name=X content=Y> in either attribute order."""
    for m in re.finditer(r"<meta\b([^>]*)>", s, re.I):
        a = attrs(m.group(1))
        if a.get("name", "").lower() == name.lower() or a.get("property", "").lower() == name.lower():
            return a.get("content", "").strip()
    return ""


def _head(s):
    head = s[:s.lower().find("</head>")] if "</head>" in s.lower() else s
    d = {}
    m = re.search(r"<title>(.*?)</title>", head, re.S | re.I)
    d["title"] = _html.unescape(m.group(1)).strip() if m else ""
    d["desc"] = _meta(head, "description")
    d["keywords"] = _meta(head, "keywords")
    d["category"] = _meta(head, "category")
    d["robots"] = _meta(head, "robots")
    d["author_meta"] = _meta(head, "author")

    d["canonical"] = ""
    d["hreflang"] = []
    for m in re.finditer(r"<link\b([^>]*)>", head, re.I):
        a = attrs(m.group(1))
        rel = a.get("rel", "").lower()
        if rel == "canonical":
            d["canonical"] = a.get("href", "")
        elif rel == "alternate" and a.get("hreflang"):
            d["hreflang"].append((a["hreflang"], a.get("href", "")))

    # JSON-LD survives verbatim: it is the single richest AEO/GEO signal on
    # the page and re-serialising it risks silently dropping a field.
    d["jsonld"] = [m.group(1).strip() for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', head, re.S | re.I)]

    # The one field that is deliberately NOT preserved. Rule 2 above keeps
    # every addressable thing the source page had, but a measurement id is not
    # an addressable thing - it is configuration, and the site has exactly one
    # correct value. Copying it across meant a stray old property survived
    # every re-skin: 94 articles carried G-2GPVY4Z5KR, a manual cleanup
    # repointed them, and the next run of reskin_articles.py read the stray
    # back out of the pre-cleanup markup and restored it. So: read what is
    # there, report anything that is not ours, and always hand back the
    # canonical id.
    m = re.search(r"gtag/js\?id=([A-Za-z0-9-]+)", head)
    found = m.group(1) if m else ""
    if found and found != kit.GA_ID:
        print(f"  !! stray GA property {found} in source; emitting {kit.GA_ID}",
              file=_sys.stderr)
    d["ga"] = kit.GA_ID

    m = re.search(r'<html\b([^>]*)>', s, re.I)
    a = attrs(m.group(1)) if m else {}
    d["lang"] = a.get("lang", "en")
    d["dir"] = a.get("dir", "rtl" if a.get("lang", "").startswith("ar") else "ltr")
    return d


def _published(d, path):
    """datePublished from the JSON-LD graph, else the filename's date stamp."""
    for block in d["jsonld"]:
        m = re.search(r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})', block)
        if m:
            return m.group(1)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(path))
    return m.group(1) if m else ""


# --------------------------------------------------------------------------
# Body regions
# --------------------------------------------------------------------------
_REF_WORDS = ("references", "sources", "المراجع", "المصادر", "مراجع", "مصادر")


_AMP_CHAIN_RX = re.compile(r"&amp;(?:amp;)+")


def _collapse_amp(src):
    """Undo stacked entity escaping: `&amp;amp;amp;` -> `&amp;`.

    The escaping bug is fixed in `attrs()`, but one unescape only removes one
    level and the corpus had up to twelve - so a straight re-run would need
    twelve passes to work through them, and every intermediate pass would ship
    a still-broken WhatsApp link. A run of two or more is corruption by
    definition: nothing on this site displays the literal text "&amp;".

    Idempotent, so it stays as a guard once the corpus is clean.
    """
    return _AMP_CHAIN_RX.sub("&amp;", src)


def _json_str(raw):
    """One JSON string body -> text, escapes resolved, encoding intact."""
    try:
        return _json.loads('"%s"' % raw)
    except ValueError:
        return raw


def _faq(main, doc):
    """[(question, answer)] from the #faq section, falling back to the
    FAQPage node in the page's own JSON-LD when the markup is missing."""
    sec = inner(main, "section", where=lambda a: a.get("id") == "faq")
    out = []
    if sec:
        for m in re.finditer(r"<h([34])[^>]*>(.*?)</h\1>\s*(?:<[^>]+>\s*)*?<p[^>]*>(.*?)</p>", sec, re.S):
            q, a = _clean_inline(m.group(2)), _clean_inline(m.group(3))
            if q and a:
                out.append((q, a))
    if out:
        return out
    for block in doc["jsonld"]:
        for m in re.finditer(r'"name"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"acceptedAnswer"\s*:\s*\{[^}]*?"text"\s*:\s*"((?:[^"\\]|\\.)*)"',
                             block, re.S):
            # json.loads, not .encode().decode("unicode_escape"): that decodes
            # as latin-1, so every non-ASCII character in an answer came back
            # mojibake - an em dash turned into "\u00e2" plus two invisible
            # bytes, and the corruption was written back on each run. It had
            # already reached 42 English files and would have reached every
            # Arabic one, where the whole answer is non-ASCII.
            q = _html.unescape(_json_str(m.group(1)))
            a = _html.unescape(_json_str(m.group(2)))
            out.append((_html.escape(q, quote=False), _html.escape(a, quote=False)))
    return out


def _refs(main):
    """[(label, url)] from the References block, plus the span to delete."""
    for m in re.finditer(r"<h([234])[^>]*>(.*?)</h\1>", main, re.S):
        if not any(w in text(m.group(2)).lower() for w in _REF_WORDS):
            continue
        sp = element(main, "ul", start=m.end())
        if not sp or sp[0] - m.end() > 400:
            continue
        items = []
        for li in re.finditer(r"<li[^>]*>(.*?)</li>", main[sp[1]:sp[2]], re.S):
            a = re.search(r'<a\b([^>]*)>(.*?)</a>', li.group(1), re.S)
            if a:
                items.append((_clean_inline(a.group(2)), attrs(a.group(1)).get("href", "")))
            elif text(li.group(1)):
                items.append((_clean_inline(li.group(1)), ""))
        return items, (m.start(), sp[3])
    return [], None


def _cta(main):
    """The end-of-article call to action, as {head, text, label, href}.

    Deliberately strict, and scanned from the end. An earlier, looser version
    matched the outermost `.glass-card` on the nine pages whose whole article
    sits inside one - the "link to WhatsApp" test hit a citation of
    business.whatsapp.com in the opening paragraph and deleted the article
    with the CTA. A CTA here must be a small, heading-plus-one-link panel that
    contains no <h2> of its own.
    """
    best = None
    for m in re.finditer(r"<div\b([^>]*)>", main, re.I):
        a = attrs(m.group(1))
        if not has(a.get("class"), "glass-card") and "border-blue-500/30" not in a.get("class", ""):
            continue
        sp = element(main, "div", start=m.start())
        if not sp:
            continue
        blk = main[sp[1]:sp[2]]
        if len(blk) > 2600 or re.search(r"<h2\b", blk, re.I):
            continue
        links = re.findall(r"<a\b([^>]*)>(.*?)</a>", blk, re.S)
        if not 1 <= len(links) <= 2:
            continue
        # Two-link CTAs exist (live demo + contact). Prefer the conversion
        # link; fall back to the first internal one.
        pick = next((l for l in links
                     if re.search(r"/contact|wa\.me|api\.whatsapp\.com", attrs(l[0]).get("href", ""))), None)
        if pick is None:
            pick = next((l for l in links
                         if re.match(r"(/|https://aiprofitlab\.io)", attrs(l[0]).get("href", ""))), None)
        if pick is None:
            continue
        links = [pick]
        href = attrs(pick[0]).get("href", "")
        h = re.search(r"<h[234][^>]*>(.*?)</h[234]>", blk, re.S)
        if not h:
            continue
        p_ = re.search(r"<p[^>]*>(.*?)</p>", blk, re.S)
        best = ({"head": _clean_inline(h.group(1)),
                 "text": _clean_inline(p_.group(1)) if p_ else "",
                 "label": _clean_inline(links[0][1]),
                 "href": href}, (sp[0], sp[3]))
    return best if best else (None, None)


def _hero(main):
    for m in re.finditer(r"<img\b([^>]*)>", main, re.I):
        a = attrs(m.group(1))
        if "/blog/images/" in a.get("src", ""):
            return ({"src": a["src"], "alt": a.get("alt", "")}, (m.start(), m.end()))
    return None, None


# The FAQ heading text each language renders. Used only to find where a
# previous run's furniture starts inside an already-damaged body.
_FAQ_HEADS = ("Questions people ask", "أسئلة يطرحها")

# One stacked copy of the article HEADER, as `rewrite()` flattens it: the
# breadcrumb line, the standfirst, the byline name, the timestamp, the two
# share links and the hero figure it has already emptied. The same twelve
# passes that stacked the FAQ stacked these above the first paragraph.
_STACKED_HEAD_RX = re.compile(
    r'\s*<p>\s*<a href="[^"]*">[^<]*</a><i>&\#10038;</i>'
    r'<a href="[^"]*">[^<]*</a><i>&\#10038;</i>\s*[^<]*</p>'
    r'(?:\s*<p>.*?</p>)?'
    r'(?:\s*<b>.*?</b>)?'
    r'(?:\s*<time[^>]*>.*?</time>)?'
    r'(?:\s*<a\b[^>]*>\s*</a>)*'
    r'(?:\s*<figure>\s*</figure>)?', re.S)

_STACKED_RX = re.compile(
    r"<h2[^>]*>\s*(?:%s)[^<]*</h2>" % "|".join(_FAQ_HEADS))

# The CTA sits directly above the first stacked FAQ copy, in this exact shape,
# because that is what the re-skin rendered before `rewrite()` flattened it.
# Each group is confined to its own element - `.*?` alone let `head` swallow
# the whole article back to the first <h3> on any page whose prose happened to
# end with a heading and a link, and the body came out 298 words long.
_STRANDED_CTA_RX = re.compile(
    r"<h3[^>]*>(?P<head>(?:(?!</h3>).)*)</h3>\s*"
    r"(?:<p[^>]*>(?P<text>(?:(?!</p>).)*)</p>\s*)?"
    r"<a\b(?P<attrs>[^>]*)>(?P<label>(?:(?!</a>).)*)</a>\s*$", re.S)


def _stranded_refs(tail):
    """The Sources list out of the furniture `_unstack` removed.

    `_refs()` never matched a re-skinned page - it looks for a heading
    followed by a <ul>, and the re-skin renders an <ol> - so from the second
    run onward every article's citations sat in the body as ordinary prose
    and `doc["refs"]` came back empty. They are worth carrying forward.
    """
    m = re.search(r"<h[234][^>]*\bid=\"sources\"[^>]*>.*?</h[234]>", tail, re.S)
    if not m:
        for h in re.finditer(r"<h([234])[^>]*>(.*?)</h\1>", tail, re.S):
            if any(w in text(h.group(2)).lower() for w in _REF_WORDS):
                m = h
                break
    if not m:
        return []
    sp = element(tail, "ol", start=m.end()) or element(tail, "ul", start=m.end())
    if not sp or sp[0] - m.end() > 400:
        return []
    out = []
    for li in re.finditer(r"<li[^>]*>(.*?)</li>", tail[sp[1]:sp[2]], re.S):
        a = re.search(r"<a\b([^>]*)>(.*?)</a>", li.group(1), re.S)
        if a:
            out.append((_clean_inline(a.group(2)), attrs(a.group(1)).get("href", "")))
        elif text(li.group(1)):
            out.append((_clean_inline(li.group(1)), ""))
    return out


def _unstack(body):
    """Strip furniture a previous run left INSIDE the article body.

    The <article class="prose"> boundary in `read()` stops this happening
    again, but it cannot undo what is already there: the copies accumulated
    before the boundary existed were written inside that wrapper, so on the
    first run after the fix they are still part of the body. This finds the
    first stacked FAQ heading, walks back over the CTA that always precedes
    it, and returns everything above it - along with that CTA, which is the
    article's own and worth keeping rather than dropping to the generic one.

    Returns (body, recovered CTA, removed tail) - the tail because the
    Sources list is in there too, stranded by the same runs, and deleting a
    page's citations to fix its duplication would be a poor trade.

    A no-op on a body that has never been stacked, which is every body once
    this has run through the corpus.
    """
    # Head first: every pass also stacked a copy of the breadcrumb, standfirst
    # and byline above the first paragraph.
    while True:
        m = _STACKED_HEAD_RX.match(body)
        if not m or m.end() == 0:
            break
        body = body[m.end():]

    m = _STACKED_RX.search(body)
    if not m:
        return body.lstrip(), None, ""
    head, tail = body[:m.start()], body[m.start():]
    cta = None
    # Only the tail can hold it, and only a conversion link makes it a CTA
    # rather than an ordinary heading that happens to end a section.
    c = _STRANDED_CTA_RX.search(head[-1600:])
    if c and re.search(r"/contact|wa\.me|api\.whatsapp\.com",
                       attrs(c.group("attrs")).get("href", "")):
        c_start = len(head) - 1600 + c.start() if len(head) > 1600 else c.start()
        cta = {"head": _clean_inline(c.group("head")),
               "text": _clean_inline(c.group("text") or ""),
               "label": _clean_inline(c.group("label")),
               "href": attrs(c.group("attrs")).get("href", "")}
        head = head[:c_start]
    return head.strip(), cta, tail


def _v4(chrome, doc):
    """Regions of a page THIS TOOL rendered on a previous run.

    Every one of these sits outside <article class="prose">, and none of them
    is shaped like the legacy markup the extractors above look for: the FAQ is
    a <section id="questions"> not <section id="faq">, Sources is an <ol> not a
    <ul>, and the CTA is .icta not .glass-card. So on a re-run every extractor
    returned nothing, the whole lot stayed in the body, and a fresh copy was
    appended below it. Reading them here is what makes the re-skin idempotent.
    """
    out = {}

    m = re.search(r'<h1[^>]*\bclass="[^"]*\bh1\b[^"]*"[^>]*>(.*?)</h1>', chrome, re.S)
    out["h1"] = _clean_inline(m.group(1)) if m else ""

    m = re.search(r'<p[^>]*\bclass="[^"]*\blede\b[^"]*"[^>]*>(.*?)</p>', chrome, re.S)
    out["dek"] = _clean_inline(m.group(1)) if m else ""

    out["hero"] = {}
    fig = element(chrome, "figure", where=lambda a: has(a.get("class"), "afig"))
    if fig:
        im = re.search(r"<img\b([^>]*)>", chrome[fig[1]:fig[2]], re.I)
        if im:
            a = attrs(im.group(1))
            out["hero"] = {"src": a.get("src", ""), "alt": a.get("alt", "")}

    faq = []
    sec = inner(chrome, "section", where=lambda a: a.get("id") == "questions")
    if sec:
        for m in re.finditer(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>\s*"
                             r"<p[^>]*>(.*?)</p>", sec, re.S):
            q, a = _clean_inline(m.group(1)), _clean_inline(m.group(2))
            if q and a:
                faq.append((q, a))
    out["faq"] = faq

    refs = []
    box = inner(chrome, "div", where=lambda a: a.get("id") == "sources"
                or has(a.get("class"), "refs"))
    if box:
        for li in re.finditer(r"<li[^>]*>(.*?)</li>", box, re.S):
            a = re.search(r"<a\b([^>]*)>(.*?)</a>", li.group(1), re.S)
            if a:
                refs.append((_clean_inline(a.group(2)), attrs(a.group(1)).get("href", "")))
            elif text(li.group(1)):
                refs.append((_clean_inline(li.group(1)), ""))
    out["refs"] = refs

    out["cta"] = None
    box = inner(chrome, "div", where=lambda a: has(a.get("class"), "icta"))
    if box:
        h = re.search(r"<h3[^>]*>(.*?)</h3>", box, re.S)
        a = re.search(r"<a\b([^>]*)>(.*?)</a>", box, re.S)
        if h and a:
            lbl = re.search(r"<span[^>]*>(.*?)</span>", a.group(2), re.S)
            p_ = re.search(r"<p[^>]*>(.*?)</p>", box, re.S)
            out["cta"] = {"head": _clean_inline(h.group(1)),
                          "text": _clean_inline(p_.group(1)) if p_ else "",
                          "label": _clean_inline(lbl.group(1) if lbl else a.group(2)),
                          "href": attrs(a.group(1)).get("href", "")}

    out["category"] = ""
    cr = inner(chrome, "p", where=lambda a: has(a.get("class"), "crumbs"))
    if cr:
        spans = re.findall(r"<span[^>]*>(.*?)</span>", cr, re.S)
        if spans:
            out["category"] = text(spans[-1])
    return out


def _dek(main, h1_end):
    """The standfirst: the first <p> in the header block after the <h1>,
    accepted only when it is close enough to be part of that block."""
    m = re.search(r"<p\b([^>]*)>(.*?)</p>", main[h1_end:h1_end + 1200], re.S)
    if not m:
        return "", None
    a = attrs(m.group(1))
    if not has(a.get("class"), "text-xl", "text-lg", "text-gray-400", "text-gray-300",
               "lead", "text-2xl"):
        return "", None
    body = _clean_inline(m.group(2))
    if len(text(body)) < 25:
        return "", None
    return body, (h1_end + m.start(), h1_end + m.end())


# --------------------------------------------------------------------------
# Inline cleaning — used for headings, deks, FAQ text and reference labels,
# where the only markup worth keeping is emphasis and links.
# --------------------------------------------------------------------------
_KEEP_INLINE = {"strong", "b", "em", "i", "code", "a", "br", "span", "sup", "sub"}


def _clean_inline(h):
    def repl(m):
        close, tag, at = m.group(1), m.group(2).lower(), m.group(3)
        if tag not in _KEEP_INLINE:
            return ""
        if tag in ("span",):
            return ""
        if close:
            return "</%s>" % tag
        if tag == "br":
            return "<br>"
        if tag == "a":
            a = attrs(at)
            href = fix_link(a.get("href", ""))
            if not href:
                return ""
            ext = href.startswith("http") and "aiprofitlab.io" not in href
            return '<a href="%s"%s>' % (_html.escape(href, quote=True),
                                        ' target="_blank" rel="noopener"' if ext else "")
        return "<%s>" % tag
    out = re.sub(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\s[^<>]*?)?)/?>", repl, h or "")
    return re.sub(r"\s+", " ", out).strip()


# --------------------------------------------------------------------------
# Prose rewriter — old Tailwind DOM in, v4 component markup out
# --------------------------------------------------------------------------
# Link targets the old corpus published that do not resolve to what they say.
# `/en/contact/` is the worst of them: the rewrite rules map /en/<name>/ to a
# root <name>.html, and contact.html is the ARABIC contact page - so 85 English
# articles were sending their readers to a page they cannot read. The rest are
# outright 404s. Repaired on the way through rather than left in place; a
# migration that carefully preserved a broken link would be preserving nothing
# worth having.
LINK_FIX = {
    # /en/<name>/ is now the v4 page itself, so those four need no repair; the
    # old -en paths are what redirect. Kept as identities so the table still
    # documents the URLs the corpus references.
    # The English home moved from /en/ to / when the v4 set launched; every
    # article's inline breadcrumb still pointed at the old path.
    "/en/": "/",
    "/en/contact-en/": "/en/contact/",
    "/en/services-en/": "/en/services/",
    "/en/about-en/": "/en/about/",
    # The stand-alone demo and simulator pages were retired into one page each
    # at the v4 launch; the corpus links to them from ~30 articles.
    "/en/whatsapp-receptionist-demo/": "/en/demos/",
    "/whatsapp-receptionist-demo/": "/en/demos/",
    "/customized-ceo-dashboard-demo/": "/en/demos/",
    "/en/missed-call-simulator-en/": "/en/simulators/",
    "/en/campaign-roi-simulator/": "/en/simulators/",
    "/campaign-roi-simulator/": "/en/simulators/",
    "/en/process-en/": "/en/process/",
    "/ar/contact/": "/contact/",
    "/ar/services/": "/services/",
    "/ar/about/": "/about/",
    "/ar/process/": "/process/",
}


def _slash(href):
    """Force the trailing-slash form of an on-site path.

    Rewrite rule 1 301s any non-file path that arrives without a trailing
    slash, and most of the corpus was written without one - so an article
    linking a sibling sent the reader through a redirect, and the sitemap
    (all slashes) disagreed with the body links (mostly none). Paths that
    name a real file keep their extension and are left alone.
    """
    base, sep, tail = href.partition("#")
    if not sep:
        base, sep, tail = href.partition("?")
    if not base.startswith(("/", "https://aiprofitlab.io/")) or base.endswith("/"):
        return href
    last = base.rstrip("/").rsplit("/", 1)[-1]
    if "." in last:
        return href
    return base + "/" + sep + tail


def fix_link(href):
    """Repair a known-bad legacy target; everything else passes through."""
    base = href.split("#")[0].split("?")[0]
    if base in LINK_FIX:
        return _slash(LINK_FIX[base] + href[len(base):])
    if base.startswith("https://aiprofitlab.io"):
        tail = base[len("https://aiprofitlab.io"):]
        if tail in LINK_FIX:
            return _slash("https://aiprofitlab.io" + LINK_FIX[tail] + href[len(base):])
    return _slash(href)


_DROP_SUBTREE = {"script", "style", "noscript", "svg", "form", "button"}
_UNWRAP = {"div", "span", "section", "article", "header", "main", "font", "center"}
_KEEP_ATTR = {"href", "src", "alt", "id", "colspan", "rowspan", "datetime", "lang",
              "dir", "title", "width", "height", "srcset", "sizes", "start", "value",
              "allow", "allowfullscreen", "frameborder", "loading", "decoding"}

# A <span> that sits in running text is content; one that sits loose in a
# <div> is chrome (the old skin's category pill, date stamp and badges). The
# only reliable difference is whether a text-flow element is open above it.
_FLOW = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th",
         "blockquote", "a", "strong", "em", "b", "i", "figcaption", "code"}

_TAG_RX = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\s[^<>]*?)?)(/?)>", re.S)


def _open(tag, a=None):
    if not a:
        return "<%s>" % tag
    s = "".join(' %s="%s"' % (k, _html.escape(v, quote=True)) for k, v in a.items() if v is not None)
    return "<%s%s>" % (tag, s)


def _heading_id(txt, used):
    base = re.sub(r"[^a-z0-9\s-]", "", text(txt).lower())
    base = re.sub(r"\s+", "-", base).strip("-")[:60].strip("-")
    if not base:
        base = "section"
    i, out = 2, base
    while out in used:
        out, i = "%s-%d" % (base, i), i + 1
    used.add(out)
    return out


def rewrite(body, headings_out=None, ids_used=None):
    """Rewrite legacy prose markup into the v4 prose vocabulary.

    Structural mapping, all of it class-driven because the corpus is Tailwind:
      div.glass-card / bordered panel -> .callout
      div.overflow-x-auto + table     -> .tblwrap > table.tbl
      iframe                          -> .embed wrapper (16:9, responsive)
      img                             -> figure.pfig with the caption preserved
      everything else decorative      -> unwrapped, so .prose styles it
    """
    ids_used = ids_used if ids_used is not None else set()
    out, stack, pos = [], [], 0
    pending_close = []          # extra closing markup keyed to stack depth

    while True:
        m = _TAG_RX.search(body, pos)
        if not m:
            out.append(body[pos:])
            break
        out.append(body[pos:m.start()])
        pos = m.end()
        if m.group(0).startswith("<!--"):
            continue

        close, tag, raw, self_close = m.group(1), m.group(2).lower(), m.group(3), m.group(4)

        # ---------------------------------------------------------- closing
        if close:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == tag:
                    act, extra = stack[i][1], stack[i][2]
                    del stack[i:]
                    if act == "keep":
                        out.append("</%s>" % tag)
                    out.append(extra)
                    break
            continue

        a = attrs(raw)
        cls = a.get("class", "")

        # ------------------------------------------------------ drop subtree
        if tag in _DROP_SUBTREE or (tag == "nav"):
            sp = element(body[m.start():], tag)
            if sp:
                pos = m.start() + sp[3]
            continue

        keep = {k: v for k, v in a.items() if k in _KEEP_ATTR}

        # ------------------------------------------------------------ blocks
        if tag == "img":
            src = keep.get("src", "")
            if not src:
                continue
            keep.setdefault("loading", "lazy")
            keep.setdefault("decoding", "async")
            keep.pop("width", None)
            keep.pop("height", None)
            out.append('<figure class="pfig">' + _open("img", keep) + "</figure>")
            continue

        if tag == "iframe":
            keep.setdefault("loading", "lazy")
            keep["allowfullscreen"] = ""
            keep.pop("width", None)
            keep.pop("height", None)
            out.append('<div class="embed">' + _open("iframe", keep) + "</iframe></div>")
            sp = element(body[m.start():], "iframe")
            if sp:
                pos = m.start() + sp[3]
            continue

        if tag == "hr":
            continue                                   # v4 separates with space

        if tag == "table":
            out.append('<div class="tblwrap"><table class="tbl">')
            stack.append(("table", "raw", "</table></div>"))
            continue

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = "h2" if tag in ("h1", "h2") else ("h3" if tag == "h3" else "h4")
            sp = element(body[m.start():], tag)
            label = body[m.start() + sp[1]:m.start() + sp[2]] if sp else ""
            hid = keep.get("id") or _heading_id(label, ids_used)
            ids_used.add(hid)
            if headings_out is not None and lvl == "h2":
                headings_out.append((text(label), hid))
            out.append(_open(lvl, {"id": hid}))
            stack.append((tag, "raw", "</%s>" % lvl))
            continue

        if tag == "span" and not any(f[0] in _FLOW for f in stack):
            sp = element(body[m.start():], "span")
            if sp:
                pos = m.start() + sp[3]
            continue

        if tag in _UNWRAP:
            # A bordered/tinted panel is the old skin's callout - but only when
            # it is a panel. On the nine oldest pages the whole article is
            # wrapped in one .glass-card, so a block holding an <h1>/<h2> or
            # running past ~2.6KB is a layout shell and gets unwrapped instead.
            # A callout this module already emitted passes straight through,
            # variant class and all. Without this the rewriter unwrapped its
            # own output, so a callout survived exactly one run.
            if tag == "div" and has(cls, "callout"):
                keep_cls = " ".join(c for c in cls.split()
                                    if c in ("callout", "warn", "tip", "note"))
                out.append('<div class="%s">' % (keep_cls or "callout"))
                stack.append((tag, "raw", "</div>"))
                continue
            if tag == "div" and (has(cls, "glass-card", "glass")
                                 or ("border" in cls and "rounded" in cls and "grid" not in cls)):
                sp = element(body[m.start():], "div")
                blk = body[m.start() + sp[1]:m.start() + sp[2]] if sp else ""
                if blk and len(blk) < 2600 and not re.search(r"<h[12]\b", blk, re.I):
                    out.append('<div class="callout">')
                    stack.append((tag, "raw", "</div>"))
                    continue
            stack.append((tag, "unwrap", ""))
            continue

        if tag == "a":
            href = fix_link(keep.get("href", ""))
            keep["href"] = href
            if not href:
                stack.append((tag, "unwrap", ""))
                continue
            if href.startswith("http") and "aiprofitlab.io" not in href:
                keep["target"] = "_blank"
                keep["rel"] = "noopener"
            keep = {k: keep[k] for k in ("href", "target", "rel", "title", "id") if k in keep}
            out.append(_open("a", keep))
            stack.append((tag, "raw", "</a>"))
            continue

        if tag in VOID:
            out.append(_open(tag, keep))
            continue

        out.append(_open(tag, keep))
        stack.append((tag, "keep", ""))

    html_out = "".join(out)
    # tidy: empty wrappers the unwrap pass leaves behind
    html_out = re.sub(r"<p>\s*</p>", "", html_out)
    html_out = re.sub(r'<div class="callout">\s*</div>', "", html_out)
    html_out = re.sub(r"<(ul|ol)>\s*</\1>", "", html_out)
    html_out = re.sub(r"[ \t]+\n", "\n", html_out)
    html_out = re.sub(r"\n{3,}", "\n\n", html_out)
    return html_out.strip()


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------
def read(path):
    """Parse one legacy article file into the dict `reskin_articles` renders."""
    src = open(path, encoding="utf-8").read()
    src = _collapse_amp(src)
    doc = _head(src)
    doc["path"] = str(path)
    doc["date_iso"] = _published(doc, path)

    main = inner(src, "main") or inner(src, "body") or src

    # A page this tool has already rendered brackets the real article in
    # <article class="prose">; everything else inside <main> is furniture this
    # tool appended last time. Taking all of <main> as the body is what made
    # the re-skin additive instead of idempotent - the CTA, the FAQ, the
    # sources, the topic chips, the author box and the related-posts grid all
    # flowed into doc["body"], and the next run appended a fresh set below
    # them. Twelve runs left 55% of the average English file as twelve stacked
    # copies of the same three blocks, with "Questions people ask" in the
    # table of contents thirteen times.
    prose = element(main, "article", where=lambda a: has(a.get("class"), "prose"))
    if prose:
        chrome = main[:prose[0]] + main[prose[3]:]
        main = main[prose[1]:prose[2]]
        v4 = _v4(chrome, doc)
        doc["h1"] = v4["h1"] or doc["title"].split("|")[0].strip()
        doc["dek"] = v4["dek"]
        doc["hero"] = v4["hero"]
        # JSON-LD first, rendered <details> second. The page's own FAQPage node
        # is carried verbatim from before any of this and is clean; the
        # <details> markup is last run's OUTPUT, so on a page corrupted by the
        # old latin-1 decode it carries that corruption forward for ever.
        doc["faq"] = _faq(main, doc) or v4["faq"]
        doc["category"] = doc["category"] or v4["category"]
        main, stranded, tail = _unstack(main)
        # The stranded one is the article's own CTA, stalled in the body since
        # the run that stopped recognising it; the one in the chrome is
        # whatever the last run fell back to. Prefer the specific one.
        doc["cta"] = stranded or v4["cta"]
        doc["refs"] = v4["refs"] or _stranded_refs(tail)
        heads, ids = [], set()
        doc["body"] = rewrite(main, headings_out=heads, ids_used=ids)
        doc["headings"] = heads
        doc["words"] = len(text(doc["body"]).split())
        return doc

    doc["faq"] = _faq(main, doc)
    main, _ = cut(main, "section", where=lambda a: a.get("id") == "faq")
    main, _ = cut(main, "nav", where=lambda a: a.get("id") == "table-of-contents")
    main, _ = cut(main, "nav", where=lambda a: a.get("id") == "header")

    doc["refs"], span = _refs(main)
    if span:
        main = main[:span[0]] + main[span[1]:]

    doc["cta"], span = _cta(main)
    if span:
        main = main[:span[0]] + main[span[1]:]

    hero, span = _hero(main)
    doc["hero"] = hero or {}
    if span:
        main = main[:span[0]] + main[span[1]:]

    h1 = element(main, "h1")
    if h1:
        doc["h1"] = _clean_inline(main[h1[1]:h1[2]])
        doc["dek"], dspan = _dek(main, h1[3])
        if dspan:
            main = main[:dspan[0]] + main[dspan[1]:]
            h1 = element(main, "h1")
        main = main[:h1[0]] + main[h1[3]:]
    else:
        doc["h1"], doc["dek"] = doc["title"].split("|")[0].strip(), ""

    # the old category pill, only when <meta name="category"> was absent
    if not doc["category"]:
        m = re.search(r'<span[^>]*class="[^"]*(?:bg-blue-500/10|rounded-full)[^"]*"[^>]*>(.*?)</span>',
                      main, re.S)
        if m and len(text(m.group(1))) < 60:
            doc["category"] = text(m.group(1))
    main = re.sub(r'<span[^>]*class="[^"]*bg-blue-500/10[^"]*"[^>]*>.*?</span>', "", main, flags=re.S)

    heads, ids = [], set()
    doc["body"] = rewrite(main, headings_out=heads, ids_used=ids)
    doc["headings"] = heads
    doc["words"] = len(text(doc["body"]).split())
    return doc
