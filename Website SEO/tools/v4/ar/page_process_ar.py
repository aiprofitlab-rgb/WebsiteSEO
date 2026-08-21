#!/usr/bin/env python3
"""طريقة العمل - the Arabic How-it-works page.

Design and the `_step` helper are imported from page_process.py, so the five
steps, the week bar and the mock panels are the same components. Only the
strings change.

The mock panels are deliberately bilingual in one respect: the scorecard shows
a row for "answered in Arabic", which on the Arabic page becomes a row for
"answered in English". The test is the same test either way - whether a buyer
gets an answer in the language they wrote in - and stating it from the reader's
own side is what makes the row mean anything to them.
"""
from kit import STAR, WA_ICON, url
from page_process import CSS, _step  # noqa: F401 - design is shared

from ar_common import FOUNDER, PROMISE, ROLE, TEST, num, wa

__all__ = ["CSS", "body", "META"]

CONTACT = url("contact", "ar")


def body():
    scorecard = f"""<div class="mock">
  <div class="mh"><b>{TEST}</b><span>تقريرك</span></div>
  <div class="scorerow"><em>الردّ على رسالة واتساب في التاسعة مساءً</em><span class="grade bad">لا ردّ</span></div>
  <div class="scorerow"><em>الردّ على الرسالة نفسها صباح اليوم التالي</em><span class="grade mid">{num('14')} س {num('25')} د</span></div>
  <div class="scorerow"><em>الردّ بالإنجليزية</em><span class="grade bad">لا</span></div>
  <div class="scorerow"><em>عرض سعر الجملة</em><span class="grade bad">لا</span></div>
  <div class="scorerow"><em>ظهور الموقع في جوجل</em><span class="grade good">الصفحة الأولى</span></div>
  <div class="scorerow"><em>ذكر النشاط في ChatGPT</em><span class="grade bad">غير مذكور</span></div>
</div>
<p class="lede" style="font-size:.86rem;margin:14px 0 0">هذا مثال على شكل التقرير. تقريرك يُملأ بما حدث فعلاً.</p>"""

    agenda = """<div class="mock">
  <div class="mh"><b>المكالمة</b><span>ثلاثون دقيقة</span></div>
  <ul class="checks">
    <li>أين يتسرّب المال، بكلماتك أنت</li>
    <li>ما الذي يسأل عنه مشتروك فعلاً، وبأي لغة</li>
    <li>أي الأنظمة الثلاثة يعالج ذلك &mdash; وغالباً واحد فقط</li>
    <li>الرقم، والطريقة التي تفضّل أن تدفع بها</li>
    <li>ما الذي <em>لن</em> أقوم به لك</li>
  </ul>
</div>
<p class="lede" style="font-size:.86rem;margin:14px 0 0">بلا شرائح عرض، وبلا عرض تجاري تجلس له. وإن لم يكن الأمر مناسباً، أقول ذلك في المكالمة.</p>"""

    board = f"""<div class="mock">
  <div class="mh"><b>مشروعك</b><span>اليوم {num('3')} من {num('7')}</span></div>
  <div class="board">
    <div class="col done"><b>منجز</b>
      <div class="t">جمع الكتالوج وشروط البيع</div>
      <div class="t">صياغة النص بالعربية والإنجليزية</div>
      <div class="t">اعتماد الهيكل</div>
    </div>
    <div class="col"><b>قيد البناء</b>
      <div class="t">تدريب وكيل المشتري على مخزونك</div>
      <div class="t">ربط التحويل إلى واتساب</div>
      <div class="t">مسار عرض السعر</div>
    </div>
    <div class="col"><b>التالي</b>
      <div class="t">الظهور في البحث وفي إجابات الذكاء الاصطناعي</div>
      <div class="t">جولة مراجعتك</div>
      <div class="t">الإطلاق</div>
    </div>
  </div>
</div>"""

    launch = """<div class="mock">
  <div class="mh"><b>قائمة ما قبل الإطلاق</b><span>قبل أن أسلّمه لك</span></div>
  <ul class="checks">
    <li>مُختبَر من هاتف حقيقي، على شبكة حقيقية</li>
    <li>الردّ صحيح بالعربية وبالإنجليزية معاً</li>
    <li>مشترٍ تجريبي وصل إلى واتساب الخاص بك</li>
    <li>ملفّك في نشاطي التجاري على جوجل يشير إلى المكان الصحيح</li>
    <li>فريقك رأى كيف يعمل، مرة واحدة، مباشرة</li>
    <li>الاستضافة والحماية والرعاية تعمل لمدة سنة</li>
  </ul>
</div>"""

    promise = f"""<div class="mock" style="background:var(--teal-950);border-color:var(--teal-900)">
  <div class="mh" style="border-bottom-color:rgba(241,239,232,.16)">
    <b style="color:var(--cream)">{PROMISE}</b><span style="color:var(--amber-pale)">{num('30')} يوماً</span>
  </div>
  <p style="font-family:var(--display);font-size:1.35rem;line-height:1.5;color:var(--cream);margin:0 0 14px">
    لم يصلك استفسار حقيقي من مشترٍ خلال {num('30')} يوماً من الإطلاق؟ أعيد بناءه مجاناً حتى يصلك.
    وإن لم يصلك بعدها، تسترد مالك.</p>
  <p style="font-family:var(--mono);font-size:.8rem;color:var(--amber-pale);margin:0">
    {FOUNDER} &#183; {ROLE}</p>
</div>"""

    steps = "\n".join([
        _step("٠١", "اليوم صفر &#183; مجاناً", TEST,
              "أراسل نشاطك تماماً كما يفعل مشترٍ &mdash; بالعربية، وبعد ساعات العمل &mdash; وأرسل لك "
              "تقريراً بما حدث. لا تدين لي بشيء، ومعظم الناس يتوقفون هنا وقد تعلّموا شيئاً.",
              scorecard),
        _step("٠٢", "اليوم صفر &#183; ثلاثون دقيقة", "محادثة واحدة صريحة",
              "ننظر في التقرير معاً، وأخبرك أي نظام يعالج المشكلة، وكم يكلّف، وهل يستحق العمل أصلاً.",
              agenda),
        _step("٠٣", "الأيام ١&ndash;٦", "البناء",
              "أبنيه أنا. وفي اليوم الثالث يصلك رابط ترى فيه تقدّماً حقيقياً، لا رسالة حالة. "
              "جولة تعديلات واحدة متوقّعة، وغير محسوبة عليك.",
              board),
        _step("٠٤", "اليوم ٧", "الإطلاق",
              "مُختبَر من هاتف حقيقي قبل أن يراه أحد. وفريقك يتعلّم كيف يعمل، مباشرة، في جلسة واحدة.",
              launch),
        _step("٠٥", "الأيام ٧&ndash;٣٧", "وعد الثلاثين يوماً",
              "تبدأ المدة يوم الإطلاق. إن لم ينتج استفساراً حقيقياً من مشترٍ خلال ثلاثين يوماً، "
              "أعيد بناءه مجاناً &mdash; وإن فشل بعدها أيضاً، تسترد مالك.",
              promise),
    ])

    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> طريقة العمل</p>
    <h1 class="h1">من أول رسالة إلى نظام يعمل،<br>في أسبوع تقريباً.</h1>
    <p class="lede">خمس خطوات. الأولى مجانية، والثانية مجرد محادثة، ويمكنك التوقف بعد أيٍّ منهما
      دون أن تدين بشيء.</p>

    <div class="weekbar rv">
      <div class="wb"><i style="--d:0s"></i><i style="--d:.1s"></i><i style="--d:.2s"></i><i style="--d:.3s"></i><i style="--d:.4s"></i></div>
      <div class="wbl">
        <span><b>اليوم ٠</b>الاختبار والمكالمة</span>
        <span><b>اليومان ١&ndash;٢</b>النص والهيكل</span>
        <span><b>الأيام ٣&ndash;٥</b>البناء</span>
        <span><b>اليوم ٦</b>مراجعتك</span>
        <span><b>اليوم ٧</b>الإطلاق</span>
      </div>
    </div>
  </div>
