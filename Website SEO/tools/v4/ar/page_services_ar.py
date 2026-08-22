#!/usr/bin/env python3
"""ما أبنيه - the Arabic Services page.

Design imported from page_services.py. Two things are authored fresh rather
than translated in place:

  * The follow-up rail SVG. It is a vertical timeline with the spine on the
    left and the labels to its right; on an Arabic page that reads backwards,
    so the coordinates are mirrored here (spine at x=426, labels anchored at
    x=402). The text groups are pinned to direction:ltr with text-anchor:end,
    which is the only combination whose anchoring is unambiguous across
    engines - each Arabic label is still a single RTL run inside it, so the
    words themselves read correctly.

  * Every price. The English table hand-writes its figures and the build
    asserts they match tools/v4/pay.py; the Arabic table computes them from
    pay.py directly, so there is nothing to drift. The build still runs the
    same assertion over this page as a second net.
"""
import pay
from kit import STAR, WA_ICON, url
from page_services import CSS  # noqa: F401 - design is shared

from ar_common import (AUTO, DASH, DESK, FOUNDING, ONE_TIME, PLAN_FULL,
                       PLAN_PROOF, PLAN_THREE, SITE, STACK, TEST, bundle_ar,
                       num, plan_instalment_ar, plan_total_ar, price_ar, wa)

__all__ = ["CSS", "body", "META"]

CONTACT = url("contact", "ar")
PROCESS = url("process", "ar")
DEMOS = url("demos", "ar")
CHK = url("checkout", "ar")


def _rail_svg():
    """The follow-up schedule, mirrored for RTL. See the module docstring."""
    beats = [
        (34, "اليوم ٠", "أُرسِل عرض السعر", "#D89234"),
        (110, "اليوم ٢", "&laquo;هل ناسبك السعر؟&raquo;", "#0F6E56"),
        (186, "اليوم ٥", "&laquo;هل أحجز لك الكمية؟&raquo;", "#0F6E56"),
        (258, "اليوم ٩", "تذكير بالفاتورة", "#1FAF5E"),
    ]
    out = []
    for y, day, label, fill in beats:
        out.append(
            f'            <circle cx="426" cy="{y}" r="7" fill="{fill}" stroke="none"/>\n'
            f'            <text x="402" y="{y - 4}">{day}</text>\n'
            f'            <text x="402" y="{y + 16}" font-family="IBM Plex Sans Arabic, sans-serif" '
            f'font-size="15" fill="#F1EFE8">{label}</text>'
        )
    return f"""<svg class="rail-svg drawn" viewBox="0 0 460 300" role="img" aria-labelledby="railT railD">
          <title id="railT">جدول المتابعة</title>
          <desc id="railD">يُرسَل عرض السعر في اليوم صفر. ثم تذكير أول في اليوم الثاني، وثانٍ في اليوم
            الخامس، وتذكير بالفاتورة في اليوم التاسع. وتتوقف السلسلة فور أن يردّ المشتري أو يدفع.</desc>
          <line x1="426" y1="30" x2="426" y2="262" stroke="#1E5344" stroke-width="2"/>
          <g font-family="IBM Plex Mono, monospace" font-size="13" fill="#E8C98F"
             style="direction:ltr;text-anchor:end">
{chr(10).join(out)}
          </g>
        </svg>"""


def _p1():
    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ما أبنيه</p>
    <h1 class="h1">أنت تصف المشكلة.<br>وأنا أبني النظام الذي يزيلها.</h1>
    <p class="lede">ثلاثة أنظمة، كل واحد منها بناء واحد بسعر ثابت. لا يحتاج أيٌّ منها اشتراكاً شهرياً
      كي يستمر في العمل، وكل سعر مذكور على هذه الصفحة.</p>
    <div class="btn-row" style="margin-top:30px">
      <a class="btn btn-teal" href="#price">انتقل إلى قائمة الأسعار</a>
      <a class="tlink" href="{PROCESS}">كيف يسير البناء فعلاً <span class="arw">&larr;</span></a>
    </div>
  </div>
