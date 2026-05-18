import re

with open('../public_html/medflow-sales-automation-demo.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace language
content = content.replace('<html lang="en">', '<html lang="ar" dir="rtl">')

# Update title and meta
content = content.replace(
    '<title>MedFlow Sales & Invoice Automation Demo | AI Profit Lab</title>',
    '<title>العرض التجريبي: أتمتة المبيعات والفواتير | AI Profit Lab</title>'
)
content = content.replace(
    'Experience MedFlow Sales & Invoice Automation. Discover how AI Profit Lab delivers 10x ROI for medical businesses in Oman and the GCC.',
    'جرب نظام أتمتة المبيعات والفواتير. اكتشف كيف تقدم AI Profit Lab عائداً على الاستثمار 10 أضعاف للشركات الطبية في عمان والخليج.'
)
content = content.replace(
    'medical sales automation, invoice automation, MedFlow, AI Profit Lab, Oman business automation, GCC',
    'أتمتة المبيعات الطبية, أتمتة الفواتير, الذكاء الاصطناعي, AI Profit Lab, أتمتة الأعمال عمان, الخليج'
)
content = content.replace(
    'Watch how orders turn into invoices automatically without manual work.',
    'شاهد كيف تتحول الطلبات إلى فواتير تلقائياً بدون عمل يدوي.'
)
content = content.replace(
    'Automate medical sales and invoice processing.',
    'أتمتة عمليات المبيعات وإصدار الفواتير الطبية.'
)
content = content.replace(
    '<link rel="canonical" href="https://aiprofitlab.io/medflow-sales-automation-demo.html" />',
    '<link rel="canonical" href="https://aiprofitlab.io/medflow-sales-automation-demo-ar.html" />'
)

# Navigation
content = content.replace('href="/en/"', 'href="/"')
content = content.replace('>How it works<', '>طريقة العمل<')
content = content.replace('>Try the demo<', '>جرب النظام<')

# Fonts update - we need to make sure Cairo is included for Arabic if needed, but the user requested exact same page, just change language.
content = content.replace("family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500", "family=Cairo:wght@300;400;500;600;700;800")
content = content.replace("--font-serif: 'Instrument Serif', Georgia, serif;", "--font-serif: 'Cairo', sans-serif;")
content = content.replace("--font-sans:  'Geist', sans-serif;", "--font-sans:  'Cairo', sans-serif;")
content = content.replace("--font-mono:  'Geist Mono', monospace;", "--font-mono:  'Cairo', sans-serif;")

# Alignment fixes for RTL in CSS
content = content.replace("margin-left:auto;", "margin-right:auto;")
content = content.replace("padding-left:4vw;padding-right:4vw;", "padding-right:4vw;padding-left:4vw;")
content = content.replace("border-right:1px solid rgba(255,255,255,0.06);", "border-left:1px solid rgba(255,255,255,0.06);")
content = content.replace("border-left:none;", "border-right:none;") # For pane:last-child (wait, let's just do it dynamically)
content = content.replace("text-align:left;", "text-align:right;")
content = content.replace("text-align:right;", "text-align:left;")

# Note: text-align replacement above might cancel out or break. Let's be careful.
content = content.replace("text-align:left;", "TEMP_TEXT_ALIGN_RIGHT;")
content = content.replace("text-align:right;", "text-align:left;")
content = content.replace("TEMP_TEXT_ALIGN_RIGHT;", "text-align:right;")

# Let's fix the pane border correctly
content = content.replace("border-right:1px solid rgba(255,255,255,0.06);", "border-left:1px solid rgba(255,255,255,0.06);border-right:none;")

# Text Replacements
content = content.replace("Medical sales automation", "أتمتة المبيعات الطبية")
content = content.replace("Orders in.<br>Invoices out.<br><em>Automatically.</em>", "الطلبات تدخل.<br>الفواتير تصدر.<br><em>تلقائياً.</em>")
content = content.replace("From WhatsApp order to paid invoice without a single manual step. Your team closes deals — the system handles everything else.", "من الطلب عبر واتساب إلى الفاتورة المدفوعة بدون تدخل يدوي. فريقك يغلق الصفقات — والنظام يتولى الباقي.")
content = content.replace("↓ Try the live demo", "↓ جرب النظام المباشر")
content = content.replace("See how it works", "شاهد كيف يعمل")

content = content.replace("Orders processed<br>this month", "الطلبات المعالجة<br>هذا الشهر")
content = content.replace("↑ 23% vs last month", "↑ 23% عن الشهر الماضي")
content = content.replace("Invoice sent after<br>order arrives", "إرسال الفاتورة بعد<br>وصول الطلب")
content = content.replace("Fully automatic", "آلي بالكامل")
content = content.replace("Saved per week<br>per sales rep", "توفير أسبوعي<br>لكل مندوب مبيعات")
content = content.replace("Zero data entry", "بدون إدخال بيانات")
content = content.replace("Improvement in<br>on-time collections", "تحسن في<br>التحصيل بالوقت المحدد")
content = content.replace("Avg across clients", "متوسط التحسن")

content = content.replace("Interactive simulation", "محاكاة تفاعلية")
content = content.replace("Be the sales rep.<br><em>Watch it automate.</em>", "كن أنت المندوب.<br><em>وشاهد الأتمتة.</em>")
content = content.replace("Type a real order below — exactly like a customer would WhatsApp you. Then watch the system process every step live across all three panels.", "اكتب طلباً حقيقياً بالأسفل — تماماً كما يرسله العميل عبر واتساب. ثم شاهد النظام يعالج كل خطوة مباشرة عبر اللوحات الثلاث.")

content = content.replace("AI Profit Lab — Sales Dashboard", "لوحة تحكم المبيعات — AI Profit Lab")
content = content.replace("Order", "الطلب")
content = content.replace("Pipeline", "مسار العمل")
content = content.replace("Output", "المخرجات")

content = content.replace("WhatsApp — Al Shifa Pharmacy", "واتساب — صيدلية الشفاء")
content = content.replace("online", "متصل")
content = content.replace("Salam! We need our monthly order please 🙏", "السلام عليكم! نحتاج طلبيتنا الشهرية لو سمحت 🙏")

content = content.replace("Type order (e.g. 100x Paracetamol, 50x Amoxicillin)…", "اكتب الطلب (مثال: 100x باراسيتامول, 50x أموكسيسيلين)...")
content = content.replace("Quick fill", "تعبئة سريعة")
content = content.replace("Pharmacy order", "طلب صيدلية")
content = content.replace("Clinic order", "طلب عيادة")
content = content.replace("Hospital order", "طلب مستشفى")

content = content.replace("Automation Pipeline", "مسار الأتمتة")
content = content.replace("Waiting for order", "بانتظار الطلب")
content = content.replace("Send an order to begin the workflow", "أرسل طلباً لبدء مسار العمل")

content = content.replace("Order received", "تم استلام الطلب")
content = content.replace("WhatsApp message parsed and captured", "تم تحليل رسالة واتساب والتقاطها")
content = content.replace("waiting", "بانتظار")

content = content.replace("Logged to Google Sheet", "تم التسجيل في جوجل شيت")
content = content.replace("Row added with ID, items, customer, rep", "تمت إضافة صف بالمعرف، العناصر، العميل")

content = content.replace("Invoice generated & sent", "تم إنشاء الفاتورة وإرسالها")
content = content.replace("PDF delivered via email + WhatsApp", "تم إرسال PDF عبر الإيميل وواتساب")

content = content.replace("Payment reminders scheduled", "تم جدولة تذكيرات الدفع")
content = content.replace("Auto-sends at D-3 and D-1", "إرسال تلقائي قبل 3 أيام ويوم واحد")

content = content.replace("Overdue escalation armed", "تم تفعيل تصعيد التأخير")
content = content.replace("Manager WhatsApp alert if payment missed", "تنبيه للمدير عبر واتساب في حال عدم الدفع")

content = content.replace("↺ Reset and try again", "↺ إعادة ضبط والمحاولة مرة أخرى")

content = content.replace("Order & Invoice Output", "مخرجات الطلب والفاتورة")
content = content.replace("Order details, invoice preview, and alerts will appear here as the workflow runs.", "ستظهر تفاصيل الطلب ومعاينة الفاتورة والتنبيهات هنا أثناء سير العمل.")

content = content.replace("Ready — type or pick a quick fill to begin", "جاهز — اكتب أو اختر تعبئة سريعة للبدء")

content = content.replace("The transformation", "التحول")
content = content.replace("What your team's day looks like<br><em>before and after</em>", "كيف يبدو يوم فريقك<br><em>قبل وبعد</em>")
content = content.replace("Without Automation", "بدون أتمتة")
content = content.replace("Rep takes order on WhatsApp, details get lost or misread", "المندوب يستلم الطلب عبر واتساب، وتضيع التفاصيل أو تُفهم خطأ")
content = content.replace("Admin manually types into Tally — takes 15–30 min per order", "إدخال يدوي في النظام المالي — يستغرق 15-30 دقيقة لكل طلب")
content = content.replace("Invoice created late, sent to wrong contact, or not at all", "الفاتورة تصدر متأخرة، ترسل للشخص الخطأ، أو لا ترسل إطلاقاً")
content = content.replace("Payment chased by phone — no one owns due-date tracking", "ملاحقة الدفع بالهاتف — لا أحد يتابع تواريخ الاستحقاق")
content = content.replace("Manager hears about overdue invoices only at month-end review", "المدير يعلم بالفواتير المتأخرة فقط في مراجعة نهاية الشهر")
content = content.replace("Zero visibility into the sales pipeline or collection rate", "انعدام الرؤية لمسار المبيعات أو معدل التحصيل")

content = content.replace("With Automation", "مع الأتمتة")
content = content.replace("Order auto-captured the moment it arrives on WhatsApp or email", "يتم التقاط الطلب آلياً لحظة وصوله عبر واتساب أو الإيميل")
content = content.replace("Instantly logged to Google Sheet — zero manual entry, zero errors", "يسجل فوراً في جوجل شيت — صفر إدخال يدوي، صفر أخطاء")
content = content.replace("Branded PDF invoice generated and sent in under 2 minutes", "يتم إنشاء فاتورة PDF احترافية وإرسالها في أقل من دقيقتين")
content = content.replace("Automated reminders go out at D-3 and D-1 without lifting a finger", "تذكيرات آلية ترسل قبل موعد الاستحقاق بـ 3 أيام ويوم واحد")
content = content.replace("Manager gets a WhatsApp alert the same day an invoice goes overdue", "المدير يتلقى تنبيهاً على واتساب في نفس يوم تأخر الفاتورة")
content = content.replace("Live dashboard — full order, invoice, and payment visibility", "لوحة تحكم مباشرة — رؤية كاملة للطلبات والفواتير والمدفوعات")

content = content.replace("Stop chasing.<br>Start <em>collecting.</em>", "توقف عن الملاحقة.<br>ابدأ <em>التحصيل.</em>")
content = content.replace("Set up in under a week. Works with your existing WhatsApp number and Google account. No disruption to how your reps work today.", "يتم الإعداد في أقل من أسبوع. يعمل مع رقم واتساب وحساب جوجل الحاليين. لا يوجد تغيير على طريقة عمل فريقك الحالية.")
content = content.replace("Request a demo", "احجز عرضاً توضيحياً")
content = content.replace("See pricing", "شاهد الباقات")

content = content.replace("Sales & Invoice Automation for Medical Teams", "أتمتة المبيعات والفواتير للفرق الطبية")
content = content.replace("Muscat, Oman", "مسقط، عمان")

content = content.replace('href="/en/contact-en/"', 'href="/contact/"')
content = content.replace('href="/en/services-en/"', 'href="/services/"')

# Script replacements
content = content.replace("Processing order…", "جاري معالجة الطلب...")
content = content.replace("capturing…", "جاري التقاط...")
content = content.replace("Capturing order", "التقاط الطلب")
content = content.replace("Reading WhatsApp message…", "قراءة رسالة واتساب...")
content = content.replace("✅ Got it! Processing your order now…", "✅ علم! جاري معالجة طلبك الآن...")
content = content.replace("captured ✓", "تم الالتقاط ✓")
content = content.replace("Logging to Google Sheet…", "جاري التسجيل في جوجل شيت...")
content = content.replace("order logged", "تم تسجيل الطلب")
content = content.replace("Step 1 complete — order captured", "الخطوة 1 اكتملت — تم التقاط الطلب")
content = content.replace("Due:", "مستحقة:")
content = content.replace("May", "مايو")
content = content.replace("Al Shifa Pharmacy", "صيدلية الشفاء")
content = content.replace("writing to sheet…", "جاري الكتابة للشيت...")
content = content.replace("Adding row with order details…", "إضافة صف بتفاصيل الطلب...")
content = content.replace("row added ✓", "تم إضافة الصف ✓")
content = content.replace("Sheet updated", "تم تحديث الشيت")
content = content.replace("Generating invoice PDF…", "جاري إنشاء الفاتورة...")
content = content.replace("Logged to Google Sheet as", "تم التسجيل برقم")
content = content.replace("Step 2 complete — logged to sheet", "الخطوة 2 اكتملت — تم التسجيل بالشيت")
content = content.replace("generating PDF…", "جاري إنشاء PDF...")
content = content.replace("Generating invoice", "إنشاء الفاتورة")
content = content.replace("Building PDF from your template…", "بناء PDF من القالب الخاص بك...")
content = content.replace("invoice sent ✓", "تم إرسال الفاتورة ✓")
content = content.replace("Invoice sent", "تم إرسال الفاتورة")
content = content.replace("Scheduling payment reminders…", "جاري جدولة تذكيرات الدفع...")
content = content.replace("Invoice", "فاتورة")
content = content.replace("sent — OMR", "أرسلت — ر.ع")
content = content.replace("due", "تستحق في")
content = content.replace("Step 3 complete — invoice delivered", "الخطوة 3 اكتملت — تم تسليم الفاتورة")

content = content.replace("Tax Invoice", "فاتورة ضريبية")
content = content.replace("SENT ✓", "أرسلت ✓")
content = content.replace("Bill to", "فاتورة إلى")
content = content.replace("Invoice #", "رقم الفاتورة")
content = content.replace("Date", "التاريخ")
content = content.replace("Due date", "تاريخ الاستحقاق")
content = content.replace("Items", "العناصر")
content = content.replace("Subtotal", "المجموع الفرعي")
content = content.replace("VAT 5%", "ضريبة 5%")
content = content.replace("Total", "الإجمالي")
content = content.replace("WhatsApp delivered", "تم التسليم عبر واتساب")

content = content.replace("scheduling reminders…", "جاري الجدولة...")
content = content.replace("Reminders scheduled", "تمت جدولة التذكيرات")
content = content.replace("Arming overdue escalation…", "جاري تجهيز التصعيد...")
content = content.replace("reminders set ✓", "تم الجدولة ✓")
content = content.replace("Reminders set for", "تم ضبط التذكيرات لتاريخ")
content = content.replace("and", "و")
content = content.replace("Step 4 complete — reminders scheduled", "الخطوة 4 اكتملت — تمت الجدولة")
content = content.replace("arming escalation…", "تجهيز التصعيد...")
content = content.replace("Arming escalation", "تجهيز التصعيد")
content = content.replace("Configuring overdue manager alert…", "إعداد تنبيه المدير للتأخير...")
content = content.replace("escalation armed ✓", "تم تجهيز التصعيد ✓")
content = content.replace("Workflow complete", "اكتمل المسار")
content = content.replace("All 5 steps done — zero manual work", "الخطوات الـ 5 اكتملت — بدون عمل يدوي")
content = content.replace("Overdue alert armed — manager will be notified if unpaid after", "تنبيه التأخير جاهز — سيتم إخطار المدير في حال عدم الدفع بعد")
content = content.replace("complete ✓", "اكتمل ✓")
content = content.replace("all done ✓", "انتهى ✓")
content = content.replace("✓ All 5 steps complete — workflow done", "✓ اكتملت جميع الخطوات الخمس — انتهى المسار")

content = content.replace("Manager escalation armed", "تم تفعيل تصعيد المدير")
content = content.replace("If payment is not received by", "إذا لم يتم استلام الدفع بحلول")
content = content.replace(", your sales manager will automatically receive a WhatsApp message with the customer name, invoice number, amount, and days overdue. No one needs to remember to follow up.", "، سيتلقى مدير المبيعات تلقائياً رسالة واتساب باسم العميل ورقم الفاتورة والمبلغ وأيام التأخير. لا حاجة لأي شخص لتذكر المتابعة.")

with open('../public_html/medflow-sales-automation-demo-ar.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Arabic file created successfully.")