</header>

<section class="s-panel">
  <div class="wrap">
    <div class="steps">
      {steps}
    </div>
  </div>
</section>

<!-- ======================================================== WHAT I NEED -->
<section class="s-dark">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ما أحتاجه منك</p>
    <h2 class="h2">ثلاثة أشياء. هذا كل المطلوب.</h2>
    <p class="lede">لن تكون أنت من يدير هذا المشروع. وإن وجدت نفسك تديره، فأنا أخطأت في شيء.</p>

    <div class="give" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div><span class="t">نحو ساعة</span><b>كتالوجك وشروط بيعك</b><p>ماذا تبيع، وبأي شرائح أسعار، وإلى أين تُوصِّل، وفي كم من الوقت.</p></div>
      <div><span class="t">نحو ثلاثين دقيقة</span><b>جولة مراجعة واحدة</b><p>تقرأه، وتؤشّر على ما هو خطأ، وأصلحه. جولة واحدة متوقّعة.</p></div>
      <div><span class="t">خمس دقائق</span><b>وصول، لا كلمات مرور</b><p>رقم واتساب الذي يجب أن تصله الطلبات. ولا شيء حسّاس عبر الرسائل.</p></div>
    </div>
  </div>
</section>

<!-- ==================================================== WHAT CAN GO WRONG -->
<section class="s-cream grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> بكل صراحة معك</p>
    <h2 class="h2">أين يتعثّر هذا العمل.</h2>
    <div class="grid" style="margin-top:26px" data-stagger>
      <article class="card"><span class="n">٠١</span><h3>لا يصلني الكتالوج أبداً</h3><p>أكثر سبب شيوعاً لتعثّر البناء. فالوكيل لا يجيد إلا بقدر ما يعرفه عن مخزونك وشروطك.</p></article>
      <article class="card"><span class="n">٠٢</span><h3>لا أحد يتابع الواتساب</h3><p>النظام يسلّمك مشترين أحياء. وإن بقي الهاتف دون قراءة يومين، تكون قد نقلت الصمت لا أزلته.</p></article>
      <article class="card"><span class="n">٠٣</span><h3>كنت تحتاج نظام ERP</h3><p>إن كانت المشكلة الحقيقية هي مخزون عدة فروع والحسابات في نظام واحد، فهذه أداة خاطئة وسأقول لك ذلك في المكالمة.</p></article>
    </div>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-teal pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">الخطوة الأولى لا تكلّفك شيئاً.</h2>
        <p class="lede" style="margin:0">دعني أراسل نشاطك كما يفعل مشترٍ، وأرسل لك التقرير.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="{CONTACT}#test">اطلب {TEST}</a>
        <a class="btn btn-ghost" href="{wa('مرحباً ناهد، قرأت صفحة طريقة العمل ولدي سؤال.')}">{WA_ICON}اسألني فقط</a>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="process",
    title="طريقة العمل | AI Profit Lab — من أول رسالة إلى نظام يعمل في أسبوع",
    desc=("خمس خطوات: اختبار المشتري الصامت مجاناً، ومحادثة صريحة واحدة، والبناء، والإطلاق، "
          "ووعد الثلاثين يوماً. وما أحتاجه منك، وأين يتعثّر هذا العمل."),
    nav="/process/",
    next=("التالي", "من يبني هذا", "/about/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"HowTo",
  "inLanguage":"ar",
  "name":"كيف يسير أي مشروع مع AI Profit Lab",
  "totalTime":"P7D",
  "step":[
    {"@type":"HowToStep","position":1,"name":"اختبار المشتري الصامت","text":"أراسل نشاطك تماماً كما يفعل مشترٍ وأرسل لك تقريراً بما حدث. مجاناً."},
    {"@type":"HowToStep","position":2,"name":"محادثة صريحة واحدة","text":"ثلاثون دقيقة حول أي نظام يعالج التسرّب، وكم يكلّف، وهل يستحق العمل."},
    {"@type":"HowToStep","position":3,"name":"البناء","text":"من اليوم الأول إلى السادس، مع رابط حيّ في اليوم الثالث وجولة تعديلات واحدة مشمولة."},
    {"@type":"HowToStep","position":4,"name":"الإطلاق","text":"مُختبَر من هاتف حقيقي، وفريقك يتعلّم كيف يعمل في جلسة واحدة."},
    {"@type":"HowToStep","position":5,"name":"وعد الثلاثين يوماً","text":"لم يصلك استفسار حقيقي خلال 30 يوماً؟ يُعاد بناؤه مجاناً، أو تسترد مالك."}
  ]
}""",
)
