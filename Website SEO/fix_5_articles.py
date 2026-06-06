import os
import json
import re
from bs4 import BeautifulSoup

base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog"

files_data = {
    "2026-06-05-whatsapp-workflows-oman-managers": {
        "en_add_faqs": [
            {"q": "Is WhatsApp automation secure for sensitive data?", "a": "Yes, the WhatsApp Cloud API uses end-to-end encryption for transmission, and deterministic backend rules ensure data is routed securely without public exposure."},
            {"q": "Can WhatsApp workflows integrate with local Omani payment gateways?", "a": "Yes, via webhooks, you can connect WhatsApp bots to payment processors like Thawani to automatically send payment links to customers."},
            {"q": "How does AI handle Arabic dialects on WhatsApp?", "a": "Modern LLMs integrated with WhatsApp are highly proficient in understanding Omani and Khaleeji dialects, ensuring smooth and natural customer interactions."},
            {"q": "Will WhatsApp ban my business number for using automation?", "a": "As long as you use the official WhatsApp Cloud API and adhere to Meta's commerce policies and opt-in rules, your number will not be banned."},
            {"q": "Can I send mass marketing broadcasts using this automation?", "a": "Yes, but WhatsApp requires pre-approved template messages for outbound marketing, which can be triggered automatically based on CRM data."}
        ],
        "ar_add_faqs": [
            {"q": "هل أتمتة الواتساب آمنة للبيانات الحساسة؟", "a": "نعم، تستخدم واجهة برمجة تطبيقات WhatsApp Cloud التشفير الشامل للنقل، وتضمن قواعد الواجهة الخلفية توجيه البيانات بأمان دون تعرضها للعامة."},
            {"q": "هل يمكن دمج مسارات عمل الواتساب مع بوابات الدفع العمانية المحلية؟", "a": "نعم، عبر خطاطيف الويب، يمكنك ربط روبوتات الواتساب بمعالجات الدفع مثل Thawani لإرسال روابط الدفع للعملاء تلقائياً."},
            {"q": "كيف يتعامل الذكاء الاصطناعي مع اللهجات العربية على الواتساب؟", "a": "النماذج اللغوية الكبيرة الحديثة المدمجة مع الواتساب بارعة جداً في فهم اللهجات العمانية والخليجية، مما يضمن تفاعلات طبيعية وسلسة مع العملاء."},
            {"q": "هل سيقوم الواتساب بحظر رقم نشاطي التجاري لاستخدام الأتمتة؟", "a": "طالما أنك تستخدم واجهة برمجة تطبيقات WhatsApp Cloud الرسمية وتلتزم بسياسات التجارة الخاصة بـ Meta وقواعد الاشتراك، فلن يتم حظر رقمك."},
            {"q": "هل يمكنني إرسال بث تسويقي جماعي باستخدام هذه الأتمتة؟", "a": "نعم، لكن الواتساب يتطلب رسائل نموذجية معتمدة مسبقاً للتسويق الصادر، والتي يمكن تشغيلها تلقائياً بناءً على بيانات CRM."}
        ]
    },
    "2026-05-13-live-ceo-dashboard-avoid-loss-secure-profit": {
        "en_add_faqs": [
            {"q": "What software is best for building a CEO dashboard?", "a": "Power BI, Tableau, and Google Looker Studio are popular choices. The best option depends on your existing tech stack and database architecture."},
            {"q": "How often is the data refreshed?", "a": "With live integrations, data can be refreshed in real-time or at scheduled intervals (e.g., every 5 minutes) depending on API rate limits."},
            {"q": "Do I need a data warehouse for a live dashboard?", "a": "For small businesses, direct API connections may suffice. For larger operations, a data warehouse (like BigQuery) is recommended to avoid slowing down production databases."},
            {"q": "Can dashboards track employee performance?", "a": "Yes, by integrating with HR and project management tools, dashboards can visualize KPIs like ticket resolution times or sales calls made per day."},
            {"q": "Are these dashboards mobile-friendly?", "a": "Modern dashboard platforms offer mobile apps or responsive designs, allowing managers to check KPIs directly from their smartphones."},
            {"q": "How much does it cost to set up a custom dashboard?", "a": "Costs vary widely based on data complexity, but a basic automated dashboard setup can range from a few hundred to a few thousand Omani Rials."}
        ],
        "ar_add_faqs": [
            {"q": "ما هو أفضل برنامج لبناء لوحة تحكم للمدير التنفيذي؟", "a": "تعد Power BI و Tableau و Google Looker Studio خيارات شائعة. يعتمد الخيار الأفضل على مجموعة التكنولوجيا وبنية قاعدة البيانات الحالية لديك."},
            {"q": "كم مرة يتم تحديث البيانات؟", "a": "من خلال التكاملات المباشرة، يمكن تحديث البيانات في الوقت الفعلي أو على فترات مجدولة (مثل كل 5 دقائق) اعتماداً على حدود واجهة برمجة التطبيقات."},
            {"q": "هل أحتاج إلى مستودع بيانات للوحة تحكم مباشرة؟", "a": "بالنسبة للشركات الصغيرة، قد تكفي اتصالات API المباشرة. للعمليات الأكبر، يوصى بمستودع بيانات (مثل BigQuery) لتجنب إبطاء قواعد بيانات الإنتاج."},
            {"q": "هل يمكن للوحات التحكم تتبع أداء الموظفين؟", "a": "نعم، من خلال الدمج مع أدوات الموارد البشرية وإدارة المشاريع، يمكن للوحات التحكم تصور مؤشرات الأداء الرئيسية مثل أوقات حل التذاكر أو مكالمات المبيعات التي يتم إجراؤها يومياً."},
            {"q": "هل لوحات التحكم هذه متوافقة مع الأجهزة المحمولة؟", "a": "تقدم منصات لوحات التحكم الحديثة تطبيقات للهواتف المحمولة أو تصميمات متجاوبة، مما يتيح للمديرين التحقق من مؤشرات الأداء الرئيسية مباشرة من هواتفهم الذكية."},
            {"q": "ما هي تكلفة إعداد لوحة تحكم مخصصة؟", "a": "تختلف التكاليف بشكل كبير بناءً على تعقيد البيانات، ولكن يمكن أن يتراوح إعداد لوحة تحكم آلية أساسية من بضع مئات إلى بضعة آلاف من الريالات العمانية."}
        ]
    },
    "2026-06-05-missed-call-recovery-system": {
        "en_add_faqs": [
            {"q": "Can I customize the WhatsApp message for missed calls?", "a": "Yes, you can personalize the message based on the time of day, day of the week, or even recognize if the caller is a returning customer."},
            {"q": "Does this work with Omani telecom providers like Omantel or Ooredoo?", "a": "It works best with Cloud Telephony/VoIP systems. Traditional landlines require a SIP trunk gateway to convert analog signals to digital webhooks."},
            {"q": "What happens if a customer replies to the automated message?", "a": "A conversational AI chatbot can immediately take over the conversation, or it can route the chat to a live human agent via a shared inbox."},
            {"q": "Can the system differentiate between business hours and after-hours?", "a": "Absolutely. The automation workflow can send a different message (e.g., 'We are currently closed') if the call is received outside working hours."},
            {"q": "How does this system impact overall sales?", "a": "By engaging leads instantly when their purchase intent is highest, missed-call recovery systems typically boost conversion rates by 15-30%."}
        ],
        "ar_add_faqs": [
            {"q": "هل يمكنني تخصيص رسالة الواتساب للمكالمات الفائتة؟", "a": "نعم، يمكنك تخصيص الرسالة بناءً على الوقت من اليوم، أو يوم الأسبوع، أو حتى التعرف على ما إذا كان المتصل عميلاً متكرراً."},
            {"q": "هل يعمل هذا مع مزودي الاتصالات العمانيين مثل عمانتل أو أوريدو؟", "a": "يعمل بشكل أفضل مع أنظمة الاتصالات السحابية/VoIP. تتطلب الخطوط الأرضية التقليدية بوابة SIP لتحويل الإشارات التناظرية إلى خطاطيف ويب رقمية."},
            {"q": "ماذا يحدث إذا رد العميل على الرسالة الآلية؟", "a": "يمكن لروبوت دردشة الذكاء الاصطناعي تولي المحادثة فوراً، أو يمكنه توجيه الدردشة إلى وكيل بشري مباشر عبر صندوق وارد مشترك."},
            {"q": "هل يمكن للنظام التمييز بين ساعات العمل وما بعد الدوام؟", "a": "بالتأكيد. يمكن لسير عمل الأتمتة إرسال رسالة مختلفة (مثل 'نحن مغلقون حالياً') إذا تم تلقي المكالمة خارج ساعات العمل."},
            {"q": "كيف يؤثر هذا النظام على المبيعات الإجمالية؟", "a": "من خلال التفاعل مع العملاء المحتملين على الفور عندما تكون نية الشراء في ذروتها، تعزز أنظمة استرداد المكالمات الفائتة عادة معدلات التحويل بنسبة 15-30٪."}
        ]
    },
    "2026-04-21-ai-oil-gas-workflow-automation": {
        "en_add_faqs": [
            {"q": "How is AI used in the oil and gas industry in Oman?", "a": "AI is used to optimize drilling operations, predict equipment failures, automate supply chain logistics, and ensure compliance with environmental regulations."},
            {"q": "What is predictive maintenance in oil rigs?", "a": "Predictive maintenance uses IoT sensors and AI to analyze equipment vibration and temperature, predicting failures before they occur to minimize costly downtime."},
            {"q": "Can AI automate pipeline monitoring?", "a": "Yes, AI-powered computer vision can analyze drone footage of pipelines to instantly detect leaks, corrosion, or security breaches."},
            {"q": "How does AI improve drilling efficiency?", "a": "AI algorithms analyze historical geological data and real-time sensor feedback to optimize drilling speed and pressure, reducing time and resource waste."},
            {"q": "Is data security a concern for AI in Omani energy sectors?", "a": "Yes, which is why energy companies deploy localized, on-premise AI models or highly secure enterprise cloud solutions to protect sensitive operational data."},
            {"q": "How does AI assist in supply chain management for oil and gas?", "a": "AI predicts material demands, optimizes delivery routes for heavy equipment, and automates inventory management at remote rig sites."},
            {"q": "Can AI help meet Oman Vision 2040 sustainability goals?", "a": "By optimizing fuel consumption in operations and detecting emissions anomalies early, AI significantly reduces the carbon footprint of oil extraction."},
            {"q": "What is a 'digital twin' in the energy sector?", "a": "A digital twin is a virtual replica of a physical asset (like a refinery). AI uses it to simulate scenarios and test operational changes without risking real-world assets."},
            {"q": "Does AI replace engineers in the oil field?", "a": "No, AI augments engineers by handling data processing and monitoring, allowing human experts to focus on complex decision-making and strategy."},
            {"q": "What is the ROI of implementing AI in oil and gas?", "a": "ROI comes from reduced operational downtime, increased extraction efficiency, and lower maintenance costs, often paying for the initial investment within months."}
        ],
        "ar_add_faqs": [
            {"q": "كيف يُستخدم الذكاء الاصطناعي في صناعة النفط والغاز في عُمان؟", "a": "يُستخدم الذكاء الاصطناعي لتحسين عمليات الحفر، والتنبؤ بأعطال المعدات، وأتمتة لوجستيات سلسلة التوريد، وضمان الامتثال للوائح البيئية."},
            {"q": "ما هي الصيانة التنبؤية في منصات النفط؟", "a": "تستخدم الصيانة التنبؤية مستشعرات إنترنت الأشياء والذكاء الاصطناعي لتحليل اهتزاز المعدات ودرجة حرارتها، والتنبؤ بالأعطال قبل حدوثها لتقليل وقت التوقف المكلف."},
            {"q": "هل يمكن للذكاء الاصطناعي أتمتة مراقبة خطوط الأنابيب؟", "a": "نعم، يمكن للرؤية الحاسوبية المدعومة بالذكاء الاصطناعي تحليل لقطات الطائرات بدون طيار لخطوط الأنابيب لاكتشاف التسربات أو التآكل أو الاختراقات الأمنية على الفور."},
            {"q": "كيف يحسن الذكاء الاصطناعي كفاءة الحفر؟", "a": "تحلل خوارزميات الذكاء الاصطناعي البيانات الجيولوجية التاريخية وملاحظات المستشعرات في الوقت الفعلي لتحسين سرعة وضغط الحفر، مما يقلل من إهدار الوقت والموارد."},
            {"q": "هل يمثل أمن البيانات مصدر قلق للذكاء الاصطناعي في قطاعات الطاقة العمانية؟", "a": "نعم، ولهذا السبب تنشر شركات الطاقة نماذج ذكاء اصطناعي محلية ومثبتة في الموقع أو حلول سحابية مؤسسية آمنة للغاية لحماية البيانات التشغيلية الحساسة."},
            {"q": "كيف يساعد الذكاء الاصطناعي في إدارة سلسلة التوريد للنفط والغاز؟", "a": "يتنبأ الذكاء الاصطناعي بمتطلبات المواد، ويحسن طرق توصيل المعدات الثقيلة، ويؤتمت إدارة المخزون في مواقع الحفر البعيدة."},
            {"q": "هل يمكن للذكاء الاصطناعي المساعدة في تحقيق أهداف الاستدامة لرؤية عمان 2040؟", "a": "من خلال تحسين استهلاك الوقود في العمليات والاكتشاف المبكر للحالات الشاذة في الانبعاثات، يقلل الذكاء الاصطناعي بشكل كبير من البصمة الكربونية لاستخراج النفط."},
            {"q": "ما هو 'التوأم الرقمي' في قطاع الطاقة؟", "a": "التوأم الرقمي هو نسخة افتراضية طبق الأصل من أصل مادي (مثل مصفاة). يستخدمه الذكاء الاصطناعي لمحاكاة السيناريوهات واختبار التغييرات التشغيلية دون المخاطرة بالأصول في العالم الحقيقي."},
            {"q": "هل يحل الذكاء الاصطناعي محل المهندسين في حقل النفط؟", "a": "لا، يعزز الذكاء الاصطناعي عمل المهندسين من خلال التعامل مع معالجة البيانات والمراقبة، مما يسمح للخبراء البشريين بالتركيز على اتخاذ القرارات المعقدة والاستراتيجية."},
            {"q": "ما هو عائد الاستثمار لتنفيذ الذكاء الاصطناعي في النفط والغاز؟", "a": "يأتي عائد الاستثمار من تقليل وقت التوقف التشغيلي، وزيادة كفاءة الاستخراج، وانخفاض تكاليف الصيانة، وغالباً ما يغطي الاستثمار الأولي في غضون أشهر."}
        ]
    },
    "2026-04-14-ai-ethics-sharia-compliance": {
        "en_add_faqs": [
            {"q": "What makes an AI system Sharia-compliant?", "a": "A Sharia-compliant AI system avoids promoting prohibited (Haram) activities, respects user privacy, ensures fairness, and operates transparently without deception."},
            {"q": "Can AI be used in Islamic finance?", "a": "Yes, AI is used in Islamic fintech for risk assessment, fraud detection, and algorithmic trading that complies with Sharia principles against usury (Riba)."},
            {"q": "How does AI respect data privacy under Islamic ethics?", "a": "Islamic ethics prioritize the protection of individual privacy and dignity. AI systems must ensure data anonymization and secure consent before processing personal information."},
            {"q": "Are there ethical guidelines for AI in Oman?", "a": "Oman is actively developing national AI strategies and ethical guidelines through the MTCIT, aligning technological advancement with Islamic values and societal norms."},
            {"q": "Does AI bias conflict with Sharia?", "a": "Yes, Sharia emphasizes justice and equality (Adl). AI algorithms that exhibit racial, gender, or economic bias violate these fundamental Islamic principles of fairness."},
            {"q": "How can companies audit AI for ethical compliance?", "a": "Companies can use third-party ethical AI audits, implement explainable AI (XAI) models, and establish ethical review boards that include Islamic scholars."},
            {"q": "Is automated decision-making allowed in Islamic law?", "a": "It is permitted for administrative tasks, but significant decisions affecting human lives (like judicial rulings or critical healthcare) must have human oversight to ensure accountability."},
            {"q": "What is the Islamic stance on AI generating deepfakes?", "a": "Generating deepfakes for deception, defamation, or spreading falsehoods is strictly prohibited, as Islam strongly condemns lying and spreading corruption."},
            {"q": "Can generative AI create Islamic content?", "a": "Generative AI can assist in translating texts or searching the Quran and Hadith, but it must be heavily fact-checked by scholars to prevent theological errors or misinterpretations."},
            {"q": "Why is transparency important in AI from an Islamic perspective?", "a": "Transparency prevents Gharar (excessive uncertainty or deception). Users have the right to know when they are interacting with an AI and how their data is being used."}
        ],
        "ar_add_faqs": [
            {"q": "ما الذي يجعل نظام الذكاء الاصطناعي متوافقاً مع الشريعة الإسلامية؟", "a": "يتجنب نظام الذكاء الاصطناعي المتوافق مع الشريعة الترويج للأنشطة المحرمة، ويحترم خصوصية المستخدم، ويضمن العدالة، ويعمل بشفافية دون خداع."},
            {"q": "هل يمكن استخدام الذكاء الاصطناعي في التمويل الإسلامي؟", "a": "نعم، يُستخدم الذكاء الاصطناعي في التكنولوجيا المالية الإسلامية لتقييم المخاطر واكتشاف الاحتيال والتداول الخوارزمي الذي يتوافق مع مبادئ الشريعة ضد الربا."},
            {"q": "كيف يحترم الذكاء الاصطناعي خصوصية البيانات في ظل الأخلاق الإسلامية؟", "a": "تعطي الأخلاق الإسلامية الأولوية لحماية خصوصية الفرد وكرامته. يجب أن تضمن أنظمة الذكاء الاصطناعي إخفاء هوية البيانات والحصول على الموافقة الآمنة قبل معالجة المعلومات الشخصية."},
            {"q": "هل هناك مبادئ توجيهية أخلاقية للذكاء الاصطناعي في عُمان؟", "a": "تعمل عُمان بنشاط على تطوير استراتيجيات وطنية ومبادئ توجيهية أخلاقية للذكاء الاصطناعي من خلال وزارة النقل والاتصالات وتقنية المعلومات، بما يوائم التقدم التكنولوجي مع القيم الإسلامية والأعراف المجتمعية."},
            {"q": "هل يتعارض تحيز الذكاء الاصطناعي مع الشريعة؟", "a": "نعم، تؤكد الشريعة على العدل والمساواة. خوارزميات الذكاء الاصطناعي التي تظهر تحيزاً عنصرياً أو جنسياً أو اقتصادياً تنتهك هذه المبادئ الإسلامية الأساسية للعدالة."},
            {"q": "كيف يمكن للشركات تدقيق الذكاء الاصطناعي للامتثال الأخلاقي؟", "a": "يمكن للشركات استخدام عمليات تدقيق أخلاقية للذكاء الاصطناعي من قبل جهات خارجية، وتنفيذ نماذج ذكاء اصطناعي قابلة للتفسير (XAI)، وتأسيس مجالس مراجعة أخلاقية تضم علماء دين."},
            {"q": "هل يُسمح باتخاذ القرارات الآلية في الشريعة الإسلامية؟", "a": "يُسمح به في المهام الإدارية، لكن القرارات المهمة التي تؤثر على حياة الإنسان (مثل الأحكام القضائية أو الرعاية الصحية الحرجة) يجب أن تخضع لإشراف بشري لضمان المساءلة."},
            {"q": "ما هو الموقف الإسلامي من إنشاء الذكاء الاصطناعي للتزييف العميق (Deepfakes)؟", "a": "يُحظر تماماً إنشاء التزييف العميق للخداع أو التشهير أو نشر الأكاذيب، حيث يدين الإسلام بشدة الكذب ونشر الفساد."},
            {"q": "هل يمكن للذكاء الاصطناعي التوليدي إنشاء محتوى إسلامي؟", "a": "يمكن للذكاء الاصطناعي التوليدي المساعدة في ترجمة النصوص أو البحث في القرآن والحديث، ولكن يجب تدقيقه بشدة من قبل العلماء لمنع الأخطاء اللاهوتية أو التفسيرات الخاطئة."},
            {"q": "لماذا تعتبر الشفافية مهمة في الذكاء الاصطناعي من منظور إسلامي؟", "a": "تمنع الشفافية 'الغرر' (عدم اليقين المفرط أو الخداع). للمستخدمين الحق في معرفة متى يتفاعلون مع ذكاء اصطناعي وكيف يتم استخدام بياناتهم."}
        ]
    }
}

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

