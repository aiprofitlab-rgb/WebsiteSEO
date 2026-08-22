#!/usr/bin/env python3
"""
Chrome for the re-skinned blog: head, header, footer and the CSS the migrated
articles need on top of the v4 kit.

Two things separate this from `kit.py`, and both are deliberate:

  * URLs point at the pages that are live and indexed today (`/en/`,
    `/en/services/`, `/blog/`, and the Arabic set at the root). Flipped on
    2026-08-21 when the v4 set launched onto those URLs; before that they
    pointed at the old `-en` pages, because linking an indexed article into a
    `noindex` preview would have pushed crawlers and readers into a page that
    asks not to be indexed.

  * Nothing here emits `<meta name="robots" content="noindex">`. `kit.HEAD`
    does, because the v4 previews must stay out of the index. An article that
    is already ranking must not inherit that tag.

The head is assembled from what the source page already had. Every field that
carried an SEO or answer-engine signal is copied across unchanged - title,
description, keywords, canonical, hreflang, and the JSON-LD graph byte for
byte. What is *added* is the layer the old pages never had: Open Graph, Twitter
cards and an explicit robots directive with large image previews.
"""
import html as _html

from kit import (BASE_CSS, GOOGLE_G, GOOGLE_REVIEW, MAIL_ICON, SKIP_CSS, SOCIALS,
                 STAR, STAR_SVG, TOKENS, WA, WA_ICON, WA_SMALL, _socials)
from article_kit import ARTICLE_CSS
from rtl import RTL_BASE

# --------------------------------------------------------------------------
# Where the chrome points. One table, both languages.
# --------------------------------------------------------------------------
URLS = {
    "en": {
        "home": "/", "services": "/en/services/", "process": "/en/process/",
        "about": "/en/about/", "contact": "/en/contact/", "blog": "/blog/",
        "privacy": "/privacy/", "other": "/ar/", "sim": "/en/simulators/",
        "demo": "/en/demos/", "dash": "/en/demos/#dash",
    },
    "ar": {
        "home": "/ar/", "services": "/services/", "process": "/process/",
        "about": "/about/", "contact": "/contact/", "blog": "/blog-ar/",
        "privacy": "/privacy/", "other": "/", "sim": "/simulators-ar/",
        "demo": "/demos-ar/", "dash": "/demos-ar/#dash",
    },
}