</header>

<div class="stats" aria-label="لمحة سريعة">
  <div><b><span data-count="168">168</span></b><span>ساعة مغطّاة أسبوعياً،<br>بما فيها الجمعة</span></div>
  <div><b>أسبوع تقريباً</b><span>من البدء<br>حتى الإطلاق</span></div>
  <div><b>لغتان</b><span>وكلتاهما<br>بالمستوى نفسه</span></div>
  <div><b>صفر</b><span>ريال عُماني مطلوب شهرياً<br>لإبقائه يعمل</span></div>
</div>

<!-- ==================================================== 01 - THE SMART WEBSITE -->
<section class="s-cream grain" id="smart-website">
  <div class="wrap">
    <div class="sysblock">
      <div>
        <span class="kicker">٠١ &#183; الأساس</span>
        <h3>{SITE}</h3>
        <p>موقع بلغتين، وبداخله وكيل يردّ على المشترين. يجيب بالعربية أو بالإنجليزية، ويعرف كتالوجك
          وشروط التوصيل لديك، ويحوّل الجادّين منهم إلى واتساب الخاص بك.</p>
        <ul class="deliver">
          <li>موظف لا ينام &mdash; الرابعة فجراً، والجمعة، والعيد</li>
          <li>الطلبات الساخنة تصل إلى هاتفك مباشرة</li>
          <li>مسار عرض سعر بالجملة، لا خانة &laquo;اتصل بنا&raquo;</li>
          <li>ملخّص قصير عمّن زار وماذا كان يريد</li>
          <li>يجده جوجل <em>و</em>يجده ChatGPT</li>
          <li>سنة كاملة من الاستضافة والحماية والرعاية مشمولة</li>
        </ul>
        <div class="pricetag"><b>{price_ar('website')}</b><span>{ONE_TIME} &#183; سعر {FOUNDING}</span></div>
        <a class="btn btn-wa" href="{wa('مرحباً ناهد، أريد السؤال عن الموقع الذكي.')}">{WA_ICON}اسأل عن موعد بناء متاح</a>
      </div>
      <div class="art rv">
        <div class="phone">
          <div class="screen">
            <div class="bar"><span class="av">AI</span><span><b>الخليج لوتس للتجارة</b><em>يردّ عادةً فوراً</em></span></div>
            <div class="thread">
              <div class="msg them">هل توصلون إلى صحار؟ وكم سعر الجملة؟<time>21:47</time></div>
              <div class="msg us">نعم، نوصل إلى صحار خلال {num('48')} ساعة. كم كرتوناً تحتاج؟<time>21:47</time></div>
              <div class="msg them" lang="en" dir="ltr">Around 40 cartons. Same price in English please.<time>21:48</time></div>
              <div class="msg us" lang="en" dir="ltr">Yes &mdash; Sohar is a next-day route. For 40 cartons you are in the bulk tier, so I can send you the wholesale sheet now.<time>21:48</time></div>
              <div class="msg us">هل آخذ اسمك واسم الشركة كي يؤكّد لك ناهد توفّر الكمية صباحاً؟<time>21:48</time></div>
              <div class="typing" aria-label="المشتري يكتب"><i></i><i></i><i></i></div>
            </div>
          </div>
        </div>
        <p class="lede" style="text-align:center;font-size:.9rem;margin:18px auto 0;max-width:34ch">مثال توضيحي لوكيل المشتري. كتالوجك أنت، وشروطك أنت، وأسلوبك أنت.</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== 02 - THE DASHBOARD -->
