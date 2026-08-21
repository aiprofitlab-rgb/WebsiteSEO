#!/usr/bin/env python3
"""تواصل معي - the Arabic Contact page.

Design imported from page_contact.py. Two things are translated rather than
shared: the FAQ answers, and the Silent Buyer Test capture script, whose
composed WhatsApp message has to arrive in Arabic or the whole point of the
Arabic page is lost at the last step.

The payment answer is gated on tools/v4/pay.py exactly as the English page is,
so the Arabic FAQ cannot go on saying "no card is taken on this site" after one
is switched on.
"""
import pay
from kit import MAIL_ICON, STAR, WA_ICON, url
from page_contact import CSS, PHONE_ICON  # noqa: F401 - design is shared

from ar_common import (AUTO, DASH, DESK, FOUNDING, PROMISE, SITE, bundle_ar,
                       num, price_ar, wa)

__all__ = ["CSS", "body", "JS", "META"]

SVC = url("services", "ar")
CHK = url("checkout", "ar")
DEMOS = url("demos", "ar")


def _body():
    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> تواصل معي</p>
    <h1 class="h1">ستتحدث إلى الشخص<br>الذي يبني النظام بنفسه.</h1>
    <p class="lede">لا فريق مبيعات ولا نظام تذاكر. كل طريق في الأسفل يصل إلى الهاتف نفسه.</p>
  </div>
</header>

<section class="s-cream grain" style="padding-top:0">
  <div class="wrap">
    <div class="chan" data-stagger>
      <a class="primary" href="{wa('مرحباً ناهد، لدي سؤال عن عملي.')}">
        <span class="ic">{WA_ICON}</span>
        <h3>واتساب</h3>
        <span class="val" dir="ltr">+968 9924 5250</span>
        <span class="when"><i></i>عادةً في اليوم نفسه</span>
      </a>
      <a href="mailto:hello@aiprofitlab.io">
        <span class="ic">{MAIL_ICON}</span>
        <h3>البريد الإلكتروني</h3>
        <span class="val" dir="ltr">hello@aiprofitlab.io</span>
        <span class="when"><i></i>خلال يوم عمل واحد</span>
      </a>
      <a href="tel:+96899245250">
        <span class="ic">{PHONE_ICON}</span>
        <h3>الهاتف</h3>
        <span class="val" dir="ltr">+968 9924 5250</span>
        <span class="when"><i></i>{num('9')} صباحاً &ndash; {num('6')} مساءً بتوقيت مسقط</span>
      </a>
    </div>
  </div>
</section>

<!-- ================================================== SILENT BUYER TEST -->
<section class="s-dark" id="test">
  <span class="plate" aria-hidden="true">
    <img src="/audit-bg.webp" alt="" width="1000" height="667" loading="lazy" decoding="async">
  </span>
  <div class="wrap">
    <div class="capture-grid">
      <div>
        <p class="eyebrow"><span class="star">{STAR}</span> مجاناً &#183; خمسة أسبوعياً</p>
        <h2 class="h2">قبل أن تشتري، انظر إلى ما يراه المشتري.</h2>
        <p class="lede">أتواصل مع نشاطك تماماً كما يفعل مشترٍ حقيقي &mdash; واتساب، ونموذج، وبريد، وهاتف.</p>
        <ul class="getlist">
          <li>كم استغرق كل قناة حتى ردّت &mdash; مقيسة، لا مقدّرة</li>
          <li>ما الذي رآه المشتري فعلاً، بالعربية أيضاً</li>
          <li>إلى أين كان سيذهب ذلك المشتري بدلاً منك</li>
          <li>بلا أي عرض بيع مرفق</li>
        </ul>
      </div>

      <form id="sbtForm" class="form-grid" novalidate>
        <div class="field">
          <label for="f-name">اسمك</label>
          <input id="f-name" name="name" type="text" required placeholder="اسمك">
        </div>
        <div class="field">
          <label for="f-biz">اسم النشاط</label>
          <input id="f-biz" name="business" type="text" required placeholder="مثال: الخليج للتجارة">
        </div>
        <div class="field">
          <label for="f-wa">رقم واتساب</label>
          <input id="f-wa" name="whatsapp" type="tel" required placeholder="+968 &hellip;" inputmode="tel" dir="ltr">
        </div>
        <div class="field">
          <label for="f-sell">ماذا تبيع؟</label>
          <input id="f-sell" name="sells" type="text" required placeholder="مستهلكات طبية، بالجملة">
        </div>
        <div class="field full">
          <button class="btn btn-wa" type="submit" style="width:100%">{WA_ICON}أرسل بياناتي على واتساب</button>
          <p class="formnote">لا يُرسَل شيء حتى تضغط زر الإرسال داخل واتساب.</p>
        </div>
      </form>
    </div>
  </div>
