#!/usr/bin/env python3
"""The AI Profit Lab monogram, as favicon-shaped SVG.

The brand icon files in brand/logo/ are drawn on a 3129x3129 canvas with the
mark sitting off-centre and a lot of air around it - fine for a slide, wrong
for a 16px tab. Here the same two glyph paths and the amber dot are re-framed
on a tight square tile so the mark fills ~80% of the width, and the ground is
a brand token (--teal-900) rather than the #0A1613 the logo files use, which
the brand book itself flags as a patch that mismatches the site's dark
sections.

Three variants come out of this module:
  tile()   rounded square - browser tab, .ico 32/48, Android icons
  small()  the same tile with the mark pushed out to 94% - the 16px .ico frame
           only. Marcellus is a high-contrast serif: at 80% the A's crossbar
           and the I's stem land on sub-pixel widths and grey out. Giving the
           glyphs the extra pixels is the difference between a mark and a smudge.
  square() full bleed, extra padding - apple-touch-icon, which iOS masks and
           rounds itself, so a pre-rounded tile would lose its corners.
"""

# Geometry of the mark, lifted unchanged from brand/logo/icon-transparent.svg.
GLYPHS = (
    "M1135.00,-0.00L1135.00,-4.00Q1137.00,-9.00 1138.00,-19.00Q1139.00,-29.00 1139.00,-37.00"
    "Q1139.00,-68.00 1130.50,-105.50Q1122.00,-143.00 1098.00,-199.00L977.00,-471.00"
    "Q921.00,-473.00 828.00,-473.00Q735.00,-473.00 627.00,-473.00Q548.00,-473.00 474.50,-473.00"
    "Q401.00,-473.00 342.00,-471.00L227.00,-207.00Q212.00,-170.00 195.00,-126.00"
    "Q178.00,-82.00 178.00,-37.00Q178.00,-24.00 180.00,-15.50Q182.00,-7.00 184.00,-4.00"
    "L184.00,-0.00L-20.00,-0.00L-20.00,-4.00Q-2.00,-23.00 25.00,-71.50Q52.00,-120.00 84.00,-193.00"
    "L657.00,-1464.00L737.00,-1464.00L1280.00,-242.00Q1299.00,-199.00 1319.50,-158.50"
    "Q1340.00,-118.00 1358.00,-86.00Q1376.00,-54.00 1390.00,-32.00Q1404.00,-10.00 1409.00,-4.00"
    "L1409.00,-0.00Z M487.00,-559.00Q545.00,-559.00 606.00,-559.50Q667.00,-560.00 725.50,-560.50"
    "Q784.00,-561.00 838.00,-561.50Q892.00,-562.00 936.00,-563.00L655.00,-1198.00L379.00,-559.00Z "
    "M1581.96,-4.00Q1587.96,-25.00 1592.96,-56.00Q1597.96,-87.00 1601.96,-133.00"
    "Q1605.96,-179.00 1607.96,-242.50Q1609.96,-306.00 1609.96,-391.00L1609.96,-1042.00"
    "Q1609.96,-1127.00 1607.96,-1190.50Q1605.96,-1254.00 1601.96,-1300.50Q1597.96,-1347.00 1592.96,-1378.00"
    "Q1587.96,-1409.00 1581.96,-1430.00L1581.96,-1434.00L1820.96,-1434.00L1820.96,-1430.00"
    "Q1814.96,-1409.00 1809.46,-1378.00Q1803.96,-1347.00 1800.46,-1300.50Q1796.96,-1254.00 1794.46,-1190.50"
    "Q1791.96,-1127.00 1791.96,-1042.00L1791.96,-391.00Q1791.96,-306.00 1794.46,-242.50"
    "Q1796.96,-179.00 1800.46,-133.00Q1803.96,-87.00 1809.46,-56.00Q1814.96,-25.00 1820.96,-4.00"
    "L1820.96,-0.00L1581.96,-0.00Z"
)
DOT = dict(cx=1914.85, cy=93.89, r=344.26)

# Ink-to-ink bounding box of glyphs + dot, measured off the path above.
BBOX = dict(x0=-20.0, y0=-1464.0, x1=2259.11, y1=438.15)

GROUND = "#0A3D30"   # --teal-900, the logo's own ink green
MARK   = "#F1EFE8"   # --cream
ACCENT = "#D89234"   # --amber-bright, the accent brand reserves for dark grounds


def _viewbox(fill):
    """Square viewBox centred on the mark, sized so the mark spans `fill` of it."""
    w = BBOX["x1"] - BBOX["x0"]
    side = w / fill
    cx = (BBOX["x0"] + BBOX["x1"]) / 2
    cy = (BBOX["y0"] + BBOX["y1"]) / 2
    return cx - side / 2, cy - side / 2, side


def _svg(fill, radius_ratio):
    x0, y0, side = _viewbox(fill)
    rx = round(side * radius_ratio, 2)
    bg = ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%s" fill="%s"/>'
          % (x0, y0, side, side, rx, GROUND))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
        'viewBox="%.2f %.2f %.2f %.2f">\n'
        '<title>AI Profit Lab</title>\n'
        '%s\n'
        '<path d="%s" fill="%s"/>\n'
        '<circle cx="%s" cy="%s" r="%s" fill="%s"/>\n'
        '</svg>\n'
    ) % (x0, y0, side, side, bg, GLYPHS, MARK, DOT["cx"], DOT["cy"], DOT["r"], ACCENT)


def tile():
    """Rounded tile: the default everywhere except iOS and the 16px .ico frame."""
    return _svg(fill=0.86, radius_ratio=0.17)


def small():
    """The 16px frame of favicon.ico. See the note at the top of the module."""
    return _svg(fill=0.94, radius_ratio=0.14)


def square():
    """Full-bleed square for apple-touch-icon. iOS rounds and can crop the
    outer few percent, so the mark is pulled in to 68% and the corners stay
    square - the OS supplies the shape."""
    return _svg(fill=0.68, radius_ratio=0.0)
