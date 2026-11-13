#!/usr/bin/env python3
"""
Turn a brand discovery brief into a draft brand book for Nahid to check and send.

    python3 tools/brand-discovery/build_brand_book.py ~/Downloads/brand-discovery-acme.md
    python3 tools/brand-discovery/build_brand_book.py --sample        # the fictional sample

INPUT  The .md brief attached to the "Brand discovery" notification email. Since
       2026-11-13 the form appends the raw answers to it as an HTML comment
       (<!-- brand-book-data {...} -->). A .json file holding those answers works too.
       Briefs sent before that date have no data block; this tool says so and stops.

OUTPUT .tmp/brand-books/<business>/          (gitignored: the repo is PUBLIC and a
         brand-book.html                       brand book carries the client's name,
         brand-book.pdf                        email and phone)
         review-notes.md   for Nahid only: what to check before sending

WHAT IT DECIDES, and how. Everything is a fixed rule over the answers, so the same
brief always gives the same book, nothing is sent anywhere, and nothing costs credits:
  - Logo type: each of the six kinds (wordmark, monogram, symbol + name, symbol,
    badge, character) collects points from the client's own picks (+3 each), the
    length of the name, where the brand is seen, the characters they chose, the
    price position, the personality sliders and the languages. The top score is
    the recommendation; every point carries the plain reason shown in the book.
  - Draft logo: the name set in the lettering they picked, in their colours. It is
    typeset, not drawn, and the book says so. A symbol is never invented: where one
    is recommended the draft shows a marked empty space for it.
  - Palette: their chosen colours (a hex code typed in "Anything specific about
    colour?" is kept exactly), nudged for their "warm/cool" and "muted/bright"
    answers, plus a deep shade, a tint, ink and paper derived from the main colour.
  - Fonts: the lettering they picked, mapped to free Google Fonts with an Arabic
    partner.
  - Voice: the three voice sliders and their own five words / never words.
  - Their story, customers and position are quoted in their own words, marked as such.

The fonts are downloaded from Google Fonts once (cached in .tmp/brand-books/_fonts/)
and embedded, so the HTML and the PDF need no network and Arabic is shaped properly.
The PDF is printed by the installed Google Chrome, headless.

The option keys below must match the form. check_against_form() reads
brand-discovery.src.html on every run and stops with a clear message if a key was
added, renamed or removed there.
"""
import argparse
import base64
import colorsys
import datetime
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent                       # "Website SEO"
FORM_SRC = HERE / "brand-discovery.src.html"
SAMPLE = HERE / "sample-brief.json"
OUT_ROOT = ROOT / ".tmp" / "brand-books"
FONT_CACHE = OUT_ROOT / "_fonts"
APL_WORDMARK = ROOT / "public_html" / "assets" / "brand" / "wordmark-primary.svg"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ---------------------------------------------------------------------------
# The form's options (keys must match brand-discovery.src.html)
# ---------------------------------------------------------------------------

COLOURS = {
    "red": ("Red", "#C8372D"), "orange": ("Orange", "#E07B2E"), "yellow": ("Yellow / gold", "#E3B53B"),
    "green": ("Green", "#4F8A3A"), "teal": ("Teal", "#138A80"), "blue": ("Blue", "#2F64C1"),
    "navy": ("Navy", "#1F2D5A"), "purple": ("Purple", "#6C4AB6"), "pink": ("Pink", "#D9668F"),
    "brown": ("Brown", "#7A5233"), "sand": ("Sand", "#D8C3A0"), "black": ("Black", "#1A1A1A"),
    "white": ("White", "#FFFFFF"), "grey": ("Grey", "#9A9A9A"),
}
NEUTRAL = {"sand", "black", "white", "grey"}

# The form's archetype icons (24x24 stroke paths), so the book matches the sheet.
ICONS = {
    "sage": '<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "hero": '<path d="M12 3l7 3v6c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z"/>',
    "caregiver": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "explorer": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    "rebel": '<path d="M13 2L5 13h6l-1 9 8-11h-6z"/>',
    "creator": '<path d="M4 20l4-1 11-11-3-3L5 16z"/><path d="M14 6l3 3"/>',
    "ruler": '<path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z"/>',
    "magician": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 15l.6 1.7 1.7.6-1.7.6-.6 1.7-.6-1.7-1.7-.6 1.7-.6z"/>',
    "lover": '<circle cx="9" cy="12" r="5.5"/><circle cx="15" cy="12" r="5.5"/>',
    "jester": '<circle cx="12" cy="12" r="9"/><path d="M8 14c1 1.6 2.4 2.4 4 2.4s3-.8 4-2.4"/><path d="M9 9.5h.01M15 9.5h.01"/>',
    "everyman": '<path d="M4 11l8-7 8 7"/><path d="M6 10v10h12V10"/><path d="M10 20v-5h4v5"/>',
    "innocent": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
}

# name, description and examples are the form's own words; look / words / behaviour
# are this book's guidance for each character.
ARCHETYPES = {
    "sage": ("The Sage", "Wise and expert. Wins trust with knowledge and evidence.", "Google · BBC",
             "Clean layouts, generous space, clear diagrams, calm colour.",
             "Explain and show evidence. No hype.",
             "Answer questions fully and share what you know."),
    "hero": ("The Hero", "Brave and driven. Proves itself through effort and results.", "Nike · FedEx",
             "Strong shapes, high contrast, a sense of movement.",
             "Direct and active. Short sentences, strong verbs.",
             "Set a standard in public, then meet it."),
    "caregiver": ("The Caregiver", "Warm and protective. Puts the customer's wellbeing first.", "Volvo · Johnson & Johnson",
                  "Soft shapes, warm colour, real people.",
                  "Reassuring, patient and personal.",
                  "Follow up, and make it easy to ask for help."),
    "explorer": ("The Explorer", "Independent and curious. Always looking for something new.", "The North Face · Jeep",
                 "Open spaces, natural textures, sturdy lettering.",
                 "Curious and free, a little adventurous.",
                 "Try new things and take customers along."),
    "rebel": ("The Rebel", "Breaks the rules and challenges how things are done.", "Harley-Davidson · Diesel",
              "High contrast, raw textures, unexpected type.",
              "Blunt and sure of itself.",
              "Say what others won't, and break a rule on purpose."),
    "creator": ("The Creator", "Imaginative and original. Loves making things well.", "LEGO · Adobe",
                "Crafted details, texture, the work visible in the making.",
                "Imaginative, specific, proud of the work.",
                "Show the process, not only the result."),
    "ruler": ("The Ruler", "Confident and premium. Sets the standard others follow.", "Rolex · Mercedes-Benz",
              "Order, symmetry, rich but restrained colour.",
              "Confident and measured. Never chatty.",
              "Keep standards high and promises few."),
    "magician": ("The Magician", "Makes big change feel effortless. Visionary.", "Disney · Dyson",
                 "Light, transformation, a touch of wonder.",
                 "Visionary and inviting.",
                 "Show the before and the after."),
    "lover": ("The Lover", "Sensual and intimate. All about beauty and feeling.", "Chanel · Godiva",
              "Rich colour, texture, close-up detail.",
              "Sensory and warm. Describe how it feels.",
              "Make every touchpoint feel personal."),
    "jester": ("The Jester", "Fun and witty. Doesn't take itself too seriously.", "Old Spice · M&M's",
               "Bright colour, playful shapes, wit in the details.",
               "Funny and light, never mean.",
               "Surprise people now and then."),
    "everyman": ("The Everyday Friend", "Down to earth and honest. Made for everyone.", "IKEA · Toyota",
                 "Honest photos, plain type, friendly colour.",
                 "Plain, down to earth, inclusive.",
                 "No jargon and no airs. Treat everyone the same."),
    "innocent": ("The Innocent", "Simple, optimistic and pure. Feels good to be around.", "Dove · Innocent Drinks",
                 "Light grounds, clean shapes, simple illustration.",
                 "Optimistic, simple, honest.",
                 "Keep things easy, and keep your word."),
}

LOGO_TYPES = {
    "wordmark": ("Wordmark", "Your name, lettered with care. No separate symbol."),
    "lettermark": ("Monogram", "Your initials, set as a compact mark."),
    "combination": ("Symbol + name", "A symbol beside your name. The symbol can later stand alone."),
    "symbol": ("Symbol only", "A mark that works without any words."),
    "emblem": ("Badge", "Your name set inside a seal or badge."),
    "mascot": ("Character", "A friendly character that stands for the brand."),
    "open": ("No preference", ""),
}
TIE_ORDER = ["wordmark", "combination", "lettermark", "emblem", "symbol", "mascot"]

# Each picked lettering -> a full type system of free Google Fonts.
# (family, weight). "ar_logo" is the Arabic lettering for an Arabic version of the name.
TYPEFACES = {
    "serif":   dict(label="Classic serif", feel="elegant and established",
                    logo=("Cormorant Garamond", 600), head=("Cormorant Garamond", 600), body=("Source Sans 3", 400),
                    ar_head=("Amiri", 700), ar_body=("Noto Naskh Arabic", 400)),
    "sans":    dict(label="Clean sans", feel="modern and direct",
                    logo=("Archivo", 600), head=("Archivo", 600), body=("Archivo", 400),
                    ar_head=("Noto Kufi Arabic", 600), ar_body=("Noto Sans Arabic", 400)),
    "slab":    dict(label="Sturdy slab", feel="dependable and honest",
                    logo=("Zilla Slab", 600), head=("Zilla Slab", 600), body=("Source Sans 3", 400),
                    ar_head=("Noto Kufi Arabic", 600), ar_body=("Noto Sans Arabic", 400)),
    "script":  dict(label="Handwritten script", feel="personal and crafted",
                    logo=("Italianno", 400), head=("Cormorant Garamond", 600), body=("Source Sans 3", 400),
                    ar_head=("Aref Ruqaa", 700), ar_body=("Noto Naskh Arabic", 400)),
    "display": dict(label="Bold display", feel="loud and expressive",
                    logo=("Abril Fatface", 400), head=("Abril Fatface", 400), body=("Work Sans", 400),
                    ar_head=("Lalezar", 400), ar_body=("Noto Sans Arabic", 400)),
    "kufi":    dict(label="Arabic: geometric Kufi", feel="structured, modern Arabic",
                    ar_logo=("Reem Kufi", 600), ar_head=("Reem Kufi", 600), ar_body=("Noto Sans Arabic", 400)),
    "ruqaa":   dict(label="Arabic: calligraphic", feel="traditional, warm Arabic",
                    ar_logo=("Aref Ruqaa", 700), ar_head=("Aref Ruqaa", 700), ar_body=("Noto Naskh Arabic", 400)),
    "open":    dict(label="No idea yet"),
}
LATIN_TF = ["serif", "sans", "slab", "script", "display"]
ARABIC_TF = ["kufi", "ruqaa"]
# An Arabic-only pick still needs a Latin partner.
LATIN_FOR_ARABIC = {"kufi": "sans", "ruqaa": "serif"}
MONO = ("IBM Plex Mono", 500)

