#!/usr/bin/env python3
"""
Build the Brand Discovery questionnaire in both languages.

    python3 tools/brand-discovery/build_brand_discovery.py

Reads   tools/brand-discovery/brand-discovery.src.html   (the one source)
Writes  public_html/en/brand-discovery.html               -> /en/brand-discovery/
        public_html/ar/brand-discovery/index.html         -> /ar/brand-discovery/

Both URLs are served without any .htaccess change: the English file by rule 3
(the same rule that serves /en/onboarding/), the Arabic one as a directory
index, the way /ar/ itself is served.

The two pages are the same form. Only the <head> and a few strings around the
form differ, and the form itself starts in the language of <html lang>, so a
second hand-kept copy would be nothing but a chance to drift. The head is
kit.head_html(), the one every v4 page uses: favicon set, og tags, gtag and the
versioned /js/apl-analytics.js tag all come from there, so this page picks up a
change to any of them on the next build.

Clarity is OFF (clarity=False). The review step renders the client's answers -
names, email, phone - as DOM, and Clarity records rendered DOM, not just field
values. See kit.head_html's docstring for the invoice-tool case that proved it.

The page is a client-only intake form: noindex, not in run_sitemap.py, not in
any nav, and build_aiden_index.py skips it on the noindex tag.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS / "v4"))
sys.path.insert(0, str(TOOLS))

import kit  # noqa: E402

SRC = HERE / "brand-discovery.src.html"
PUB = ROOT / "public_html"

EN_PATH = "/en/brand-discovery/"
AR_PATH = "/ar/brand-discovery/"

# Every family the form uses, including the eight it only shows as typeface and
# logo previews. kit.head_html loads the site subset for one language; this adds
# the rest, because either page can be toggled into the other language.
FONTS_ALL = ("https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600"
             "&family=IBM+Plex+Mono:wght@400;500&family=Markazi+Text:wght@400;500;600"
             "&family=IBM+Plex+Sans+Arabic:wght@400;500;600&family=Cormorant+Garamond:wght@500"
             "&family=Archivo:wght@600&family=Zilla+Slab:wght@600&family=Italianno&family=Abril+Fatface"
             "&family=Reem+Kufi:wght@600&family=Aref+Ruqaa:wght@700&display=swap")

HEADEXTRA = (f'<link rel="stylesheet" media="print" onload="this.media=\'all\'" href="{FONTS_ALL}">\n'
             f'<noscript><link rel="stylesheet" href="{FONTS_ALL}"></noscript>\n'
             '<meta name="theme-color" content="#0A3D30">')

# kit.SKIP_CSS parks the skip link at left:-9999px, which under dir=rtl is a
# 10,000px sideways scroll. These are the two rules tools/v4/rtl.py (RTL_CHROME)
# gives the Arabic v4 pages. Both outputs carry them, because the in-page toggle
# flips <html dir> on either page.
SKIP_RTL = """
[dir=rtl] .skip{left:auto;right:-9999px;border-radius:0 0 0 8px}
[dir=rtl] .skip:focus{left:auto;right:0}
"""

MAIL = '<a href="mailto:hello@aiprofitlab.io" dir="ltr">hello@aiprofitlab.io</a>'
WHATSAPP = '<a href="https://wa.me/96899245250" dir="ltr">+968 9924 5250</a>'

LANGS = {
    "en": {
        "out": PUB / "en" / "brand-discovery.html",
        "path": EN_PATH, "other": AR_PATH,
        "title": "Brand discovery questionnaire — AI Profit Lab",
        "desc": ("Before we draw a logo or pick a colour, we need to understand your business, your "
                 "customers and the character you want to show. About 20–25 minutes; saves as you go."),
        "home": "/",
        "noscript": (f"<b>This form needs JavaScript.</b> If you can't turn it on, email us at {MAIL} "
                     f"or send a WhatsApp to {WHATSAPP} and we'll go through the questions with you."),
    },
    "ar": {
        "out": PUB / "ar" / "brand-discovery" / "index.html",
        "path": AR_PATH, "other": EN_PATH,
        "title": "استبيان اكتشاف الهوية — AI Profit Lab",
        # The form's own welcome lede, word for word.
        "desc": ("قبل أن نصمم شعاراً أو نختار لوناً، نحتاج إلى فهم عملك وعملائك والشخصية التي تريد أن تظهر "
                 "بها. حوالي ٢٠–٢٥ دقيقة."),
        "home": "/ar/",
        # New Arabic, not yet reviewed - so it carries the same disclosure the
        # form shows on its welcome step.
        "noscript": (f"<b>يحتاج هذا الاستبيان إلى JavaScript.</b> إذا تعذّر تفعيله، راسلنا على {MAIL} "
                     f"أو عبر واتساب على {WHATSAPP} وسنمرّ على الأسئلة معك.<br>"
                     "ملاحظة: النص العربي في هذه الصفحة لم تتم مراجعته بعد من قبل متحدث أصلي."),
    },
}


def split_source(text):
    """(css, body): the first <style> block, and everything after it."""
    m = re.search(r"<style>(.*?)</style>", text, re.S)
    if not m or not m.group(1).lstrip().startswith(("/*", ":root")):
        sys.exit("brand-discovery.src.html: the first <style> block is not the page CSS")
    return m.group(1), text[m.end():].strip() + "\n"


def build(lang, css, body):
    c = LANGS[lang]
    head = kit.head_html(lang, clarity=False)
    fills = {
        "ROBOTS": kit.ROBOTS_NONE,
        "ALTERNATES": kit.alternates(c["path"], c["other"], lang),
        "TITLE": c["title"],
        "DESC": c["desc"],
        "PATH": c["path"],
        "HEADEXTRA": HEADEXTRA,
        "CSS": css + kit.SKIP_CSS + SKIP_RTL,
        "SCHEMA": "",
    }
    for k, v in fills.items():
        head = head.replace("{{%s}}" % k, v)

    page_body = (body
                 .replace("{{HOME}}", c["home"])
                 .replace("{{HOME_ARIA_EN}}", kit.CHROME["en"]["home_aria"])
                 .replace("{{HOME_ARIA_AR}}", kit.CHROME["ar"]["home_aria"])
                 .replace("{{HOME_ARIA}}", kit.CHROME[lang]["home_aria"])
                 .replace("{{NOSCRIPT}}", c["noscript"])
                 .replace("{{LEGAL_EN}}", kit.CHROME["en"]["legal"])
                 .replace("{{LEGAL_AR}}", kit.CHROME["ar"]["legal"])
                 .replace("{{HIDE_EN}}", "" if lang == "en" else " hidden")
                 .replace("{{HIDE_AR}}", "" if lang == "ar" else " hidden"))

    html = head + page_body + "</body>\n</html>\n"
    left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", html)))
    if left:
        sys.exit(f"{lang}: unfilled placeholders {left}")
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    c["out"].write_text(html, encoding="utf-8")
    print(f"  {c['out'].relative_to(ROOT)}  ({len(html) // 1024} KB)")


def main():
    css, body = split_source(SRC.read_text(encoding="utf-8"))
    for lang in LANGS:
        build(lang, css, body)


if __name__ == "__main__":
    main()
