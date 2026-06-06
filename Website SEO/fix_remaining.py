import os
import re
import json
from bs4 import BeautifulSoup
import random

base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog"
en_dir = os.path.join(base_dir, "en")
ar_dir = os.path.join(base_dir, "ar")

files_to_fix = []
for d in [en_dir, ar_dir]:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".html") and f != "index.html":
                files_to_fix.append(os.path.join(d, f))

en_faq_pool = [
    {"q": "How much does it cost to implement AI in an Omani business?", "a": "Costs vary depending on the scope. A simple workflow automation might cost a few hundred Omani Rials, while a full enterprise AI infrastructure can require a larger investment."},
    {"q": "Is my company's data safe when using AI?", "a": "Yes, provided you use enterprise-grade AI models with strict data privacy agreements or deploy on-premise solutions that comply with Oman's data protection laws."},
    {"q": "Do I need a technical background to use AI automation?", "a": "No, modern AI automation platforms and custom dashboards are built for non-technical managers, with intuitive interfaces and clear ROI tracking."},
    {"q": "How long does it take to see ROI from AI implementation?", "a": "Many businesses in the GCC report seeing a positive Return on Investment within 3 to 6 months of deploying targeted AI workflow automations."},
    {"q": "Can AI replace my human employees?", "a": "AI is designed to augment human workers, not replace them. It handles repetitive administrative tasks, allowing your team to focus on high-value strategy and customer relations."},
    {"q": "Will AI tools support the Arabic language perfectly?", "a": "Recent advancements in LLMs have significantly improved Arabic comprehension, including Khaleeji dialects, making them highly effective for the Omani market."},
    {"q": "What is the first step to integrating AI into my business?", "a": "The first step is a thorough operational audit to identify repetitive bottlenecks and data silos that can be easily automated for quick wins."},
    {"q": "Does AI automation align with Oman Vision 2040?", "a": "Absolutely. AI and digital transformation are key pillars of Oman Vision 2040, aimed at diversifying the economy and increasing operational efficiency."},
    {"q": "Can AI integrate with my existing ERP or CRM?", "a": "Yes, via APIs and webhooks, AI tools can seamlessly integrate with legacy systems like SAP, Oracle, Zoho, and Salesforce."},
    {"q": "What if the AI makes a mistake with a customer?", "a": "Proper AI implementations use deterministic guardrails and RAG (Retrieval-Augmented Generation) to prevent hallucinations, often keeping a human-in-the-loop for sensitive interactions."},
    {"q": "How does AI handle customer support outside of business hours?", "a": "AI chatbots and voice agents provide 24/7 instant responses, capturing leads and resolving common issues even when your physical office is closed."},
    {"q": "Can AI help with marketing and lead generation?", "a": "Yes, AI can analyze market trends, generate personalized ad copy, and automatically score incoming leads based on their likelihood to convert."},
    {"q": "How do we train our staff to use new AI systems?", "a": "A reputable AI agency provides comprehensive onboarding, standard operating procedures, and ongoing support to ensure smooth user adoption."},
    {"q": "Are there local AI agencies in Muscat?", "a": "Yes, local agencies like AI Profit Lab specialize in bringing global AI automation standards to Omani businesses with localized context."},
    {"q": "Can small SMEs afford AI technology?", "a": "Yes, the rise of no-code and low-code platforms has democratized AI, making it highly affordable for SMEs compared to hiring full-time developers."},
    {"q": "How does AI improve supply chain management?", "a": "AI predicts demand fluctuations, optimizes delivery routes in real-time, and automates inventory reordering, significantly reducing logistical costs."},
    {"q": "What is Retrieval-Augmented Generation (RAG)?", "a": "RAG is a technique where an AI model securely searches your private company documents before answering a question, ensuring accuracy and context."},
    {"q": "Is cloud-based AI legal for government contractors in Oman?", "a": "Government contractors must adhere to MTCIT guidelines, which often require data sovereignty and hosting sensitive data on local Omani servers."},
    {"q": "How does AI impact local hiring?", "a": "By automating mundane tasks, businesses can hire higher-skilled workers for strategic roles, elevating the overall capability of the local workforce."},
    {"q": "What is a realistic timeline for an AI project?", "a": "A focused automation project can be designed and deployed in 4-8 weeks. Larger enterprise integrations typically take 3-6 months including testing and staff training."},
]

