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

What this file owns is strings - the copy, the quiz, the four phone builds and
the JS message table - plus the handful of glyphs whose reading direction
matters (the arrows).

The page holds no prices. Like its English twin it renders whatever the Cloud
Run ledger returns from /status and shows an explicit "the live count isn't
loading" panel if that call fails; see the smart-storefront-offer-stack note.
The pledge board is gated behind ?pledges=open by the same script.

The URL follows the site's existing Arabic convention (kit.PAGES_AR): a root
`<name>-ar.html` served at `/<name>-ar/` by .htaccess rule 5, so no rewrite
rule is needed.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "public_html" / "en" / "smart-storefront.html"
OUT = ROOT / "public_html" / "smart-storefront-ar.html"

EN_URL = "https://aiprofitlab.io/en/smart-storefront/"
AR_URL = "https://aiprofitlab.io/smart-storefront-ar/"


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
[dir=rtl] .hero .sub,[dir=rtl] .lede{line-height:1.85}
[dir=rtl] .credo p{font-size:clamp(1.45rem,3.4vw,2.3rem);line-height:1.5}
[dir=rtl] .vow q{font-size:clamp(1.25rem,2.7vw,1.6rem);line-height:1.6}
[dir=rtl] .sig{font-size:1.2rem}
[dir=rtl] .qtitle{font-size:1.55rem}
[dir=rtl] .sc-sold{font-size:1.7rem}
[dir=rtl] .sticky .info b{font-size:1.15rem}
[dir=rtl] .curtain .sign h3{font-size:1.5rem}

/* Tracking and small-caps are Latin devices. letter-spacing on Arabic breaks
   the join between letters - it does not look airy, it makes the word
   unreadable - and text-transform does nothing at all. Both come off
   everywhere the English sheet sets them on a string that is now Arabic.
   .nav-lang and .ptag are deliberately absent: both still carry Latin. */
[dir=rtl] .eyebrow,[dir=rtl] .btn,[dir=rtl] .nav-cta,[dir=rtl] .hero-trust,
[dir=rtl] .qstep,[dir=rtl] .sc-badge,[dir=rtl] .sc-cell .k,[dir=rtl] .sc-sold,
[dir=rtl] .trophy .badge,[dir=rtl] .uptime,[dir=rtl] .sticky .seats,
[dir=rtl] .sigsub,[dir=rtl] .field label,[dir=rtl] .pfoot,
[dir=rtl] .paper .pscan,[dir=rtl] .mockup .pstrip,
[dir=rtl] .mockup[data-vibe="modern"] .pchip,
[dir=rtl] .mockup[data-vibe="expensive"] .pmark,
[dir=rtl] .mockup[data-vibe="expensive"] .pmeta,
[dir=rtl] .mockup[data-vibe="expensive"] .pbtn{
  letter-spacing:0;text-transform:none;
}

/* The phone and the four mockup builds are 236px wide with type between 8 and
   19px. Arabic needs a step up at every one of those sizes to stay legible,
   and Markazi needs two. Everything here is a size, never a layout. */
[dir=rtl] .paper{line-height:1.7;font-size:11px}
[dir=rtl] .paper .ph{font-size:21px;line-height:1.35}
[dir=rtl] .paper .pm{font-size:11px}
[dir=rtl] .pbody .pht{font-size:16.5px;line-height:1.35}
[dir=rtl] .pchip{font-size:9px}
[dir=rtl] .pbtn{font-size:10px}
[dir=rtl] .pfoot{font-size:9px}
[dir=rtl] .bub{font-size:10px;line-height:1.6}
[dir=rtl] .bub.ar{font-size:10.5px}
[dir=rtl] .ptoast{font-size:9.5px}
[dir=rtl] .mockup .psub{font-size:9.5px;line-height:1.7}
[dir=rtl] .mockup[data-vibe="serious"] .pht{font-size:15px}
[dir=rtl] .mockup[data-vibe="serious"] .pspec li{font-size:9.5px}
[dir=rtl] .mockup[data-vibe="modern"] .pht{font-size:14px;letter-spacing:0;line-height:1.45}
[dir=rtl] .mockup[data-vibe="expensive"] .pht{font-size:19px;line-height:1.4}
[dir=rtl] .mockup[data-vibe="plain"] .pht{font-size:13.5px;line-height:1.5}
[dir=rtl] .mockup[data-vibe="plain"] .plist{font-size:9.5px;line-height:1.8}
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
/* The flyer is the Arabic flyer - this page opens by telling you you scanned
   it. Only the brand line stays Latin, and it needs its own direction or the
   leading star lands on the wrong side of the wordmark. */
[dir=rtl] .paper{text-align:right}
[dir=rtl] .paper .pbrand{font-family:'Marcellus',Georgia,serif;direction:ltr;unicode-bidi:isolate;text-align:right}
[dir=rtl] .ptop b{margin-right:0;margin-left:auto}
/* The demo thread carries BOTH languages on purpose - answering an Arabic
   buyer and an English one in the same thread is the whole illustration. */
[dir=rtl] .bub.en{direction:ltr;text-align:left}
[dir=rtl] .opt{text-align:right}
[dir=rtl] .opt:hover{transform:translateX(-4px)}
/* The glyph itself is flipped in the markup; only travel is restated here. */
[dir=rtl] .opt::after{right:auto;left:14px;transform:translate(-6px,-50%)}
[dir=rtl] .opt:hover::after{transform:translate(0,-50%)}
/* "Grow from the reader's starting edge" - which is the right one here. */
[dir=rtl] .qdot::after,[dir=rtl] .card::before{transform-origin:100% 50%}
[dir=rtl] .mrow b{transform-origin:left center}
/* The amber rule under the credo's verbs is an inset shadow in the bottom
   few px of the inline box. Latin has nothing there; Arabic has the kasra
   and the shadda, and the rule cut through them. Inline padding-bottom
   drops the band below the marks without opening up the leading. */
[dir=rtl] .credo i{padding-bottom:.16em;box-shadow:inset 0 -.09em 0 var(--amber-pale)}
[dir=rtl] .say .caret{margin-left:0;margin-right:1px}
[dir=rtl] .vow{border-left:1px solid var(--line);border-right:3px solid var(--amber);border-radius:16px 0 0 16px}
[dir=rtl] .seatbar i,[dir=rtl] .sc-pips i.open{background:linear-gradient(270deg,var(--amber-bright),var(--amber-pale))}
[dir=rtl] .pledge:hover{transform:translateX(-4px)}
[dir=rtl] .mockup[data-vibe="plain"] .plist{padding-left:0;padding-right:15px}
[dir=rtl] .mockup[data-vibe="plain"] .pfoot{text-align:right}
/* The receipt. Its value column has to sit on the reader's FAR edge, which is
   the left one here: `margin-left:auto` absorbs the slack on the wrong side in
   RTL and shunts every price back against its own label. The mobile rule below
   it is the wrapped invoice row, where `justify-content` is already
   direction-aware and needs nothing said about it. */
