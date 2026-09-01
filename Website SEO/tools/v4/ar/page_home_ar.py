#!/usr/bin/env python3
"""الرئيسية - the Arabic home page.

The English home page is aimed at a state of mind, not at a feature list: a
profitable owner who privately thinks "I know what I'm doing and I'm making
money, but what is this AI everyone talks about? Do I have to learn it?" The
Arabic page answers the same five questions in the same order, with the same
components - the buzzword cloud, the reply race, the four sliders, the
WhatsApp morning brief, the ladder, the demos, the 168 hours, the promise.

Three things are authored here rather than translated in place:

  * The hero. hero.py holds the English copy inline, so the Arabic beats are
    written out below. The scrub mechanism, the frame sequence and every id the
    scroll script reads are identical - only the words differ.

  * Three SVG diagrams. The staircase, the cost-growth chart and the leak bars
    all encode a reading direction, so their coordinates are mirrored. The
    text groups are pinned to direction:ltr with an explicit text-anchor, which
    is the only combination that anchors predictably; each Arabic label is
    still one RTL run inside it and reads correctly.

  * The buzzword cloud keeps its Latin words on purpose. The section's point is
    that this is jargon the owner keeps hearing and does not want to learn -
    and he hears it in English. Translating it would soften the very thing the
    section is about. The screen-reader summary under it is Arabic.
"""
import json as _json
import re
from kit import STAR, WA_ICON, url
from page_home import CSS, _buzz, _hours_grid  # noqa: F401 - design is shared

from ar_common import (AUTO, DASH, FOUNDER, PROMISE, ROLE, SITE, TEST, num, wa)

__all__ = ["CSS", "body", "META"]

SVC = url("services", "ar")
PROCESS = url("process", "ar")
ABOUT = url("about", "ar")
CONTACT = url("contact", "ar")
DEMOS = url("demos", "ar")

# The two proof tiles in S7 show screenshots of the stand-alone demo builds,
# not of the /demos-ar/ tab panel. Both Arabic pages were deleted in the
# 2026-08-27 v3 sweep and 301'd to /demos-ar/, which left each tile
# advertising one build and opening another. Restored 2026-08-30 at their
# original URLs. They are RTL pages in their own right, so the Arabic tiles
# get the Arabic demos - not the English ones.
#
# The prose links elsewhere still point at {DEMOS}: that is the indexed hub,
# and these two are noindex.
DASH_DEMO = "/customized-ceo-dashboard-demo-ar/"
WA_DEMO   = "/whatsapp-receptionist-demo-ar/"
BLOG = "/blog-ar/"

# --------------------------------------------------------------------------
# S2 - the five questions he does not ask out loud, in his own words.
# --------------------------------------------------------------------------
QUESTIONS = [
    ("٠١", "هل هذا حقيقي أم مجرد ضجّة؟",
     "بالنسبة لشركة تجارية، هو شيء واحد: آلة تردّ على المشترين بالعربية والإنجليزية في الثانية "
     "فجراً. <b>هذا الجزء يعمل اليوم.</b>"),
    ("٠٢", "هل سيمسّ عملي فعلاً؟",
     "فقط عبر المورّد الذي ردّ على مشتريك <b>بينما كنت أنت على العشاء</b>. ولا شيء آخر عن الذكاء "
     "الاصطناعي يعنيك هذه السنة."),
    ("٠٣", "هل يجب أن أتعلّمه؟",
     "لا. لن تفتحه، ولن تسجّل دخولاً، ولن تكتب أمراً واحداً. "
     "<b>يرفع لك تقريره على واتساب في جملة واحدة.</b>"),
    ("٠٤", "هل سيقلب طريقة عملي الحالية؟",
     "لا شيء في يومك يتغيّر. يُبنى <b>بجانب</b> عملك لا فوقه &mdash; الهاتف والأسعار والناس "
     "يبقون كما هم تماماً."),
    ("٠٥", "هل يمكن أن يجعلني أنفق أقل فعلاً؟",
     "يُدفَع <b>مرة واحدة</b>، لا كل شهر. ولا يأخذ تأشيرة ولا إجازة ولا أيام مرضية، ويكلّفك الشيء "
     "نفسه سواء راسلك مشترٍ واحد الليلة أو أربعون."),
]

