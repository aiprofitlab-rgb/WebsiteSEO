#!/usr/bin/env python3
"""
The cache-busting token for /js/aiden-chat.js.

The widget ships from one stable filename, and .htaccess serves every .js as
`max-age=31536000, immutable`. Hostinger's edge takes that literally: on
2026-08-20 the redesigned widget was on the origin (byte-identical to the repo
under a `?cb=` buster) while every visitor - and every CDN edge - was still
being served the 17 August build, because nothing about the URL had changed.
The v4 pages carry no Tailwind, and the old widget's launcher is styled
entirely with Tailwind classes, so on those pages it rendered as a bare grey
square: "the chatbot is missing".

So the tag carries a content hash. Edit the widget, re-stamp the pages, and
every page points at a URL nothing has cached yet. The hash is derived from the
file rather than hand-bumped so it cannot be forgotten.

    python3 tools/aiden_version.py     # print the current token
"""

import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIDGET = ROOT / "public_html" / "js" / "aiden-chat.js"


def token(path=WIDGET):
    """Short content hash of the widget, e.g. '89deeeec'."""
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:8]


def src(path=WIDGET):
    """The versioned src attribute value."""
    return "/js/aiden-chat.js?v=" + token(path)


def tag(path=WIDGET):
    """The full script tag every page carries."""
    return '<script defer src="%s"></script>' % src(path)


if __name__ == "__main__":
    print(token())