[dir=rtl] .vs-val{margin-left:0;margin-right:auto}
[dir=rtl] .vs-row.core{background:linear-gradient(260deg,rgba(15,110,86,.10),rgba(15,110,86,.02))}
[dir=rtl] .trophy{text-align:right}
[dir=rtl] .hp{left:auto;right:-9999px}
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
<title>موقع ذكي يبيع وأنت نائم — AI Profit Lab</title>
<meta name="description" content="موقع ثنائي اللغة يرد على مشتريك في الرابعة فجراً، ويسلّم الجادّين منهم إلى واتساب، ويخبرك من هو على وشك الشراء. سعر لمرة واحدة، وسنة استضافة ورعاية مشمولة."/>
<!-- Mirrors the English page's robots value. Flip both together at handover. -->
<meta name="robots" content="noindex, follow"/>
<meta name="author" content="AI Profit Lab"/>
<meta name="theme-color" content="#0A3D30"/>

<link rel="canonical" href="__AR_URL__"/>
<link rel="alternate" hreflang="ar" href="__AR_URL__"/>
<link rel="alternate" hreflang="en" href="__EN_URL__"/>
<link rel="alternate" hreflang="x-default" href="__EN_URL__"/>

<meta property="og:title" content="موقع ذكي يبيع وأنت نائم — AI Profit Lab"/>
<meta property="og:description" content="مسحتَ الورقة. هذا ما تتحوّل إليه الورقة."/>
<meta property="og:url" content="__AR_URL__"/>
<meta property="og:type" content="website"/>
<meta property="og:locale" content="ar_OM"/>
<meta property="og:locale:alternate" content="en_US"/>
<meta property="og:image" content="https://aiprofitlab.io/og-aiprofitlab-2026.jpg"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="ناهد أبياري، مؤسس AI Profit Lab — أتمتة بالذكاء الاصطناعي لشركات الخليج"/>
<meta name="twitter:card" content="summary_large_image"/>

<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=20260822">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=20260822">
<link rel="manifest" href="/site.webmanifest?v=20260822">

<script>document.documentElement.className += " js";</script>

<!-- ══ pledge gate ══
     Identical to the English page's, and it reads the SAME localStorage key,
     so a link handed out in one language opens the board in the other too.
     The "Four ways to pay less" board (section 6) is hidden from every visitor
     by default, so the published price is the price. Open the page with
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
     figures. Marcellus stays in the list for the Latin wordmark on the flyer,
     which must not render in a Naskh face. -->
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Marcellus&family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<link rel="stylesheet" media="print" onload="this.media='all'" href="https://fonts.googleapis.com/css2?family=Marcellus&family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Marcellus&family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"></noscript>

<style>
__CSS__
</style>
<!-- Microsoft Clarity -->
<script>(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window,document,"clarity","script","y7wcjlyamc");</script>
<script defer src="/js/apl-analytics.js?v=c85e0eed"></script>
</head>
"""


# ══════════════════════════════════════════════════════════════════════════
# BODY. Same components, same section order and the same figures as the
# English page - only the strings and the direction-carrying glyphs change.
#
# Voice: first person singular, matching the rest of the Arabic site
# (tools/v4/ar/*). "نحن" would contradict the one claim the guarantee makes.
# ══════════════════════════════════════════════════════════════════════════
BODY = r"""<body>

<nav>
  <div class="nav-in">
    <a class="brand" href="/ar/" aria-label="AI Profit Lab — الصفحة الرئيسية">
      <img src="/en/logo/wordmark-cream.svg" alt="AI Profit Lab" width="158" height="27"/>
    </a>
    <a class="nav-lang" href="__EN_PATH__" hreflang="en" lang="en">English</a>
    <a class="nav-cta" href="#claim">احجز مقعدك</a>
  </div>
</nav>

<!-- ═══ 1. THE PAPER HANDSHAKE ═══ -->
<header class="hero">
  <div class="stars" id="stars" aria-hidden="true"></div>
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow"><span class="star">✼</span> لقد مسحتَ الورقة</p>
      <h1>يبيع وأنت نائم.</h1>
      <p class="sub">موقع ذكي ثنائي اللغة يرد على مشتريك بالعربية أو الإنجليزية &mdash; في أي ساعة &mdash; ويسلّم الجادّين منهم إلى واتساب.</p>

      <div class="hero-ctas">
        <a class="btn btn-cream" href="#roast">أرِني موقعي</a>
        <a class="btn btn-outline" href="#value">أرِني السعر</a>
      </div>

      <ul class="hero-trust">
        <li>سعر لمرة واحدة</li>
        <li>سنة استضافة ورعاية مشمولة</li>
        <li>عربي وإنجليزي</li>
        <li>بلا اشتراك شهري</li>
      </ul>
    </div>

    <div class="stage" id="stage">
      <div class="flyer" id="flyer" aria-hidden="true"></div>
      <div class="phone" id="phone" role="img" aria-label="هاتف يعرض الموقع الذكي ثنائي اللغة الذي تتحوّل إليه الورقة: موقع بالعربية والإنجليزية، فيه زر طلب تسعيرة بالجملة، وزر واتساب، ومحادثة حيّة مع مشترٍ، وتنبيه باستفسار جديد.">
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

<!-- ═══ 1b. THE CREDO ═══ -->
<section class="credo">
  <div class="wrap">
    <p class="rv">أنا لا أبني مواقع وحسب &mdash; <b>أبني أنظمة رقمية ذكية
      <i>تفكّر</i> و<i>تتكيّف</i> و<i>تُحوِّل</i>.</b></p>
  </div>
</section>

<!-- ═══ 2. THE GUARANTEE, AND THE FACE BEHIND IT ═══ -->
<section>
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> وعد الاستفسار الأول</p>
    <div class="vow rv">
      <picture>
        <source srcset="/nahid-founder-seated-2026.webp" type="image/webp"/>
        <img src="/nahid-founder-seated-2026.jpg" alt="ناهد أبياري، مؤسس AI Profit Lab" width="200" height="235" decoding="async"/>
      </picture>
      <div>
        <q>لم يصلك استفسار حقيقي من مشترٍ خلال 30 يوماً من إطلاق الموقع؟ أُعيد بناءه مجاناً حتى يصلك واحد. وإن لم يصلك بعدها، تسترد مالك.</q>
        <p class="sig">— ناهد أبياري</p>
        <p class="sigsub">الرئيس التنفيذي، AI Profit Lab</p>
      </div>
    </div>
  </div>
</section>

