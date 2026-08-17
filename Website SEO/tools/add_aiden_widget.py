#!/usr/bin/env python3
"""
Add the Aiden widget to every published page that doesn't already have it.

Ten pages (home / services / process / about / contact, EN+AR) ship the widget
markup inline and lazy-load /js/aiden-chat.js from their own script block. Those
are left untouched. Every other page — articles, guides, demos, tools — gets a
single deferred script tag; aiden-chat.js builds its own DOM when none is present.

    python3 tools/add_aiden_widget.py --dry-run
    python3 tools/add_aiden_widget.py
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, "public_html")

TAG = '<script defer src="/js/aiden-chat.js"></script>'
MARKER = "/js/aiden-chat.js"

# Same exclusions as the knowledge index: don't touch scratch or template files.
EXCLUDE_FILES = {"test.html", "whatsapp_receptionist_demo.html", "Customized_CEO_Dashboard.html"}
EXCLUDE_PATTERNS = [
    re.compile(r"/en/.*-new\.html$"),
    re.compile(r"/en/index-cinematic\.html$"),
    re.compile(r"/en/preview-templates\.html$"),
    re.compile(r"/tmp_"),
]


def excluded(rel, filename):
    return filename in EXCLUDE_FILES or any(p.search(rel) for p in EXCLUDE_PATTERNS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    added, already, skipped, failed = [], [], [], []

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

            if MARKER in html:
                already.append(rel)
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
    print(f"Already had it            : {len(already)} pages")
    print(f"Skipped (template/scratch): {len(skipped)} pages")
    if already:
        print("\nPages that already load aiden-chat.js:")
        for r in already:
            print(f"  {r}")
    if failed:
        print(f"\nFAILED ({len(failed)}):", file=sys.stderr)
        for f in failed:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
