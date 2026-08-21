#!/usr/bin/env python3
"""التجارب - the Arabic Demos page.

Same player, same dashboard, same CSS. What changes is the running order of the
conversations and the language they are in: the English page opens on an
English buyer and offers Arabic as the second tab, so this one opens on an
Arabic buyer and offers English as the second. The point of the second tab is
identical either way - the language is detected from the buyer's first message
rather than chosen from a menu.

`page_demo.JS_HEAD/JS_TAIL` are reused verbatim; only the data between them is
Arabic. The scenarios carry their own dir/lang, which is what lets the English
thread read left-to-right inside an RTL page.

⚠ The Arabic conversation copy has not been reviewed by a native speaker. That
is the standing rule in brand/docs/02-brand-book.md and it still applies here.
"""
import json

import page_demo
from kit import STAR, WA_ICON, url
from page_demo import CSS, _static_rail, _static_thread  # noqa: F401

from ar_common import num, wa

__all__ = ["CSS", "JS", "body", "META"]

SVC = url("services", "ar")
SIM = url("simulators", "ar")

# --------------------------------------------------------------------------
# Conversations. Shape, keys and ordering rules are page_demo.SCENARIOS';
# see the note there. All figures belong to a fictional distributor, stated on
# the page rather than implied.
# --------------------------------------------------------------------------
SCENARIOS = [
    {
        "id": "night",
        "tab": "الجمعة، 21:41",
        "title": "مشترٍ يسأل عن التوفّر والسعر بعد الدوام",
        "sub": "لا أحد في المكتب. الوكيل يجيب من مخزونك أنت ومن قائمة أسعارك، ثم يسلّم المحادثة "
               "لحظة أن يُظهر المشتري نيّة الشراء.",
        "dir": "rtl", "lang": "ar",
        "msgs": [
            {"who": "day", "text": "الجمعة 21:41"},
            {"who": "in", "t": "21:41",
             "text": "مساء الخير — عندكم زيت هيدروليك براميل ٢٠ لتر؟ أحتاج ٨ لموقع في صحار.",
             "rail": ["21:41", "وصلت الرسالة. المكتب أغلق قبل خمس ساعات."]},
            {"who": "out", "t": "21:41", "typing": 1400,
             "text": "نعم — ISO 68 و ISO 46، الاثنان متوفران. ثمانية براميل ٢٠ لتر يمكن خروجها من "
                     "مخزن الرسيل صباح الغد.",
             "rail": ["21:41", "اللغة: العربية. النيّة: استعلام توفّر، الكمية ٨."]},
            {"who": "out", "t": "21:41", "typing": 900,
             "text": "سعر ISO 68 هو ٢١.٤٠٠ ريال عماني للبرميل عند هذه الكمية. التسليم إلى صحار قبل الظهر.",
             "rail": ["21:41", "المخزون: ISO 68 — ٤١ برميلاً في الرسيل. طُبّقت شريحة ٨–١٤."]},
            {"who": "in", "t": "21:43", "text": "وإذا أخذت ١٥؟",
             "rail": ["21:43", "تغيّرت الكمية. ولم يُوقَظ أي موظف حتى الآن."]},
            {"who": "out", "t": "21:43", "typing": 1200,
             "text": "١٥ برميلاً تنزل بالسعر إلى ٢٠.١٠٠ للبرميل. أستطيع حجز الكمية على رقمك الآن — أحجزها؟",
             "rail": ["21:43", "طُبّقت شريحة ١٥ فأكثر. حُجز المخزون ولم يُبَع."]},
            {"who": "in", "t": "21:44", "text": "نعم من فضلك. وأحتاج فاتورة باسم الشركة.",
             "rail": ["21:44", "إشارة شراء: طلب فاتورة."]},
            {"who": "out", "t": "21:44", "typing": 1000,
             "text": "تم الحجز: ١٥ × ISO 68 على هذا الرقم. المحادثة الآن عند ناهد وسيؤكّد معك بيانات "
                     "الفاتورة — كل ما سبق أمامه، فلن تُضطر لإعادة شيء.",
             "rail": ["21:44", "سُلّمت إلى إنسان ومعها المحادثة كاملة."]},
            {"who": "sys", "text": "ثلاث دقائق. ولم يكن أحد مستيقظاً.",
             "rail": ["21:44", "إجمالي الوقت من أول رسالة: ٣ دقائق."]},
        ],
    },
    {
        "id": "english",
        "tab": "English",
        "title": "الوكيل نفسه، يردّ بالإنجليزية",
        "sub": "اللغة تُكتشف من أول رسالة للمشتري، لا تُختار من قائمة. من يكتب بالإنجليزية يُجاب "
               "بالإنجليزية، بالمخزون نفسه وبالأسعار نفسها.",
        "dir": "ltr", "lang": "en",
        "msgs": [
            {"who": "day", "text": "Saturday 20:12"},
            {"who": "in", "t": "20:12", "text": "Evening — do you have an oil filter for a 2019 Toyota Hilux?",
             "rail": ["20:12", "اللغة المكتشفة: الإنجليزية. الردود تتحوّل تلقائياً."]},
            {"who": "out", "t": "20:12", "typing": 1300,
             "text": "Good evening. Yes — 18 in stock at the Rusayl warehouse.",
             "rail": ["20:12", "طُوبق الصنف على كتالوجك أنت، لا على تخمين."]},
            {"who": "out", "t": "20:12", "typing": 800,
             "text": "OMR 4.500 each, dropping to OMR 4.100 from ten pieces up.",
             "rail": ["20:12", "شريحة الكمية الخاصة بك، مقروءة من قائمة الأسعار."]},
            {"who": "in", "t": "20:14", "text": "I need 20. When can you deliver?",
             "rail": ["20:14", "النيّة: طلب، الكمية ٢٠."]},
            {"who": "out", "t": "20:14", "typing": 1200,
             "text": "Tomorrow in Muscat. I will hold the 20 against your number now, and Nahid will "
                     "confirm the order with you directly.",
             "rail": ["20:14", "حُجز المخزون. وسُلّمت المحادثة إلى إنسان."]},
            {"who": "sys", "text": "Two minutes, in the buyer's own language.",
             "rail": ["20:14", "لم يكن مطلوباً وجود موظف يتحدث الإنجليزية في الثامنة مساء السبت."]},
        ],
    },
    {
        "id": "followup",
        "tab": "المشتري الصامت",
        "title": "عرض سعر يخرج، ثم يصمت المشتري",
        "sub": "هذا هو الطيار الآلي لا موظف الاستقبال. يتابع عرض السعر وفق جدول تضبطه أنت، ويوقف "
               "نفسه لحظة أن يردّ المشتري — وهذه بالضبط النقطة التي تخطئ فيها معظم أدوات المتابعة.",
        "dir": "rtl", "lang": "ar",
        "msgs": [
            {"who": "sys", "text": "أُرسل عرض السعر رقم ١١٨٤ — ٢٬٣٤٠ ريالاً عمانياً",
             "rail": ["الاثنين 11:02", "صدر عرض السعر. جدول المتابعة: اليوم ٢، واليوم ٥، واليوم ٩."]},
            {"who": "day", "text": "بعد يومين"},
            {"who": "out", "t": "11:02", "typing": 900,
             "text": "صباح الخير — أتأكد فقط أن عرض السعر رقم ١١٨٤ للبراميل الخمسة عشر قد وصلك. "
                     "ويسعدني تثبيت السعر حتى الخميس إن كان ذلك يساعدك.",
             "rail": ["الأربعاء 11:02", "المتابعة ١ من ٣. أرسلها النظام، وباسمك أنت."]},
            {"who": "day", "text": "بعد ثلاثة أيام"},
            {"who": "out", "t": "09:30", "typing": 900,
             "text": "ما زلت محتفظاً لك بالبراميل الخمسة عشر. وإن تغيّرت الكمية أستطيع إعادة التسعير "
                     "خلال دقيقة — فقط أخبرني بالرقم.",
             "rail": ["السبت 09:30", "المتابعة ٢ من ٣."]},
            {"who": "in", "t": "09:52",
             "text": "المعذرة — كنت أنتظر شريكي. أرسل الفاتورة، بالكمية نفسها.",
             "rail": ["السبت 09:52", "ردّ المشتري. أُلغيت المتابعة ٣ تلقائياً."]},
            {"who": "sys", "text": "توقفت السلسلة. ولم يُطارَد أحد مرتين.",
             "rail": ["السبت 09:52", "الطلب الذي كان سيموت بصمت صار على مكتبك بدلاً من ذلك."]},
        ],
    },
]