<section class="s-panel" id="dashboard">
  <div class="wrap">
    <div class="sysblock flip">
      <div>
        <span class="kicker">٠٢ &#183; إضافة</span>
        <h3>{DASH}</h3>
        <p>بعد أن يبدأ المشترون في الوصول، يصبح السؤال التالي: هل تعرف وضعك أنت حين يتصل أحدهم؟
          هذه اللوحة تجيب عن ذلك دون أن تضطر للاتصال بثلاثة أشخاص أولاً.</p>
        <ul class="deliver">
          <li>السيولة وهامش الربح والمخزون على شاشة واحدة</li>
          <li>البضاعة الراكدة والأصناف الخاسرة، بالاسم</li>
          <li>ما الذي تفعله حيال كل واحد منها، في جملة واضحة</li>
          <li>يقرأ من الأنظمة التي تستخدمها أصلاً</li>
        </ul>
        <div class="pricetag"><b>+{price_ar('dashboard')}</b><span>{ONE_TIME} &#183; تُضاف إلى {SITE}</span></div>
        <div class="btn-row">
          <a class="btn btn-teal" href="{DEMOS}#dash">افتح التجربة الحيّة</a>
          <a class="tlink" href="#price">شاهدها في قائمة الأسعار <span class="arw">&larr;</span></a>
        </div>
      </div>
      <div class="art rv">
        <div class="dash">
          <div class="dhead"><b>الملخّص التنفيذي</b><span>حيّ &#183; متزامن</span></div>
          <div class="kpis">
            <div class="kpi"><span>الإيراد منذ بداية الشهر</span><b>{num('109')} ألف ر.ع.</b><i>&uarr; {num('12')}%</i></div>
            <div class="kpi"><span>الربح الإجمالي</span><b>{num('41.9')} ألف ر.ع.</b><i>هامش {num('38.4')}%</i></div>
            <div class="kpi"><span>تحت الحد الأدنى</span><b>{num('16 / 47')}</b><i class="dn">عاجل</i></div>
          </div>
          <div class="alertrow"><em>حرج &mdash; تصرّف اليوم</em><p>المعدات الثقيلة تسحب الهامش الإجمالي إلى الأسفل بمقدار {num('4.2')} نقطة. والسبب هو الشحن.</p></div>
          <div class="alertrow"><em>فرصة &mdash; هذا الأسبوع</em><p>{num('6,900')} ر.ع. من السيولة محتجزة في {num('4')} أصناف راكدة، وتكلّفك {num('350')} ر.ع. شهرياً رسوم مخازن.</p></div>
          <div class="alertrow ok"><em>خبر جيد &mdash; ضاعف عليه</em><p>عبوات الخلط وأشرطة المقاومة هي أعلى أصنافك هامشاً، ومخزونها يوشك على النفاد.</p></div>
        </div>
        <p class="lede" style="text-align:center;font-size:.9rem;margin:18px auto 0;max-width:34ch">أرقام توضيحية. النسخة الحيّة تقرأ أرقامك أنت.</p>
      </div>
    </div>
  </div>
</section>

<!-- ===================================================== 03 - THE AUTOPILOT -->
<section class="s-dark" id="autopilot">
  <div class="wrap">
    <div class="sysblock">
      <div>
        <span class="kicker">٠٣ &#183; إضافة</span>
        <h3>{AUTO}</h3>
        <p>عروض الأسعار والفواتير لا تطارد نفسها، ولا أحد في مكتب مزدحم يتذكّرها كلها.
          هذا النظام يتذكّرها، وفق جدول، وباسمك أنت.</p>
        <ul class="deliver">
          <li>متابعة عروض الأسعار، بفواصل زمنية ولباقة</li>
          <li>تذكير بالفواتير قبل موعد الاستحقاق وبعده</li>
          <li>يتوقف فور أن يردّ المشتري أو يدفع</li>
          <li>كل رسالة مسجّلة في مكان تستطيع قراءته</li>
        </ul>
        <div class="pricetag"><b>+{price_ar('autopilot')}</b><span>{ONE_TIME} &#183; تُضاف إلى {SITE}</span></div>
        <a class="btn btn-ghost" href="#price">شاهده في قائمة الأسعار</a>
      </div>
      <div class="art rv">
        {_rail_svg()}
        <p class="lede" style="text-align:center;font-size:.9rem;margin:14px auto 0;max-width:36ch">ردّ واحد من المشتري، وتتوقف السلسلة كلها.</p>
      </div>
    </div>
  </div>