# S3 - the reply race. Bar length is RANKED, not linear: 40 seconds against
# 14 hours on a true scale is a bar you cannot see. The note says so.
RACE = [
    ("أنت، الليلة", f"{num('14')} س {num('25')} د", 100, "bad",
     f"قرأ سعرك في {num('8:12')} صباحاً. وكان قد اشترى في {num('10:03')} مساءً.", ""),
    ("المورّد الثاني", f"{num('2')} س {num('04')} د", 31, "mid",
     "متأخر هو الآخر. ولم يصله ردّ أصلاً.", ""),
    ("المورّد الذي فاز", f"{num('4')} دقائق", 9, "good",
     "ليس أرخص. وليس أفضل. كان مستيقظاً.", "حصل على الطلب"),
    ("أنت، مع النظام", f"{num('40')} ثانية", 3.5, "best",
     "يُرسَل عرض السعر. ويصل الطلب إلى هاتفك.", "ردّ أولاً"),
]

FACTS = [
    "لا شيء جديد تتعلّمه", "تبقى على واتساب", "دفعة واحدة", "بلا التزام شهري",
    "عربي &#43; إنجليزي", "يعمل خلال أسبوع", "مبني في مسقط", "تملك ما أبنيه",
]


def _facts():
    half = "".join(f'<span><span class="star">{STAR}</span>{f}</span>' for f in FACTS)
    return f"""<div class="facts" aria-label="حقائق أساسية">
  <div class="track">
    <div class="half">{half}</div>
    <div class="half" aria-hidden="true">{half}</div>
  </div>
</div>"""


PAGE_URL = 'https://aiprofitlab.io/ar/'
LANG = 'ar'
def _faq_schema():
    """FAQPage built from the five questions the page already shows.

    The block was on the page as visible copy and nowhere in the markup, so
    the one section written to be quoted was the one an answer engine could
    not read as an answer. Built from QUESTIONS so the two cannot drift.
    """
    import html as _h
    strip = lambda t: _h.unescape(re.sub(r"<[^>]+>", "", t)).strip()
    rows = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (_json.dumps(strip(q), ensure_ascii=False), _json.dumps(strip(a), ensure_ascii=False))
        for _, q, a in QUESTIONS)
    return ('{"@type":"FAQPage","@id":"%s#faq","inLanguage":"%s",'
            '"isPartOf":{"@id":"https://aiprofitlab.io/#website"},'
            '"mainEntity":[%s]}' % (PAGE_URL, LANG, rows))


def _questions():
    rows = []
    for n, q, a in QUESTIONS:
        rows.append(f"""      <div class="qa-row rv">
        <div class="qa-q"><span class="qa-n">{n}</span><p>&laquo;{q}&raquo;</p></div>
        <p class="qa-a">{a}</p>
      </div>""")
    return "\n".join(rows)


def _race():
    lanes = []
    for who, when, width, tone, note, flag in RACE:
        chip = f'<span class="lane-flag">{flag}</span>' if flag else ""
        lanes.append(f"""      <div class="lane {tone}">
        <div class="lane-head">
          <span class="lane-who">{who}{chip}</span>
          <span class="lane-when">{when}</span>
        </div>
        <div class="lane-track"><i style="--w:{width}%"></i></div>
        <p class="lane-note">{note}</p>
      </div>""")
    return "\n".join(lanes)


