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
import re

# --------------------------------------------------------------------------
# Small HTML utilities. A real parser would be nicer, but bs4 is not installed
# on this machine and the corpus is machine-generated and regular, so a
# depth-counting scanner is both sufficient and dependency-free.
# --------------------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}

_ATTR_RX = re.compile(r"""([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?""")


def attrs(s):
    """Attribute string -> dict. Bare attributes map to ''."""
    out = {}
    for m in _ATTR_RX.finditer(s or ""):
        out[m.group(1).lower()] = m.group(2) or m.group(3) or m.group(4) or ""
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

    m = re.search(r"gtag/js\?id=([A-Za-z0-9-]+)", head)
    d["ga"] = m.group(1) if m else ""

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
            q = _html.unescape(m.group(1).encode().decode("unicode_escape", "ignore"))
            a = _html.unescape(m.group(2).encode().decode("unicode_escape", "ignore"))
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
    "/en/contact/": "/en/contact-en/",
    "/en/services/": "/en/services-en/",
    "/en/about/": "/en/about-en/",
    "/en/process/": "/en/process-en/",
    "/ar/": "/",
    "/ar/contact/": "/contact/",
    "/ar/services/": "/services/",
    "/ar/about/": "/about/",
    "/ar/process/": "/process/",
}


def fix_link(href):
    """Repair a known-bad legacy target; everything else passes through."""
    base = href.split("#")[0].split("?")[0]
    if base in LINK_FIX:
        return LINK_FIX[base] + href[len(base):]
    if base.startswith("https://aiprofitlab.io"):
        tail = base[len("https://aiprofitlab.io"):]
        if tail in LINK_FIX:
            return "https://aiprofitlab.io" + LINK_FIX[tail] + href[len(base):]
    return href


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
    doc = _head(src)
    doc["path"] = str(path)
    doc["date_iso"] = _published(doc, path)

    main = inner(src, "main") or inner(src, "body") or src

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