</section>
"""


def _p2():
    deposit = pay.money_ar(pay.DEPOSIT)
    pay_how = "بالبطاقة أو بحوالة بنكية" if pay.PAY_LIVE else "بحوالة بنكية"
    return f"""
<!-- ================================================== THE WHOLE PRICE LIST -->
<section class="s-white" id="price">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> قائمة الأسعار كاملة</p>
    <h2 class="h2">كل رقم، على الصفحة، قبل أن تتحدث إليّ.</h2>
    <p class="lede">سعر {FOUNDING} يسري على المجموعة الأولى المحدودة فقط. والعمود القياسي هو ما يُنشَر
      بعد إغلاق تلك المجموعة.</p>

    <div class="tablewrap rv" style="margin-top:clamp(26px,3.5vw,44px)">
      <table class="t">
        <caption>كل درجة، وما الذي تضيفه</caption>
        <thead>
          <tr><th scope="col">ما الذي تحصل عليه</th><th scope="col" class="n">{FOUNDING}</th><th scope="col" class="n">السعر القياسي</th><th scope="col">طريقة الاحتساب</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><b>{TEST}</b><span class="mini">أراسل نشاطك كما يفعل مشترٍ، وأرسل لك التقرير</span></td>
            <td class="n">مجاناً</td><td class="n">مجاناً</td><td>&mdash;</td>
          </tr>
          <tr class="hi">
            <td><b>{SITE}</b><span class="mini">موقع بلغتين، ووكيل مشترٍ بالذكاء الاصطناعي، ومسار عرض سعر بالجملة، وتحويل إلى واتساب، وظهور في بحث الذكاء الاصطناعي، وسنة استضافة ورعاية</span></td>
            <td class="n">{price_ar('website')}</td><td class="n">{price_ar('website', standard=True)}</td><td>{ONE_TIME}</td>
          </tr>
          <tr>
            <td>+ {DASH}<span class="mini">لوحة للسيولة والمخزون والطلبات المفتوحة</span></td>
            <td class="n">+{price_ar('dashboard')}</td><td class="n">+{price_ar('dashboard', standard=True)}</td><td>{ONE_TIME}</td>
          </tr>
          <tr>
            <td>+ {AUTO}<span class="mini">متابعة عروض الأسعار والفواتير، وفق جدول</span></td>
            <td class="n">+{price_ar('autopilot')}</td><td class="n">+{price_ar('autopilot', standard=True)}</td><td>{ONE_TIME}</td>
          </tr>
          <tr>
            <td><b>{STACK}</b><span class="mini">الأنظمة الثلاثة معاً</span></td>
            <td class="n">{bundle_ar()}</td><td class="n">{bundle_ar(standard=True)}</td><td>{ONE_TIME}</td>
          </tr>
          <tr>
            <td>{DESK}<span class="mini">رعاية شهرية اختيارية، وميزات جديدة، ومراجعة للتقارير. غير مطلوب أبداً لإبقاء أي شيء يعمل.</span></td>
            <td class="n">{price_ar('desk')}/شهرياً</td><td class="n">{price_ar('desk', standard=True)}/شهرياً</td><td>اشتراك اختياري، يُلغى في أي وقت</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</section>