<!-- ═══ 3. THREE TAPS ═══ -->
<section class="roast" id="roast">
  <div class="wrap narrow">
    <p class="eyebrow rv"><span class="star">✼</span> عشر ثوانٍ</p>
    <h2 class="rv">شاهد كيف سيبدو موقعك أنت.</h2>
    <p class="lede rv" style="margin-bottom:30px">ثلاث نقرات. بلا بريد، وبلا تسجيل.</p>

    <div class="qcard rv" id="qcard">
      <div id="qwrap">
        <div class="qhead">
          <svg class="mascot" id="mascot" viewBox="0 0 80 80" aria-hidden="true">
            <line x1="40" y1="20" x2="40" y2="10" stroke="#0A3D30" stroke-width="3" stroke-linecap="round"/>
            <circle class="m-tip" cx="40" cy="7" r="5" fill="#D89234"/>
            <rect x="13" y="20" width="54" height="46" rx="15" fill="#0A3D30"/>
            <circle class="m-eye" cx="30" cy="40" r="5" fill="#F1EFE8"/>
            <circle class="m-eye" cx="50" cy="40" r="5" fill="#F1EFE8"/>
            <path id="mouth" d="M31 53q9 6 18 0" stroke="#E8C98F" stroke-width="3" fill="none" stroke-linecap="round"/>
          </svg>
          <div>
            <p class="qstep" id="qstep">السؤال 1 من 3</p>
            <h3 class="qtitle" id="qtitle">ماذا تبيع؟</h3>
          </div>
        </div>
        <div class="opts" id="qopts"></div>
        <div class="qprog" id="qprog"><i class="qdot on"></i><i class="qdot"></i><i class="qdot"></i></div>
      </div>
      <p class="say" id="say" aria-live="polite"></p>

      <div class="result" id="qresult">
        <!-- built by renderMockup() as soon as the third question is answered -->
        <div class="mockup" id="mockup" data-vibe="serious"></div>
        <div>
          <h3 style="font-family:var(--display);font-weight:400;font-size:1.7rem;color:var(--teal-900);margin-bottom:12px">نموذج، لا وعد.</h3>
          <p style="color:var(--muted);font-size:.97rem">عشر ثوانٍ من الإثبات، بقيمتها تماماً. الموقع الحقيقي يستغرق نحو أسبوع، وفيه منتجاتك أنت، باللغتين.</p>
          <p style="margin-top:16px"><a class="btn btn-primary" href="#value">كم يكلّف؟</a></p>
          <p><button type="button" class="opt" id="qagain" style="margin-top:10px;width:auto">ابدأ من جديد</button></p>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ═══ 4. WHAT YOU GET ═══ -->
<section>
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ما الذي تحصل عليه</p>
    <h2 class="rv">ستة أشياء. لكلٍّ منها وظيفة.</h2>
    <div class="grid3" style="margin-top:34px">
      <div class="card rv"><span class="ic">🕐</span><h3>موظّف لا ينام</h3><p>وكيل ذكاء اصطناعي ثنائي اللغة يرد على المشترين في الرابعة فجراً، ويوم الجمعة، وفي العيد.</p></div>
      <div class="card rv"><span class="ic">📲</span><h3>عملاء ساخنون في جيبك</h3><p>المشترون الجادّون يُسلَّمون مباشرة إلى واتساب.</p></div>
      <div class="card rv"><span class="ic">📋</span><h3>مبنيّ لتسعيرات الجملة</h3><p>مسار طلب تسعيرة بالجملة، لا صندوق «اتصل بنا» للتجزئة.</p></div>
      <div class="card rv"><span class="ic">👀</span><h3>اعرف من هو على وشك الشراء</h3><p>ملخّص قصير عمّن زار وماذا سأل، يصل إلى هاتفك.</p></div>
      <div class="card rv"><span class="ic">🔎</span><h3>يظهر في جوجل وفي ChatGPT</h3><p>مبنيّ للبحث التقليدي ولإجابات الذكاء الاصطناعي معاً.</p></div>
      <div class="card rv"><span class="ic">🛠️</span><h3>لا شيء تصونه</h3><p>سنة كاملة من الاستضافة والحماية والرعاية، مشمولة.</p></div>
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
     scan as one figure. -->
<section class="vs-sec" id="value">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> ما الذي يشتريه المبلغ فعلاً</p>
    <h2 class="rv">أنت تدفع ثمن الموقع. والباقي هديّة إطلاق.</h2>
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
      <div class="vs-row" style="--i:6"><span class="vs-lbl">تسليم وتدريب لفريقك، مُسجَّل</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:7"><span class="vs-lbl">استضافة اثني عشر شهراً</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>
      <div class="vs-row" style="--i:8"><span class="vs-lbl">ملاحظة عمّن زار موقعك، ومن أي البلدان، وماذا سأل</span><span class="vs-val"><span class="vs-was">50 ر.ع.</span><span class="vs-free">مجاناً</span></span></div>

      <div class="vs-tot">
        <div class="vs-trow"><span class="lbl">كل ما سبق، <a href="/services/">بسعره المعتاد</a></span><b>949 ر.ع.</b></div>
        <div class="vs-trow gift"><span class="lbl">هديّة الإطلاق</span><b id="vsGift">—</b></div>
        <div class="vs-trow pay"><span class="lbl">تدفع اليوم</span><b id="vsPay">—</b></div>
      </div>
    </div>

    <p class="vs-foot rv"><b>لا شيء هنا يُباع لك لاحقاً كإضافة.</b> كل سطر داخل البناء، بسعر مقعد اليوم. وحين تنتهي المقاعد بهذا السعر يرتفع السعر — وتنقص الهديّة بالمقدار نفسه. أمّا السعر المنشور في صفحة الخدمات فلا يتحرك.</p>
  </div>
</section>

<!-- ═══ 5. SCARCITY ═══ -->
<section class="scarcity" id="ladder">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> السعر يرتفع كلما امتلأت المقاعد</p>
    <h2 class="rv">المقاعد المتبقية بسعر اليوم:</h2>

    <div class="offline" id="ladderOffline">
      <strong>العدّاد المباشر لا يُحمّل الآن.</strong>
      أُفضّل ألا أعرض لك شيئاً على أن أعرض رقماً اختلقته. <a href="https://api.whatsapp.com/send?phone=96899245250" target="_blank" rel="noopener">اسألني على واتساب</a>.
    </div>

    <div class="scard rv" id="ladderList">
      <div class="sc-badge"><i></i> أقرأ السجل</div>
      <div class="sc-count"><b><span class="skel" style="min-width:1.1em"></span></b><span>مقاعد متبقية بهذا السعر</span></div>
      <div class="sc-pips"><i></i><i></i><i></i></div>
    </div>

    <p class="sc-note rv">مقعد واحد = عربون 50% وصل فعلاً. ليس مؤقّتاً يعود إلى الصفر كلما أعدت تحميل الصفحة. إرسال النموذج لا يحجز مقعداً — العربون هو الذي يحجزه.</p>
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

<!-- ═══ 6b. THE BUTTON THAT RUNS AWAY ═══
     Sits outside #pledges on purpose. The pledge board is gated (see the top of
     this file) and a child of a display:none section can never be shown again,
     so the chase lives in its own section and survives the gate. -->
