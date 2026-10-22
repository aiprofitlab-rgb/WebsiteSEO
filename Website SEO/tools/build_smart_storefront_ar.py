#!/usr/bin/env python3
"""
Build the Arabic Smart Storefront page.

    python3 tools/build_smart_storefront_ar.py

    public_html/en/smart-storefront.html   ->   public_html/smart-storefront-ar.html
                /en/smart-storefront/                    /smart-storefront-ar/

The Arabic page is NOT a translated copy of the English file. It reads the
English page's <style> block at build time and appends an `[dir=rtl]` override
layer, exactly the way tools/v4/rtl.py serves the nine v4 pages: the design
lives in ONE place, so a tweak to a card, a button or the phone mock lands on
both languages, and only the declarations that genuinely name a physical side
are restated. Re-run this script after any CSS edit to the English page.

What this file owns is strings - the copy and the JS message table - plus the
handful of glyphs whose reading direction matters (the arrows). The section
order follows the English page, which since 2026-10-22 is the simple page for
visitors arriving from a Google search: what it is, the guarantee, what you
get, proof, the receipt, seats, how it works, questions, the form.

The page holds no prices. Like its English twin it renders whatever the
storefront ledger returns from /status and shows an explicit "the live count
isn't loading" panel if that call fails; see the smart-storefront-offer-stack
note. The pledge board is gated behind ?pledges=open by the same script.

Arabic a native reader has not yet passed is listed in UNREVIEWED below, and
every build renders that list to build/smart-storefront-ar-review.html for the
reviewer.

The URL follows the site's existing Arabic convention (kit.PAGES_AR): a root
`<name>-ar.html` served at `/<name>-ar/` by .htaccess rule 5, so no rewrite
rule is needed.
"""
import html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import aiden_version  # noqa: E402
import analytics_version  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "public_html" / "en" / "smart-storefront.html"
OUT = ROOT / "public_html" / "smart-storefront-ar.html"
REVIEW = ROOT / "build" / "smart-storefront-ar-review.html"

EN_URL = "https://aiprofitlab.io/en/smart-storefront/"
AR_URL = "https://aiprofitlab.io/smart-storefront-ar/"

# Every WhatsApp link on the page opens with the same greeting: "مرحباً ناهد"
# (kit.py wa_short), "لدي سؤال عن" (wa_intro) and "الموقع الذكي" from the
# page's own copy, all three already reviewed. The English page words its hero
# link differently from its header; which button was tapped is data-wa's job,
# not the message's.
WA_HREF = ("https://api.whatsapp.com/send?phone=96899245250&amp;text="
           "%D9%85%D8%B1%D8%AD%D8%A8%D8%A7%D9%8B%20%D9%86%D8%A7%D9%87%D8%AF%D8%8C%20"
           "%D9%84%D8%AF%D9%8A%20%D8%B3%D8%A4%D8%A7%D9%84%20%D8%B9%D9%86%20"
           "%D8%A7%D9%84%D9%85%D9%88%D9%82%D8%B9%20%D8%A7%D9%84%D8%B0%D9%83%D9%8A.")

WA_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 '
           '12 2zm0 1.8a8.2 8.2 0 1 1-4.2 15.3l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 0 1 12 3.8zm-3.1 4c-.2 0-.5 '
           '0-.7.3-.2.3-.9.9-.9 2.1s.9 2.4 1 2.6c.1.2 1.8 2.8 4.4 3.8 2.2.9 2.6.7 3.1.7.5-.1 1.5-.6 1.7-1.2.2-.6.2'
           '-1.1.1-1.2-.1-.1-.2-.2-.5-.3l-1.7-.8c-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.1'
           '-.2 0-.4.1-.5l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5L10 8.2c-.2-.4-.4-.4-.6-.4h-.5z"/></svg>')


# ══════════════════════════════════════════════════════════════════════════
# The RTL layer. Appended AFTER the English page's own CSS, so every rule
# here wins on a specificity tie without a single !important.
#
# Three kinds of rule, in this order:
#   1. TYPE   - the Arabic stack, its fallback metrics, and the sizes that
#               have to move because Markazi Text sets visibly smaller than
#               Marcellus at the same px.
#   2. BIDI   - the isolation that keeps a figure, a time or a price from
#               being reordered inside Arabic running text.
#   3. MIRROR - the declarations that name a physical side. Short by design.
# ══════════════════════════════════════════════════════════════════════════
RTL_CSS = r"""
/* ══════════════════ 1. TYPE ══════════════════ */
/* Fallback metrics, lifted from tools/v4/rtl.py where they were measured out
   of the actual font files. Without them the Arabic page shifts on font swap
   and the byte-identical English one does not: Markazi Text's x-height is
   36.4% of its em against Geeza Pro's 49.1%, so every Arabic heading paints a
   third too large in the fallback and snaps down when the webfont lands. */
@font-face{
  font-family:'Markazi Fallback';src:local('Geeza Pro');
  size-adjust:74.2%;ascent-override:113.1%;descent-override:48.7%;line-gap-override:0%;
}
@font-face{
  font-family:'Markazi Fallback 2';src:local('Tahoma'),local('Segoe UI');
  size-adjust:66.8%;ascent-override:125.6%;descent-override:54.1%;line-gap-override:0%;
}
@font-face{
  font-family:'Plex Arabic Fallback';src:local('Geeza Pro');
  size-adjust:105.1%;ascent-override:103.2%;descent-override:39.5%;line-gap-override:0%;
}
@font-face{
  font-family:'Plex Arabic Fallback 2';src:local('Tahoma'),local('Segoe UI');
  size-adjust:94.6%;ascent-override:114.7%;descent-override:43.9%;line-gap-override:0%;
}

[dir=rtl]{
  --display:'Markazi Text','Markazi Fallback','Markazi Fallback 2','Amiri',Georgia,serif;
  --sans:'IBM Plex Sans Arabic','Plex Arabic Fallback','Plex Arabic Fallback 2','IBM Plex Sans',-apple-system,'Segoe UI',sans-serif;
  --mono:'IBM Plex Mono','IBM Plex Sans Arabic','Plex Arabic Fallback',ui-monospace,SFMono-Regular,Menlo,monospace;
}
/* Naskh needs more leading than Latin at the same size: the descenders and the
   dots below the baseline collide at 1.65. */
[dir=rtl] body{line-height:1.85}
[dir=rtl] h1,[dir=rtl] h2,[dir=rtl] h3{letter-spacing:0;line-height:1.32}
[dir=rtl] .hero h1{font-size:clamp(2.3rem,6vw,3.9rem);line-height:1.26}
[dir=rtl] h2{font-size:clamp(1.9rem,4.4vw,2.7rem)}
[dir=rtl] h3{font-size:1.1rem}
/* The two h3s set in the display face. `[dir=rtl] h3` above ties them on
   specificity and comes later, so without these they fall to 1.1rem of
   Markazi, which reads as a caption rather than a heading. */
[dir=rtl] .steps h3{font-size:1.55rem}
[dir=rtl] .notinc h3{font-size:1.6rem}
[dir=rtl] .hero .sub,[dir=rtl] .lede{line-height:1.85}
[dir=rtl] .vow q{font-size:clamp(1.25rem,2.7vw,1.6rem);line-height:1.6}
[dir=rtl] .sig{font-size:1.2rem}
[dir=rtl] .sc-sold{font-size:1.7rem}
[dir=rtl] .sticky .info b{font-size:1.15rem}

/* Tracking and small-caps are Latin devices. letter-spacing on Arabic breaks
   the join between letters - it does not look airy, it makes the word
   unreadable - and text-transform does nothing at all. Both come off
   everywhere the English sheet sets them on a string that is now Arabic.
   .nav-lang and .ptag are deliberately absent: both still carry Latin. */
[dir=rtl] .eyebrow,[dir=rtl] .btn,[dir=rtl] .nav-cta,
[dir=rtl] .sc-badge,[dir=rtl] .sc-cell .k,[dir=rtl] .sc-sold,
[dir=rtl] .sticky .seats,[dir=rtl] .sigsub,[dir=rtl] .field label,[dir=rtl] .pfoot,
[dir=rtl] .card .go,[dir=rtl] .steps li::before,
[dir=rtl] .smenu a em,[dir=rtl] .smenu .mfoot{
  letter-spacing:0;text-transform:none;
}
/* The hero's price line and the proof cards' link text are mono in English,
   at .8rem and under. Plex Mono has no Arabic, so those words fell through to
   the fallback at a size Arabic cannot be read at. They move to the sans a
   size up. The price goes with them: in mono, "ر.ع." took Plex Mono's
   full-width space and full-width full stops and printed as "249  ر . ع ." */
[dir=rtl] .hero-simple .hero-price{font-family:var(--sans);font-size:.95rem;letter-spacing:0}
[dir=rtl] .hero-simple .hero-price b{font-size:1.15rem;font-weight:600;font-variant-numeric:tabular-nums}
[dir=rtl] .card .go{font-family:var(--sans);font-size:.92rem}
/* The steps count in the same Arabic-Indic digits as the site menu (٠١ ٠٢
   ٠٣). Plex Mono has none, so the numbers take the menu's size bump too. */
[dir=rtl] .steps li::before{content:"٠" counter(step,arabic-indic);font-size:1rem}
/* The site menu. Markazi sets smaller than Marcellus at the same px, and
   Plex Mono has no Arabic-Indic digits, so the fallback draws the numbers
   tiny. The contact line leaves the mono stack because its Arabic words took
   Plex Mono's wide space between them. The toggle's line-height follows the
   Arabic body's 1.85 so it stands as tall as the links beside it. */
[dir=rtl] .smenu a{font-size:clamp(1.95rem,8vw,2.9rem);line-height:1.35}
[dir=rtl] .smenu a em{font-size:1rem}
[dir=rtl] .smenu .mfoot{font-family:var(--sans);font-size:.95rem}
[dir=rtl] .nav-menu{line-height:1.85}

/* The hero phone is 236px wide with type between 8 and 19px. Arabic needs a
   step up at every one of those sizes to stay legible, and Markazi needs two.
   Everything here is a size, never a layout. */
[dir=rtl] .pbody .pht{font-size:16.5px;line-height:1.35}
[dir=rtl] .pchip{font-size:9px}
[dir=rtl] .pbtn{font-size:10px}
[dir=rtl] .pfoot{font-size:9px}
[dir=rtl] .bub{font-size:10px;line-height:1.6}
[dir=rtl] .bub.ar{font-size:10.5px}
[dir=rtl] .ptoast{font-size:9.5px}
/* The hero phone is a fixed 412px box with overflow:hidden, and .pbody is
   flex:none in the English sheet - taller Arabic copy would push the demo
   conversation straight out of the bottom of the handset. Letting the body
   shrink clips inside itself instead, which is the failure worth having. */
[dir=rtl] .phone .pbody{flex:0 1 auto;min-height:0;overflow:hidden}

/* ══════════════════ 2. BIDI ══════════════════ */
/* Figures, prices, times and phone numbers stay left-to-right inside Arabic
   running text. isolate, NOT embed: under `embed` the Latin run still takes
   part in the surrounding reorder, so a figure at the start of a box gets
   thrown to the far edge and the Arabic closes up behind it.

   The size/colour resets are not cosmetic. `.ltr` is a <span>, and it lands
   inside components whose caption rule is an unscoped descendant selector -
   `.sc-count span` (1.06rem, flex:1) and `.pledge .txt span` (.86rem, muted).
   Those are (0,1,1) and would beat a bare `.ltr`; this is (0,2,0) and wins.
   Everything is inherit-or-off, so a figure takes the size and colour of
   whatever it sits in. */
[dir=rtl] .ltr,[dir=rtl] [dir=ltr]{direction:ltr;unicode-bidi:isolate}
[dir=rtl] .ltr{
  display:inline;margin:0;flex:none;
  font-size:inherit;line-height:inherit;color:inherit;
  letter-spacing:0;text-transform:none;font-weight:inherit;
}

/* ══════════════════ 3. MIRROR ══════════════════ */
[dir=rtl] .brand{margin-right:0;margin-left:auto}
[dir=rtl] .ptop b{margin-right:0;margin-left:auto}
/* The demo thread carries BOTH languages on purpose - answering an Arabic
   buyer and an English one in the same thread is the whole illustration. */
[dir=rtl] .bub.en{direction:ltr;text-align:left}
/* "Grow from the reader's starting edge" - which is the right one here. */
[dir=rtl] .card::before{transform-origin:100% 50%}
[dir=rtl] .mrow b{transform-origin:left center}
[dir=rtl] .vow{border-left:1px solid var(--line);border-right:3px solid var(--amber);border-radius:16px 0 0 16px}
[dir=rtl] .seatbar i,[dir=rtl] .sc-pips i.open{background:linear-gradient(270deg,var(--amber-bright),var(--amber-pale))}
[dir=rtl] .pledge:hover{transform:translateX(-4px)}
/* The receipt. Its value column has to sit on the reader's FAR edge, which is
   the left one here: `margin-left:auto` absorbs the slack on the wrong side in
   RTL and shunts every price back against its own label. The mobile rule below
   it is the wrapped invoice row, where `justify-content` is already
   direction-aware and needs nothing said about it. */
[dir=rtl] .vs-val{margin-left:0;margin-right:auto}
[dir=rtl] .vs-row.core{background:linear-gradient(260deg,rgba(15,110,86,.10),rgba(15,110,86,.02))}
/* The FAQ's +/x marker and the room reserved for it, and the bullet indent
   on "what's not included". All three name a physical side in the English
   sheet, so the marker would sit on top of the question's first word. */
[dir=rtl] .faq summary{padding:18px 0 18px 36px}
[dir=rtl] .faq summary::after{right:auto;left:4px}
[dir=rtl] .notinc ul{padding-left:0;padding-right:1.1em}
[dir=rtl] .hp{left:auto;right:-9999px}
/* The select's chevron is a background image, and `background-position:right`
   is not direction-aware the way padding and margin are - left alone it lands
   on top of the last letter of the Arabic option. The padding that reserved
   room for it travels with it. */
[dir=rtl] .field select{background-position:left 13px center;padding-right:13px;padding-left:36px}
[dir=rtl] .sticky .info{margin-right:0;margin-left:auto}

/* The .nav-lang switch is NOT restated here. It is defined once in the English
   stylesheet, which this file carries over whole, and it is one of the HOOKS
   below so a rename over there fails the build rather than silently dropping
   the Arabic reader's way back to English. */
"""


