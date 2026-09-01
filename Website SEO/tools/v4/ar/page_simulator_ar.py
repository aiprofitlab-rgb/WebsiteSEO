#!/usr/bin/env python3
"""الحاسبات - the Arabic simulators page.

The engine is the English one: `page_simulator.js("ar")` fills the same
template with the Arabic string table in page_simulator.WORDS, so the
arithmetic, the chart, the payback line and the WhatsApp handoff are literally
the same code in both languages. Only the markup and the words are here.

The two tools compare against the same published one-time prices as everywhere
else, read from tools/v4/pay.py rather than typed.
"""
import pay
import page_simulator
from kit import STAR, WA, WA_ICON, url
from page_simulator import CSS, _field  # noqa: F401 - design is shared

from ar_common import AUTO, DASH, DESK, SITE, num, price_ar

__all__ = ["CSS", "JS", "body", "META"]

JS = page_simulator.js("ar")

SVC = url("services", "ar")
DEMOS = url("demos", "ar")

SMART_SITE = pay.omr(pay.price(pay.item(pay.BASE_ID)))
AUTOPILOT = pay.omr(pay.price(pay.item("autopilot")))


def body():
    presets = [
        ("ورشة سيارات", "a1:30,a2:35,a3:25,a4:90"),
        ("تجارة وتوزيع", "a1:22,a2:45,a3:15,a4:420"),
        ("عقارات", "a1:18,a2:50,a3:10,a4:800"),
        ("عيادة", "a1:45,a2:40,a3:30,a4:35"),
    ]
    preset_html = "".join(
        f'<button type="button" data-preset="{v}">{n}</button>' for n, v in presets)

    return f"""<main id="main">

<section class="phero s-panel grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span>الحاسبات</p>
    <h1 class="h1">احسب أرقامك أنت</h1>
    <p class="lede">حاسبتان لأكثر تسرّبين أُسأل عنهما: المشترون الذين يراسلون حين لا يوجد أحد،
      والساعات التي يقضيها فريقك في إعادة إدخال ما تعرفه الآلة أصلاً.
      كل قيمة هنا رقم تضبطه أنت. لا شيء يُخزَّن، ولا شيء يُرسَل، ولا نتيجة هنا وعد.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="#tools">افتح الحاسبات</a>
      <a class="tlink" href="/blog-ar/">اقرأ الطريقة أولاً <span class="arw">&larr;</span></a>
    </div>
  </div>
</section>

<section class="s-dark grain" id="tools">
  <div class="wrap">
    <div class="tabs" id="simtabs" role="tablist" aria-label="اختر حاسبة">
      <button type="button" role="tab" id="tabA" aria-controls="panelA" aria-selected="true" tabindex="0"><em>٠١</em>تكلفة الصمت</button>
      <button type="button" role="tab" id="tabB" aria-controls="panelB" aria-selected="false" tabindex="-1"><em>٠٢</em>تكلفة إعادة الإدخال</button>
    </div>

    <!-- ------------------------------------------------ tool A: silence -->
    <div class="simgrid" id="panelA" role="tabpanel" aria-labelledby="tabA">
      <div class="simin">
        <p class="simlbl"><span class="star">{STAR}</span>أرقامك</p>
        <div class="presets">{preset_html}</div>
        {_field("a1", "استفسارات المشترين في أسبوع عادي", 5, 150, 1, 30, "30")}
        {_field("a2", "نسبة ما يصل خارج ساعات العمل", 5, 80, 5, 35, "35%")}
        {_field("a3", "نسبة الاستفسارات التي تكسبها بعد الردّ", 5, 60, 5, 25, "25%")}
        {_field("a4", "متوسط قيمة الطلب لديك", 20, 2000, 10, 90, "90 ر.ع.")}
        <p class="micro">احسب الأشخاص لا الرسائل، واعتمد أسبوعاً عادياً لا أفضل أسابيعك.
          وقرّب كل رقم إلى الأدنى &mdash; فالحجّة أقوى حين تكون متحفّظة.</p>
      </div>
      <div class="simout">
        <span class="bignum-cap">إيراد على المحكّ، شهرياً</span>
        <span class="bignum" id="AMonthly" dir="ltr">1,023 ر.ع.</span>
        <div class="chain" id="AChain"></div>
        <div class="figs">
          <div><b id="AAnnual" dir="ltr">12,276 ر.ع.</b><span>على مدى اثني عشر شهراً</span></div>
          <div><b id="ADaily" dir="ltr">34 ر.ع.</b><span>كل يوم يبقى فيه مفتوحاً</span></div>
          <div><b id="APayback" dir="ltr">28 يوماً</b><span>لتغطية {num(SMART_SITE)} ر.ع. مرة واحدة</span></div>
        </div>
        <div class="chartwrap">
          <h4>تراكمياً، مقابل التكلفة المرة الواحدة لإغلاقه</h4>
          <svg class="chart" id="AChart" viewBox="0 0 620 210" role="img"
               aria-label="الإيراد التراكمي على المحكّ خلال اثني عشر شهراً، مقارنةً بالتكلفة المرة الواحدة للموقع الذكي"></svg>
          <p class="legend"><span><i style="background:#D89234"></i>الشهر الذي سدّد فيه تكلفته</span>
            <span><i style="background:rgba(241,239,232,.22)"></i>التراكمي على المحكّ</span>
            <span><i class="dash"></i><span id="ACost">{SITE}، مرة واحدة &middot; {num(SMART_SITE)} ر.ع.</span></span></p>
        </div>
        <div class="btn-row">
          <a class="btn btn-wa" id="AWa" href="{WA}">{WA_ICON}<span>أرسل لي هذه الأرقام</span></a>
          <a class="btn btn-ghost" href="{SVC}#price">شاهد ما الذي يغلقه</a>
        </div>
        <p class="assume">هذا ما كان <em>على المحكّ</em> في الرسائل التي لم يردّ عليها أحد &mdash; لا إيراداً
          مضموناً أنك ستستعيده. ولا أضربه عمداً في نسبة استرداد، لأنني عندها أكون قد اخترعت تلك النسبة
          ولن تملك أي وسيلة للتحقق منها.</p>
      </div>
    </div>

    <!-- ----------------------------------------------- tool B: re-typing -->
    <div class="simgrid" id="panelB" role="tabpanel" aria-labelledby="tabB" hidden>
      <div class="simin">
        <p class="simlbl"><span class="star">{STAR}</span>أرقامك</p>
        {_field("b1", "عدد من يعيدون إدخال البيانات بين الأنظمة", 1, 20, 1, 3, "3")}
        {_field("b2", "ساعات كل واحد منهم في ذلك أسبوعياً", 1, 30, 1, 6, "6 س")}
        {_field("b3", "التكلفة المحمّلة لساعة من وقته", 1, 15, 1, 4, "4 ر.ع.")}
        {_field("b4", "الجزء الميكانيكي البحت منه", 10, 90, 5, 70, "70%")}
        <p class="micro">التكلفة المحمّلة تعني الراتب وكل ما يأتي معه، مقسوماً على الساعات المشتغلة فعلاً
          &mdash; لا الأجر بالساعة في العقد. والجزء الميكانيكي هو ما لا اجتهاد فيه: النسخ، وإعادة التنسيق،
          ومطابقة شاشة بأخرى.</p>
      </div>
      <div class="simout">
        <span class="bignum-cap">مدفوع مقابل عمل لا يحاسب عليه أحد، شهرياً</span>
        <span class="bignum" id="BMonthly" dir="ltr">218 ر.ع.</span>
        <div class="chain" id="BChain"></div>
        <div class="figs">
          <div><b id="BAnnual" dir="ltr">2,619 ر.ع.</b><span>على مدى اثني عشر شهراً</span></div>
          <div><b id="BDaily" dir="ltr">7 ر.ع.</b><span>كل يوم يبقى فيه يدوياً</span></div>
          <div><b id="BPayback" dir="ltr">124 يوماً</b><span>لتغطية {num(AUTOPILOT)} ر.ع. مرة واحدة</span></div>
        </div>
        <div class="chartwrap">
          <h4>تراكمياً، مقابل التكلفة المرة الواحدة لأتمتته</h4>
          <svg class="chart" id="BChart" viewBox="0 0 620 210" role="img"
               aria-label="التكلفة التراكمية لإعادة الإدخال اليدوي خلال اثني عشر شهراً، مقارنةً بالتكلفة المرة الواحدة للطيار الآلي الكامل"></svg>
          <p class="legend"><span><i style="background:#D89234"></i>الشهر الذي سدّد فيه تكلفته</span>
            <span><i style="background:rgba(241,239,232,.22)"></i>التكلفة التراكمية</span>
            <span><i class="dash"></i><span id="BCost">{AUTO}، مرة واحدة &middot; {num(AUTOPILOT)} ر.ع.</span></span></p>
        </div>
        <div class="btn-row">
          <a class="btn btn-wa" id="BWa" href="{WA}">{WA_ICON}<span>أرسل لي هذه الأرقام</span></a>
          <a class="btn btn-ghost" href="{SVC}#price">شاهد ما الذي يغلقه</a>
        </div>
        <p class="assume">هذه تكلفة حقيقية لا تكلفة فرصة: أنت تدفعها فعلاً كل شهر في الرواتب.
          وما لا تشمله هو نسبة الخطأ &mdash; الرقم الخاطئ يُكتب مرة واحدة ثم يثق به كل من بعده.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-cream grain">
  <div class="wrap">
    <div class="asterism"><span>{STAR}</span></div>
    <p class="eyebrow"><span class="star">{STAR}</span>كيف تقرأ النتيجة</p>
    <h2 class="h2">ثلاث قواعد تُبقي الرقم صادقاً</h2>
    <div class="method grid" data-stagger style="margin-top:clamp(28px,4vw,44px)">
      <div class="card">
        <span class="n">٠١</span>
        <h3>كل قيمة هي قيمتك أنت</h3>
        <p>لا يوجد في هذه الصفحة متوسط قطاعي واحد. وإن بدت النتيجة خاطئة، فأحد مدخلاتك الأربعة خاطئ
          &mdash; وأنت وحدك من يستطيع تصحيحه.</p>
      </div>
      <div class="card">
        <span class="n">٠٢</span>
        <h3>على المحكّ، لا مُستعاد</h3>
        <p>الحاسبة الأولى تسعّر ما كان في تلك الرسائل، لا ما سيستعيده أي نظام. ومن يعطيك نسبة استرداد
          ثابتة فقد اخترعها.</p>
      </div>
      <div class="card">
        <span class="n">٠٣</span>
        <h3>مرة واحدة مقابل شهري</h3>
        <p>المقارنة التي تهمّ هي تسرّب متكرر مقابل تكلفة تدفعها مرة واحدة. وهذا وحده سبب وجود خط
          التسديد على الرسم.</p>
      </div>
    </div>
  </div>
</section>

<section class="s-panel grain fixes">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span>ما الذي يشتريه المال</p>
    <h2 class="h2">الأسعار المعلنة التي تقارن بها هذه الرسوم</h2>
    <p class="lede">لا &laquo;السعر عند الطلب&raquo;، ولا مكالمة استكشاف قبل أن تُخبَر برقم.</p>
    <div class="tblwrap" style="margin-top:clamp(24px,3vw,34px)">
      <table class="tbl">
        <thead><tr>
          <th scope="col">ما هو</th><th scope="col">دفعة واحدة</th><th scope="col">المطلوب شهرياً</th>
        </tr></thead>
        <tbody>
          <tr>
            <th scope="row"><b>{SITE}</b>
              <span>موقع بداخله وكيل يردّ على المشترين بالعربية والإنجليزية</span></th>
            <td class="n" data-l="دفعة واحدة"><span class="v">{price_ar('website')}</span></td>
            <td class="n nil" data-l="المطلوب شهرياً"><span class="v">{num('0')} ر.ع.</span></td>
          </tr>
          <tr>
            <th scope="row"><b>{DASH}</b>
              <span>السيولة والهامش والمخزون والطلبات المفتوحة على شاشة واحدة</span></th>
            <td class="n" data-l="دفعة واحدة"><span class="v"><i class="plus">+</i>{price_ar('dashboard')}</span></td>
            <td class="n nil" data-l="المطلوب شهرياً"><span class="v">{num('0')} ر.ع.</span></td>
          </tr>
          <tr>
            <th scope="row"><b>{AUTO}</b>
              <span>متابعة عروض الأسعار والفواتير تتوقف فور أن يردّ المشتري</span></th>
            <td class="n" data-l="دفعة واحدة"><span class="v"><i class="plus">+</i>{price_ar('autopilot')}</span></td>
            <td class="n nil" data-l="المطلوب شهرياً"><span class="v">{num('0')} ر.ع.</span></td>
          </tr>
          <tr>
            <th scope="row"><b>{DESK}</b>
              <span>اختياري، يُلغى في أي وقت، وغير مطلوب أبداً لإبقاء النظام يعمل</span></th>
            <td class="n nil" data-l="دفعة واحدة"><span class="v">&mdash;</span></td>
            <td class="n" data-l="المطلوب شهرياً"><span class="v">{price_ar('desk')}/شهرياً</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="tblnote">السعر المسبوق بعلامة <i class="plus">+</i> يُضاف إلى {SITE} ولا يحلّ محلّه. و{DESK}
      هو البند الشهري الوحيد هنا، وإلغاؤه لا يوقف شيئاً.</p>
    <div class="btn-row" style="margin-top:26px">
      <a class="btn btn-teal" href="{SVC}#price">صفحة الأسعار كاملة</a>
      <a class="btn btn-ghost" href="{DEMOS}">شاهده يردّ على مشترٍ</a>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="simulators",
    title="الحاسبات | AI Profit Lab — احسب تكلفة الصمت وإعادة الإدخال",
    desc=("حاسبتان بأرقامك أنت: ما تضعه الرسائل التي لا يردّ عليها أحد على المحكّ شهرياً، وما تكلّفه "
          "ساعات إعادة إدخال البيانات. لا متوسطات قطاعية، ولا شيء يُرسَل أو يُخزَّن."),
    nav="/simulators-ar/",
    next=("التالي", "شاهد الأنظمة تعمل", "/demos-ar/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"WebApplication",
  "inLanguage":"ar",
  "name":"حاسبات AI Profit Lab",
  "applicationCategory":"BusinessApplication",
  "operatingSystem":"Web",
  "description":"حاسبتان لأصحاب الأعمال في عُمان: تكلفة الاستفسارات التي لا يردّ عليها أحد، وتكلفة إعادة الإدخال اليدوي للبيانات. كل قيمة يضبطها المستخدم ولا شيء يُخزَّن.",
  "offers":{"@type":"Offer","price":"0","priceCurrency":"OMR"}
}""",
)