HERO_HTML_AR = f"""<section class="cine" id="cine">
  <div class="cine-stage" id="cineStage">
    <div class="cine-media" id="cineMedia">
      <picture>
        <!-- Portrait poster below 1100px - see the note in hero.py. -->
        <source id="cinePosterPortrait" media="(max-width:767px)"
          srcset="/assets/cinematic/poster-portrait.webp?v=20260825" width="1080" height="1920">
        <img class="cine-poster" id="cinePoster" src="/assets/cinematic/poster.webp?v=20260825"
          alt="رسم توضيحي للمساعد الذكي: هيئة آلة تتحوّل إلى شخص ويبدأ العمل."
          width="1440" height="810" fetchpriority="high" decoding="async">
      </picture>
      <canvas class="cine-canvas" id="cineCanvas" aria-hidden="true"></canvas>
      <div class="wash-l"></div><div class="wash-r"></div>
    </div>

    <div class="cine-ui">
      <div class="lead on" id="lead">
        <h1>لست مضطراً لتعلّم الذكاء الاصطناعي.</h1>
        <p class="sub">أنت مضطر فقط للتوقف عن خسارة المشترين لصالح من يردّ قبلك.</p>
        <div class="lead-cta">
          <a class="btn btn-teal" href="#noise">أرِني، في دقيقة واحدة &darr;</a>
        </div>
      </div>

      <p class="beat" data-at="0.16"><span>{num('9:47')} مساءً. مشترٍ يسأل إن كنت توصّل إلى صحار.</span></p>
      <p class="beat" data-at="0.28"><span>مكتبك أغلق قبل أربع ساعات.</span></p>
      <p class="beat" data-at="0.40"><span>شيء ما يردّ عليه. بالعربية.</span></p>
      <p class="beat" data-at="0.52"><span>يعرف مخزونك. ويعرف أيام التوصيل لديك.</span></p>
      <p class="beat" data-at="0.64"><span>يُسعِّر. ويحجز الموعد. ويسجّل الطلب.</span></p>
      <p class="beat" data-at="0.76"><span>تقرأ عن ذلك مع قهوتك. ولم تتعلّم شيئاً جديداً.</span></p>

      <div class="endcard" id="endcard">
        <p>كل نجاح يبدأ برؤية.</p>
        <a class="btn btn-wa" href="{wa('مرحباً ناهد، أريد السؤال عن موقع ذكي لنشاطي.')}">{WA_ICON}راسلني على واتساب</a>
      </div>

    </div>

    <div class="cine-progress"><i id="cineBar"></i></div>
  </div>
</section>
"""


def _stair_svg():
    """The three systems as a staircase, mirrored: it climbs right-to-left, so
    the first step is where an Arabic reader starts."""
    return f"""<svg class="stair rv" viewBox="0 0 1000 400" role="img" aria-labelledby="stairT stairD">
      <title id="stairT">الأنظمة الثلاثة على هيئة درج</title>
      <desc id="stairD">الدرجة الأولى، {SITE}، تجعل المشترين يصلون. وهذا يخلق
        السؤال التالي الذي تجيب عنه الدرجة الثانية، {DASH}. وهذا يخلق السؤال التالي
        الذي تجيب عنه الدرجة الثالثة، {AUTO}.</desc>

      <g style="direction:ltr;text-anchor:end">
        <g class="step" style="--d:0s">
          <rect x="690" y="270" width="280" height="90" rx="12" fill="#0F6E56"/>
          <text x="946" y="310" fill="#F1EFE8" font-family="Markazi Text, serif" font-size="30">{SITE}</text>
          <text x="946" y="340" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">٠١</text>
        </g>

        <g class="anno" style="--d:.55s">
          <path d="M648 146 l12 -7 v14 z" fill="#BA7517"/>
          <text x="626" y="151" fill="#8F5A11" font-family="IBM Plex Mono, monospace" font-size="16">يبدأ المشترون بالوصول</text>
          <text x="648" y="177" fill="#232B26" font-family="IBM Plex Sans Arabic, sans-serif" font-size="18">&laquo;ما وضع سيولتي ومخزوني؟&raquo;</text>
        </g>

        <g class="step" style="--d:.18s">
          <rect x="370" y="190" width="280" height="170" rx="12" fill="#0A3D30"/>
          <text x="626" y="230" fill="#F1EFE8" font-family="Markazi Text, serif" font-size="30">لوحة متابعة</text>
          <text x="626" y="262" fill="#F1EFE8" font-family="Markazi Text, serif" font-size="30">المالك الحيّة</text>
          <text x="626" y="290" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">٠٢</text>
        </g>

        <g class="anno" style="--d:.75s">
          <path d="M328 66 l12 -7 v14 z" fill="#BA7517"/>
          <text x="306" y="71" fill="#8F5A11" font-family="IBM Plex Mono, monospace" font-size="16">تتكدّس عروض الأسعار</text>
          <text x="328" y="97" fill="#232B26" font-family="IBM Plex Sans Arabic, sans-serif" font-size="18">&laquo;من يطارد الفاتورة؟&raquo;</text>
        </g>

        <g class="step" style="--d:.36s">
          <rect x="30" y="110" width="300" height="250" rx="12" fill="#072B22"/>
          <text x="306" y="150" fill="#F1EFE8" font-family="Markazi Text, serif" font-size="30">{AUTO}</text>
          <text x="306" y="180" fill="#BFE3D5" font-family="IBM Plex Mono, monospace" font-size="17">٠٣</text>
        </g>
      </g>

      <line x1="30" y1="372" x2="970" y2="372" stroke="#DED8C8" stroke-width="2"/>
    </svg>"""