T = {
    "en": {
        "nav": [("Home", "home", "01"), ("What I Build", "services", "02"),
                ("How It Works", "process", "03"), ("About", "about", "04"),
                ("Contact", "contact", "05"), ("Articles", "blog", "06")],
        "other_lang": "&#1593;&#1585;&#1576;&#1610;", "whatsapp": "WhatsApp",
        "skip": "Skip to content", "menu": "Open menu",
        "crumb_home": "Home", "crumb_blog": "Articles", "article": "Article",
        "onpage": "On this page", "allposts": "All articles",
        "questions": "Questions people ask", "sources": "Sources",
        "keepreading": "Keep reading", "read": "Read &rarr;",
        "minread": "min read", "published": "Published", "updated": "Updated",
        "share_wa": "Share on WhatsApp", "share_li": "Share on LinkedIn", "copy": "Copy link",
        "copied": "Link copied", "by": "AI Profit Lab", "byrole": "Written and published in Muscat",
        "aboutlbl": "Who publishes this", "aboutname": "AI Profit Lab",
        "abouttext": ("AI Profit Lab builds WhatsApp AI agents, bilingual storefronts and live "
                      "dashboards for trading, distribution and service businesses in Oman and the "
                      "wider Gulf. If a number in this article does not match your business, send "
                      "yours and we will run it with you."),
        "askme": "Ask a question on WhatsApp", "moreabout": "About AI Profit Lab",
        "cta_head": "Want this running in your business?",
        "cta_text": ("Send one message and describe what your team handles by hand today. "
                     "You will get a straight answer about whether automation is worth it "
                     "for you &mdash; and what it would cost."),
        "cta_label": "Message us on WhatsApp",
        "cta_wa": "Hello%20Nahid%2C%20I%20read%20one%20of%20your%20articles%20and%20have%20a%20question.",
        "wa_intro": "Hello%20Nahid%2C%20I%20have%20a%20question%20about%20my%20business.",
        "f_work": "The work", "f_talk": "Talk to us",
        "f_links": [("What I build", "services"), ("How it works", "process"),
                    ("Articles", "blog"), ("Revenue leak simulator", "sim"),
                    ("WhatsApp demo", "demo"), ("Dashboard demo", "dash")],
        "f_direct": [("Contact page", "contact"), ("About", "about"), ("Privacy", "privacy")],
        "review_k": "Worked with us?", "review_t": "Leave a review on Google Maps",
        "follow": "Follow the work",
        "slogan": 'Every success starts with <span class="ins">insight</span>.',
        "legal": ('&copy; 2026 AI Profit Lab &mdash; a brand of Lotus Gulf International '
                  '(CR <span dir="ltr">1570092</span>)<br>South Al Khuwair, Bousher, Muscat, '
                  'Oman &middot; Not VAT registered (TIN <span dir="ltr">2317725</span>)'),
        "months": ["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"],
    },
    "ar": {
        # Kept identical to kit.NAV_AR - an article header and a core-page
        # header are the same component and must name the same pages the same
        # way. First person singular, for the reason given there.
        "nav": [("الرئيسية", "home", "٠١"), ("ما أبنيه", "services", "٠٢"),
                ("طريقة العمل", "process", "٠٣"), ("من أنا", "about", "٠٤"),
                ("تواصل معي", "contact", "٠٥"), ("المقالات", "blog", "٠٦")],
        "other_lang": "English", "whatsapp": "واتساب",
        "skip": "تخطَّ إلى المحتوى", "menu": "فتح القائمة",
        "crumb_home": "الرئيسية", "crumb_blog": "المقالات", "article": "مقال",
        "onpage": "في هذه الصفحة", "allposts": "كل المقالات",
        "questions": "أسئلة يطرحها القُرّاء", "sources": "المصادر",
        "keepreading": "اقرأ أيضاً", "read": "اقرأ &larr;",
        "minread": "دقائق قراءة", "published": "نُشر", "updated": "حُدّث",
        "share_wa": "شارك على واتساب", "share_li": "شارك على لينكدإن", "copy": "نسخ الرابط",
        "copied": "تم نسخ الرابط", "by": "AI Profit Lab", "byrole": "يُكتب ويُنشر في مسقط",
        "aboutlbl": "الجهة الناشرة", "aboutname": "AI Profit Lab",
        "abouttext": ("نبني في AI Profit Lab وكلاء واتساب بالذكاء الاصطناعي، ومواقع ثنائية اللغة، "
                      "ولوحات متابعة حيّة لشركات التجارة والتوزيع والخدمات في عُمان والخليج. "
                      "إذا لم تنطبق أرقام هذا المقال على نشاطك، أرسل لنا أرقامك ونحسبها معك."),
        "askme": "اسألنا مباشرة على واتساب", "moreabout": "عن AI Profit Lab",
        "cta_head": "تريد تشغيل هذا في شركتك؟",
        "cta_text": ("أرسل رسالة واحدة تصف فيها ما يقوم به فريقك يدوياً اليوم، وستحصل على إجابة "
                     "صريحة: هل الأتمتة مجدية لك، وكم تكلفتها."),
        "cta_label": "راسلنا على واتساب",
        "cta_wa": "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%D8%8C%20%D9%82%D8%B1%D8%A3%D8%AA%20"
                  "%D8%A3%D8%AD%D8%AF%20%D9%85%D9%82%D8%A7%D9%84%D8%A7%D8%AA%D9%83%D9%85"
                  "%20%D9%88%D9%84%D8%AF%D9%8A%20%D8%B3%D8%A4%D8%A7%D9%84.",
        "wa_intro": "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%D8%8C%20%D9%84%D8%AF%D9%8A%20"
                    "%D8%B3%D8%A4%D8%A7%D9%84%20%D8%B9%D9%86%20%D8%B9%D9%85%D9%84%D9%8A.",
        "f_work": "ما أقدّمه", "f_talk": "تواصل معي",
        "f_links": [("ما أبنيه", "services"), ("طريقة العمل", "process"),
                    ("المقالات", "blog"), ("حاسبة الإيرادات الضائعة", "sim"),
                    ("تجربة واتساب", "demo"), ("تجربة لوحة المتابعة", "dash")],
        "f_direct": [("صفحة التواصل", "contact"), ("عن ناهد", "about"), ("الخصوصية", "privacy")],
        "review_k": "تعاملت معي؟", "review_t": "اترك تقييماً على خرائط جوجل",
        "follow": "تابع العمل",
        "slogan": 'كل نجاح يبدأ <span class="ins">برؤية</span>',
        "legal": ('&copy; 2026 AI Profit Lab &mdash; علامة تجارية تابعة لشركة Lotus Gulf International '
                  '(س.ت <span dir="ltr">1570092</span>)<br>الخوير الجنوبية، بوشر، مسقط، سلطنة عُمان '
                  '&middot; غير مسجّلة لضريبة القيمة المضافة (الرقم الضريبي <span dir="ltr">2317725</span>)'),
        "months": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو",
                   "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    },
}

FONTS_EN = ("https://fonts.googleapis.com/css2?family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600;700"
            "&family=IBM+Plex+Mono:wght@400;500&display=swap")
FONTS_AR = ("https://fonts.googleapis.com/css2?family=Marcellus&family=Markazi+Text:wght@400;500;600"
            "&family=IBM+Plex+Sans+Arabic:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap")


def fmt_date(iso, lang):
    """2026-08-19 -> '19 August 2026' / '19 أغسطس 2026'. Empty in, empty out."""
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        return "%d %s %d" % (d, T[lang]["months"][m - 1], y)
    except Exception:
        return ""


# --------------------------------------------------------------------------
# Extra CSS: components the migration produces that the v4 kit does not yet
# have a rule for, plus the Arabic/RTL layer.
# --------------------------------------------------------------------------
MIGRATED_CSS = """
/* Panels lifted from the old skin keep their heading, so a callout has to
   style one. `article_kit` only ever emitted a mono <b> label. */
.callout h3,.callout h4{
  font-family:var(--display);font-weight:400;line-height:1.25;
  font-size:clamp(1.08rem,1.7vw,1.28rem);color:var(--teal-950);margin:0 0 12px;
}
.callout ul,.callout ol{margin:0}
.callout li{font-size:1rem;line-height:1.6}
.callout li:last-child{margin-bottom:0}
.callout p:last-child,.callout ul:last-child,.callout ol:last-child{margin-bottom:0}
.callout .callout{background:var(--panel-2);margin:18px 0}

/* YouTube embeds: 16:9 box so the iframe cannot set the page's width. */
.embed{
  position:relative;padding-top:56.25%;margin:clamp(30px,3.6vw,44px) 0;
  border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--panel-2);
}
.embed iframe{position:absolute;inset:0;width:100%;height:100%;border:0}

/* In-prose figures carry no caption in the migrated set - the old pages put
   their captions in the surrounding paragraph. */
.pfig img{background:var(--panel-2)}

/* The article footer: brand block in place of the personal byline, because
   every one of these pages declares an Organization as its schema author. */
.brandbox{
  display:grid;grid-template-columns:64px 1fr;gap:clamp(16px,2.4vw,24px);align-items:start;
  background:var(--panel-2);border-radius:16px;padding:clamp(22px,3vw,32px);margin-top:clamp(40px,5vw,60px);
}
.brandbox .bmark{width:64px;height:64px;border-radius:14px;background:var(--teal-950);
  display:flex;align-items:center;justify-content:center;padding:11px}
.brandbox .bmark img{width:100%;height:auto}
.brandbox .rolelbl{font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;
  color:var(--amber-text);margin:0 0 8px}
.brandbox h3{font-size:clamp(1.2rem,2vw,1.45rem);margin:0 0 10px}
.brandbox p{font-size:.99rem;color:var(--muted);margin:0 0 18px;line-height:1.62}

/* Byline mark stands in for the portrait in `article_kit`. */
.byline .bymark{width:42px;height:42px;border-radius:11px;background:var(--teal-950);flex:none;
  display:flex;align-items:center;justify-content:center;padding:8px}
.byline .bymark img{width:100%;height:auto}

/* The keyword row: the page's own <meta name="keywords">, shown as topic
   chips. They are the article's declared subjects, so they double as the
   entity list an answer engine reads off the page. */
.topics{display:flex;flex-wrap:wrap;gap:9px;margin:clamp(34px,4vw,48px) 0 0;padding-top:24px;border-top:1px solid var(--line)}
.topics span:first-child{font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;
  text-transform:uppercase;color:var(--muted);align-self:center;margin-right:4px}
.topics b{font-weight:400;font-size:.86rem;color:var(--teal-900);background:var(--panel);
  border:1px solid var(--line);border-radius:99px;padding:5px 13px}

/* .faq is a <section>, so it inherits the site's section padding - which puts
   a 138px chasm between its own border-top hairline and its heading. On the
   marketing pages that padding separates full-bleed bands; here it separates
   two blocks inside one column. */
.faq{padding:clamp(26px,3.2vw,38px) 0 0}
.faq>h2{margin-bottom:clamp(8px,1.4vw,16px)}

/* Long machine-generated headings need a lower ceiling than the v4 hero. */
.ahero .h1{font-size:clamp(1.85rem,3.9vw,3rem)}
"""

RTL_CSS = RTL_BASE + """
/* ------------------------------------------- article-specific RTL layer */
/* The tokens, the type scale and the tracking kill-list above come from
   tools/v4/rtl.py, which the core pages load too - one copy, so the article
   header and the services header cannot end up on different Arabic faces.
   What follows is only what an ARTICLE has and a core page does not. */
[dir=rtl] body{line-height:1.85}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3,[dir=rtl] h4{letter-spacing:0}
[dir=rtl] .h1,[dir=rtl] .ahero .h1{font-size:clamp(2rem,4.3vw,3.2rem);line-height:1.3}
[dir=rtl] .h2,[dir=rtl] .prose h2{line-height:1.35}
[dir=rtl] .prose h2{font-size:clamp(1.7rem,3.1vw,2.4rem)}
[dir=rtl] .prose h3{font-size:clamp(1.3rem,2.1vw,1.55rem);line-height:1.4}
[dir=rtl] .prose p{line-height:1.9}
[dir=rtl] .prose blockquote p{line-height:1.6}
[dir=rtl] .faq summary{line-height:1.5}
[dir=rtl] .callout h3,[dir=rtl] .callout h4{line-height:1.45}

/* Tracking and small-caps are Latin devices; on Arabic they break the join
   between letters and leave a label unreadable. */
[dir=rtl] .eyebrow,[dir=rtl] .crumbs,[dir=rtl] .toc h2,[dir=rtl] .keybox h4,
[dir=rtl] .callout b,[dir=rtl] .refs h2,[dir=rtl] .tblcap,[dir=rtl] .tbl th,
[dir=rtl] .byline .who span,[dir=rtl] .byline .stamp,[dir=rtl] .steps b,
[dir=rtl] .related .card .rd,[dir=rtl] .related .card .n,[dir=rtl] .pfig figcaption,
[dir=rtl] .afig figcaption,[dir=rtl] .brandbox .rolelbl,[dir=rtl] .topics span:first-child,
[dir=rtl] .lnk,[dir=rtl] .top-wa,[dir=rtl] .btn,[dir=rtl] .chip,
[dir=rtl] .pager .pl,[dir=rtl] .foot h4,[dir=rtl] .soc-h,[dir=rtl] .rk,[dir=rtl] .rt,
[dir=rtl] .legal,[dir=rtl] .mfoot,[dir=rtl] .mmenu a{
  letter-spacing:0;text-transform:none;
}

/* ------------------------------------------------------------ mirroring */
[dir=rtl] .prog{left:auto;right:0}
[dir=rtl] .skip{left:auto;right:-9999px;border-radius:0 0 0 8px}
[dir=rtl] .skip:focus{left:auto;right:0}

[dir=rtl] .prose p.open::first-letter{float:right;padding:.06em 0 0 .12em}
[dir=rtl] .prose li{padding-left:0;padding-right:30px}
[dir=rtl] .prose ul>li::before{left:auto;right:6px}
[dir=rtl] .prose ol>li::before{left:auto;right:0}
[dir=rtl] .prose blockquote{padding:0 clamp(20px,3vw,30px) 0 0;border-left:0;border-right:2px solid var(--amber)}

[dir=rtl] .keybox{border-left:0;border-right:3px solid var(--amber);border-radius:14px 0 0 14px}
[dir=rtl] .keybox li{padding-left:0;padding-right:26px}
[dir=rtl] .keybox li::before{left:auto;right:0}

[dir=rtl] .toc a{padding:8px 15px 8px 0;border-left:0;border-right:1px solid var(--line)}
[dir=rtl] .toc a.on{border-left-color:transparent;border-right-color:var(--amber)}

[dir=rtl] .tbl th{text-align:right}
[dir=rtl] .tblcap,[dir=rtl] .pfig figcaption,[dir=rtl] .afig figcaption{
  padding-left:0;padding-right:16px;border-left:0;border-right:2px solid var(--amber);
}
[dir=rtl] .afig figcaption{padding-right:14px}

[dir=rtl] .refs li{padding-left:0;padding-right:32px}
[dir=rtl] .refs li::before{left:auto;right:0}

[dir=rtl] .faq summary{padding:20px 0 20px 44px}
[dir=rtl] .faq summary::after{right:auto;left:8px}
[dir=rtl] .faq summary::before{right:auto;left:14px}
[dir=rtl] .faq details p{padding-right:0;padding-left:44px}

[dir=rtl] .icta::after{right:auto;left:-40px}
[dir=rtl] .topics span:first-child{margin-right:0;margin-left:4px}

/* Figures, prices, phone numbers and code stay left-to-right inside Arabic
   running text; without this "OMR 1,023" comes out reversed. */
[dir=rtl] .num,[dir=rtl] .tbl td.n,[dir=rtl] .formula span,[dir=rtl] .prose code{
  direction:ltr;unicode-bidi:embed;text-align:right;
}

/* ---------------------------------------------- footer signature, mirrored */
/* On an Arabic page the two lines swap roles: .slogan carries the Arabic and
   .slogan-ar carries the English echo. The amber stroke follows the Latin word
   rather than staying on .slogan, because under Arabic it cuts through the
   descenders and the join. The frame itself needs no override - .fsig is built
   on logical properties and mirrors on its own. */
[dir=rtl] .foot .slogan .ins::after{content:none}
/* .slogan-ar carries Latin here, so it drops the Arabic fallback stack and
   takes Marcellus - which these pages already load for the wordmark - instead
   of rendering the English echo in a Naskh face. */
[dir=rtl] .foot .slogan-ar{font-family:'Marcellus',Georgia,'Times New Roman',serif}
[dir=rtl] .foot .slogan-ar .ins{display:inline-block;position:relative;white-space:nowrap}
[dir=rtl] .foot .slogan-ar .ins::after{
  content:"";position:absolute;left:-.04em;right:-.04em;bottom:-.12em;
  height:4px;border-radius:3px;
  background:linear-gradient(90deg,rgba(216,146,52,.85),rgba(216,146,52,.22));
  transition:background .45s var(--ease);
}
[dir=rtl] .fsig:hover .slogan-ar .ins::after{background:linear-gradient(90deg,var(--amber-bright),var(--amber-bright))}
/* the beat fades away from the inline-start edge, which is the right one here */
[dir=rtl] .fsig .sig-beat{background:linear-gradient(270deg,rgba(232,201,143,.6),rgba(232,201,143,0))}
"""


def stylesheet():
    """The one stylesheet every migrated article links. Order matters: tokens,
    then the shared v4 design system, then the article system, then the
    components the migration introduces, then the RTL layer last so it wins."""
    return TOKENS + SKIP_CSS + BASE_CSS + ARTICLE_CSS + MIGRATED_CSS + RTL_CSS


# --------------------------------------------------------------------------
# Head
# --------------------------------------------------------------------------
def _esc(s):
    """Normalise, then escape. The source pages mix raw characters with named
    entities in the same attribute ("Ma&rsquo;een AI, Oman LLM"); escaping
    those directly would double-encode the ampersand and publish the literal
    text "Ma&rsquo;een". Unescaping first makes the output independent of how
    the original happened to be written."""
    return _html.escape(_html.unescape(s or ""), quote=True)


def head(doc, og_image, css_href, js_href=None):
    """The <head> for one migrated article."""
    lang = "ar" if doc["lang"].startswith("ar") else "en"
    t = T[lang]
    direction = "rtl" if lang == "ar" else "ltr"
    fonts = FONTS_AR if lang == "ar" else FONTS_EN
    url = doc["canonical"] or ""

    alts = "\n".join(
        '<link rel="alternate" hreflang="%s" href="%s">' % (_esc(h), _esc(u))
        for h, u in doc["hreflang"])

    ga = doc["ga"] or "G-SLR9GD3MJP"
    keywords = ('\n<meta name="keywords" content="%s">' % _esc(doc["keywords"])) if doc["keywords"] else ""
    cat = ('\n<meta name="category" content="%s">' % _esc(doc["category"])) if doc["category"] else ""
    schema = "\n".join('<script type="application/ld+json">\n%s\n</script>' % b for b in doc["jsonld"])

    return f"""<!DOCTYPE html>
<html dir="{direction}" lang="{_esc(doc["lang"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{_esc(doc["title"])}</title>
<meta name="description" content="{_esc(doc["desc"])}">{keywords}{cat}
<!-- Explicit and permissive: large image previews and uncapped snippets are
     what let this page surface as a rich result and be quoted in full by an
     answer engine. The old template shipped no robots tag at all. -->
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{_esc(url)}">
{alts}
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20260822">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260822">
<link rel="manifest" href="/site.webmanifest?v=20260822">

<meta property="og:type" content="article">
<meta property="og:site_name" content="AI Profit Lab">
<meta property="og:title" content="{_esc(doc["title"])}">
<meta property="og:description" content="{_esc(doc["desc"])}">
<meta property="og:url" content="{_esc(url)}">
<meta property="og:image" content="{_esc(og_image)}">
<meta property="og:locale" content="{'ar_OM' if lang == 'ar' else 'en_OM'}">
<meta property="article:published_time" content="{_esc(doc["date_iso"])}">
<meta property="article:publisher" content="https://www.facebook.com/profile.php?id=61584870364473">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{_esc(doc["title"])}">
<meta name="twitter:description" content="{_esc(doc["desc"])}">
<meta name="twitter:image" content="{_esc(og_image)}">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{fonts}">
<link rel="stylesheet" media="print" onload="this.media='all'" href="{fonts}">
<noscript><link rel="stylesheet" href="{fonts}"></noscript>
<!-- One stylesheet, shared by all 300 articles. The filename carries a content
     hash, which is what makes the host's `immutable, max-age=31536000` rule on
     /assets/** safe here: an edited stylesheet ships under a new name instead
     of sitting behind a year-long cache on a stale one. -->
<link rel="stylesheet" href="{css_href}">
<script>document.documentElement.className+=" js"</script>

<!-- Google tag (gtag.js) -->
<script defer src="{js_href}"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{ga}');</script>

{schema}
</head>
<body>
<a class="skip" href="#main">{t["skip"]}</a>
"""


# --------------------------------------------------------------------------
# Header / footer
# --------------------------------------------------------------------------
def header(lang):
    t, u = T[lang], URLS[lang]
    links = "\n    ".join('<a class="lnk" href="%s">%s</a>' % (u[key], label)
                          for label, key, _ in t["nav"][1:])
    other_lang = 'ar' if lang == 'en' else 'en'
    menu = "\n  ".join('<a href="%s"><em>%s</em>%s</a>' % (u[key], n, label)
                       for label, key, n in t["nav"])
    return f"""<header class="top" id="top">
  <a href="{u["home"]}" aria-label="AI Profit Lab">
    <img class="mark" src="/assets/brand/wordmark-primary.svg" alt="AI Profit Lab" width="160" height="28">
  </a>
  <nav class="nav" aria-label="Primary">
    {links}
    <a class="lnk" href="{u["other"]}" lang="{other_lang}">{t["other_lang"]}</a>
    <a class="top-wa" href="{WA}&text={t["wa_intro"]}" target="_blank" rel="noopener" aria-label="{t["whatsapp"]}">{WA_ICON}<span>{t["whatsapp"]}</span></a>
    <button class="burger" id="burger" aria-label="{t["menu"]}" aria-expanded="false" aria-controls="mmenu"><i></i></button>
  </nav>
</header>
<div class="mmenu" id="mmenu" aria-hidden="true">
  {menu}
  <a href="{u["other"]}" lang="{other_lang}"><em>07</em>{t["other_lang"]}</a>
  <p class="mfoot">hello@aiprofitlab.io &middot; <span dir="ltr">+968 9924 5250</span><br>Muscat, Oman</p>
</div>
"""


def footer(lang):
    t, u = T[lang], URLS[lang]
    work = "\n          ".join('<li><a href="%s">%s</a></li>' % (u[key], label)
                               for label, key in t["f_links"])
    direct = "\n          ".join('<li><a href="%s">%s</a></li>' % (u[key], label)
                                 for label, key in t["f_direct"])
    slogan_other = ('<p class="slogan-ar" lang="ar" dir="rtl">&#1603;&#1604; &#1606;&#1580;&#1575;&#1581; '
                    '&#1610;&#1576;&#1583;&#1571; <span class="ins">&#1576;&#1585;&#1572;&#1610;&#1577;</span></p>'
                    if lang == "en" else
                    '<p class="slogan-ar" lang="en" dir="ltr">Every success starts with '
                    '<span class="ins">insight</span>.</p>')
    return f"""<footer class="foot">
  <div class="wrap">
    <div class="foot-grid">

      <div class="foot-brand">
        <img class="fmark" src="/assets/brand/wordmark-reversed.svg" alt="AI Profit Lab" width="170" height="29">
        <div class="fsig">
          <p class="slogan">{t["slogan"]}</p>
          <span class="sig-beat" aria-hidden="true"></span>
          {slogan_other}
        </div>
        <div class="soc-wrap">
          <h4 class="soc-h">{t["follow"]}</h4>
          <ul class="socials">
{_socials()}
          </ul>
        </div>
      </div>

      <nav class="fcol" aria-label="{t["f_work"]}">
        <h4>{t["f_work"]}</h4>
        <ul>
          {work}
        </ul>
      </nav>

      <nav class="fcol" aria-label="{t["f_talk"]}">
        <h4>{t["f_talk"]}</h4>
        <ul class="direct">
          <li><a href="{WA}&text={t["wa_intro"]}">{WA_SMALL}<span dir="ltr">+968 9924 5250</span></a></li>
          <li><a href="mailto:hello@aiprofitlab.io">{MAIL_ICON}hello@aiprofitlab.io</a></li>
        </ul>
        <ul>
          {direct}
        </ul>
      </nav>

    </div>

    <a class="review" href="{GOOGLE_REVIEW}" target="_blank" rel="noopener">
      <span class="gmark" aria-hidden="true">{GOOGLE_G}</span>
      <span class="rbody">
        <span class="stars" aria-hidden="true">{STAR_SVG * 5}</span>
        <span class="rk">{t["review_k"]}</span>
        <span class="rt">{t["review_t"]}</span>
      </span>
      <span class="rarw" aria-hidden="true">{'&larr;' if lang == 'ar' else '&rarr;'}</span>
    </a>

    <p class="legal">{t["legal"]}</p>
  </div>
</footer>
"""


# Re-exported so the driver does not need to import kit as well.
__all__ = ["URLS", "T", "head", "footer", "header", "fmt_date", "MIGRATED_CSS",
           "RTL_CSS", "WA", "WA_ICON", "STAR", "SOCIALS"]
