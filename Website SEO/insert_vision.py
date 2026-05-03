# -*- coding: utf-8 -*-
import os

en_insert = '''
    <!-- ======================= Vision 2040 & Decree Section ======================= -->
    <section id="vision" class="py-24 px-4 border-t border-gray-900 bg-[#050505] overflow-hidden" itemscope itemtype="https://schema.org/GovernmentService">
        <meta itemprop="provider" content="AI Profit Lab">
        <meta itemprop="serviceArea" content="Muscat, Oman">
        <div class="max-w-6xl mx-auto">
            <div class="flex flex-col lg:flex-row items-center gap-16">
                <div class="lg:w-1/2">
                    <h2 class="text-4xl font-black mb-6 leading-tight">
                        Powering the <br><span class="text-blue-500">Muscat AI Special Zone</span>
                    </h2>
                    <p class="text-gray-400 text-lg mb-8 leading-relaxed" itemprop="description">
                        Following the landmark <strong>Royal Decree 50/2026</strong>, Muscat has emerged as the GCC's hub for technological breakout. <strong>AI Profit Lab</strong> provides the technical bridge for local and expat companies to integrate into this new economic ecosystem.
                    </p>
                    
                    <ul class="space-y-4">
                        <li class="flex items-start gap-4">
                            <div class="bg-blue-500/20 p-2 rounded-lg mt-1"><svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg></div>
                            <div>
                                <p class="font-bold text-white">Vision 2040 Compliance</p>
                                <p class="text-sm text-gray-500">Our automation stacks are designed to meet the digital KPI targets set by the Omani government.</p>
                            </div>
                        </li>
                        <li class="flex items-start gap-4">
                            <div class="bg-green-500/20 p-2 rounded-lg mt-1"><svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg></div>
                            <div>
                                <p class="font-bold text-white">In-Country Value (ICV)</p>
                                <p class="text-sm text-gray-500">We prioritize the development of local AI talent and Omani business scaling through automated infrastructure.</p>
                            </div>
                        </li>
                    </ul>
                </div>
                
                <div class="lg:w-1/2 relative">
                    <!-- Visual Representation of the Decree/Zone -->
                    <div class="glass-card p-8 rounded-3xl border-blue-500/30 bg-gradient-to-br from-blue-600/10 to-transparent relative z-10">
                        <div class="flex justify-between items-start mb-6">
                            <span class="text-xs font-bold text-blue-400 tracking-widest uppercase" itemprop="areaServed">Legislative Alignment</span>
                            <span class="text-xs text-gray-500">Muscat, OM</span>
                        </div>
                        <h3 class="text-2xl font-bold text-white mb-4" itemprop="name">Decree 50/2026 Readiness</h3>
                        <p class="text-gray-400 text-sm mb-6">We provide "Sandboxed" AI testing environments that comply with the regulatory frameworks of the new Special Zone.</p>
                        
                        <div class="space-y-3">
                            <div class="h-2 w-full bg-gray-800 rounded-full overflow-hidden"><div class="h-full bg-blue-500 w-[95%]"></div></div>
                            <div class="flex justify-between text-[10px] font-bold text-gray-500">
                                <span>REGULATORY COMPLIANCE</span>
                                <span>95%</span>
                            </div>
                        </div>
                    </div>
                    <!-- Decorative Glow -->
                    <div class="absolute -top-10 -right-10 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full"></div>
                </div>
            </div>
        </div>
    </section>
'''