def _growth_svg():
    """Monthly cost against buyer volume, mirrored: the axis is on the right
    and both lines run right-to-left."""
    return """<svg class="drawn" viewBox="0 0 640 284" role="img" aria-labelledby="grT grD">
        <title id="grT">التكلفة الشهرية كلما زاد عدد المشترين</title>
        <desc id="grD">تكلفة الموظفين ترتفع على شكل درجات: كل زيادة في حجم الاستفسارات تحتاج في
          النهاية راتباً إضافياً. أما خط النظام فمستقيم — يُدفَع مرة واحدة ولا يرتفع مع عدد المشترين.</desc>
        <line x1="28" y1="246" x2="592" y2="246" stroke="#DED8C8" stroke-width="2"/>
        <line x1="592" y1="22" x2="592" y2="246" stroke="#DED8C8" stroke-width="2"/>
        <polyline points="592,180 450,180 450,140 308,140 308,98 166,98 166,50 28,50"
          fill="none" stroke="#A6431F" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>
        <polyline points="592,224 28,224" fill="none" stroke="#1FAF5E" stroke-width="3" stroke-linecap="round"/>
        <g style="direction:ltr;text-anchor:end">
          <text x="582" y="168" fill="#A6431F" font-family="IBM Plex Sans Arabic, sans-serif" font-size="15">موظفون أكثر</text>
          <text x="582" y="212" fill="#178A4B" font-family="IBM Plex Sans Arabic, sans-serif" font-size="15">النظام</text>
          <text x="592" y="272" fill="#5A665D" font-family="IBM Plex Sans Arabic, sans-serif" font-size="13">&#8592; المشترون شهرياً</text>
          <text x="620" y="134" fill="#5A665D" font-family="IBM Plex Sans Arabic, sans-serif" font-size="13"
            text-anchor="middle" transform="rotate(90 620 134)">التكلفة الشهرية</text>
        </g>
      </svg>"""


