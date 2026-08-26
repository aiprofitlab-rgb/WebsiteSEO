#!/usr/bin/env python3
"""صفحة الطلب - the Arabic checkout.

The engine is `page_checkout.js("ar")`: the same quote() port, the same integer
baisa arithmetic, the same reference format, the same offline handover. Only
the string table differs, so the two checkouts cannot compute different totals.

Product names, blurbs and payment-structure labels come from tools/v4/pay.py
through `pay.t(entry, field, "ar")` - the same table the JSON config is built
from - so the markup and the script always name a thing the same way.

The option rows are re-authored here rather than imported because their English
twins hard-code the label text; everything about their markup and classes is
identical.
"""
import pay
import page_checkout
from kit import STAR, WA, WA_ICON, url
from page_checkout import BACK, CSS, DOC, LOCK, SHIELD  # noqa: F401 - design is shared

from ar_common import FOUNDING, PROMISE, TEST, num, wa

__all__ = ["CSS", "JS", "body", "META"]

JS = page_checkout.js("ar")

SVC = url("services", "ar")
CONTACT = url("contact", "ar")

M = pay.money_ar


def _addon(i):
    """A toggleable build item."""
    return f"""      <label class="opt" data-kind="item">
        <input type="checkbox" name="item" value="{i['id']}">
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{pay.t(i, 'name', 'ar')}</b><span class="opt-p">+{M(pay.price(i))}</span></span>
          <span class="opt-d">{pay.t(i, 'blurb', 'ar')}</span>
        </span>
      </label>"""


def _monthly(i):
    return f"""      <label class="opt" data-kind="item">
        <input type="checkbox" name="item" value="{i['id']}">
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{pay.t(i, 'name', 'ar')}</b><span class="opt-p">{M(pay.price(i))}/شهرياً</span></span>
          <span class="opt-d">{pay.t(i, 'blurb', 'ar')} <b>غير محتسب اليوم</b> &mdash; يبدأ في الشهر
            التالي لإطلاق موقعك، ويُفوتر شهرياً.</span>
        </span>
      </label>"""


def _plan_card(p):
    """A payment structure. The figure on the right is what is due TODAY for
    the default configuration; the script rewrites it as items are toggled."""
    q = pay.quote([pay.BASE_ID], p["id"])
    fig = "لا شيء اليوم" if p["due"] == "zero" else f"{M(q['due'])} اليوم"
    flag = f'<span class="flag">{pay.t(p, "badge", "ar")}</span>' if p.get("badge") else ""
    checked = " checked" if p.get("recommended") else ""
    return f"""      <label class="opt" data-kind="plan" data-plan="{p['id']}">
        <input type="radio" name="plan" value="{p['id']}"{checked}>
        <span class="tick" aria-hidden="true"></span>
        <span class="opt-b">
          <span class="opt-h"><b>{pay.t(p, 'label', 'ar')}{flag}</b><span class="opt-p" data-planfig="{p['id']}">{fig}</span></span>
          <span class="opt-d">{pay.t(p, 'blurb', 'ar')}</span>
        </span>
      </label>"""


def _default_summary():
    """The server-rendered summary: the default configuration, correct with
    JavaScript switched off. The script replaces the whole list on its first
    run, so this is the floor under a visitor, not the target."""
    q = pay.quote([pay.BASE_ID], "deposit")
    base = pay.item(pay.BASE_ID)
    return (f"""        <li><span class="nm">{pay.t(base, 'name', 'ar')}</span><span class="amt">{M(pay.price(base))}</span></li>\n"""
            f"""        <li class="later"><span class="nm">المتبقي بعد العربون<small>يُفوتر بعد تأكيد ملخّص طلبك</small></span><span class="amt">{M(q['balance'])}</span></li>""")


