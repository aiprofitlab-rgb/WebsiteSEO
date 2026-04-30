import os
import re

def standardize_file(file_path, lang='en'):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()

    # Define Unified Navigation HTML
    if lang == 'en':
        nav_html = """<!-- ======================= Navigation ======================= -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 fixed w-full z-50 glass bg-black/30">
        <a href="en.html" class="font-extrabold text-3xl md:text-4xl tracking-tighter">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        
        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center gap-8">
            <div class="desktop-nav-links">
                <a href="en.html">Home</a>
                <a href="services-en.html">Services</a>
                <a href="process-en.html">How It Works</a>
                
                <!-- Resources Dropdown -->
                <div class="relative group cursor-pointer h-full flex items-center">
                    <span class="hover:text-blue-400 transition flex items-center gap-1">
                        Resources
                        <svg class="w-4 h-4 transition-transform group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </span>
                    <div class="absolute top-full left-1/2 -translate-x-1/2 w-48 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 flex flex-col z-50">
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                Demo
                                <svg class="w-4 h-4 transform -rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="Customized_CEO_Dashboard_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">CEO Dashboard</a>
                                <a href="whatsapp_receptionist_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">WhatsApp Receptionist</a>
                            </div>
                        </div>
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                Simulators
                                <svg class="w-4 h-4 transform -rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="Missed-Call Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">Missed-Call Simulator</a>
                                <a href="Campaign_ROI_Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">Campaign ROI Simulator</a>
                            </div>
                        </div>
                        <a href="blog.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">Articles</a>
                        <a href="https://www.youtube.com/@AI_for_Managers" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">YouTube</a>
                        <a href="about-en.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">About</a>
                    </div>
                </div>
                
                <a href="contact-en.html">Contact</a>
            </div>
            <!-- Language Switch -->
            <a href="index.html" class="bg-blue-600/20 hover:bg-blue-600/30 text-white px-4 py-2 rounded-full text-sm font-bold transition border border-blue-500/30">
                العربية
            </a>
        </div>
        
        <!-- Mobile Controls -->
        <div class="mobile-controls md:hidden">
            <a href="index.html" class="bg-blue-600/20 text-white px-3 py-1 rounded-full text-xs font-bold border border-blue-500/30">
                عربي
            </a>
            <button id="mobileMenuToggle" class="text-white text-3xl focus:outline-none">☰</button>
        </div>
        
        <!-- Mobile Dropdown Menu -->
        <div id="mobileDropdownMenu" class="mobile-dropdown-menu">
            <a href="en.html">Home</a>
            <a href="services-en.html">Services</a>
            <a href="process-en.html">How It Works</a>
            
            <div class="flex flex-col text-center w-full py-2 bg-black/40 rounded-lg">
                <span class="text-xs text-gray-500 font-bold uppercase tracking-widest mb-2">Resources</span>
                <a href="Customized_CEO_Dashboard_demo.html" class="py-2 text-sm text-gray-300 border-none">CEO Dashboard</a>
                <a href="whatsapp_receptionist_demo.html" class="py-2 text-sm text-gray-300 border-none">WhatsApp Receptionist</a>
                <a href="Missed-Call Simulator.html" class="py-2 text-sm text-gray-300 border-none">Missed-Call Simulator</a>
                <a href="Campaign_ROI_Simulator.html" class="py-2 text-sm text-gray-300 border-none">Campaign ROI Simulator</a>
                <a href="blog.html" class="py-2 text-sm text-gray-300 border-none">Articles</a>
                <a href="about-en.html" class="py-2 text-sm text-gray-300 border-none">About</a>
            </div>
            
            <a href="contact-en.html">Contact</a>
            <a href="index.html" style="color: #3B82F6; font-weight: bold;">العربية</a>
        </div>
    </nav>"""
    else:
        nav_html = """<!-- ======================= Navigation ======================= -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 fixed w-full z-50 glass bg-black/30">
        <a href="index.html" class="font-extrabold text-3xl md:text-4xl tracking-tighter">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        
        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center gap-8">
            <div class="desktop-nav-links">
                <a href="index.html">الرئيسية</a>
                <a href="services.html">الخدمات</a>
                <a href="process.html">طريقتنا</a>
                
                <!-- Resources Dropdown -->
                <div class="relative group cursor-pointer h-full flex items-center">
                    <span class="hover:text-blue-400 transition flex items-center gap-1">
                        الموارد
                        <svg class="w-4 h-4 transition-transform group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </span>
                    <div class="absolute top-full left-1/2 -translate-x-1/2 w-48 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 flex flex-col z-50">
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                عروض تجريبية
                                <svg class="w-4 h-4 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="Customized_CEO_Dashboard_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">لوحة تحكم المدير</a>
                                <a href="whatsapp_receptionist_demo_ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">موظف استقبال واتساب</a>
                            </div>
                        </div>
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                محاكيات
                                <svg class="w-4 h-4 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="Missed-Call-Simulator-ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">محاكي المكالمات الفائتة</a>
                                <a href="Campaign_ROI_Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">محاكي عائد الحملات</a>
                            </div>
                        </div>
                        <a href="blog_ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">المقالات</a>
                        <a href="https://www.youtube.com/@AI_for_Managers" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">يوتيوب</a>
                        <a href="about.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">من نحن</a>
                    </div>
                </div>
                
                <a href="contact.html">اتصل بنا</a>
            </div>
            <!-- Language Switch -->
            <a href="en.html" class="bg-blue-600/20 hover:bg-blue-600/30 text-white px-4 py-2 rounded-full text-sm font-bold transition border border-blue-500/30">
                English
            </a>
        </div>
        
        <!-- Mobile Controls -->
        <div class="mobile-controls">
            <a href="en.html" class="bg-blue-600/30 text-white px-3 py-1.5 rounded-full text-sm font-bold border border-blue-500/40">
                EN
            </a>
            <button id="mobileMenuToggle" class="text-white text-3xl focus:outline-none leading-none" aria-label="القائمة">
                ☰
            </button>
        </div>
        
        <!-- Mobile Dropdown Menu -->
        <div id="mobileDropdownMenu" class="mobile-dropdown-menu">
            <a href="index.html" class="hover:text-blue-400 transition">الرئيسية</a>
            <a href="services.html" class="hover:text-blue-400 transition">الخدمات</a>
            <a href="process.html" class="hover:text-blue-400 transition">طريقتنا</a>
            
            <div class="flex flex-col text-center w-full py-2 bg-black/40 rounded-lg">
                <span class="text-xs text-gray-500 font-bold uppercase tracking-widest mb-2">الموارد</span>
                <a href="Customized_CEO_Dashboard_demo.html" class="py-2 text-sm text-gray-300 border-none">لوحة تحكم المدير</a>
                <a href="whatsapp_receptionist_demo_ar.html" class="py-2 text-sm text-gray-300 border-none">موظف استقبال واتساب</a>
                <a href="Missed-Call-Simulator-ar.html" class="py-2 text-sm text-gray-300 border-none">محاكي المكالمات الفائتة</a>
                <a href="Campaign_ROI_Simulator.html" class="py-2 text-sm text-gray-300 border-none">محاكي عائد الحملات</a>
                <a href="blog_ar.html" class="py-2 text-sm text-gray-300 border-none">المقالات</a>
                <a href="about.html" class="py-2 text-sm text-gray-300 border-none">من نحن</a>
            </div>
            
            <a href="contact.html" class="hover:text-blue-400 transition">اتصل بنا</a>
            <a href="en.html" style="color: #3B82F6; font-weight: bold;">English</a>
        </div>
    </nav>"""

    # Regex to find any existing nav block and replace it
    # We look for <nav class="..."> ... </nav> blocks that look like headers
    new_content = re.sub(r'<!-- ======================= Navigation ======================= -->.*?<nav.*?>.*?</nav>', nav_html, content, flags=re.DOTALL)
    
    # Fallback if the comment tag is missing
    if new_content == content:
        new_content = re.sub(r'<nav class="flex justify-between items-center.*?">.*?</nav>', nav_html, content, flags=re.DOTALL)

    # Also clean up any extra mobile dropdowns or menus
    new_content = re.sub(r'<!-- Mobile Dropdown Menu \(hidden by default\) -->.*?<div id="mobileMenuDropdown".*?>.*?</div>', '', new_content, flags=re.DOTALL)
    new_content = re.sub(r'<div class="nav-links mobile-menu">.*?</div>', '', new_content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    print(f"Standardized {file_path}")

# List of all pages to standardize
pages = [
    ('public_html/index.html', 'ar'),
    ('public_html/en.html', 'en'),
    ('public_html/services.html', 'ar'),
    ('public_html/services-en.html', 'en'),
    ('public_html/process.html', 'ar'),
    ('public_html/process-en.html', 'en'),
    ('public_html/contact.html', 'ar'),
    ('public_html/contact-en.html', 'en'),
    ('public_html/about.html', 'ar'),
    ('public_html/about-en.html', 'en'),
    ('public_html/blog.html', 'en'),
    ('public_html/blog_ar.html', 'ar')
]

for page, lang in pages:
    standardize_file(page, lang)
