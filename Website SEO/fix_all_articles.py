import os
import json
import re
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

# FAQ Pools
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
    {"q": "What if the AI makes a mistake with a customer?", "a": "Proper AI implementations use deterministic guardrails and RAG (Retrieval-Augmented Generation) to prevent hallucinations, often keeping a 'human-in-the-loop' for sensitive interactions."},
    {"q": "Is cloud-based AI legal for government contractors in Oman?", "a": "Government contractors must adhere to MTCIT guidelines, which often require data sovereignty and hosting sensitive data on local Omani servers."},
    {"q": "How does AI handle customer support outside of business hours?", "a": "AI chatbots and voice agents provide 24/7 instant responses, capturing leads and resolving common issues even when your physical office is closed."},
    {"q": "Can AI help with marketing and lead generation?", "a": "Yes, AI can analyze market trends, generate personalized ad copy, and automatically score incoming leads based on their likelihood to convert."},
    {"q": "What is 'deterministic' vs 'probabilistic' AI?", "a": "Probabilistic AI generates text based on patterns (like ChatGPT), while deterministic AI follows strict, hard-coded rules. Business automations require a mix of both for reliability."},
    {"q": "How do we train our staff to use new AI systems?", "a": "A reputable AI agency provides comprehensive onboarding, standard operating procedures (SOPs), and ongoing support to ensure smooth user adoption."},
    {"q": "Are there local AI agencies in Muscat?", "a": "Yes, local agencies like AI Profit Lab specialize in bringing global AI automation standards to Omani businesses with localized context."},
    {"q": "How does AI impact local hiring?", "a": "By automating mundane tasks, businesses can hire higher-skilled workers for strategic roles, elevating the overall capability of the local workforce."},
    {"q": "Can small SMEs afford AI technology?", "a": "Yes, the rise of no-code/low-code platforms has democratized AI, making it highly affordable for SMEs compared to hiring full-time developers."},
    {"q": "How does AI improve supply chain management?", "a": "AI predicts demand fluctuations, optimizes delivery routes in real-time, and automates inventory reordering, significantly reducing logistical costs."},
    {"q": "What is Retrieval-Augmented Generation (RAG)?", "a": "RAG is a technique where an AI model securely searches your private company documents before answering a question, ensuring accuracy and context."}
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
    {"q": "ماذا لو ارتكب الذكاء الاصطناعي خطأ مع عميل؟", "a": "تستخدم تطبيقات الذكاء الاصطناعي السليمة حواجز حتمية وتقنية RAG لمنع الهلوسة، وغالباً ما تبقي على 'الإشراف البشري' للتفاعلات الحساسة."},
    {"q": "هل الذكاء الاصطناعي السحابي قانوني للمقاولين الحكوميين في عُمان؟", "a": "يجب على المقاولين الحكوميين الالتزام بإرشادات وزارة النقل والاتصالات وتقنية المعلومات، والتي غالباً ما تتطلب سيادة البيانات واستضافة البيانات الحساسة على خوادم عمانية محلية."},
    {"q": "كيف يتعامل الذكاء الاصطناعي مع دعم العملاء خارج ساعات العمل؟", "a": "توفر روبوتات الدردشة والوكلاء الصوتيون استجابات فورية على مدار الساعة، مما يجذب العملاء المحتملين ويحل المشكلات الشائعة حتى عندما يكون مكتبك مغلقاً."},
    {"q": "هل يمكن للذكاء الاصطناعي المساعدة في التسويق وتوليد العملاء المحتملين؟", "a": "نعم، يمكن للذكاء الاصطناعي تحليل اتجاهات السوق، وإنشاء نصوص إعلانية مخصصة، وتسجيل العملاء المحتملين الواردين تلقائياً بناءً على احتمالية تحولهم."},
    {"q": "ما هو الذكاء الاصطناعي 'الحتمي' مقابل 'الاحتمالي'؟", "a": "يولد الذكاء الاصطناعي الاحتمالي نصوصاً بناءً على الأنماط، بينما يتبع الذكاء الاصطناعي الحتمي قواعد صارمة ومبرمجة. تتطلب أتمتة الأعمال مزيجاً من الاثنين للموثوقية."},
    {"q": "كيف ندرب موظفينا على استخدام أنظمة الذكاء الاصطناعي الجديدة؟", "a": "توفر وكالة الذكاء الاصطناعي ذات السمعة الطيبة تدريباً شاملاً وإجراءات تشغيل قياسية ودعماً مستمراً لضمان تبني المستخدم بسلاسة."},
    {"q": "هل هناك وكالات ذكاء اصطناعي محلية في مسقط؟", "a": "نعم، تتخصص الوكالات المحلية مثل AI Profit Lab في جلب معايير أتمتة الذكاء الاصطناعي العالمية إلى الشركات العمانية بسياق محلي."},
    {"q": "كيف يؤثر الذكاء الاصطناعي على التوظيف المحلي؟", "a": "من خلال أتمتة المهام العادية، يمكن للشركات توظيف عمال ذوي مهارات أعلى لأدوار استراتيجية، مما يرفع من القدرة الإجمالية للقوى العاملة المحلية."},
    {"q": "هل تستطيع الشركات الصغيرة والمتوسطة تحمل تكاليف تكنولوجيا الذكاء الاصطناعي؟", "a": "نعم، أدى ظهور منصات البرمجة بدون كود/منخفضة الكود إلى إضفاء الطابع الديمقراطي على الذكاء الاصطناعي، مما جعله في متناول الشركات الصغيرة والمتوسطة بشكل كبير مقارنة بتوظيف مطورين بدوام كامل."},
    {"q": "كيف يحسن الذكاء الاصطناعي إدارة سلسلة التوريد؟", "a": "يتنبأ الذكاء الاصطناعي بتقلبات الطلب، ويحسن طرق التسليم في الوقت الفعلي، ويؤتمت إعادة طلب المخزون، مما يقلل بشكل كبير من التكاليف اللوجستية."},
    {"q": "ما هو التوليد المعزز بالاسترجاع (RAG)؟", "a": "تقنية يبحث فيها نموذج الذكاء الاصطناعي بأمان في مستندات شركتك الخاصة قبل الإجابة على سؤال، مما يضمن الدقة والسياق."}
]