# this-or-that: (a, b, what a means for design, what b means)
PAIRS = {
    "temp": ("Warm", "Cool", "Warm colours lead: earth, sun and spice. Photos in warm light.",
             "Cool colours lead: sea, sky and stone. Crisp daylight photos."),
    "shape": ("Geometric", "Organic", "Clean lines, circles and squares. Shapes drawn on a grid.",
              "Soft curves and hand-drawn shapes. Nothing too rigid."),
    "density": ("Airy & minimal", "Rich & detailed", "Plenty of empty space. One message per layout.",
                "Patterns, frames and layered detail. Decoration is part of the brand."),
    "sat": ("Soft & muted", "Bright & bold", "Soft, dusty colour. Bright colour only as a small accent.",
            "Full-strength colour and confident contrast."),
    "finish": ("Flat & clean", "Textured & crafted", "Flat colour and clean edges. No textures.",
               "Paper grain, print texture, signs of the hand."),
    "mood": ("Light & open", "Dark & moody", "Light backgrounds, open and airy.",
             "Dark backgrounds, rich colour, dramatic light."),
}
PERSONALITY = [("era", "Classic", "Modern"), ("mood", "Serious", "Playful"), ("reach", "Exclusive", "Accessible"),
               ("volume", "Quiet", "Bold"), ("gender", "Feminine", "Masculine"), ("detail", "Simple", "Ornate"),
               ("scale", "Corporate", "Personal")]
VOICE = [("formality", "Formal", "Casual"), ("expertise", "Expert & technical", "Plain-spoken"),
         ("energy", "Calm & reserved", "Enthusiastic")]

# voice slider -> (principle, do, don't) for each end and the middle.
# The example sentences are illustrations of tone and say so in the book.
VOICE_GUIDE = {
    "formality": {
        "a": ("Courteous and complete. Full sentences, no slang, titles where people expect them.",
              "Thank you for your order. It will be with you on Sunday morning.",
              "Hey! Your stuff's on the way!!"),
        "b": ("Friendly and relaxed, like a good neighbour. Contractions and first names are fine.",
              "Thanks! Your order's on its way and arrives Sunday morning.",
              "We hereby confirm that your order has been dispatched."),
        "m": ("Polite but warm: never stiff, never chatty.",
              "Thanks for your order. It arrives on Sunday morning.",
              "We hereby confirm dispatch of your order."),
    },
    "expertise": {
        "a": ("Show what you know. Use the right terms, and explain each one the first time.",
              "We check every order against your specification before it leaves.",
              "Our stuff is just really good quality."),
        "b": ("Say it simply. If a customer would have to look a word up, use another word.",
              "We check every order before it leaves.",
              "We operate end-to-end quality assurance protocols."),
        "m": ("Clear first, detailed when someone asks for more.",
              "Every order is checked before it leaves. Ask us how.",
              "Quality assured through robust multi-stage protocols."),
    },
    "energy": {
        "a": ("Let the facts speak. Few exclamation marks, no capitals for emphasis.",
              "New this week: three more colours.",
              "AMAZING NEWS!!! You NEED these!!!"),
        "b": ("Show that you care. Energy is welcome; hype is not.",
              "New this week, and we love them: three more colours!",
              "Additional colour options are now available."),
        "m": ("Warm, with the energy saved for things that deserve it.",
              "Three new colours this week. Come and see them.",
              "OMG new colours!!!"),
    },
}

CHANNELS = {
    "instagram": ("Instagram", "Profile picture: the monogram on the main colour. Posts: one idea per post."),
    "tiktok": ("TikTok", "Profile picture: the monogram. Keep text clear of the top and bottom of the video."),
    "linkedin": ("LinkedIn", "The full logo on the banner. Posts follow the colour and font rules."),
    "whatsapp": ("WhatsApp", "Business profile picture: the monogram. Catalogue photos on a plain background."),
    "website": ("Website", "Full logo top left (top right on Arabic pages). Browser icon from the monogram."),
    "print": ("Print", "Full logo in Deep or Ink. Check colours on a printed proof before a big run."),
    "packaging": ("Packaging", "The badge or full logo on the front. Give the printer the colour codes in this book."),
    "store": ("Storefront & signage", "Full logo, large, on the fascia. Check it reads from across the street."),
    "vehicles": ("Vehicles", "Full logo large on both sides; the monogram on the back."),
    "events": ("Events & exhibitions", "Full logo on banners, one block of colour per surface."),
    "uniforms": ("Uniforms", "The monogram or a one-colour logo, embroidered. Keep fine detail out."),
}
SMALL_SPACES = {"instagram", "tiktok", "whatsapp", "linkedin"}
FAR_AWAY = {"store", "vehicles", "uniforms", "events"}

PRICE = {"budget": "Budget", "mid": "Mid-market", "premium": "Premium", "luxury": "Luxury"}
PROJECT = {"new": "A brand new brand", "refresh": "A refresh", "rebrand": "A full rebrand"}


def check_against_form():
    """Stop if the form's option keys and this file's tables have drifted apart."""
    src = FORM_SRC.read_text(encoding="utf-8")
    tables = {"COLOURS": COLOURS, "ARCHETYPES": ARCHETYPES, "LOGO_TYPES": LOGO_TYPES, "TYPEFACES": TYPEFACES,
              "PAIRS": PAIRS, "PERSONALITY": {k: 1 for k, _, _ in PERSONALITY},
              "VOICE": {k: 1 for k, _, _ in VOICE}, "CHANNELS": CHANNELS}
    problems = []
    for name, ours in tables.items():
        m = re.search(r"const %s = \[(.*?)\n\]" % name, src, re.S)
        if not m:
            problems.append(f"{name}: not found in the form source")
            continue
        block = m.group(1)
        keys = re.findall(r'\["(\w+)",L\(', block) if name == "CHANNELS" else re.findall(r'\{\s*v:"(\w+)"', block)
        theirs, mine = set(keys), set(ours)
        if theirs != mine:
            problems.append(f"{name}: form has {sorted(theirs - mine)} that this tool lacks, "
                            f"this tool has {sorted(mine - theirs)} that the form lacks")
    if problems:
        sys.exit("The form and build_brand_book.py disagree about option keys:\n  " + "\n  ".join(problems)
                 + "\nUpdate the tables at the top of build_brand_book.py to match brand-discovery.src.html.")


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

def load_brief(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        data = data if "answers" in data else {"answers": data}
    else:
        start = text.rfind("<!-- brand-book-data")
        if start < 0:
            sys.exit(f"{path.name} has no brand-book-data block. Briefs sent before 2026-11-13 don't carry "
                     "one: make a .json of the answers from the Sheet row instead, keyed as in the form.")
        end = text.find("\n-->", start)
        data = json.loads(text[text.index("\n", start) + 1:end])
    data["answers"] = {k: v for k, v in data["answers"].items() if not k.startswith("_")}
    return data


# ---------------------------------------------------------------------------
# Colour maths
# ---------------------------------------------------------------------------

def rgb(hx):
    hx = hx.lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    return tuple(int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_hex(r, g, b):
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02X}" for c in (r, g, b))


def hls(hx):
    return colorsys.rgb_to_hls(*rgb(hx))


def from_hls(h, l, s):
    return to_hex(*colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s))))


def luminance(hx):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb(hx))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def cmyk(hx):
    r, g, b = rgb(hx)
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    return tuple(round(x * 100) for x in ((1 - r - k) / (1 - k), (1 - g - k) / (1 - k), (1 - b - k) / (1 - k), k))


def toward(h, target, step):
    d = (target - h + 0.5) % 1 - 0.5
    return h + max(-step, min(step, d))


def tune(hx, tt):
    """Nudge a picked colour for the client's 'muted/bright' and 'warm/cool' answers."""
    h, l, s = hls(hx)
    if tt.get("sat") == "a":
        s *= 0.72
        l += (0.5 - l) * 0.15
    elif tt.get("sat") == "b":
        s = min(1, s * 1.12)
    if tt.get("temp") == "a":
        h = toward(h, 35 / 360, 6 / 360)
    elif tt.get("temp") == "b":
        h = toward(h, 210 / 360, 6 / 360)
    return from_hls(h, l, s)


# ---------------------------------------------------------------------------
# Deriving the brand
# ---------------------------------------------------------------------------

def txt(a, k):
    v = a.get(k)
    if isinstance(v, dict):
        v = v.get("links", "")
    return str(v or "").strip()


def lst(a, k):
    v = a.get(k)
    return [x for x in v if x] if isinstance(v, list) else []


def slider(a, group, k):
    v = (a.get(group) or {}).get(k)
    return 50 if v is None else int(v)


def side(n):
    return "a" if n < 40 else "b" if n > 60 else "m"


ARABIC_RUN = re.compile(r"[؀-ۿ][؀-ۿ\s]*[؀-ۿ]|[؀-ۿ]")
STOP = {"llc", "spc", "saog", "saoc", "co", "co.", "company", "the", "and", "&", "of", "for", "al", "el", "ltd", "est"}


def names(a):
    """(latin name, arabic name, where the arabic came from, initials)."""
    business = txt(a, "business")
    notes = txt(a, "nameNotes")
    if ARABIC_RUN.search(business) and not re.search(r"[A-Za-z]{2}", business):
        ar, latin, src = business, "", "name"
        m = re.findall(r"[A-Za-z][A-Za-z&'.\- ]{2,}", notes)
        latin = max(m, key=len).strip() if m else ""
    else:
        latin = business
        runs = ARABIC_RUN.findall(notes)
        ar = max(runs, key=len).strip() if runs else ""
        src = "notes" if ar else ""
    words = [w for w in re.split(r"[\s\-]+", latin) if w and w.lower().strip(".") not in STOP]
    if not words and latin:
        words = latin.split()
    initials = "".join(w[0] for w in words[:3]).upper() if latin else (ar[:1] if ar else "")
    return latin, ar, src, initials


