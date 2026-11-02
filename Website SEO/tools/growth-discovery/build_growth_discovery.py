#!/usr/bin/env python3
"""
Build the Growth Discovery questionnaire in three languages.

    python3 tools/growth-discovery/build_growth_discovery.py

Reads   tools/growth-discovery/growth-discovery.src.html     (the one source)
Writes  public_html/en/growth-discovery.html                  -> /en/growth-discovery/
        public_html/fa/growth-discovery/index.html            -> /fa/growth-discovery/
        public_html/ar/growth-discovery/index.html            -> /ar/growth-discovery/

All three URLs are served without any .htaccess change: the English file by
rule 3 (the rule that serves /en/brand-discovery/), the Persian and Arabic ones
as directory indexes. /fa/ is the site's first Persian path; nothing else lives
there yet, so the logo on the Persian page goes to the English home.

The three pages are the same form. Only the <head> and the strings around the
form differ, and the form starts in the language of <html lang>. The head is
kit.head_html(), the one every v4 page uses. kit has no Persian chrome, so the
Persian head is the Arabic one (RTL, Arabic-script fonts) with lang, og:locale
and the skip link changed.

Clarity is OFF (clarity=False): the review and results screens render the
client's answers as DOM, and Clarity records rendered DOM.

The page is a client-only intake form: noindex, not in run_sitemap.py, not in
any nav, and build_aiden_index.py skips it on the noindex tag.

Personal links: ?b=Business%20Name&ig=handle1,handle2&n=Contact prefills an
empty draft; ?plans=off hides the plan names; ?built=, ?until= and ?pp= are for
a client who already has our proposal. See docs/growth-discovery.md.
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

SRC = HERE / "growth-discovery.src.html"
PUB = ROOT / "public_html"

PATHS = {"en": "/en/growth-discovery/", "fa": "/fa/growth-discovery/", "ar": "/ar/growth-discovery/"}

# Every family the form uses. kit.head_html loads the site subset for one
# language; this adds the rest, because the language switch can turn any of the
# three pages into the others.
FONTS_ALL = ("https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600"
             "&family=IBM+Plex+Mono:wght@400;500&family=Markazi+Text:wght@400;500;600"
             "&family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap")

HEADEXTRA = (f'<link rel="stylesheet" media="print" onload="this.media=\'all\'" href="{FONTS_ALL}">\n'
             f'<noscript><link rel="stylesheet" href="{FONTS_ALL}"></noscript>\n'
             '<meta name="theme-color" content="#0A3D30">')

# kit.SKIP_CSS parks the skip link at left:-9999px, which under dir=rtl is a
# 10,000px sideways scroll. The two rules tools/v4/rtl.py gives the Arabic pages.
SKIP_RTL = """
[dir=rtl] .skip{left:auto;right:-9999px;border-radius:0 0 0 8px}
[dir=rtl] .skip:focus{left:auto;right:0}
"""

MAIL = '<a href="mailto:hello@aiprofitlab.io" dir="ltr">hello@aiprofitlab.io</a>'
WHATSAPP = '<a href="https://api.whatsapp.com/send?phone=96899245250" dir="ltr">+968 9924 5250</a>'

LEGAL_FA = ('&copy; ۲۰۲۶ AI Profit Lab، برندی از Lotus Gulf International '
            '(ثبت تجاری <span dir="ltr">1570092</span>)<br>\n      الخویر جنوبی، بوشر، مسقط، عمان '
            '&middot; بدون ثبت در مالیات بر ارزش افزوده (شماره‌ی مالیاتی <span dir="ltr">2317725</span>)<br>\n      '
            '<a href="/terms/">شرایط خدمات</a> &middot; <a href="/refund-policy/">بازپرداخت و لغو</a>\n      '
            '&middot; <a href="/privacy/">حریم خصوصی</a>')

LANGS = {
    "en": {
        "out": PUB / "en" / "growth-discovery.html",
        "home": "/", "home_aria": kit.CHROME["en"]["home_aria"],
        "title": "Growth discovery — AI Profit Lab",
        "desc": ("About fifteen minutes of questions on your business, your customers and a normal week. "
                 "As you answer, your Growth X-ray builds beside you."),
        "noscript": (f"<b>This form needs JavaScript.</b> If you can't turn it on, email us at {MAIL} "
                     f"or send a WhatsApp to {WHATSAPP} and we'll go through the questions with you."),
    },
    "fa": {
        "out": PUB / "fa" / "growth-discovery" / "index.html",
        "home": "/", "home_aria": "AI Profit Lab — صفحه‌ی اصلی",
        "title": "پرسشنامه‌ی رشد دیجیتال — AI Profit Lab",
        "desc": ("حدود پانزده دقیقه سؤال درباره‌ی کسب‌وکارتان، مشتری‌هایتان و یک هفته‌ی معمولی کارتان. "
                 "همزمان با جواب‌دادن، چکاپ رشد شما کنار صفحه ساخته می‌شود."),
        "noscript": (f"<b>این فرم به JavaScript نیاز دارد.</b> اگر نمی‌توانید روشنش کنید، به {MAIL} ایمیل بزنید "
                     f"یا در واتساپ به {WHATSAPP} پیام بدهید تا سؤال‌ها را با هم مرور کنیم."),
    },
    "ar": {
        "out": PUB / "ar" / "growth-discovery" / "index.html",
        "home": "/ar/", "home_aria": kit.CHROME["ar"]["home_aria"],
        "title": "استبيان النمو الرقمي — AI Profit Lab",
        "desc": ("حوالي خمس عشرة دقيقة من الأسئلة عن عملك وعملائك وأسبوع عمل عادي. "
                 "مع كل إجابة يُبنى فحص النمو الخاص بك بجانبك."),
        # New Arabic, not yet reviewed - the form shows the same disclosure.
        "noscript": (f"<b>يحتاج هذا الاستبيان إلى JavaScript.</b> إذا تعذّر تفعيله، راسلنا على {MAIL} "
                     f"أو عبر واتساب على {WHATSAPP} وسنمرّ على الأسئلة معك.<br>"
                     "ملاحظة: النص العربي في هذه الصفحة لم تتم مراجعته بعد من قبل متحدث أصلي."),
    },
}


def alternates():
    out = [f'<link rel="alternate" hreflang="{l}" href="https://aiprofitlab.io{p}">' for l, p in PATHS.items()]
    out.append(f'<link rel="alternate" hreflang="x-default" href="https://aiprofitlab.io{PATHS["en"]}">')
    return "\n".join(out)


def head_for(lang):
    if lang != "fa":
        return kit.head_html(lang, clarity=False)
    head = kit.head_html("ar", clarity=False)
    swaps = [
        ('<html dir="rtl" lang="ar">', '<html dir="rtl" lang="fa">'),
        ('content="ar_OM"', 'content="fa_IR"'),
        ('>%s</a>' % kit.CHROME["ar"]["skip"], '>رفتن به محتوا</a>'),
    ]
    for a, b in swaps:
        if a not in head:
            sys.exit(f"fa head: expected to find {a!r} in kit.head_html('ar')")
        head = head.replace(a, b)
    return head


def split_source(text):
    """(css, body): the first <style> block, and everything after it."""
    m = re.search(r"<style>(.*?)</style>", text, re.S)
    if not m or not m.group(1).lstrip().startswith(("/*", ":root")):
        sys.exit("growth-discovery.src.html: the first <style> block is not the page CSS")
    return m.group(1), text[m.end():].strip() + "\n"


def build(lang, css, body):
    c = LANGS[lang]
    head = head_for(lang)
    fills = {
        "ROBOTS": kit.ROBOTS_NONE,
        "ALTERNATES": alternates(),
        "TITLE": c["title"],
        "DESC": c["desc"],
        "PATH": PATHS[lang],
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
                 .replace("{{HOME_ARIA}}", c["home_aria"])
                 .replace("{{NOSCRIPT}}", c["noscript"])
                 .replace("{{LEGAL_EN}}", kit.CHROME["en"]["legal"])
                 .replace("{{LEGAL_FA}}", LEGAL_FA)
                 .replace("{{LEGAL_AR}}", kit.CHROME["ar"]["legal"])
                 .replace("{{HIDE_EN}}", "" if lang == "en" else " hidden")
                 .replace("{{HIDE_FA}}", "" if lang == "fa" else " hidden")
                 .replace("{{HIDE_AR}}", "" if lang == "ar" else " hidden"))

    html = head + page_body + "</body>\n</html>\n"
    left = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", html)))
    if left:
        sys.exit(f"{lang}: unfilled placeholders {left}")
    if "wa.me/" in html:
        sys.exit(f"{lang}: a wa.me link slipped in - use api.whatsapp.com/send?phone= (see whatsapp-links-never-wa-me)")
    c["out"].parent.mkdir(parents=True, exist_ok=True)
    c["out"].write_text(html, encoding="utf-8")
    print(f"  {c['out'].relative_to(ROOT)}  ({len(html) // 1024} KB)")


def main():
    css, body = split_source(SRC.read_text(encoding="utf-8"))
    for lang in LANGS:
        build(lang, css, body)


if __name__ == "__main__":
    main()