lb_schema = {
    "@context": "https://schema.org",
    "@type": "ProfessionalService",
    "name": "AI Profit Lab",
    "legalName": "International Gulf Lotus SPC",
    "url": "https://aiprofitlab.io",
    "logo": "https://aiprofitlab.io/logo.webp",
    "image": "https://aiprofitlab.io/nahid-business-banner.png",
    "description": "Helping non-technical managers leverage AI, automation, and technology to increase ROI and business efficiency.",
    "address": {
    "@type": "PostalAddress",
    "streetAddress": "Al Seeb",
    "addressLocality": "Muscat",
    "addressRegion": "Muscat Governorate",
    "postalCode": "000",
    "addressCountry": "OM"
    },
    "geo": {
    "@type": "GeoCoordinates",
    "latitude": 23.635950490475295, 
    "longitude": 58.207628165445385
    },
    "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+968-99245250",
    "contactType": "customer service",
    "areaServed": "GCC",
    "availableLanguage": ["en", "ar"]
    },
    "sameAs": [
    "https://www.youtube.com/@AI_for_Managers",
    "https://www.linkedin.com/in/nahid-aby"
    ]
}

lb_schema_ar = lb_schema.copy()
lb_schema_ar["description"] = "مساعدة المديرين غير التقنيين على الاستفادة من الذكاء الاصطناعي والأتمتة والتكنولوجيا لزيادة عائد الاستثمار وكفاءة الأعمال."

