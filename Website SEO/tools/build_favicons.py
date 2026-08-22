#!/usr/bin/env python3
"""Build the whole favicon set from tools/favicon/mark.py.

    python3 tools/build_favicons.py

Writes into public_html/:
    favicon.svg           the tile, for every browser that takes an SVG icon
    favicon.ico           16/32/48, for Safari, Windows and Google's SERP crawler
    apple-touch-icon.png  180x180, opaque, square - iOS supplies the rounding
    icon-192.png          Android home screen
    icon-512.png          Android splash / install prompt
    site.webmanifest      names the two PNGs above so Android stops guessing

Rasterising needs an SVG renderer. The machine has no rsvg/cairo/ImageMagick,
so this shells out to headless Chrome - the same renderer the brand PDFs go
through, and the one whose output actually matches what a browser tab shows.

Idempotent: re-running produces byte-identical files.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "public_html"
sys.path.insert(0, str(HERE / "favicon"))
import mark  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Bumped whenever the artwork changes. .htaccess serves everything under
# public_html as `max-age=31536000, immutable`, so a favicon at a stable
# filename would stay stale in returning browsers for a year - see
# tools/apply_favicon_links.py, which stamps this onto the <link href>.
VERSION = "20260822"


def rasterise(svg_text, size):
    """SVG string -> PIL RGBA image, via a headless Chrome screenshot."""
    if not pathlib.Path(CHROME).exists():
        sys.exit("Chrome not found at %s - no other SVG renderer is installed." % CHROME)
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        (tmp / "icon.svg").write_text(svg_text)
        href = urllib.parse.quote(str(tmp / "icon.svg"))
        (tmp / "page.html").write_text(
            "<!doctype html><meta charset=utf-8>"
            "<style>html,body{margin:0;padding:0;background:transparent}"
            "img{display:block;width:%dpx;height:%dpx}</style>"
            '<img src="file://%s">' % (size, size, href))
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--default-background-color=00000000", "--force-device-scale-factor=1",
             "--window-size=%d,%d" % (size, size),
             "--screenshot=%s" % (tmp / "shot.png"), (tmp / "page.html").as_uri()],
            check=True, capture_output=True)
        return Image.open(tmp / "shot.png").convert("RGBA").copy()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    tile, small, square = mark.tile(), mark.small(), mark.square()

    (OUT / "favicon.svg").write_text(tile)

    # 16 comes off the tighter variant; 32 and 48 off the standard tile. The
    # largest frame has to be the one .save() is called on: Pillow drops any
    # requested size larger than the base image, so leading with the 16 would
    # silently write a single-frame .ico.
    f16, f32, f48 = rasterise(small, 16), rasterise(tile, 32), rasterise(tile, 48)
    f48.save(OUT / "favicon.ico", format="ICO",
             sizes=[(16, 16), (32, 32), (48, 48)], append_images=[f16, f32])

    # iOS renders alpha in an apple-touch-icon as black, so flatten to RGB.
    rasterise(square, 180).convert("RGB").save(
        OUT / "apple-touch-icon.png", format="PNG", optimize=True)

    for size in (192, 512):
        rasterise(tile, size).save(OUT / ("icon-%d.png" % size),
                                   format="PNG", optimize=True)

    # No "display" key on purpose: this exists so Android picks the right icon
    # for a home-screen shortcut, not to turn the site into an installable app.
    (OUT / "site.webmanifest").write_text(
        '{\n'
        '  "name": "AI Profit Lab",\n'
        '  "short_name": "AI Profit Lab",\n'
        '  "icons": [\n'
        '    { "src": "/icon-192.png?v=%(v)s", "sizes": "192x192", "type": "image/png" },\n'
        '    { "src": "/icon-512.png?v=%(v)s", "sizes": "512x512", "type": "image/png" }\n'
        '  ],\n'
        '  "theme_color": "%(ground)s",\n'
        '  "background_color": "%(cream)s"\n'
        '}\n' % {"v": VERSION, "ground": mark.GROUND, "cream": "#F1EFE8"})

    for name in ("favicon.svg", "favicon.ico", "apple-touch-icon.png",
                 "icon-192.png", "icon-512.png", "site.webmanifest"):
        print("%-22s %6d bytes" % (name, (OUT / name).stat().st_size))


if __name__ == "__main__":
    main()