for slug, data in files_data.items():
    for lang in ["en", "ar"]:
        path = os.path.join(base_dir, lang, slug + ".html")
        if not os.path.exists(path):
            print(f"Skipping {path}, not found.")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix HTML lang and dir
        if lang == "ar":
            content = re.sub(r'<html[^>]*>', '<html lang="ar" dir="rtl">', content)
        else:
            content = re.sub(r'<html[^>]*>', '<html lang="en" dir="ltr">', content)

        # Fix Footer
        en_footer = '<footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">\n        <p>&copy; 2025 AI Profit Lab &mdash; a brand of International Gulf Lotus SPC &bull; All Rights Reserved</p>\n    </footer>'
        ar_footer = '<footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">\n        <p dir="ltr">&copy; ٢٠٢٥ AI Profit Lab &mdash; علامة تجارية لشركة International Gulf Lotus SPC &bull; جميع الحقوق محفوظة</p>\n    </footer>'
        
        # Replace existing footer or append before </body>
        footer_regex = r'<footer.*?</footer>'
        if re.search(footer_regex, content, re.DOTALL):
            content = re.sub(footer_regex, ar_footer if lang=="ar" else en_footer, content, flags=re.DOTALL)
        else:
            content = content.replace("</body>", (ar_footer if lang=="ar" else en_footer) + "\n</body>")

        # Fix LocalBusiness Schema
        lb_json_str = json.dumps(lb_schema_ar if lang=="ar" else lb_schema, indent=4, ensure_ascii=False)
        lb_script = f'<script type="application/ld+json">\n{lb_json_str}\n</script>'
        
        # Remove old LocalBusiness if present
        soup = BeautifulSoup(content, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        lb_script_tag = None
        for s in scripts:
            if "ProfessionalService" in s.string or "LocalBusiness" in s.string:
                lb_script_tag = s
                break
        if lb_script_tag:
            content = content.replace(str(lb_script_tag), lb_script)
        else:
            content = content.replace("</head>", lb_script + "\n</head>")

        # Fix links (Broken links replacement)
        if slug == "2026-04-14-ai-ethics-sharia-compliance":
            content = content.replace("https://ssrn.com/abstract=3830491", "https://www.mtcit.gov.om/")
            content = content.replace("https://hai.stanford.edu/news/global-ai-ethics-review", "https://hai.stanford.edu/")
            content = content.replace("https://www.weforum.org/agenda/2026/02/ai-governance-middle-east-growth/", "https://www.mtcit.gov.om/")

        # Insert missing FAQ schema and HTML if missing entirely
        # For oil-gas and ethics, they are missing it entirely
        add_faqs = data["ar_add_faqs"] if lang == "ar" else data["en_add_faqs"]
        
        # Determine current FAQs in JSON
        # First let's just append the new FAQs to the HTML
        if "id=\"faq\"" not in content:
            faq_title = "الأسئلة الشائعة" if lang=="ar" else "Frequently Asked Questions"
            faq_html = f'\n\n            <!-- FAQ Section -->\n            <section class="mt-16 pt-8 border-t border-white/10" id="faq">\n                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">{faq_title}</h2>\n                <div class="space-y-6">'
            for f_item in add_faqs:
                faq_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{f_item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{f_item["a"]}</p>\n                    </div>'
            faq_html += '\n                </div>\n            </section>'
            
            # insert before references or </article>
            if "<!-- References -->" in content:
                content = content.replace("<!-- References -->", faq_html + "\n\n            <!-- References -->")
            else:
                article_end = content.find("</article>")
                if article_end != -1:
                    content = content[:article_end] + faq_html + "\n        " + content[article_end:]
        else:
            # Append to existing FAQ HTML
            insert_pos = content.rfind("</div>", 0, content.find("</section>", content.find("id=\"faq\"")))
            if insert_pos != -1:
                extra_html = ""
                for f_item in add_faqs:
                    extra_html += f'\n                    <div class="glass-card rounded-2xl p-6">\n                        <h3 class="text-lg font-bold text-white mb-2">{f_item["q"]}</h3>\n                        <p class="text-gray-400 mb-0">{f_item["a"]}</p>\n                    </div>'
                content = content[:insert_pos] + extra_html + "\n                " + content[insert_pos:]

        # Now, fix JSON-LD for Organization, Article, FAQPage
        # If it's missing, let's inject it.
        if "FAQPage" not in content:
            # We need to construct the full schema for Article, Org, FAQ
            faq_json_nodes = [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in add_faqs]
            title_match = re.search(r'<title>(.*?)</title>', content)
            title = title_match.group(1).replace(" | AI Profit Lab", "") if title_match else ""
            desc_match = re.search(r'<meta name="description" content="(.*?)">', content)
            desc = desc_match.group(1) if desc_match else ""
            
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
            # Update existing FAQPage schema
            # We need to parse and rewrite the @graph schema
            soup2 = BeautifulSoup(content, "html.parser")
            scripts2 = soup2.find_all("script", type="application/ld+json")
            for s2 in scripts2:
                if "FAQPage" in s2.string:
                    try:
                        d2 = json.loads(s2.string)
                        if "@graph" in d2:
                            for item in d2["@graph"]:
                                if item.get("@type") == "FAQPage":
                                    existing_faqs = item.get("mainEntity", [])
                                    for f_item in add_faqs:
                                        existing_faqs.append({"@type": "Question", "name": f_item["q"], "acceptedAnswer": {"@type": "Answer", "text": f_item["a"]}})
                                    item["mainEntity"] = existing_faqs
                                if item.get("@type") == "Organization":
                                    item["legalName"] = "International Gulf Lotus SPC"
                            new_s2 = json.dumps(d2, indent=4, ensure_ascii=False)
                            content = content.replace(s2.string, "\n" + new_s2 + "\n")
                    except Exception as e:
                        print(e)
                        pass
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {path}")

