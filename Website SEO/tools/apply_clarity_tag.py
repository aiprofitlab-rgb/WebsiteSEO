#!/usr/bin/env python3
"""Put the shared measurement tags on every page the generators do not build.

    python3 tools/apply_clarity_tag.py --check   # report, change nothing
    python3 tools/apply_clarity_tag.py           # rewrite in place

Two tags, for the same reason and by the same rule:

  * the Microsoft Clarity snippet (kit.CLARITY_SNIPPET);
  * the shared analytics script, /js/apl-analytics.js (kit.APL_ANALYTICS_TAG),
    which carries scroll depth, real time on page, page_exit, outbound/CTA
    clicks and the page_type / content_language / article_slug dimensions that
    every other GA4 event inherits.

build_v4.py, reskin_articles.py and reskin_blog_hubs.py emit both, so the 328
pages they own carry them by construction. The rest of public_html is
hand-maintained markup from before the v4 build - the legal pages, the
Academy, /en/pay/, /en/smart-storefront/ and a tail of legacy URLs that
.htaccess now 301s away. Those had gtag pasted into them one at a time, and
nothing regenerates them, so they need this.

The analytics tag is not optional on those pages: aiden-chat.js reads its page
classifier from window.APLPage, which apl-analytics.js defines. A page with
the widget and without the script would label every visitor's context as the
generic "page".

Both snippets are read from kit rather than repeated here: the Clarity id, the
GA4 id and the script's content hash each live in exactly one place. Any
existing copy of either block is removed before the current one is written at
the end of <head>, so a second run is a no-op, a changed id propagates, and an
edited apl-analytics.js re-stamps its ?v= token instead of being duplicated.

SKIP is the dev surface: preview templates, superseded homepage cuts, and the
one-page checkout preview. They are reachable if you know the filename, and a
recording of me clicking around a preview is noise in a dataset whose whole
value is that it shows what real buyers do.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PUBLIC = ROOT / "public_html"
sys.path.insert(0, str(HERE / "v4"))

import kit  # noqa: E402

# Relative to public_html/.
SKIP = {
    "en/about-new.html", "en/academy-new.html", "en/article-new.html",
    "en/blog-new.html", "en/contact-new.html", "en/index-new.html",
    "en/process-new.html", "en/services-new.html", "en/preview-templates.html",
    "en/index-cinematic.html", "en/index-v3.html",
}

# Matches the block this script writes, comment included, so removal is exact
# and a hand-pasted variant without the comment is still caught by the second
# alternative.
EXISTING = re.compile(
    r'[ \t]*(?:<!--\s*Microsoft Clarity\s*-->\s*\n)?'
    r'[ \t]*<script\b[^>]*>(?:(?!</script>).)*clarity\.ms/tag(?:(?!</script>).)*</script>[ \t]*\n?',
    re.I | re.S)

# The analytics tag with or WITHOUT its ?v= token, so a page stamped by an
# earlier run is re-stamped rather than given a second tag.
EXISTING_APL = re.compile(
    r'[ \t]*<script\b[^>]*\bsrc="/js/apl-analytics\.js(?:\?[^"]*)?"[^>]*>\s*</script>[ \t]*\n?',
    re.I)

CLOSE_HEAD = re.compile(r"[ \t]*</head\s*>", re.I)


# (label, current snippet, regex matching any older copy of it).
TAGS = (
    ("clarity", kit.CLARITY_SNIPPET, EXISTING),
    ("analytics", kit.APL_ANALYTICS_TAG, EXISTING_APL),
)


def rewrite(html):
    """(new_html, note). note is None when the file is already correct."""
    out = html
    added, updated = [], []

    for label, snippet, existing in TAGS:
        # A page that already carries the current snippet is finished, wherever
        # in the head it sits. This is what keeps the script off the 328
        # generated pages: their tag comes from the same constant, at the
        # position their template chose, and moving it here would be undone by
        # the next build.
        if snippet in out:
            continue

        stripped = existing.sub("", out)
        had = stripped != out

        m = CLOSE_HEAD.search(stripped)
        if not m:
            return html, "no </head> - skipped"

        out = stripped[:m.start()] + snippet + "\n" + stripped[m.start():]
        (updated if had else added).append(label)

    if out == html:
        return html, None

    note = []
    if added:
        note.append("added " + "+".join(added))
    if updated:
        note.append("updated " + "+".join(updated))
    return out, ", ".join(note) or "rewritten"


def main(check):
    changed = ok = 0
    for path in sorted(PUBLIC.rglob("*.html")):
        rel = path.relative_to(PUBLIC).as_posix()
        if rel in SKIP:
            continue
        html = path.read_text(encoding="utf-8")
        out, note = rewrite(html)
        if note is None:
            ok += 1
            continue
        changed += 1
        print(f"  {'would ' if check else ''}{note}  {rel}")
        if not check:
            path.write_text(out, encoding="utf-8")

    print(f"{changed} {'to change' if check else 'changed'}, {ok} already current, "
          f"{len(SKIP)} skipped")


if __name__ == "__main__":
    main("--check" in sys.argv[1:])
