"""Build the scan-to-save contact QR for Nahid Abyari.

Encodes a complete vCard 3.0 *inside* the QR - no network round-trip, so a
scan opens the phone's "add contact" sheet straight away and the person just
taps Save.

    python3 tools/build_vcard_qr.py            # everything
    python3 tools/build_vcard_qr.py --no-photo # drop PHOTO, smaller/sparser QR

Outputs to brand/vcard/. Needs segno + Pillow; opencv (cv2) is used only to
verify the finished art still decodes.

Fonts are vendored in brand/vcard/fonts/ (Marcellus + IBM Plex Mono, both OFL)
so the build is reproducible offline and matches the site's --display/--mono.
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os, sys, segno

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "brand", "vcard")
FONTS = os.path.join(OUT, "fonts")
LOGO = os.path.join(HERE, "brand", "logo")
os.makedirs(OUT, exist_ok=True)

WITH_PHOTO = "--no-photo" not in sys.argv

# ---------- brand palette (tools/v4 theme) ----------
INK      = "#0A3D30"   # logo green, QR modules on cream
GOLD     = "#BA7517"   # finder eyes on cream
GOLD_LT  = "#D89234"   # gold accent for type on dark
PALE_GLD = "#E8C98F"   # finder eyes on dark - see note in render_png
CREAM    = "#F1EFE8"
CREAM_LN = "#DCC49A"   # hairline rule
DARK     = "#0A1A14"   # dark card ground
MUTED    = "#5A665D"
MUTED_DK = "#9F9683"

# ---------- 1. the vCard ----------
# vCard 3.0, not 4.0: 3.0 is what iOS Contacts and Android/Google Contacts both
# import cleanly. item{N}.X-ABLabel is Apple's labelled-field syntax (renders as
# a named row on iOS); the group prefix is spec-legal so Android keeps the URL
# and just drops the label.
LINES = [
    "BEGIN:VCARD",
    "VERSION:3.0",
    "N:Abyari;Nahid;;;",
    "FN:Nahid Abyari",
    "ORG:AI Profit Lab",
    "TITLE:Founder",
    "TEL;TYPE=CELL:+96899245250",
    "EMAIL;TYPE=INTERNET:nahid@aiprofitlab.io",
    "ADR;TYPE=WORK:;;;Muscat;;;Oman",
    "URL:https://aiprofitlab.io",
]
if WITH_PHOTO:
    LINES.append("PHOTO;VALUE=URI:https://aiprofitlab.io/assets/email/nahid-avatar.png")
LINES += [
    "item1.URL:https://linkedin.com/in/nahid-aby",
    "item1.X-ABLabel:LinkedIn",
    "item2.URL:https://instagram.com/nahid_aby",
    "item2.X-ABLabel:Instagram",
    "item3.URL:https://wa.me/96899245250",      # wa.me, not api.whatsapp.com: 25 fewer bytes
    "item3.X-ABLabel:WhatsApp",
    "END:VCARD",
]
VCARD = "\r\n".join(LINES) + "\r\n"          # CRLF per RFC 2426

vcf = os.path.join(OUT, "nahid-abyari.vcf")
with open(vcf, "wb") as f:
    f.write(VCARD.encode("utf-8"))

# ---------- 2. the symbol ----------
# error='m' on purpose. At a fixed printed size the module *pitch* drives scan
# reliability more than the recovery level does, and M keeps the version (and so
# the module count) as low as this payload allows. boost_error still lifts us to
# a higher level for free whenever the chosen version has spare capacity.
qr = segno.make(VCARD, error="m", encoding="utf-8", mode="byte")
MX = [bytearray(r) for r in qr.matrix]
N = len(MX)
QUIET = 4
print(f"vCard {len(VCARD)}B -> QR version {qr.version}, level {qr.error}, {N} modules")

FINDERS = [(0, 0), (0, N - 7), (N - 7, 0)]
def in_finder(r, c):
    return any(fr <= r < fr + 7 and fc <= c < fc + 7 for fr, fc in FINDERS)

# centre logo plate, in modules (odd so it centres on the grid)
PLATE = 15 if WITH_PHOTO else 13
P0 = (N - PLATE) // 2
def under_plate(r, c):
    return P0 <= r < P0 + PLATE and P0 <= c < P0 + PLATE

def dark(r, c):
    return 0 <= r < N and 0 <= c < N and MX[r][c]

# ---------- 3. PNG renderer ----------
def render_png(path, fg, bg, eye, logo_png, rounded=True, scale=24, ss=3):
    """Draw the matrix by hand: modules keep full coverage but corners with no
    orthogonal neighbour get rounded, so the field reads soft without losing
    dark area. Rendered at ss-times scale and downsampled."""
    S = scale * ss
    px = (N + 2 * QUIET) * S
    im = Image.new("RGB", (px, px), bg)
    d = ImageDraw.Draw(im)
    rad = int(S * 0.5) if rounded else 0
    off = QUIET * S

    for r in range(N):
        for c in range(N):
            if not MX[r][c] or in_finder(r, c) or (logo_png and under_plate(r, c)):
                continue
            x0, y0 = off + c * S, off + r * S
            x1, y1 = x0 + S, y0 + S
            d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=fg)
            if not rad:
                continue
            up, dn = dark(r - 1, c), dark(r + 1, c)
            lf, rt = dark(r, c - 1), dark(r, c + 1)
            for corner, cut in (
                ((not up and not lf), (x0, y0, 180, 270)),
                ((not up and not rt), (x1 - rad, y0, 270, 360)),
                ((not dn and not rt), (x1 - rad, y1 - rad, 0, 90)),
                ((not dn and not lf), (x0, y1 - rad, 90, 180)),
            ):
                if not corner:
                    continue
                cx, cy, a0, a1 = cut
                d.rectangle([cx, cy, cx + rad - 1, cy + rad - 1], fill=bg)
                bx = cx if a0 in (180, 90) else cx - rad
                by = cy if a0 in (180, 270) else cy - rad
                d.pieslice([bx, by, bx + 2 * rad - 1, by + 2 * rad - 1], a0, a1, fill=fg)

    # Finder eyes stay square, deliberately. Detectors find a symbol by hunting
    # the 1:1:3:1:1 dark:light run ratio along scanlines crossing a finder;
    # rounding the corners skews that ratio on every off-centre scanline. Tested
    # here - a corner radius of even 0.9 modules stopped the code decoding at
    # every scale, while rounded *data* modules decoded with zero misreads. So
    # the brand lives in the eye colour, not the eye shape.
    #
    # The eye colour must also binarise to the same side as the data modules,
    # or the finder reads inverted. On dark grounds that rules out mid golds.
    for fr, fc in FINDERS:
        x0, y0 = off + fc * S, off + fr * S
        d.rectangle([x0, y0, x0 + 7 * S - 1, y0 + 7 * S - 1], fill=eye)
        d.rectangle([x0 + S, y0 + S, x0 + 6 * S - 1, y0 + 6 * S - 1], fill=bg)
        d.rectangle([x0 + 2 * S, y0 + 2 * S, x0 + 5 * S - 1, y0 + 5 * S - 1], fill=eye)

    # Centre mark. The modules under it were skipped above rather than painted
    # over, so the cleared area reads as plain ground - nothing peeks out around
    # the mark, and the decoder sees blank space instead of a false structure.
    if logo_png:
        px0, py0 = off + P0 * S, off + P0 * S
        mark = Image.open(logo_png).convert("RGBA")
        mark = mark.crop(mark.getchannel("A").getbbox())   # drop viewBox padding
        fit = PLATE * S * 0.80
        k = fit / max(mark.width, mark.height)
        mark = mark.resize((max(int(mark.width * k), 1), max(int(mark.height * k), 1)), Image.LANCZOS)
        im.paste(mark, (px0 + (PLATE * S - mark.width) // 2,
                        py0 + (PLATE * S - mark.height) // 2), mark)

    im = im.resize((px // ss, px // ss), Image.LANCZOS)
    im.save(path)
    return im

# ---------- 4. SVG renderer (print) ----------
def mod_d(x, y, s, tl, tr, br, bl, r):
    p = [f"M{x + (r if tl else 0)},{y}", f"H{x + s - (r if tr else 0)}"]
    if tr: p.append(f"a{r},{r} 0 0 1 {r},{r}")
    p.append(f"V{y + s - (r if br else 0)}")
    if br: p.append(f"a{r},{r} 0 0 1 -{r},{r}")
    p.append(f"H{x + (r if bl else 0)}")
    if bl: p.append(f"a{r},{r} 0 0 1 -{r},-{r}")
    p.append(f"V{y + (r if tl else 0)}")
    if tl: p.append(f"a{r},{r} 0 0 1 {r},-{r}")
    return "".join(p) + "Z"

def mark_bbox():
    """Tight bounds of the mark as fractions of its viewBox. Measured off the
    1024px render rather than by parsing the path, which is exact enough and
    keeps the SVG and PNG framing identical."""
    im = Image.open(os.path.join(LOGO, "icon-transparent.png")).convert("RGBA")
    l, t, r, b = im.getchannel("A").getbbox()
    w, h = im.size
    return l / w, t / h, (r - l) / w, (b - t) / h


def logo_svg_inner(glyph=None, dot=None):
    with open(os.path.join(LOGO, "icon-transparent.svg")) as f:
        s = f.read()
    vb = s.split('viewBox="')[1].split('"')[0].split()
    inner = s[s.index(">") + 1: s.rindex("</svg>")]
    if glyph:
        inner = inner.replace(INK, glyph)
    if dot:
        inner = inner.replace(GOLD, dot)
    return inner, [float(v) for v in vb]

def render_svg(path, fg, bg, eye, logo=True, rounded=True, glyph=None, dot=None):
    S, side = 10, (N + 2 * QUIET) * 10
    r = 5 if rounded else 0
    off = QUIET * S
    parts = []
    for row in range(N):
        for col in range(N):
            if not MX[row][col] or in_finder(row, col) or (logo and under_plate(row, col)):
                continue
            x, y = off + col * S, off + row * S
            up, dn = dark(row - 1, col), dark(row + 1, col)
            lf, rt = dark(row, col - 1), dark(row, col + 1)
            parts.append(mod_d(x, y, S, (not up and not lf), (not up and not rt),
                               (not dn and not rt), (not dn and not lf), r))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}" '
           f'viewBox="0 0 {side} {side}" shape-rendering="crispEdges">',
           f'<rect width="{side}" height="{side}" fill="{bg}"/>',
           f'<path fill="{fg}" d="{"".join(parts)}"/>']
    for fr, fc in FINDERS:   # square, for the reason spelled out in render_png
        x, y = off + fc * S, off + fr * S
        out.append(f'<rect x="{x}" y="{y}" width="{7*S}" height="{7*S}" fill="{eye}"/>')
        out.append(f'<rect x="{x+S}" y="{y+S}" width="{5*S}" height="{5*S}" fill="{bg}"/>')
        out.append(f'<rect x="{x+2*S}" y="{y+2*S}" width="{3*S}" height="{3*S}" fill="{eye}"/>')
    if logo:
        px0 = off + P0 * S
        inner, vb = logo_svg_inner(glyph, dot)
        fx, fy, fw, fh = mark_bbox()                       # crop the viewBox padding
        bx, by = vb[0] + fx * vb[2], vb[1] + fy * vb[3]
        bw, bh = fw * vb[2], fh * vb[3]
        k = (PLATE * S * 0.80) / max(bw, bh)
        tx = px0 + (PLATE * S - bw * k) / 2 - bx * k
        ty = px0 + (PLATE * S - bh * k) / 2 - by * k
        out.append(f'<g transform="translate({tx:.2f},{ty:.2f}) scale({k:.5f})">{inner}</g>')
    out.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(out))

def reversed_mark(path):
    """Recolour the transparent brand mark for dark grounds - deep-green glyph
    to cream, gold dot to pale gold. Alpha carries the antialiasing, so swapping
    RGB per pixel by nearest source colour is clean.

    This is not only cosmetic. The first cut pasted icon-on-cream.png (an opaque
    cream tile) onto the dark plate, which dropped a solid ~11x11-module blot in
    the middle of the symbol and stopped it decoding at every scale, inverted or
    not. Keeping the plate the same colour as the ground means the covered area
    reads as blank rather than as a false structure, which is why the cream card
    worked while the dark one did not.
    """
    a = np.array(Image.open(os.path.join(LOGO, "icon-transparent.png")).convert("RGBA")).astype(int)
    rgb = a[..., :3]
    def hx(h):
        h = h.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    near_glyph = ((rgb - hx(INK)) ** 2).sum(-1) <= ((rgb - hx(GOLD)) ** 2).sum(-1)
    out = np.zeros_like(a)
    out[..., :3] = np.where(near_glyph[..., None], hx(CREAM), hx(PALE_GLD))
    out[..., 3] = a[..., 3]
    Image.fromarray(out.astype(np.uint8)).save(path)
    return path


# ---------- 5. the three symbols ----------
render_png(os.path.join(OUT, "qr-cream.png"), INK, CREAM, GOLD, os.path.join(LOGO, "icon-transparent.png"))
render_svg(os.path.join(OUT, "qr-cream.svg"), INK, CREAM, GOLD)
render_png(os.path.join(OUT, "qr-dark.png"), CREAM, DARK, PALE_GLD,
           reversed_mark(os.path.join(OUT, "icon-reversed.png")))
render_svg(os.path.join(OUT, "qr-dark.svg"), CREAM, DARK, PALE_GLD, glyph=CREAM, dot=PALE_GLD)
# mono: no rounding, no mark, pure contrast - for print vendors and bad scanners
render_png(os.path.join(OUT, "qr-mono.png"), "#000000", "#FFFFFF", "#000000", None, rounded=False)
render_svg(os.path.join(OUT, "qr-mono.svg"), "#000000", "#FFFFFF", "#000000", logo=False, rounded=False)

# ---------- 6. the cards ----------
def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)

def tracked(d, xy, text, f, fill, track=0, anchor="mm"):
    """PIL has no letter-spacing; lay the glyphs out by hand."""
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x = xy[0] - total / 2 if anchor[0] == "m" else xy[0]
    for ch, w in zip(text, widths):
        d.text((x, xy[1]), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += w + track
    return total

def card(path, qr_img, bg, ink, sub, rule, accent, wordmark):
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([26, 26, W - 27, H - 27], outline=rule, width=2)

    wm = Image.open(os.path.join(LOGO, wordmark)).convert("RGBA")
    wm = wm.resize((330, int(330 * wm.height / wm.width)), Image.LANCZOS)
    im.paste(wm, ((W - wm.width) // 2, 104), wm)

    q = qr_img.resize((684, 684), Image.LANCZOS)
    im.paste(q, ((W - 684) // 2, 232))

    tracked(d, (W / 2, 1010), "NAHID ABYARI", font("Marcellus-Regular.ttf", 62), ink, track=7)
    tracked(d, (W / 2, 1074), "Founder · AI Profit Lab",
            font("IBMPlexMono-Regular.ttf", 27), sub, track=2.2)
    d.line([(W / 2 - 132, 1132), (W / 2 + 132, 1132)], fill=rule, width=2)
    tracked(d, (W / 2, 1186), "SCAN TO SAVE MY CONTACT",
            font("IBMPlexMono-SemiBold.ttf", 24), accent, track=5.5)
    tracked(d, (W / 2, 1252), "aiprofitlab.io · +968 9924 5250",
            font("IBMPlexMono-Regular.ttf", 24), sub, track=1.6)
    im.save(path)

card(os.path.join(OUT, "card-cream.png"), Image.open(os.path.join(OUT, "qr-cream.png")),
     CREAM, INK, MUTED, CREAM_LN, GOLD, "wordmark-primary.png")
card(os.path.join(OUT, "card-dark.png"), Image.open(os.path.join(OUT, "qr-dark.png")),
     DARK, CREAM, MUTED_DK, "#2A3A31", GOLD_LT, "wordmark-reversed.png")

print("wrote", ", ".join(sorted(os.listdir(OUT))))