def derive_palette(a):
    tt = a.get("thisThat") or {}
    avoid = set(lst(a, "colorsAvoid"))
    loved = [c for c in lst(a, "colorsLove") if c in COLOURS and c not in avoid]
    kept = re.findall(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", txt(a, "colorNotes"))
    base, notes = [], []
    for hx in kept:
        base.append(("Your colour", "#" + rgb_hex_norm(hx), True))
    if kept:
        notes.append("The hex code you gave us is kept exactly.")
    for c in loved:
        if c not in NEUTRAL:
            base.append((COLOURS[c][0], tune(COLOURS[c][1], tt), False))
    suggested = False
    if not base:
        lead = (lst(a, "archetypes") or ["everyman"])[0]
        fallback = {"sage": "navy", "hero": "red", "caregiver": "teal", "explorer": "green", "rebel": "red",
                    "creator": "orange", "ruler": "navy", "magician": "purple", "lover": "red", "jester": "yellow",
                    "everyman": "blue", "innocent": "teal"}.get(lead, "blue")
        base.append((COLOURS[fallback][0], tune(COLOURS[fallback][1], tt), False))
        suggested = True
        notes.append(f"You didn't choose colours, so the main colour is suggested from your character "
                     f"({ARCHETYPES.get(lead, ARCHETYPES['everyman'])[0]}).")
    adj = []
    if tt.get("sat") == "a":
        adj.append("softened for “soft & muted”")
    elif tt.get("sat") == "b":
        adj.append("strengthened for “bright & bold”")
    if tt.get("temp") in ("a", "b"):
        adj.append("warmed slightly" if tt["temp"] == "a" else "cooled slightly")
    if adj and any(not k for _, _, k in base):
        notes.append("Your chosen colours were " + " and ".join(adj) + ".")

    pname, primary, _ = base[0]
    h, l, s = hls(primary)
    deep = from_hls(h, 0.2, min(s, 0.55))
    tint = from_hls(h, 0.93, s * 0.4)
    ink = "#1A1A1A" if "black" in loved else from_hls(h, 0.12, min(0.25, s * 0.4))
    if "white" in loved and tt.get("mood") != "b":
        paper = "#FFFFFF"
    elif "sand" in loved:
        sh, _, ss = hls(COLOURS["sand"][1])
        paper = from_hls(sh, 0.945, ss * 0.85)
    elif tt.get("temp") == "a":
        paper = from_hls(40 / 360, 0.96, 0.32)
    elif tt.get("temp") == "b":
        paper = from_hls(210 / 360, 0.97, 0.2)
    else:
        paper = from_hls(h, 0.965, 0.15)

    main = [("Primary", pname, primary)]
    roles = ["Secondary", "Accent"]
    for (nm, hx, _), role in zip(base[1:3], roles):
        main.append((role, nm, hx))
    main.append(("Deep", "for text and dark grounds", deep))
    neutrals = [("Paper", "backgrounds", paper), ("Tint", "light panels", tint), ("Ink", "body text", ink)]
    if "sand" in loved:
        neutrals.insert(1, ("Sand", "warm neutral", tune(COLOURS["sand"][1], {})))
    if "grey" in loved:
        neutrals.append(("Stone", "lines and quiet text", COLOURS["grey"][1]))
    mid = from_hls(h, 0.45, min(s, 0.12))
    avoided = [(COLOURS[c][0], COLOURS[c][1]) for c in lst(a, "colorsAvoid") if c in COLOURS]
    ratio = [("Paper", paper, 60), ("Primary", primary, 25 if len(main) > 2 else 30)]
    if len(main) > 2:
        ratio.append((main[1][0], main[1][2], 10))
        ratio.append(("Accent" if len(main) > 3 else "Deep", main[2][2] if len(main) > 3 else deep, 5))
    else:
        ratio.append(("Deep", deep, 10))
    dark_ground = tt.get("mood") == "b"
    return dict(primary=primary, deep=deep, tint=tint, ink=ink, paper=paper, mid=mid,
                second=main[1][2] if len(main) > 2 else deep, main=main, neutrals=neutrals,
                avoided=avoided, ratio=ratio, notes=notes, suggested=suggested, dark=dark_ground)


def rgb_hex_norm(hx):
    hx = hx.lstrip("#")
    return ("".join(c * 2 for c in hx) if len(hx) == 3 else hx).upper()


def derive_type(a):
    picks = [p for p in lst(a, "typeface") if p in TYPEFACES and p != "open"]
    note = ""
    latin = next((p for p in picks if p in LATIN_TF), None)
    arabic = next((p for p in picks if p in ARABIC_TF), None)
    if not latin:
        if arabic:
            latin = LATIN_FOR_ARABIC[arabic]
        else:
            era, detail = slider(a, "personality", "era"), slider(a, "personality", "detail")
            lead = (lst(a, "archetypes") or [""])[0]
            if detail > 65:
                latin = "display"
            elif era < 45:
                latin = "serif"
            elif era > 55:
                latin = "sans"
            else:
                latin = {"ruler": "serif", "sage": "serif", "lover": "serif", "hero": "slab", "rebel": "slab",
                         "explorer": "slab", "jester": "display", "creator": "display"}.get(lead, "sans")
            note = "You didn't pick a lettering, so this one is suggested from your personality answers."
    L = TYPEFACES[latin]
    t = dict(latin_key=latin, arabic_key=arabic, label=L["label"], feel=L["feel"],
             logo=L["logo"], head=L["head"], body=L["body"],
             ar_head=TYPEFACES[arabic]["ar_head"] if arabic else L["ar_head"],
             ar_body=TYPEFACES[arabic]["ar_body"] if arabic else L["ar_body"],
             ar_logo=TYPEFACES[arabic]["ar_logo"] if arabic else L["ar_head"],
             also=[TYPEFACES[p]["label"] for p in picks if p not in (latin, arabic)],
             note=note, script=latin == "script")
    # A script face is for the logo only: unreadable small, so the monogram uses the heading face.
    t["mono_font"] = t["head"] if t["script"] else t["logo"]
    return t


def derive_logo(a, latin_name):
    """Score each logo type. Returns (ranked [(key, score)], reasons {key: [text]}, flags)."""
    score = {k: 0 for k in TIE_ORDER}
    why = {k: [] for k in TIE_ORDER}

    def add(k, n, reason=None):
        score[k] += n
        if reason and n > 0:
            why[k].append(reason)

    for k in lst(a, "logoType"):
        if k in score:
            add(k, 3, "You picked it yourself in the questionnaire.")
    letters = len(re.sub(r"[^A-Za-z؀-ۿ]", "", latin_name))
    words = len(latin_name.split())
    nm = latin_name or "your name"
    if not letters:
        pass                      # no Latin name (Arabic only): length says nothing here
    elif letters <= 10:
        add("wordmark", 2, f"“{nm}” is short ({letters} letters), so the name can carry the logo on its own.")
    elif letters <= 16 and words < 3:
        add("wordmark", 1, f"“{nm}” is a comfortable length for lettering.")
        add("combination", 1, f"At {letters} letters, a small symbol can stand in for the name where space is tight.")
    else:
        add("lettermark", 2, f"“{nm}” is long, so a short monogram helps wherever space is tight.")
        add("wordmark", -1)
    ch = set(lst(a, "channels"))
    small = sorted(ch & SMALL_SPACES)
    if small:
        add("lettermark", 1, "Profile pictures on " + ", ".join(CHANNELS[c][0] for c in small)
            + " are small circles, where a monogram reads better than a full name.")
    far = sorted(ch & FAR_AWAY)
    if far:
        msg = ("Your brand is seen from a distance (" + ", ".join(CHANNELS[c][0].lower() for c in far)
               + "), where a bold, simple shape helps.")
        add("emblem", 1, msg)
        add("combination", 1, msg)
    if "packaging" in ch:
        add("emblem", 1, "On packaging a badge works as a seal or a sticker.")
    arch_types = {"sage": ("wordmark", "lettermark"), "hero": ("combination", "symbol"),
                  "caregiver": ("combination", "wordmark"), "explorer": ("emblem", "combination"),
                  "rebel": ("symbol", "emblem"), "creator": ("combination", "symbol"),
                  "ruler": ("wordmark", "emblem"), "magician": ("symbol", "combination"),
                  "lover": ("wordmark", "lettermark"), "jester": ("mascot", "combination"),
                  "everyman": ("combination", "wordmark"), "innocent": ("combination", "mascot")}
    for k in lst(a, "archetypes"):
        for t in arch_types.get(k, ()):
            add(t, 1, f"It suits {ARCHETYPES[k][0]}, one of the characters you chose.")
    price = a.get("price")
    if price == "luxury":
        add("wordmark", 2, "Luxury brands usually let refined lettering speak alone.")
        add("lettermark", 1, "Luxury brands often use a monogram.")
        add("mascot", -2)
    elif price == "premium":
        add("wordmark", 1, "At a premium price, refined lettering says more than a busy symbol.")
    elif price == "budget":
        add("combination", 1, "At a value price, a friendly mark that's easy to spot helps.")
        add("mascot", 1, "At a value price, a friendly character can help people remember you.")
    era, detail, mood = (slider(a, "personality", k) for k in ("era", "detail", "mood"))
    if era < 35:
        add("emblem", 1, "You lean classic, and a badge feels established.")
    elif era > 65:
        add("lettermark", 1, "You lean modern, and a clean monogram suits that.")
        add("symbol", 1, "You lean modern, and a clean symbol suits that.")
    if detail < 35:
        add("wordmark", 1, "You prefer simple, and lettering alone is the simplest logo there is.")
    elif detail > 65:
        add("emblem", 1, "You like detail, and a badge has room for it.")
    if mood > 65:
        add("mascot", 1, "You lean playful, and a character can carry that.")
    elif mood < 35:
        add("mascot", -1)
    langs = set(lst(a, "languages"))
    if {"en", "ar"} <= langs:
        add("combination", 1, "Your brand works in English and Arabic. A symbol stays the same in both while the name changes script.")
    ranked = sorted(TIE_ORDER, key=lambda k: (-score[k], TIE_ORDER.index(k)))
    primary = ranked[0] if score[ranked[0]] > 0 else "wordmark"
    if primary != ranked[0]:
        ranked.remove(primary)
        ranked.insert(0, primary)
    if primary in ("wordmark", "emblem", "mascot"):
        compact = "lettermark"
    elif primary in ("combination", "symbol"):
        compact = "symbol"
    else:
        compact = "wordmark"
    badge = primary != "emblem" and score["emblem"] >= 4 and bool(ch & {"packaging", "store"} or "emblem" in lst(a, "logoType"))
    return dict(primary=primary, compact=compact, badge=badge or primary == "emblem",
                ranked=[(k, score[k]) for k in ranked], why=why,
                needs_symbol=primary in ("combination", "symbol") , needs_character=primary == "mascot")


# ---------------------------------------------------------------------------
# Fonts: fetched once from Google Fonts, embedded as base64
# ---------------------------------------------------------------------------

ARABIC_FAMILIES = {"Amiri", "Noto Naskh Arabic", "Noto Kufi Arabic", "Noto Sans Arabic", "Reem Kufi", "Aref Ruqaa", "Lalezar"}


def curl(url, binary=False):
    r = subprocess.run(["curl", "-sSfL", "--max-time", "60", "-A", UA, url], capture_output=True)
    if r.returncode:
        raise RuntimeError(f"curl failed ({r.returncode}) for {url}: {r.stderr.decode()[:200]}")
    return r.stdout if binary else r.stdout.decode("utf-8")


def font_css(families):
    """@font-face rules for {family: {weights}}, with the woff2 files inlined."""
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    out = []
    for fam, weights in sorted(families.items()):
        keep = {"arabic"} if fam in ARABIC_FAMILIES else {"latin", "latin-ext"}
        q = fam.replace(" ", "+") + ("" if weights == {400} else ":wght@" + ";".join(str(w) for w in sorted(weights)))
        cache = FONT_CACHE / (hashlib.sha1(q.encode()).hexdigest()[:16] + ".css")
        if not cache.exists():
            cache.write_text(curl(f"https://fonts.googleapis.com/css2?family={q}&display=block"), encoding="utf-8")
        css = cache.read_text(encoding="utf-8")
        for subset, rule in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*\{.*?\})", css, re.S):
            if subset not in keep:
                continue
            url = re.search(r"url\((https://[^)]+)\)", rule).group(1)
            f = FONT_CACHE / (hashlib.sha1(url.encode()).hexdigest()[:20] + ".woff2")
            if not f.exists():
                f.write_bytes(curl(url, binary=True))
            data = base64.b64encode(f.read_bytes()).decode("ascii")
            out.append(rule.replace(url, "data:font/woff2;base64," + data))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def e(s):
    return html.escape(str(s or ""), quote=True)


