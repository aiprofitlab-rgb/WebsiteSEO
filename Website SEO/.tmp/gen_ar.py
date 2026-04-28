#!/usr/bin/env python3
"""Generate Arabic version of Saudi SME article from English version."""
import re

en_path = "../public_html/blog/en/2026-04-28-ai-automation-saudi-sme-worth-it.html"
ar_path = "../public_html/blog/ar/2026-04-28-ai-automation-saudi-sme-worth-it.html"

with open(en_path, "r") as f:
    html = f.read()

# Map of English to Arabic replacements
replacements = [
    ('lang="en" dir="ltr"', 'lang="ar" dir="rtl"'),
    ('href="../../en.html"', 'href="../../ar.html"'),
    ('href="../../blog.html"', 'href="../../blog_ar.html"'),
    ('>Back to Hub</a>', '>العودة إلى المركز</a>'),
    ('border-left: 4px solid #3B82F6; padding-left: 1rem;', 'border-right: 4px solid #3B82F6; padding-right: 1rem;'),
    ('margin-left: 0;', 'margin-right: 0;'),
    ('text-align: left;', 'text-align: right;'),
    ('<meta name="category" content="Business ROI">', '<meta name="category" content="عائد الاستثمار">'),
    ('<title>AI Automation for Saudi SMEs: Is It Worth It? (Vision 2030 Guide) | AI Profit Lab</title>',
     '<title>أتمتة الذكاء الاصطناعي للشركات السعودية الصغيرة والمتوسطة: هل تستحق؟ (دليل رؤية 2030) | AI Profit Lab</title>'),
    ('<meta name="description" content="Is AI automation worth it for Saudi SMEs in 2026? Explore SAR pricing, Vision 2030 alignment, real ROI data, and a step-by-step guide for Saudi business owners.">',
     '<meta name="description" content="هل أتمتة الذكاء الاصطناعي تستحق للشركات السعودية الصغيرة والمتوسطة في 2026؟ اكتشف أسعار الريال، توافق رؤية 2030، وبيانات العائد الحقيقية.">'),
    ('href="https://aiprofitlab.io/blog/en/2026-04-28-ai-automation-saudi-sme-worth-it.html"',
     'href="https://aiprofitlab.io/blog/ar/2026-04-28-ai-automation-saudi-sme-worth-it.html"'),
    ('>Business ROI</span>', '>عائد الاستثمار</span>'),
    ('>AI Automation for Saudi SMEs: Is It Worth It?</h1>',
     '>أتمتة الذكاء الاصطناعي للشركات السعودية الصغيرة والمتوسطة: هل تستحق؟</h1>'),
    (">Vision 2030 is reshaping the Kingdom's economy. Here's the honest answer on whether AI automation delivers real returns for Saudi small and medium businesses.</p>",
     ">رؤية 2030 تعيد تشكيل اقتصاد المملكة. إليك الإجابة الصريحة حول ما إذا كانت أتمتة الذكاء الاصطناعي تحقق عوائد حقيقية للشركات السعودية الصغيرة والمتوسطة.</p>"),
    (">Frequently Asked Questions</h2>", ">الأسئلة الشائعة</h2>"),
    (">References</h3>", ">المراجع</h3>"),
]

# Body content translations
body_replacements = [
    ("Picture this: Khalid runs a mid-sized trading company in Riyadh's Al Olaya district.",
     "تخيل هذا: خالد يدير شركة تجارية متوسطة في حي العليا بالرياض."),
    ("His sales team fields 80 WhatsApp inquiries per day. Half get answered within the hour. The other half? Gone by morning.",
     "فريق مبيعاته يتلقى 80 استفساراً عبر واتساب يومياً. نصفها يتم الرد عليه خلال ساعة. والنصف الآخر؟ يضيع بحلول الصباح."),
    ("His operations manager spends three hours daily copy-pasting order data between a spreadsheet and their supplier portal.",
     "مدير العمليات يقضي ثلاث ساعات يومياً في نسخ ولصق بيانات الطلبات بين جداول البيانات وبوابة الموردين."),
    ("And every month, Khalid pays a SAR 9,000 salary to an admin who does little beyond data entry and scheduling.",
     "وكل شهر يدفع خالد 9,000 ريال راتباً لموظف إداري لا يفعل أكثر من إدخال البيانات وجدولة المواعيد."),
    ("Khalid knows about AI. He has read the headlines about Vision 2030 and Saudi Arabia's ambition to become a global AI hub.",
     "خالد يعرف عن الذكاء الاصطناعي. قرأ العناوين عن رؤية 2030 وطموح المملكة لتصبح مركزاً عالمياً للذكاء الاصطناعي."),
    ("But every time he reaches out to a technology firm, the proposals come back in the hundreds of thousands of riyals, and he walks away unconvinced.",
     "لكن في كل مرة يتواصل مع شركة تقنية، تعود العروض بمئات آلاف الريالات، فينصرف غير مقتنع."),
    ("Is AI automation genuinely worth it for a Saudi SME — or is it a tool only for Aramco and the megacorporations?",
     "هل أتمتة الذكاء الاصطناعي تستحق فعلاً للشركات السعودية الصغيرة — أم أنها أداة لأرامكو والشركات العملاقة فقط؟"),
    ('The short answer: <strong>it is absolutely worth it</strong> — but only if you approach it correctly. This guide gives Saudi SME owners the unfiltered, data-backed answer.',
     'الإجابة المختصرة: <strong>تستحق بالتأكيد</strong> — لكن فقط إذا تعاملت معها بالطريقة الصحيحة. هذا الدليل يقدم لأصحاب الشركات السعودية إجابة صريحة مدعومة بالبيانات.'),
    ("How does Saudi Vision 2030 make AI automation a strategic priority for SMEs?",
     "كيف تجعل رؤية 2030 أتمتة الذكاء الاصطناعي أولوية استراتيجية للشركات الصغيرة والمتوسطة؟"),
    ("What does AI automation actually cost for a Saudi SME in 2026?",
     "كم تبلغ تكلفة أتمتة الذكاء الاصطناعي فعلياً لشركة سعودية صغيرة في 2026؟"),
    ("Which Saudi industries are seeing the fastest AI ROI?",
     "ما هي القطاعات السعودية التي تحقق أسرع عائد على الاستثمار من الذكاء الاصطناعي؟"),
    ("What are the hidden costs Saudi SMEs must budget for?",
     "ما هي التكاليف الخفية التي يجب على الشركات السعودية وضعها في الميزانية؟"),
    ("How should a Saudi SME start with AI automation in 2026?",
     "كيف يجب أن تبدأ الشركة السعودية الصغيرة بأتمتة الذكاء الاصطناعي في 2026؟"),
    ("So — is AI automation worth it for Saudi SMEs?",
     "إذاً — هل تستحق أتمتة الذكاء الاصطناعي للشركات السعودية الصغيرة والمتوسطة؟"),
]

for old, new in replacements:
    html = html.replace(old, new)

for old, new in body_replacements:
    html = html.replace(old, new)

with open(ar_path, "w") as f:
    f.write(html)

print(f"Arabic article saved to {ar_path}")
