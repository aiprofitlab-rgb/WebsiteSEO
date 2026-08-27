#!/usr/bin/env python3
"""
Build the Aiden knowledge index.

Crawls every published page in public_html/ and writes a compact JSON index that
the Aiden backend loads at runtime. This is what lets Aiden answer "do you have
an article about X?" with a real link, and lets it know what the visitor is
currently reading.

Output: public_html/aiden-index.json

Run after publishing new articles / editing service pages, then deploy as usual:
    python3 tools/build_aiden_index.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public_html")
OUT = os.path.join(PUBLIC, "aiden-index.json")
SITE = "https://aiprofitlab.io"

# Pages that exist on disk but are not part of the live site Aiden should cite:
# scratch/test files and pages kept live but deliberately uncited.
EXCLUDE_FILES = {
    "test.html",
    "onboarding.html",                   # client-only page, not public marketing
    # Live but deliberately unlinked and noindex - see the indexing decisions
    # note. The noindex check below would catch these anyway; they are named
    # here so the intent survives a future edit to that check.
    "medflow-sales-automation-demo.html",
    "medflow-sales-automation-demo-ar.html",
}
# The long list of retired v3/v4 filenames that used to live above was removed
# on 2026-08-27, when those 29 files were DELETED from the tree rather than
# left on disk behind their 301s. A file that does not exist cannot be walked,
# so excluding it by name is dead configuration. The redirects that keep their
# indexed URLs alive are .htaccess sections 2, 2b, 2b-i and 2c; git history has
# the files. Anything retired in future should be deleted the same way - only
# add a name here if the file has to STAY on disk and stay out of Aiden.
EXCLUDE_PATTERNS = [
    re.compile(r"/tmp_"),
    re.compile(r"^/en/claim\.html$"),    # 301s to /en/pay/; Aiden must not quote it
]

# Ordered: first matching rule wins.
TYPE_RULES = [
    (re.compile(r"/blog/(en|ar)/"), "article"),
    (re.compile(r"/academy/(en|ar)/"), "guide"),
    (re.compile(r"^/(blog|blog-ar)/index\.html$"), "blog-hub"),
    (re.compile(r"^/(academy|academy-ar)/index\.html$"), "academy-hub"),
    (re.compile(r"services"), "services"),
    (re.compile(r"process"), "process"),
    (re.compile(r"about"), "about"),
    (re.compile(r"contact"), "contact"),
    (re.compile(r"privacy|terms|legal|refund"), "legal"),
    (re.compile(r"offer|smart-storefront"), "offer"),  # the live campaign page
    (re.compile(r"simulator|calculator"), "tool"),
    (re.compile(r"demo"), "demo"),
    (re.compile(r"^/index\.html$|^/ar/index\.html$"), "home"),
]

STOPWORDS = set("""
a an the and or but if then than that this these those of in on at to for from by with without
is are was were be been being do does did doing have has had having i you he she it we they them
your our their my me us as not no yes can could should would will just about into over under more
most other some such only own same so too very s t don now what which who whom how why when where
""".split())


class TextExtractor(HTMLParser):
    """Collects visible text, headings, and paragraph copy; ignores script/style/nav."""

    SKIP = {"script", "style", "noscript", "svg", "template", "nav", "header", "footer"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.headings = []
        self.paragraphs = []
        self._skip_depth = 0
        self._heading_tag = None
        self._heading_buf = []
        self._para_depth = 0
        self._para_buf = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        elif re.fullmatch(r"h[1-3]", tag):
            self._heading_tag = tag
            self._heading_buf = []
        elif tag == "p" and not self._skip_depth:
            self._para_depth += 1
            self._para_buf = []

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == self._heading_tag:
            text = clean(" ".join(self._heading_buf))
            if 3 <= len(text) <= 120:
                self.headings.append(text)
            self._heading_tag = None
            self._heading_buf = []
        elif tag == "p" and self._para_depth:
            text = clean(" ".join(self._para_buf))
            if len(text) >= 60:
                self.paragraphs.append(text)
            self._para_depth = 0
            self._para_buf = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._heading_tag:
            self._heading_buf.append(data)
        if self._para_depth:
            self._para_buf.append(data)
        self.parts.append(data)

    @property
    def text(self):
        return clean(" ".join(self.parts))

    @property
    def body(self):
        """Real prose only — paragraphs, falling back to full text."""
        return " ".join(self.paragraphs) if self.paragraphs else self.text


def clean(s):
    return re.sub(r"\s+", " ", unescape(s or "")).strip()


def meta(html, name=None, prop=None):
    if name:
        pat = r'<meta[^>]+name=["\']%s["\'][^>]*content=["\']([^"\']*)["\']' % name
    else:
        pat = r'<meta[^>]+property=["\']%s["\'][^>]*content=["\']([^"\']*)["\']' % prop
    m = re.search(pat, html, re.I)
    if not m:
        # attribute order can be reversed
        if name:
            pat = r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']%s["\']' % name
        else:
            pat = r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*property=["\']%s["\']' % prop
        m = re.search(pat, html, re.I)
    return clean(m.group(1)) if m else ""


def page_type(rel):
    for pattern, kind in TYPE_RULES:
        if pattern.search(rel):
            return kind
    return "page"


def detect_lang(html, rel):
    m = re.search(r'<html[^>]*\blang=["\']([^"\']+)["\']', html, re.I)
    if m:
        return "ar" if m.group(1).lower().startswith("ar") else "en"
    if "/ar/" in rel or rel.endswith("-ar.html") or "-ar/" in rel:
        return "ar"
    if "/en/" in rel or rel.endswith("-en.html"):
        return "en"
    return "ar"  # site default is Arabic at the root


def url_aliases(rel, canonical):
    """
    Every path the browser might report for this page.

    Canonicals are pretty paths (/en/services-en/) while the file on disk is
    services-en.html, so the backend needs both to resolve window.location.pathname.
    """
    out = []

    def add(p):
        if p and p not in out:
            out.append(p)

    if canonical:
        path = re.sub(r"^https?://[^/]+", "", canonical) or "/"
        add(path)
        add(path.rstrip("/") or "/")
        add(path.rstrip("/") + "/")

    add(rel)                                   # /services-en.html
    add(re.sub(r"\.html$", "", rel))            # /services-en
    add(re.sub(r"/index\.html$", "/", rel))     # /blog/
    add(re.sub(r"\.html$", "/", rel))           # /services-en/
    return out


def summarize(text, limit=320):
    """First chunk of body copy, cut on a sentence boundary where possible."""
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in (". ", "? ", "! ", "، ", "۔ "):
        idx = cut.rfind(sep)
        if idx > limit * 0.5:
            return cut[: idx + 1].strip()
    return cut.rsplit(" ", 1)[0] + "…"


def keywords(title, desc, headings, text, lang):
    """Cheap term list used for retrieval scoring on the backend."""
    blob = " ".join([title, desc, " ".join(headings), text[:2500]]).lower()
    if lang == "ar":
        tokens = re.findall(r"[؀-ۿ]{3,}", blob)
    else:
        tokens = re.findall(r"[a-z][a-z0-9\-]{2,}", blob)
    counts = {}
    for tok in tokens:
        if tok in STOPWORDS:
            continue
        counts[tok] = counts.get(tok, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:25]]


ARABIC = re.compile(r"[؀-ۿ]")

# Many pages inherited a single templated Arabic meta description regardless of
# page language. It carries no page-specific meaning, so prefer real body copy.
BOILERPLATE_DESC = re.compile(r"أتمتة الذكاء الاصطناعي في عمان\. اكتشف كيف يمكننا")


def useful_desc(desc, lang):
    """Reject templated or wrong-language meta descriptions."""
    if not desc:
        return False
    if BOILERPLATE_DESC.search(desc):
        return False
    has_arabic = bool(ARABIC.search(desc))
    if lang == "en" and has_arabic:
        return False
    if lang == "ar" and not has_arabic:
        return False
    return len(desc) >= 40


def clean_title(title, lang):
    """Drop the brand suffix in either language, keeping the page-specific part."""
    parts = re.split(r"\s*[|｜]\s*", title)
    kept = [p for p in parts if p and "AI Profit Lab" not in p and "بروفيت لاب" not in p]
    title = kept[0].strip() if kept else parts[0].strip()
    return re.sub(r"\s*[\-–—]\s*AI Profit Lab.*$", "", title).strip()


def article_date(rel, html):
    m = re.search(r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})', html)
    if m:
        return m.group(1)
    m = re.search(r"/([0-9]{4}-[0-9]{2}-[0-9]{2})-", rel)
    return m.group(1) if m else ""


def dedupe(pages):
    """
    Two files can share one canonical URL (e.g. smart-website-offer-en.html and
    en/smart-website-offer.html). Keep the richest entry and merge the aliases so
    either physical path still resolves.
    """
    merged = {}
    order = []
    for p in pages:
        key = p["url"].rstrip("/") or "/"
        if key not in merged:
            merged[key] = p
            order.append(key)
            continue
        kept = merged[key]
        for alias in p["aliases"]:
            if alias not in kept["aliases"]:
                kept["aliases"].append(alias)
        # prefer the entry carrying more usable content
        if len(p.get("desc", "")) > len(kept.get("desc", "")):
            kept["desc"] = p["desc"]
        if len(p.get("headings", [])) > len(kept.get("headings", [])):
            kept["headings"] = p["headings"]
    return [merged[k] for k in order]


def excluded(rel, filename):
    if filename in EXCLUDE_FILES:
        return True
    return any(p.search(rel) for p in EXCLUDE_PATTERNS)


def build():
    pages = []
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(PUBLIC):
        dirnames[:] = [d for d in dirnames if d not in {"assets", "images", "js", "node_modules"}]
        for filename in sorted(filenames):
            if not filename.endswith(".html"):
                continue
            full = os.path.join(dirpath, filename)
            rel = "/" + os.path.relpath(full, PUBLIC).replace(os.sep, "/")
            if excluded(rel, filename):
                skipped += 1
                continue

            try:
                html = open(full, encoding="utf-8", errors="replace").read()
            except OSError as exc:
                print(f"  ! unreadable {rel}: {exc}", file=sys.stderr)
                skipped += 1
                continue

            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', html, re.I):
                skipped += 1
                continue

            parser = TextExtractor()
            try:
                parser.feed(html)
            except Exception:
                pass  # malformed markup: keep whatever was parsed

            tm = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
            title = clean(tm.group(1)) if tm else ""
            title = title or meta(html, prop="og:title") or filename

            lang = detect_lang(html, rel)
            title = clean_title(title, lang)

            desc = meta(html, name="description") or meta(html, prop="og:description")
            canonical = ""
            m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.I)
            if m:
                canonical = clean(m.group(1))

            headings = parser.headings[:12]
            body = parser.body
            if not useful_desc(desc, lang):
                desc = summarize(body, 240)

            entry = {
                "url": (re.sub(r"^https?://[^/]+", "", canonical) or rel) if canonical else rel,
                "aliases": url_aliases(rel, canonical),
                "lang": lang,
                "type": page_type(rel),
                "title": title,
                "desc": desc,
                "headings": headings,
                "keywords": keywords(title, desc, headings, body, lang),
            }
            date = article_date(rel, html)
            if date:
                entry["date"] = date
            if entry["type"] in ("article", "guide"):
                entry["summary"] = summarize(body, 320)

            pages.append(entry)

    pages = dedupe(pages)
    pages.sort(key=lambda p: (p["lang"], p["type"], p.get("date", ""), p["url"]))
    for i, p in enumerate(pages):
        p["id"] = i

    index = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "site": SITE,
        "count": len(pages),
        "pages": pages,
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, separators=(",", ":"))

    by_type = {}
    by_lang = {}
    for p in pages:
        by_type[p["type"]] = by_type.get(p["type"], 0) + 1
        by_lang[p["lang"]] = by_lang.get(p["lang"], 0) + 1

    size_kb = os.path.getsize(OUT) / 1024
    print(f"Wrote {OUT}")
    print(f"  {len(pages)} pages ({skipped} skipped), {size_kb:.0f} KB")
    print(f"  by language: {dict(sorted(by_lang.items()))}")
    print(f"  by type:     {dict(sorted(by_type.items(), key=lambda kv: -kv[1]))}")
    return index


if __name__ == "__main__":
    build()