def paras(s, cls=""):
    s = str(s or "").strip()
    if not s:
        return ""
    c = f' class="{cls}"' if cls else ""
    return "".join(f'<p{c} dir="auto">' + "<br>".join(e(x) for x in p.split("\n")) + "</p>"
                   for p in re.split(r"\n\s*\n", s))


def fam(*fonts, generic="serif"):
    """A font stack: the Latin face first, then the Arabic one, then ONE generic at the
    very end. A generic in the middle would catch Arabic letters with a system font
    before the embedded Arabic face got a chance."""
    names = list(dict.fromkeys(f[0] for f in fonts))
    return ", ".join(f"'{n}'" for n in names) + f", {generic}"


def is_ar(s):
    return bool(ARABIC_RUN.search(s or "")) and not re.search(r"[A-Za-z]{2}", s or "")


def wordmark(name, cls="", style=""):
    if is_ar(name):
        cls += " ar"
    return f'<div class="wm fit {cls}" dir="auto" style="{style}">{e(name)}</div>'


def monogram_svg(initials, fill, ink, font, size=120, ring=None):
    n = max(1, len(initials))
    fs = {1: 58, 2: 46, 3: 36}.get(n, 32)
    ring_el = f'<circle cx="60" cy="60" r="52" fill="none" stroke="{ring}" stroke-width="1.5"/>' if ring else ""
    return (f'<svg class="mono-svg" viewBox="0 0 120 120" width="{size}" height="{size}" role="img" aria-label="{e(initials)} monogram">'
            f'<circle cx="60" cy="60" r="60" fill="{fill}"/>{ring_el}'
            f'<text x="60" y="61" text-anchor="middle" dominant-baseline="central" font-family="{e(font[0])}" '
            f'font-weight="{font[1]}" font-size="{fs}" fill="{ink}" letter-spacing="1">{e(initials)}</text></svg>')


def badge_svg(name, initials, fill, ink, font, size=150, uid="b"):
    label = name.upper()
    arc = 3.1416 * 2 * 46 * 0.62
    fs = max(7, min(13, arc / max(1, len(label)) / 0.62))
    return (f'<svg viewBox="0 0 140 140" width="{size}" height="{size}" role="img" aria-label="{e(name)} badge">'
            f'<defs><path id="arc-{uid}" d="M 24 70 A 46 46 0 0 1 116 70"/></defs>'
            f'<circle cx="70" cy="70" r="69" fill="{fill}"/>'
            f'<circle cx="70" cy="70" r="62" fill="none" stroke="{ink}" stroke-width="1"/>'
            f'<circle cx="70" cy="70" r="33" fill="none" stroke="{ink}" stroke-width="1"/>'
            f'<text font-family="{e(font[0])}" font-weight="{font[1]}" font-size="{fs:.1f}" fill="{ink}" letter-spacing="1.5">'
            f'<textPath href="#arc-{uid}" startOffset="50%" text-anchor="middle">{e(label)}</textPath></text>'
            f'<text x="70" y="71" text-anchor="middle" dominant-baseline="central" font-family="{e(font[0])}" '
            f'font-weight="{font[1]}" font-size="{26 if len(initials) < 3 else 20}" fill="{ink}">{e(initials)}</text>'
            f'<g fill="{ink}"><circle cx="46" cy="108" r="1.6"/><circle cx="70" cy="113" r="1.6"/><circle cx="94" cy="108" r="1.6"/></g></svg>')


def page(content, cls="", num=None, title="", foot=None, style=""):
    head = (f'<div class="ph"><span class="ast">✼</span><span>{num:02d} · {e(title)}</span></div>'
            if num is not None else "")
    return f'<section class="page {cls}" style="{style}">{head}{content}{foot or ""}</section>'


CSS = r"""
@page { size: 297mm 210mm; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { background: #CFCBC2; font-family: var(--f-body); color: var(--ink); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
@media screen { .page { margin: 10mm auto; box-shadow: 0 6px 30px rgba(0,0,0,.18); } }
.page { width: 297mm; height: 210mm; position: relative; overflow: hidden; background: var(--paper); padding: 22mm 22mm 20mm; break-after: page; page-break-after: always; font-size: 10.5pt; line-height: 1.55; display: flex; flex-direction: column; justify-content: center; }
.page > * { flex: none; }
.ph { position: absolute; top: 10mm; left: 22mm; right: 22mm; display: flex; gap: 2.2mm; align-items: center; font: 500 7pt/1 var(--f-mono); letter-spacing: .16em; text-transform: uppercase; color: var(--muted); }
.ph .ast, .ast { color: var(--primary); }
.nm { font-family: var(--f-body); letter-spacing: 0; text-transform: none; font-size: 7.4pt; }
.pf { position: absolute; left: 22mm; right: 22mm; bottom: 9mm; display: flex; justify-content: space-between; font: 400 6.6pt/1 var(--f-mono); letter-spacing: .08em; color: var(--muted); text-transform: uppercase; }
h1, h2, h3 { font-family: var(--f-head); font-weight: var(--w-head); color: var(--deep); margin: 0; line-height: 1.08; letter-spacing: -.005em; text-wrap: balance; }
h1 { font-size: 34pt; }
h2 { font-size: 24pt; margin-bottom: 4mm; }
h3 { font-size: 13pt; margin-bottom: 1.6mm; }
p { margin: 0 0 2.4mm; }
.k { font: 500 6.8pt/1.3 var(--f-mono); letter-spacing: .14em; text-transform: uppercase; color: var(--muted); margin-bottom: 1.8mm; }
.lede { font-size: 12pt; color: var(--muted); max-width: 120mm; }
.yours { display: inline-block; font: 500 6.2pt/1 var(--f-mono); letter-spacing: .14em; text-transform: uppercase; color: var(--primary-text); border: .25mm solid currentColor; border-radius: 9mm; padding: 1.2mm 2.4mm; margin-bottom: 3mm; }
.grid2 { display: grid; grid-template-columns: 88mm 1fr; gap: 14mm; }
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 9mm; }
.col { min-width: 0; }
.rule { height: .3mm; background: var(--line); margin: 5mm 0; }
.statement { font-family: var(--f-head); font-weight: var(--w-head); font-size: 21pt; line-height: 1.2; color: var(--deep); text-wrap: balance; }
.quote { font-family: var(--f-head); font-weight: var(--w-head); font-size: 15pt; line-height: 1.3; color: var(--deep); }
.small { font-size: 8.6pt; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: 2mm; }
.chip { border: .3mm solid var(--line); background: var(--panel); border-radius: 9mm; padding: 1.4mm 3.4mm; font-size: 9.5pt; }
.chip.big { font-family: var(--f-head); font-weight: var(--w-head); font-size: 14pt; padding: 2mm 5mm; color: var(--deep); }
.chip.no { text-decoration: line-through; color: var(--muted); }
.card { background: var(--panel); border: .3mm solid var(--line); border-radius: 4mm; padding: 6mm; }
/* cover */
.cover { background: var(--cover-bg); color: var(--cover-ink); padding: 0; }
.cover .in { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 30mm; text-align: center; }
.cover .wm { color: var(--cover-ink); font-size: 64pt; width: 100%; }
.cover .t { font: 500 8pt/1 var(--f-mono); letter-spacing: .3em; text-transform: uppercase; margin-top: 10mm; opacity: .85; }
.cover .line { margin-top: 5mm; font-size: 11pt; opacity: .8; max-width: 160mm; }
.cover .pf { color: var(--cover-ink); opacity: .7; }
.wm { font-family: var(--f-logo); font-weight: var(--w-logo); color: var(--wm); white-space: nowrap; line-height: 1.15; text-align: center; overflow: visible; }
.wm.ar { font-family: var(--f-ar-logo); font-weight: var(--w-ar-logo); }
.mono-svg text { font-feature-settings: "lnum"; }
/* contents */
.toc { list-style: none; padding: 0; margin: 0; columns: 2; column-gap: 12mm; }
.toc li { display: flex; gap: 4mm; padding: 2.3mm 0; border-bottom: .3mm solid var(--line); break-inside: avoid; font-size: 10.5pt; }
.toc .n { font: 500 8pt/1.9 var(--f-mono); color: var(--primary-text); width: 7mm; }
/* values */
.vals { list-style: none; margin: 0; padding: 0; }
.vals li { padding: 3mm 0; border-bottom: .3mm solid var(--line); display: grid; grid-template-columns: 9mm 1fr; }
.vals .n { font: 500 8pt/1.9 var(--f-mono); color: var(--primary-text); }
.vals b { font-family: var(--f-head); font-weight: var(--w-head); font-size: 13pt; color: var(--deep); display: block; }
/* price scale */
.scale4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5mm; margin-top: 2mm; }
.scale4 span { border-top: 1.2mm solid var(--line); padding-top: 2mm; font-size: 8.6pt; color: var(--muted); }
.scale4 span.on { border-color: var(--primary); color: var(--deep); font-weight: 600; }
/* archetypes */
.arch { display: grid; grid-template-columns: 16mm 1fr; gap: 5mm; }
.arch svg { width: 16mm; height: 16mm; stroke: var(--primary); fill: none; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; }
.arch.sub svg { width: 11mm; height: 11mm; }
.arch dl { display: grid; grid-template-columns: 22mm 1fr; gap: 1.6mm 4mm; margin: 3mm 0 0; font-size: 9.4pt; }
.arch dt { font: 500 6.6pt/1.9 var(--f-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.arch dd { margin: 0; }
/* sliders */
.sl { display: grid; grid-template-columns: 30mm 1fr 30mm; gap: 3mm; align-items: center; padding: 2.1mm 0; font-size: 9.4pt; }
.sl span:last-child { text-align: right; }
.sl .on { color: var(--deep); font-weight: 600; }
.sl .bar { height: .4mm; background: var(--line); position: relative; }
.sl .bar i { position: absolute; top: 50%; width: 3.6mm; height: 3.6mm; border-radius: 50%; background: var(--primary); transform: translate(-50%, -50%); }
.vp { padding: 3.2mm 0; border-bottom: .3mm solid var(--line); }
.vp .do, .vp .dont { font-size: 9.2pt; margin: 1.2mm 0 0; padding-left: 6mm; position: relative; }
.vp .do::before, .vp .dont::before { position: absolute; left: 0; font: 600 9pt/1.4 var(--f-mono); }
.vp .do::before { content: "✓"; color: var(--primary-text); }
.vp .dont::before { content: "✕"; color: #A6431F; }
.vp .dont { color: var(--muted); }
/* logo advice */
.rec { font-family: var(--f-head); font-weight: var(--w-head); font-size: 26pt; line-height: 1.1; color: var(--deep); margin-bottom: 3mm; }
.reasons { margin: 0; padding: 0; list-style: none; }
.reasons li { padding: 2mm 0 2mm 6mm; position: relative; border-bottom: .3mm solid var(--line); font-size: 9.8pt; }
.reasons li::before { content: "✼"; position: absolute; left: 0; color: var(--primary); font-size: 8pt; top: 2.4mm; }
.rank { display: grid; grid-template-columns: 30mm 1fr 8mm; gap: 3mm; align-items: center; font-size: 9.2pt; padding: 1.5mm 0; }
.rank .bar { height: 2.6mm; background: var(--line); border-radius: 2mm; overflow: hidden; }
.rank .bar i { display: block; height: 100%; background: var(--primary); border-radius: 2mm; }
.rank.top { font-weight: 600; color: var(--deep); }
.rank .s { font: 500 8pt/1 var(--f-mono); text-align: right; color: var(--muted); }
/* logo boards */
.board { border-radius: 4mm; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; padding: 8mm; }
.board > svg { width: auto; height: 29mm; }
.board .cap { position: absolute; left: 4mm; bottom: 3mm; font: 500 6pt/1 var(--f-mono); letter-spacing: .14em; text-transform: uppercase; opacity: .7; }
.ph-sym { width: 18mm; height: 18mm; border: .5mm dashed currentColor; border-radius: 3mm; display: flex; align-items: center; justify-content: center; font: 500 5.6pt/1.2 var(--f-mono); letter-spacing: .1em; text-transform: uppercase; text-align: center; flex: none; opacity: .75; }
.lockup { display: flex; align-items: center; gap: 6mm; width: 100%; justify-content: center; }
.lockup .wm { width: auto; flex: 0 1 auto; min-width: 0; }
/* usage */
.clear { position: relative; display: inline-block; max-width: 100%; padding: 9mm 11mm; border: .3mm dashed var(--muted); }
.clear .x { position: absolute; font: 600 7pt/1 var(--f-mono); color: var(--primary-text); }
.dont-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 4mm; }
.dont-grid .board { height: 30mm; padding: 3mm; }
.dont-grid .wm { font-size: 15pt; }
.dont-grid p { font-size: 8.4pt; margin-top: 2mm; }
.dont-grid p::before { content: "✕  "; color: #A6431F; font-weight: 600; }
/* colour */
.sw-row { display: grid; gap: 4mm; }
.sw { border-radius: 3.5mm; overflow: hidden; border: .3mm solid var(--line); background: var(--panel); }
.sw .chipc { height: 30mm; display: flex; align-items: flex-end; padding: 3mm; font-family: var(--f-head); font-weight: var(--w-head); font-size: 15pt; }
.sw.small .chipc { height: 16mm; font-size: 11pt; }
.sw .codes { padding: 2.6mm 3mm; font: 400 7.2pt/1.6 var(--f-mono); color: var(--muted); }
.sw .codes b { display: block; font: 600 8.4pt/1.4 var(--f-body); color: var(--ink); }
.ratio { display: flex; height: 7mm; border-radius: 2mm; overflow: hidden; border: .3mm solid var(--line); }
.ratio span { display: block; }
.legend { display: flex; flex-wrap: wrap; gap: 1.5mm 5mm; margin-top: 2mm; font: 400 7pt/1.4 var(--f-mono); color: var(--muted); }
.legend i { display: inline-block; width: 2.6mm; height: 2.6mm; border-radius: 50%; margin-right: 1.4mm; vertical-align: -.3mm; border: .2mm solid var(--line); }
.av { display: inline-flex; align-items: center; gap: 2mm; margin-right: 4mm; font-size: 9pt; }
.av i { width: 7mm; height: 7mm; border-radius: 50%; position: relative; display: inline-block; }
.av i::after { content: ""; position: absolute; left: -1mm; right: -1mm; top: 50%; height: .5mm; background: var(--ink); transform: rotate(-35deg); }
/* type */
.spec { font-family: var(--f-head); font-weight: var(--w-head); font-size: 66pt; line-height: 1; color: var(--deep); }
.spec.ar { font-family: var(--f-ar-head); font-weight: var(--w-ar-head); }
.scale-t { width: 100%; border-collapse: collapse; }
.scale-t td { border-bottom: .3mm solid var(--line); padding: 2mm 0; vertical-align: baseline; }
.scale-t td:first-child { font: 500 6.8pt/1 var(--f-mono); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); width: 22mm; }
.scale-t td:last-child { text-align: right; font: 400 7.4pt/1 var(--f-mono); color: var(--muted); white-space: nowrap; }
.ar-body { font-family: var(--f-ar-body); }
/* look */
.dir { border-top: 1mm solid var(--primary); padding-top: 3mm; }
.dir h3 { font-size: 14pt; }
/* applications */
.mock-ig { width: 78mm; background: #fff; border-radius: 5mm; border: .3mm solid #ddd; padding: 5mm; color: #222; font-family: var(--f-body); font-size: 8pt; }
.mock-ig .top { display: flex; gap: 4mm; align-items: center; margin-bottom: 4mm; }
.mock-ig .tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1mm; }
.mock-ig .tiles div { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; text-align: center; padding: 2mm; overflow: hidden; }
.apps { display: grid; grid-template-columns: 80mm 72mm minmax(0,1fr); gap: 8mm; align-items: start; margin-top: 2mm; }
.cards { display: flex; flex-direction: column; gap: 4mm; }
.card-bc { width: 72mm; height: 42mm; border-radius: 2mm; border: .3mm solid var(--line); display: flex; flex-direction: column; justify-content: center; padding: 6mm; position: relative; overflow: hidden; }
.card-bc .wm { font-size: 18pt; width: 100%; }
.mock-ig { width: 80mm; }
.sign { width: 100%; height: 30mm; border-radius: 2mm; display: flex; align-items: center; justify-content: center; padding: 0 8mm; border-bottom: 2mm solid rgba(0,0,0,.18); }
.sign .wm { width: 100%; }
.k.cap2 { margin-top: 2mm; }
.chan { display: grid; grid-template-columns: 34mm 1fr; gap: 2mm 4mm; font-size: 9pt; padding: 1.8mm 0; border-bottom: .3mm solid var(--line); }
.chan b { font-weight: 600; color: var(--deep); }
/* open points */
.todo { list-style: none; margin: 0; padding: 0; }
.todo li { padding: 3mm 0 3mm 9mm; border-bottom: .3mm solid var(--line); position: relative; }
.todo li::before { content: ""; position: absolute; left: 0; top: 3.6mm; width: 4mm; height: 4mm; border: .4mm solid var(--primary); border-radius: 1mm; }
.todo b { color: var(--deep); }
/* back */
.back { background: #F1EFE8; color: #232B26; }
.back .in { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; gap: 5mm; font-family: 'IBM Plex Mono', monospace; }
.back img { width: 62mm; }
.back p { font-size: 8pt; letter-spacing: .06em; margin: 0; color: #5A665D; }
"""

