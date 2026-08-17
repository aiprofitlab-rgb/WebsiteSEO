#!/usr/bin/env python3
"""
Build the scroll-scrub frame sequence for public_html/en/index-cinematic.html.

Lives outside public_html/ on purpose: the FTP deploy mirrors that directory,
so anything left in it is publicly readable at the site root.

No Homebrew and no system ffmpeg needed. Uses the ffmpeg binary bundled with
the already-installed imageio-ffmpeg package, plus Pillow for WebP encoding.

    # before any Kling asset exists — testable placeholder sequence
    python3 tools/build_cinematic_frames.py --placeholder

    # once the assembled video exists
    python3 tools/build_cinematic_frames.py --from-video ~/Desktop/assembled.mp4

    # how heavy is it?
    python3 tools/build_cinematic_frames.py --report

If you change --frames, the page constants must change too; the script prints
the exact lines to paste.
"""

import argparse
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "public_html" / "assets" / "cinematic"
PAGE = REPO / "public_html" / "en" / "index-cinematic.html"

# Frame counts. Mobile is every 2nd desktop frame.
# 150 samples the 14.5s source at ~10 fps. 90 (~6 fps) was visibly steppy under
# the scrub even with cross-fade blending on the page side.
FRAMES = 150
DESKTOP_W, DESKTOP_H = 1440, 810
MOBILE_W, MOBILE_H = 900, 506
QUALITY_DESKTOP = 72
QUALITY_MOBILE = 68

# Budget the page is designed around.
BUDGET_DESKTOP_MB = 4.0
BUDGET_MOBILE_MB = 1.5

# Brand Playbook v2
CREAM = (241, 239, 232)
INK = (35, 43, 38)
TEAL = (15, 110, 86)
TEAL_DEEP = (10, 61, 48)
AMBER = (186, 117, 23)
AMBER_BRIGHT = (216, 146, 52)
PEARL = (231, 228, 220)
SKIN = (198, 152, 114)
SHIRT = (238, 234, 224)


# ---------------------------------------------------------------- utilities


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        sys.exit(
            "imageio-ffmpeg is not installed.\n"
            "  python3 -m pip install --user imageio-ffmpeg\n"
            "It ships its own ffmpeg binary, so no Homebrew is required."
        )
    return imageio_ffmpeg.get_ffmpeg_exe()