# ══════════════════════════════════════════════════════════════════════════
# HEAD. Same tags as the English page, plus the reciprocal hreflang pair and
# the Arabic font stack. The pledge gate, GA4, Clarity and the analytics
# bundle are copied verbatim so both languages report into one property.
# ══════════════════════════════════════════════════════════════════════════
HEAD = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover"/>
<!-- "تصميم موقع الكتروني" is the phrase Oman searches most in Arabic for this
     (about 70 a month, 2026-10-22), spelled the way people type it, without
     the hamza. -->
<title>تصميم موقع الكتروني في عُمان، بالعربية والإنجليزية — AI Profit Lab</title>
<meta name="description" content="موقع الكتروني لنشاطك التجاري في عُمان، بالعربية والإنجليزية. يرد على المشترين في أي ساعة، وياخذ الجادّين منهم إلى برنامج الواتساب. السعر لمرة واحدة، وسنة استضافة ورعاية مشمولة، وجاهز خلال أسبوع تقريباً."/>
<!-- Mirrors the English page's robots value; indexable since 2026-08-27. -->
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1"/>
<meta name="author" content="AI Profit Lab"/>
<meta name="theme-color" content="#0A3D30"/>

<link rel="canonical" href="__AR_URL__"/>
<link rel="alternate" hreflang="ar" href="__AR_URL__"/>
<link rel="alternate" hreflang="en" href="__EN_URL__"/>
<link rel="alternate" hreflang="x-default" href="__EN_URL__"/>

<meta property="og:title" content="تصميم موقع الكتروني في عُمان، بالعربية والإنجليزية — AI Profit Lab"/>
<meta property="og:description" content="موقع يرد على المشترين في أي ساعة، وياخذ الجادّين منهم إلى برنامج الواتساب. السعر لمرة واحدة، وجاهز خلال أسبوع تقريباً."/>
<meta property="og:url" content="__AR_URL__"/>
<meta property="og:type" content="website"/>
<meta property="og:locale" content="ar_OM"/>
<meta property="og:locale:alternate" content="en_US"/>
<meta property="og:image" content="https://aiprofitlab.io/og-aiprofitlab-2026-v2.jpg"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:type" content="image/jpeg"/>
<meta property="og:image:alt" content="ناهيد آبياري، مؤسس AI Profit Lab — أتمتة بالذكاء الاصطناعي لشركات الخليج"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:image" content="https://aiprofitlab.io/og-aiprofitlab-2026-v2.jpg"/>

<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20260822">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260822">
<link rel="manifest" href="/site.webmanifest?v=20260822">

<script>document.documentElement.className += " js";</script>

<!-- ══ pledge gate ══
     Identical to the English page's, and it reads the SAME localStorage key,
     so a link handed out in one language opens the board in the other too.
     The "Four ways to pay less" board is hidden from every visitor by
     default, so the published price is the price. Open the page with
     ?pledges=open and the board appears, and stays open on that browser until
     ?pledges=off puts it away again. Change UNLOCK below to change the link. -->