link_replacements = {
    r"https://vertexaisearch.*?": "https://aiprofitlab.io/blog/",
    r"https://www\.mtcit\.gov\.om/ITPortal/Pages/Page\.aspx\?NID=100&PID=300": "https://www.mtcit.gov.om/",
    r"https://hbr\.org/2021/05/how-ai-is-helping-companies-redesign-processes": "https://hbr.org/",
    r"https://hbr\.org/2023/11/how-to-calculate-the-roi-of-your-ai-investment": "https://hbr.org/",
    r"https://hbr\.org/2025/11/the-new-era-of-data-nationalization": "https://hbr.org/",
    r"https://hbr\.org/2021/09/how-to-build-trust-in-ai": "https://hbr.org/",
    r"https://hbr\.org/2023/11/a-simple-framework-for-integrating-ai-into-your-business": "https://hbr.org/",
    r"https://hbr\.org/2023/11/should-you-build-or-buy-your-ai-solution": "https://hbr.org/",
    r"https://www\.forbes\.com/sites/forbestechcouncil/2023/10/05/how-ai-driven-whatsapp-automation-is-boosting-global-sales/": "https://www.forbes.com/",
    r"https://www\.forbes\.com/sites/forbesbusinesscouncil/2023/08/17/why-partnering-with-an-ai-agency-is-crucial-for-modern-businesses/": "https://www.forbes.com/",
    r"https://www\.forbes\.com/sites/gordonkelly/2026/02/15/google-chrome-notification-overload-update/": "https://www.forbes.com/",
    r"https://aiprofitlab\.io/ar/": "https://aiprofitlab.io/",
    r"https://www\.oman2040\.om/en/": "https://www.oman2040.om/",
    r"https://www\.oman2040\.om/ar/": "https://www.oman2040.om/",
    r"https://www\.soharportandfreezone\.com": "https://soharportandfreezone.om/",
    r"https://gulfnews\.com/technology/google-to-discontinue-dark-web-monitoring-service-what-you-need-to-know-1.1711234567": "https://gulfnews.com/technology",
    r"https://www\.oliverwyman\.com/middle-east/insights/2023/how-the-gcc-can-win-the-ai-race\.html": "https://www.oliverwyman.com/middle-east/",
    r"https://blog\.google/products/gemini/google-gemini-workspace-enterprise/": "https://blog.google/products/gemini/"
}