def body():
    cfg = pay.CONFIG_JSON("ar")
    base = pay.item(pay.BASE_ID)
    addons = [i for i in pay.CATALOG if i["kind"] == "build" and not i["required"]]
    monthlies = [i for i in pay.CATALOG if i["kind"] == "monthly"]
    q0 = pay.quote([pay.BASE_ID], "deposit")

    # The wording of the action changes entirely with the gateway switch, and
    # nothing about it is left to a CSS class - a disabled-looking button that
    # still says "pay now" is exactly the lie this page must not tell.
    if pay.PAY_LIVE:
        btn_label = f"ادفع {M(q0['due'])} بأمان"
        under = ("ستُكمل الدفع على صفحة ثواني الآمنة نفسها. بيانات بطاقتك تُدخَل هناك ولا تصل "
                 "إلى هذا الموقع إطلاقاً.")
    else:
        btn_label = "احجز موعدي"
        under = ("الدفع بالبطاقة قيد التفعيل. وحتى ذلك الحين يُؤكَّد طلبك على واتساب وتتبعه "
                 "الفاتورة &mdash; ولا يُحتسب شيء هنا.")

    envbar = ""
    if pay.PAY_LIVE and pay.THAWANI_ENV != "live":
        envbar = ('<div class="envbar">وضع اختباري &mdash; المدفوعات تعمل على بيئة ثواني التجريبية. '
                  'لا تتحرك أموال حقيقية.</div>')

    founding_note = (f"سعر {FOUNDING}، محجوز للمجموعة الأولى المحدودة."
                     if pay.FOUNDING_OPEN else "السعر القياسي.")

    return f"""<main id="main">
{envbar}
<header class="phero s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> الطلب &#183; {founding_note}</p>
    <h1 class="h1">ابنِه تماماً<br>بالشكل الذي تحتاجه.</h1>
    <p class="lede">اختر ما تريد بناءه، وحدّد كيف تريد الدفع، والإجمالي على اليسار يتحدّث معك خطوة بخطوة.
      ولن يظهر بند مخفي في النهاية &mdash; ما تراه هو الفاتورة.</p>
  </div>
</header>

<section class="s-cream grain" style="padding-top:0">
  <div class="wrap">
    <form id="coForm" class="co-grid" novalidate>

      <!-- ================================================= the order -->
      <div>

        <div class="step">
          <p class="step-h"><span class="sn">٠١</span></p>
          <h2 class="h3" style="margin:0 0 6px">ما الذي تبنيه</h2>
          <p class="hint">{pay.t(base, 'name', 'ar')} هو الأساس &mdash; والاثنان الآخران يُبنيان فوقه،
            ويمكن إضافتهما لاحقاً بالسعر نفسه الذي تراه الآن.</p>

          <div class="opts">
            <span class="opt locked" data-kind="locked">
              <span class="tick" aria-hidden="true"></span>
              <span class="opt-b">
                <span class="opt-h"><b>{pay.t(base, 'name', 'ar')}<span class="flag">مشمول</span></b><span class="opt-p">{M(pay.price(base))}</span></span>
                <span class="opt-d">{pay.t(base, 'blurb', 'ar')}</span>
              </span>
            </span>
{chr(10).join(_addon(i) for i in addons)}
          </div>

          <div class="bundle" id="bundleNote">
            <span class="star" aria-hidden="true">{STAR}</span>
            <span>الثلاثة معاً هي <b>{pay.t(pay.BUNDLE, 'name', 'ar')}</b>، وتُسعَّر كبناء واحد لا ثلاثة
              &mdash; أي <b>{M(pay.bundle_saving())} خصماً</b> عن مجموع الأجزاء، وهي محتسبة أصلاً في
              الإجمالي على اليسار.</span>
          </div>

          <p class="hint" style="margin:26px 0 12px">وشيء اختياري واحد <b>غير</b> محتسب اليوم:</p>
          <div class="opts">
{chr(10).join(_monthly(i) for i in monthlies)}
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">٠٢</span></p>
          <h2 class="h3" style="margin:0 0 6px">كيف تحب أن تدفع</h2>
          <p class="hint">البناء نفسه في كل صف. والفرق الوحيد هو متى يتحرك المال.</p>
          <div class="opts">
{chr(10).join(_plan_card(p) for p in pay.PLANS)}
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">٠٣</span></p>
          <h2 class="h3" style="margin:0 0 6px">لمن أبنيه</h2>
          <p class="hint">ما يكفي لإصدار الفاتورة وبدء العمل. ولا شيء هنا يُستخدم في التسويق.</p>

          <div class="flds">
            <div class="fld">
              <label for="f-name">اسمك</label>
              <input id="f-name" name="name" type="text" autocomplete="name" required placeholder="اسمك">
              <span class="err" data-for="name"></span>
            </div>
            <div class="fld">
              <label for="f-biz">اسم النشاط</label>
              <input id="f-biz" name="business" type="text" autocomplete="organization" required placeholder="الخليج لوتس للتجارة ش.م.م">
              <span class="err" data-for="business"></span>
            </div>
            <div class="fld">
              <label for="f-email">البريد الإلكتروني <span class="opt-tag">&mdash; يصلك الإيصال هنا</span></label>
              <input id="f-email" name="email" type="email" autocomplete="email" required placeholder="you@company.om" inputmode="email" dir="ltr">
              <span class="err" data-for="email"></span>
            </div>
            <div class="fld">
              <label for="f-wa">رقم واتساب</label>
              <input id="f-wa" name="whatsapp" type="tel" autocomplete="tel" required placeholder="+968 &hellip;" inputmode="tel" dir="ltr">
              <span class="err" data-for="whatsapp"></span>
            </div>
            <div class="fld">
              <label for="f-cr">رقم السجل التجاري <span class="opt-tag">&mdash; اختياري، للفاتورة</span></label>
              <input id="f-cr" name="cr" type="text" placeholder="1234567" inputmode="numeric" dir="ltr">
            </div>
            <div class="fld">
              <label for="f-city">المدينة</label>
              <input id="f-city" name="city" type="text" autocomplete="address-level2" placeholder="مسقط">
            </div>
            <div class="fld full">
              <label for="f-notes">أي شيء ينبغي أن أعرفه قبل مكالمة الملخّص <span class="opt-tag">&mdash; اختياري</span></label>
              <textarea id="f-notes" name="notes" placeholder="ماذا تبيع، وكيف يصل إليك المشترون اليوم، والشيء الواحد الذي يكلّفك مالاً."></textarea>
            </div>
          </div>
        </div>

        <div class="step">
          <p class="step-h"><span class="sn">٠٤</span></p>
          <h2 class="h3" style="margin:0 0 14px">أكّد وأرسل</h2>

          <label class="consent">
            <input type="checkbox" name="agree" id="f-agree" required>
            <span>قرأت <a href="/terms-ar/" target="_blank" rel="noopener">شروط الخدمة</a> و<a href="/refund-policy-ar/" target="_blank" rel="noopener">سياسة
              الاسترداد والإلغاء</a>، وأفهم ما هو مشمول في هذا البناء وما هو غير مشمول.</span>
          </label>

          <div class="act">
            <p class="formerr" id="formErr" role="alert"></p>
            <button class="btn btn-teal" type="submit" id="payBtn">{LOCK}<span id="payLabel">{btn_label}</span></button>
            <p class="undertext" id="payUnder">{under}</p>
          </div>

          <div class="offline" id="offlinePanel" role="status" aria-live="polite">
            <h3>طلبك جاهز للإرسال.</h3>
            <p id="offlineWhy">الدفع بالبطاقة قيد التفعيل، ولهذا تتم هذه الخطوة الأخيرة على واتساب:
              اضغط الزر ويصلني الطلب كاملاً في رسالة واحدة. أؤكّده، وأرسل الفاتورة وبيانات التحويل،
              ويُحجَز موعدك من تلك اللحظة.</p>
            <div class="refbox">
              <span>رقمك المرجعي</span>
              <b id="offlineRef">&mdash;</b>
            </div>
            <div class="btn-row">
              <a class="btn btn-wa" id="offlineWa" href="{WA}" target="_blank" rel="noopener">{WA_ICON}أرسل طلبي على واتساب</a>
              <a class="btn btn-ghost" id="offlineMail" href="mailto:hello@aiprofitlab.io">أرسله بالبريد بدلاً من ذلك</a>
            </div>
          </div>

          <noscript>
            <div class="offline on" style="margin-top:20px">
              <h3>الطلب دون جافاسكربت</h3>
              <p>تحسب هذه الصفحة طلبك داخل المتصفح، وهذا يحتاج جافاسكربت. راسل
                <a href="{WA}">+968 9924 5250</a> على واتساب أو أرسل بريداً إلى
                <a href="mailto:hello@aiprofitlab.io">hello@aiprofitlab.io</a> بما تريد بناءه
                وسأرسل لك الفاتورة برداً. والأسعار على اليسار هي الأسعار الحقيقية في الحالتين.</p>
            </div>
          </noscript>
        </div>

      </div>

      <!-- ============================================== the summary -->
      <div class="sum-wrap">
        <aside class="sum" aria-label="ملخّص الطلب">
          <!-- Deliberately NOT an <h2>: the shared motion script wraps the
               children of every `section h2` in one .wi span for its reveal
               wipe, which would glue the two halves of this flex row together. -->
          <p class="sum-t" role="heading" aria-level="2"><span>طلبك</span><span class="ref" id="refTag"></span></p>

          <ul class="sum-lines" id="sumLines">
{_default_summary()}
          </ul>

          <div class="sum-due">
            <span class="k" id="dueKey">المستحق اليوم</span>
            <b class="v" id="dueVal">{M(q0['due'])}</b>
          </div>
          <p class="sum-then" id="sumThen">المتبقي {M(q0['balance'])} يُفوتر بعد تأكيد ملخّص طلبك،
            والعربون الذي دفعته اليوم مخصوم منه أصلاً.</p>

          <p class="sum-note">
            <b>لا تُضاف ضريبة قيمة مضافة.</b> شركة Lotus Gulf International دون حدّ التسجيل في عُمان،
            فالمبلغ أعلاه هو المبلغ في الفاتورة.<br>
            يُحصَّل بالريال العُماني من <b>Lotus Gulf International</b>، س.ت <span dir="ltr">1570092</span>،
            وتتاجر باسم AI Profit Lab.
          </p>
        </aside>

        <ul class="trust">
          <li>{LOCK}<span>بيانات بطاقتك تُدخَل على صفحة مزوّد الدفع نفسه. ولا تُكتب في هذا الموقع
            ولا تُرسَل إليه ولا تُخزَّن فيه إطلاقاً.</span></li>
          <li>{BACK}<span>ألغِ قبل أن أبدأ البناء وتسترد كل شيء &mdash;
            <a href="/refund-policy-ar/">سياسة الاسترداد</a> تحدّد بالضبط متى وكم.</span></li>
          <li>{SHIELD}<span>{PROMISE}: إن لم يصلك استفسار حقيقي من مشترٍ خلال {num('30')} يوماً من
            الإطلاق أعيد بناءه مجاناً. وإن لم يصلك بعدها، تسترد مالك.</span></li>
          <li>{DOC}<span>فاتورة مفصّلة من شركة عُمانية مسجّلة، لا رابط دفع من مجهول.</span></li>
        </ul>
      </div>

    </form>
  </div>
</section>

<!-- ==================================================== WHAT HAPPENS NEXT -->
<section class="s-panel">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> بعد أن تضغط الزر</p>
    <h2 class="h2">أربعة أشياء تحدث، بهذا الترتيب.</h2>

    <div class="after" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div>
        <h3>يصلك إيصال</h3>
        <p>بالبريد خلال دقائق، ومعه رقمك المرجعي وفاتورة مفصّلة من Lotus Gulf International.</p>
      </div>
      <div>
        <h3>أتصل بك</h3>
        <p>خلال يوم عمل واحد، لأخذ الملخّص كما ينبغي. ولا يُبنى شيء من نموذج وحده.</p>
      </div>
      <div>
        <h3>تشاهده وهو يُبنى</h3>
        <p>رابط يعمل من الأسبوع الأول، يُحدَّث مع التقدّم. ولن تُعرض عليك نسخة نهائية لم ترها من قبل.</p>
      </div>
      <div>
        <h3>يُطلَق</h3>
        <p>ويبدأ عدّ الثلاثين يوماً لوعد أول استفسار من ذلك اليوم، لا من يوم الدفع.</p>
      </div>
    </div>
  </div>
</section>

<!-- ============================================================ QUESTIONS -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 400px">
        <h2 class="h2" style="margin-bottom:12px">لست مستعداً للدفع بعد؟</h2>
        <p class="lede" style="margin:0">هذا منطقي. ابدأ بالمجاني إذاً: أراسل نشاطك كما يفعل مشترٍ
          وأرسل لك التقرير. تحتفظ به في الحالتين، وبلا أي عرض بيع مرفق.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="{CONTACT}#test">اطلب {TEST}</a>
        <a class="btn btn-ghost" href="{SVC}#price">اطّلع على قائمة الأسعار كاملة</a>
      </div>
    </div>
  </div>
</section>

<div class="paybar" id="payBar" aria-hidden="true">
  <span><span class="pb-k" id="barKey">المستحق اليوم</span><span class="pb-v" id="barVal">{M(q0['due'])}</span></span>
  <button class="btn btn-teal" type="submit" form="coForm" id="barBtn">احجز</button>
</div>

<script type="application/json" id="payCfg">{cfg}</script>
</main>
"""


META = dict(
    slug="checkout",
    title="ابدأ طلبك | AI Profit Lab — كل رقم قبل أن تدفع",
    desc=("اختر ما تريد بناءه، وحدّد كيف تدفع، وشاهد الإجمالي يتحدّث معك. لا ضريبة قيمة مضافة، "
          "ولا بنود مخفية، وفاتورة مفصّلة من شركة عُمانية مسجّلة."),
    nav="/checkout-ar/",
    next=("التالي", "طريقة العمل", "/process/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"CheckoutPage",
  "inLanguage":"ar",
  "name":"ابدأ طلبك — AI Profit Lab",
  "url":"https://aiprofitlab.io/checkout-ar/"
}""",
)