ar_insert = '''
    <!-- ======================= Vision 2040 & Decree Section ======================= -->
    <section id="vision" class="py-24 px-4 border-t border-gray-900 bg-[#050505] overflow-hidden" dir="rtl" itemscope itemtype="https://schema.org/GovernmentService">
        <meta itemprop="provider" content="AI Profit Lab">
        <meta itemprop="serviceArea" content="مسقط، عمان">
        <div class="max-w-6xl mx-auto">
            <div class="flex flex-col lg:flex-row items-center gap-16">
                <div class="lg:w-1/2 text-right">
                    <h2 class="text-4xl font-black mb-6 leading-tight">
                        تمكين <br><span class="text-blue-500">منطقة الذكاء الاصطناعي بمسقط</span>
                    </h2>
                    <p class="text-gray-400 text-lg mb-8 leading-relaxed" itemprop="description">
                        إثر <strong>المرسوم السلطاني التاريخي 50/2026</strong>، برزت مسقط كمركز لدول مجلس التعاون الخليجي للانطلاقة التكنولوجية. يوفر <strong>AI Profit Lab</strong> الجسر التقني للشركات المحلية والأجنبية للاندماج في هذا النظام الاقتصادي الجديد.
                    </p>
                    
                    <ul class="space-y-4">
                        <li class="flex items-start gap-4">
                            <div class="bg-blue-500/20 p-2 rounded-lg mt-1"><svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg></div>
                            <div>
                                <p class="font-bold text-white">التوافق مع رؤية عمان 2040</p>
                                <p class="text-sm text-gray-500">تم تصميم أنظمة الأتمتة لدينا لتلبية أهداف مؤشرات الأداء الرقمية التي حددتها الحكومة العمانية.</p>
                            </div>
                        </li>
                        <li class="flex items-start gap-4">
                            <div class="bg-green-500/20 p-2 rounded-lg mt-1"><svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg></div>
                            <div>
                                <p class="font-bold text-white">القيمة المحلية المضافة (ICV)</p>
                                <p class="text-sm text-gray-500">نحن نعطي الأولوية لتطوير مواهب الذكاء الاصطناعي المحلية وتوسيع نطاق الأعمال العمانية من خلال البنية التحتية المؤتمتة.</p>
                            </div>
                        </li>
                    </ul>
                </div>
                
                <div class="lg:w-1/2 relative text-right">
                    <!-- Visual Representation of the Decree/Zone -->
                    <div class="glass-card p-8 rounded-3xl border-blue-500/30 bg-gradient-to-bl from-blue-600/10 to-transparent relative z-10">
                        <div class="flex justify-between items-start mb-6" dir="ltr">
                            <span class="text-xs text-gray-500">Muscat, OM</span>
                            <span class="text-xs font-bold text-blue-400 tracking-widest uppercase" itemprop="areaServed">التوافق التشريعي</span>
                        </div>
                        <h3 class="text-2xl font-bold text-white mb-4" itemprop="name">الجاهزية للمرسوم 50/2026</h3>
                        <p class="text-gray-400 text-sm mb-6">نحن نقدم بيئات اختبار الذكاء الاصطناعي "الرملية" التي تتوافق مع الأطر التنظيمية للمنطقة الخاصة الجديدة.</p>
                        
                        <div class="space-y-3">
                            <div class="h-2 w-full bg-gray-800 rounded-full overflow-hidden" dir="ltr"><div class="h-full bg-blue-500 w-[95%]"></div></div>
                            <div class="flex justify-between text-[10px] font-bold text-gray-500" dir="ltr">
                                <span>REGULATORY COMPLIANCE</span>
                                <span>95%</span>
                            </div>
                        </div>
                    </div>
                    <!-- Decorative Glow -->
                    <div class="absolute -top-10 -left-10 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full"></div>
                </div>
            </div>
        </div>
    </section>
'''

# Update en.html
try:
    with open('public_html/en.html', 'r', encoding='utf-8') as f:
        en_content = f.read()
    
    if "Muscat AI Special Zone" not in en_content:
        # Insert before Quick Comparison
        target_en = '    <!-- ======================= Quick Comparison ======================= -->'
        en_content = en_content.replace(target_en, en_insert + '\n' + target_en)
        
        with open('public_html/en.html', 'w', encoding='utf-8') as f:
            f.write(en_content)
        print("Successfully updated en.html")
except Exception as e:
    print(f"Error with en.html: {e}")

# Update index.html
try:
    with open('public_html/index.html', 'r', encoding='utf-8') as f:
        ar_content = f.read()
        
    if "منطقة الذكاء الاصطناعي بمسقط" not in ar_content:
        # Insert before the Quick Comparison equivalent section
        target_ar = '    <section class="py-16 px-4 bg-[#0a0a0a]">'
        # Find the first occurrence right after the Hero
        parts = ar_content.split(target_ar, 1)
        if len(parts) == 2:
            ar_content = parts[0] + ar_insert + '\n' + target_ar + parts[1]
            
            with open('public_html/index.html', 'w', encoding='utf-8') as f:
                f.write(ar_content)
            print("Successfully updated index.html")
        else:
            print("Target not found in index.html")
except Exception as e:
    print(f"Error with index.html: {e}")