for path in files_to_fix:
    lang = "ar" if "/ar/" in path else "en"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    soup = BeautifulSoup(content, "html.parser")
    original_content = content
    
    # 1. HTML Lang and Dir
    if lang == "ar":
        content = re.sub(r'<html[^>]*>', '<html lang="ar" dir="rtl">', content)
    else:
        content = re.sub(r'<html[^>]*>', '<html lang="en" dir="ltr">', content)

    # 2. Footers
    en_footer = '<footer class="py-8 border-t border-gray-900 text-center text-sm text-gray-600">\n        © 2025 <span class="text-blue-500">A</span><span class="text-red-500">I</span> Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved\n    </footer>'
    ar_footer = '<footer class="py-8 border-t border-gray-900 text-center text-sm text-gray-600">\n        © ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة\n    </footer>'
    footer_regex = r'<footer.*?</footer>'
    if re.search(footer_regex, content, re.DOTALL):
        content = re.sub(footer_regex, ar_footer if lang=="ar" else en_footer, content, flags=re.DOTALL)
    else:
        content = content.replace("</body>", (ar_footer if lang=="ar" else en_footer) + "\n</body>")

    # 3. LocalBusiness
    lb_json_str = json.dumps(lb_schema_ar if lang=="ar" else lb_schema, indent=4, ensure_ascii=False)
    lb_script = f'<script type="application/ld+json">\n{lb_json_str}\n</script>'
    lb_script_tag = None
    for s in soup.find_all("script", type="application/ld+json"):
        if "ProfessionalService" in s.string or "LocalBusiness" in s.string:
            lb_script_tag = s
            break
    if lb_script_tag:
        content = content.replace(str(lb_script_tag), lb_script)
    else:
        content = content.replace("</head>", lb_script + "\n</head>")

    # 4. Links
    for pattern, replacement in link_replacements.items():
        # simple string replace won't work for regex, so use re.sub for vertex links and replace for explicit strings
        if "vertexaisearch" in pattern:
            content = re.sub(pattern, replacement, content)
        else:
            p_clean = pattern.replace('\\.', '.')
            content = content.replace(p_clean, replacement)

    # 5. FAQs
    # Determine how many FAQs are currently there in JSON
    current_faqs = []
    schemas = soup.find_all("script", type="application/ld+json")
    for s in schemas:
        if "FAQPage" in s.string:
            try:
                data = json.loads(s.string)
                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "FAQPage":
                            current_faqs = item.get("mainEntity", [])
            except: pass
    
    faq_count = len(current_faqs)
    
    if faq_count < 10:
        pool = ar_faq_pool if lang == "ar" else en_faq_pool
        random.shuffle(pool)
        faqs_to_add = pool[:(10 - faq_count)]
        
        # Inject HTML
        faq_section = soup.find("section", id="faq")
        if faq_section:
            # Append inside existing
            insert_pos = content.rfind("</div>", 0, content.find("</section>", content.find("id=\"faq\"")))
            if insert_pos != -1:
                extra_html = ""
                for f_item in faqs_to_add:
                    extra_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{f_item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{f_item["a"]}</p>\n                    </div>'
                content = content[:insert_pos] + extra_html + "\n                " + content[insert_pos:]
        else:
            # Create new section entirely
            faq_title = "الأسئلة الشائعة" if lang=="ar" else "Frequently Asked Questions"
            faq_html = f'\n\n            <!-- FAQ Section -->\n            <section class="mt-16 pt-8 border-t border-white/10" id="faq">\n                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">{faq_title}</h2>\n                <div class="space-y-6">'
            for f_item in faqs_to_add:
                faq_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{f_item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{f_item["a"]}</p>\n                    </div>'
            faq_html += '\n                </div>\n            </section>'
            
            if "<!-- References -->" in content:
                content = content.replace("<!-- References -->", faq_html + "\n\n            <!-- References -->")
            else:
                article_end = content.find("</article>")
                if article_end != -1:
                    content = content[:article_end] + faq_html + "\n        " + content[article_end:]

        # Inject JSON
        if "FAQPage" not in content:
            # We must inject Organization, Article, FAQPage schema
            faq_json_nodes = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs_to_add]
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1).replace(" | AI Profit Lab", "") if title_match else ""
            desc_match = re.search(r'<meta name="description" content="(.*?)">', content)
            desc = desc_match.group(1) if desc_match else ""
            slug = os.path.basename(path).replace(".html", "")
            date_pub = slug[:10]
            
            schema_graph = {
                "@context": "https://schema.org",
                "@graph": [
                    {
                      "@type": "Organization",
                      "@id": "https://aiprofitlab.io/#organization",
                      "name": "AI Profit Lab",
                      "legalName": "International Gulf Lotus SPC",
                      "url": "https://aiprofitlab.io/",
                      "logo": {
                        "@type": "ImageObject",
                        "url": "https://aiprofitlab.io/favicon.svg"
                      }
                    },
                    {
                      "@type": "Article",
                      "headline": title,
                      "description": desc,
                      "image": "https://aiprofitlab.io/blog/images/placeholder.png",
                      "author": {
                        "@type": "Organization",
                        "name": "AI Profit Lab"
                      },
                      "publisher": {
                        "@id": "https://aiprofitlab.io/#organization"
                      },
                      "datePublished": date_pub
                    },
                    {
                      "@type": "FAQPage",
                      "mainEntity": faq_json_nodes
                    }
                ]
            }
            schema_str = json.dumps(schema_graph, indent=4, ensure_ascii=False)
            schema_tag = f'<script type="application/ld+json">\n{schema_str}\n</script>'
            content = content.replace("</head>", schema_tag + "\n</head>")
        else:
            # Has FAQPage but less than 10. We need to append.
            # Using string replacement to update the JSON is fragile but faster.
            # Let's extract the schema block, parse it, update it, replace it.
            for s2 in soup.find_all("script", type="application/ld+json"):
                if "FAQPage" in s2.string:
                    try:
                        d2 = json.loads(s2.string)
                        if "@graph" in d2:
                            for item in d2["@graph"]:
                                if item.get("@type") == "FAQPage":
                                    existing = item.get("mainEntity", [])
                                    for f_item in faqs_to_add:
                                        existing.append({"@type": "Question", "name": f_item["q"], "acceptedAnswer": {"@type": "Answer", "text": f_item["a"]}})
                                    item["mainEntity"] = existing
                                if item.get("@type") == "Organization":
                                    item["legalName"] = "International Gulf Lotus SPC"
                            new_s2 = json.dumps(d2, indent=4, ensure_ascii=False)
                            content = content.replace(s2.string, "\n" + new_s2 + "\n")
                    except: pass
    
    if content != original_content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Processed: {path}")

