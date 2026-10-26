#!/usr/bin/env python3
"""
Builds the images for /en/free-demo/ and points the page at them.

    python3 tools/free-demo/build_free_demo_assets.py

Reads the originals in .tmp/free-demo/src/ (gitignored: the 16 generated
sample photos and the 12 screenshots of lead preview sites, names already
blurred at capture time), writes resized WebP files to
public_html/assets/free-demo/<name>.<hash>.webp, and rewrites every
/assets/free-demo/<name>[.<hash>].webp reference in public_html/en/free-demo.html
to the current file.

Why the hash is in the filename: .htaccess serves every image
`max-age=31536000, immutable`, so a changed image under an unchanged name
never reaches a returning visitor. A new hash is a new URL.

Re-running is safe: unchanged images keep their hash, and the old file for a
changed image is deleted locally (the server keeps whatever it was sent,
which is harmless).
"""
import hashlib
import io
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]          # Website SEO/
SRC = ROOT / ".tmp" / "free-demo" / "src"
OUT = ROOT / "public_html" / "assets" / "free-demo"
PAGE = ROOT / "public_html" / "en" / "free-demo.html"

# name -> (max width, webp quality). Sample-site photos are shown inside a
# mock laptop about 700 css px wide, so 1600 covers a 2x screen.
SIZES = {}
for trade in ("cafe", "trade", "style", "care"):
    SIZES[f"{trade}-hero"] = (1600, 78)
    for i in (1, 2, 3):
        SIZES[f"{trade}-{i}"] = (700, 78)
for t in ("perfume", "resthouse", "vet", "cafe", "kidsalon", "salon"):
    SIZES[f"proof-{t}-desk"] = (1280, 76)
    SIZES[f"proof-{t}-phone"] = (420, 80)


def encode(src: Path, width: int, quality: int) -> bytes:
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def main() -> int:
    if not SRC.is_dir():
        print(f"missing sources: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    current = {}
    for name, (width, quality) in SIZES.items():
        src = SRC / f"{name}.png"
        if not src.exists():
            print(f"missing source {src.name}", file=sys.stderr)
            return 1
        data = encode(src, width, quality)
        h = hashlib.sha256(data).hexdigest()[:8]
        target = OUT / f"{name}.{h}.webp"
        for old in OUT.glob(f"{name}.*.webp"):
            if old != target:
                old.unlink()
        if not target.exists():
            target.write_bytes(data)
        current[name] = target.name
        print(f"{target.name:40} {len(data) // 1024:>4} KB")

    if PAGE.exists():
        html = PAGE.read_text(encoding="utf-8")
        missing = set()

        def swap(m):
            name = m.group(1)
            if name not in current:
                missing.add(name)
                return m.group(0)
            return f"/assets/free-demo/{current[name]}"

        new = re.sub(r"/assets/free-demo/([a-z0-9-]+?)(?:\.[0-9a-f]{8})?\.webp", swap, html)
        if missing:
            print(f"page names images this script does not build: {sorted(missing)}", file=sys.stderr)
            return 1
        if new != html:
            PAGE.write_text(new, encoding="utf-8")
            print(f"updated references in {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