ar_faq_pool = [
    {"q": "كم تكلفة تطبيق الذكاء الاصطناعي في شركة عمانية؟", "a": "تختلف التكاليف حسب النطاق. قد تكلف أتمتة سير العمل البسيطة بضع مئات من الريالات العمانية، بينما تتطلب البنية التحتية الكاملة للذكاء الاصطناعي استثماراً أكبر."},
    {"q": "هل بيانات شركتي آمنة عند استخدام الذكاء الاصطناعي؟", "a": "نعم، شريطة استخدام نماذج مؤسسية مع اتفاقيات صارمة لخصوصية البيانات أو نشر حلول محلية تتوافق مع قوانين حماية البيانات في عُمان."},
    {"q": "هل أحتاج إلى خلفية تقنية لاستخدام أتمتة الذكاء الاصطناعي؟", "a": "لا، تم تصميم منصات الأتمتة الحديثة ولوحات التحكم للمديرين غير التقنيين، مع واجهات بديهية وتتبع واضح لعائد الاستثمار."},
    {"q": "كم من الوقت يستغرق رؤية عائد الاستثمار من الذكاء الاصطناعي؟", "a": "تبلغ العديد من الشركات في دول مجلس التعاون الخليجي عن رؤية عائد استثمار إيجابي في غضون 3 إلى 6 أشهر من نشر أتمتة سير العمل."},
    {"q": "هل يمكن للذكاء الاصطناعي أن يحل محل الموظفين البشريين؟", "a": "صُمم الذكاء الاصطناعي لتعزيز قدرات العمال البشريين وليس استبدالهم. فهو يتولى المهام الإدارية المتكررة، مما يتيح لفريقك التركيز على الاستراتيجية وعلاقات العملاء."},
    {"q": "هل ستدعم أدوات الذكاء الاصطناعي اللغة العربية بشكل مثالي؟", "a": "أدت التطورات الأخيرة في النماذج اللغوية الكبيرة إلى تحسين الفهم العربي بشكل كبير، بما في ذلك اللهجات الخليجية، مما يجعلها فعالة للغاية للسوق العماني."},
    {"q": "ما هي الخطوة الأولى لدمج الذكاء الاصطناعي في عملي؟", "a": "الخطوة الأولى هي إجراء تدقيق تشغيلي شامل لتحديد الاختناقات المتكررة وصوامع البيانات التي يمكن أتمتتها بسهولة لتحقيق مكاسب سريعة."},
    {"q": "هل تتماشى أتمتة الذكاء الاصطناعي مع رؤية عمان 2040؟", "a": "بالتأكيد. يعد الذكاء الاصطناعي والتحول الرقمي من الركائز الأساسية لرؤية عمان 2040، بهدف تنويع الاقتصاد وزيادة الكفاءة التشغيلية."},
    {"q": "هل يمكن دمج الذكاء الاصطناعي مع نظام ERP أو CRM الحالي لدي؟", "a": "نعم، عبر واجهات برمجة التطبيقات وخطاطيف الويب، يمكن لأدوات الذكاء الاصطناعي التكامل بسلاسة مع الأنظمة القديمة مثل SAP و Oracle و Zoho و Salesforce."},
    {"q": "ماذا لو ارتكب الذكاء الاصطناعي خطأ مع عميل؟", "a": "تستخدم تطبيقات الذكاء الاصطناعي السليمة حواجز حتمية لمنع الهلوسة، وغالباً ما تبقي على الإشراف البشري للتفاعلات الحساسة."},
    {"q": "كيف يتعامل الذكاء الاصطناعي مع دعم العملاء خارج ساعات العمل؟", "a": "توفر روبوتات الدردشة استجابات فورية على مدار الساعة، مما يجذب العملاء المحتملين ويحل المشكلات الشائعة حتى عندما يكون مكتبك مغلقاً."},
    {"q": "هل يمكن للذكاء الاصطناعي المساعدة في التسويق وتوليد العملاء المحتملين؟", "a": "نعم، يمكن للذكاء الاصطناعي تحليل اتجاهات السوق، وإنشاء نصوص إعلانية مخصصة، وتسجيل العملاء المحتملين الواردين تلقائياً."},
    {"q": "كيف ندرب موظفينا على استخدام أنظمة الذكاء الاصطناعي الجديدة؟", "a": "توفر وكالة الذكاء الاصطناعي ذات السمعة الطيبة تدريباً شاملاً وإجراءات تشغيل قياسية ودعماً مستمراً لضمان تبني المستخدم بسلاسة."},
    {"q": "هل هناك وكالات ذكاء اصطناعي محلية في مسقط؟", "a": "نعم، تتخصص الوكالات المحلية مثل AI Profit Lab في جلب معايير أتمتة الذكاء الاصطناعي العالمية إلى الشركات العمانية بسياق محلي."},
    {"q": "هل تستطيع الشركات الصغيرة والمتوسطة تحمل تكاليف تكنولوجيا الذكاء الاصطناعي؟", "a": "نعم، أدى ظهور منصات البرمجة بدون كود إلى إضفاء الطابع الديمقراطي على الذكاء الاصطناعي، مما جعله في متناول الشركات الصغيرة والمتوسطة."},
    {"q": "كيف يحسن الذكاء الاصطناعي إدارة سلسلة التوريد؟", "a": "يتنبأ الذكاء الاصطناعي بتقلبات الطلب، ويحسن طرق التسليم في الوقت الفعلي، ويؤتمت إعادة طلب المخزون، مما يقلل بشكل كبير من التكاليف اللوجستية."},
    {"q": "ما هو التوليد المعزز بالاسترجاع (RAG)؟", "a": "تقنية يبحث فيها نموذج الذكاء الاصطناعي بأمان في مستندات شركتك الخاصة قبل الإجابة على سؤال، مما يضمن الدقة والسياق."},
    {"q": "هل الذكاء الاصطناعي السحابي قانوني للمقاولين الحكوميين في عُمان؟", "a": "يجب على المقاولين الحكوميين الالتزام بإرشادات وزارة النقل والاتصالات، والتي غالباً ما تتطلب سيادة البيانات واستضافتها على خوادم عمانية محلية."},
    {"q": "كيف يؤثر الذكاء الاصطناعي على التوظيف المحلي؟", "a": "من خلال أتمتة المهام العادية، يمكن للشركات توظيف عمال ذوي مهارات أعلى لأدوار استراتيجية، مما يرفع من القدرة الإجمالية للقوى العاملة المحلية."},
    {"q": "ما هو الجدول الزمني الواقعي لمشروع الذكاء الاصطناعي؟", "a": "يمكن تصميم مشروع الأتمتة المركّز ونشره في غضون 4-8 أسابيع. تستغرق التكاملات المؤسسية الأكبر عادةً 3-6 أشهر شاملةً الاختبار وتدريب الموظفين."},
]

