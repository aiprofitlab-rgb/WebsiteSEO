#!/usr/bin/env python3
"""Point every page in public_html at the new favicon set.

    python3 tools/apply_favicon_links.py --check   # report, change nothing
    python3 tools/apply_favicon_links.py           # rewrite in place

The pages were carrying two links, both at /favicon.svg. That was wrong twice
over: the artwork was the retired blue/red identity, and `apple-touch-icon`
pointed at an SVG, which iOS ignores outright - so an iPhone home-screen
shortcut got a screenshot of the page instead of a logo.

This normalises all of them onto one block. Every existing icon-ish <link>
(icon, shortcut icon, apple-touch-icon, mask-icon, manifest) is removed and
the block is written at the position of the first one, so running twice is a
no-op. Pages that never had an icon link get the block after </title>.

The ?v= token exists because .htaccess serves /favicon.svg as
`max-age=31536000, immutable`: without it, everyone who has ever loaded the
site keeps the old mark in their tab for a year. Same trick the cinematic
poster and the Aiden widget already use. favicon.ico is deliberately bare -
browsers and crawlers fetch it by convention with no query string - so it is
exempted from the immutable rule in .htaccess instead.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public_html"

VERSION = "20260822"   # keep in step with tools/build_favicons.py

BLOCK = "\n".join([
    '<link rel="icon" href="/favicon.ico" sizes="32x32">',
    '<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=%s">' % VERSION,
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=%s">' % VERSION,
    '<link rel="manifest" href="/site.webmanifest?v=%s">' % VERSION,
])

LINK = re.compile(r'[ \t]*<link\b[^>]*>[ \t]*\n?', re.I)
REL = re.compile(r'\brel\s*=\s*["\']?([^"\'>]+)', re.I)
ICON_RELS = {"icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed",
             "mask-icon", "manifest"}


def head_span(html):
    """(start, end) of the <head> contents, or None."""
    open_tag = re.search(r"<head\b[^>]*>", html, re.I)
    close_tag = re.search(r"</head\s*>", html, re.I)
    if not open_tag or not close_tag or close_tag.start() < open_tag.end():
        return None
    return open_tag.end(), close_tag.start()


def rewrite(html):
    span = head_span(html)
    if not span:
        return html, "no <head>"
    start, end = span
    head = html[start:end]

    hits = []
    for m in LINK.finditer(head):
        rel = REL.search(m.group(0))
        if rel and rel.group(1).strip().lower() in ICON_RELS:
            hits.append(m)

    if hits:
        # Rebuild the head with the block where the first icon link was.
        pieces, cursor = [], 0
        for i, m in enumerate(hits):
            pieces.append(head[cursor:m.start()])
            if i == 0:
                pieces.append(BLOCK + "\n")
            cursor = m.end()
        pieces.append(head[cursor:])
        new_head = "".join(pieces)
        action = "replaced %d link(s)" % len(hits)
    else:
        title = re.search(r"</title\s*>", head, re.I)
        at = title.end() if title else 0
        new_head = head[:at] + "\n" + BLOCK + head[at:]
        action = "inserted (none present)"

    if new_head == head:
        return html, "unchanged"
    return html[:start] + new_head + html[end:], action


def main():
    check = "--check" in sys.argv
    changed = skipped = 0
    for path in sorted(PUBLIC.rglob("*.html")):
        html = path.read_text(encoding="utf-8", errors="surrogateescape")
        new, action = rewrite(html)
        if new == html:
            skipped += 1
            if action == "no <head>":
                print("  skip  %-60s %s" % (path.relative_to(ROOT), action))
            continue
        changed += 1
        if not check:
            path.write_text(new, encoding="utf-8", errors="surrogateescape")
    print("%s: %d changed, %d already correct" %
          ("would change" if check else "changed", changed, skipped))


if __name__ == "__main__":
    main()