<section id="chase">
  <div class="wrap">
    <div class="chase rv">
      <p class="chase-note pledge-only-b">بعضهم سيبحث الآن عن الزر الذي يعطيه أكثر.</p>
      <p class="chase-note nopledge">بعضهم سيذهب الآن يبحث عن الزر الذي يخصم قليلاً أكثر.</p>
      <button type="button" id="runaway-btn">أريد خصماً أكبر</button>
      <div class="trophy" id="trophy">
        <span class="badge">✼ صائد أزرار معتمد</span>
        <strong>حسناً. فزت.</strong>
        <p style="margin:8px 0 0;color:var(--muted);font-size:.94rem">لا يوجد خصم إضافي فعلاً. لكنك طاردت زراً سبع مرات — وهذا بالضبط قدر الإصرار الذي يلزم لتحصيل فاتورة متأخرة. صوّر الشاشة؛ استحققتها.</p>
      </div>
    </div>
  </div>
</section>

<!-- ═══ 7. CLAIM FORM ═══ -->
<section class="roast" id="claim">
  <div class="wrap">
    <p class="eyebrow rv"><span class="star">✼</span> احجز مقعداً</p>
    <h2 class="rv">ستة حقول. ثم تصلك فاتورتك في بريدك.</h2>
    <p class="lede rv" style="margin-bottom:28px">هذا يحفظ مكانك بسعر اليوم. أما التفاصيل الكاملة فتأتي لاحقاً، بعد أن يصل العربون.</p>

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
        <div class="field full"><label for="f-site">موقعك الحالي <span class="opt-tag">— اختياري، و«لا يوجد» إجابة سليمة تماماً</span></label><input id="f-site" name="currentSite" dir="ltr" placeholder="لا يوجد"/></div>
      </div>

      <div class="hp" aria-hidden="true"><label for="f-companyurl">Company URL</label><input id="f-companyurl" name="companyUrl" tabindex="-1" autocomplete="off"/></div>

      <label class="consent"><input type="checkbox" id="f-consent" required/>
        <span>أوافق على أن تتواصل معي AI Profit Lab بخصوص هذا الحجز عبر البريد وواتساب، وأن تحفظ هذه البيانات لإعداد اتفاقي. لا شيء غير ذلك، ولا قوائم بريدية. <a href="/privacy-ar/" target="_blank" rel="noopener">الخصوصية</a>.</span>
      </label>

      <div class="formerr" id="formErr"></div>

      <p style="margin:20px 0 0"><button type="submit" class="btn btn-primary" id="fSubmit" style="width:100%">احجز لي مقعداً بهذا السعر</button></p>
      <p id="fPayNote" style="font-size:.84rem;color:var(--muted);margin:12px 0 0">لا دفع في هذه الصفحة. تصلك فاتورتك بالبريد لحظة الإرسال، والصفحة التالية هي مكان دفع العربون.</p>
    </form>
  </div>
</section>

<!-- ═══ 8. FOOTER + CAT ═══ -->
<footer>
  <div class="wrap footgrid">
    <div>
      <img class="foot-logo" src="/en/logo/wordmark-dark.svg" alt="AI Profit Lab" width="150" height="26" loading="lazy"/>
      <p style="margin:0">كل نجاح يبدأ ببصيرة.</p>
      <p style="margin:10px 0 0;font-size:.8rem"><span class="ltr">© 2026 AI Profit Lab</span> — علامة تجارية تابعة لـ Lotus Gulf International (س.ت <span class="ltr">1570092</span>) · <a href="/refund-policy-ar/">سياسة الاسترجاع</a> · <a href="/privacy-ar/">الخصوصية</a></p>
    </div>

    <div class="uptime">
      <span>ضمان تشغيل 100% للذكاء الاصطناعي<sup>*</sup></span>
      <button class="catbtn" id="catBtn" aria-label="أيقظ قط الخادم" title="لا توقظ قط الخادم">
        <svg viewBox="0 0 70 52" id="catSvg" aria-hidden="true">
          <rect x="4" y="26" width="62" height="9" rx="2" fill="#16261F" stroke="#3FAE8A" stroke-width="1"/>
          <rect x="4" y="37" width="62" height="9" rx="2" fill="#16261F" stroke="#3FAE8A" stroke-width="1"/>
          <circle cx="60" cy="30.5" r="1.6" fill="#3FAE8A"/><circle cx="60" cy="41.5" r="1.6" fill="#D89234"/>
          <g class="cat-body">
            <path d="M14 26c0-6 5-10 11-10s11 4 11 10z" fill="#D89234"/>
            <path d="M36 25c7 1 9-2 8-6" stroke="#D89234" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            <path d="M18 17.5l1.5-5 3.5 4z" fill="#BA7517"/><path d="M31 16.5l2-4 1.5 5z" fill="#BA7517"/>
            <circle cx="22" cy="21" r="1.3" fill="#2A1B04" class="cat-eye"/><circle cx="29" cy="21" r="1.3" fill="#2A1B04" class="cat-eye"/>
            <path d="M20.5 21.5h3M27.5 21.5h3" stroke="#2A1B04" stroke-width="1.1" stroke-linecap="round" class="cat-shut"/>
          </g>
          <text x="40" y="16" class="cat-z" font-size="9" fill="#E8C98F" font-family="monospace">z</text>
          <text x="46" y="10" class="cat-z" font-size="7" fill="#E8C98F" font-family="monospace">z</text>
        </svg>
      </button>
    </div>
  </div>
  <div class="wrap"><p style="font-size:.72rem;color:rgba(241,239,232,.4);margin:18px 0 0">* القط للزينة. أما نسبة التشغيل فليست كذلك — هي اتفاقية استضافة حقيقية، والقط لم يقترب من خادم قط.</p></div>
</footer>

<div class="curtain" id="curtain">
  <div class="sign">
    <h3>تحت الإنشاء</h3>
    <p>القط استيقظ وله رأي في قراءتك. لا شيء معطّل فعلاً.</p>
    <button class="btn btn-primary" id="curtainClose" style="width:100%">انقر لإزالة القط</button>
  </div>
