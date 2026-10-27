#!/usr/bin/env python3
"""
Builds the images and clips for /en/free-demo/ and points the page at them.

    python3 tools/free-demo/build_free_demo_assets.py

Reads the originals in .tmp/free-demo/src/ (gitignored), writes
public_html/assets/free-demo/<name>.<hash>.<ext>, and rewrites every
/assets/free-demo/<name>[.<hash>].(webp|mp4) reference in
public_html/en/free-demo.html to the current file.

The originals:
- clip-<demo>.mp4 / -m.mp4 / .png and tile-<demo>.png: the six lead preview
  demos recorded in motion by tools/free-demo/capture_demo_clips.mjs, names
  and logos blurred in the page before capture. The .png is the clip's first
  frame (its poster); the tile is the frame the peak's wall shows at rest.
- proof-<demo>-phone.png and proof-cafe-desk.png: the earlier screenshots of
  the same demos, names blurred the same way. The phone ones are the phone
  beside the hero laptop and the phone-sized wall; the café pair is the sample
  Instagram post.

Why the hash is in the filename: .htaccess serves these files
`max-age=31536000, immutable`, so a changed file under an unchanged name never
reaches a returning visitor. A new hash is a new URL.

Re-running is safe: unchanged files keep their hash, and the old file for a
changed one is deleted locally (the server keeps whatever it was sent, which
is harmless).
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

DEMOS = ("vet", "perfume", "resthouse", "kidsalon", "cafe", "salon")

# Images: output name -> (source png, max width, webp quality). The hero
# laptop is at most ~640 css px wide (1280 covers a 2x screen; phones get the
# 640 one), the wall tiles ~340 css px, the phone stills ~150.
IMAGES = {}
for d in DEMOS:
    IMAGES[f"clip-{d}"] = (f"clip-{d}.png", 1280, 74)
    IMAGES[f"clip-{d}-s"] = (f"clip-{d}.png", 640, 74)
    IMAGES[f"tile-{d}"] = (f"tile-{d}.png", 720, 74)
    IMAGES[f"proof-{d}-phone"] = (f"proof-{d}-phone.png", 420, 80)
IMAGES["clip-vet-phone"] = ("clip-vet-phone.png", 540, 74)
IMAGES["proof-cafe-desk"] = ("proof-cafe-desk.png", 1280, 76)

# The light behind the hero laptop: each demo's first frame shrunk to 32 px.
# The browser's upscale does the blur, so it costs no CSS filter.
GLOWS = {f"glow-{d}": f"clip-{d}.png" for d in DEMOS}

# Clips are copied as encoded by the capture script.
CLIPS = [f"clip-{d}" for d in DEMOS] + [f"clip-{d}-m" for d in DEMOS] + ["clip-vet-phone"]


def webp(src: Path, width: int, quality: int) -> bytes:
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def store(name: str, ext: str, data: bytes) -> str:
    h = hashlib.sha256(data).hexdigest()[:8]
    target = OUT / f"{name}.{h}.{ext}"
    for old in OUT.glob(f"{name}.*.{ext}"):
        # only this name's own hashed files: "clip-vet.*" must not catch "clip-vet-m.<hash>"
        if old != target and re.fullmatch(re.escape(name) + r"\.[0-9a-f]{8}\." + ext, old.name):
            old.unlink()
    if not target.exists():
        target.write_bytes(data)
    print(f"{target.name:40} {len(data) // 1024:>4} KB")
    return target.name


def main() -> int:
    if not SRC.is_dir():
        print(f"missing sources: {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    current = {}
    missing_src = []
    for name, (src, width, quality) in IMAGES.items():
        if not (SRC / src).exists():
            missing_src.append(src)
            continue
        current[(name, "webp")] = store(name, "webp", webp(SRC / src, width, quality))
    for name, src in GLOWS.items():
        if not (SRC / src).exists():
            missing_src.append(src)
            continue
        current[(name, "webp")] = store(name, "webp", webp(SRC / src, 32, 80))
    for name in CLIPS:
        src = SRC / f"{name}.mp4"
        if not src.exists():
            missing_src.append(src.name)
            continue
        current[(name, "mp4")] = store(name, "mp4", src.read_bytes())
    if missing_src:
        print(f"missing sources (run capture_demo_clips.mjs?): {sorted(set(missing_src))}", file=sys.stderr)
        return 1

    if PAGE.exists():
        html = PAGE.read_text(encoding="utf-8")
        missing = set()

        def swap(m):
            key = (m.group(1), m.group(2))
            if key not in current:
                missing.add(f"{key[0]}.{key[1]}")
                return m.group(0)
            return f"/assets/free-demo/{current[key]}"

        new = re.sub(r"/assets/free-demo/([a-z0-9-]+?)(?:\.[0-9a-f]{8})?\.(webp|mp4)", swap, html)
        if missing:
            print(f"page names files this script does not build: {sorted(missing)}", file=sys.stderr)
            return 1
        if new != html:
            PAGE.write_text(new, encoding="utf-8")
            print(f"updated references in {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