FIT_JS = """<script>
/* Shrink any .fit wordmark that is wider than its box, once the fonts are in. */
function fitAll(){ document.querySelectorAll('.fit').forEach(function(el){
  var fs = parseFloat(getComputedStyle(el).fontSize), g = 0;
  while (el.scrollWidth > el.clientWidth + 1 && g++ < 80) { fs *= 0.95; el.style.fontSize = fs + 'px'; }
}); document.documentElement.setAttribute('data-fit', '1'); }
(document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(fitAll);
</script>"""


def render(brief):
    a = brief["answers"]
    today = datetime.date.today()
    date_s = today.strftime("%-d %B %Y")
    latin, ar_name, ar_src, initials = names(a)
    # The name exactly as they wrote it leads; the other script is the second line.
    display_name = txt(a, "business") or "Your brand"
    second_name = latin if is_ar(display_name) else ar_name
    words_ = display_name.split()
    short_name = display_name
    while len(short_name) > 22 and len(words_) > 1:
        words_ = words_[:-1]
        short_name = " ".join(words_)
    P = derive_palette(a)
    T = derive_type(a)
    LG = derive_logo(a, latin)
    langs = set(lst(a, "languages"))
    show_ar = bool(ar_name) or "ar" in langs

    # colours for text on the cover / primary grounds
    on_primary = P["paper"] if contrast(P["paper"], P["primary"]) >= 3 else P["ink"]
    cover_bg = P["deep"] if P["dark"] or contrast(P["primary"], P["paper"]) < 3 else P["primary"]
    cover_ink = P["paper"] if contrast(P["paper"], cover_bg) >= 3 else P["ink"]
    primary_text = P["primary"] if contrast(P["primary"], P["paper"]) >= 4.5 else P["deep"]
    line = from_hls(hls(P["primary"])[0], 0.84, 0.12) if luminance(P["paper"]) > .5 else "#444"
    panel = from_hls(hls(P["paper"])[0], min(0.985, hls(P["paper"])[1] + 0.02), hls(P["paper"])[2])

    fonts = {}
    for f in (T["logo"], T["head"], T["body"], T["ar_head"], T["ar_body"], T["ar_logo"], T["mono_font"], MONO,
              (MONO[0], 400), (T["body"][0], 600)):
        fonts.setdefault(f[0], set()).add(f[1])
    root = f""":root {{
  --wm: {P['primary'] if contrast(P['primary'], P['paper']) >= 3 else P['deep']};
  --primary: {P['primary']}; --deep: {P['deep']}; --tint: {P['tint']}; --ink: {P['ink']}; --paper: {P['paper']};
  --panel: {panel}; --line: {line}; --muted: {P['mid']}; --primary-text: {primary_text};
  --cover-bg: {cover_bg}; --cover-ink: {cover_ink};
  --f-head: {fam(T['head'], T['ar_head'])}; --w-head: {T['head'][1]};
  --f-body: {fam(T['body'], T['ar_body'], generic='sans-serif')};
  --f-logo: {fam(T['logo'], T['ar_logo'])}; --w-logo: {T['logo'][1]};
  --f-ar-logo: {fam(T['ar_logo'])}; --w-ar-logo: {T['ar_logo'][1]};
  --f-ar-head: {fam(T['ar_head'])}; --w-ar-head: {T['ar_head'][1]};
  --f-ar-body: {fam(T['ar_body'], generic='sans-serif')};
  --f-mono: 'IBM Plex Mono', {fam(T['ar_body'], generic='monospace')};
}}"""
    css_fonts = font_css(fonts)
    pages = []
    n = [0]

    def foot():
        return (f'<div class="pf"><span><span class="nm" dir="auto">{e(display_name)}</span> · Brand book · Draft for review · {e(date_s)}</span>'
                f'<span>Prepared by AI Profit Lab</span></div>')

    def add(content, title, cls="", style=""):
        n[0] += 1
        pages.append((title, page(content, cls, n[0], title, foot(), style)))

    # 1. Cover
    cover = (f'<div class="in">{wordmark(display_name)}'
             + (wordmark(second_name, "", "font-size:30pt;margin-top:4mm;color:var(--cover-ink)") if second_name else "")
             + f'<div class="t">Brand book · Draft</div>'
             + (f'<div class="line" dir="auto">{e(txt(a, "oneLiner"))}</div>' if txt(a, "oneLiner") else "")
             + f'</div><div class="pf"><span>{e(date_s)}</span><span>Prepared by AI Profit Lab</span></div>')
    cover_page = f'<section class="page cover">{cover}</section>'

    # 3. Who we are
    if txt(a, "oneLiner") or txt(a, "why"):
        cols = []
        if txt(a, "why"):
            cols.append(f'<div class="col"><div class="k">Why we exist</div>{paras(txt(a, "why"))}</div>')
        if txt(a, "vision"):
            cols.append(f'<div class="col"><div class="k">Where we\'re going</div>{paras(txt(a, "vision"))}</div>')
        meta = [x for x in (txt(a, "industry"), txt(a, "markets")) if x]
        if meta:
            cols.append(f'<div class="col"><div class="k">What and where</div>' + "".join(f"<p dir='auto'>{e(x)}</p>" for x in meta) + "</div>")
        add(f'<div style="margin-top:6mm"><span class="yours">In your words</span>'
            f'<div class="statement" dir="auto" style="max-width:220mm">{e(txt(a, "oneLiner"))}</div></div>'
            f'<div class="rule" style="margin:10mm 0 7mm"></div><div class="grid3">{"".join(cols)}</div>', "Who we are")

    # 4. Story and values
    if txt(a, "story") or txt(a, "values"):
        vals = [v.strip(" -•\t") for v in re.split(r"\n+", txt(a, "values")) if v.strip(" -•\t")]
        items = []
        for i, v in enumerate(vals[:6], 1):
            m = re.match(r"^([^:—–-]{2,40})\s*[:—–-]\s*(.+)$", v)
            body = f'<b dir="auto">{e(m.group(1))}</b><span dir="auto">{e(m.group(2))}</span>' if m else f'<span dir="auto">{e(v)}</span>'
            items.append(f'<li><span class="n">{i:02d}</span><div>{body}</div></li>')
        left = (f'<div class="col"><h2>Our story</h2><span class="yours">In your words</span>{paras(txt(a, "story"))}</div>'
                if txt(a, "story") else '<div class="col"></div>')
        right = (f'<div class="col"><h2>What we value</h2><ul class="vals">{"".join(items)}</ul></div>' if items else "")
        add(f'<div class="grid2" style="grid-template-columns:1fr 1fr">{left}{right}</div>', "Story and values")

    # 5. Who we serve
    if txt(a, "customer"):
        right = ""
        for k, label in (("problem", "The problem we solve"), ("trust", "Why they choose us"), ("notCustomer", "Not for")):
            if txt(a, k):
                right += f'<div style="margin-bottom:5mm"><div class="k">{label}</div>{paras(txt(a, k))}</div>'
        feel = (f'<div style="margin-top:8mm"><div class="k">After dealing with us they should feel</div>'
                f'<div class="quote" dir="auto">{e(txt(a, "feel"))}</div></div>' if txt(a, "feel") else "")
        add(f'<div class="grid2" style="grid-template-columns:1.1fr 1fr"><div class="col"><h2>Who we serve</h2>'
            f'<span class="yours">In your words</span><div class="quote" dir="auto" style="font-size:13pt">{e(txt(a, "customer"))}</div>{feel}</div>'
            f'<div class="col" style="padding-top:12mm">{right}</div></div>', "Who we serve")

    # 6. Where we stand
    comps = [c for c in (a.get("competitors") or []) if isinstance(c, dict) and (c.get("name") or "").strip()]
    if txt(a, "different") or comps or a.get("price") in PRICE:
        price = a.get("price")
        scale = ("<div class='k' style='margin-top:9mm'>Price position</div><div class='scale4'>"
                 + "".join(f'<span class="{"on" if k == price else ""}">{v}</span>' for k, v in PRICE.items()) + "</div>"
                 if price in PRICE else "")
        comp_html = ""
        if comps:
            comp_html = ('<div class="k">Who customers compare us with</div><div class="chips" style="margin-bottom:6mm">'
                         + "".join(f'<span class="chip" dir="auto">{e(c["name"].strip())}</span>' for c in comps) + "</div>")
            for k, label in (("compGood", "What they do well"), ("compBad", "Where they fall short")):
                if txt(a, k):
                    comp_html += f'<div style="margin-bottom:4mm"><div class="k">{label}</div>{paras(txt(a, k))}</div>'
        add(f'<div class="grid2" style="grid-template-columns:1.1fr 1fr"><div class="col"><h2>Where we stand</h2>'
            + (f'<div class="k" style="margin-top:6mm">What makes us different</div><div class="quote" dir="auto">{e(txt(a, "different"))}</div>' if txt(a, "different") else "")
            + f'{scale}</div><div class="col" style="padding-top:12mm">{comp_html}</div></div>', "Where we stand")

    # 7. Character
    arch = [k for k in lst(a, "archetypes") if k in ARCHETYPES]
    if arch or txt(a, "fiveWords"):
        blocks = ""
        for i, k in enumerate(arch[:2]):
            nm, desc, eg, look, words, behave = ARCHETYPES[k]
            blocks += (f'<div class="arch{" sub" if i else ""}" style="margin-bottom:6mm"><svg viewBox="0 0 24 24">{ICONS[k]}</svg><div>'
                       f'<div class="k">{"Leading character" if i == 0 else "With a touch of"}</div>'
                       f'<h3 style="font-size:{18 if i == 0 else 13}pt">{nm}</h3><p class="small">{desc} Brands with this character: {eg}.</p>'
                       + (f'<dl><dt>Looks</dt><dd>{look}</dd><dt>Speaks</dt><dd>{words}</dd><dt>Acts</dt><dd>{behave}</dd></dl>' if i == 0 else "")
                       + "</div></div>")
        five = [w.strip() for w in re.split(r"[,،;\n/]+", txt(a, "fiveWords")) if w.strip()][:8]
        never = [w.strip() for w in re.split(r"[,،;\n/]+", txt(a, "neverWords")) if w.strip()][:6]
        right = ""
        if five:
            right += '<div class="k">We are</div><div class="chips" style="margin-bottom:6mm">' + "".join(f'<span class="chip big" dir="auto">{e(w)}</span>' for w in five) + "</div>"
        if never:
            right += '<div class="k">We are never</div><div class="chips" style="margin-bottom:6mm">' + "".join(f'<span class="chip no" dir="auto">{e(w)}</span>' for w in never) + "</div>"
        if txt(a, "person"):
            right += f'<div class="k">If we were a person</div><div class="quote" dir="auto">{e(txt(a, "person"))}</div>'
        add(f'<div class="grid2" style="grid-template-columns:1.15fr 1fr"><div class="col"><h2>Our character</h2>{blocks}</div>'
            f'<div class="col" style="padding-top:12mm">{right}</div></div>', "Character")

    # 8. Personality and voice
    sl = ""
    for k, lo, hi in PERSONALITY:
        v = slider(a, "personality", k)
        sl += (f'<div class="sl"><span class="{"on" if v < 40 else ""}">{lo}</span><span class="bar"><i style="left:{v}%"></i></span>'
               f'<span class="{"on" if v > 60 else ""}">{hi}</span></div>')
    vp = ""
    for k, lo, hi in VOICE:
        v = slider(a, "voice", k)
        s = side(v)
        principle, do, dont = VOICE_GUIDE[k][s]
        label = lo if s == "a" else hi if s == "b" else f"Between {lo.lower()} and {hi.lower()}"
        vp += (f'<div class="vp"><h3>{e(label)}</h3><p style="font-size:9.6pt;margin:0">{principle}</p>'
               f'<p class="do">“{e(do)}”</p><p class="dont">“{e(dont)}”</p></div>')
    add(f'<div class="grid2" style="grid-template-columns:1fr 1.15fr"><div class="col"><h2>Personality</h2>'
        f'<p class="small">Where you placed the brand on each scale.</p>{sl}</div>'
        f'<div class="col"><h2>How we sound</h2>{vp}<p class="small" style="margin-top:3mm">The example sentences show tone only. They are not things to publish as they are.</p></div></div>',
        "Personality and voice")

    # 9. Logo advice
    p_name, p_what = LOGO_TYPES[LG["primary"]]
    if LG["primary"] == "lettermark":
        rec_line = "Monogram, with the full name where there's room"
    else:
        compact_name = {"lettermark": "a monogram", "symbol": "the symbol on its own"}[LG["compact"]]
        rec_line = f"{p_name}, with {compact_name} for small spaces"
    if LG["badge"] and LG["primary"] != "emblem":
        rec_line += ", and a badge for packaging and seals"
    reasons = "".join(f"<li>{e(r)}</li>" for r in dict.fromkeys(LG["why"][LG["primary"]]))
    top = max(1, LG["ranked"][0][1])
    ranks = "".join(f'<div class="rank{" top" if i == 0 else ""}"><span>{LOGO_TYPES[k][0]}</span>'
                    f'<span class="bar"><i style="width:{max(0, s) / top * 100:.0f}%"></i></span><span class="s">{max(0, s)}</span></div>'
                    for i, (k, s) in enumerate(LG["ranked"]))
    msg = (f'<div style="margin-top:8mm"><div class="k">Your logo should say</div><div class="quote" dir="auto">{e(txt(a, "logoMessage"))}</div></div>'
           if txt(a, "logoMessage") else "")
    add(f'<div class="grid2" style="grid-template-columns:1.2fr 1fr"><div class="col"><div class="k">The right type of logo for you</div>'
        f'<div class="rec">{e(rec_line)}</div><p class="small" style="margin-bottom:5mm">{e(p_what)}</p>'
        f'<div class="k">Why</div><ul class="reasons">{reasons or "<li>It is the clearest, most flexible starting point.</li>"}</ul></div>'
        f'<div class="col" style="padding-top:2mm"><div class="k">How each type scored on your answers</div>{ranks}'
        f'<p class="small" style="margin-top:3mm">Points come from your own picks (3 each), your name, where you are seen, your characters, price and personality.</p>{msg}</div></div>',
        "Logo type")

    # 10. Draft logo
    mono_font = T["mono_font"]
    rtl = ' dir="rtl"' if is_ar(display_name) else ""
    sym = ""
    if LG["needs_symbol"] or LG["needs_character"]:
        sym = f'<div class="ph-sym">{"Symbol" if LG["needs_symbol"] else "Character"}<br>to be<br>designed</div>'
    if LG["primary"] == "lettermark":
        main_lockup = (f'<div class="lockup">{monogram_svg(initials, P["primary"], on_primary, T["mono_font"], 170)}'
                       f'{wordmark(display_name, "", "font-size:34pt")}</div>')
    else:
        main_lockup = f'<div class="lockup"{rtl}>{sym}{wordmark(display_name, "", "font-size:54pt")}</div>'
    main_rev = f'<div class="lockup"{rtl} style="color:{on_primary}">{sym}{wordmark(display_name, "", f"font-size:30pt;color:{on_primary}")}</div>'
    paper_c = P["paper"]
    main_dark = f'<div class="lockup"{rtl} style="color:{paper_c}">{sym}{wordmark(display_name, "", f"font-size:30pt;color:{paper_c}")}</div>'
    boards = (f'<div class="board" style="background:var(--panel);border:.3mm solid var(--line);height:72mm;grid-column:1/-1">{main_lockup}'
              f'<span class="cap">Primary · on paper</span></div>'
              f'<div class="board" style="background:{P["primary"]};height:44mm;color:{on_primary}">{main_rev}<span class="cap">On the main colour</span></div>'
              f'<div class="board" style="background:{P["ink"]};height:44mm;color:{P["paper"]}">{main_dark}<span class="cap">On ink</span></div>')
    extras = (f'<div class="board" style="background:var(--panel);border:.3mm solid var(--line);height:44mm;color:var(--muted)">'
              f'{monogram_svg(initials, P["primary"], on_primary, mono_font, 120)}<span class="cap">Monogram · profile pictures</span></div>')
    if LG["badge"] and latin:
        extras += (f'<div class="board" style="background:var(--panel);border:.3mm solid var(--line);height:44mm;color:var(--muted)">'
                   f'{badge_svg(latin, initials, P["deep"], P["paper"], mono_font, 140)}<span class="cap">Badge · packaging and seals</span></div>')
    if ar_name and latin:
        extras += (f'<div class="board" style="background:var(--panel);border:.3mm solid var(--line);height:44mm;flex-direction:column;gap:1mm;color:var(--muted)">'
                   f'{wordmark(latin, "", "font-size:20pt")}<div class="wm ar fit" dir="rtl" style="font-size:20pt">{e(ar_name)}</div>'
                   f'<span class="cap">English and Arabic</span></div>')
    cols = max(1, min(3, extras.count('class="board"')))
    used = f"{T['logo'][0]}" + (f" and {T['ar_logo'][0]} for Arabic" if ar_name else "")
    add(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:5mm;margin-top:2mm">{boards}</div>'
        f'<div style="display:grid;grid-template-columns:repeat({cols},minmax(0,1fr));gap:5mm;margin-top:5mm">{extras}</div>',
        "Draft logo", style="padding-top:18mm")
    # The caption for the draft page goes on the usage page header, so the boards keep their room.

    # 11. Using the logo
    skew_col = P["avoided"][0][1] if P["avoided"] else "#E0218A"
    dont = (f'<div><div class="board" style="background:var(--panel);border:.3mm solid var(--line)"><div class="wm fit" style="width:66%;font-size:15pt;transform:scaleX(1.45)">{e(display_name)}</div></div><p>Don\'t stretch or squash it.</p></div>'
            f'<div><div class="board" style="background:var(--panel);border:.3mm solid var(--line)"><div class="wm fit" style="width:100%;font-size:15pt;color:{skew_col}">{e(display_name)}</div></div><p>Don\'t use colours outside this book.</p></div>'
            f'<div><div class="board" style="background:repeating-linear-gradient(45deg,{P["primary"]} 0 3mm,{P["tint"]} 3mm 6mm)"><div class="wm fit" style="width:100%;font-size:15pt;color:{P["deep"]}">{e(display_name)}</div></div><p>Don\'t place it on busy backgrounds.</p></div>'
            f'<div><div class="board" style="background:var(--panel);border:.3mm solid var(--line)"><div class="wm fit" style="width:100%;font-size:15pt;color:transparent;-webkit-text-stroke:.3mm {P["primary"]};transform:rotate(-8deg)">{e(display_name)}</div></div><p>No outlines, shadows or rotation.</p></div>')
    add(f'<div class="grid2" style="grid-template-columns:1fr 1.2fr;height:auto"><div class="col"><h2>Using the logo</h2>'
        f'<p>This draft is your name set in <b>{e(used)}</b>, in your colours. It shows the direction; the final logo is drawn and refined '
        f'(spacing, details, every file format) once you are happy with it.</p>'
        f'<div class="k" style="margin-top:6mm">Minimum size</div><p>Full logo: at least 30 mm wide in print, 120 px on screen. Smaller than that, use the monogram (down to 8 mm or 24 px).</p></div>'
        f'<div class="col" style="display:flex;flex-direction:column;align-items:center;justify-content:center"><div class="k">Clear space</div>'
        f'<div class="clear"><span class="x" style="top:2mm;left:50%">x</span><span class="x" style="bottom:2mm;left:50%">x</span>'
        f'<span class="x" style="left:3mm;top:45%">x</span><span class="x" style="right:3mm;top:45%">x</span>{wordmark(display_name, "", "font-size:28pt")}</div>'
        f'<p class="small" style="margin-top:3mm;text-align:center">Keep empty space around the logo at least as tall as its capital letters (x).</p></div></div>'
        f'<div class="dont-grid" style="margin-top:8mm">{dont}</div>', "Using the logo")

    # 12. Colour
    def swatch(role, nm, hx, small=False):
        r, g, b = (round(c * 255) for c in rgb(hx))
        c_, m_, y_, k_ = cmyk(hx)
        fg = "#FFFFFF" if contrast("#FFFFFF", hx) >= contrast(P["ink"], hx) else P["ink"]
        return (f'<div class="sw{" small" if small else ""}"><div class="chipc" style="background:{hx};color:{fg}">{e(role)}</div>'
                f'<div class="codes"><b>{e(nm.capitalize() if nm else role)}</b>{hx}<br>RGB {r} {g} {b}<br>CMYK {c_} {m_} {y_} {k_}</div></div>')
    main_sw = "".join(swatch(*x) for x in P["main"])
    neu_sw = "".join(swatch(*x, small=True) for x in P["neutrals"])
    ratio = "".join(f'<span style="width:{w}%;background:{hx}"></span>' for nm, hx, w in P["ratio"])
    ratio += '</div><div class="legend">' + "".join(f'<span><i style="background:{hx}"></i>{e(nm)} {w}%</span>' for nm, hx, w in P["ratio"])
    avoided = ("<div class='k' style='margin-top:5mm'>Not for this brand</div>" + "".join(
        f'<span class="av"><i style="background:{hx}"></i>{e(nm)}</span>' for nm, hx in P["avoided"]) if P["avoided"] else "")
    notes = " ".join(P["notes"])
    add(f'<h2>Colour</h2><div class="sw-row" style="grid-template-columns:repeat({len(P["main"])},minmax(0,1fr))">{main_sw}</div>'
        f'<div class="sw-row" style="grid-template-columns:repeat({len(P["neutrals"])},minmax(0,1fr));margin-top:4mm">{neu_sw}</div>'
        f'<div style="display:grid;grid-template-columns:1.3fr 1fr;gap:10mm;margin-top:5mm"><div><div class="k">Roughly how much of each</div><div class="ratio">{ratio}</div>{avoided}</div>'
        f'<p class="small" style="margin:0">{e(notes)} Print colours (CMYK) are a starting point: check them on a printed proof.</p></div>',
        "Colour", style="padding-top:18mm")

    # 13. Typography
    sample_text = txt(a, "why") or txt(a, "oneLiner") or "Every brand has a voice. These are the letters it speaks in."
    sample_text = sample_text if len(sample_text) < 260 else sample_text[:257].rsplit(" ", 1)[0] + "…"
    ar_block = ""
    if show_ar:
        ar_sample = ar_name or "نص تجريبي لعرض الخط العربي"
        ar_block = (f'<div style="margin-top:7mm"><div class="k">Arabic</div><div class="spec ar" dir="rtl" style="font-size:40pt">{e(ar_sample)}</div>'
                    f'<p class="small">Headings: {e(T["ar_head"][0])} · Text: {e(T["ar_body"][0])}</p></div>')
    also = f' You also liked: {", ".join(T["also"])}.' if T["also"] else ""
    add(f'<div class="grid2" style="grid-template-columns:1fr 1fr"><div class="col"><h2>Typography</h2>'
        f'<p class="small">{e(T["label"])}: {e(T["feel"])}.{e(also)} {e(T["note"])} All of these are free Google Fonts, free to use commercially.</p>'
        f'<div class="k" style="margin-top:5mm">Headings · {e(T["head"][0])}</div><div class="spec">Aa</div>'
        f'<div class="k" style="margin-top:5mm">Text · {e(T["body"][0])}</div><p dir="auto" style="font-size:11pt">{e(sample_text)}</p>'
        + (f'<div class="k" style="margin-top:5mm">Logo lettering · {e(T["logo"][0])}</div>' if T["logo"] != T["head"] else "")
        + f'</div><div class="col">{ar_block}<div class="k" style="margin-top:7mm">Sizes</div><table class="scale-t">'
        f'<tr><td>Title</td><td style="font-family:var(--f-head);font-weight:var(--w-head);font-size:26pt;color:var(--deep)" dir="auto">{e(short_name)}</td><td>40 / 26 pt</td></tr>'
        f'<tr><td>Heading</td><td style="font-family:var(--f-head);font-weight:var(--w-head);font-size:16pt;color:var(--deep)">A clear heading</td><td>24 / 16 pt</td></tr>'
        f'<tr><td>Text</td><td style="font-size:10.5pt">Body text for reading, set comfortably.</td><td>16 px / 10.5 pt</td></tr>'
        f'<tr><td>Small</td><td style="font-size:8.5pt;color:var(--muted)">Captions and notes</td><td>13 px / 8.5 pt</td></tr></table></div></div>',
        "Typography")

    # 14. Look and feel
    tt = a.get("thisThat") or {}
    dirs = ""
    for k, (la, lb, ma, mb) in PAIRS.items():
        v = tt.get(k)
        if v in ("a", "b"):
            dirs += f'<div class="dir"><h3>{la if v == "a" else lb}</h3><p class="small">{ma if v == "a" else mb}</p></div>'
    extra = ""
    if txt(a, "avoid"):
        extra += f'<div><div class="k">Avoid</div>{paras(txt(a, "avoid"))}</div>'
    if txt(a, "admire"):
        extra += f'<div><div class="k">Brands you admire</div>{paras(txt(a, "admire"))}</div>'
    refs = txt(a, "refsLike")
    if refs:
        extra += f'<div><div class="k">References you sent</div>{paras(refs, "small")}</div>'
    if dirs or extra:
        add(f'<h2>Look and feel</h2><div class="grid3" style="margin-top:4mm">{dirs}</div>'
            + (f'<div class="grid3" style="margin-top:9mm">{extra}</div>' if extra else ""), "Look and feel")

    # 15. Where people will see you
    ch = [c for c in lst(a, "channels") if c in CHANNELS]
    handle = (re.findall(r"@[\w.]+", txt(a, "social")) or ["@" + re.sub(r"[^a-z0-9]+", "", display_name.lower())[:24]])[0]
    words5 = [w.strip() for w in re.split(r"[,،;\n/]+", txt(a, "fiveWords")) if w.strip()]
    tile1 = (words5[0] if words5 else display_name).capitalize()
    ig = (f'<div class="mock-ig"><div class="top">{monogram_svg(initials, P["primary"], on_primary, mono_font, 54)}'
          f'<div><b style="font-size:9pt">{e(handle)}</b><div style="color:#666;margin-top:1mm" dir="auto">{e((txt(a, "oneLiner") or "")[:90])}</div></div></div>'
          f'<div class="tiles"><div style="background:{P["primary"]};color:{on_primary};font-family:var(--f-head);font-weight:var(--w-head);font-size:13pt" dir="auto">{e(tile1)}</div>'
          f'<div style="background:{P["tint"]}">{monogram_svg(initials, P["deep"], P["paper"], mono_font, 46)}</div>'
          f'<div style="background:{P["paper"]};color:{P["deep"]};font-size:7pt;border:.2mm solid #eee" dir="auto">{e((txt(a, "different") or txt(a, "why") or "")[:80])}</div></div></div>')
    contact_lines = [x for x in (txt(a, "contactName"), txt(a, "role"), txt(a, "email"), txt(a, "phone")) if x]
    front = f'<div class="card-bc" style="background:{P["paper"]};align-items:center">{wordmark(display_name, "", "font-size:18pt")}</div>'
    back_c = (f'<div class="card-bc" style="background:{P["primary"]};color:{on_primary};font-size:8pt;line-height:1.6;border:0">'
              f'<b style="font-family:var(--f-head);font-weight:var(--w-head);font-size:12pt" dir="auto">{e(contact_lines[0] if contact_lines else display_name)}</b>'
              + "".join(f'<span dir="auto">{e(x)}</span>' for x in contact_lines[1:]) + "</div>")
    under = ""
    if set(ch) & {"store", "vehicles", "events"}:
        under = (f'<div class="k cap2" style="margin-top:6mm">Sign</div><div class="sign" style="background:{P["deep"]}">'
                 f'{wordmark(display_name, "", "font-size:24pt;color:" + P["paper"])}</div>')
    elif "packaging" in ch:
        label = badge_svg(latin, initials, P["deep"], P["paper"], mono_font, 110, "pk") if (LG["badge"] and latin) else wordmark(display_name, "", "font-size:20pt")
        under = (f'<div class="k cap2" style="margin-top:6mm">Packaging label</div>'
                 f'<div class="board" style="background:{P["tint"]};height:34mm">{label}</div>')
    chan_list = "".join(f'<div class="chan"><b>{CHANNELS[c][0]}</b><span>{CHANNELS[c][1]}</span></div>' for c in ch)
    add(f'<h2>Where people will see you</h2><div class="apps"><div><div class="k">Profile and posts</div>{ig}{under}</div>'
        f'<div><div class="k">Business card</div><div class="cards">{front}{back_c}</div></div>'
        f'<div><div class="k">Guidance</div>{chan_list or "<p class=small>You did not choose where the brand will be seen. Tell us, and we will add guidance for each place.</p>"}</div></div>',
        "Where people will see you")

    # 16. Before this is final
    todo = ['<li><b>The logo is a draft.</b> It is your name set in a chosen typeface. The final logo is drawn and refined once you agree the direction.</li>']
    if LG["needs_symbol"]:
        todo.append("<li><b>The symbol is not designed yet.</b> The empty box in the draft marks where it goes.</li>")
    if LG["needs_character"]:
        todo.append("<li><b>The character is not designed yet.</b> The empty box in the draft marks where it goes.</li>")
    if a.get("nameFinal") in ("open", "need"):
        todo.append("<li><b>The name isn't final.</b> You told us the name is still open, and the logo depends on it.</li>")
    if ar_name and ar_src == "notes":
        todo.append(f'<li><b>Check the Arabic name.</b> We took <span dir="rtl">{e(ar_name)}</span> from your answer about how the name is written. Confirm the spelling.</li>')
    if "ar" in langs and not ar_name:
        todo.append("<li><b>Arabic name.</b> Your brand works in Arabic, but we don't have the Arabic spelling of the name yet.</li>")
    if a.get("tagline") in ("need", "unsure"):
        todo.append("<li><b>Tagline.</b> You don't have one yet, so this draft has none.</li>")
    todo.append("<li><b>Colours on paper.</b> Screen and print colours differ. Check a printed proof before any large print run.</li>")
    add(f'<div class="grid2" style="grid-template-columns:1fr 1.3fr"><div class="col"><h2>Before this is final</h2>'
        f'<p class="lede">This book is a first draft, built from your answers. Mark anything that doesn\'t feel like you, and send it back to us.</p></div>'
        f'<div class="col"><ul class="todo">{"".join(todo)}</ul></div></div>', "Before this is final")

    # Contents (built last so it lists the pages that exist)
    toc_items = "".join(f'<li><span class="n">{i:02d}</span>{e(t)}</li>' for i, (t, _) in enumerate(pages, 1))
    contents = (f'<section class="page"><div class="grid2"><div class="col"><h1>{e(display_name)}</h1>'
                f'<div class="k" style="margin-top:4mm">Brand book · First draft · {e(date_s)}</div>'
                f'<p class="lede" style="margin-top:8mm">This is a first draft of your brand book, built from your answers to our brand discovery questions. '
                f'Where we quote you, it says so. Everything else is our recommendation, to discuss, not final artwork.</p></div>'
                f'<div class="col" style="padding-top:2mm"><div class="k">Contents</div><ul class="toc">{toc_items}</ul></div></div>'
                f'<div class="pf"><span><span class="nm" dir="auto">{e(display_name)}</span> · Brand book · Draft for review</span><span>Prepared by AI Profit Lab</span></div></section>')

    apl = base64.b64encode(APL_WORDMARK.read_bytes()).decode("ascii") if APL_WORDMARK.exists() else ""
    back = (f'<section class="page back"><div class="in">'
            + (f'<img src="data:image/svg+xml;base64,{apl}" alt="AI Profit Lab">' if apl else "<p>AI Profit Lab</p>")
            + '<p style="margin-top:4mm">Prepared by AI Profit Lab</p>'
              '<p>aiprofitlab.io · hello@aiprofitlab.io · <span dir="ltr">+968 9924 5250</span></p>'
              '<p style="margin-top:6mm;font-size:6.6pt">AI Profit Lab is a brand of Lotus Gulf International (CR 1570092) · South Al Khuwair, Bousher, Muscat, Oman</p>'
              '</div></section>')

    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{e(display_name)} · Brand book (draft)</title>'
           f'<meta name="robots" content="noindex"><style>{css_fonts}\n{root}\n{CSS}</style></head><body>'
           + cover_page + contents + "".join(p for _, p in pages) + back + FIT_JS + "</body></html>")
    return doc, dict(P=P, T=T, LG=LG, latin=latin, ar=ar_name, ar_src=ar_src, initials=initials, pages=len(pages) + 3)