<!-- ==================================================== THREE WAYS TO PAY -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> ثلاث طرق للدفع</p>
    <h2 class="h2">البناء نفسه. اختر ما ترتاح إليه.</h2>

    <div class="pay-grid" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div class="pay hero-pay">
        <span class="badge">أكثر ما يبدأ به أصحاب الأعمال</span>
        <h3>{PLAN_PROOF}</h3>
        <span class="price">{plan_total_ar('proof')}</span>
        <p>لا شيء اليوم. ولا شيء عند الإطلاق. أرسل لك الفاتورة فقط بعد أن ينتج موقعك الذكي أول
          استفسار حقيقي وقابل للتحقق من مشترٍ. وإن لم ينتجه أبداً، فلن تدفع أبداً.</p>
        <div class="btn-row"><a class="btn btn-amber" href="{CHK}?plan=proof">ابدأ هذا الطلب</a><a class="btn btn-ghost" href="{wa('مرحباً ناهد، أريد الموقع الذكي بصيغة الدفع عند الإثبات.')}">{WA_ICON}اسأل أولاً</a></div>
      </div>
      <div class="pay">
        <span class="badge">الأقل تكلفة</span>
        <h3>{PLAN_FULL}</h3>
        <span class="price">{plan_total_ar('full')}</span>
        <p>يُدفَع مقدّماً {pay_how}. يوفّر عليك {pay.money_ar(pay.plan('proof')['surcharge'])} مقارنةً
          بـ{PLAN_PROOF}، ويشمل مجاناً تحرير المحتوى العربي، وضبط ملفّك في نشاطي التجاري على جوجل،
          وجلسة تدريب واحدة للفريق.</p>
        <div class="btn-row"><a class="btn btn-ghost" href="{CHK}?plan=full">ابدأ هذا الطلب</a><a class="btn btn-ghost" href="{wa('مرحباً ناهد، أريد الموقع الذكي مدفوعاً مقدّماً.')}">{WA_ICON}اسأل أولاً</a></div>
      </div>
      <div class="pay">
        <span class="badge">وزّعها على مراحل</span>
        <h3>{PLAN_THREE}</h3>
        <span class="price">{num('3')} &times; {plan_instalment_ar('three')}</span>
        <p>عند التوقيع، وعند الإطلاق، وبعد ثلاثين يوماً. المجموع أقل من راتب شهر واحد لموظف إداري
          &mdash; ويستمر في العمل بعد انتهاء الأشهر الثلاثة.</p>
        <div class="btn-row"><a class="btn btn-ghost" href="{CHK}?plan=three">ابدأ هذا الطلب</a><a class="btn btn-ghost" href="{wa('مرحباً ناهد، أريد الموقع الذكي على ثلاث دفعات.')}">{WA_ICON}اسأل أولاً</a></div>
      </div>
    </div>

    <p class="lede" style="margin:clamp(20px,2.6vw,30px) auto 0;max-width:66ch">
      لست مستعداً للالتزام بالمبلغ كاملاً اليوم؟ <a href="{CHK}">احجز موعد بناء مقابل {deposit}</a>
      بدلاً من ذلك &mdash; يحفظ لك مكانك في الدور، ويُخصم من سعرك بالكامل، وقابل للاسترداد حتى يوم
      بدء البناء.</p>

    <!-- The exclusions sit immediately beside the price. That placement is the
         point: it is where honesty does the most work. -->
    <div class="nolog rv" style="margin-top:clamp(34px,4.5vw,60px)">
      <h3 class="h3">ما هو غير مشمول &mdash; قبل أن يتحرك أي مبلغ</h3>
      <ul>
        <li>هذا <b>ليس نظام ERP</b>. إن كنت تحتاج مخزون عدة فروع والحسابات في نظام واحد، فذلك وزن مختلف
          تماماً وسأقول لك ذلك في المكالمة.</li>
        <li>وهو <b>لا يغني عن محاسبك</b>. يريك ما يحدث الآن، ويبقى إقفال الدفاتر عملهم هم.</li>
        <li>لا إدارة إعلانات مدفوعة، ولا إدارة مستمرة لمواقع التواصل، ولا كتابة محتوى مستمرة بعد
          النص الأول لموقعك.</li>
        <li>لا معالجة مدفوعات إلكترونية ولا سلة شراء. وإن احتجتها، تُدرَس وتُسعَّر على حدة.</li>
        <li>الأسعار أعلاه مبنية على كتالوج منتجات واحد وزوج لغات واحد. وأي شيء أكبر من ذلك فعلاً
          يُسعَّر على حدة، لا يُحشَر في باقة.</li>
      </ul>
    </div>
  </div>
</section>