</section>

<!-- ================================================================ FAQ -->
<section class="s-cream grain">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> الأسئلة المحرجة</p>
    <h2 class="h2">مطروحة، ومُجاب عنها.</h2>

    <div class="faq" style="margin-top:clamp(22px,3vw,38px)">
      <details>
        <summary>كم التكلفة؟</summary>
        <p class="ans">{SITE}: {price_ar('website')} بسعر {FOUNDING}، و{price_ar('website', standard=True)} بالسعر
          القياسي. {DASH} بزيادة {price_ar('dashboard')}، و{AUTO} بزيادة {price_ar('autopilot')}،
          والثلاثة معاً {bundle_ar()}. كل رقم موجود في
          <a href="{SVC}#price">قائمة الأسعار</a>.</p>
      </details>
      <details>
        <summary>هل هناك رسوم شهرية؟</summary>
        <p class="ans">لا شيء مطلوب لإبقاء النظام يعمل. السنة الأولى من الاستضافة والحماية والرعاية
          مشمولة في سعر البناء. و{DESK} بـ{price_ar('desk')} شهرياً اختياري تماماً.</p>
      </details>
      <details>
        <summary>هل لديك عملاء يمكنني التحدث إليهم؟</summary>
        <p class="ans">ليس بعد، ولن أدّعي غير ذلك. ولهذا السبب تحديداً يوجد ضمان بالاسم، وتجربتان
          مفتوحتان للنقر دون أن أطلب منك شيئاً: <a href="{DEMOS}#dash">لوحة المتابعة</a>
          و<a href="{DEMOS}">وكيل المشتري</a>.</p>
      </details>
      <details>
        <summary>وماذا لو لم ينجح؟</summary>
        <p class="ans">{PROMISE}: إن لم يصلك استفسار حقيقي من مشترٍ خلال {num('30')} يوماً من الإطلاق،
          أعيد بناءه مجاناً. وإن لم يصلك بعدها، تسترد مالك.</p>
      </details>
      <details>
        <summary>هل تعمل بالعربية؟</summary>
        <p class="ans">نعم &mdash; اللغتان بالمستوى نفسه، والنص العربي يراجعه قارئ عربي قبل النشر.</p>
      </details>
      <details>
        <summary>مع من أتعاقد فعلياً؟</summary>
        <p class="ans">مع شركة لوتس الخليج العالمية &mdash; <span lang="en" dir="ltr">Lotus Gulf International</span>،
          س.ت <span dir="ltr">1570092</span>، بوشر، مسقط. و&laquo;AI Profit Lab&raquo; هي العلامة التجارية.
          الشركة غير مسجّلة في ضريبة القيمة المضافة، فالفواتير لا تحمل بند ضريبة.</p>
      </details>
      <details>
        <summary>كيف أدفع؟</summary>
        <p class="ans">{{PAY_ANSWER}}</p>
      </details>
    </div>
  </div>
</section>