# ---------------------------------------------------------------------------
# Review notes for Nahid (never sent to the client)
# ---------------------------------------------------------------------------

def review_notes(brief, info, out_dir):
    a = brief["answers"]
    LG, P, T = info["LG"], info["P"], info["T"]
    empty = [k for k in ("why", "vision", "story", "values", "customer", "problem", "trust", "different",
                         "competitors", "fiveWords", "neverWords", "logoMessage", "logoType", "typeface",
                         "colorsLove", "channels") if not (lst(a, k) if isinstance(a.get(k), list) else txt(a, k))]
    lines = [f"# Review notes: {txt(a, 'business')}", "",
             "For you only. Read before sending the brand book.", "",
             f"- Brief language: {'Arabic' if brief.get('lang') == 'ar' else 'English'}"
             + (" - the book is in English and quotes their Arabic answers as written." if brief.get("lang") == "ar" else ""),
             f"- Project type: {PROJECT.get(a.get('projectType'), '—')}",
             f"- Logo advice: {LOGO_TYPES[LG['primary']][0]} (scores: "
             + ", ".join(f"{LOGO_TYPES[k][0]} {s}" for k, s in LG["ranked"]) + ")",
             f"- Lettering: {T['label']} → logo {T['logo'][0]}, headings {T['head'][0]}, text {T['body'][0]}; "
             f"Arabic {T['ar_head'][0]} / {T['ar_body'][0]}" + (f" ({T['note']})" if T["note"] else ""),
             f"- Palette: " + ", ".join(f"{r} {hx}" for r, _, hx in P["main"]) + ("  [suggested, they chose none]" if P["suggested"] else ""),
             f"- Monogram initials: {info['initials'] or '—'} (check they make sense)",
             ]
    if info["ar"]:
        lines.append(f"- Arabic name: {info['ar']} (from {'their name' if info['ar_src'] == 'name' else 'their notes'}) - confirm spelling")
    if a.get("projectType") in ("refresh", "rebrand"):
        lines.append("- This is a REFRESH/REBRAND: look at their current logo (Drive link in the email) before sending. The draft ignores it.")
    ups = [k for k in ("existing", "refsLike", "refsDislike") if isinstance(a.get(k), dict) and (a[k].get("links") or "").strip()]
    if ups:
        lines.append("- They gave reference links in: " + ", ".join(ups) + ". Uploaded files are only in the email's Drive links.")
    lines.append("- Uploaded files (if any) are NOT in this brief: open the Drive links in the notification email.")
    if empty:
        lines.append("- Unanswered, so missing from the book: " + ", ".join(empty))
    if txt(a, "anything"):
        lines += ["", "## They added", "", txt(a, "anything")]
    lines += ["", "## Before sending", "",
              "1. Open brand-book.html in Chrome and read every page.",
              "2. Fix wording directly in the HTML if needed, then reprint: "
              "`python3 tools/brand-discovery/build_brand_book.py --reprint " + str(out_dir / "brand-book.html") + "`",
              "3. Send brand-book.pdf to " + (txt(a, "email") or "the client") + "."]
    (out_dir / "review-notes.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def print_pdf(html_path, pdf_path):
    if not pathlib.Path(CHROME).exists():
        print("  Google Chrome not found, so no PDF. Open the HTML in a browser and print it to PDF "
              "(landscape, no margins, background graphics on).")
        return False
    r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--no-first-run",
                        "--virtual-time-budget=8000", "--run-all-compositor-stages-before-draw",
                        f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
                       capture_output=True, timeout=180)
    if not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        print("  Chrome did not write a PDF:", r.stderr.decode()[-400:])
        return False
    return True