def video_duration(path: Path) -> float:
    """Parse duration from ffmpeg's stderr banner (no ffprobe in the bundle)."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-i", str(path)],
        capture_output=True,
        text=True,
    )
    m = re.search(r"Duration:\s*(\d+):(\d\d):(\d\d(?:\.\d+)?)", proc.stderr)
    if not m:
        sys.exit(f"Could not read duration from {path}. Is it a valid video?")
    h, mnt, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mnt * 60 + s


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c1, c2))


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(t):
    """smoothstep"""
    t = clamp01(t)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------- placeholder frames


def draw_placeholder(i: int, n: int, W: int, H: int) -> Image.Image:
    """
    A deliberately schematic robot -> human -> at-work morph.

    This exists so the scrub mechanics, sticky behaviour, overlay timing and
    load performance can all be verified before a single Kling credit is spent.
    It is not art direction — every frame is stamped PLACEHOLDER so it can
    never be mistaken for the real sequence.
    """
    t = i / (n - 1) if n > 1 else 0.0
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")

    # Phase envelopes, matched to the seven scenes in the prompt pack.
    wake = ease((t - 0.08) / 0.14)          # amber dot brightens
    fracture = ease((t - 0.26) / 0.20)      # panels lift
    human = ease((t - 0.44) / 0.22)         # becomes human
    sit = ease((t - 0.70) / 0.18)           # sits at the desk
    work = ease((t - 0.86) / 0.14)          # screen + cards light up

    u = H * 0.30                             # figure unit
    cx = W * 0.5
    cy = H * 0.56 + sit * H * 0.10           # settles downward when seated

    body_col = mix(PEARL, SHIRT, human)
    head_col = mix(PEARL, SKIN, human)
    edge_col = mix(TEAL, AMBER, human * 0.5)

    # ---- desk materialises
    if sit > 0.01:
        dy = cy + u * 0.62
        d.rounded_rectangle(
            [cx - u * 1.35, dy, cx + u * 1.35, dy + u * 0.10],
            radius=u * 0.05,
            fill=(*mix(CREAM, PEARL, 1.0), int(235 * sit)),
        )
        d.line([cx - u * 1.35, dy, cx + u * 1.35, dy], fill=(*TEAL, int(90 * sit)), width=2)
        # screen
        sw, sh = u * 0.78, u * 0.50
        sx, sy = cx + u * 0.28, dy - sh - u * 0.02
        d.rounded_rectangle(
            [sx, sy, sx + sw, sy + sh],
            radius=u * 0.03,
            fill=(*mix(PEARL, TEAL_DEEP, 0.25 + 0.35 * work), int(240 * sit)),
        )
        for k in range(3):
            ly = sy + sh * (0.28 + k * 0.22)
            lw = sw * (0.62 - k * 0.13) * work
            if lw > 1:
                d.line(
                    [sx + sw * 0.14, ly, sx + sw * 0.14 + lw, ly],
                    fill=(*(AMBER_BRIGHT if k == 1 else TEAL), int(220 * work)),
                    width=max(2, int(u * 0.022)),
                )
        # phone
        d.rounded_rectangle(
            [cx - u * 0.72, dy - u * 0.30, cx - u * 0.44, dy - u * 0.02],
            radius=u * 0.04,
            fill=(*mix(PEARL, INK, 0.55), int(235 * sit)),
        )

    # ---- torso
    torso_top = cy - u * 0.34
    torso_bot = cy + u * (0.62 if sit < 0.5 else 0.60)
    d.rounded_rectangle(
        [cx - u * 0.42, torso_top, cx + u * 0.42, torso_bot],
        radius=u * 0.20,
        fill=body_col,
    )

    # ---- arms (reach toward the desk once seated)
    reach = sit * u * 0.30
    for sgn in (-1, 1):
        ax = cx + sgn * u * 0.50
        d.rounded_rectangle(
            [ax - u * 0.11, torso_top + u * 0.06,
             ax + u * 0.11, torso_top + u * 0.62 + reach],
            radius=u * 0.10,
            fill=body_col,
        )

    # ---- head, turning three-quarter as it becomes human
    hr = u * 0.26
    hx = cx + human * u * 0.05
    hy = cy - u * 0.62 + sit * u * 0.06
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=head_col)
    # visor, only while it is still a machine
    if human < 0.98:
        d.rounded_rectangle(
            [hx - hr * 0.74, hy - hr * 0.22, hx + hr * 0.74, hy + hr * 0.30],
            radius=hr * 0.22,
            fill=(*mix(TEAL_DEEP, PEARL, 0.25), int(235 * (1 - human))),
        )

    # ---- seam lines charging with teal
    if human < 0.99:
        a = int(150 * (0.25 + 0.75 * wake) * (1 - human))
        for k in range(3):
            sy_ = torso_top + u * (0.20 + k * 0.20)
            d.line([cx - u * 0.38, sy_, cx + u * 0.38, sy_], fill=(*edge_col, a), width=2)

    # ---- panels lifting away
    if 0.01 < fracture < 0.99:
        spread = fracture * u * 0.55
        for k in range(6):
            ang = -math.pi / 2 + (k - 2.5) * 0.52
            px = cx + math.cos(ang) * spread * 1.7
            py = cy + math.sin(ang) * spread
            s = u * 0.15 * (1 - fracture * 0.4)
            d.rounded_rectangle(
                [px - s, py - s * 0.6, px + s, py + s * 0.6],
                radius=s * 0.25,
                fill=(*PEARL, int(220 * (1 - fracture))),
            )

    # ---- amber particles through the transformation
    glow = max(fracture * (1 - human), human * (1 - human) * 2)
    if glow > 0.01:
        for k in range(26):
            ang = (k / 26) * math.tau + t * 2.2
            rad = u * (0.45 + 0.55 * ((k * 37) % 11) / 11) * (0.6 + fracture)
            px = cx + math.cos(ang) * rad
            py = cy - u * 0.05 + math.sin(ang) * rad * 0.7 - fracture * u * 0.25
            r = u * 0.012 * (1 + (k % 3))
            d.ellipse([px - r, py - r, px + r, py + r],
                      fill=(*AMBER_BRIGHT, int(200 * glow)))

    # ---- the brand's amber signal dot: chest -> heart
    dot = u * 0.045 * (1 + 0.35 * wake)
    dx = cx + human * u * 0.10
    dy_ = torso_top + u * 0.22
    d.ellipse([dx - dot * 2.4, dy_ - dot * 2.4, dx + dot * 2.4, dy_ + dot * 2.4],
              fill=(*AMBER_BRIGHT, int(60 * (0.3 + 0.7 * wake))))
    d.ellipse([dx - dot, dy_ - dot, dx + dot, dy_ + dot], fill=AMBER)

    # ---- floating message cards once working
    if work > 0.02:
        for k in range(3):
            w_, h_ = u * 0.46, u * 0.13
            px = cx + u * (0.55 + k * 0.06)
            py = cy - u * (0.75 + k * 0.30) - work * u * 0.10
            d.rounded_rectangle([px, py, px + w_, py + h_], radius=h_ * 0.35,
                                fill=(*PEARL, int(230 * work)))
            d.line([px + w_ * 0.12, py + h_ * 0.5, px + w_ * 0.62, py + h_ * 0.5],
                   fill=(*TEAL, int(200 * work)), width=2)

    # ---- unmistakable placeholder stamp
    d.text((int(W * 0.035), int(H * 0.94)),
           f"PLACEHOLDER  ·  f-{i:03d}/{n:03d}  ·  t={t:.2f}",
           fill=(*INK, 120))
    return img


def build_placeholder(frames: int, recolor: bool = True) -> None:
    print(f"Rendering {frames} placeholder frames ...")
    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        for i in range(frames):
            draw_placeholder(i, frames, DESKTOP_W, DESKTOP_H).save(
                tmpd / f"src-{i:03d}.png"
            )
        encode_sets(tmpd, frames, recolor)


# ---------------------------------------------------------- video extraction


def build_from_video(video: Path, frames: int, recolor: bool = True) -> None:
    if not video.exists():
        sys.exit(f"No such video: {video}")
    dur = video_duration(video)
    fps = frames / dur
    print(f"{video.name}: {dur:.2f}s -> sampling {frames} frames at {fps:.3f} fps")

    with tempfile.TemporaryDirectory() as tmp:
        tmpd = Path(tmp)
        subprocess.run(
            [
                ffmpeg_exe(), "-y", "-i", str(video),
                "-vf", f"fps={fps:.6f},scale={DESKTOP_W}:{DESKTOP_H}:force_original_"
                       f"aspect_ratio=increase,crop={DESKTOP_W}:{DESKTOP_H}",
                "-frames:v", str(frames),
                str(tmpd / "src-%03d.png"),
            ],
            check=True,
            capture_output=True,
        )
        got = sorted(tmpd.glob("src-*.png"))
        if not got:
            sys.exit("ffmpeg produced no frames.")
        # ffmpeg is 1-indexed and can come up one short on rounding; normalise.
        for idx, p in enumerate(got):
            p.rename(tmpd / f"norm-{idx:03d}.png")
        norm = sorted(tmpd.glob("norm-*.png"))
        while len(norm) < frames:
            shutil.copy(norm[-1], tmpd / f"norm-{len(norm):03d}.png")
            norm = sorted(tmpd.glob("norm-*.png"))
        for idx, p in enumerate(norm[:frames]):
            p.rename(tmpd / f"src-{idx:03d}.png")
        print(f"Extracted {frames} frames.")
        encode_sets(tmpd, frames, recolor)


# --------------------------------------------------------------- hud recolor

# The delivered footage ends on a bright cyan holographic interface. Cyan is
# the exact "oversaturated blue tone typical of AI/SaaS marketing" the Brand
# Playbook rules out, so the closing beat gets remapped to teal + amber.
#
# Two gates keep this from touching anything it shouldn't:
#   1. Frame gate — only frames containing a strong cyan core (b-r > 120 AND
#      b > g) are processed at all. That is frames 79-89; the rest are byte
#      identical to the source.
#   2. Pixel gate — the robot's own teal panelling is blue-ish too (b-r ~ 70),
#      but teal has GREEN dominant (g > b) while cyan has BLUE dominant
#      (b > g). Without this the machine's detailing would be recoloured in
#      every frame of the first two thirds.
#
# Saturation and value are capped because the brand teal (#0F6E56 / #3FAE8A)
# is a restrained colour: a straight hue rotation at full HUD brightness reads
# as neon spring green, not teal.

HUD_H_TEAL = 124      # uint8 hue (~175 deg) — teal, leaning off pure cyan
HUD_H_AMBER = 27      # uint8 hue (~38 deg)  — amber
HUD_S_CAP = 140       # keeps the teal from going neon
HUD_V_CAP = 230
HUD_AMBER_AT = 205    # value above which a HUD pixel becomes an amber accent


def recolor_hud(im: Image.Image) -> tuple[Image.Image, bool]:
    """Cyan HUD -> teal with amber accents. Returns (image, was_changed)."""
    import numpy as np

    rgb = im.convert("RGB")
    a = np.asarray(rgb, dtype=np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    # Frame gate. Measured separation is wide: frames carrying only the robot's
    # teal panelling score <= 0.03% here, the first HUD frame (79) scores 1.05%
    # and the rest 1.5-2.9%. A 0.2% cut sits in the gap. Using a harder cyan
    # threshold (b-r > 120) instead misses frame 79, where the HUD is still
    # fading in, and leaves one cyan frame in the middle of the recoloured run.
    if (((b - r) > 60) & (b > g)).mean() < 0.002:
        return im, False                       # no HUD in this frame

    hsv = np.asarray(rgb.convert("HSV")).astype(np.int16)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    hud = (H > 118) & (H < 195) & (S > 40)
    amber = hud & (V >= HUD_AMBER_AT)
    teal = hud & ~amber

    H2, S2, V2 = H.copy(), S.copy(), V.copy()
    H2[teal] = HUD_H_TEAL
    S2[teal] = np.clip(S[teal] * 1.1, 0, HUD_S_CAP)
    V2[teal] = np.clip(V[teal], 0, HUD_V_CAP)
    H2[amber] = HUD_H_AMBER
    S2[amber] = np.clip(S[amber] * 1.5 + 40, 0, 235)

    out = np.stack([H2, S2, V2], -1).astype(np.uint8)
    return Image.fromarray(out, "HSV").convert("RGB"), True


# ------------------------------------------------------------ webp encoding


def encode_sets(src_dir: Path, frames: int, recolor: bool = True) -> None:
    desktop = OUT / "desktop"
    mobile = OUT / "mobile"
    for dirp in (desktop, mobile):
        if dirp.exists():
            shutil.rmtree(dirp)
        dirp.mkdir(parents=True)

    mobile_n = 0
    recoloured = 0
    for i in range(frames):
        src = src_dir / f"src-{i:03d}.png"
        im = Image.open(src).convert("RGB")

        if recolor:
            im, changed = recolor_hud(im)
            if changed:
                recoloured += 1
                im.save(src)          # keep stills in step with the sequence

        im.resize((DESKTOP_W, DESKTOP_H), Image.LANCZOS).save(
            desktop / f"f-{i:03d}.webp", "WEBP", quality=QUALITY_DESKTOP, method=6
        )
        if i % 2 == 0:
            im.resize((MOBILE_W, MOBILE_H), Image.LANCZOS).save(
                mobile / f"f-{mobile_n:03d}.webp", "WEBP",
                quality=QUALITY_MOBILE, method=6,
            )
            mobile_n += 1

    # Two stills, and the distinction matters:
    #   poster.webp — frame 0. Painted under the canvas so the very first thing
    #                 on screen is the same image the scrub starts from. Using
    #                 the last frame here would flash "at work" and then jump
    #                 back to "standby" once the canvas took over.
    #   still.webp  — last frame. Swapped in only on prefers-reduced-motion and
    #                 in <noscript>, where one image has to tell the whole story.
    for name, idx, q in (("poster", 0, 82), ("still", frames - 1, 82)):
        Image.open(src_dir / f"src-{idx:03d}.png").convert("RGB").resize(
            (DESKTOP_W, DESKTOP_H), Image.LANCZOS
        ).save(OUT / f"{name}.webp", "WEBP", quality=q, method=6)

    print(f"Wrote {frames} desktop + {mobile_n} mobile frames + poster + still.")
    if recolor:
        print(f"HUD recolour: {recoloured} frame(s) remapped cyan -> teal/amber.")
    check_page_constants(frames, mobile_n)
    stamp_asset_version()
    report()


def check_page_constants(desktop_n: int, mobile_n: int) -> None:
    if not PAGE.exists():
        return
    html = PAGE.read_text(encoding="utf8")
    # tolerate any spacing around "=" so aligned declarations don't false-alarm
    ok_d = re.search(rf"FRAMES_DESKTOP\s*=\s*{desktop_n}\b", html)
    ok_m = re.search(rf"FRAMES_MOBILE\s*=\s*{mobile_n}\b", html)
    if ok_d and ok_m:
        return
    print(
        "\n  ! Frame counts differ from the page. Update index-cinematic.html:\n"
        f"      const FRAMES_DESKTOP = {desktop_n};\n"
        f"      const FRAMES_MOBILE  = {mobile_n};"
    )


def stamp_asset_version() -> None:
    """
    Give this build its own asset URLs.

    The host serves /assets/cinematic/** with `max-age=31536000, immutable` and
    the filenames are positional, so f-093.webp from a new build lands on the
    URL the old f-093.webp already owns. CDN edges then keep whichever build
    they cached first, independently of one another, and a visitor can be
    served frames from two different cuts of the source in the same scrub. That
    is what produced the "the ending plays twice" report on 2026-08-17: the
    frames on disk were correct, the bytes on the edge were half a build old.

    Bumping ?v= on every rebuild gives the new frames URLs nothing has cached.
    """
    if not PAGE.exists():
        return
    html = PAGE.read_text(encoding="utf8")
    old = re.search(r'const ASSET_V\s*=\s*"([^"]+)"', html)
    if not old:
        print("\n  ! No ASSET_V constant in the page — frame URLs are not "
              "cache-busted. Rebuilt frames may not reach visitors.")
        return

    # Date, plus a letter when rebuilding more than once in a day.
    from datetime import date
    stem = date.today().strftime("%Y%m%d")
    prev = old.group(1)
    if prev == stem or prev.startswith(stem):
        suffix = prev[len(stem):]
        new = stem + (chr(ord(suffix) + 1) if suffix else "b")
    else:
        new = stem

    html = re.sub(r'(const ASSET_V\s*=\s*")[^"]+(")', rf"\g<1>{new}\g<2>", html)
    html = re.sub(r"(/assets/cinematic/[^\"'\s]*\.webp\?v=)[^\"'\s]+",
                  rf"\g<1>{new}", html)
    PAGE.write_text(html, encoding="utf8")
    print(f"Asset version: {prev} -> {new} (frame URLs cache-busted).")


# ------------------------------------------------------------------- report


def report() -> None:
    if not OUT.exists():
        sys.exit("No frames built yet. Run --placeholder or --from-video first.")

    def size_of(p: Path) -> int:
        return sum(f.stat().st_size for f in p.glob("*.webp")) if p.exists() else 0

    d_bytes = size_of(OUT / "desktop")
    m_bytes = size_of(OUT / "mobile")
    p_bytes = sum(
        (OUT / f"{n}.webp").stat().st_size
        for n in ("poster", "still")
        if (OUT / f"{n}.webp").exists()
    )

    d_n = len(list((OUT / "desktop").glob("*.webp")))
    m_n = len(list((OUT / "mobile").glob("*.webp")))

    def mb(b):
        return b / 1024 / 1024

    print("\n  frame budget")
    print("  " + "-" * 52)
    for label, n, b, budget in (
        ("desktop", d_n, d_bytes, BUDGET_DESKTOP_MB),
        ("mobile ", m_n, m_bytes, BUDGET_MOBILE_MB),
    ):
        avg = (b / n / 1024) if n else 0
        flag = "ok " if mb(b) <= budget else "OVER"
        print(f"  {label}  {n:>3} frames  {mb(b):6.2f} MB  "
              f"avg {avg:5.1f} KB  [{flag} / {budget:.1f} MB]")
    print(f"  stills            {mb(p_bytes):6.2f} MB")
    print(f"  total             {mb(d_bytes + m_bytes + p_bytes):6.2f} MB")
    print("  " + "-" * 52)
    if mb(d_bytes) > BUDGET_DESKTOP_MB or mb(m_bytes) > BUDGET_MOBILE_MB:
        print("  Over budget — lower QUALITY_DESKTOP / QUALITY_MOBILE and rebuild.\n")
    else:
        print("  Within budget.\n")


# --------------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--placeholder", action="store_true",
                   help="render a testable procedural sequence (no assets needed)")
    g.add_argument("--from-video", metavar="MP4",
                   help="extract frames from the assembled Kling video")
    g.add_argument("--report", action="store_true",
                   help="print byte sizes of the current frame sets")
    ap.add_argument("--frames", type=int, default=FRAMES,
                    help=f"desktop frame count (default {FRAMES})")
    ap.add_argument("--no-recolor", action="store_true",
                    help="keep the closing HUD its original cyan (off-brand)")
    a = ap.parse_args()

    if a.report:
        report()
    elif a.placeholder:
        build_placeholder(a.frames, not a.no_recolor)
    else:
        build_from_video(Path(a.from_video).expanduser(), a.frames, not a.no_recolor)


if __name__ == "__main__":
    main()
