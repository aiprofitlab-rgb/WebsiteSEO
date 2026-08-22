#!/usr/bin/env python3
"""
Swap the Tailwind CDN for the pre-built stylesheet, and drop the FOUC mask.

    python3 tools/retire_tailwind_cdn.py --dry-run
    python3 tools/retire_tailwind_cdn.py

The pages that still carry the pre-v4 skin loaded `cdn.tailwindcss.com` as a
render-blocking <script> in <head>: 124 KB fetched, then the whole stylesheet
generated in the visitor's browser, ~770 ms of render-blocking on each page by
Lighthouse's measure. Because that flashes unstyled content, every one of them
also painted a full-viewport `#fouc-overlay` over the page and only removed it
on `load` - so the visitor saw a blank rectangle until the very last asset
landed, which is what put about-en at CLS 0.363.

Build the stylesheet first:

    node_modules/.bin/tailwindcss -i tools/tailwind/input.css \\
        -o tools/tailwind/built.css --minify

then this script hashes it into apl-tailwind.<hash>.css and points the pages
at that, deleting the previous hash.

Idempotent: a page that has already been converted is left alone.
"""
import argparse
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public_html"
SHEET_DIR = "assets/css"
SHEET_GLOB = "apl-tailwind.*.css"

CDN = re.compile(r'[ \t]*<script[^>]*src="https://cdn\.tailwindcss\.com"[^>]*>\s*</script>[ \t]*\n?')
# The overlay in all three of its parts: the style block that paints it, the
# div itself, and the IIFE that takes it away on load.
FOUC_STYLE = re.compile(r'[ \t]*<style>\s*#fouc-overlay\s*\{.*?\}\s*</style>[ \t]*\n?', re.S)
FOUC_DIV = re.compile(r'[ \t]*<div id="fouc-overlay"></div>[ \t]*\n?')
FOUC_JS = re.compile(r'[ \t]*<script>\s*\(function\(\)\s*\{\s*var overlay = '
                     r'document\.getElementById\(\'fouc-overlay\'\).*?\}\)\(\);\s*</script>[ \t]*\n?', re.S)
# Some pages carry the older, blunter version of the same trick.
FOUC_HIDE = re.compile(r'[ \t]*<style>\s*body\s*\{\s*visibility:\s*hidden;?\s*\}\s*</style>[ \t]*\n?')

# The preconnect/dns-prefetch pair pointed at the CDN host. Once nothing is
# fetched from it they are two speculative connections to nowhere.
HINTS = re.compile(r'[ \t]*<link[^>]*rel="(?:preconnect|dns-prefetch)"[^>]*'
                   r'cdn\.tailwindcss\.com[^>]*>[ \t]*\n?')

def sheet_href():
    """Content-hash the built stylesheet and return its href.

    A stable filename would be the wrong shape here: .htaccess serves every
    .css as `max-age=31536000, immutable`, and this site has already lost a
    day to an edge that kept serving a year-pinned asset after the origin
    changed. The hash means a rebuilt stylesheet is a URL nothing has cached.
    Matches what reskin_articles.build_assets() does for the article CSS.
    """
    src = ROOT / "tools" / "tailwind" / "built.css"
    # Built OUTSIDE public_html on purpose: an intermediate that also sits in
    # the deploy root is a second copy of the stylesheet on a stable filename,
    # which is the thing the hash exists to avoid.
    if not src.exists():
        raise SystemExit("build %s first - see the docstring" % src)
    body = src.read_bytes()
    name = "apl-tailwind.%s.css" % hashlib.sha256(body).hexdigest()[:10]
    dest = PUBLIC / SHEET_DIR / name
    for old in (PUBLIC / SHEET_DIR).glob(SHEET_GLOB):
        if old.name != name:
            old.unlink()
    if not dest.exists():
        dest.write_bytes(body)
    return "/%s/%s" % (SHEET_DIR, name)


def strip_fouc(text):
    for rx in (FOUC_STYLE, FOUC_DIV, FOUC_JS, FOUC_HIDE):
        text = rx.sub("", text)
    return text


SHEET_LINK_RX = re.compile(
    r'[ \t]*<link rel="stylesheet" href="/assets/css/(?:tailwind\.min|apl-tailwind\.[0-9a-f]+)\.css">[ \t]*\n')


def convert(original):
    # Compare against what came in, not against a partly-cleaned copy: doing
    # the hint strip first and then testing `out != text` measured the change
    # against the already-stripped string, so a page whose only remaining
    # problem was the dead preconnect reported "no change" and kept it.
    text = HINTS.sub("", original)
    # Repoint a page already converted under a different hash.
    text = SHEET_LINK_RX.sub('<link rel="stylesheet" href="%s">\n' % HREF, text)
    if not CDN.search(text):
        # Pages that carry the mask but never loaded the CDN - the Arabic
        # Academy lessons and the retired demos and simulators. All of their
        # CSS is inline, so it applies at parse time and there is no flash to
        # hide: the overlay only holds the page blank until `load`.
        out = strip_fouc(text)
        return out, out != original
    text = CDN.sub("", text, count=1)
    text = strip_fouc(text)
    link = ('<!-- Built by tools/tailwind/input.css, not compiled in the browser. -->\n'
            '<link rel="stylesheet" href="%s">\n' % HREF)
    # The stylesheet goes where the charset/viewport pair already is, so it
    # starts downloading in the first packet rather than after the metadata.
    m = re.search(r'<meta[^>]+viewport[^>]*>\s*\n', text)
    at = m.end() if m else text.index("<head>") + len("<head>") + 1
    return text[:at] + link + text[at:], True


HREF = None


def main():
    global HREF
    HREF = sheet_href()
    print(f"  stylesheet: {HREF}")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    n = 0
    for f in sorted(PUBLIC.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        out, changed = convert(text)
        if not changed:
            continue
        n += 1
        print(f"  {'would convert' if a.dry_run else 'converted'} "
              f"{f.relative_to(ROOT)}  ({len(text) - len(out):+d} bytes)")
        if not a.dry_run:
            f.write_text(out, encoding="utf-8")
    print(f"{n} page(s)")


if __name__ == "__main__":
    main()