fixed_count = 0

for path in sorted(files_to_fix):
    lang = "ar" if "/ar/" in path else "en"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    # 1. Fix malformed Vertex AI redirect links that were mis-replaced
    # Pattern: aiprofitlab.io/blog/.cloud.google.com/grounding-api-redirect/...
    content = re.sub(
        r'https://aiprofitlab\.io/blog/\.cloud\.google\.com/grounding-api-redirect/[A-Za-z0-9_\-=]+',
        'https://aiprofitlab.io/blog/',
        content
    )
    # Also catch any raw vertexaisearch links still lurking
    content = re.sub(
        r'https://vertexaisearch\.cloud\.google\.com/grounding-api-redirect/[A-Za-z0-9_\-=]+',
        'https://aiprofitlab.io/blog/',
        content
    )

    # 2. Fix remaining broken MTCIT link variant
    content = content.replace(
        'https://www.mtcit.gov.om/ITPortal/Pages/Page.aspx?NID=100&PID=300',
        'https://www.mtcit.gov.om/'
    )

    # 3. Fix NVIDIA broken link
    content = content.replace(
        'https://www.nvidia.com/en-us/glossary/sovereign-ai/',
        'https://www.nvidia.com/en-us/ai/'
    )

    # 4. Fix footer — use plain text encoding to be robust
    en_footer_plain = '© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved'
    ar_footer_plain = '© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة'
    en_footer_html = '<footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">\n        <p>© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved</p>\n    </footer>'
    ar_footer_html = '<footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">\n        <p>© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة</p>\n    </footer>'

    # Replace any existing footer regardless of content
    footer_regex = r'<footer[^>]*>.*?</footer>'
    correct_footer = ar_footer_html if lang == "ar" else en_footer_html
    if re.search(footer_regex, content, re.DOTALL):
        content = re.sub(footer_regex, correct_footer, content, flags=re.DOTALL)
    else:
        content = content.replace("</body>", correct_footer + "\n</body>")

    # 5. Fix HTML lang/dir
    if lang == "ar":
        content = re.sub(r'<html[^>]*>', '<html lang="ar" dir="rtl">', content)
    else:
        content = re.sub(r'<html[^>]*>', '<html lang="en" dir="ltr">', content)

    # 6. Fix missing FAQ section (HTML) for files that still don't have one
    if 'id="faq"' not in content:
        pool = ar_faq_pool if lang == "ar" else en_faq_pool
        random.seed(os.path.basename(path))  # deterministic shuffle per file
        shuffled = pool[:]
        random.shuffle(shuffled)
        faqs_to_add = shuffled[:10]

        faq_title = "الأسئلة الشائعة" if lang == "ar" else "Frequently Asked Questions"
        faq_html = f'\n\n            <!-- FAQ Section -->\n            <section class="mt-16 pt-8 border-t border-white/10" id="faq">\n                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">{faq_title}</h2>\n                <div class="space-y-6">'
        for item in faqs_to_add:
            faq_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{item["a"]}</p>\n                    </div>'
        faq_html += '\n                </div>\n            </section>'

        if "<!-- References -->" in content:
            content = content.replace("<!-- References -->", faq_html + "\n\n            <!-- References -->")
        else:
            article_end = content.find("</article>")
            if article_end != -1:
                content = content[:article_end] + faq_html + "\n        " + content[article_end:]
            else:
                main_end = content.rfind("</main>")
                if main_end != -1:
                    content = content[:main_end] + faq_html + "\n        " + content[main_end:]

        # Also inject FAQPage JSON-LD if missing
        if "FAQPage" not in content:
            faq_json_nodes = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs_to_add]
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1).replace(" | AI Profit Lab", "").strip() if title_match else ""
            desc_match = re.search(r'<meta name="description" content="(.*?)"', content)
            desc = desc_match.group(1) if desc_match else ""
            slug = os.path.basename(path).replace(".html", "")
            date_pub = slug[:10] if re.match(r'\d{4}-\d{2}-\d{2}', slug) else "2025-01-01"

            schema_graph = {
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "Organization", "@id": "https://aiprofitlab.io/#organization", "name": "AI Profit Lab", "legalName": "International Gulf Lotus SPC", "url": "https://aiprofitlab.io/", "logo": {"@type": "ImageObject", "url": "https://aiprofitlab.io/favicon.svg"}},
                    {"@type": "Article", "headline": title, "description": desc, "author": {"@type": "Organization", "name": "AI Profit Lab"}, "publisher": {"@id": "https://aiprofitlab.io/#organization"}, "datePublished": date_pub},
                    {"@type": "FAQPage", "mainEntity": faq_json_nodes}
                ]
            }
            schema_str = json.dumps(schema_graph, indent=4, ensure_ascii=False)
            schema_tag = f'<script type="application/ld+json">\n{schema_str}\n</script>'
            content = content.replace("</head>", schema_tag + "\n</head>")

    # 7. Pad FAQs in HTML that have section but < 10 <h3> items
    else:
        soup = BeautifulSoup(content, "html.parser")
        faq_sec = soup.find("section", id="faq")
        if faq_sec:
            h3_count = len(faq_sec.find_all("h3"))
            if h3_count < 10:
                pool = ar_faq_pool if lang == "ar" else en_faq_pool
                random.seed(os.path.basename(path) + str(h3_count))
                shuffled = pool[:]
                random.shuffle(shuffled)
                faqs_to_add = shuffled[:(10 - h3_count)]

                # Find the closing div of the faq section's inner div to insert before
                faq_pos = content.find('id="faq"')
                section_end = content.find("</section>", faq_pos)
                inner_div_close = content.rfind("</div>", faq_pos, section_end)
                if inner_div_close != -1:
                    extra_html = ""
                    for item in faqs_to_add:
                        extra_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{item["a"]}</p>\n                    </div>'
                    content = content[:inner_div_close] + extra_html + "\n                " + content[inner_div_close:]

    # 8. Fix JSON-LD FAQ count if < 10
    soup2 = BeautifulSoup(content, "html.parser")
    for s in soup2.find_all("script", type="application/ld+json"):
        if s.string and "FAQPage" in s.string:
            try:
                d = json.loads(s.string)
                changed = False
                if "@graph" in d:
                    for item in d["@graph"]:
                        if item.get("@type") == "FAQPage":
                            existing = item.get("mainEntity", [])
                            if len(existing) < 10:
                                pool = ar_faq_pool if lang == "ar" else en_faq_pool
                                random.seed(os.path.basename(path) + "json")
                                shuffled = pool[:]
                                random.shuffle(shuffled)
                                needed = 10 - len(existing)
                                for f_item in shuffled[:needed]:
                                    existing.append({"@type": "Question", "name": f_item["q"], "acceptedAnswer": {"@type": "Answer", "text": f_item["a"]}})
                                item["mainEntity"] = existing
                                changed = True
                        if item.get("@type") == "Organization":
                            if item.get("legalName") != "International Gulf Lotus SPC":
                                item["legalName"] = "International Gulf Lotus SPC"
                                changed = True
                if changed:
                    new_str = "\n" + json.dumps(d, indent=4, ensure_ascii=False) + "\n"
                    content = content.replace(s.string, new_str)
            except Exception as e:
                pass

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        fixed_count += 1
        print(f"  Fixed: {os.path.basename(path)}")

print(f"\nDone. {fixed_count} files updated.")
