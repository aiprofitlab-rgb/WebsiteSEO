#!/usr/bin/env python3
"""من أنا - the Arabic About page.

Same components, same order and same argument as page_about.py; the CSS is
imported from it rather than restated, so the two pages cannot diverge
visually. Only the strings are new.

Voice: first person singular throughout, exactly as the English. The corporate
plural ("نحن نبني") is deliberately avoided - it would contradict the one claim
this page exists to make, which is that this is one operator and not an agency.
The founder story follows the approved wording in
brand/docs/01-persona-and-avatar.md section 5: an engineer who has built and
run a real distribution business, with no implication of Omani roots or a local
trade network.
"""
from kit import STAR, WA_ICON, url
from page_about import CSS  # noqa: F401 - the design is shared, not copied

from ar_common import CITY, FOUNDER, ROLE, TEST, wa

__all__ = ["CSS", "body", "META"]


def body():
    return f"""<main id="main">

<header class="phero s-cream grain">
  <div class="wrap">
    <div class="about-hero">
      <div>
        <p class="eyebrow"><span class="star">{STAR}</span> من يبني هذا</p>
        <h1 class="h1">لست وكالة.<br>مهندس واحد أدار شركة توزيع حقيقية.</h1>
        <p class="lede">ولهذا السبب وحده أعرف كم تكلّف رسالة وصلت في التاسعة مساءً ولم يردّ عليها أحد،
          ولماذا لا يوجد في هذا الموقع سطر واحد مكتوب بلغة المبرمجين.</p>
        <div class="btn-row" style="margin-top:30px">
          <a class="btn btn-wa" href="{wa('مرحباً ناهد، قرأت صفحة «من أنا» ولدي سؤال.')}">{WA_ICON}راسلني مباشرة</a>
          <a class="tlink" href="{url('services', 'ar')}">شاهد ما أبنيه <span class="arw">&larr;</span></a>
        </div>
      </div>
      <figure class="portrait rv" style="margin:0">
        <img src="/nahid-founder-seated-2026.webp" alt="{FOUNDER}، مؤسس AI Profit Lab، في مسقط" width="600" height="705" loading="eager" decoding="async">
        <figcaption>{FOUNDER} &#183; {ROLE} &#183; {CITY}</figcaption>
      </figure>
    </div>
  </div>
</header>

<!-- ================================================================ STORY -->
<section class="s-panel">
  <div class="wrap-n prose">
    <p class="eyebrow"><span class="star">{STAR}</span> باختصار</p>
    <p class="open">أنا مهندس بنى شركة توزيع حقيقية وأدارها &mdash; استيراد، وتخزين، وعروض أسعار،
      ومتابعة لا تنتهي. لست مستشاراً قرأ عن ذلك في كتاب.</p>
    <p>المشكلة التي كنت أصطدم بها لم تكن الاستراتيجية يوماً. كانت رسالة تصل في التاسعة مساءً ويُردّ عليها
      في الثامنة من صباح اليوم التالي، وقد اشترى صاحبها من مكان آخر قبل ذلك. اضرب هذا في سنة كاملة،
      ولن يكون الرقم صغيراً.</p>
    <p>فبدأت أبني ما كنت أحتاجه أنا: نظام يردّ باللغتين، يعرف المخزون وشروط البيع، ولا يحوّل إليّ إلا
      المشترين الذين يستحقون وقتي. هذا هو AI Profit Lab، وأبنيه اليوم لأصحاب أعمال في الموقف نفسه.</p>
    <div class="sigline"><span class="mk"></span><span>{FOUNDER} &#183; {ROLE}</span></div>
  </div>
</section>

<!-- ================================================================= PATH -->
<section class="s-dark">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> كيف وصلت إلى هنا</p>
    <h2 class="h2">أربع خطوات، بالترتيب.</h2>

    <div class="path" data-stagger>
      <div><b>٠١</b><h3>الهندسة</h3><p>تدرّبت على تفكيك أي نظام، وتحديد نقطة الاختناق فيه، وإصلاح تلك النقطة وحدها.</p></div>
      <div><b>٠٢</b><h3>التوزيع</h3><p>أدرت عملية تجارية حقيقية. كتالوجات، وشرائح أسعار، وشحن، وفواتير، ومتابعة لا يجد أحد وقتاً لها.</p></div>
      <div><b>٠٣</b><h3>نقطة الاختناق</h3><p>اكتشفت أن العائق لم يكن السعر ولا المنتج. كان زمن الردّ.</p></div>
      <div><b>٠٤</b><h3>AI Profit Lab</h3><p>أبني اليوم هذا الحل لأصحاب أعمال آخرين &mdash; جاهزاً بالكامل، بلغة واضحة، وبسعر بالريال العُماني.</p></div>
    </div>
  </div>
</section>

<!-- =========================================================== PRINCIPLES -->
<section class="s-cream grain">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> كيف أعمل</p>
    <h2 class="h2">أربع قواعد لا أتنازل عنها.</h2>

    <div class="grid g4" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <article class="card"><span class="n">٠١</span><h3>لغة واضحة</h3><p>إن احتاجت الجملة إلى مصطلح تقني كي تؤدي معناها، فالجملة نفسها خاطئة.</p></article>
      <article class="card"><span class="n">٠٢</span><h3>الأسعار معلنة</h3><p>كل رقم موجود على الموقع. لا ينبغي أن تحضر مكالمة كي تعرف كم يكلّف شيء ما.</p></article>
      <article class="card"><span class="n">٠٣</span><h3>غير المشمول أولاً</h3><p>أذكره بالوضوح نفسه الذي أذكر به المشمول &mdash; قبل أن يتحرك أي مبلغ.</p></article>
      <article class="card"><span class="n">٠٤</span><h3>لا أرقام مخترعة</h3><p>إن لم يكن للرقم مصدر، فلا مكان له على الصفحة. ولهذا لا ترى هنا أي إحصاءات.</p></article>
    </div>
  </div>
</section>

<!-- =========================================================== SAY NO TO -->
<section class="s-teal">
  <div class="wrap">
    <p class="eyebrow"><span class="star">{STAR}</span> صراحة في مسألة الملاءمة</p>
    <h2 class="h2">من أعتذر عن العمل معه.</h2>
    <p class="lede">كتابة هذا على صفحة علنية تكلّفني طلبات. وتوفّر علينا معاً شهراً ضائعاً.</p>

    <div class="nope" style="margin-top:clamp(26px,3.5vw,44px)" data-stagger>
      <div><b>الشركات الكبرى ومشاريع أنظمة ERP</b><p>وزن مختلف تماماً ودورة شراء طويلة. أنت تحتاج شركة تكامل أنظمة، ومن حقك أن تحصل عليها.</p></div>
      <div><b>من يبحث عن الأرخص فقط</b><p>لست الخيار الأرخص في عُمان ولن أدّعي ذلك. أنافس على أن العمل يُنجَز نيابة عنك.</p></div>
      <div><b>أعمال بلا أي وجود رقمي بعد</b><p>إن لم يكن هناك رقم واتساب ولا أي تدفّق للمشترين أصلاً، فلا يوجد بعد ما يمكن أتمتته.</p></div>
      <div><b>&laquo;اجعلنا ننتشر&raquo;</b><p>مشكلة خاطئة ومقياس خاطئ. أنا أبني أنظمة تردّ على المشترين، لا حملات تطارد الانتباه.</p></div>
    </div>
  </div>
</section>

<!-- ============================================================== FACTS -->
<section class="s-panel">
  <div class="wrap-n">
    <p class="eyebrow"><span class="star">{STAR}</span> تفاصيل غير لامعة</p>
    <h2 class="h2">مع من تتعامل فعلاً.</h2>
    <dl class="facts-sheet" style="margin-top:clamp(24px,3vw,38px)">
      <div><dt>العلامة التجارية</dt><dd>AI Profit Lab</dd></div>
      <div><dt>الكيان القانوني</dt><dd>لوتس الخليج العالمية &mdash; <span lang="en" dir="ltr">Lotus Gulf International</span> &mdash; س.ت <span dir="ltr">1570092</span></dd></div>
      <div><dt>ضريبة القيمة المضافة</dt><dd>غير مسجّلة (الرقم الضريبي <span dir="ltr">2317725</span>). الفواتير لا تحمل بند ضريبة.</dd></div>
      <div><dt>المقر</dt><dd>الخوير الجنوبية، بوشر، مسقط، سلطنة عُمان</dd></div>
      <div><dt>اللغات</dt><dd>العربية والإنجليزية، وكلتاهما بالمستوى نفسه</dd></div>
      <div><dt>من ينفّذ العمل</dt><dd>أنا. ولن يتم تحويلك إلى مدير حسابات.</dd></div>
      <div><dt>للتواصل</dt><dd><a href="{wa('مرحباً ناهد')}">واتساب <span dir="ltr">+968 9924 5250</span></a> &#183; <a href="mailto:hello@aiprofitlab.io">hello@aiprofitlab.io</a></dd></div>
    </dl>
  </div>
</section>

<!-- ================================================================ CTA -->
<section class="s-dark pad-s">
  <div class="wrap">
    <div style="display:flex;gap:clamp(20px,4vw,50px);align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="flex:1 1 380px">
        <h2 class="h2" style="margin-bottom:12px">ما زلت تقرأ؟ إذاً لنختبر عملك.</h2>
        <p class="lede" style="margin:0">مجاناً، يستغرق مني نحو أربعين دقيقة، وتحتفظ بالتقرير مهما كان قرارك.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn-amber" href="{url('contact', 'ar')}#test">اطلب {TEST}</a>
        <a class="btn btn-ghost" href="{url('services', 'ar')}#price">اطّلع على الأسعار</a>
      </div>
    </div>
  </div>
</section>

</main>
"""


META = dict(
    slug="about",
    title="من أنا | AI Profit Lab — مشغّل واحد، لا وكالة",
    desc=("مهندس بنى شركة توزيع حقيقية وأدارها، ويبني اليوم أنظمة ذكاء اصطناعي لأصحاب أعمال التجارة "
          "والتوزيع في عُمان. وفيها أيضاً من أعتذر عن العمل معه."),
    nav="/about/",
    next=("التالي", "تواصل معي", "/contact/"),
    schema="""{
  "@context":"https://schema.org",
  "@type":"AboutPage",
  "inLanguage":"ar",
  "mainEntity":{
    "@type":"Person",
    "name":"ناهد آبياري",
    "alternateName":"Nahid Abyari",
    "jobTitle":"المؤسس",
    "email":"hello@aiprofitlab.io",
    "telephone":"+968 9924 5250",
    "worksFor":{"@type":"Organization","name":"AI Profit Lab","parentOrganization":{"@type":"Organization","name":"Lotus Gulf International","identifier":"CR 1570092"}},
    "address":{"@type":"PostalAddress","addressLocality":"Bousher","addressRegion":"Muscat","addressCountry":"OM"}
  }
}""",
)