</div>

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
# are the difference, plus four Arabic-specific changes, each marked ARABIC:
# in place.
# ══════════════════════════════════════════════════════════════════════════
JS = r"""<script>
(function(){
  "use strict";
  var API = "https://storefront-offer-api-989128855797.me-central1.run.app";
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

  /* ─────────── confetti + dust puffs ─────────── */
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
  function puff(x, y) {
    if (reduce) return;
    for (var i = 0; i < 6; i++) {
      spawn("puff", x, y, {
        "--dx": ((Math.random() - 0.5) * 70).toFixed(0) + "px",
        "--dy": ((Math.random() - 0.5) * 70).toFixed(0) + "px"
      }, 620);
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

  /* ─────────── 1. flyer → storefront ─────────── */
  var flyer = document.getElementById("flyer");
  var phone = document.getElementById("phone");
  var STRIPS = 12;

  var paperHTML =
    '<div class="paper">' +
      '<div class="pbrand">✼ AI Prof<i>i</i>t Lab</div>' +
      '<div class="ph">موقع يبيع وأنت نائم.</div>' +
      '<div class="pm">ثنائي اللغة · عربي وإنجليزي<br>صُنع في مسقط</div>' +
      '<div class="pqr"></div>' +
      '<div class="pscan">امسحني ←</div>' +
      '<div class="pcut"></div>' +
    '</div>';

  for (var st = 0; st < STRIPS; st++) {
    var strip = document.createElement("div");
    strip.className = "strip";
    strip.style.clipPath = "inset(0 " + (100 - (st + 1) * (100 / STRIPS)) + "% 0 " + (st * (100 / STRIPS)) + "%)";
    strip.innerHTML = paperHTML;
    flyer.appendChild(strip);
  }

  function upgrade() {
    if (reduce) { flyer.style.display = "none"; phone.classList.add("on"); return; }
    flyer.querySelectorAll(".strip").forEach(function(el, i){
      var drift = (i - STRIPS / 2) * 5;
      el.style.transition = "transform .95s cubic-bezier(.5,0,.75,0), opacity .8s ease-in";
      el.style.transitionDelay = (i * 32) + "ms";
      el.style.transform = "translate(" + drift + "px," + (150 + Math.random() * 90) + "px) rotate(" + drift + "deg)";
      el.style.opacity = "0";
    });
    setTimeout(function(){ phone.classList.add("on"); }, 430);
    setTimeout(function(){ flyer.style.display = "none"; }, 1600);
  }
  setTimeout(upgrade, reduce ? 0 : 900);

  /* ─────────── 2. three taps ─────────── */
  var QUESTIONS = [
    { title: "ماذا تبيع؟", key: "sector", options: [
      { label: "مواد بناء",        say: "مواد بناء. مشتروك يتصلون بثلاثة موردين ويشترون من أول من يرد. هذه هي اللعبة كلها." },
      { label: "مستلزمات طبية",     say: "مستلزمات طبية. مشتروك يحتاجون أوراق المواصفات، ويحتاجونها في ساعات غريبة. صفحة تقول «منتجات عالية الجودة» لن تكفي." },
      { label: "قطع غيار سيارات",   say: "قطع غيار. نصف استفساراتك من شخص يمسك قطعة مكسورة ويسأل إن كانت عندك. أسرع إجابة تكسب." },
      { label: "أغذية ومواد استهلاكية", say: "أغذية ومواد استهلاكية. إعادة طلب، وقوائم أسعار، وأيام توصيل. مملّ ومتكرّر — وهذا بالضبط ما ينبغي أن تتولاه آلة." },
      { label: "شيء آخر",          say: "شيء آخر. جيد — صناعة القوالب الجاهزة تكره ذلك، وهو السبب في ألا يكون موقعك قالباً." }
    ]},
    { title: "ما وضع موقعك الحالي؟", key: "site", options: [
      { label: "ليس لديّ موقع",      say: "صريح. وكثير من منافسيك لديهم موقع أسوأ من لا شيء، فأنت متقدّم أكثر مما تظن." },
      { label: "لديّ موقع، من 2019", say: "موقع 2019 يُحمّل صورة بأربعة ميغابايت، ثم يطلب من غريب أن يملأ نموذجاً. نستطيع التفوّق على ذلك قبل الغداء." },
      { label: "ابن أخي بناه",       say: "كل ابن أخٍ في عُمان بنى موقعاً واحداً بالضبط. له كل الاحترام. لكنه لا يرد على مشتريك في منتصف الليل." },
      { label: "نستخدم واتساب فقط",  say: "واتساب بصراحة هو المكان الصحيح لإغلاق الصفقة. المشكلة أن يجدك أحد أصلاً قبل أن تبدأ تلك المحادثة." }
    ]},
    { title: "بأي إحساس تريده؟", key: "vibe", options: [
      { label: "جادّ ومتين",   vibe: "serious",   say: "جادّ ومتين. الترجمة: بلا صورة مصافحة أمام مبنى زجاجي." },
      { label: "عصري ونظيف",   vibe: "modern",    say: "عصري ونظيف. ممكن. ويعني غالباً حذف أشياء، وهو ما لا أحد يحب أن يحاسبك عليه." },
      { label: "فاخر",         vibe: "expensive", say: "فاخر. خلفية داكنة، ومساحة فارغة كثيرة، وجملة واحدة واثقة جداً. ينجح لأنه يبدو ضبطاً للنفس." },
      { label: "المهم أن يعمل", vibe: "plain",     say: "المهم أن يعمل. ملخّصي المفضّل. آراء أقل، وإطلاق أسرع، واستفسارات أكثر." }
    ]}
  ];

  /* ─── what the mockup is built from ───
     Sector picks the copy and the conversation, the website answer picks the
     notification, and the vibe picks an entirely different build of the screen
     (SKINS below). Five sectors x four situations x four vibes, so two people
     answering differently never see the same phone.

     ARABIC: `mark` is a field rather than the English page's
     brand.replace(/^YOUR /, "") — there is no prefix to strip off an Arabic
     brand line, so the "expensive" build states its own wordmark. */
  var SECTORS = {
    "مواد بناء": {
      brand:"شركتك لمواد البناء",
      mark: "مواد البناء",
      h:    "أسمنت وحديد وبلوك — يُوصَّل في كل عُمان.",
      sub:  "من طبلية واحدة إلى مشروع كامل، بسعر يوم تسأل.",
      chips:["أسعار الجملة","توصيل للموقع","توفّر المخزون"],
      cta:  "اطلب تسعيرة بالجملة",
      ar:   "مرحباً! تحتاج تسعيرة بالجملة؟",
      en:   "400 bags, delivered to Sohar."
    },
    "مستلزمات طبية": {
      brand:"شركتك للمستلزمات الطبية",
      mark: "المستلزمات الطبية",
      h:    "مستلزمات طبية، وأوراقها مرتّبة.",
      sub:  "بيانات فنية، وسلسلة تبريد، ووثائق مناقصات، عند الطلب.",
      chips:["بيانات فنية","سلسلة تبريد","مناقصات"],
      cta:  "اطلب المواصفات والأسعار",
      ar:   "مرحباً! تبحث عن مواصفات المنتج؟",
      en:   "Can you send the spec sheet?"
    },
    "قطع غيار سيارات": {
      brand:"شركتك لقطع الغيار",
      mark: "قطع الغيار",
      h:    "القطعة التي تحتاجها، متوفّرة، اليوم.",
      sub:  "أرسل رقم القطعة أو صورة لها. ستعرف خلال دقائق.",
      chips:["بحث برقم القطعة","أسعار التجارة","تسليم بنفس اليوم"],
      cta:  "تحقّق من توفّر القطعة",
      ar:   "مرحباً! تبحث عن قطعة معيّنة؟",
      en:   "Do you have this part number?"
    },
    "أغذية ومواد استهلاكية": {
      brand:"شركتك للتوزيع بالجملة",
      mark: "التوزيع بالجملة",
      h:    "توريد بالجملة تعتمد عليه رفوفك.",
      sub:  "طلبات دائمة، وقوائم أسعار أسبوعية، وأيام توصيل تخطّط عليها.",
      chips:["قائمة الأسعار","إعادة الطلب","أيام التوصيل"],
      cta:  "احصل على قائمة أسعار هذا الأسبوع",
      ar:   "مرحباً! تريد قائمة الأسعار؟",
      en:   "Send me this week’s price list."
    },
    "شيء آخر": {
      brand:"شركتك",
      mark: "شركتك",
      h:    "نُورّد في عُمان، منذ يوم بدأت.",
      sub:  "يرد بلغة مشتريك، في ساعة مشتريك.",
      chips:["أسعار الجملة","التوصيل","بيانات المنتجات"],
      cta:  "اطلب تسعيرة بالجملة",
      ar:   "مرحباً! كيف أقدر أساعدك؟",
      en:   "Can I get a bulk quote?"
    }
  };

  // the notification is the part that answers "what was I missing before?"
  var TOASTS = {
    "ليس لديّ موقع":      "استفسار جديد ← إلى هاتفك",
    "لديّ موقع، من 2019": "رُدّ عليه " + ltr("2:14") + " فجراً ← وأنت نائم",
    "ابن أخي بناه":       "طلب تسعيرة ← مباشرة إلى واتساب",
    "نستخدم واتساب فقط":  "وجدك في جوجل ← والآن في واتساب",
    _default:             "استفسار جديد ← إلى هاتفك"
  };

  function mkConv(d) {
    return '<div class="pconv">'
      + '<div class="bub ar d-ar">' + d.ar + '</div>'
      + '<div class="bub d-type"><i></i><i></i><i></i></div>'
      + '<div class="bub en d-en">' + d.en + '</div>'
      + '</div>';
  }
  function mkChips(list) {
    return list.map(function(c){ return '<span class="pchip">' + c + '</span>'; }).join("");
  }
  function mkItems(list) {
    return list.map(function(c){ return '<li>' + c + '</li>'; }).join("");
  }

  /* Four builds. Same ingredients, different architecture: the chrome, the type,
     the way the three selling points are listed and the buttons all change. */
  var SKINS = {
    // trade chrome, credentials, a ticked spec list, squared buttons
    serious: function(d, toast) {
      return '<div class="pscreen">'
        + '<div class="ptop"><b>' + d.brand + '</b><span class="ptag">AR</span><span class="ptag">EN</span></div>'
        + '<div class="pstrip">سجل تجاري · توريد بالجملة · عُمان</div>'
        + '<div class="pbody">'
        +   '<div class="pht">' + d.h + '</div>'
        +   '<div class="prule"></div>'
        +   '<ul class="pspec">' + mkItems(d.chips) + '</ul>'
        +   '<div class="pbtn">' + d.cta + '</div>'
        +   '<div class="pbtn wa">تحدّث على واتساب</div>'
        +   '<div class="pfoot">عربي وإنجليزي · رد على مدار الساعة</div>'
        + '</div>' + mkConv(d)
        + '<div class="ptoast">' + toast + '</div></div>';
    },
    // light chrome, white space, outline chips, pill buttons
    modern: function(d, toast) {
      return '<div class="pscreen">'
        + '<div class="ptop"><b>' + d.brand + '</b><span class="ptag">AR</span><span class="ptag">EN</span></div>'
        + '<div class="pbody">'
        +   '<div class="pht">' + d.h + '</div>'
        +   '<p class="psub">' + d.sub + '</p>'
        +   '<div class="pchips">' + mkChips(d.chips) + '</div>'
        +   '<div class="pbtn">' + d.cta + '</div>'
        +   '<div class="pbtn wa">واتساب</div>'
        +   '<div class="pfoot">ثنائي اللغة · دائم التشغيل</div>'
        + '</div>' + mkConv(d)
        + '<div class="ptoast">' + toast + '</div></div>';
    },
    // dark, no chrome, one sentence, one thin outlined button
    expensive: function(d, toast) {
      return '<div class="pscreen">'
        + '<div class="pmark">' + d.mark + '</div>'
        + '<div class="pbody">'
        +   '<div class="pht">' + d.h + '</div>'
        +   '<p class="pmeta">' + d.chips.join(" · ") + '</p>'
        +   '<div class="pbtn">استفسر</div>'
        +   '<span class="pwa">أو واتساب ←</span>'
        + '</div>' + mkConv(d)
        + '<div class="ptoast">' + toast + '</div></div>';
    },
    // no decoration, WhatsApp first and biggest, every corner square
    plain: function(d, toast) {
      return '<div class="pscreen">'
        + '<div class="ptop"><b>' + d.brand + '</b><span class="ptag">AR</span><span class="ptag">EN</span></div>'
        + '<div class="pbody">'
        +   '<div class="pht">' + d.h + '</div>'
        +   '<ul class="plist">' + mkItems(d.chips) + '</ul>'
        +   '<div class="pbtn wa">راسلنا على واتساب</div>'
        +   '<div class="pbtn sec">' + d.cta + '</div>'
        +   '<div class="pfoot">بالعربية والإنجليزية، في أي ساعة.</div>'
        + '</div>' + mkConv(d)
        + '<div class="ptoast">' + toast + '</div></div>';
    }
  };

  function renderMockup(sector, site, vibe) {
    var d = SECTORS[sector] || SECTORS["شيء آخر"];
    var mk = document.getElementById("mockup");
    mk.setAttribute("data-vibe", vibe);
    mk.innerHTML = (SKINS[vibe] || SKINS.serious)(d, TOASTS[site] || TOASTS._default);
  }

  // `busy` locks input while the commentary is typing. Without it, two quick taps on the
  // same question advance the counter twice, run finish() with unanswered questions, and
  // throw before the result panel is ever shown.
  var qi = 0, answers = {}, busy = false;
  var qwrap = document.getElementById("qwrap"), qstep = document.getElementById("qstep"),
      qtitle = document.getElementById("qtitle"), qopts = document.getElementById("qopts"),
      qprog = document.getElementById("qprog"), say = document.getElementById("say"),
      qresult = document.getElementById("qresult"), mascot = document.getElementById("mascot"),
      mouth = document.getElementById("mouth");

  function mascotThink(on) {
    mascot.classList.toggle("think", on);
    mouth.setAttribute("d", on ? "M35 53q5 3 10 0" : "M31 53q9 6 18 0");
  }
  function mascotCheer() {
    mascot.classList.remove("think");
    mouth.setAttribute("d", "M29 51q11 9 22 0");
    mascot.classList.add("happy");
    setTimeout(function(){ mascot.classList.remove("happy"); }, 650);
  }

  /* ARABIC: the English page types by appending a text node per tick. Arabic
     letters join, and a letter's shape depends on its neighbours - growing the
     line out of a chain of sibling text nodes leaves the joins at the mercy of
     how the engine happens to segment them. Rewriting the WHOLE prefix into
     ONE text node every tick keeps the run intact, so each new letter simply
     joins the word the way it will finally sit. */
  function type(text, done) {
    if (reduce) { say.textContent = text; if (done) done(); return; }
    say.innerHTML = '<span class="typed"></span><span class="caret"> </span>';
    var node = say.querySelector(".typed"), caret = say.querySelector(".caret");
    var i = 0;
    var timer = setInterval(function(){
      i += 2;
      node.textContent = text.slice(0, i);
      if (i >= text.length) { clearInterval(timer); caret.remove(); if (done) done(); }
    }, 16);
  }

  function renderQuestion() {
    var q = QUESTIONS[qi];
    qstep.textContent = "السؤال " + (qi + 1) + " من " + QUESTIONS.length;
    qtitle.textContent = q.title;
    qopts.innerHTML = "";
    q.options.forEach(function(o){
      var b = document.createElement("button");
      b.type = "button";
      b.className = "opt";
      b.textContent = o.label;
      b.addEventListener("click", function(){ answer(q, o); });
      qopts.appendChild(b);
    });
    Array.prototype.forEach.call(qprog.children, function(d, i){ d.classList.toggle("on", i <= qi); });
  }

  function answer(q, o) {
    if (busy) return;
    busy = true;
    answers[q.key] = o;
    mascotThink(true);
    track("roast_answer", { step: q.key, choice: o.label });
    type(o.say, function(){
      mascotThink(false);
      qi++;
      if (qi < QUESTIONS.length) { setTimeout(function(){ renderQuestion(); busy = false; }, 320); }
      else { setTimeout(finish, 420); }
    });
  }

  function finish() {
    var sector = answers.sector ? answers.sector.label : "شيء آخر";
    var site = answers.site ? answers.site.label : "";
    var vibe = answers.vibe ? answers.vibe.vibe : "serious";
    renderMockup(sector, site, vibe);

    var sectorField = document.getElementById("f-sector");
    if (!sectorField.value) sectorField.value = sector === "شيء آخر" ? "" : sector;

    qwrap.style.display = "none";
    qresult.classList.add("on");
    mascotCheer();
    confetti(document.getElementById("qcard"), 18);
    track("roast_complete", { sector: sector, site: site, vibe: vibe });
  }

  document.getElementById("qagain").addEventListener("click", function(){
    qi = 0; answers = {}; busy = false; say.textContent = "";
    qresult.classList.remove("on"); qwrap.style.display = "";
    mascotThink(false);
    renderQuestion();
  });
  renderQuestion();

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
      document.getElementById("chase").style.display = "none";
      document.getElementById("claimForm").style.display = "none";
      document.getElementById("sPrice").textContent = "نفدت المقاعد";
      paintReceipt("نفدت المقاعد", "\u2014", "نفدت المقاعد");
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
    paintReceipt(money0(price), "\u2212" + money0(VS_TOTAL - price), money0(price));
  }

  function ledgerOffline() {
    document.getElementById("ladderOffline").classList.add("on");
    document.getElementById("ladderList").style.display = "none";
    document.getElementById("pledgeList").innerHTML =
      '<p style="color:var(--muted)">لوحة التعهدات تحتاج السعر المباشر لتعرض لك أرقاماً حقيقية، وهي غير متاحة الآن. ' +
      '<a href="' + WA + '" target="_blank" rel="noopener">اسألني على واتساب</a> وسأشرحها لك.</p>';
    document.getElementById("maths").style.display = "none";
    // No live price on screen means "I want more discount" has nothing to be less than.
    document.getElementById("chase").style.display = "none";
    document.getElementById("sPrice").textContent = "اسألني";
    paintReceipt("اسألني", "\u2014", "اسألني");
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
        if (note) note.textContent = "لا دفع في هذه الصفحة. تصلك فاتورتك بالبريد لحظة الإرسال، والصفحة التالية تستلم العربون بالبطاقة — على صفحة ثواني (Thawani) الآمنة، فلا أرى رقم بطاقتك إطلاقاً.";
      }
      // A sold-out ledger has already stripped the pledge board and the form; running
      // the maths afterwards would put a live price back into the sticky bar.
      if (!state.soldOut) { if (PLEDGES_ON) renderPledges(); renderMaths(); }
    })
    .catch(function(err){ console.warn("ledger unavailable:", err); ledgerOffline(); });

  /* ─────────── 4. the button that runs away ─────────── */
  var btn = document.getElementById("runaway-btn");
  var dodges = 0, caught = false, lastDodge = 0, DODGE_LIMIT = 7;
  // Nothing runs anywhere until the visitor has actually gone for the button.
  var armed = false;
  // Real cursor movement, as opposed to the page scrolling under a parked cursor.
  // Both raise mouseover on this button; only one of them is somebody chasing it.
  var moved = 0;
  document.addEventListener("mousemove", function(){ moved = Date.now(); }, { passive: true });
  var TAUNTS = ["لا.","ليس اليوم.","حاول ثانية.","تقترب.","بارد.","كدت!","الأخيرة…"];

  function flee(e) {
    if (caught) return;
    if (e) e.preventDefault();
    // Without a cooldown the button lands under the moving cursor, fires mouseover again,
    // and burns all seven dodges in one flick of the wrist. Each dodge should be earned.
    if (Date.now() - lastDodge < 260) return;
    lastDodge = Date.now();
    dodges++;

    if (dodges > DODGE_LIMIT) { surrender(); return; }

    var was = btn.getBoundingClientRect();
    puff(was.left + was.width / 2, was.top + was.height / 2);

    var w = btn.offsetWidth, h = btn.offsetHeight, pad = 8;
    // Keep it clear of the sticky bar at the bottom and the nav at the top.
    var x = pad + Math.random() * Math.max(0, window.innerWidth  - w - pad * 2);
    var y = 70 + Math.random() * Math.max(0, window.innerHeight - h - 160);

    btn.classList.add("loose", "squash");
    btn.style.left = x + "px";
    btn.style.top  = y + "px";
    setTimeout(function(){ btn.classList.remove("squash"); }, 180);
    btn.textContent = TAUNTS[dodges - 1] || "أريد خصماً أكبر";
  }

  function surrender() {
    caught = true;
    btn.classList.remove("loose", "squash");
    btn.classList.add("caught");
    btn.style.left = btn.style.top = "";
    btn.textContent = "🏆 أمسكت بي";
    var trophy = document.getElementById("trophy");
    trophy.classList.add("on");
    confetti(btn, 30);
    trophy.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
    track("button_caught", { dodges: dodges });
  }

  // The opening move has to be a genuine attempt at the button. Fleeing on the first
  // hover also fires when the page merely scrolls under a parked cursor, or when the
  // .rv reveal slides the button up into one — and a button that bolts before anyone
  // has touched it reads as a broken layout, not as a joke.
  btn.addEventListener("mousedown", function(e){ armed = true; flee(e); });
  btn.addEventListener("mouseover", function(e){
    if (!armed) return;
    // A mouseover with no cursor movement behind it is the page moving, not the visitor:
    // that is the button landing under a still cursor, and it would burn a free dodge.
    if (Date.now() - moved > 150) return;
    flee(e);
  });

  // Touch is the whole audience here — a mouseover-only version would be inert on a
  // phone. But fleeing on touchstart fires when a swipe merely BEGINS on the button,
  // and the preventDefault() that goes with it kills that scroll too. So the finger has
  // to actually tap: short, and going nowhere.
  var tapAt = 0, tapX = 0, tapY = 0;
  btn.addEventListener("touchstart", function(e){
    var t = e.changedTouches[0];
    tapAt = Date.now(); tapX = t.clientX; tapY = t.clientY;
  }, { passive: true });
  btn.addEventListener("touchend", function(e){
    var t = e.changedTouches[0];
    if (Date.now() - tapAt > 500) return;                                           // a long press
    if (Math.abs(t.clientX - tapX) > 12 || Math.abs(t.clientY - tapY) > 12) return; // a swipe
    armed = true;
    flee(e);   // the preventDefault() inside flee() also cancels the click this tap synthesises
  }, { passive: false });

  // Keyboard users get the joke without the chase: focus doesn't trigger flight, and
  // activating it simply surrenders. An unreachable control is not a joke, it's a trap.
  // A mouse click only counts as a catch once the chase is on and the button has come to
  // rest — the click that ends the very press which sent it running is not a catch.
  btn.addEventListener("click", function(e){
    if (caught) return;
    if (e.detail === 0) { surrender(); return; }
    if (dodges > 0 && Date.now() - lastDodge > 600) surrender();
  });

  /* ─────────── 5. the claim ─────────── */
  var form = document.getElementById("claimForm");
  var submitBtn = document.getElementById("fSubmit");
  var formErr = document.getElementById("formErr");

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
      companyUrl:  document.getElementById("f-companyurl").value.trim(),
      consent:     document.getElementById("f-consent").checked,
      pledges:     chosen,
      caughtButton: caught,
      // Ignored by the service today (routes/claim.js reads a fixed key list),
      // and sent anyway so the row and the invoice can be told which language
      // the buyer arrived in the day that side speaks Arabic.
      lang: "ar"
    };

    if (!payload.name || !payload.business || !payload.sector || !payload.whatsapp || !payload.email) {
      return fail("بقيت حقول فارغة — الاسم، واسم النشاط، وما تبيعه، ورقم واتساب، والبريد، كلها لازمة لكتابة اتفاقك.");
    }
    if (!payload.consent) {
      return fail("أحتاج إذنك لحفظ هذه البيانات والتواصل معك، وإلا لا أستطيع إرسال اتفاق لك.");
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "أحجز مقعدك…";

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
        track("claim_submitted", { pledges: chosen.length, caught_button: caught });
        window.location.href = "/en/pay/?ref=" + encodeURIComponent(res.body.ref) + "&new=1";
      })
      .catch(function(){
        fail("لم أستطع الوصول إلى الخادم. اتصالك أو خادمي — في الحالتين، راسلني على واتساب ولن يضيع شيء.");
      });
  });

  /* ─────────── 6. the cat ─────────── */
  var cat = document.getElementById("catBtn");
  var catSvg = document.getElementById("catSvg");
  var curtain = document.getElementById("curtain");

  function wake() {
    catSvg.classList.add("awake");
    catSvg.querySelectorAll(".cat-shut").forEach(function(e){ e.style.display = "none"; });
    curtain.classList.add("on");
    document.getElementById("curtainClose").focus();
    track("cat_woken");
  }
  function sleep() {
    catSvg.classList.remove("awake");
    catSvg.querySelectorAll(".cat-shut").forEach(function(e){ e.style.display = ""; });
    curtain.classList.remove("on");
    cat.focus();
  }
  cat.addEventListener("click", function(){ curtain.classList.contains("on") ? sleep() : wake(); });
  document.getElementById("curtainClose").addEventListener("click", sleep);
  document.addEventListener("keydown", function(e){ if (e.key === "Escape" && curtain.classList.contains("on")) sleep(); });
})();
</script>
    <script defer src="/js/aiden-chat.js?v=3762fcc3"></script>
</body>
</html>
"""


