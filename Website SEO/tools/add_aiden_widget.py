#!/usr/bin/env python3
"""
Add the Aiden widget to every published page that should carry it.

Aiden runs on every page EXCEPT the articles under /blog/en/ and /blog/ar/. An
article page is a reading surface: the chat launcher competes with the reading
flow, and the article's own WhatsApp float already occupies that corner. The
blog and academy hubs DO get the widget - a visitor browsing an index is looking
for something, which is exactly when Aiden is useful.

Ten pages (home / services / process / about / contact, EN+AR) still ship the
old widget markup inline. They are given the script tag like everything else;
aiden-chat.js removes that legacy markup on mount and replaces it with the one
current widget, so no page edit is needed to retire it.

The tag carries the widget's content hash, so editing aiden-chat.js and running
this script again re-stamps every page with a URL nothing has cached - without
it the edit never reaches a returning visitor. See tools/aiden_version.py.

    python3 tools/add_aiden_widget.py --dry-run
    python3 tools/add_aiden_widget.py            # add where missing, re-stamp stale
    python3 tools/add_aiden_widget.py --prune    # also strip it from articles
"""

import argparse
import os
import re
import sys

import aiden_version

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public_html")

TAG = aiden_version.tag()
# Matches the tag with or without a version token, so a page stamped by an
# older run is still recognised - and re-stamped rather than duplicated.
MARKER = "/js/aiden-chat.js"

# Same exclusions as the knowledge index: don't touch scratch or template files.
EXCLUDE_FILES = {"test.html", "whatsapp_receptionist_demo.html", "Customized_CEO_Dashboard.html"}
EXCLUDE_PATTERNS = [
    re.compile(r"/en/.*-new\.html$"),
    re.compile(r"/en/index-cinematic\.html$"),
    re.compile(r"/en/index-v3\.html$"),
    re.compile(r"/en/preview-templates\.html$"),
    re.compile(r"/tmp_"),
    # Both blog hubs, for the reason the articles are excluded below:
    # blog_chrome.footer already pins a WhatsApp action button to the bottom
    # corner and Aiden's launcher pins to the same one, so the two overlap.
    # The articles were protected by ARTICLE_PATTERNS; the hubs were not, so
    # any run of this script silently undid the re-skin's decision on them.
    re.compile(r"^/blog/index\.html$"),
    re.compile(r"^/blog-ar/index\.html$"),
]

# Articles carry no chat widget. /en/article-v4.html is the article template for
# the v4 skin, so it follows the same rule as the articles it stands in for.
ARTICLE_PATTERNS = [
    re.compile(r"^/blog/(en|ar)/"),
    re.compile(r"^/en/article-v4\.html$"),
]

# The script tag on its own line, however it was indented when it was added.
TAG_LINE = re.compile(r"[ \t]*<script[^>]+src=\"/js/aiden-chat\.js(?:\?[^\"]*)?\"[^>]*></script>[ \t]*\n?")


def is_article(rel):
    return any(p.search(rel) for p in ARTICLE_PATTERNS)


def excluded(rel, filename):
    return filename in EXCLUDE_FILES or any(p.search(rel) for p in EXCLUDE_PATTERNS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    ap.add_argument("--prune", action="store_true",
                    help="also remove the script tag from article pages that have it")
    args = ap.parse_args()

    added, already, skipped, failed, articles, pruned, restamped = [], [], [], [], [], [], []

    for dirpath, dirnames, filenames in os.walk(PUBLIC):
        dirnames[:] = [d for d in dirnames if d not in {"assets", "images", "js", "node_modules"}]
        for filename in sorted(filenames):
            if not filename.endswith(".html"):
                continue
            full = os.path.join(dirpath, filename)
            rel = "/" + os.path.relpath(full, PUBLIC).replace(os.sep, "/")

            if excluded(rel, filename):
                skipped.append(rel)
                continue

            try:
                html = open(full, encoding="utf-8").read()
            except OSError as exc:
                failed.append(f"{rel}: {exc}")
                continue

            if is_article(rel):
                articles.append(rel)
                if args.prune and MARKER in html:
                    stripped = TAG_LINE.sub("", html)
                    if stripped != html:
                        if not args.dry_run:
                            with open(full, "w", encoding="utf-8") as fh:
                                fh.write(stripped)
                        pruned.append(rel)
                continue

            if MARKER in html:
                if TAG in html:
                    already.append(rel)
                    continue
                # Present but pointing at an older build of the widget: replace
                # the tag in place rather than adding a second one.
                updated = TAG_LINE.sub("    " + TAG + "\n", html, count=1)
                if TAG_LINE.search(html) is None:
                    failed.append(f"{rel}: widget referenced but no tag line matched")
                    continue
                if not args.dry_run:
                    with open(full, "w", encoding="utf-8") as fh:
                        fh.write(updated)
                restamped.append(rel)
                continue

            if "</body>" not in html:
                failed.append(f"{rel}: no </body>")
                continue

            # Insert immediately before the final </body> so it never blocks render.
            head, sep, tail = html.rpartition("</body>")
            updated = head + "    " + TAG + "\n" + sep + tail

            if not args.dry_run:
                with open(full, "w", encoding="utf-8") as fh:
                    fh.write(updated)
            added.append(rel)

    print(f"{'Would add' if args.dry_run else 'Added'} widget to : {len(added)} pages")
    print(f"Already current           : {len(already)} pages")
    print(f"{'Would re-stamp' if args.dry_run else 'Re-stamped'} to v={aiden_version.token()} : {len(restamped)} pages")
    print(f"Articles (widget excluded): {len(articles)} pages")
    print(f"{'Would strip' if args.dry_run else 'Stripped'} from articles : {len(pruned)} pages")
    print(f"Skipped (template/scratch): {len(skipped)} pages")
    if added:
        print("\nPages the widget was added to:")
        for r in added:
            print(f"  {r}")
    if pruned:
        print("\nArticle pages the widget was removed from:")
        for r in pruned:
            print(f"  {r}")
    if failed:
        print(f"\nFAILED ({len(failed)}):", file=sys.stderr)
        for f in failed:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
