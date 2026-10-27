#!/usr/bin/env python3
"""
Build the Arabic free-demo page.

    python3 tools/free-demo/build_free_demo_ar.py           # write it
    python3 tools/free-demo/build_free_demo_ar.py --check   # exit 1 if it is stale

    public_html/en/free-demo.html   ->   public_html/free-demo-ar.html
              /en/free-demo/                     /free-demo-ar/

The Arabic page is GENERATED from the English one by string substitution, the
way tools/build_pay_ar.py makes /pay-ar/. The markup, the CSS and the whole
script carry over byte for byte, so the form, the Apps Script endpoint, the
GA4 events and the Google Ads conversions are literally the same code in both
languages. A fix made to the English page reaches the Arabic one on the next
build, and there is no second copy for a payment-style bug to hide in.

What this file owns:
  1. SWAPS: every English string the visitor can see or hear, and its Arabic.
     Each English fragment must occur in the source exactly the stated number
     of times, or the build stops. Reword a line in en/free-demo.html without
     updating the row here and this script refuses to run: that is the feature.
  2. RTL_CSS: an `[dir=rtl]` layer appended after the English sheet. Type
     first (Markazi Text / IBM Plex Sans Arabic, no tracking on Arabic), then
     isolation, then the short list of declarations that name a physical side.

The six demos in the hero and the peak are recordings of real pages (most of
them Arabic-first), so they are the same files on both pages; only the words
around them change, including the demos' trades and places in the #worlds JSON.

Arabic a native reader has not passed yet is every SWAPS row whose
provenance does not start with "reviewed". Each build renders those rows to
build/free-demo-ar-review.html for the reviewer. When the reviewer corrects a
line, edit its Arabic here; when they pass one, change its provenance to
"reviewed <date>" so it leaves the review page.

The URL follows the site's `-ar` convention: a root `<name>-ar.html`, served at
`/<name>-ar/` by .htaccess rule 5, so no rewrite rule is needed.
"""
import html
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "public_html" / "en" / "free-demo.html"
OUT = ROOT / "public_html" / "free-demo-ar.html"
REVIEW = ROOT / "build" / "free-demo-ar-review.html"

EN_URL = "https://aiprofitlab.io/en/free-demo/"
AR_URL = "https://aiprofitlab.io/free-demo-ar/"

# "مرحباً ناهد،" and "لدي سؤال عن" are the reviewed WhatsApp greeting
# (kit.py wa_short / wa_intro); the object of the question is new.
WA_TEXT = "مرحباً ناهد، لدي سؤال عن النموذج المجاني للموقع."
# api.whatsapp.com, never wa.me: a mobile network blocked DNS for wa.me (2026-10-27).
WA_EN = "https://api.whatsapp.com/send?phone=96899245250&amp;text=Hi%2C%20a%20question%20about%20the%20free%20website%20demo"
WA_AR = "https://api.whatsapp.com/send?phone=96899245250&amp;text=" + urllib.parse.quote(WA_TEXT)

# The page's three arrow buttons point the way Arabic reads.
ARROW_EN = 'M4 10h11m-4-4 4 4-4 4'
ARROW_AR = 'M16 10H5m4-4-4 4 4 4'

R_SITE = "reviewed: live Arabic site"
R_STORE = "reviewed: smart-storefront-ar.html"
R_LEGAL = "reviewed: checkout-ar / smart-storefront-ar footer"


