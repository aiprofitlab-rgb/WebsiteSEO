#!/usr/bin/env python3
"""
The cache-busting token for /js/apl-analytics.js.

Exactly the pattern tools/aiden_version.py documents, for the same reason:
.htaccess serves every .js as `max-age=31536000, immutable`, so a stable
filename means an edited script never reaches a returning visitor - or a CDN
edge - until the cache expires a year later. The tag carries a content hash
instead, so editing the script and re-running the builders points every page
at a URL nothing has cached.

The hash itself comes from aiden_version.token(), which already takes a path.
Two copies of a four-line sha256 helper is exactly the drift this whole change
exists to avoid.

    python3 tools/analytics_version.py     # print the current token
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# Importable from tools/v4/kit.py, which sits one directory down and does not
# otherwise put tools/ on the path.
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aiden_version  # noqa: E402

SCRIPT = ROOT / "public_html" / "js" / "apl-analytics.js"


def token(path=SCRIPT):
    """Short content hash of the analytics script, e.g. '89deeeec'."""
    return aiden_version.token(path)


def src(path=SCRIPT):
    """The versioned src attribute value."""
    return "/js/apl-analytics.js?v=" + token(path)


def tag(path=SCRIPT):
    """The full script tag every page carries."""
    return '<script defer src="%s"></script>' % src(path)


if __name__ == "__main__":
    print(token())