JS = page_demo.JS_HEAD + json.dumps(SCENARIOS, ensure_ascii=False) + page_demo.JS_TAIL


def body():
    first = SCENARIOS[0]
    sctabs = "".join(
        f'<button type="button" role="tab" data-i="{i}" '
        f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">'
        f'<em>{["٠١", "٠٢", "٠٣"][i]}</em>{s["tab"]}</button>'
        for i, s in enumerate(SCENARIOS))

    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>التجارب</p>
    <h1 class="h1">شاهده يردّ على مشترٍ</h1>
    <p class="lede">ليس فيديو ولا عرض شرائح. هذا هو منطق المحادثة نفسه والشاشة نفسها التي يحصل عليها
      المالك، تعمل هنا داخل الصفحة. الشركة خيالية وأرقامها خيالية &mdash; وكل ما عدا ذلك هو السلوك الحقيقي.</p>
  </div>
</section>

<section class="s-dark grain" id="demos">
  <div class="wrap">
    <div class="dtabs" id="dtabs" role="tablist" aria-label="اختر تجربة">
      <button type="button" role="tab" id="dtab1" aria-controls="demo1" aria-selected="true" tabindex="0"><em>٠١</em>وكيل المشتري</button>
      <button type="button" role="tab" id="dtab2" aria-controls="demo2" aria-selected="false" tabindex="-1"><em>٠٢</em>لوحة متابعة المالك</button>
    </div>

    <!-- ------------------------------------------------ demo 1: the agent -->
    <div class="stage" id="demo1" role="tabpanel" aria-labelledby="dtab1">
      <div>
        <div class="phone">
          <div class="bar">
            <span class="av" aria-hidden="true">&#10038;</span>
            <div>
              <b>الخليج للزيوت وقطع الغيار</b>
              <span><i></i>يردّ خلال ثوانٍ</span>
            </div>
          </div>
          <div class="thread" id="thread" aria-live="polite" aria-label="محادثة تجريبية">
        {_static_thread(first)}
          </div>
        </div>
        <div class="replay">
          <button type="button" id="again">أعد التشغيل</button>
          <span>شركة خيالية، وسلوك حقيقي</span>
        </div>
      </div>

      <div class="rail">
        <div class="dtabs sub" id="sctabs" role="tablist" aria-label="اختر محادثة" style="margin-bottom:26px">
          {sctabs}
        </div>
        <h3 id="scTitle">{first["title"]}</h3>
        <p class="sub" id="scSub">{first["sub"]}</p>
        <p class="lbl"><span class="star">{STAR}</span>ما الذي فعله النظام</p>
        <ul class="steps2" id="rail">
        {_static_rail(first)}
        </ul>
        <div class="btn-row" style="margin-top:30px">
          <a class="btn btn-wa" href="{wa('مرحباً ناهد، شاهدت تجربة وكيل المشتري — هل يستطيع الرد من قائمة مخزوني؟')}">{WA_ICON}<span>اسأله عن مخزوني</span></a>
          <a class="btn btn-ghost" href="{SVC}#price">كم يكلّف</a>
        </div>
      </div>
    </div>

    <!-- -------------------------------------------- demo 2: the dashboard -->
    <div class="stage" id="demo2" role="tabpanel" aria-labelledby="dtab2" hidden
         style="grid-template-columns:minmax(0,1fr)">
      <div>
        <div class="dash">
          <div class="head">
            <b>الخليج للزيوت وقطع الغيار &mdash; هذا الشهر</b>
            <span class="live"><i></i>حُدّثت قبل {num('4')} دقائق</span>
          </div>
          <div class="body">
            <div>
              <div class="kpis">
                <div class="kpi"><span>الإيراد منذ بداية الشهر</span>
                  <b><span data-count="109400" data-post=" ر.ع."></span></b><i>&uarr; {num('12')}% عن الشهر الماضي</i></div>
                <div class="kpi"><span>الربح الإجمالي</span>
                  <b><span data-count="41900" data-post=" ر.ع."></span></b><i>هامش {num('38.3')}%</i></div>
                <div class="kpi"><span>المحصّل نقداً</span>
                  <b><span data-count="72150" data-post=" ر.ع."></span></b><i class="down">{num('37,250')} ر.ع. متأخرة</i></div>
              </div>
              <div class="dchart">
                <h4>الربح الإجمالي أسبوعياً &mdash; بالريال العُماني</h4>
                <svg viewBox="0 0 560 170" style="width:100%;height:auto;display:block;direction:ltr" role="img"
                     aria-label="الربح الإجمالي أسبوعياً: 8,200 ثم 9,400 ثم 7,100 ثم 11,300 ثم 9,900 ثم 12,400 ثم 10,800 ثم 13,200">
                  <g fill="rgba(241,239,232,.18)">
                    <rect x="4"   y="86"  width="58" height="60" rx="4"/>
                    <rect x="74"  y="70"  width="58" height="76" rx="4"/>
                    <rect x="144" y="100" width="58" height="46" rx="4"/>
                    <rect x="214" y="46"  width="58" height="100" rx="4"/>
                    <rect x="284" y="63"  width="58" height="83" rx="4"/>
                    <rect x="354" y="32"  width="58" height="114" rx="4"/>
                    <rect x="424" y="53"  width="58" height="93" rx="4"/>
                  </g>
                  <rect x="494" y="22" width="58" height="124" rx="4" fill="#D89234"/>
                  <line x1="0" y1="146" x2="560" y2="146" stroke="rgba(241,239,232,.16)" stroke-width="1"/>
                  <text x="4" y="164" fill="rgba(241,239,232,.45)" font-family="IBM Plex Mono, monospace" font-size="11">أ١</text>
                  <text x="523" y="164" fill="#D89234" font-family="IBM Plex Sans Arabic, sans-serif" font-size="11" text-anchor="middle">هذا الأسبوع</text>
                </svg>
              </div>
              <div class="dchart" style="margin-top:18px">
                <h4>أقدم الفواتير غير المسدّدة &mdash; بمن تتصل أولاً</h4>
                <table class="mini">
                  <tr><td>الباطنة للمقاولات</td><td>{num('112')} يوماً</td><td class="r">{num('14,800')} ر.ع.</td></tr>
                  <tr><td>صحار للخدمات البحرية</td><td>{num('96')} يوماً</td><td class="r">{num('9,250')} ر.ع.</td></tr>
                  <tr><td>مسقط لعناية الأساطيل</td><td>{num('61')} يوماً</td><td class="r">{num('6,400')} ر.ع.</td></tr>
                  <tr><td>ثلاث جهات أخرى دون {num('45')} يوماً</td><td>&mdash;</td><td class="r">{num('6,800')} ر.ع.</td></tr>
                </table>
              </div>
              <p class="dnote">بيانات نموذجية لموزّع خيالي. في أي بناء حقيقي تُقرأ هذه الأرقام من الأنظمة
                التي تشغّلها أصلاً &mdash; ملف المحاسبة، وكشف المخزون، ومحادثة واتساب.</p>
            </div>

            <div class="alerts">
              <h4>ما يحتاج إليك اليوم</h4>
              <div class="alert red">
                <b>السيولة &mdash; تصرّف هذا الأسبوع</b>
                <p>{num('37,250')} ر.ع. متأخرة على {num('6')} فواتير. اثنتان منها تجاوزتا {num('90')} يوماً،
                  وكلتاهما لدى العميل نفسه.</p>
                <em>مقترح: أوقف طلبات الائتمان الجديدة لذلك الحساب حتى تُسدَّد واحدة.</em>
              </div>
              <div class="alert">
                <b>المخزون &mdash; مال نائم</b>
                <p>{num('6,900')} ر.ع. راكدة في {num('4')} أصناف لم تتحرك منذ {num('90')} يوماً، وتكلّف نحو
                  {num('350')} ر.ع. شهرياً مساحة مخازن.</p>
                <em>مقترح: صفّها بسعر التكلفة. المساحة تساوي أكثر من الهامش.</em>
              </div>
              <div class="alert green">
                <b>الطلبات &mdash; رُدّ عليها دونك</b>
                <p>وصل {num('18')} استفساراً من مشترين بعد الدوام هذا الشهر. رُدّ على الثمانية عشر جميعاً؛
                  وتحوّل {num('5')} منها إلى عروض أسعار، ودفع اثنان بالفعل.</p>
                <em>لا شيء عليك فعله. هذا هو الجزء الذي كان صمتاً.</em>
              </div>
            </div>
          </div>
        </div>
        <div class="btn-row" style="margin-top:28px">
          <a class="btn btn-wa" href="{wa('مرحباً ناهد، أريد لوحة متابعة مثل التجربة — مبنية على أرقامي أنا.')}">{WA_ICON}<span>ابنِ هذه على أرقامي</span></a>
          <a class="btn btn-ghost" href="{SIM}">احسب أرقامي أولاً</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>ما لا تستطيع تجربة أن تريك إياه</p>
    <h2 class="h2">ثلاثة أمور أفضّل قولها هنا لا في مكالمة بيع</h2>
    <div class="grid g3" data-stagger style="margin-top:clamp(28px,4vw,44px)">
      <div class="card">
        <span class="n">٠١</span>
        <h3>يجيب من بياناتك أو لا يجيب</h3>
        <p>كل سعر وكل رقم مخزون في الأعلى جاء من قائمة. الوكيل لا يخترع إجابة &mdash; وحين لا يجد لها
          مصدراً يقول ذلك ويحوّل المشتري إليك.</p>
      </div>
      <div class="card">
        <span class="n">٠٢</span>
        <h3>التسليم قاعدة لا مزاج</h3>
        <p>الفاتورة، والتفاوض، والشكوى، وأي شيء غير متأكد منه &mdash; كلها تُحوَّل إلى إنسان بقاعدة
          تضبطها أنت. وهذا الحدّ هو الفرق بين نظام ومقامرة.</p>
      </div>
      <div class="card">
        <span class="n">٠٣</span>
        <h3>بيانات مشتريك تبقى تحت المساءلة</h3>
        <p>بموجب قانون حماية البيانات الشخصية العُماني، محادثة كهذه بيانات شخصية. الموافقة والغرض
          ومدة الحفظ تُصمَّم من البداية، لا تُضاف بعد أن يسأل أحد.</p>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="demos",
    title="التجارب | شاهد وكيل المشتري يردّ — AI Profit Lab",
    desc=("تجربة حيّة لوكيل المشتري على واتساب وهو يردّ بالعربية والإنجليزية بعد الدوام، ولوحة "
          "متابعة المالك. شركة خيالية، وسلوك حقيقي."),
    nav="/demos-ar/",
    next=("التالي", "تواصل معي", "/contact/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"WebPage",
  "name":"AI Profit Lab — التجارب",
  "url":"https://aiprofitlab.io/demos-ar/",
  "description":"تجارب تفاعلية لوكيل المشتري على واتساب ولوحة متابعة المالك الحيّة.",
  "inLanguage":"ar",
  "publisher":{"@type":"Organization","name":"AI Profit Lab","legalName":"Lotus Gulf International"}
}""",
)