# ══════════════════════════════════════════════════════════════════════════
# SWAPS: (section, English fragment, Arabic fragment, count, provenance).
# Applied in order.
# ══════════════════════════════════════════════════════════════════════════
SWAPS = [
    # ── head ──────────────────────────────────────────────────────────────
    ("head", '<html lang="en" dir="ltr">', '<html lang="ar" dir="rtl">', 1, "markup"),
    ("نتائج البحث",
     "<title>Free Website Demo for Your Business in Oman · AI Profit Lab</title>",
     "<title>تصميم موقع الكتروني لنشاطك في عُمان: نموذج مجاني خلال 24 ساعة · AI Profit Lab</title>", 1,
     "new; carries the search phrase as Oman types it (no hamza), like smart-storefront-ar"),
    ("نتائج البحث",
     'content="See your new website in 24 hours, free. A demo homepage in your logo, colours and photos, in English and Arabic. No payment, no call." />',
     'content="شاهد موقعك الجديد خلال 24 ساعة، مجاناً. صفحة رئيسية تجريبية بشعارك وألوانك وصورك، بالعربية والإنجليزية. بلا دفع، وبلا مكالمة." />', 1, "new"),
    ("مشاركة الرابط",
     '<meta property="og:title" content="See your new website in 24 hours. Free." />',
     '<meta property="og:title" content="شاهد موقعك الجديد خلال 24 ساعة. مجاناً." />', 1, "new"),
    ("مشاركة الرابط",
     '<meta property="og:description" content="A free demo homepage in your brand, in English and Arabic, within 24 hours. No call needed." />',
     '<meta property="og:description" content="صفحة رئيسية تجريبية مجانية بهويتك، بالعربية والإنجليزية، خلال 24 ساعة. بلا مكالمة." />', 1, "new"),
    ("head", '<meta property="og:url" content="%s" />' % EN_URL, '<meta property="og:url" content="%s" />' % AR_URL, 1, "markup"),
    ("head", '<link rel="canonical" href="%s" />' % EN_URL, '<link rel="canonical" href="%s" />' % AR_URL, 1, "markup"),
    ("head",
     "family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap",
     "family=Markazi+Text:wght@400;500;600&family=IBM+Plex+Sans+Arabic:wght@400;500;600&family=Marcellus&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap",
     3, "markup"),

    # ── header ────────────────────────────────────────────────────────────
    ("الترويسة", '<a class="logo" href="/" aria-label="AI Profit Lab home">',
     '<a class="logo" href="/ar/" aria-label="AI Profit Lab — الصفحة الرئيسية">', 1, R_STORE),
    # the header, the phone bar and the footer share one WhatsApp link
    ("الترويسة", 'href="%s"' % WA_EN, 'href="%s"' % WA_AR, 3,
     "new (the WhatsApp message's greeting is reviewed)"),
    ("الترويسة", 'target="_blank" rel="noopener">Questions? <b>WhatsApp</b></a>',
     'target="_blank" rel="noopener">أسئلة؟ <b>واتساب</b></a>', 1, "new"),
    ("الترويسة", '<a class="hdr-lang" href="/free-demo-ar/" hreflang="ar" lang="ar">عربي</a>',
     '<a class="hdr-lang" href="/en/free-demo/" hreflang="en" lang="en" aria-label="English">'
     '<span class="hl-long">English</span><span class="hl-short" aria-hidden="true">EN</span></a>', 1, "markup"),
    ("الترويسة", '<span class="chip-t" id="chipT">Get my free demo</span>',
     '<span class="chip-t" id="chipT">اطلب نموذجك المجاني</span>', 1, "new"),

    # ── hero ──────────────────────────────────────────────────────────────
    ("أعلى الصفحة", '<p class="eyebrow">Free website demo · Oman</p>',
     '<p class="eyebrow">تصميم موقع الكتروني · نموذج مجاني</p>', 1, "new; carries the search phrase"),
    ("أعلى الصفحة", '<h1>See your new website in 24&nbsp;hours. <span class="free">Free.</span></h1>',
     '<h1>شاهد موقعك الجديد خلال 24&nbsp;ساعة. <span class="free">مجاناً.</span></h1>', 1, "new"),
    ("أعلى الصفحة", '<p class="lede">Type your business name. Watch.</p>',
     '<p class="lede">اكتب اسم نشاطك. وشاهد.</p>', 1, "new"),
    ("أعلى الصفحة", '<label for="nameIn" class="sr">Your business name</label>',
     '<label for="nameIn" class="sr">اسم نشاطك التجاري</label>', 1, "new"),
    ("أعلى الصفحة", 'placeholder="Your business name" maxlength="40"',
     'placeholder="اسم نشاطك التجاري" maxlength="40" dir="auto"', 1, "new"),
    ("أعلى الصفحة", 'data-cta="hero">Get my free demo', 'data-cta="hero">اطلب نموذجك المجاني', 1, "new"),
    ("أعلى الصفحة", '<p class="trust">No payment<i>✼</i>No call<i>✼</i>English + <span lang="ar">عربي</span></p>',
     '<p class="trust">بلا دفع<i>✼</i>بلا مكالمة<i>✼</i>عربي + <span lang="en">English</span></p>', 1, "new"),
    ("أعلى الصفحة", '<span id="giant" dir="auto">Vet</span>', '<span id="giant" dir="auto">بيطري</span>', 1,
     "new 2026-10-27; the first demo's word, before the script takes over"),
    ("أعلى الصفحة", '<span class="tag">Real demos · names hidden</span>',
     '<span class="tag">نماذج حقيقية · الأسماء مخفية</span>', 1, "new 2026-10-27"),
    ("أعلى الصفحة", '<p class="w-cap" id="wCap"><b>Vet clinic</b> · Muscat<span class="w-lang"> · English + Arabic</span></p>',
     '<p class="w-cap" id="wCap"><b>عيادة بيطرية</b> · مسقط<span class="w-lang"> · إنجليزي + عربي</span></p>', 1,
     "new 2026-10-27; the words of the old demo-rail caption"),
    ("أعلى الصفحة", 'aria-label="The demos"', 'aria-label="النماذج"', 1, "new 2026-10-27"),
    ("أعلى الصفحة", 'aria-label="Pause the demos"', 'aria-label="أوقف عرض النماذج"', 1, "new 2026-10-27"),
    ("الشاشة السابعة",
     '<p class="y-k"><i class="y-dot"></i>Designing next</p><p class="y-n empty" data-b="yname" dir="auto">Your business</p><p class="y-e">Unveiled <b data-eta></b></p>',
     '<p class="y-k"><i class="y-dot"></i>قيد التصميم</p><p class="y-n empty" data-b="yname" dir="auto">نشاطك</p><p class="y-e">جاهز قبل <b data-eta></b></p>', 3,
     "new 2026-10-27; the visitor's own screen, with the live delivery time"),

    # ── the six demos' words (the #worlds JSON) ──
    ("النماذج", '"trade": "Vet clinic", "word": "Vet", "where": "Muscat", "langs": "English + Arabic"',
     '"trade": "عيادة بيطرية", "word": "بيطري", "where": "مسقط", "langs": "إنجليزي + عربي"', 1, "new 2026-10-27"),
    ("النماذج", '"trade": "Perfume & bakhoor", "word": "Bakhoor", "where": "Dhofar", "langs": "Arabic + English"',
     '"trade": "عطور وبخور", "word": "بخور", "where": "ظفار", "langs": "عربي + إنجليزي"', 1, "new 2026-10-27"),
    ("النماذج", '"trade": "Private rest house", "word": "Rest house", "where": "Al Batinah", "langs": "Arabic + English"',
     '"trade": "استراحة خاصة", "word": "استراحة", "where": "الباطنة", "langs": "عربي + إنجليزي"', 1, "new 2026-10-27"),
    ("النماذج", '"trade": "Kids\' salon", "word": "Kids\' salon", "where": "Muscat & Sohar", "langs": "Arabic + English"',
     '"trade": "صالون أطفال", "word": "صالون أطفال", "where": "مسقط وصحار", "langs": "عربي + إنجليزي"', 1, "new 2026-10-27"),
    ("النماذج", '"trade": "Heritage café", "word": "Café", "where": "Muscat", "langs": "Arabic + English"',
     '"trade": "مقهى تراثي", "word": "مقهى", "where": "مسقط", "langs": "عربي + إنجليزي"', 1, "new 2026-10-27"),
    ("النماذج", '"trade": "Ladies\' salon", "word": "Salon", "where": "Al Batinah", "langs": "Arabic + English"',
     '"trade": "صالون نسائي", "word": "صالون", "where": "الباطنة", "langs": "عربي + إنجليزي"', 1, "new 2026-10-27"),

    # ── the dive ──────────────────────────────────────────────────────────
    ("الغوص", '<h2>Six businesses. <span>Six different demos.</span></h2>',
     '<h2>ستة أنشطة. <span>ستة نماذج مختلفة.</span></h2>', 1, "new 2026-10-27"),
    ("الغوص", '<p class="note">Not&nbsp;clients<i>✼</i><wbr>names&nbsp;hidden<i>✼</i><wbr>no&nbsp;two&nbsp;alike</p>',
     '<p class="note">ليسوا&nbsp;عملاء<i>✼</i><wbr>الأسماء&nbsp;مخفية<i>✼</i><wbr>لا&nbsp;يتشابه&nbsp;نموذجان</p>', 1, "new; moved from the demo rail 2026-10-27"),
    ("الغوص", '<p class="dive-line" id="diveLine" aria-hidden="true">Made for a vet clinic.</p>',
     '<p class="dive-line" id="diveLine" aria-hidden="true">صُمّم لعيادة بيطرية.</p>', 1, "new 2026-10-27"),
    ("الغوص", '<i class="y-dot"></i>Next<b data-b="name" dir="auto">your business</b>',
     '<i class="y-dot"></i>التالي<b data-b="name" dir="auto">نشاطك</b>', 1, "new 2026-10-27"),
    ("الغوص", '<figcaption class="tl-cap">Perfume &amp; bakhoor · Dhofar</figcaption>', '<figcaption class="tl-cap">عطور وبخور · ظفار</figcaption>', 1, "new"),
    ("الغوص", '<figcaption class="tl-cap">Private rest house · Al Batinah</figcaption>', '<figcaption class="tl-cap">استراحة خاصة · الباطنة</figcaption>', 1, "new"),
    ("الغوص", "<figcaption class=\"tl-cap\">Kids' salon · Muscat &amp; Sohar</figcaption>", '<figcaption class="tl-cap">صالون أطفال · مسقط وصحار</figcaption>', 1, "new"),
    ("الغوص", '<figcaption class="tl-cap">Vet clinic · Muscat</figcaption>', '<figcaption class="tl-cap">عيادة بيطرية · مسقط</figcaption>', 1, "new"),
    ("الغوص", '<figcaption class="tl-cap">Heritage café · Muscat</figcaption>', '<figcaption class="tl-cap">مقهى تراثي · مسقط</figcaption>', 1, "new"),
    ("الغوص", "<figcaption class=\"tl-cap\">Ladies' salon · Al Batinah</figcaption>", '<figcaption class="tl-cap">صالون نسائي · الباطنة</figcaption>', 1, "new"),
    ("الغوص", 'data-cta="peak">Make mine', 'data-cta="peak">اصنع نموذجي', 1, "new"),
    ("الغوص", '<span>Free · under 24 hours</span>', '<span>مجاناً · في أقل من 24 ساعة</span>', 2, "new; also the order slip's header"),

    # ── the demos' alt text (the wall in the dive) ─────────────────────────
    ("النماذج", 'alt="Arabic homepage demo for a perfume and bakhoor shop, name hidden"',
     'alt="نموذج صفحة رئيسية بالعربية لمحل عطور وبخور، الاسم مخفي"', 1, "new"),
    ("النماذج", 'alt="English homepage demo for a vet clinic, name hidden"',
     'alt="نموذج صفحة رئيسية بالإنجليزية لعيادة بيطرية، الاسم مخفي"', 1, "new"),
    ("النماذج", 'alt="Arabic homepage demo for a private rest house with a pool, name hidden"',
     'alt="نموذج صفحة رئيسية بالعربية لاستراحة خاصة بمسبح، الاسم مخفي"', 1, "new"),
    ("النماذج", 'alt="Arabic homepage demo for an Omani heritage café, name hidden"',
     'alt="نموذج صفحة رئيسية بالعربية لمقهى تراثي عُماني، الاسم مخفي"', 1, "new"),
    ("النماذج", "alt=\"Arabic homepage demo for a ladies' salon, name hidden\"",
     'alt="نموذج صفحة رئيسية بالعربية لصالون نسائي، الاسم مخفي"', 1, "new"),
    ("النماذج", "alt=\"Arabic homepage demo for a children's hair salon, name hidden\"",
     'alt="نموذج صفحة رئيسية بالعربية لصالون حلاقة للأطفال، الاسم مخفي"', 1, "new"),

    # ── why free ──────────────────────────────────────────────────────────
    ("لماذا مجاني", '<h2 class="rv">Why is it free?</h2>', '<h2 class="rv">لماذا هو مجاني؟</h2>', 1, "new"),
    ("لماذا مجاني",
     '<p class="big rv">So I can post it on\n            <a href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener">@ai.profit.lab.gcc</a>,\n            with your name hidden.</p>',
     '<p class="big rv">لأنشره على\n            <a dir="ltr" href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener">@ai.profit.lab.gcc</a>،\n            مع إخفاء اسمك.</p>', 1,
     "new; the handle is isolated so its @ stays in front"),
    ("لماذا مجاني", '<span>No payment</span></li>', '<span>بلا دفع</span></li>', 1, "new"),
    ("لماذا مجاني", '<span>No call</span></li>', '<span>بلا مكالمة</span></li>', 1, "new"),
    ("لماذا مجاني", '<span>Nobody chases you</span></li>', '<span>لن يلاحقك أحد</span></li>', 1, "new"),
    ("لماذا مجاني", '<span>Post removed on request</span></li>', '<span>يُحذف المنشور عند طلبك</span></li>', 1, "new"),
    ("لماذا مجاني", 'aria-label="How the sample post would look, with your name hidden"',
     'aria-label="شكل المنشور التجريبي، مع إخفاء اسمك"', 1, "new"),
    ("لماذا مجاني", '<b>ai.profit.lab.gcc</b><span>Sample</span></div>', '<b>ai.profit.lab.gcc</b><span>نموذج</span></div>', 1, "new"),
    ("لماذا مجاني",
     '<b>ai.profit.lab.gcc</b> Website demo for a heritage café in Oman, in English and Arabic.<br>\n            <span class="hide">Business name, logo and contact details removed</span>',
     '<b>ai.profit.lab.gcc</b> نموذج موقع مقهى تراثي في عُمان، بالعربية والإنجليزية.<br>\n            <span class="hide">حُذف اسم النشاط والشعار وبيانات التواصل</span>', 1, "new; the café is now named, 2026-10-27"),

    # ── answers ───────────────────────────────────────────────────────────
    ("أسئلة", '<h2 class="rv">Straight answers.</h2>', '<h2 class="rv">إجابات مباشرة.</h2>', 1,
     "smart-storefront-ar heading (itself still awaiting review)"),
    ("أسئلة", '<summary>What exactly do I get?<i aria-hidden="true"></i></summary>',
     '<summary>ماذا أحصل عليه بالضبط؟<i aria-hidden="true"></i></summary>', 1, "new"),
    ("أسئلة", "<p>A link to a homepage in your brand, in English and Arabic, for phones and computers. It's a demo: not the full website, and not on your own domain yet.</p>",
     "<p>رابط لصفحة رئيسية بهويتك، بالعربية والإنجليزية، للهاتف والكمبيوتر. إنها نموذج تجريبي: ليست الموقع الكامل، وليست على نطاقك الخاص بعد.</p>", 1, "new"),
    ("أسئلة", '<summary>Is it a template?<i aria-hidden="true"></i></summary>',
     '<summary>هل هو قالب جاهز؟<i aria-hidden="true"></i></summary>', 1, "new 2026-10-26"),
    ("أسئلة", "<p>No. I design each one from your Instagram or Maps photos, your colours and your words. It's quick because it's one homepage, not a whole website.</p>",
     "<p>لا. أصمّم كل نموذج من صورك على إنستغرام أو خرائط جوجل، وألوانك، وكلماتك. وهو سريع لأنه صفحة رئيسية واحدة، لا موقع كامل.</p>", 1, "new 2026-10-26"),
    ("أسئلة", '<summary>What do you need from me?<i aria-hidden="true"></i></summary>',
     '<summary>ماذا تحتاج مني؟<i aria-hidden="true"></i></summary>', 1, "new"),
    ("أسئلة", "<p>Your business name and your Instagram, website or Google Maps page. No page yet? Tell me what you sell.</p>",
     "<p>اسم نشاطك، وحسابك على إنستغرام أو موقعك أو صفحتك على خرائط جوجل. ليست لديك صفحة بعد؟ أخبرني بما تبيع.</p>", 1, "new"),
    ("أسئلة", '<summary>What if I like it?<i aria-hidden="true"></i></summary>',
     '<summary>وإن أعجبني؟<i aria-hidden="true"></i></summary>', 1, "new"),
    ("أسئلة", "<p>Reply. I'll quote the full website: one fixed price, paid once, no monthly retainer. You decide in your own time.</p>",
     "<p>ردّ عليّ، وأرسل لك سعر الموقع الكامل: سعر ثابت واحد، يُدفع مرة واحدة، بِلا اشتراك شهري. والقرار لك، في وقتك.</p>", 1,
     "new; “بِلا اشتراك شهري” is the reviewed phrase from smart-storefront-ar"),
    ("أسئلة", '<summary>Who are you?<i aria-hidden="true"></i></summary>',
     '<summary>من أنت؟<i aria-hidden="true"></i></summary>', 1, "new"),
    ("أسئلة", "<p>Nahid Abyari, an engineer who has designed and run a real distribution business. AI Profit Lab is my studio in Muscat. Every demo is made here, not by a template site.</p>",
     "<p>ناهيد أبياري، مهندس صمّم وأدار نشاط توزيع حقيقياً. و<span dir=\"ltr\">AI Profit Lab</span> هو الاستوديو الخاص بي في مسقط. كل نموذج يُصنع هنا، لا في موقع قوالب.</p>", 1,
     "new; the name is the reviewed signature on smart-storefront-ar"),

    # ── the order slip ────────────────────────────────────────────────────
    ("النموذج", '<p class="eyebrow" style="color:var(--amber-pale)">Your free demo</p>',
     '<p class="eyebrow" style="color:var(--amber-pale)">نموذجك المجاني</p>', 1, "new"),
    ("النموذج", '<h2>Where should I send it?</h2>', '<h2>إلى أين أرسله؟</h2>', 1, "new"),
    ("النموذج", '<li><b>01</b>You send this<span>30 seconds</span></li>', '<li><b>01</b>ترسل هذا<span>30 ثانية</span></li>', 1, "new"),
    ("النموذج", '<li><b>02</b>I design it from your Instagram<span>Under 24 hours</span></li>',
     '<li><b>02</b>أصمّمه من إنستغرامك<span>أقل من 24 ساعة</span></li>', 1, "new; reworded 2026-10-26"),
    ("النموذج", '<li><b>03</b>You get a link<span class="due" data-eta="by">Yours to keep</span></li>',
     '<li><b>03</b>يصلك رابط<span class="due" data-eta="by">لك تحتفظ به</span></li>', 1, "new; replaced by the live time once the script runs"),
    ("النموذج", '<span class="tag" id="orderTag">Draft for <span data-b="name">your business</span></span>',
     '<span class="tag" id="orderTag">مسودة <span data-b="name" dir="auto">نشاطك</span></span>', 1, "new"),
    ("النموذج", '<div class="slip-head"><b>Demo order</b>', '<div class="slip-head"><b>طلب نموذج</b>', 1, "new"),
    ("النموذج", '<label for="fBiz">Business name</label>', '<label for="fBiz">اسم النشاط التجاري</label>', 1, R_STORE),
    ("النموذج", 'placeholder="e.g. Al Wadi Supplies" />', 'placeholder="مثلاً: الوادي للتوريدات" dir="auto" />', 1, "new; “مثلاً:” as on smart-storefront-ar"),
    ("النموذج", '<label for="fLink">Your Instagram, website or Maps link <em>(optional)</em></label>',
     '<label for="fLink">رابط إنستغرام أو موقعك أو خرائط جوجل <em>(اختياري)</em></label>', 1, "new"),
    ("النموذج", 'placeholder="@yourbrand, or just what you sell" autocomplete="url"',
     'placeholder="ما تبيعه، أو ‎@yourbrand" autocomplete="url" dir="auto"', 1, "new"),
    ("النموذج", '<span class="lbl" id="whenLbl">When do you want it live?</span>',
     '<span class="lbl" id="whenLbl">متى تريد إطلاقه؟</span>', 1, "new"),
    ("النموذج", 'data-when="This month">This month</button>', 'data-when="This month">هذا الشهر</button>', 1, "new"),
    ("النموذج", 'data-when="1-3 months">1–3 months</button>',
     'data-when="1-3 months"><span dir="ltr">1–3</span> أشهر</button>', 1,
     "new; the range is isolated, or RTL turns 1–3 into 3–1"),
    ("النموذج", 'data-when="Just looking">Just looking</button>', 'data-when="Just looking">أتفرّج فقط</button>', 1, "new"),
    ("النموذج", '<span class="lbl" id="viaLbl">Send the demo to my</span>',
     '<span class="lbl" id="viaLbl">أرسل النموذج إلى</span>', 1, "new"),
    ("النموذج", '</svg>WhatsApp</button>', '</svg>واتساب</button>', 1, R_SITE),
    ("النموذج", '</svg>Email</button>', '</svg>البريد</button>', 1, "new (brand-discovery uses the same word)"),
    ("النموذج", '<label for="fWa">WhatsApp number</label>', '<label for="fWa">رقم واتساب</label>', 1, R_STORE),
    ("النموذج", 'maxlength="20" placeholder="9X XX XX XX" />', 'maxlength="20" placeholder="9X XX XX XX" dir="ltr" />', 1, "markup"),
    ("النموذج", '<label for="fEm">Email</label>', '<label for="fEm">البريد الإلكتروني</label>', 1, R_STORE),
    ("النموذج", 'placeholder="you@business.com" />', 'placeholder="you@business.com" dir="ltr" />', 1, "markup"),
    ("النموذج", '<span class="lbl">Logo file <em>(optional)</em></span>', '<span class="lbl">ملف الشعار <em>(اختياري)</em></span>', 1, "new"),
    ("النموذج", '<span id="dropT"><b>Add your logo</b> · up to 5 MB</span>',
     '<span id="dropT"><b>أضف شعارك</b> · حتى 5 ميغابايت</span>', 1, "new"),
    ("النموذج",
     '<span>You may post the finished design on @ai.profit.lab.gcc as a sample, with my business name, logo and contact details removed.</span>',
     '<span>أوافق على نشر التصميم النهائي على <span dir="ltr">@ai.profit.lab.gcc</span> كنموذج، بعد حذف اسم نشاطي وشعاري وبيانات التواصل.</span>', 1, "new"),
    ("النموذج", 'id="fSend">Send me my free demo</button>', 'id="fSend">أرسل لي نموذجي المجاني</button>', 1, "new"),
    ("النموذج",
     "<p class=\"slip-eta\">Send now, and it's <span id=\"etaVia\">on your WhatsApp</span> by <b data-eta>this time tomorrow</b></p>",
     '<p class="slip-eta">أرسل الآن، ويصلك <span id="etaVia">على واتساب</span> قبل <b data-eta>هذا الوقت غداً</b></p>', 1, "new"),
    ("النموذج", '<p class="slip-note">Used only to send your demo · <a href="/privacy/">Privacy</a></p>',
     '<p class="slip-note">لا تُستخدم بياناتك إلا لإرسال نموذجك · <a href="/privacy-ar/">الخصوصية</a></p>', 1,
     "new (“الخصوصية” is reviewed)"),
    ("بعد الإرسال", '</svg>Received</span>', '</svg>تم الاستلام</span>', 1, "new"),
    ("بعد الإرسال", '<h3 id="doneH">Your demo is in the queue.</h3>', '<h3 id="doneH">نموذجك في قائمة الانتظار.</h3>', 1, "new"),
    ("بعد الإرسال", "<p>Nothing else to do. If you'd like to add something, reply when it arrives.</p>",
     "<p>لا شيء آخر عليك فعله. وإن أردت إضافة شيء، ردّ عليّ حين يصلك.</p>", 1, "new"),

    # ── footer and the phone bar ──────────────────────────────────────────
    ("التذييل", '<p>Every success starts with insight.</p>', '<p>كل نجاح يبدأ برؤية.</p>', 1, "reviewed: the locked slogan"),
    ("التذييل",
     '<a href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener">Instagram</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a>',
     '<a href="https://www.instagram.com/ai.profit.lab.gcc/" target="_blank" rel="noopener">إنستغرام</a><a href="/privacy-ar/">الخصوصية</a><a href="/terms-ar/">شروط الخدمة</a>', 1, R_LEGAL),
    ("التذييل",
     '<p>© 2026 AI Profit Lab, a brand of Lotus Gulf International (CR 1570092) · South Al Khuwair, Bousher, Muscat, Oman</p>',
     '<p><span dir="ltr">© 2026 AI Profit Lab</span> — علامة تجارية تابعة لشركة Lotus Gulf International (س.ت <span dir="ltr">1570092</span>) · الخوير الجنوبية، بوشر، مسقط، سلطنة عُمان</p>', 1, R_LEGAL),
    ("التذييل", 'target="_blank" rel="noopener">WhatsApp</a>', 'target="_blank" rel="noopener">واتساب</a>', 1,
     "reviewed: kit.py whatsapp"),
    ("أسفل الهاتف", 'data-cta="sticky">Get my free demo</a>', 'data-cta="sticky">اطلب نموذجك المجاني</a>', 1, "new"),
    ("أسفل الهاتف", 'aria-label="Chat with Nahid on WhatsApp"', 'aria-label="راسل ناهد على واتساب"', 1,
     "reviewed: kit.py wa_aria"),

    # ── the script's words ────────────────────────────────────────────────
    ("الشريط العلوي",
     'chipT.appendChild(document.createTextNode(window.innerWidth < 560 ? "Free demo" : "Free demo for "));',
     'chipT.appendChild(document.createTextNode(window.innerWidth < 560 ? "نموذج مجاني" : "نموذج "));', 1,
     "new; with a name: “نموذج مقهى السدر”"),
    ("الشريط العلوي", 'chip.setAttribute("aria-label", "Get my free demo for " + state.name);',
     'chip.setAttribute("aria-label", "اطلب نموذجك المجاني: " + state.name);', 1, "new"),
    ("الشريط العلوي", 'chipT.textContent = window.innerWidth < 560 ? "Free demo" : "Get my free demo";',
     'chipT.textContent = window.innerWidth < 560 ? "نموذج مجاني" : "اطلب نموذجك المجاني";', 1, "new"),
    ("النموذج", 'el.textContent = state.typed && state.name ? state.name : "your business";',
     'el.textContent = state.typed && state.name ? state.name : "نشاطك";', 1, "new"),
    ("أعلى الصفحة",
     'var TXT = { yours: "Yours", yourBiz: "Your business", fromIg: "from your Instagram", show: "Show: ", pause: "Pause the demos", play: "Play the demos" };',
     'var TXT = { yours: "نموذجك", yourBiz: "نشاطك", fromIg: "من إنستغرامك", show: "اعرض: ", pause: "أوقف عرض النماذج", play: "شغّل عرض النماذج" };', 1,
     "new 2026-10-27; the seventh screen's caption reads “نموذجك · من إنستغرامك”"),
    ("النموذج", '$("#etaVia").textContent = via === "whatsapp" ? "on your WhatsApp" : "in your inbox";',
     '$("#etaVia").textContent = via === "whatsapp" ? "على واتساب" : "على بريدك";', 1, "new"),
    ("النموذج", '(el.getAttribute("data-eta") === "by" ? "By " : "")', '(el.getAttribute("data-eta") === "by" ? "قبل " : "")', 1, "new"),
    ("النموذج", 'dropT.textContent = "That file is over 5 MB. Try a smaller one.";',
     'dropT.textContent = "الملف أكبر من 5 ميغابايت. جرّب ملفاً أصغر.";', 1, "new"),
    ("أخطاء النموذج", '"Your business name, so the demo carries it."', '"اكتب اسم نشاطك، ليظهر في النموذج."', 1, "new"),
    ("أخطاء النموذج", '"Pick one. Any answer gets a demo."', '"اختر واحداً. كل إجابة تحصل على نموذج."', 1, "new"),
    ("أخطاء النموذج", '"A WhatsApp number, so I can send the link."', '"رقم واتساب، لأرسل لك الرابط."', 1, "new"),
    ("أخطاء النموذج", '"An email address, so I can send the link."', '"عنوان بريد إلكتروني، لأرسل لك الرابط."', 1, "new"),
    ("أخطاء النموذج", '"Tick this to get the free demo. It\'s the one thing I ask."',
     '"أشِّر هنا لتحصل على النموذج المجاني. هذا الشيء الوحيد الذي أطلبه."', 1, "new; “أشِّر على” as on smart-storefront-ar"),
    ("النموذج", 'new Intl.DateTimeFormat("en-GB", {', 'new Intl.DateTimeFormat("ar-OM-u-nu-latn", {', 1,
     "markup; Western digits, as everywhere on the site: “الثلاثاء، 27 أكتوبر، 9:03 ص”"),
    ("رسالة بديلة",
     '"Free website demo request",\n          "Business: " + p.business,\n          "Brand link: " + (p.brandLink || "-"),\n          "Wants it live: " + p.timeline,\n          "Send to: " + (p.via === "whatsapp" ? "WhatsApp " + p.whatsapp : "Email " + p.email),\n          "OK to post as an anonymous sample: yes"',
     '"طلب نموذج موقع مجاني",\n          "النشاط: " + p.business,\n          "الرابط: " + (p.brandLink || "-"),\n          "متى يريده: " + ((($("#whenPick button[aria-pressed=\'true\']") || {}).textContent) || p.timeline),\n          "أرسله إلى: " + (p.via === "whatsapp" ? "واتساب " + p.whatsapp : "البريد " + p.email),\n          "موافق على نشره كنموذج دون اسم: نعم"', 1,
     "new; the message a visitor sends Nahid when the form fails"),
    ("رسالة بديلة", 'box.appendChild(document.createTextNode(why + " Your details are still here. Send them another way: "));',
     'box.appendChild(document.createTextNode(why + " بياناتك ما زالت هنا. أرسلها بطريقة أخرى: "));', 1, "new"),
    ("رسالة بديلة", 'encodeURIComponent("Free website demo: " + p.business)', 'encodeURIComponent("نموذج موقع مجاني: " + p.business)', 1, "new"),
    ("رسالة بديلة", 'm.textContent = "by email";', 'm.textContent = "بالبريد";', 1, "new"),
    ("رسالة بديلة", 'w.textContent = "by WhatsApp";', 'w.textContent = "عبر واتساب";', 1, "new"),
    ("رسالة بديلة", 'box.appendChild(document.createTextNode(" or "));', 'box.appendChild(document.createTextNode(" أو "));', 1, "new"),
    ("رسالة بديلة", 'showFallback(p, "The form isn\'t connected yet.");', 'showFallback(p, "النموذج غير متصل بعد.");', 1, "new"),
    ("رسالة بديلة", 'showFallback(p, "That didn\'t go through.");', 'showFallback(p, "لم يصل طلبك.");', 1, "new"),
    ("النموذج", 'send.textContent = "Sending…";', 'send.textContent = "جارٍ الإرسال…";', 1, "new (brand-discovery uses the same words)"),
    ("النموذج", 'send.textContent = "Send me my free demo";', 'send.textContent = "أرسل لي نموذجي المجاني";', 1, "new"),
    ("المسار", 'lang: "en", page: location.pathname', 'lang: "ar", page: location.pathname', 1, "markup"),
    ("بعد الإرسال", '$("#doneH").textContent = "Your demo for " + p.business + " is in the queue.";',
     '$("#doneH").textContent = "نموذج \\u2068" + p.business + "\\u2069 في قائمة الانتظار.";', 1,
     "new; the name is isolated so a Latin one keeps its place"),
    ("بعد الإرسال",
     'eta.appendChild(document.createTextNode("It will reach your " + (p.via === "whatsapp" ? "WhatsApp" : "inbox") + " by "));',
     'eta.appendChild(document.createTextNode("سيصلك " + (p.via === "whatsapp" ? "على واتساب" : "على بريدك") + " قبل "));', 1, "new"),
    ("بعد الإرسال", 'eta.appendChild(document.createTextNode(", Muscat time."));', 'eta.appendChild(document.createTextNode("، بتوقيت مسقط."));', 1, "new"),
    ("بعد الإرسال", 'tag.textContent = "Draft started · " + p.business;', 'tag.textContent = "بدأت المسودة · \\u2068" + p.business + "\\u2069";', 1, "new"),

    # ── arrows ────────────────────────────────────────────────────────────
    ("markup", ARROW_EN, ARROW_AR, 2, "markup"),
]