</main>
"""


def body():
    if pay.PAY_LIVE:
        answer = (f'بالبطاقة عبر <a href="{CHK}">صفحة الطلب</a>، أو بحوالة بنكية بالريال العُماني '
                  f'&mdash; عند البدء، أو على ثلاث دفعات، أو بعد أن يأتيك استفسار حقيقي فعلاً. '
                  f'كل صيغة موضّحة في <a href="{SVC}#price">صفحة الأسعار</a>.')
    else:
        answer = (f'بحوالة بنكية بالريال العُماني &mdash; عند البدء، أو على ثلاث دفعات، أو بعد أن '
                  f'يأتيك استفسار حقيقي فعلاً. كل صيغة موضّحة في '
                  f'<a href="{SVC}#price">صفحة الأسعار</a>. يمكنك تجهيز طلبك على '
                  f'<a href="{CHK}">صفحة الطلب</a> وأرسل لك الفاتورة؛ والدفع بالبطاقة على الموقع '
                  f'قيد التفعيل الآن.')
    return _body().replace("{PAY_ANSWER}", answer)


JS = """
/* ---------------------------------------------------------------------------
   Silent Buyer Test capture, Arabic.

   Same mechanism as the English page: it composes a WhatsApp message rather
   than posting to a backend, so nothing is transmitted until the visitor
   presses send inside WhatsApp - which is exactly what the note under the
   button promises. The message itself is Arabic, because a visitor who filled
   in an Arabic form and got handed an English draft would reasonably assume
   the form was broken.
--------------------------------------------------------------------------- */
(function(){
  "use strict";
  var form = document.getElementById("sbtForm");
  if (!form) return;

  form.addEventListener("submit", function(e){
    e.preventDefault();
    var get = function(n){ return (form.elements[n].value || "").trim(); };
    var required = ["name","business","whatsapp","sells"];
    for (var i = 0; i < required.length; i++){
      var n = required[i];
      if (!get(n)){
        form.elements[n].focus();
        if (form.elements[n].reportValidity) form.elements[n].reportValidity();
        return;
      }
    }
    var msg = "\\u0645\\u0631\\u062d\\u0628\\u0627\\u064b \\u0646\\u0627\\u0647\\u062f \\u2014 " +
      "\\u0623\\u0631\\u064a\\u062f \\u0627\\u062e\\u062a\\u0628\\u0627\\u0631 " +
      "\\u0627\\u0644\\u0645\\u0634\\u062a\\u0631\\u064a \\u0627\\u0644\\u0635\\u0627\\u0645\\u062a " +
      "\\u0627\\u0644\\u0645\\u062c\\u0627\\u0646\\u064a.\\n\\n" +
      "\\u0627\\u0644\\u0627\\u0633\\u0645: " + get("name") + "\\n" +
      "\\u0627\\u0644\\u0646\\u0634\\u0627\\u0637: " + get("business") + "\\n" +
      "\\u0648\\u0627\\u062a\\u0633\\u0627\\u0628: " + get("whatsapp") + "\\n" +
      "\\u0646\\u0628\\u064a\\u0639: " + get("sells");
    if (typeof gtag === "function") gtag("event","generate_lead",{method:"silent_buyer_test_ar"});
    window.open("https://api.whatsapp.com/send?phone=96899245250&text=" + encodeURIComponent(msg), "_blank", "noopener");
  });
})();
"""

META = dict(
    slug="contact",
    title="تواصل معي | AI Profit Lab — تحدّث إلى من يبني النظام",
    desc=("واتساب أو بريد أو هاتف — كلها تصل إلى الشخص نفسه في مسقط. أو ابدأ باختبار المشتري الصامت "
          "المجاني وشاهد ما يراه المشتري حين يراسل نشاطك."),
    nav="/contact/",
    next=("عد إلى البداية", "لست مضطراً لتعلّم الذكاء الاصطناعي", "/ar/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"FAQPage",
  "inLanguage":"ar",
  "mainEntity":[
    {"@type":"Question","name":"كم التكلفة؟","acceptedAnswer":{"@type":"Answer","text":"الموقع الذكي بـ950 ريالاً عُمانياً دفعة واحدة بسعر الشريك المؤسِّس، و1,450 بالسعر القياسي. لوحة المتابعة تضيف 650، والطيار الآلي يضيف 900، والثلاثة معاً 2,200."}},
    {"@type":"Question","name":"هل هناك رسوم شهرية؟","acceptedAnswer":{"@type":"Answer","text":"لا شيء مطلوب لإبقاء النظام يعمل. السنة الأولى من الاستضافة والحماية والرعاية مشمولة في سعر البناء. مكتب النمو بـ75 ريالاً شهرياً اختياري وغير مطلوب أبداً."}},
    {"@type":"Question","name":"هل لديك عملاء يمكنني التحدث إليهم؟","acceptedAnswer":{"@type":"Answer","text":"ليس بعد. ولهذا يوجد ضمان بالاسم، ولهذا تجربتا لوحة المتابعة ووكيل المشتري مفتوحتان للنقر دون طلب أي بيانات."}},
    {"@type":"Question","name":"وماذا لو لم ينجح؟","acceptedAnswer":{"@type":"Answer","text":"وعد أول استفسار: إن لم يصلك استفسار حقيقي من مشترٍ خلال 30 يوماً من الإطلاق، يُعاد بناؤه مجاناً حتى يصلك. وإن لم يصلك بعدها، تسترد مالك."}},
    {"@type":"Question","name":"هل تعمل بالعربية؟","acceptedAnswer":{"@type":"Answer","text":"نعم. العربية والإنجليزية كلتاهما بالمستوى نفسه، والنص العربي يراجعه قارئ عربي قبل النشر."}},
    {"@type":"Question","name":"مع من أتعاقد فعلياً؟","acceptedAnswer":{"@type":"Answer","text":"مع شركة Lotus Gulf International، س.ت 1570092، الخوير الجنوبية، بوشر، مسقط. AI Profit Lab هي العلامة التجارية. الشركة غير مسجّلة في ضريبة القيمة المضافة، فالفواتير لا تحمل بند ضريبة."}}
  ]
}""",
)