def body():
    # Sun-Thu (cols 0-4), 08:00-15:59 -> exactly 40 of 168 hours, which is the
    # figure in brand/docs/03-money-model.md section 5.
    office = _hours_grid(lambda d, h: d <= 4 and 8 <= h <= 15)
    always = _hours_grid(lambda d, h: True)

    p1 = f"""<main id="main">

{HERO_HTML_AR}

{_facts()}

<!-- ================================= S2 - THE NOISE, THEN THE REAL QUESTIONS -->
<section class="s-dark" id="noise">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ابدأ من هنا</p>
    <h2 class="h2">الجميع يتحدث عن الذكاء الاصطناعي. ولا شيء من ذلك تقريباً هو شغلك.</h2>

    <div class="buzz rv" aria-hidden="true">
{_buzz()}
      <div class="buzz-card">
        <p class="k">شغلك سؤال واحد</p>
        <p class="q">هل حصل ذلك المشتري على ردّ، <em>أم ذهب إلى مكان آخر؟</em></p>
      </div>
    </div>
    <p class="sr-only">سحابة من مصطلحات الذكاء الاصطناعي &mdash; نماذج لغوية، واسترجاع معزّز، وضبط
      دقيق، ووكلاء، وتضمينات، واستدلال وغيرها &mdash; وفوقها جملة واحدة: شغلك سؤال واحد. هل حصل ذلك
      المشتري على ردّ، أم ذهب إلى مكان آخر؟</p>

    <div class="asterism" style="margin-top:clamp(38px,5vw,64px)" aria-hidden="true">{STAR}</div>

    <p class="eyebrow"><span class="star">{STAR}</span> الأسئلة الخمسة التي لا تقولها بصوت عالٍ</p>
    <div class="qa">
{_questions()}
    </div>
  </div>
</section>

<!-- ======================================================= S3 - THE REPLY RACE -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ما الذي تغيّر فعلاً</p>
    <h2 class="h2">مشتريك لم يعد ينتظر. هذا كل التغيير.</h2>
    <p class="lede">مساء واحد. مشترٍ واحد. السؤال نفسه أُرسل إلى ثلاثة مورّدين في {num('9:47')} مساءً.</p>

    <div class="race rv" data-stagger>
{_race()}
    </div>

    <div class="race-foot">
      <p class="race-kick">ثلاثة مورّدين وصلتهم الرسالة. واحد حصل على الطلب.</p>
      <p class="race-note">مساء من النوع الذي مررت به، لا إحصائية.
        وطول الأشرطة ترتيبي لا نسبي.</p>
    </div>
  </div>
</section>

<!-- ========================================== S4 - YOUR OWN NUMBER, NOT MINE -->
<section class="s-dark" id="leak">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> أرقامك أنت</p>
    <h2 class="h2">أربعة مؤشرات. بلا افتراضات. ورقمك أنت.</h2>
    <p class="lede">ليست لديّ أي أرقام عن عملك، فكل رقم في الأسفل أنت من يضبطه.</p>

    <div class="leak-grid" style="margin-top:clamp(30px,4vw,52px)">
      <div class="panelcard rv">
        <h3>عملك، في أربعة أرقام</h3>

        <div class="fieldrow">
          <label for="q1">استفسارات المشترين التي تصلك أسبوعياً <output id="o1" dir="ltr">25</output></label>
          <input type="range" id="q1" min="5" max="150" step="5" value="25">
        </div>
        <div class="fieldrow">
          <label for="q2">نسبة ما يصل خارج ساعات العمل <output id="o2" dir="ltr">40%</output></label>
          <input type="range" id="q2" min="5" max="80" step="5" value="40">
        </div>
        <div class="fieldrow">
          <label for="q3">متوسط قيمة الطلب لديك <output id="o3" dir="ltr">180 ر.ع.</output></label>
          <input type="range" id="q3" min="20" max="2000" step="20" value="180">
        </div>
        <div class="fieldrow" style="margin-bottom:0">
          <label for="q4">نسبة الاستفسارات التي تكسبها بعد الردّ <output id="o4" dir="ltr">20%</output></label>
          <input type="range" id="q4" min="5" max="60" step="5" value="20">
        </div>
      </div>

      <div class="panelcard result rv" style="--d:.12s">
        <span class="bignum-cap">إيراد يمشي بعيداً، شهرياً</span>
        <span class="bignum" id="leakNum" dir="ltr">1,559 ر.ع.</span>

        <p class="assume">استفسارات ما بعد الدوام شهرياً &times; نسبة كسبك &times; متوسط طلبك.
          يُظهر ما هو <em>على المحكّ</em> في تلك الرسائل &mdash; لا وعداً باستعادته.</p>
      </div>
    </div>
  </div>
</section>

<!-- ============================== S5 - THE PART HE IS ACTUALLY AFRAID OF -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> الجزء الذي يقلقك</p>
    <h2 class="h2">لا يوجد هنا شيء عليك أن تتعلّمه.</h2>
    <p class="lede">لا تطبيق تُثبّته. ولا شاشة تتفقّدها. رسالة واحدة تصلك كل صباح،
      في المكان الذي تنظر إليه أولاً أصلاً.</p>

    <div class="touch-grid" style="margin-top:clamp(30px,4vw,52px)">
      <div class="rv">
        <div class="phone">
          <div class="phone-in">
            <div class="phone-bar">
              <span class="phone-av" aria-hidden="true">AI</span>
              <span class="phone-nm">AI Profit Lab<span>متصل</span></span>
            </div>
            <div class="phone-body">
              <div class="bub">
                <p><b>صباح الخير.</b> خلال الليل، بينما كنت نائماً:</p>
                <ul>
                  <li>{num('6')} مشترين سألوا عن المخزون والتوصيل</li>
                  <li>{num('4')} حصلوا على الأسعار والمواعيد &mdash; أُغلقت</li>
                  <li class="act"><span class="act-l">تحتاج إليك:</span> {num('200')} كرتون إلى صحار</li>
                  <li class="act"><span class="act-l">تحتاج إليك:</span> طلب ائتمان {num('60')} يوماً</li>
                </ul>
                <p style="margin:0">الرقمان محفوظان في هاتفك.</p>
                <span class="tme">{num('07:02')} &#10003;&#10003;</span>
              </div>
            </div>
          </div>
        </div>
        <p class="phone-cap">مثال على الرسالة اليومية</p>
      </div>

      <ul class="zeros rv" style="--d:.12s">
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">تطبيقات تُثبّتها
            <small>هاتفك يبقى كما هو تماماً اليوم.</small></p>
        </li>
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">كلمات مرور تحفظها
            <small>لا يوجد لك تسجيل دخول أصلاً، فلا يوجد ما تنساه.</small></p>
        </li>
        <li>
          <span class="z" aria-hidden="true">0</span>
          <p class="zt">شاشات عليك تفقّدها
            <small>هو من يكتب إليك. ولن تذهب أنت للبحث عنه.</small></p>
        </li>
      </ul>
    </div>

    <p class="touch-kick">إن كنت تقرأ رسالة واتساب، <em>فأنت تستطيع تشغيل هذا.</em></p>
  </div>
</section>
"""

    p2 = f"""
<section class="s-cream grain" id="build">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ما الذي يُبنى</p>
    <h2 class="h2">ثلاثة أنظمة. ابدأ بالذي يؤلمك.</h2>
    <p class="credo rv">نحن لا نبني مواقع إلكترونية فحسب &mdash; <b>بل أنظمة رقمية ذكية
      <i>تفكّر</i>، و<i>تتكيّف</i>، و<i>تحوّل</i> الزائر إلى عميل.</b></p>
    <p class="lede">لا شيء منها باقة مفروضة تشتريها دفعة واحدة. ولا شيء منها يحتاج رسماً شهرياً كي يستمر.</p>

    {_stair_svg()}

    <div class="grid g3" data-stagger>
      <article class="card sys-card">
        <span class="n">٠١</span>
        <h3>{SITE}</h3>
        <p>يردّ على المشترين بالعربية والإنجليزية، ويسجّل من هم، ويحوّل الأحياء منهم إلى واتساب الخاص بك.</p>
        <span class="tag">دفعة واحدة</span>
        <a class="tlink" href="{SVC}#smart-website">شاهد ما بداخله <span class="arw">&larr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">٠٢</span>
        <h3>{DASH}</h3>
        <p>السيولة والمخزون والطلبات المفتوحة على شاشة واحدة &mdash; دون الاتصال بثلاثة أشخاص لتجميعها.</p>
        <span class="tag">إضافة</span>
        <a class="tlink" href="{DEMOS}#dash">افتح التجربة الحيّة <span class="arw">&larr;</span></a>
      </article>
      <article class="card sys-card">
        <span class="n">٠٣</span>
        <h3>{AUTO}</h3>
        <p>لا بدّ لشيء أن يطارد عروض الأسعار والفواتير. هذا يفعلها، وفق جدول، دون أن يُذكَّر.</p>
        <span class="tag">إضافة</span>
        <a class="tlink" href="{SVC}#autopilot">شاهد ما بداخله <span class="arw">&larr;</span></a>
      </article>
    </div>
  </div>
</section>

<!-- ================================================= S7 - PROOF YOU CAN CLICK -->
<section class="s-dark" id="proof">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> دليل، لا شهادات</p>
    <h2 class="h2">لا تصدّق كلامي. افتح الآلات بنفسك.</h2>
    <p class="lede">أنظمة حقيقية تعمل على بيانات تجريبية. والنقر على واحدة منها اختبار أفضل من عبارة
      مدح من شخص لم تقابله قط.</p>

    <div class="tiles" style="margin-top:clamp(28px,4vw,48px)" data-stagger>
      <a class="tile" href="{DASH_DEMO}">
        <span class="live"><i></i>تجربة حيّة</span>
        <span class="shot"><img src="/assets/v4/demo-dashboard-960.webp" alt="تجربة لوحة متابعة المدير: بطاقات الإيراد والربح الإجمالي والهامش فوق قائمة إجراءات مرتّبة." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>عملك على شاشة واحدة</h3>
          <p>السيولة والهامش والبضاعة الراكدة وما تفعله حيالها &mdash; مرتّبة، وبجمل واضحة.</p>
          <span class="tlink">افتحها <span class="arw">&larr;</span></span>
        </span>
      </a>

      <a class="tile" href="{WA_DEMO}">
        <span class="live"><i></i>تجربة حيّة</span>
        <span class="shot"><img src="/assets/v4/demo-whatsapp-960.webp" alt="تجربة موظف استقبال واتساب: قائمة الطلبات بجانب محادثة كاملة مع مشترٍ يديرها الوكيل الذكي." width="960" height="600" loading="lazy" decoding="async"></span>
        <span class="cap">
          <h3>وكيل المشتري، في وسط المحادثة</h3>
          <p>شاهده يؤهّل مشترياً، ويمسك بخيط الحديث، ويحجز الموعد.</p>
          <span class="tlink">افتحها <span class="arw">&larr;</span></span>
        </span>
      </a>

      <a class="tile tile-wide" href="{CONTACT}#test">
        <span class="cap">
          <h3>أو وجّهه إلى عملك أنت: {TEST}</h3>
          <p>أراسل نشاطك تماماً كما يفعل مشترٍ، ثم أرسل لك التقرير &mdash; كم استغرقت، وما الذي فاتك،
            وكم كلّفك ذلك. مجاناً، ولا تدين لي بشيء بعدها.</p>
        </span>
        <span class="chip">مجاناً &#183; <b>{num('5')} أسبوعياً</b></span>
      </a>
    </div>
  </div>
</section>

<!-- ================================== S8 - SPEND LESS, SERVE MORE -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> أنفق أقل. اخدم أكثر.</p>
    <h2 class="h2">في الأسبوع {num('168')} ساعة. والموظف الإداري يغطّي {num('40')}.</h2>
    <p class="lede">كل مربّع ساعة من أسبوعك. والحديث هنا عن التغطية لا عن الجودة &mdash;
      فالموظف الجيد يفعل أشياء لا يفعلها أي نظام.</p>

    <div class="hours-grid" style="margin-top:clamp(28px,4vw,48px)" data-stagger>
      <div class="hcard">
        <h3>توظيف موظف إداري</h3>
        <p class="sub">{num('350')}&ndash;{num('500')} ر.ع. شهرياً، كل شهر</p>
        <p class="hlegend">الصفوف: الأحد &#8592; السبت &#183; الأعمدة: {num('00:00')} &#8592; {num('23:00')}</p>
        {office}
        <span class="hcount"><span data-count="40">40</span> من {num('168')} ساعة</span>
        <p class="note">إضافةً إلى التأشيرة والتأمين والإجازات وأيام المرض &mdash; والتغطية تتوقف حين يتوقف هو.</p>
      </div>

      <div class="hcard win">
        <h3>{SITE}</h3>
        <p class="sub">تُدفع مرة واحدة، لا كل شهر</p>
        <p class="hlegend">الصفوف: الأحد &#8592; السبت &#183; الأعمدة: {num('00:00')} &#8592; {num('23:00')}</p>
        {always}
        <span class="hcount"><span data-count="168">168</span> من {num('168')} ساعة</span>
        <p class="note">هو لا يحلّ محلّه. بل يغطّي الـ{num('128')} ساعة التي لم يكن فيها أصلاً.</p>
      </div>
    </div>

    <div class="growth rv">
      {_growth_svg()}
      <div>
        <h3>عشرة مشترين دفعة واحدة يكلّفون ما يكلّفه واحد.</h3>
        <p>كل قفزة في الحجم تكلّف في النهاية راتباً إضافياً، كل شهر. أما النظام فيُدفَع مرة واحدة
          ولا يلاحظ كم شخصاً راسلك الليلة.</p>
      </div>
    </div>

    <div class="btn-row" style="margin-top:clamp(26px,3vw,40px)">
      <a class="btn btn-teal" href="{SVC}#price">اطّلع على قائمة الأسعار كاملة</a>
      <a class="tlink" href="{SVC}">كل نظام بالتفصيل <span class="arw">&larr;</span></a>
    </div>
  </div>
</section>

<!-- ================================================== S9 - THE NAMED PROMISE -->
<section class="s-teal promise">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> {PROMISE}</p>
    <div class="promise-grid" style="margin-top:14px">
      <img class="promise-photo" src="/nahid-founder-2026.webp" alt="{FOUNDER}، مؤسس AI Profit Lab" width="220" height="220" loading="lazy" decoding="async">
      <div>
        <q>لم يصلك استفسار حقيقي من مشترٍ خلال {num('30')} يوماً من الإطلاق؟ أعيد بناءه مجاناً حتى يصلك.
          وإن لم يصلك بعدها، تسترد مالك.</q>
        <p class="sig">{FOUNDER} &#183; {ROLE}، AI Profit Lab</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== S10 - EXPLORE RAIL -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> واصل</p>
    <h2 class="h2">أربعة أماكن تستحق دقائقك الخمس القادمة.</h2>

    <div class="rail" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <a class="rcard" href="{SVC}">
        <span class="rn">٠١</span>
        <span><h3>ما أبنيه</h3><p>ثلاثة أنظمة، وكل سعر، وما هو غير مشمول عن قصد.</p></span>
        <span class="go">افتح <span aria-hidden="true">&larr;</span></span>
      </a>
      <a class="rcard" href="{PROCESS}">
        <span class="rn">٠٢</span>
        <span><h3>طريقة العمل</h3><p>من أول رسالة إلى نظام يعمل، خطوة بخطوة، مع المواعيد.</p></span>
        <span class="go">افتح <span aria-hidden="true">&larr;</span></span>
      </a>
      <a class="rcard" href="{ABOUT}">
        <span class="rn">٠٣</span>
        <span><h3>من يبني هذا</h3><p>مشغّل واحد، لا وكالة. وفيها أيضاً من أعتذر عن العمل معه.</p></span>
        <span class="go">افتح <span aria-hidden="true">&larr;</span></span>
      </a>
      <a class="rcard" href="{BLOG}">
        <span class="rn">٠٤</span>
        <span><h3>المقالات</h3><p>كتابة بلغة واضحة عن الذكاء الاصطناعي للشركات التجارية في عُمان والخليج.</p></span>
        <span class="go">افتح <span aria-hidden="true">&larr;</span></span>
      </a>
    </div>
  </div>
</section>

</main>
"""
    return p1 + p2


META = dict(
    slug="index",
    title="AI Profit Lab | لست مضطراً لتعلّم الذكاء الاصطناعي — مسقط، عُمان",
    desc=("لن تفتحه، ولن تسجّل دخولاً، ولن تكتب أمراً واحداً. موقع ذكي بلغتين يردّ على مشتريك "
          "بالعربية والإنجليزية في الثانية فجراً، ويرفع لك تقريره على واتساب في جملة واحدة. "
          "دفعة واحدة، بلا التزام شهري، مبني على يد مشغّل في مسقط."),
    nav="/ar/",
    hero=True,
    calc=True,
    next=("التالي", "ما أبنيه", "/services/"),
    schema=_faq_schema(),
)