# ══════════════════════════════════════════════════════════════════════════
# The RTL layer, appended after the English sheet so a tie goes to it.
# ══════════════════════════════════════════════════════════════════════════
RTL_CSS = r"""
    /* ══════════ Arabic layer: tools/free-demo/build_free_demo_ar.py ══════════ */

    /* ── 1. TYPE ── Fallback metrics measured out of the font files for
       tools/v4/rtl.py: without them the Arabic headings paint a third too large
       in Geeza Pro and snap down when Markazi Text lands. */
    @font-face { font-family: 'Markazi Fallback'; src: local('Geeza Pro'); size-adjust: 74.2%; ascent-override: 113.1%; descent-override: 48.7%; line-gap-override: 0%; }
    @font-face { font-family: 'Markazi Fallback 2'; src: local('Tahoma'), local('Segoe UI'); size-adjust: 66.8%; ascent-override: 125.6%; descent-override: 54.1%; line-gap-override: 0%; }
    @font-face { font-family: 'Plex Arabic Fallback'; src: local('Geeza Pro'); size-adjust: 105.1%; ascent-override: 103.2%; descent-override: 39.5%; line-gap-override: 0%; }
    @font-face { font-family: 'Plex Arabic Fallback 2'; src: local('Tahoma'), local('Segoe UI'); size-adjust: 94.6%; ascent-override: 114.7%; descent-override: 43.9%; line-gap-override: 0%; }
    [dir=rtl] {
      --display: 'Markazi Text', 'Markazi Fallback', 'Markazi Fallback 2', Georgia, serif;
      --sans: 'IBM Plex Sans Arabic', 'Plex Arabic Fallback', 'Plex Arabic Fallback 2', 'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif;
      --mono: 'IBM Plex Mono', 'IBM Plex Sans Arabic', 'Plex Arabic Fallback', ui-monospace, monospace;
    }
    [dir=rtl] .hdr-lang { font-family: 'IBM Plex Sans', -apple-system, sans-serif; }

    /* "English" is twice as wide as "عربي": on phones under 400px the bar
       had no room for it beside the Arabic chip, so it shortens to EN */
    .hl-short { display: none; }
    @media (max-width: 400px) { .hl-long { display: none; } .hl-short { display: inline; } }

    /* Naskh needs more leading than Latin: its dots and descenders collide at 1.65 */
    [dir=rtl] body { line-height: 1.85; }
    [dir=rtl] h1, [dir=rtl] h2, [dir=rtl] h3 { letter-spacing: 0; line-height: 1.3; }
    [dir=rtl] h2 { font-size: clamp(2.2rem, 4.8vw, 3.6rem); }
    [dir=rtl] .hero h1 { font-size: clamp(3rem, 6vw, 5.2rem); line-height: 1.2; max-width: 11ch; }
    [dir=rtl] .peak-head h2 { font-size: clamp(1.9rem, 3.6vw, 2.9rem); line-height: 1.25; }
    [dir=rtl] .deal .big { font-size: clamp(1.6rem, 2.8vw, 2.2rem); line-height: 1.5; }
    [dir=rtl] .slip-head b { font-size: 1.7rem; }
    [dir=rtl] .done h3 { font-size: clamp(1.9rem, 3.4vw, 2.5rem); }
    [dir=rtl] .giant { line-height: 1.15; }
    [dir=rtl] .y-n { line-height: 1.3; }
    [dir=rtl] .next-l b, [dir=rtl] .dive-line { font-size: 1.5rem; line-height: 1.4; }
    @media (max-width: 900px) { [dir=rtl] .hero h1 { font-size: clamp(2.6rem, 10vw, 3.6rem); max-width: 13ch; } }

    /* Tracking and capitals are Latin devices. Letter-spacing on Arabic breaks
       the joins between letters, so every mono label that now carries Arabic
       moves to Plex Sans Arabic, untracked, and a size up (the brand asks for
       no tiny mono Arabic). */
    [dir=rtl] .eyebrow, [dir=rtl] .hdr-q, [dir=rtl] .hero .lede, [dir=rtl] .trust, [dir=rtl] .tag,
    [dir=rtl] .ask span, [dir=rtl] .w-cap, [dir=rtl] .tl-cap, [dir=rtl] .y-k, [dir=rtl] .y-e, [dir=rtl] .next-l,
    [dir=rtl] .peak-head .note, [dir=rtl] .ig-top span, [dir=rtl] .mini span,
    [dir=rtl] .slip-head span, [dir=rtl] .field label, [dir=rtl] .field .lbl, [dir=rtl] .done .stamp {
      letter-spacing: 0; text-transform: none; font-family: var(--sans);
    }
    [dir=rtl] .eyebrow { font-size: .98rem; }
    [dir=rtl] .hdr-q { font-size: .92rem; }
    [dir=rtl] .hero .lede { font-size: 1.12rem; font-weight: 600; }
    [dir=rtl] .trust { font-size: .95rem; }
    [dir=rtl] .tag, [dir=rtl] .ig-top span, [dir=rtl] .slip-head span, [dir=rtl] .mini span { font-size: .88rem; }
    [dir=rtl] .ask span, [dir=rtl] .peak-head .note, [dir=rtl] .w-cap, [dir=rtl] .next-l { font-size: .95rem; }
    [dir=rtl] .tl-cap { font-size: .78rem; }
    [dir=rtl] .y-k, [dir=rtl] .y-e { font-size: 2.8cqw; }
    [dir=rtl] .phone .y-k, [dir=rtl] .phone .y-e { font-size: 5.4cqw; }
    [dir=rtl] .field label, [dir=rtl] .field .lbl { font-size: .92rem; }
    [dir=rtl] .done .stamp { font-size: .9rem; }

    /* ── 2. MIRROR ── only the declarations that name a physical side. */
    [dir=rtl] .eyebrow::before { margin-right: 0; margin-left: .6em; }
    @media (hover: hover) and (pointer: fine) { [dir=rtl] .btn:hover svg { transform: translateX(-3px); } }
    [dir=rtl] .chip-cta { padding: 0 14px 0 18px; }
    [dir=rtl] .namebar input { padding: 0 18px 0 8px; }
    [dir=rtl] .giant { left: -40vw; right: -6%; }
    [dir=rtl] .hero-stage .laptop, [dir=rtl] .ig-media .laptop, [dir=rtl] .order-prev .laptop { left: auto; right: 0; }
    [dir=rtl] .hero-stage .phone, [dir=rtl] .ig-media .phone, [dir=rtl] .order-prev .phone { right: auto; left: 1%; }
    /* an over-wide block in RTL ignores its LEFT margin, so the base's -8% moves sides */
    [dir=rtl] .base { margin-left: 0; margin-right: -8%; }
    [dir=rtl] .floor { left: 6%; right: 4%; }
    [dir=rtl] .tag { left: auto; right: 2%; }
    [dir=rtl] .order-prev .tag { left: auto; right: 0; }
    /* the caption leaves room for the pause button, which RTL puts on the left */
    [dir=rtl] .w-cap { left: 46px; right: 0; }
    [dir=rtl] .tl-cap { left: auto; right: 8px; }

    [dir=rtl] .ig-top span { margin-left: 0; margin-right: auto; }
    [dir=rtl] .mini span { text-align: left; }
    /* +968 and the number read left to right, so the whole field does */
    [dir=rtl] .tel { direction: ltr; }
    /* dir=auto follows what the visitor types (an @handle reads left to
       right), but an empty field fell back to LTR and laid the Arabic
       placeholder out backwards */
    [dir=rtl] input[dir=auto]:placeholder-shown { direction: rtl; }
    [dir=rtl] .hp { left: auto; right: -9999px; }
    [dir=rtl] .done { text-align: right; }
    [dir=rtl] .done .stamp { padding: 9px 12px 9px 16px; }
    @media (max-width: 420px) {
      [dir=rtl] .mini span { text-align: right; }
    }
"""


