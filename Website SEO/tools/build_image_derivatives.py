#!/usr/bin/env python3
"""
Resized WebP derivatives for the article heroes and the blog-hub cards.

    python3 tools/build_image_derivatives.py            # build what is missing
    python3 tools/build_image_derivatives.py --force    # rebuild everything
    python3 tools/build_image_derivatives.py --report   # print sizes, write nothing

Why this exists
---------------
Both hubs rendered every card as the article's FULL-RESOLUTION hero, scaled
down in the browser to 420x236. `public_html/blog/images/` holds 145 files
totalling 83 MB, 101 of them over 500 KB, and exactly one .webp - so a single
hub view pulled roughly 6 MB over the wire to paint thumbnails. Mobile LCP was
8.7 s on /blog-ar/ and 6.3 s on /blog/, and the 761 KB article hero carrying
`fetchpriority="high"` was the largest single element on an article page.

Two sizes, because there are two jobs:

    -640.webp   card thumbnails, displayed at 420x236 (2x on a retina phone)
    -1200.webp  the article hero, displayed at 1180 wide
    -1200.jpg   the share card behind og:image / twitter:image

The third one is a format choice, not a size one. LinkedIn does not decode
WebP at all and WhatsApp is unreliable with it, so the 308 article pages that
pointed og:image at their -1200.webp hero previewed as a bare link on exactly
the two channels these get shared on. JPEG is the one format every scraper
reads; the WebP stays where it belongs, rendering the page.

Originals are left untouched: they are the source these are derived from, and
nothing about the pipeline should depend on a lossy file.
"""
import argparse
import pathlib
import re
import sys

try:
    from PIL import Image
except ImportError:                                          # pragma: no cover
    sys.exit("Pillow is required: python3 -m pip install Pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMAGES = ROOT / "public_html" / "blog" / "images"

# (suffix, target width, quality). Quality 82 is the point where these
# photographic/illustrative PNGs stop shedding visible detail.
SIZES = ((640, 82), (1200, 82))
# (width, quality) for the share card. A touch above the WebP quality because
# JPEG spends its bits less efficiently and a share card is judged at full
# size in a feed, not scaled into a column.
SHARE = (1200, 86)
SOURCE_EXT = {".png", ".jpg", ".jpeg"}


def derivative(src: pathlib.Path, width: int) -> pathlib.Path:
    """Path of the resized WebP for `src` at `width`."""
    return src.with_name(f"{src.stem}-{width}.webp")


def share(src: pathlib.Path) -> pathlib.Path:
    """Path of the share-card JPEG for `src`."""
    return src.with_name(f"{src.stem}-{SHARE[0]}.jpg")


def is_derivative(path: pathlib.Path) -> bool:
    """True only for a file this script wrote.

    The width has to be one of ours: a source whose name merely ends in a
    number - oman-10-percent-gdp-target-2040.png, ceo-dashboard-story-
    1774720867978.png - is not a derivative, and treating it as one silently
    left seven article heroes on the full-resolution original.
    """
    widths = "|".join(str(w) for w, _ in SIZES)
    if path.suffix == ".webp" and re.fullmatch(rf".*-({widths})", path.stem):
        return True
    # The share JPEG is one of ours too. .jpg is a source extension, so
    # without this it lands in sources() on the next run and the script
    # starts building foo-1200-640.webp out of its own output.
    return (path.suffix.lower() in {".jpg", ".jpeg"}
            and re.fullmatch(rf".*-{SHARE[0]}", path.stem) is not None)


def build(src: pathlib.Path, width: int, quality: int, force=False):
    """Write one derivative. Returns (path, bytes) or None when skipped."""
    dest = derivative(src, width)
    if dest.exists() and not force and dest.stat().st_mtime >= src.stat().st_mtime:
        return None
    with Image.open(src) as im:
        # Upscaling would cost bytes and add nothing; copy the source size.
        w = min(width, im.width)
        h = round(im.height * w / im.width)
        im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im = im.resize((w, h), Image.LANCZOS)
        im.save(dest, "WEBP", quality=quality, method=6)
    return dest, dest.stat().st_size


def build_share(src: pathlib.Path, force=False):
    """Write the share-card JPEG. Returns (path, bytes) or None when skipped."""
    dest = share(src)
    if dest.exists() and not force and dest.stat().st_mtime >= src.stat().st_mtime:
        return None
    with Image.open(src) as im:
        w = min(SHARE[0], im.width)
        h = round(im.height * w / im.width)
        im = im.resize((w, h), Image.LANCZOS)
        if im.mode in ("RGBA", "LA", "P"):
            # JPEG has no alpha. Compositing onto white matches how these
            # heroes already render against the article's page background;
            # dropping the channel instead would leave the transparent areas
            # filled with whatever garbage was underneath.
            im = im.convert("RGBA")
            flat = Image.new("RGB", im.size, (255, 255, 255))
            flat.paste(im, mask=im.split()[3])
            im = flat
        else:
            im = im.convert("RGB")
        im.save(dest, "JPEG", quality=SHARE[1], optimize=True, progressive=True)
    return dest, dest.stat().st_size


def sources():
    return sorted(p for p in IMAGES.iterdir()
                  if p.suffix.lower() in SOURCE_EXT and not is_derivative(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild existing derivatives")
    ap.add_argument("--report", action="store_true", help="print sizes, write nothing")
    a = ap.parse_args()

    src_bytes = made_bytes = 0
    made = skipped = 0
    for src in sources():
        src_bytes += src.stat().st_size
        for width, quality in SIZES:
            if a.report:
                d = derivative(src, width)
                if d.exists():
                    made_bytes += d.stat().st_size
                continue
            out = build(src, width, quality, a.force)
            if out is None:
                skipped += 1
                made_bytes += derivative(src, width).stat().st_size
            else:
                made += 1
                made_bytes += out[1]

        if a.report:
            if share(src).exists():
                made_bytes += share(src).stat().st_size
        else:
            out = build_share(src, a.force)
            if out is None:
                skipped += 1
                made_bytes += share(src).stat().st_size
            else:
                made += 1
                made_bytes += out[1]

    print(f"  sources     {len(sources()):>4} files  {src_bytes/1e6:>7.1f} MB")
    print(f"  derivatives {made + skipped:>4} files  {made_bytes/1e6:>7.1f} MB"
          f"   ({made} written, {skipped} already current)")
    if src_bytes:
        print(f"  card+hero payload is now {made_bytes/src_bytes*100:.0f}% of the originals")


if __name__ == "__main__":
    main()