def slugify(s):
    return re.sub(r"[^a-z0-9؀-ۿ]+", "-", s.lower()).strip("-") or "brand"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("brief", nargs="?", help="the .md brief from the notification email, or a .json of answers")
    ap.add_argument("--sample", action="store_true", help="build the fictional sample in sample-brief.json")
    ap.add_argument("--out", help="output folder (default .tmp/brand-books/<business>/)")
    ap.add_argument("--no-pdf", action="store_true", help="write the HTML only")
    ap.add_argument("--reprint", metavar="HTML", help="print an edited brand-book.html to PDF again, nothing else")
    args = ap.parse_args()

    if args.reprint:
        h = pathlib.Path(args.reprint)
        pdf = h.with_suffix(".pdf")
        if print_pdf(h, pdf):
            print(f"  {pdf}")
        return

    check_against_form()
    path = SAMPLE if args.sample else pathlib.Path(args.brief).expanduser() if args.brief else None
    if not path or not path.exists():
        ap.error("give the path of a brief (.md or .json), or --sample")
    brief = load_brief(path)
    if not txt(brief["answers"], "business"):
        sys.exit("The brief has no business name.")
    doc, info = render(brief)
    out = pathlib.Path(args.out) if args.out else OUT_ROOT / slugify(txt(brief["answers"], "business"))
    out.mkdir(parents=True, exist_ok=True)
    h = out / "brand-book.html"
    h.write_text(doc, encoding="utf-8")
    review_notes(brief, info, out)
    print(f"  {h}  ({len(doc) // 1024} KB, {info['pages']} pages)")
    if not args.no_pdf and print_pdf(h, out / "brand-book.pdf"):
        print(f"  {out / 'brand-book.pdf'}")
    print(f"  {out / 'review-notes.md'}")
    LG = info["LG"]
    extra = {"lettermark": "monogram for small spaces", "symbol": "symbol alone for small spaces",
             "wordmark": "full name where there's room"}[LG["compact"]]
    print(f"  logo: {LOGO_TYPES[LG['primary']][0]}, {extra}"
          f" · lettering: {info['T']['label']} · primary {info['P']['primary']}")


if __name__ == "__main__":
    main()