<script>
(function(){
  var UNLOCK = "open", KEY = "apl_pledges", ON = " pledges-on";
  var m = /[?&]pledges=([^&#]+)/.exec(location.search);
  var v = m ? decodeURIComponent(m[1]).toLowerCase() : null;
  try {
    if (v === UNLOCK)      localStorage.setItem(KEY, "1");
    else if (v === "off")  localStorage.removeItem(KEY);
    if (localStorage.getItem(KEY) === "1") document.documentElement.className += ON;
  } catch (e) {
    // private mode / storage blocked — the link still works, it just won't stick
    if (v === UNLOCK) document.documentElement.className += ON;
  }
})();
</script>

<!-- Campaign normaliser - must stay above the gtag snippet, which reads
     location.search when it fires the page_view. The printed flyer's QR
     carries ?utm_source=flyer and no medium, and GA4 files a session with no
     medium under "Unassigned". Only ADDS missing keys. Mirrors the block in
     the English page; keep the two tables identical. -->
<script>
  (function () {
    try {
      var q = new URLSearchParams(location.search);
      var src = (q.get("utm_source") || "").trim().toLowerCase();
      if (!src) return;
      var DEFAULTS = { flyer: ["print", "smart_storefront_launch"] };
      var d = DEFAULTS[src];
      if (!d) return;
      var changed = false;
      if (!q.get("utm_medium")) { q.set("utm_medium", d[0]); changed = true; }
      if (!q.get("utm_campaign")) { q.set("utm_campaign", d[1]); changed = true; }
      if (changed && window.history && history.replaceState) {
        history.replaceState(null, "", location.pathname + "?" + q.toString() + location.hash);
      }
    } catch (e) { }
  })();
</script>

<script async src="https://www.googletagmanager.com/gtag/js?id=G-SLR9GD3MJP"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-SLR9GD3MJP');
</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- Non-blocking font load, matching the v4 pattern in tools/v4/kit.py. The
     Arabic set: Markazi Text display, IBM Plex Sans Arabic body, IBM Plex Mono
     figures. No Marcellus: the English sheet reaches it only through
     --display, which the RTL layer replaces, and the flyer's Latin wordmark
     that once needed it left with the flyer. -->
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" media="print" onload="this.media='all'" href="https://fonts.googleapis.com/css2?family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"></noscript>

<style>
__CSS__
</style>
<!-- Microsoft Clarity -->
<script>(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","y7wcjlyamc");</script>
__ANALYTICS_TAG__
</head>
"""


# ══════════════════════════════════════════════════════════════════════════
# BODY. Same components, same section order and the same figures as the
# English page - only the strings and the direction-carrying glyphs change.
#
# Voice: first person singular, matching the rest of the Arabic site
# (tools/v4/ar/*). "نحن" would contradict the one claim the guarantee makes.
# Where a line had already been through the native reader and the English
# beside it kept its meaning, the reviewed Arabic stays word for word,
# including the reviewer's own spellings ("الالكتروني", "ياخذ").
# ══════════════════════════════════════════════════════════════════════════
BODY = r"""<body>

<nav>
  <div class="nav-in">
    <a class="brand" href="/ar/" aria-label="AI Profit Lab — الصفحة الرئيسية">
      <img src="/en/logo/wordmark-cream.svg" alt="AI Profit Lab" width="158" height="27"/>
    </a>
    <a class="nav-lang" href="__EN_PATH__" hreflang="en" lang="en">English</a>
    <a class="top-wa" data-wa="header" href="__WA__" target="_blank" rel="noopener" aria-label="راسل ناهد على واتساب">__WA_ICON__<span>واتساب</span></a>
    <a class="nav-cta" href="#claim">احجز مقعدك</a>
    <button class="nav-menu" id="navMenu" type="button" aria-expanded="false" aria-controls="smenu"><i aria-hidden="true"></i><span>القائمة</span></button>
  </div>
</nav>

<!-- Every Arabic label below is lifted from the live, reviewed site chrome
     (tools/v4/kit.py NAV_AR and CHROME["ar"]), not translated here. The
     free-tools row is absent because those pages are English-only. -->
<div class="smenu" id="smenu" hidden>
  <div class="smenu-in">
    <a href="/ar/"><em>٠١</em>الرئيسية</a>
    <a href="/services/"><em>٠٢</em>ما أبنيه</a>
    <a href="/process/"><em>٠٣</em>طريقة العمل</a>
    <a href="/about/"><em>٠٤</em>من أنا</a>
    <a href="/contact/"><em>٠٥</em>تواصل معي</a>
    <a href="/blog-ar/"><em>٠٦</em>المقالات</a>
    <p class="mfoot"><span dir="ltr">hello@aiprofitlab.io</span> · <span dir="ltr">+968 9924 5250</span><br>مسقط، سلطنة عُمان</p>
  </div>
</div>

__MENU_JS__

<!-- ═══ 1. WHAT IT IS ═══
     Written for a stranger arriving from a search, like the English hero:
     the words they searched, the price, and two ways in. The price is the
     ledger's, written into #hPrice by the script below. It is never typed
     here. -->
<header class="hero hero-simple">
  <div class="stars" id="stars" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow"><span class="star">✼</span> تصميم مواقع الكترونية · مسقط، سلطنة عُمان</p>
      <h1>موقع الكتروني لنشاطك التجاري في عُمان، بالعربية والإنجليزية.</h1>
      <p class="sub">يرد على المشترين في أي ساعة، وياخذ الجادّين منهم مباشرة إلى برنامج الواتساب. جاهز خلال أسبوع تقريباً.</p>
      <p class="hero-price">السعر لمرة واحدة <b id="hPrice"><span class="skel" style="min-width:4.6em"></span></b><br>
        سنة استضافة ورعاية مشمولة · بِلا اشتراك شهري</p>

      <div class="hero-ctas">
        <a class="btn btn-wa" data-wa="hero" href="__WA__" target="_blank" rel="noopener">__WA_ICON__اسألني على واتساب</a>
        <a class="btn btn-outline" href="#claim">احجز مقعداً</a>
      </div>
      <p class="hero-ig"><a href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener">شاهد نماذج من المواقع على إنستغرام ↖</a></p>
    </div>

    <div class="stage" id="stage">
      <div class="phone on" id="phone" role="img" aria-label="هاتف يعرض موقعاً ثنائي اللغة لنشاط تجاري: بالعربية والإنجليزية، فيه زر طلب تسعيرة بالجملة، وزر واتساب، ومحادثة مع مشترٍ، وتنبيه باستفسار جديد.">
        <div class="pscreen">
          <div class="ptop"><b>اسم شركتك</b><span class="ptag">AR</span><span class="ptag">EN</span></div>
          <div class="pbody">
            <div class="pht">نُورّد في عُمان، منذ يوم بدأت.</div>
            <div class="pchips"><span class="pchip">أسعار الجملة</span><span class="pchip">التوصيل</span><span class="pchip">بيانات المنتجات</span></div>
            <div class="pbtn">اطلب تسعيرة بالجملة</div>
            <div class="pbtn wa">تحدّث على واتساب</div>
            <div class="pfoot">يرد بالعربية والإنجليزية · <span class="ltr">24/7</span></div>
          </div>
          <div class="pconv">
            <div class="bub ar d-ar">مرحباً! تحتاج تسعيرة بالجملة؟</div>
            <div class="bub d-type"><i></i><i></i><i></i></div>
            <div class="bub en d-en">Yes — 400 bags, delivered to Sohar.</div>
          </div>
          <div class="ptoast">استفسار جديد ← إلى هاتفك</div>
        </div>
      </div>
    </div>
  </div>
</header>

<!-- ═══ 2. THE GUARANTEE, AND THE FACE BEHIND IT ═══ -->
<section>
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ضمان الاستفسار الأولي</p>
    <div class="vow rv">
      <picture>
        <source srcset="/nahid-founder-seated-2026.webp" type="image/webp"/>
        <img src="/nahid-founder-seated-2026.jpg" alt="ناهيد آبياري، مؤسس AI Profit Lab" width="200" height="235" decoding="async"/>
      </picture>
      <div>
        <q>إن لم يصلك استفسار حقيقي من مشتري خلال 30 يوماً من إطلاق الموقع؟ أُعيد بناءه مجاناً حتى يصلك واحد. وإن لم يصلك بعدها، تسترد مبلغك المالي</q>
        <p class="sig">— ناهيد أبياري</p>
        <p class="sigsub">مؤسس AI Profit Lab</p>
      </div>
    </div>
  </div>
</section>

<!-- ═══ 3. WHAT YOU GET ═══ -->
<section class="band">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ما الذي سوف تحصل عليه</p>
    <h2 class="rv">يبيع وأنت نائم. وإليك كيف.</h2>
    <div class="grid3" style="margin-top:34px">
      <div class="card rv"><span class="ic">🕐</span><h3>يرد على المشترين في أي ساعة</h3><p>وكيل ذكاء اصطناعي ثنائي اللغة يرد على المشترين في الرابعة فجراً، ويوم الجمعة، وفي العيد.</p></div>
      <div class="card rv"><span class="ic">📲</span><h3>المشترون الجادّون يصلون إلى واتساب</h3><p>حين يكون أحدهم جاهزاً للطلب، تصل المحادثة إلى هاتفك.</p></div>
      <div class="card rv"><span class="ic">📋</span><h3>طلبات تسعيرة بالجملة</h3><p>نموذج تسعيرة حقيقي لمشتري الجملة، لا صندوق «اتصل بنا» عادي.</p></div>
      <div class="card rv"><span class="ic">👀</span><h3>اعرف من هو على وشك الشراء</h3><p>ملخّص قصير عمّن زار وماذا سأل، يصل إلى هاتفك.</p></div>
      <div class="card rv"><span class="ic">🔎</span><h3>يظهر في جوجل وفي ChatGPT</h3><p>يظهر للبحث التقليدي ولإجابات الذكاء الاصطناعي معاً.</p></div>
      <div class="card rv"><span class="ic">🛠️</span><h3>لا يطلب صيانة</h3><p>السنة الأولى من الاستضافة والحماية والرعاية، مشمولة.</p></div>
    </div>
  </div>
</section>

<!-- ═══ 3b. PROOF ═══
     There are no client testimonials to show yet, so the proof is the work
     itself: the sample sites on the brand's Instagram, and the live demo -
     the Arabic one, whose heading this card's title is lifted from. -->
<section id="work">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> تحقّق قبل أن تدفع</p>
    <h2 class="rv">شاهد أعمالي أولاً.</h2>
    <div class="proof">
      <a class="card rv" href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener"><span class="ic">📸</span>
        <h3>نماذج مواقع على إنستغرام</h3>
        <p>مواقع صمّمتُها، منشورة على حساب <span class="ltr">@ai.profit.lab.gcc</span>.</p>
        <span class="go">افتح إنستغرام ↖</span>
      </a>
      <a class="card rv" href="/demos-ar/"><span class="ic">▶️</span>
        <h3>شاهده يردّ على مشترٍ</h3>
        <p>مشترٍ يسأل عن التوفّر والسعر بعد ساعات العمل. شاهد بالضبط ما يفعله وكيل المشتري.</p>
        <span class="go">شاهد التجربة ←</span>
      </a>
    </div>
  </div>
</section>

<!-- ═══ 4b. THE RECEIPT ═══
     The value stack. Same structure and the same figures as the English page -
     the ten rows sum to OMR 949 and split as 249 + 700 at the launch rung -
     because the ledger it reads from is the same ledger, and a buyer switching
     languages mid-scroll has to land on the same offer.

     ARABIC: the values are written the way money() writes it below, figure
     first and currency after, so the static rows and the three live ones read
     as one column. The minus on the gift row needs no wrapper. U+2212 only
     folds into a number run when it sits BETWEEN two of them (bidi W4), and
     here it leads, so it resolves as a neutral and takes the paragraph's RTL
     level - which parks it at the right-hand end of the cell, the first thing
     an Arabic reader meets. Measured, not assumed: right to left the cell
     reads minus, 700, ر.ع. It is set tight against the digits only so the two
     scan as one figure.

     The footnote is empty, as it is on the English page. -->
<section class="vs-sec" id="value">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ما الذي يشتريه المبلغ فعلاً</p>
    <h2 class="rv">أنت تدفع ثمن الموقع. والباقي هديّة إطلاق الموقع حالياً.</h2>
    <p class="lede rv">اسأل أي وكالة في مسقط كم يكلّف بناء موقع ثنائي اللغة. ثم اقرأ الأسطر التسعة تحته — تلك التي لا يحاسبك عليها أحد.</p>

    <div class="vs rv">
      <div class="vs-hd"><span>ما الذي يصلك</span><span>سعره المعتاد</span></div>

      <div class="vs-row core">
        <span class="vs-core-lbl">
          <b>موقع ثنائي اللغة، مُصمَّم ومبنيّ بالكامل</b>
          <span>صفحاتك، وكتالوجك، وشروطك. جاهز خلال أسبوع تقريباً.</span>
        </span>
        <span class="vs-val"><span class="vs-core-val" id="vsCore">—</span><span class="vs-pay-tag">هذا ما تدفعه</span></span>
      </div>

      <div class="vs-row" style="--i:0"><span class="vs-lbl">مُهيّأ ليُكتشَف في جوجل <em>وفي</em> ChatGPT</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:1"><span class="vs-lbl">نظام إدارة عملاء صغير مدمج، يحجز المواعيد ويوزّع المهام بحسب ما يجري في الموقع</span><span class="vs-val"><span class="vs-was">100 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:2"><span class="vs-lbl">وكيل مبيعات افتراضي يتحدّث إلى زوار موقعك ويعرّفهم بنشاطك</span><span class="vs-val"><span class="vs-was">100 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:3"><span class="vs-lbl">المشترون الجادّون يصلون مباشرة إلى واتساب</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:4"><span class="vs-lbl">شات بوت ذكي يجيب عن أي سؤال عن نشاطك، بأي لغة</span><span class="vs-val"><span class="vs-was">200 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:5"><span class="vs-lbl">ملف نشاطك على جوجل مُصحَّح ومُوثَّق</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:6"><span class="vs-lbl">فيديو مسجّل لتدريب موظّفينك</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:7"><span class="vs-lbl">استضافة اثني عشر شهراً</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:8"><span class="vs-lbl">ملاحظة عمّن زار موقعك، ومن أي البلدان، وماذا سأل</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>

      <div class="vs-tot">
        <div class="vs-trow"><span class="lbl">كل ما سبق، <a href="/services/">بسعره المعتاد</a></span><b>949 ر.ع.</b></div>
        <div class="vs-trow gift"><span class="lbl">هديّة الإطلاق</span><b id="vsGift">—</b></div>
        <div class="vs-trow pay"><span class="lbl">تدفع اليوم</span><b id="vsPay">—</b></div>
      </div>
    </div>

    <p class="vs-foot rv"></p>
  </div>
</section>

<!-- ═══ 5. SCARCITY ═══ -->
<section class="scarcity" id="ladder">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> السعر يرتفع كلما امتلأت المقاعد</p>
    <h2 class="rv">المقاعد المتبقية بسعر اليوم:</h2>

    <div class="offline" id="ladderOffline">
      <strong>العدّاد المباشر لا يُحمّل الآن.</strong>
      أُفضّل ألا أعرض لك شيئاً على أن أعرض رقماً اختلقته. <a data-wa="ladder" href="https://api.whatsapp.com/send?phone=96899245250" target="_blank" rel="noopener">اسألني على واتساب</a>.
    </div>

    <div class="scard rv" id="ladderList">
      <div class="sc-badge"><i></i> أقرأ السجل</div>
      <div class="sc-count"><b><span class="skel" style="min-width:1.1em"></span></b><span>مقاعد متبقية بهذا السعر</span></div>
      <div class="sc-pips"><i></i><i></i><i></i></div>
    </div>

    <p class="sc-note rv"> المقاعد محدودة لسعر المعروض عليك دفع عربون ٥٠٪ حالياً لحجز المقعد</p>
  </div>
</section>

<!-- ═══ 6. PLEDGES ═══ -->
<section id="pledges">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ادفع أقل، لاحقاً</p>
    <h2 class="rv">أربع طرق لتدفع أقل.</h2>
    <p class="lede rv" style="margin-bottom:22px">أشِّر على ما ستفعله فعلاً <em>بعد</em> أن يصبح موقعك جاهزاً. كل واحدة تُعاد إليك — لا يُخصم شيء مقدماً، ولا يُسترد شيء إن غيّرت رأيك.</p>
    <p class="tapme rv">لكل واحدة قيمة مختلفة. انقر واحدة لتعرف. ↓</p>

    <div class="pledges rv" id="pledgeList"></div>

    <div class="maths rv" id="maths">
      <div class="mrow"><span class="lbl">سعرك اليوم</span><b id="mPrice">—</b></div>
      <div class="mrow"><span class="lbl">ما يعود إليك بعد أن تفي</span><b id="mRebate">0.00 ر.ع.</b></div>
      <div class="mrow total"><span class="lbl">ما ينتهي به الأمر أن يكلّفك</span><b id="mNet">—</b></div>
      <div class="allfour" id="allFour">
        الأربع كلها — نصف السعر يعود إليك. الآن، شهادة حقيقية من موزّع حقيقي أثمن عندي من الهامش.
      </div>
    </div>

  </div>
</section>

<!-- ═══ 6b. HOW IT WORKS ═══
     The timeline is the one terms-ar.html section 5 publishes, and most of
     the wording is lifted from it; the payment split is the one the proforma
     prints (deposit now, balance on delivery). -->
<section class="band" id="how">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> طريقة العمل</p>
    <h2 class="rv">ثلاث خطوات. أسبوع تقريباً.</h2>
    <ol class="steps">
      <li class="rv">
        <h3>احجز مقعدك</h3>
        <p>املأ النموذج القصير أدناه. تصلك فاتورتك بالبريد، وعربون 50% بالبطاقة أو بالتحويل البنكي يحفظ لك سعر اليوم.</p>
      </li>
      <li class="rv">
        <h3>حدّثني عن نشاطك</h3>
        <p>مكالمة قصيرة، ثم ترسل منتجاتك وأسعارك، ومعها شعارك وصورك إن كانت لديك.</p>
      </li>
      <li class="rv">
        <h3>تطّلع عليه في اليوم الثالث، ويُطلَق في اليوم السابع</h3>
        <p>يصلك رابط تطّلع عليه في اليوم الثالث، مع جولة تعديلات واحدة مشمولة. ويُطلَق الموقع في اليوم السابع، ويُدفع النصف الآخر عند التسليم.</p>
      </li>
    </ol>
    <p class="steps-note rv">اليوم الأول هو يوم اعتماد ملخص متطلباتك، لا يوم دفعك.</p>
  </div>
</section>

<!-- ═══ 6c. QUESTIONS, AND WHAT IS NOT INCLUDED ═══
     Every answer is the English page's, which lifts them from terms.html
     (sections 5, 8 and 9) and the refund policy. The Arabic is lifted the same
     way from terms-ar.html and refund-policy-ar.html, moved from their "we"
     into this page's "I". Change the terms first, then both pages. -->
<section id="faq">
  <div class="wrap narrow">
    <p class="eyebrow rv"><span class="star">✼</span> أسئلة</p>
    <h2 class="rv">إجابات مباشرة.</h2>
    <div class="faq rv">
      <details>
        <summary>من يملك الموقع؟</summary>
        <p>أنت. عند سداد كامل المبلغ، تملك الموقع ومحتواه والحسابات التي يعمل من خلالها، وهي مسجّلة باسمك حيثما تسمح المنصّة بذلك. ويمكنك نقله أو تعديله أو تسليمه لشخص آخر.</p>
      </details>
      <details>
        <summary>ماذا يحدث بعد السنة الأولى؟</summary>
        <p>السنة الأولى من الاستضافة والرعاية مشمولة. وبعد تلك السنة تصبح اختيارية وتُسعَّر على حدة. ولا يتوقف موقعك عن العمل لأنك رفضتها.</p>
      </details>
      <details>
        <summary>لديّ موقع بالفعل. هل تستطيع استبداله؟</summary>
        <p>نعم. يُطلَق الموقع الجديد على نطاقك أنت، أو على عنوان مؤقت أولاً إن لم يكن نطاقك جاهزاً.</p>
      </details>
      <details>
        <summary>ماذا لو لم يتواصل معي أي مشترٍ؟</summary>
        <p>إن لم يصلك استفسار حقيقي من مشتري خلال 30 يوماً من إطلاق الموقع، أُعيد بناءه مجاناً حتى يصلك واحد. وإن لم يصلك بعدها، تسترد مبلغك المالي.</p>
      </details>
      <details>
        <summary>هل أحتاج إلى أي معرفة تقنية؟</summary>
        <p>لا. ترسل منتجاتك وأسعارك وصورك، وأنا أبنيه، ويحصل فريقك على فيديو مسجّل يشرح طريقة عمله.</p>
      </details>
      <details>
        <summary>كيف أدفع؟</summary>
        <p>النصف الآن، بالبطاقة أو بالتحويل البنكي، لحجز مقعدك. والنصف الآخر عند التسليم. والمبلغ المدوَّن في الفاتورة هو المبلغ الذي تدفعه: لا تُضاف إليه ضريبة القيمة المضافة. وطريقة الاسترداد موضّحة في <a href="/refund-policy-ar/">سياسة الاسترجاع</a>.</p>
      </details>
    </div>

    <div class="notinc rv">
      <h3>ما لا يشمله السعر</h3>
      <ul>
        <li>اسم النطاق، إن لم يكن لديك واحد بعد. أستأذنك قبل شرائه، وأُطلعك على الإيصال.</li>
        <li>الاستضافة والرعاية بعد السنة الأولى. اختيارية، وتُسعَّر على حدة.</li>
        <li>الخدمات المدفوعة لدى أطراف ثالثة. إن احتجنا إلى واحدة، تُخبَر قبل استخدامها ويكون الحساب باسمك.</li>
        <li>أكثر من جولة تعديلات واحدة في أسبوع الإطلاق.</li>
        <li>الإضافات: لوحة المعلومات الحيّة لصاحب العمل، والتشغيل الآلي الكامل. تُبنى بعد إطلاق الموقع وتُباع على حدة.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ═══ 7. CLAIM FORM ═══ -->
<section class="roast" id="claim">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> احجز مقعداً</p>
    <h2 class="rv">احجز مقعدك بسعر اليوم.</h2>
    <p class="lede rv" style="margin-bottom:28px">سبعة حقول قصيرة. تصلك فاتورتك بالبريد، وتدفع عربون 50% بالبطاقة أو بالتحويل البنكي. أما التفاصيل الكاملة فتأتي بعد ذلك.</p>

    <form class="form rv" id="claimForm" novalidate>
      <div class="fsummary">
        السعر اليوم: <b id="fPrice">—</b> · عربون 50% لحجز مقعد: <b id="fDeposit">—</b> <span class="pledge-only">· ما يعود إليك: <b id="fRebate">0.00 ر.ع.</b></span>
        <div class="pledge-only-b" style="color:var(--muted);font-size:.85rem;margin-top:5px">غيّر تعهداتك في <a href="#pledges">القسم أعلاه</a>.</div>
      </div>

      <div class="fgrid">
        <div class="field"><label for="f-name">اسمك</label><input id="f-name" name="name" autocomplete="name" required/></div>
        <div class="field"><label for="f-business">اسم النشاط التجاري</label><input id="f-business" name="business" autocomplete="organization" required/></div>
        <div class="field full"><label for="f-sector">ماذا تبيع؟</label><input id="f-sector" name="sector" placeholder="مثلاً: مواد بناء، مستلزمات طبية، قطع غيار" required/></div>
        <!-- dir=ltr on the three Latin-content fields. A leading "+" is a bidi
             neutral: inside an RTL field "+968" is typed and stored correctly
             but renders as "968+", and an email reads back reordered. -->
        <div class="field"><label for="f-whatsapp">رقم واتساب</label><input id="f-whatsapp" name="whatsapp" type="tel" inputmode="tel" autocomplete="tel" dir="ltr" placeholder="+968 …" required/></div>
        <div class="field"><label for="f-email">البريد الإلكتروني</label><input id="f-email" name="email" type="email" inputmode="email" autocomplete="email" dir="ltr" required/></div>
        <div class="field full"><label for="f-site">موقعك الالكتروني الحالي <span class="opt-tag">— اختياري </span></label><input id="f-site" name="currentSite" dir="ltr" placeholder="لا يوجد"/></div>
        <!-- The self-reported half of attribution. The VALUES here are the same
             stable ids the English page posts, so an Arabic claim and an English
             one are one channel in the ledger rather than two. Keep this list
             identical to public_html/en/smart-storefront.html and to LABELS in
             the API's lib/heard.js - only the labels are translated.
             No dir=ltr on the ChatGPT row: it is Latin at the START of an
             otherwise Arabic string, which base RTL already places on the
             reader's first edge. -->
        <div class="field full"><label for="f-heard">كيف سمعت عنّا؟</label>
          <select id="f-heard" name="heard" required>
            <option value="" selected disabled>اختر واحداً…</option>
            <option value="flyer">منشور مطبوع</option>
            <option value="google">بحث في جوجل</option>
            <option value="ai">ChatGPT أو مساعد ذكاء اصطناعي آخر</option>
            <option value="instagram">إنستغرام</option>
            <option value="linkedin">لينكدإن</option>
            <option value="whatsapp">رسالة واتساب من ناهد</option>
            <option value="referral">أحدهم رشّحكم لي</option>
            <option value="inperson">التقيت بكم شخصياً</option>
            <option value="other">مكان آخر</option>
          </select>
        </div>
        <div class="field full" id="heardMore" hidden><label for="f-heard-detail" id="heardMoreLabel">من رشّحنا لك؟</label><input id="f-heard-detail" name="heardDetail" maxlength="200" placeholder="اختياري، لكنه يساعدني كثيراً."/></div>
      </div>

      <div class="hp" aria-hidden="true"><label for="f-companyurl">Company URL</label><input id="f-companyurl" name="companyUrl" tabindex="-1" autocomplete="off"/></div>

      <label class="consent"><input type="checkbox" id="f-consent" required/>
        <span>أوافق على أن تتواصل معي AI Profit Lab بخصوص هذا الحجز عبر البريد وواتساب، وأن تحفظ هذه البيانات لإعداد اتفاقي. لا شيء غير ذلك، ولا قوائم بريدية. <a href="/privacy-ar/" target="_blank" rel="noopener">الخصوصية</a>.</span>
      </label>

      <div class="formerr" id="formErr"></div>

      <p style="margin:20px 0 0"><button type="submit" class="btn btn-primary" id="fSubmit" style="width:100%">احجز لي مقعداً بهذا السعر</button></p>
      <p id="fPayNote" style="font-size:.84rem;color:var(--muted);margin:12px 0 0"></p>
    </form>
    <p class="alt-wa">تفضّل أن تسأل أولاً؟ <a data-wa="claim" href="__WA__" target="_blank" rel="noopener">راسلني على واتساب</a>.</p>
  </div>
</section>

<!-- ═══ 8. FOOTER ═══ -->
<footer>
  <div class="wrap footgrid">
    <div>
      <img class="foot-logo" src="/en/logo/wordmark-dark.svg" alt="AI Profit Lab" width="150" height="26" loading="lazy"/>
      <p style="margin:0">كل نجاح يبدأ برؤية.</p>
      <p class="foot-nav"><a href="/ar/">الرئيسية</a><a href="/services/">ما أبنيه</a><a href="/process/">طريقة العمل</a><a href="/blog-ar/">المقالات</a><a href="/about/">عن ناهد</a><a href="/contact/">صفحة التواصل</a></p>
      <p style="margin:10px 0 0;font-size:.8rem"><span class="ltr">© 2026 AI Profit Lab</span> — علامة تجارية تابعة لـ Lotus Gulf International (س.ت <span class="ltr">1570092</span>) · <a href="/refund-policy-ar/">سياسة الاسترجاع</a> · <a href="/privacy-ar/">الخصوصية</a></p>
    </div>
  </div>
</footer>

<div class="sticky">
  <div class="sticky-in">
    <div class="info">سعر اليوم<b id="sPrice">—</b></div>
    <span class="seats" id="sSeats"></span>
    <a class="btn btn-primary" href="#claim">احجز مقعداً</a>
  </div>
</div>
"""


# ══════════════════════════════════════════════════════════════════════════
# The page script. Structurally a line-for-line copy of the English page's -
# same functions, same order, same guards, same comments where they explain a
# bug that was paid for once already - so the two can be diffed. The strings
# are the difference, plus the Arabic-specific changes, each marked ARABIC:
# in place.
# ══════════════════════════════════════════════════════════════════════════
JS = r"""<script>
(function(){
  "use strict";
  var API = "https://offer.aiprofitlab.io";
  var WA  = "https://api.whatsapp.com/send?phone=96899245250";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Both languages report into one GA4 property, so every event carries the
  // language it happened in; without it an Arabic claim and an English one are
  // the same row.
  var track = function(name, params){
    if (!window.gtag) return;
    params = params || {};
    params.lang = "ar";
    gtag("event", name, params);
  };

  /* ARABIC: a figure, a time or a price sitting inside Arabic running text has
     to be isolated or the bidi algorithm reorders it - "2:14" reads as "14:2".
     In markup that is <span class="ltr">; in a textContent string it is a
     LRI/PDI pair, which needs no element. */
  function ltr(s){ return "⁦" + s + "⁩"; }

  /* ARABIC: Arabic counts in four shapes where English has two, and this is
     the loudest number on the page. 1 مقعد / 2 مقعدان / 3-10 مقاعد / 11+ مقعداً. */
  function seatsLeftPhrase(n){
    if (n === 1) return "مقعد متبقٍ";
    if (n === 2) return "مقعدان متبقيان";
    if (n >= 3 && n <= 10) return "مقاعد متبقية";
    return "مقعداً متبقياً";
  }
  function seatNoun(n){
    if (n === 1) return "مقعد";
    if (n === 2) return "مقعدين";
    if (n >= 3 && n <= 10) return "مقاعد";
    return "مقعداً";
  }

  /* ─────────── scroll reveal ─────────── */
  var revealables = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (!e.isIntersecting) return;
        e.target.classList.add("vis");
        io.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    revealables.forEach(function(el, i){ el.style.transitionDelay = (i % 6) * 45 + "ms"; io.observe(el); });
  } else {
    revealables.forEach(function(el){ el.classList.add("vis"); });
  }

  /* ─────────── drifting brand stars ─────────── */
  if (!reduce) {
    var starHTML = "";
    for (var s = 0; s < 9; s++) {
      starHTML += '<i style="left:' + (4 + Math.random() * 92).toFixed(1) + '%;' +
        'font-size:' + (10 + Math.random() * 20).toFixed(0) + 'px;' +
        'animation-duration:' + (16 + Math.random() * 18).toFixed(0) + 's;' +
        'animation-delay:-' + (Math.random() * 20).toFixed(0) + 's">✼</i>';
    }
    document.getElementById("stars").innerHTML = starHTML;
  }

  /* ─────────── confetti ─────────── */
  var COLORS = ["#D89234", "#0F6E56", "#E8C98F", "#BA7517"];
  function spawn(cls, x, y, style, life) {
    var n = document.createElement("i");
    n.className = cls;
    n.style.left = x + "px";
    n.style.top = y + "px";
    for (var k in style) n.style.setProperty(k, style[k]);
    document.body.appendChild(n);
    setTimeout(function(){ n.remove(); }, life);
    return n;
  }
  function confetti(el, count) {
    if (reduce || !el) return;
    var r = el.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    for (var i = 0; i < (count || 14); i++) {
      var c = spawn("confetti", cx, cy, {
        "--dx": ((Math.random() - 0.5) * 190).toFixed(0) + "px",
        "--dy": (60 + Math.random() * 190).toFixed(0) + "px",
        "--rot": (Math.random() * 720 - 360).toFixed(0) + "deg"
      }, 1800);
      c.style.background = COLORS[i % COLORS.length];
      c.style.animationDelay = (Math.random() * 0.12).toFixed(2) + "s";
    }
  }

  /* ─────────── rolling numbers ───────────
     Money is written directly, never interpolated. Counting the digits up made
     the displayed price depend on animation frames arriving on time, and they
     do not: requestAnimationFrame is paused in background tabs and its
     timestamp is not guaranteed to share a clock with performance.now().
     Testing on the English page caught a rebate of 1866 against a 249 price,
     and later a stale 49.80 next to a "0%" label. A wrong price on a page whose
     entire pitch is "these numbers are real" is not a trade worth making for a
     flourish, so the value is set instantly and only its container animates. */
  function bump(el, text) {
    if (el.textContent === text) return;
    el.textContent = text;
    if (reduce) return;
    el.classList.remove("bumped");
    void el.offsetWidth;                       // restart the animation on repeat changes
    el.classList.add("bumped");
  }

  /* ─────────── 1. WhatsApp taps, as a conversion ───────────
     apl-analytics.js already reports these as cta_click with cta_type
     "whatsapp". This page also sends whatsapp_click, one event name with
     nothing else in it, so GA4 can mark it as a key event and Google Ads can
     import it as a conversion. data-wa says which button. Same event, same
     locations as the English page; `lang` tells the two apart. */
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest ? e.target.closest('a[href*="whatsapp.com"], a[href*="wa.me"]') : null;
    if (a) track("whatsapp_click", { cta_location: a.getAttribute("data-wa") || "other" });
  }, true);

  /* The hero's price line. Same rule as every other figure here: it is
     whatever the ledger says, or an honest "ask me", never a typed number. */
  function heroPrice(text) {
    var el = document.getElementById("hPrice");
    if (el) el.textContent = text;
  }

  /* ─────────── 3. the ledger ─────────── */
  var state = null, chosen = [];
  var PLEDGES_ON = document.documentElement.className.indexOf("pledges-on") > -1;
  /* ARABIC: the currency follows the figure. The number is a European-number
     run and the base direction is RTL, so "249.00 ر.ع." is laid out with the
     digits on the right and the currency to their left - which is the order an
     Arabic reader reads it in. No wrapper needed on the figure itself. */
  var money = function(n){ return Number(n).toFixed(2) + " ر.ع."; };
  /* The receipt prints round riyals. A figure set in 3rem with ".00" hanging
     off it reads as a bill someone is about to argue with; the decimals stay
     everywhere a deposit can land on a half riyal. */
  var money0 = function(n){ n = Number(n); return (n % 1 ? n.toFixed(2) : n.toFixed(0)) + " ر.ع."; };

  /* The value stack's three live figures. VS_TOTAL is the sum of the ten
     printed rows and is deliberately NOT read from the ledger - it is the thing
     the ladder discounts against, so it has to hold still while the rung moves.
     Change a row's figure and change this with it. */
  var VS_TOTAL = 949;
  function paintReceipt(core, gift, pay) {
    var set = function(id, txt){ var el = document.getElementById(id); if (el) el.textContent = txt; };
    set("vsCore", core); set("vsGift", gift); set("vsPay", pay);
  }

  /* ARABIC: the ledger serves its pledge labels in English. Only the display
     strings are localised here - the id and the percentage stay the service's,
     exactly as the prices do - and anything the table does not know falls back
     to what the API sent, so a pledge added server-side renders in English
     rather than as a blank row. */
  var PLEDGE_AR = {
    testimonial: { label: "شهادة مصوّرة",
                   detail: "مصوّرة بهاتفك. دقيقتان، بكلماتك أنت، وبلا نص مني." },
    endorsement: { label: "توصية على لينكدإن وتقييم على خرائط جوجل",
                   detail: "كلاهما علني، وكلاهما باسمك." },
    social:      { label: "منشور واحد على حساباتك، بصيغة نتفق عليها",
                   detail: "ستستلم الصيغة جاهزة قبل أن تلتزم بها." },
    referral:    { label: "تعرّفني على صاحب نشاط آخر يطلب هو أيضاً",
                   detail: "تُحتسب عندما يطلب فعلاً — التعريف وحده لا يكفي." }
  };
  function pledgeText(p, field){
    var t = PLEDGE_AR[p.id];
    return (t && t[field]) || p[field];
  }

  function renderLadder() {
    var list = document.getElementById("ladderList");
    var stickySeats = document.getElementById("sSeats");
    if (state.soldOut) {
      list.innerHTML = '<div class="sc-badge"><i></i> مباشر من السجل</div>' +
        '<p class="sc-sold">كل المقاعد محجوزة.</p>' +
        '<p style="margin:0;color:rgba(241,239,232,.7)">راسلني وسأخبرك بصدق متى يُفتح المقعد التالي.</p>';
      document.getElementById("pledgeList").innerHTML = "";
      document.getElementById("maths").style.display = "none";
      document.getElementById("claimForm").style.display = "none";
      document.getElementById("sPrice").textContent = "نفدت المقاعد";
      heroPrice("نفدت المقاعد");
      paintReceipt("نفدت المقاعد", "—", "نفدت المقاعد");
      if (stickySeats) stickySeats.textContent = "نفدت المقاعد";
      return;
    }

    // One rung is live; the first one after it is the price this buyer pays by waiting.
    var live = null, next = null;
    state.published.forEach(function(r){
      if (!live) { if (r.state === "live") live = r; }
      else if (!next) next = r;
    });
    if (!live) live = state.published[0];

    list.innerHTML =
      '<div class="sc-badge"><i></i> مباشر من السجل</div>' +
      '<div class="sc-count"><b id="seatCount">0</b><span>' + seatsLeftPhrase(live.seatsLeft) +
        ' بهذا السعر</span></div>' +
      seatMeter(live) +
      '<div class="sc-prices">' +
        '<div class="sc-cell"><span class="k">اليوم</span><span class="v">' + live.price + ' ر.ع.</span></div>' +
        (next
          ? '<span class="sc-rise" aria-hidden="true">↖</span>' +
            '<div class="sc-cell then"><span class="k">بعد نفادها</span><span class="v">' + next.price + ' ر.ع.</span></div>'
          : "") +
      '</div>' +
      (state.moreRungsAfter ? '<p class="sc-after">…ويواصل الارتفاع بعدها.</p>' : "");

    if (stickySeats) {
      stickySeats.textContent = live.seatsLeft + " " + seatsLeftPhrase(live.seatsLeft);
    }

    // Count the seats up rather than snapping — it reads as a live reading, not a static label.
    var countEl = document.getElementById("seatCount"), bar = document.getElementById("seatBar");
    if (countEl) {
      if (reduce) { countEl.textContent = live.seatsLeft; }
      else {
        var n = 0;
        var tick = setInterval(function(){
          countEl.textContent = ++n;
          if (n >= live.seatsLeft) clearInterval(tick);
        }, Math.max(110, 480 / Math.max(1, live.seatsLeft)));
      }
    }
    // The bar shows capacity *remaining*, matching the "N seats left" framing above it —
    // it starts full and drains as seats sell, rather than sitting empty at launch.
    if (bar) setTimeout(function(){
      bar.style.width = Math.round((live.seatsLeft / live.seats) * 100) + "%";
    }, 140);
  }

  // One pip per seat in the tier, lit for the ones still open. Past a dozen seats the
  // pips get too thin to count, so fall back to the draining bar.
  function seatMeter(live) {
    var total = live.seats, left = live.seatsLeft;
    var label = "متبقٍ " + left + " من " + total + " " + seatNoun(total) + " بهذا السعر";
    if (total > 12) return '<div class="seatbar" role="img" aria-label="' + label + '"><i id="seatBar"></i></div>';
    var pips = "";
    for (var i = 0; i < total; i++) {
      pips += '<i class="' + (i < left ? "open" : "taken") + '" style="animation-delay:' + (i * 90) + 'ms"></i>';
    }
    return '<div class="sc-pips" role="img" aria-label="' + label + '">' + pips + '</div>';
  }

  function renderPledges() {
    document.getElementById("pledgeList").innerHTML = state.pledges.map(function(p){
      return '<label class="pledge" data-id="' + p.id + '">' +
        '<input type="checkbox" value="' + p.id + '"/>' +
        '<span class="txt"><b>' + pledgeText(p, "label") + '</b><span>' + pledgeText(p, "detail") + '</span></span>' +
        '<span class="pct hidden" data-pct="' + p.pct + '">؟</span></label>';
    }).join("");

    document.querySelectorAll(".pledge input").forEach(function(cb){
      cb.addEventListener("change", function(){
        var row = cb.closest(".pledge");
        row.classList.toggle("on", cb.checked);

        // The percentage is a surprise until it's tapped for. Once revealed it stays
        // revealed — re-hiding a number someone has already seen reads as a trick.
        var chip = row.querySelector(".pct");
        if (chip.classList.contains("hidden")) {
          chip.classList.remove("hidden");
          chip.classList.add("shown");
          chip.textContent = chip.getAttribute("data-pct") + "%";
          confetti(chip, 10);
          track("pledge_revealed", { pledge: cb.value });
        }

        chosen = Array.prototype.map.call(
          document.querySelectorAll(".pledge input:checked"), function(x){ return x.value; });
        track("pledge_toggle", { pledge: cb.value, on: cb.checked });
        renderMaths();
      });
    });
  }

  function renderMaths() {
    if (!state || !state.activeTier) return;
    var price = state.activeTier.price;
    var pct = state.pledges
      .filter(function(p){ return chosen.indexOf(p.id) > -1; })
      .reduce(function(sum, p){ return sum + p.pct; }, 0);
    var rebate = price * pct / 100;

    bump(document.getElementById("mPrice"), money(price));
    // The parenthetical is isolated: "(" and ")" are bidi neutrals and would
    // otherwise take their side from whatever ends up next to them.
    bump(document.getElementById("mRebate"), money(rebate) + (pct ? "  " + ltr("(" + pct + "%)") : ""));
    bump(document.getElementById("mNet"), money(price - rebate));

    var all = document.getElementById("allFour");
    if (pct >= 50 && !all.classList.contains("on")) confetti(all, 24);
    all.classList.toggle("on", pct >= 50);

    document.getElementById("fPrice").textContent   = money(price);
    document.getElementById("fDeposit").textContent = money(state.activeTier.deposit);
    document.getElementById("fRebate").textContent  = money(rebate);
    document.getElementById("sPrice").textContent   = money(price);
    heroPrice(money0(price));
    paintReceipt(money0(price), "−" + money0(VS_TOTAL - price), money0(price));
  }

  function ledgerOffline() {
    document.getElementById("ladderOffline").classList.add("on");
    document.getElementById("ladderList").style.display = "none";
    document.getElementById("pledgeList").innerHTML =
      '<p style="color:var(--muted)">لوحة التعهدات تحتاج السعر المباشر لتعرض لك أرقاماً حقيقية، وهي غير متاحة الآن. ' +
      '<a href="' + WA + '" target="_blank" rel="noopener">اسألني على واتساب</a> وسأشرحها لك.</p>';
    document.getElementById("maths").style.display = "none";
    document.getElementById("sPrice").textContent = "اسألني";
    heroPrice("اسألني على واتساب");
    paintReceipt("اسألني", "—", "اسألني");
    var stickySeats = document.getElementById("sSeats");
    if (stickySeats) stickySeats.textContent = "";
    document.getElementById("claimForm").style.display = "none";
  }

  fetch(API + "/status")
    .then(function(r){ if (!r.ok) throw new Error("status " + r.status); return r.json(); })
    .then(function(data){
      if (!data.ok) throw new Error("not ok");
      state = data;
      renderLadder();
      // Whether a card can be taken is the service's answer, never this page's guess —
      // same rule as the prices. Promising a card the gateway can't process would send
      // someone to a pay page with no pay button on it.
      if (data.pay && data.pay.card) {
        var note = document.getElementById("fPayNote");
        if (note) note.textContent = "تصلك فاتورتك بالبريد لحظة إتمام الطلب.";
      }
      // A sold-out ledger has already stripped the pledge board and the form; running
      // the maths afterwards would put a live price back into the sticky bar.
      if (!state.soldOut) { if (PLEDGES_ON) renderPledges(); renderMaths(); }
    })
    .catch(function(err){ console.warn("ledger unavailable:", err); ledgerOffline(); });

  /* ─────────── 5. the claim ─────────── */
  var form = document.getElementById("claimForm");
  var submitBtn = document.getElementById("fSubmit");
  var formErr = document.getElementById("formErr");

  /* "كيف سمعت عنّا؟" - two answers earn one more question, every other one
     closes it, and the box is emptied on the way out so a name typed under
     "أحدهم رشّحكم لي" cannot survive a change of mind and get filed under
     "بحث في جوجل". Identical behaviour to the English page. */
  var heardSel = document.getElementById("f-heard");
  var heardMore = document.getElementById("heardMore");
  var heardDetail = document.getElementById("f-heard-detail");
  heardSel.addEventListener("change", function(){
    var asks = heardSel.value === "referral" || heardSel.value === "other";
    if (asks) {
      document.getElementById("heardMoreLabel").textContent =
        heardSel.value === "referral" ? "من رشّحنا لك؟" : "أين صادفتنا؟";
    } else {
      heardDetail.value = "";
    }
    heardMore.hidden = !asks;
  });

  function fail(msg) {
    formErr.textContent = msg;
    formErr.classList.remove("on");
    void formErr.offsetWidth;           // restart the shake on repeated failures
    formErr.classList.add("on");
    submitBtn.disabled = false;
    submitBtn.textContent = "احجز لي مقعداً بهذا السعر";
  }

  form.addEventListener("submit", function(e){
    e.preventDefault();
    formErr.classList.remove("on");

    var payload = {
      name:        document.getElementById("f-name").value.trim(),
      business:    document.getElementById("f-business").value.trim(),
      sector:      document.getElementById("f-sector").value.trim(),
      whatsapp:    document.getElementById("f-whatsapp").value.trim(),
      email:       document.getElementById("f-email").value.trim(),
      currentSite: document.getElementById("f-site").value.trim(),
      // The id, never the label - the same ids the English page posts, so both
      // languages count as one channel in the ledger.
      heardAbout:  heardSel.value,
      heardDetail: heardDetail.value.trim(),
      companyUrl:  document.getElementById("f-companyurl").value.trim(),
      consent:     document.getElementById("f-consent").checked,
      pledges:     chosen,
      // Ignored by the service today (routes/claim.js reads a fixed key list),
      // and sent anyway so the row and the invoice can be told which language
      // the buyer arrived in the day that side speaks Arabic.
      lang: "ar"
    };

    if (!payload.name || !payload.business || !payload.sector || !payload.whatsapp || !payload.email) {
      return fail("بقيت حقول فارغة — الاسم، واسم النشاط، وما تبيعه، ورقم واتساب، والبريد، كلها لازمة لكتابة اتفاقك.");
    }
    if (!payload.heardAbout) {
      heardSel.focus();
      return fail("بقي سؤال واحد: كيف سمعت عنّا؟ هذه هي الطريقة الوحيدة لأعرف أيّاً مما أفعله يعمل فعلاً.");
    }
    if (!payload.consent) {
      return fail("أحتاج إذنك لحفظ هذه البيانات والتواصل معك، وإلا لا أستطيع إرسال اتفاق لك.");
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "أحجز مقعدك…";

    /* Attribution, identical in shape to the English page - the Arabic funnel
       has to be measurable as its own channel or there is no way to tell
       whether the translation is earning its keep. */
    if (window.APLPage && window.APLPage.attributionFields) {
      var attr = window.APLPage.attributionFields();
      for (var k in attr) { if (attr.hasOwnProperty(k)) payload[k] = attr[k]; }
    }

    function sendClaim() {
    fetch(API + "/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
      .then(function(r){ return r.json().then(function(body){ return { ok: r.ok, body: body }; }); })
      .then(function(res){
        if (!res.ok || !res.body.ok) {
          if (res.body && res.body.error === "sold_out") {
            return fail("نفدت كل المقاعد للتو. لن أدّعي غير ذلك — راسلني على واتساب وسأخبرك متى يُفتح المقعد التالي.");
          }
          return fail("حدث خطأ أثناء حفظ حجزك. وبدلاً من أن يضيع، راسلني على واتساب وسآخذ التفاصيل بنفسي.");
        }
        track("claim_submitted", { pledges: chosen.length });
        /* The Arabic seat page, built by tools/build_pay_ar.py. Until 2026-09-05
           this sent an Arabic buyer to /en/pay/ - the last screen before they
           pay, and the one that has to explain a 50% deposit, switched to a
           language they had not been reading for the previous ten minutes. */
        window.location.href = "/pay-ar/?ref=" + encodeURIComponent(res.body.ref) + "&new=1";
      })
      .catch(function(){
        fail("لم أستطع الوصول إلى الخادم. اتصالك أو خادمي — في الحالتين، راسلني على واتساب ولن يضيع شيء.");
      });
    }

    /* See the English page: gtag('get') is async and silent when blocked, so
       this resolves on a timer and the claim is never held up by it. */
    if (window.APLPage && window.APLPage.gaIds) {
      window.APLPage.gaIds(function (ids) {
        payload.gaClientId = ids.client_id;
        payload.gaSessionId = ids.session_id;
        sendClaim();
      }, 900);
    } else {
      sendClaim();
    }
  });
})();
</script>
    __AIDEN_TAG__
</body>
</html>
"""


# ══════════════════════════════════════════════════════════════════════════
# ARABIC THE NATIVE READER HAS NOT SEEN YET.
#
# Everything else on the page was on the live Arabic site when the reviewer
# went through it (2026-09-05) and is kept word for word. These lines arrived
# with the simple page on 2026-10-22. Each row is (section, the English it
# stands for, the Arabic on the page, where it came from). "new" means drafted
# here; the rest were built from reviewed Arabic and say from where.
#
# Every build renders this list to build/smart-storefront-ar-review.html and
# warns about any row whose Arabic is no longer on the page. When the reviewer
# corrects a line, edit BODY (or JS) and delete the row. When they pass one
# unchanged, delete the row.
# ══════════════════════════════════════════════════════════════════════════
UNREVIEWED = [
    ("نتائج البحث", "Website Design in Oman, in Arabic & English (page title)",
     "تصميم موقع الكتروني في عُمان، بالعربية والإنجليزية",
     "new; the search phrase as Oman types it"),
    ("نتائج البحث", "A website for your business in Oman, in Arabic and English. It answers buyers at any hour "
     "and sends the serious ones to your WhatsApp. One-time price, first year of hosting included, live in "
     "about a week. (search description)",
     "موقع الكتروني لنشاطك التجاري في عُمان، بالعربية والإنجليزية. يرد على المشترين في أي ساعة، وياخذ الجادّين "
     "منهم إلى برنامج الواتساب. السعر لمرة واحدة، وسنة استضافة ورعاية مشمولة، وجاهز خلال أسبوع تقريباً.",
     "built from reviewed phrases on this page"),
    ("نتائج البحث", "A website that answers your buyers at any hour and sends the serious ones to your "
     "WhatsApp. One-time price, live in about a week. (link preview)",
     "موقع يرد على المشترين في أي ساعة، وياخذ الجادّين منهم إلى برنامج الواتساب. السعر لمرة واحدة، وجاهز خلال "
     "أسبوع تقريباً.",
     "built from reviewed phrases on this page"),
    ("أعلى الصفحة", "Website design · Muscat, Oman",
     "تصميم مواقع الكترونية · مسقط، سلطنة عُمان", "new"),
    ("أعلى الصفحة", "A website for your Oman business, in Arabic and English.",
     "موقع الكتروني لنشاطك التجاري في عُمان، بالعربية والإنجليزية.", "new"),
    ("أعلى الصفحة", "It answers your buyers at any hour and sends the serious ones straight to your "
     "WhatsApp. Live in about a week.",
     "يرد على المشترين في أي ساعة، وياخذ الجادّين منهم مباشرة إلى برنامج الواتساب. جاهز خلال أسبوع تقريباً.",
     "built from the reviewed hero line and receipt"),
    ("أعلى الصفحة", "See sample websites on Instagram ↗",
     "شاهد نماذج من المواقع على إنستغرام ↖", "new"),
    ("أعلى الصفحة", "A phone showing a bilingual business website… (read aloud to blind visitors)",
     "هاتف يعرض موقعاً ثنائي اللغة لنشاط تجاري: بالعربية والإنجليزية، فيه زر طلب تسعيرة بالجملة، وزر واتساب، "
     "ومحادثة مع مشترٍ، وتنبيه باستفسار جديد.",
     "the reviewed label, with the flyer taken out"),
    ("الضمان", "Founder, AI Profit Lab (was “AI Profit Lab CEO”)",
     "مؤسس AI Profit Lab", "from the reviewed photo caption"),
    ("ما الذي سوف تحصل عليه", "It sells while you sleep. Here is how.",
     "يبيع وأنت نائم. وإليك كيف.", "first sentence is the reviewed old headline"),
    ("ما الذي سوف تحصل عليه", "Answers buyers at any hour",
     "يرد على المشترين في أي ساعة", "new"),
    ("ما الذي سوف تحصل عليه", "Serious buyers go to your WhatsApp",
     "المشترون الجادّون يصلون إلى واتساب", "from the reviewed receipt row"),
    ("ما الذي سوف تحصل عليه", "When someone is ready to order, the conversation lands on your phone.",
     "حين يكون أحدهم جاهزاً للطلب، تصل المحادثة إلى هاتفك.", "new"),
    ("ما الذي سوف تحصل عليه", "Bulk quote requests",
     "طلبات تسعيرة بالجملة", "new"),
    ("ما الذي سوف تحصل عليه", "A proper quote form for wholesale buyers, not a basic \"contact us\" box.",
     "نموذج تسعيرة حقيقي لمشتري الجملة، لا صندوق «اتصل بنا» عادي.", "adapted from the reviewed card"),
    ("ما الذي سوف تحصل عليه", "The first year of hosting, security and care is included.",
     "السنة الأولى من الاستضافة والحماية والرعاية، مشمولة.",
     "the reviewed card, “سنة كاملة” changed to “السنة الأولى”"),
    ("أعمالي", "Check before you pay", "تحقّق قبل أن تدفع", "new"),
    ("أعمالي", "See my work first.", "شاهد أعمالي أولاً.", "new"),
    ("أعمالي", "Sample websites on Instagram", "نماذج مواقع على إنستغرام", "new"),
    ("أعمالي", "Websites I've designed, posted at @ai.profit.lab.gcc.",
     "مواقع صمّمتُها، منشورة على حساب @ai.profit.lab.gcc.", "new"),
    ("أعمالي", "Open Instagram ↗", "افتح إنستغرام ↖", "new"),
    ("أعمالي", "A buyer asks for stock and a price after hours. See exactly what the assistant does.",
     "مشترٍ يسأل عن التوفّر والسعر بعد ساعات العمل. شاهد بالضبط ما يفعله وكيل المشتري.",
     "new; “وكيل المشتري” is the demo page's own name for it"),
    ("أعمالي", "Watch the demo →", "شاهد التجربة ←", "new"),
    ("طريقة العمل", "Three steps. About a week.", "ثلاث خطوات. أسبوع تقريباً.", "new"),
    ("طريقة العمل", "Fill in the short form below. Your invoice arrives by email, and a 50% deposit by card "
     "or bank transfer holds today's price.",
     "املأ النموذج القصير أدناه. تصلك فاتورتك بالبريد، وعربون 50% بالبطاقة أو بالتحويل البنكي يحفظ لك سعر اليوم.",
     "new"),
    ("طريقة العمل", "Tell me about your business", "حدّثني عن نشاطك", "new"),
    ("طريقة العمل", "A short call, then you send your products and prices, plus your logo and photos if you "
     "have them.",
     "مكالمة قصيرة، ثم ترسل منتجاتك وأسعارك، ومعها شعارك وصورك إن كانت لديك.", "terms-ar §6, adapted"),
    ("طريقة العمل", "Check it on day 3, live on day 7",
     "تطّلع عليه في اليوم الثالث، ويُطلَق في اليوم السابع", "terms-ar §5, adapted"),
    ("طريقة العمل", "You get a link to look at on day three, with one round of changes included. It goes "
     "live on day seven, and the other 50% is paid on delivery.",
     "يصلك رابط تطّلع عليه في اليوم الثالث، مع جولة تعديلات واحدة مشمولة. ويُطلَق الموقع في اليوم السابع، "
     "ويُدفع النصف الآخر عند التسليم.",
     "terms-ar §5, adapted"),
    ("طريقة العمل", "Day one is the day your brief is confirmed, not the day you pay.",
     "اليوم الأول هو يوم اعتماد ملخص متطلباتك، لا يوم دفعك.", "terms-ar §5"),
    ("أسئلة", "Questions", "أسئلة", "new"),
    ("أسئلة", "Straight answers.", "إجابات مباشرة.", "new"),
    ("أسئلة", "Who owns the website?", "من يملك الموقع؟", "new"),
    ("أسئلة", "You do. Once it's paid in full, the site, its content and the accounts it runs on are yours…",
     "أنت. عند سداد كامل المبلغ، تملك الموقع ومحتواه والحسابات التي يعمل من خلالها، وهي مسجّلة باسمك حيثما "
     "تسمح المنصّة بذلك. ويمكنك نقله أو تعديله أو تسليمه لشخص آخر.",
     "terms-ar §8"),
    ("أسئلة", "What happens after the first year?", "ماذا يحدث بعد السنة الأولى؟", "new"),
    ("أسئلة", "The first year of hosting and care is included. After that it's optional and quoted "
     "separately, and your site doesn't stop working if you say no.",
     "السنة الأولى من الاستضافة والرعاية مشمولة. وبعد تلك السنة تصبح اختيارية وتُسعَّر على حدة. ولا يتوقف "
     "موقعك عن العمل لأنك رفضتها.",
     "terms-ar §9"),
    ("أسئلة", "I already have a website. Can you replace it?",
     "لديّ موقع بالفعل. هل تستطيع استبداله؟", "new"),
    ("أسئلة", "Yes. The new site goes live on your own domain. If your domain isn't ready, it goes live on "
     "a temporary address first.",
     "نعم. يُطلَق الموقع الجديد على نطاقك أنت، أو على عنوان مؤقت أولاً إن لم يكن نطاقك جاهزاً.",
     "terms-ar §5"),
    ("أسئلة", "What if no buyers contact me?", "ماذا لو لم يتواصل معي أي مشترٍ؟", "new"),
    ("أسئلة", "If there's no real buyer inquiry within 30 days of going live, I rebuild it free…",
     "إن لم يصلك استفسار حقيقي من مشتري خلال 30 يوماً من إطلاق الموقع، أُعيد بناءه مجاناً حتى يصلك واحد. "
     "وإن لم يصلك بعدها، تسترد مبلغك المالي.",
     "the reviewed guarantee, punctuation only"),
    ("أسئلة", "Do I need to know anything technical?", "هل أحتاج إلى أي معرفة تقنية؟", "new"),
    ("أسئلة", "No. You send your products, prices and photos. I build it, and your team gets a recorded "
     "handover showing how it works.",
     "لا. ترسل منتجاتك وأسعارك وصورك، وأنا أبنيه، ويحصل فريقك على فيديو مسجّل يشرح طريقة عمله.", "new"),
    ("أسئلة", "How do I pay?", "كيف أدفع؟", "new"),
    ("أسئلة", "Half now, by card or bank transfer, to hold your seat. The other half on delivery. The "
     "figure on your invoice is the figure you pay: there is no VAT to add…",
     "النصف الآن، بالبطاقة أو بالتحويل البنكي، لحجز مقعدك. والنصف الآخر عند التسليم. والمبلغ المدوَّن في "
     "الفاتورة هو المبلغ الذي تدفعه: لا تُضاف إليه ضريبة القيمة المضافة. وطريقة الاسترداد موضّحة في سياسة الاسترجاع.",
     "terms-ar §3, adapted"),
    ("ما لا يشمله السعر", "What's not included", "ما لا يشمله السعر", "new"),
    ("ما لا يشمله السعر", "A domain name, if you don't have one yet. I ask before buying it and show you the "
     "receipt.",
     "اسم النطاق، إن لم يكن لديك واحد بعد. أستأذنك قبل شرائه، وأُطلعك على الإيصال.", "refund-policy-ar, adapted"),
    ("ما لا يشمله السعر", "Hosting and care after the first year. Optional, and quoted separately.",
     "الاستضافة والرعاية بعد السنة الأولى. اختيارية، وتُسعَّر على حدة.", "terms-ar §9, adapted"),
    ("ما لا يشمله السعر", "Paid outside services. If one is ever needed, you're told first and the account "
     "is in your name.",
     "الخدمات المدفوعة لدى أطراف ثالثة. إن احتجنا إلى واحدة، تُخبَر قبل استخدامها ويكون الحساب باسمك.",
     "terms-ar §9, adapted"),
    ("ما لا يشمله السعر", "More than one round of changes in launch week.",
     "أكثر من جولة تعديلات واحدة في أسبوع الإطلاق.", "new"),
    ("ما لا يشمله السعر", "The add-ons, the Live Owner Dashboard and the Full Autopilot. They're built "
     "after launch and sold separately.",
     "الإضافات: لوحة المعلومات الحيّة لصاحب العمل، والتشغيل الآلي الكامل. تُبنى بعد إطلاق الموقع وتُباع على حدة.",
     "terms-ar §5, adapted"),
    ("النموذج", "Hold your seat at today's price.", "احجز مقعدك بسعر اليوم.", "built from reviewed phrases"),
    ("النموذج", "Seven short fields. Your invoice arrives by email, and you pay the 50% deposit by card or "
     "bank transfer. The full brief comes after that.",
     "سبعة حقول قصيرة. تصلك فاتورتك بالبريد، وتدفع عربون 50% بالبطاقة أو بالتحويل البنكي. أما التفاصيل الكاملة "
     "فتأتي بعد ذلك.",
     "built from the reviewed old lede"),
    ("النموذج", "Rather ask something first? Message me on WhatsApp.",
     "تفضّل أن تسأل أولاً؟ راسلني على واتساب.", "question new, link text reviewed"),
    ("النموذج", "Your invoice is emailed to you the moment you complete the process (shown under the button)",
     "تصلك فاتورتك بالبريد لحظة إتمام الطلب.",
     "the reviewed note, shortened to match the English"),
]


# The mirror layer is a set of overrides keyed on the English page's own class
# names. Rename one there and the Arabic page loses that rule silently - the
# page still renders, it just renders wrong, in a language its author can't
# read. So the build asserts the hooks are still there.
HOOKS = [
    ".brand{", ".ptop b{", ".bub.en{", ".card::before{", ".mrow b{", ".vow{",
    ".seatbar i{", ".sc-pips i.open{", ".pledge:hover{", ".hp{",
    ".sticky .info{", ".nav-lang{", ".sc-count span{", ".pledge .txt span{", ".pbody{",
    ".field select{",
    ".vs-val{", ".vs-row.core{",
    ".hero-simple .hero-price{", ".card .go{", ".steps li::before{", ".steps h3{", ".notinc h3{",
    ".faq summary{", ".faq summary::after{", ".notinc ul{",
]


def write_review(page):
    """Render UNREVIEWED as a page a reviewer can work through, and name any
    row whose Arabic has gone from the page - the reviewer must never be asked
    about a sentence no visitor can see."""
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    text = re.sub(r" ([.،؟:])", r"\1", text)
    gone = [ar for _, _, ar, _ in UNREVIEWED if ar not in page and ar not in text]

    rows, last = [], None
    for where, en, ar, src in UNREVIEWED:
        if where != last:
            rows.append(f'<tr class="grp"><th colspan="3">{html.escape(where)}</th></tr>')
            last = where
        rows.append(f'<tr><td lang="en" dir="ltr">{html.escape(en)}</td>'
                    f'<td class="ar">{html.escape(ar)}</td>'
                    f'<td lang="en" dir="ltr" class="src">{html.escape(src)}</td></tr>')

    REVIEW.parent.mkdir(exist_ok=True)
    REVIEW.write_text(f"""<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta name="robots" content="noindex"/>
<title>مراجعة صفحة الموقع الذكي — {len(UNREVIEWED)} سطراً</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>
body{{margin:0;background:#F1EFE8;color:#232B26;font:16px/1.7 'IBM Plex Sans Arabic','IBM Plex Sans',sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 16px 80px}}
h1{{font-weight:600;color:#072B22;margin:0 0 6px}}
p.lede{{color:#5A665D;margin:0 0 24px;max-width:60ch}}
table{{width:100%;border-collapse:collapse;background:#FAF8F2;border:1px solid #DED8C8}}
td,th{{padding:12px 14px;border-top:1px solid #DED8C8;vertical-align:top;text-align:start}}
td[lang=en]{{font-family:'IBM Plex Sans',sans-serif;font-size:.9rem;color:#5A665D;width:34%}}
td.ar{{font-size:1.08rem}}
td.src{{width:16%;font-size:.8rem}}
tr.grp th{{background:#EAE4D5;color:#0A3D30;font-weight:600}}
</style></head><body><main>
<h1>صفحة الموقع الذكي: عربية لم تُراجَع بعد</h1>
<p class="lede">هذه الأسطر جديدة على <span dir="ltr">aiprofitlab.io/smart-storefront-ar/</span>، كُتبت في <span dir="ltr">2026-10-22</span> لتطابق الصفحة الإنجليزية الجديدة. كل ما عداها على الصفحة سبقت مراجعته ولم يتغيّر. صحّح ما يحتاج تصحيحاً في العمود الأوسط.</p>
<table>{"".join(rows)}</table>
</main></body></html>
""", encoding="utf-8")
    return gone


def build():
    src = SRC.read_text(encoding="utf-8")

    # The closing tag may be indented: the English page was run through a
    # formatter between 2026-08-27 and 2026-08-29, which turned `</style>` into
    # `  </style>` and every `.sel{` into `.sel {`. The old patterns matched
    # neither, so this script hard-failed for six days and the Arabic page could
    # not be rebuilt at all. Both patterns are now whitespace-tolerant, because a
    # reformat is not a restructure and must not read as one.
    m = re.search(r"<style>\n(.*?)\n\s*</style>", src, re.S)
    if not m:
        sys.exit(f"no <style> block found in {SRC} - has the page been restructured?")
    css = m.group(1)

    # A hook is a selector, so compare selectors — not the exact bytes around the
    # brace. The guard still catches what it is for (a selector the mirror layer
    # overrides having genuinely disappeared) without firing on a whitespace change.
    missing = [h for h in HOOKS if not re.search(re.escape(h[:-1].rstrip()) + r"\s*\{", css)]
    if missing:
        sys.exit("the English stylesheet no longer carries: " + ", ".join(missing) +
                 "\nUpdate the MIRROR section of RTL_CSS before rebuilding.")

    # The site menu's script is behaviour with no strings in it, so it is
    # carried over whole rather than kept as a second copy that could drift.
    menu_js = re.search(r'<script id="smenu-js">.*?</script>', src, re.S)
    if not menu_js:
        sys.exit(f'no <script id="smenu-js"> in {SRC.name} - the Arabic page\'s menu button\n'
                 "would open nothing. Restore the block or update this builder.")

    if 'hreflang="ar"' not in src:
        sys.exit(f"{SRC.name} carries no hreflang back to the Arabic page.\n"
                 "hreflang has to be reciprocal or it is ignored, and a visitor who lands\n"
                 "on the wrong language has no way across. Add the alternate links and the\n"
                 ".nav-lang switch to the English page first.")

    out = (HEAD.replace("__CSS__", css + "\n" + RTL_CSS)
               .replace("__AR_URL__", AR_URL)
               .replace("__EN_URL__", EN_URL)
           + BODY.replace("__EN_PATH__", "/en/smart-storefront/")
                 .replace("__MENU_JS__", menu_js.group(0))
                 .replace("__WA_ICON__", WA_ICON)
                 .replace("__WA__", WA_HREF)
           + JS).replace("__AIDEN_TAG__", aiden_version.tag()) \
                 .replace("__ANALYTICS_TAG__", analytics_version.tag())

    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(out):,} bytes, "
          f"{len(css.splitlines()):,} lines of CSS carried over from the English page)")

    gone = write_review(out)
    print(f"wrote {REVIEW.relative_to(ROOT)}  ({len(UNREVIEWED)} lines awaiting the native reader)")
    if gone:
        print("WARNING: these UNREVIEWED rows are no longer on the page - update the list:\n  " +
              "\n  ".join(gone))


if __name__ == "__main__":
    build()