def fail(msg):
    sys.exit("build_free_demo_ar: " + msg)


def build():
    out = SRC.read_text(encoding="utf-8")
    for sec, en, ar, n, prov in SWAPS:
        got = out.count(en)
        if got != n:
            fail("[%s] expected %d of %r in the English page, found %d. Was the English page reworded?"
                 % (sec, n, en[:90], got))
        out = out.replace(en, ar)
    if out.count("  </style>") < 1:
        fail("no closing style tag to append the Arabic layer before")
    out = out.replace("  </style>", RTL_CSS + "  </style>", 1)
    out = out.replace("<head>\n", "<head>\n  <!-- GENERATED from public_html/en/free-demo.html by "
                      "tools/free-demo/build_free_demo_ar.py. Edit the English page or the builder, never this file. -->\n", 1)
    return out


def review_rows():
    return [(s, en, ar, p) for s, en, ar, n, p in SWAPS if p not in ("markup",) and not p.startswith("reviewed")]


ARABIC_RUN = re.compile(r'[^<>"]*[؀-ۿ][^<>"]*')


def arabic_runs(s):
    """The Arabic-bearing pieces of a fragment, cut at tags and quotes, so an
    attribute, a JS line and a text node all reduce to the words themselves."""
    return [r for r in (x.strip() for x in ARABIC_RUN.findall(s)) if r]