<!-- ======================================================= BUILT TO ORDER -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> يُبنى حسب الطلب</p>
    <h2 class="h2">والأشياء التي يحتاجها عملك أنت وحده.</h2>
    <p class="lede">تُدرَس وتُسعَّر واحدة تلو الأخرى، وغالباً فوق نظام قائم بالفعل.</p>

    <div class="ord" style="margin-top:clamp(26px,3.5vw,42px)" data-stagger>
      <div><h4>تحرير المحتوى العربي</h4><p>إعادة صياغة صفحاتك الحالية بحيث يأخذك المشتري العربي على محمل الجدّ.</p></div>
      <div><h4>ملف نشاطي التجاري على جوجل</h4><p>مُصحَّح، وموثَّق، ومثبَّت على الموقع الصحيح في الخريطة.</p></div>
      <div><h4>أتمتة عروض الأسعار</h4><p>تجميع أسعار الجملة وإرسالها دون إعادة بنائها في كل مرة.</p></div>
      <div><h4>تنبيهات المورّدين والمخزون</h4><p>تُخبَر قبل أن ينفد المخزون، لا بعد أن يسأل مشترٍ.</p></div>
      <div><h4>تدريب الفريق</h4><p>ساعتان في مكتبك، حتى يستخدم الفريق فعلاً ما تم بناؤه.</p></div>
      <div><h4>شيء آخر تماماً</h4><p>صِف نقطة الاختناق. وإن كنت لا أستطيع بناءها، سأقول ذلك.</p></div>
    </div>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">لست متأكداً أيها تحتاج؟</h2>
        <p class="lede" style="margin:0">ابدأ بالمجاني إذاً. سأراسل نشاطك كما يفعل مشترٍ وأرسل لك التقرير
          &mdash; بلا أي التزام، وتحتفظ به في الحالتين.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="{CONTACT}#test">اطلب {TEST}</a>
        <a class="btn btn-ghost" href="{CHK}">أو ابدأ طلباً</a>
        <a class="btn btn-ghost" href="{PROCESS}">شاهد كيف يسير البناء</a>
      </div>
    </div>
  </div>
</section>

</main>
"""


def body():
    return _p1() + _p2()


META = dict(
    slug="services",
    title="ما أبنيه | AI Profit Lab — ثلاثة أنظمة، وكل سعر معلن",
    desc=("الموقع الذكي، ولوحة متابعة المالك الحيّة، والطيار الآلي الكامل — ماذا يفعل كل واحد منها، "
          "وكم يكلّف بالريال العُماني، وما هو غير مشمول عن قصد."),
    nav="/services/",
    next=("التالي", "طريقة العمل", "/process/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"ItemList",
  "inLanguage":"ar",
  "name":"الأنظمة التي يبنيها AI Profit Lab",
  "itemListElement":[
    {"@type":"Service","position":1,"name":"الموقع الذكي","description":"موقع بلغتين مع وكيل مشترٍ بالذكاء الاصطناعي يردّ بالعربية والإنجليزية ويحوّل المشترين الأحياء إلى واتساب.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"950","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/checkout/?plan=website","priceValidUntil":"2026-12-31"}},
    {"@type":"Service","position":2,"name":"لوحة متابعة المالك الحيّة","description":"السيولة وهامش الربح والمخزون والطلبات المفتوحة على شاشة واحدة، ومع كل بند الإجراء الذي يطلبه.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"650","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/checkout/?plan=dashboard","priceValidUntil":"2026-12-31"}},
    {"@type":"Service","position":3,"name":"الطيار الآلي الكامل","description":"متابعة عروض الأسعار والفواتير وفق جدول، وتتوقف فور أن يردّ المشتري أو يدفع.","provider":{"@id":"https://aiprofitlab.io/#organization"},"areaServed":"Oman","offers":{"@type":"Offer","price":"900","priceCurrency":"OMR","availability":"https://schema.org/InStock","url":"https://aiprofitlab.io/checkout/?plan=autopilot","priceValidUntil":"2026-12-31"}}
  ]
}""",
)
