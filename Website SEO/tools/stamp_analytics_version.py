#!/usr/bin/env python3
"""
Re-stamp /js/apl-analytics.js?v=... across every built page.

    python3 tools/stamp_analytics_version.py          # rewrite
    python3 tools/stamp_analytics_version.py --check  # report only, exit 1 if stale

Why this exists: .htaccess serves every .js as `max-age=31536000, immutable`,
so a returning visitor - or a CDN edge - holds the old script for a YEAR unless
the URL changes. The `?v=` token is a content hash of the script, so editing
apl-analytics.js and not re-stamping means the change is live for first-time
visitors only, and silently absent for exactly the returning audience a
campaign is trying to measure. See the deploy-failure-modes note.

tools/v4/kit.py already computes the token, so every page build_v4.py and the
reskins produce is correct the moment the builders re-run. This exists for the
pages no builder owns - the hand-maintained ones, en/smart-storefront.html and
en/pay.html among them - which would otherwise keep a stale token forever.

Idempotent on purpose: running it twice changes nothing the second time, which
is the property that makes it safe to put at the end of every rebuild.
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import analytics_version  # noqa: E402

ROOT = HERE.parent
PAGES = ROOT / "public_html"

# Matches the tag however it was written - the token is the only capture that
# moves, and a page that somehow lost its ?v= entirely is matched too so it
# gains one rather than being quietly skipped.
TAG = re.compile(r"(/js/apl-analytics\.js)(\?v=[A-Za-z0-9]+)?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report stale pages without writing; exit 1 if any")
    args = ap.parse_args()

    token = analytics_version.token()
    want = "/js/apl-analytics.js?v=" + token

    stale, fixed, seen = [], 0, 0

    for path in sorted(PAGES.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        if "/js/apl-analytics.js" not in text:
            continue
        seen += 1
        new = TAG.sub(want, text)
        if new == text:
            continue
        stale.append(path.relative_to(ROOT))
        if not args.check:
            path.write_text(new, encoding="utf-8")
            fixed += 1

    print(f"current token: {token}")
    print(f"pages carrying the tag: {seen}")

    if args.check:
        if stale:
            print(f"STALE: {len(stale)} page(s) still on an old token")
            for p in stale[:10]:
                print(f"  {p}")
            if len(stale) > 10:
                print(f"  ... and {len(stale) - 10} more")
            return 1
        print("all pages current")
        return 0

    print(f"re-stamped: {fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