# The mirror layer is a set of overrides keyed on the English page's own class
# names. Rename one there and the Arabic page loses that rule silently - the
# page still renders, it just renders wrong, in a language its author can't
# read. So the build asserts the hooks are still there.
HOOKS = [
    ".brand{", ".paper{", ".paper .pbrand{", ".ptop b{", ".bub.en{", ".opt{",
    ".opt::after{", ".qdot::after{", ".card::before{", ".mrow b{", ".vow{",
    ".seatbar i{", ".sc-pips i.open{", ".pledge:hover{", ".trophy{", ".hp{",
    ".sticky .info{", ".nav-lang{", ".sc-count span{", ".pledge .txt span{", ".pbody{",
    ".vs-val{", ".vs-row.core{",
    '.mockup[data-vibe="plain"] .plist{',
]


def build():
    src = SRC.read_text(encoding="utf-8")

    m = re.search(r"<style>\n(.*?)\n</style>", src, re.S)
    if not m:
        sys.exit(f"no <style> block found in {SRC} - has the page been restructured?")
    css = m.group(1)

    missing = [h for h in HOOKS if h not in css]
    if missing:
        sys.exit("the English stylesheet no longer carries: " + ", ".join(missing) +
                 "\nUpdate the MIRROR section of RTL_CSS before rebuilding.")

    if 'hreflang="ar"' not in src:
        sys.exit(f"{SRC.name} carries no hreflang back to the Arabic page.\n"
                 "hreflang has to be reciprocal or it is ignored, and a visitor who lands\n"
                 "on the wrong language has no way across. Add the alternate links and the\n"
                 ".nav-lang switch to the English page first.")

    out = (HEAD.replace("__CSS__", css + "\n" + RTL_CSS)
               .replace("__AR_URL__", AR_URL)
               .replace("__EN_URL__", EN_URL)
           + BODY.replace("__EN_PATH__", "/en/smart-storefront/")
           + JS)

    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(out):,} bytes, "
          f"{len(css.splitlines()):,} lines of CSS carried over from the English page)")


if __name__ == "__main__":
    build()