def plain(s):
    """What the reviewer reads: tags dropped, entities and isolates resolved."""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r'\\u2068|\\u2069|‎|‌', "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def write_review(page):
    rows = review_rows()
    missing = [r for r in rows if any(run not in page for run in arabic_runs(r[2]))]
    trs = []
    for i, (sec, en, ar, prov) in enumerate(rows, 1):
        shown = " · ".join(plain(r) for r in arabic_runs(ar))
        trs.append("<tr><td class=n>%d</td><td class=s>%s</td><td class=en>%s</td><td class=ar dir=rtl lang=ar>%s</td><td class=p>%s</td></tr>"
                   % (i, html.escape(sec), html.escape(plain(en)), html.escape(shown), html.escape(prov)))
    REVIEW.parent.mkdir(exist_ok=True)
    REVIEW.write_text("""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>Free demo (Arabic): lines to review</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Sans+Arabic:wght@400;600&display=swap">
<style>
body{margin:0;padding:32px 16px;background:#F1EFE8;color:#232B26;font:15px/1.6 'IBM Plex Sans',sans-serif}
h1{font-weight:600;font-size:1.3rem;margin:0 0 6px}p{margin:0 0 20px;color:#5A665D;max-width:80ch}
table{border-collapse:collapse;width:100%%;background:#FAF8F2}td{border-top:1px solid #DED8C8;padding:10px;vertical-align:top}
.n{color:#8F5A11;font-variant-numeric:tabular-nums}.s{color:#5A665D;white-space:nowrap;font-family:'IBM Plex Sans Arabic'}
.ar{font:17px/1.9 'IBM Plex Sans Arabic',sans-serif;color:#072B22}.p{color:#5A665D;font-size:13px}
</style></head><body>
<h1>/free-demo-ar/ · %d Arabic lines not yet read by a native speaker</h1>
<p>Generated by tools/free-demo/build_free_demo_ar.py. Mark each line OK or write the correction next to it, and send it back.
The rest of the page is Arabic the reviewer already passed on the live site.</p>
<table>%s</table></body></html>
""" % (len(rows), "\n".join(trs)), encoding="utf-8")
    return rows, missing


def main():
    page = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != page:
            sys.exit("free-demo-ar.html is stale: run python3 tools/free-demo/build_free_demo_ar.py")
        print("free-demo-ar.html is up to date")
        return
    left = re.findall(r'>([^<>{}\n]*\b(?:the|your|you|demo|free)\b[^<>{}\n]*)<', page.split("<body>", 1)[1].split("<template", 1)[0], re.I)
    OUT.write_text(page, encoding="utf-8")
    rows, missing = write_review(page)
    print("wrote %s (%d bytes)" % (OUT.relative_to(ROOT), len(page.encode())))
    print("wrote %s: %d lines for the native reviewer" % (REVIEW.relative_to(ROOT), len(rows)))
    for r in missing:
        print("  warning: review row not found on the page: %s" % plain(r[2])[:60])
    for t in left:
        if t.strip():
            print("  English still visible? %r" % t.strip()[:80])


if __name__ == "__main__":
    main()
