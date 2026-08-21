#!/usr/bin/env python3
"""حالة الطلب - the Arabic order-status page.

The return page a buyer lands on after the payment provider hands them back.
Same five states, same confirmation logic: `?status=success` is a claim made by
a URL, so a successful return still opens in "confirming" and is only upgraded
once the API says `payment_status === "paid"`. That honesty is the whole design
of the page and it is not restated per language - `page_order.js("ar")` is the
same script with one word translated.

noindex, like its English twin: it is a landing point, not a page to find.
"""
import pay
import page_order
from kit import STAR, WA_ICON, url
from page_order import CHECK, CLOCK, CROSS, CSS, _state  # noqa: F401

from ar_common import PROMISE, num, wa

__all__ = ["CSS", "JS", "body", "META"]

JS = page_order.js("ar")

CHK = url("checkout", "ar")


def body():
    cfg = pay.CONFIG_JSON("ar")

    # Python 3.11 cannot nest a triple-quoted f-string inside another one, so
    # the shared blocks are built first and passed in as plain strings.
    contact = f"""    <div class="btn-row" style="margin-top:clamp(26px,3.4vw,38px)">
      <a class="btn btn-wa" href="{wa('مرحباً ناهد، بخصوص طلبي ')}">{WA_ICON}اسألني عنه</a>
      <a class="btn btn-ghost" href="/ar/">عد إلى الموقع</a>
    </div>"""

    retry = f"""    <div class="btn-row" style="margin-top:clamp(26px,3.4vw,38px)">
      <a class="btn btn-amber" href="{CHK}?restore=1">أكمل من حيث توقفت</a>
      <a class="btn btn-ghost" href="{wa('مرحباً ناهد، واجهت مشكلة في الدفع على الموقع.')}">حدث خطأ ما &mdash; أخبرني</a>
    </div>"""

    ref_status = """    <div class="refcard">
      <div><span class="k">رقمك المرجعي</span><span class="v" data-ref>&mdash;</span></div>
      <div><span class="k">الحالة</span><span class="v" data-status>قيد التأكيد</span></div>
    </div>
""" + contact

    ref_paid = """    <div class="refcard">
      <div><span class="k">رقمك المرجعي</span><span class="v" data-ref>&mdash;</span></div>
      <div><span class="k">المدفوع</span><span class="v" data-paid>&mdash;</span></div>
    </div>
""" + contact

    states = "\n\n".join([
        _state("wait", "wait", CLOCK,
               "شكراً لك &mdash; أنا الآن أؤكّد دفعتك.",
               "وصل طلبك. أراجع كل دفعة بنفسي لدى مزوّد الخدمة قبل أن أعتبر أي شيء مؤكّداً، "
               "ولهذا يصلك الإيصال بالبريد بعد قليل &mdash; عادةً خلال دقائق، ودائماً خلال يوم عمل واحد.",
               ref_status),
        _state("paid", "good", CHECK,
               "استُلمت الدفعة. وموعدك محجوز.",
               "انتهى الجانب المالي. وكل ما بعده بيني وبينك: سأتواصل معك خلال يوم عمل واحد لأخذ "
               "ملخّص العمل كما ينبغي، ولا يُبنى شيء من نموذج وحده.",
               ref_paid),
        _state("cancel", "stop", CROSS,
               "لم يُحتسب شيء.",
               "خرجت من صفحة الدفع، وهذا حقّك تماماً &mdash; لم يتحرك أي مبلغ ولم يُنشأ أي طلب. "
               "وإعداداتك ما زالت محفوظة في هذا المتصفح، فيمكنك العودة إليها مباشرةً، أو أن تسألني "
               "السؤال الذي أوقفك.",
               retry),
        _state("fail", "stop", CROSS,
               "لم تكتمل تلك الدفعة.",
               "يخبرني مزوّد الخدمة أن الدفعة لم تكتمل، فلم يُحتسب شيء. وهذا عادةً بنك يرفض عملية "
               "إلكترونية لا خلل في البطاقة نفسها &mdash; ومكالمة معهم، أو بطاقة أخرى، تحلّ الأمر غالباً.",
               retry),
        _state("none", "wait", CLOCK,
               "تبحث عن طلب؟",
               "لا يوجد ما يُعرَض على هذه الصفحة ما لم تكن قد عدت للتوّ من عملية دفع. وإن كان لديك "
               "رقم مرجعي وتريد معرفة أين وصل، أرسله لي وسأخبرك بوضوح.",
               contact),
    ])

    return f"""<main id="main">

<header class="ost s-dark grain">
  <div class="wrap">

{states}

  </div>
</header>

<section class="s-cream grain pad-s">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> ماذا يحدث الآن</p>
    <h2 class="h2">الأشياء الأربعة التالية، بالترتيب.</h2>
    <ol class="nxt">
      <li><b>إيصالك وفاتورتك</b>بالبريد إلى العنوان المذكور في طلبك، مفصّلة، من
        Lotus Gulf International (س.ت <span dir="ltr">1570092</span>). بلا بند ضريبة قيمة مضافة،
        لأن الشركة دون حدّ التسجيل.</li>
      <li><b>مكالمة الملخّص</b>خلال يوم عمل واحد. نصف ساعة، هاتفياً أو على واتساب، عن عملك أنت
        لا عن المواقع.</li>
      <li><b>رابط في الأسبوع الأول</b>تشاهده وهو يُبنى. ولن تُسلَّم نسخة نهائية لم ترها ولم تعلّق عليها.</li>
      <li><b>الإطلاق، وبدء الوعد</b>{PROMISE} لمدة {num('30')} يوماً يبدأ عدّه من يوم الإطلاق،
        لا من يوم الدفع.</li>
    </ol>

    <p style="margin-top:clamp(26px,3.4vw,38px);color:var(--muted);font-size:.96rem">
      غيّرت رأيك؟ <a href="/refund-policy-ar/">سياسة الاسترداد والإلغاء</a> تحدّد بالضبط ما الذي يعود
      ومتى &mdash; وباختصار: كل شيء، حتى يوم بدء البناء.
    </p>
  </div>
</section>

<script type="application/json" id="payCfg">{cfg}</script>
</main>
"""


META = dict(
    noindex=True,
    slug="order",
    title="حالة طلبك | AI Profit Lab",
    desc="أين وصل طلبك لدى AI Profit Lab، وماذا يحدث بعد ذلك.",
    nav="/services/",
    next=("عد إلى البداية", "لست مضطراً لتعلّم الذكاء الاصطناعي", "/ar/"),
)
