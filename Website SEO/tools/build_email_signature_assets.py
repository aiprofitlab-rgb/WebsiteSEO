"""Rebuild every image used by the nahid@aiprofitlab.io email signature.

Outputs to public_html/assets/email/ (mirrored to https://aiprofitlab.io/assets/email/
by .github/workflows/deploy.yml on push to main).

    python3 tools/build_email_signature_assets.py

Needs Pillow and Google Chrome (headless Chrome rasterises the SVG glyphs;
there is no rsvg/cairosvg/ImageMagick on this machine).
"""

from PIL import Image, ImageDraw, ImageFilter
import os, statistics, subprocess, tempfile

SRC_SIG = "/Users/nahid/Desktop/Nahid/AI Profit Lab/signature_luxury_blue.PNG"
SRC_PHOTO = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/brand/photos/nahid-founder-2026-master.jpeg"
OUT = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/assets/email"
os.makedirs(OUT, exist_ok=True)

# ---------- 1. chroma-key the signature (green screen -> alpha) ----------
im = Image.open(SRC_SIG).convert("RGB")
w, h = im.size
px = im.load()

# key colour = median of the border ring
ring = []
for x in range(0, w, 7):
    ring += [px[x, 2], px[x, h - 3]]
for y in range(0, h, 7):
    ring += [px[2, y], px[w - 3, y]]
kr = statistics.median(p[0] for p in ring)
kg = statistics.median(p[1] for p in ring)
kb = statistics.median(p[2] for p in ring)
print("key colour:", (kr, kg, kb))

T1, T2 = 70.0, 165.0   # fully keyed  ->  fully opaque
out = Image.new("RGBA", (w, h))
op = out.load()
for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        d = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
        if d <= T1:
            op[x, y] = (0, 0, 0, 0)
            continue
        a = 255 if d >= T2 else int(255 * (d - T1) / (T2 - T1))
        # despill: kill the green fringe left on soft edges
        avg = (r + b) / 2
        if g > avg:
            g = int(avg + (g - avg) * 0.15)
        op[x, y] = (r, g, b, a)

bbox = out.getbbox()
out = out.crop(bbox)
pad = 12
canvas = Image.new("RGBA", (out.width + pad * 2, out.height + pad * 2), (0, 0, 0, 0))
canvas.paste(out, (pad, pad), out)
target_w = 480                                   # 240 CSS px @2x
canvas = canvas.resize((target_w, round(canvas.height * target_w / canvas.width)), Image.LANCZOS)
canvas.save(f"{OUT}/nahid-signature.png", optimize=True)
# dark-mode fallback: same art flattened onto white, for clients that invert
# the page behind a transparent PNG and swallow the dark navy ink
flat = Image.new("RGB", canvas.size, (255, 255, 255))
flat.paste(canvas, (0, 0), canvas)
flat.save(f"{OUT}/nahid-signature-white.png", optimize=True)
print("signature:", canvas.size, os.path.getsize(f"{OUT}/nahid-signature.png") // 1024, "KB")

# ---------- 2. circular avatar ----------
ph = Image.open(SRC_PHOTO).convert("RGB")
# square crop around the head/shoulders (source is 1536x2752)
box = (105, 150, 1455, 1500)
ph = ph.crop(box)
S = 240                                          # 120 CSS px @2x
ph = ph.resize((S, S), Image.LANCZOS)
SS = 4                                           # supersampled mask -> smooth edge
mask = Image.new("L", (S * SS, S * SS), 0)
ImageDraw.Draw(mask).ellipse((0, 0, S * SS - 1, S * SS - 1), fill=255)
mask = mask.resize((S, S), Image.LANCZOS)
av = Image.new("RGBA", (S, S), (0, 0, 0, 0))
av.paste(ph, (0, 0), mask)
av.save(f"{OUT}/nahid-avatar.png", optimize=True)
print("avatar:", av.size, os.path.getsize(f"{OUT}/nahid-avatar.png") // 1024, "KB")


# ---------- 3. social icons ----------
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
D = tempfile.mkdtemp(prefix="apl-sig-html-")   # scratch for the SVG pages Chrome shoots

# glyph paths: whatsapp/linkedin/youtube/facebook lifted verbatim from the site footer
P = {
 "whatsapp": "M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.2 15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 0 1 12 3.8zm-3.1 4c-.2 0-.5 0-.7.3-.2.3-.9.9-.9 2.1s.9 2.4 1 2.6c.1.2 1.8 2.8 4.4 3.8 2.2.9 2.6.7 3.1.7.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.1-1.2-.1-.1-.2-.2-.5-.3l-1.7-.8c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.1-.2 0-.4.1-.5l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5L10 8.2c-.2-.4-.4-.4-.6-.4h-.5z",
 "linkedin": "M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z",
 "youtube": "M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z",
 "facebook": "M9 8h-3v4h3v12h5v-12h3.642l.358-4h-4v-1.667c0-.955.192-1.333 1.115-1.333h2.885v-5h-3.808c-3.596 0-5.192 1.583-5.192 4.615v3.385z",
 "instagram": "M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm7.846-10.405a1.441 1.441 0 01-2.88 0 1.44 1.44 0 012.88 0z",
}
FILL = {
 "whatsapp":  "#25D366",
 "linkedin":  "#0A66C2",
 "youtube":   "#FF0000",
 "facebook":  "#1877F2",
 "instagram": "url(#ig)",
}
IG_GRAD = ('<defs><linearGradient id="ig" x1="0" y1="1" x2="1" y2="0">'
           '<stop offset="0" stop-color="#FEDA75"/><stop offset=".25" stop-color="#FA7E1E"/>'
           '<stop offset=".55" stop-color="#D62976"/><stop offset=".8" stop-color="#962FBF"/>'
           '<stop offset="1" stop-color="#4F5BD5"/></linearGradient></defs>')

SIZE = 28          # CSS px shown in the mail
GLYPH = 15.5       # glyph box inside the circle
off = (SIZE - GLYPH) / 2
for name, path in P.items():
    grad = IG_GRAD if name == "instagram" else ""
    html = f"""<html><body style="margin:0;background:transparent">
<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">{grad}
<circle cx="{SIZE/2}" cy="{SIZE/2}" r="{SIZE/2}" fill="{FILL[name]}"/>
<g transform="translate({off},{off}) scale({GLYPH/24})"><path d="{path}" fill="#ffffff"/></g>
</svg></body></html>"""
    open(f"{D}/{name}.html", "w").write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--default-background-color=00000000", "--force-device-scale-factor=2",
                    f"--window-size={SIZE},{SIZE}",
                    f"--screenshot={OUT}/icon-{name}.png", f"file://{D}/{name}.html"],
                   check=True, capture_output=True)
    print(name, os.path.getsize(f"{OUT}/icon-{name}.png"), "bytes")


# ---------- 4. brand wordmark ----------
WM = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/assets/brand/wordmark-primary.svg"
w, h = 150, 26
open(f"{D}/wordmark.html", "w").write(
    f'<html><body style="margin:0;background:transparent">'
    f'<img src="file://{WM}" width="{w}" style="display:block"></body></html>')
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                "--default-background-color=00000000", "--force-device-scale-factor=2",
                f"--window-size={w},{h}", f"--screenshot={OUT}/apl-wordmark.png",
                f"file://{D}/wordmark.html"], check=True, capture_output=True)
print("wordmark done")
