import os
import re

# ======================== CONFIGURATION ========================

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

EN_PAGES = [
    "en.html", "services-en.html", "contact-en.html", "about-en.html", 
    "process-en.html", "blog.html", "academy.html"
]

AR_PAGES = [
    "index.html", "services.html", "contact.html", "about.html", 
    "process.html", "blog_ar.html", "academy_ar.html"
]

# Styles block to inject
NAV_STYLES = """
        /* ========== FIXED: UNIFIED NAVIGATION STYLES ========== */
        .desktop-menu-container { display: none; }
        .mobile-controls { display: flex; align-items: center; gap: 1rem; }
        .mobile-dropdown-menu {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background-color: #0a0a0a;
            padding: 1.25rem;
            flex-direction: column;
            gap: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1);
            border-bottom: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .mobile-dropdown-menu a { padding: 0.75rem 0; text-align: center; font-weight: 600; font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.08); transition: color 0.2s; }
        .mobile-dropdown-menu a:last-child { border-bottom: none; }
        .mobile-dropdown-menu a:hover { color: #60a5fa; }
        .mobile-dropdown-menu.open { display: flex; }
        .desktop-nav-links { display: flex; gap: 2rem; align-items: center; }
        .desktop-nav-links a { font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; transition: color 0.2s; }
        .desktop-nav-links a:hover { color: #3b82f6; }
        @media (min-width: 768px) {
            .desktop-menu-container { display: block; }
            .mobile-controls { display: none !important; }
            .mobile-dropdown-menu { display: none !important; }
        }
        .group-submenu:hover .submenu-content { opacity: 1; visibility: visible; }
"""

# Script block to inject
NAV_SCRIPT = """
    <!-- ======================= NAVIGATION SCRIPT ======================= -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const mobileToggleBtn = document.getElementById('mobileMenuToggle');
            const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
            if (mobileToggleBtn && mobileMenuDropdown) {
                mobileToggleBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    mobileMenuDropdown.classList.toggle('open');
                });
                
                document.addEventListener('click', function(event) {
                    if (!mobileToggleBtn.contains(event.target) && !mobileMenuDropdown.contains(event.target)) {
                        mobileMenuDropdown.classList.remove('open');
                    }
                });
                
                // Close menu when clicking any link inside
                mobileMenuDropdown.querySelectorAll('a').forEach(link => {
                    link.addEventListener('click', () => {
                        mobileMenuDropdown.classList.remove('open');
                    });
                });
            }
        });
    </script>
"""

# Header HTML Templates
EN_NAV_TEMPLATE = """
    <!-- ======================= FIXED: SINGLE NAVIGATION SYSTEM ======================= -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-6 fixed w-full z-50 glass bg-black/40 backdrop-blur-md">
        <!-- Logo -->
        <a href="{rel}en.html" class="font-extrabold text-3xl md:text-4xl tracking-tighter">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        
        <!-- DESKTOP MENU -->
        <div class="desktop-menu-container">
            <div class="desktop-nav-links flex items-center gap-6 text-sm font-bold uppercase">
                <a href="{rel}en.html" class="hover:text-blue-400 transition">Home</a>
                <a href="{rel}services-en.html" class="hover:text-blue-400 transition">Services</a>
                <a href="{rel}process-en.html" class="hover:text-blue-400 transition">How It Works</a>
                
                <!-- Resources Dropdown -->
                <div class="relative group cursor-pointer h-full flex items-center">
                    <span class="hover:text-blue-400 transition flex items-center gap-1">
                        Resources
                        <svg class="w-4 h-4 transition-transform group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </span>
                    <div class="absolute top-8 left-1/2 -translate-x-1/2 w-48 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 flex flex-col z-50">
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                Demo
                                <svg class="w-4 h-4 transform -rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="{rel}Customized_CEO_Dashboard_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">CEO Dashboard</a>
                                <a href="{rel}whatsapp_receptionist_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">WhatsApp Receptionist</a>
                            </div>
                        </div>
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                Simulators
                                <svg class="w-4 h-4 transform -rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute left-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50">
                                <a href="{rel}Missed-Call Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">Missed-Call Simulator</a>
                                <a href="{rel}Campaign_ROI_Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">ROI Simulator</a>
                            </div>
                        </div>
                        <a href="{rel}blog.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">Articles</a>
                        <a href="{rel}academy.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">YouTube</a>
                        <a href="{rel}about-en.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">About</a>
                    </div>
                </div>
                
                <a href="{rel}contact-en.html" class="hover:text-blue-400 transition">Contact</a>
                <a href="{rel}index.html" class="bg-blue-600/30 hover:bg-blue-600/50 text-white px-5 py-2 rounded-full text-sm font-bold transition border border-blue-500/40 shadow-sm ml-2">
                    العربية
                </a>
            </div>
        </div>
        
        <!-- MOBILE CONTROLS -->
        <div class="mobile-controls">
            <a href="{rel}index.html" class="bg-blue-600/30 text-white px-3 py-1.5 rounded-full text-sm font-bold border border-blue-500/40">
                AR
            </a>
            <button id="mobileMenuToggle" class="text-white text-3xl focus:outline-none leading-none">
                ☰
            </button>
        </div>
        
        <!-- MOBILE DROPDOWN MENU -->
        <div id="mobileDropdownMenu" class="mobile-dropdown-menu">
            <a href="{rel}en.html">Home</a>
            <a href="{rel}services-en.html">Services</a>
            <a href="{rel}process-en.html">How It Works</a>
            
            <div class="flex flex-col text-center w-full py-2 bg-black/40 rounded-lg">
                <span class="text-xs text-gray-500 font-bold uppercase tracking-widest mb-2">Resources</span>
                <a href="{rel}blog.html" class="py-1.5 text-sm text-gray-300 border-none">Articles</a>
                <a href="{rel}academy.html" class="py-1.5 text-sm text-gray-300 border-none">YouTube</a>
                <a href="{rel}about-en.html" class="py-1.5 text-sm text-gray-300 border-none">About</a>
            </div>
            
            <a href="{rel}contact-en.html">Contact</a>
        </div>
    </nav>
"""

AR_NAV_TEMPLATE = """
    <!-- ======================= FIXED: SINGLE NAVIGATION SYSTEM ======================= -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-6 fixed w-full z-50 glass bg-black/40 backdrop-blur-md">
        <!-- Logo -->
        <a href="{rel}index.html" class="font-extrabold text-3xl md:text-4xl tracking-tighter">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        
        <!-- DESKTOP MENU -->
        <div class="desktop-menu-container">
            <div class="desktop-nav-links flex items-center gap-6 text-sm font-bold uppercase">
                <a href="{rel}index.html" class="hover:text-blue-400 transition">الرئيسية</a>
                <a href="{rel}services.html" class="hover:text-blue-400 transition">الخدمات</a>
                <a href="{rel}process.html" class="hover:text-blue-400 transition">طريقتنا</a>
                
                <!-- Resources Dropdown -->
                <div class="relative group cursor-pointer h-full flex items-center">
                    <span class="hover:text-blue-400 transition flex items-center gap-1">
                        الموارد
                        <svg class="w-4 h-4 transition-transform group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </span>
                    <div class="absolute top-8 right-1/2 translate-x-1/2 w-48 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 flex flex-col z-50">
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                العروض التجريبية
                                <svg class="w-4 h-4 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute right-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50 text-right">
                                <a href="{rel}Customized_CEO_Dashboard_demo.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">لوحة تحكم المدير التنفيذي</a>
                                <a href="{rel}whatsapp_receptionist_demo_ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">موظف استقبال واتساب</a>
                            </div>
                        </div>
                        <div class="relative group-submenu">
                            <div class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition flex justify-between items-center cursor-pointer text-[15px] font-bold tracking-wide">
                                المحاكيات
                                <svg class="w-4 h-4 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                            </div>
                            <div class="submenu-content absolute right-full top-0 w-64 bg-[#0a0a0a] border border-gray-800 rounded-xl shadow-2xl opacity-0 invisible transition-all duration-300 flex flex-col z-50 text-right">
                                <a href="{rel}Missed-Call-Simulator-ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">محاكي المكالمات الفائتة</a>
                                <a href="{rel}Campaign_ROI_Simulator.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">محاكي عائد الحملات</a>
                            </div>
                        </div>
                        <a href="{rel}blog_ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">المقالات</a>
                        <a href="{rel}academy_ar.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 border-b border-gray-800 transition text-[15px] font-bold tracking-wide">اليوتيوب</a>
                        <a href="{rel}about.html" class="px-5 py-4 hover:bg-gray-800 hover:text-blue-400 transition text-[15px] font-bold tracking-wide">حولنا</a>
                    </div>
                </div>
                
                <a href="{rel}contact.html" class="hover:text-blue-400 transition">اتصل بنا</a>
                <a href="{rel}en.html" class="bg-blue-600/30 hover:bg-blue-600/50 text-white px-5 py-2 rounded-full text-sm font-bold transition border border-blue-500/40 shadow-sm mr-2">
                    English
                </a>
            </div>
        </div>
        
        <!-- MOBILE CONTROLS -->
        <div class="mobile-controls">
            <a href="{rel}en.html" class="bg-blue-600/30 text-white px-3 py-1.5 rounded-full text-sm font-bold border border-blue-500/40">
                EN
            </a>
            <button id="mobileMenuToggle" class="text-white text-3xl focus:outline-none leading-none">
                ☰
            </button>
        </div>
        
        <!-- MOBILE DROPDOWN MENU -->
        <div id="mobileDropdownMenu" class="mobile-dropdown-menu">
            <a href="{rel}index.html">الرئيسية</a>
            <a href="{rel}services.html">الخدمات</a>
            <a href="{rel}process.html">طريقتنا</a>
            
            <div class="flex flex-col text-center w-full py-2 bg-black/40 rounded-lg">
                <span class="text-xs text-gray-500 font-bold uppercase tracking-widest mb-2">الموارد</span>
                <a href="{rel}blog_ar.html" class="py-1.5 text-sm text-gray-300 border-none">المقالات</a>
                <a href="{rel}academy_ar.html" class="py-1.5 text-sm text-gray-300 border-none">اليوتيوب</a>
                <a href="{rel}about.html" class="py-1.5 text-sm text-gray-300 border-none">حولنا</a>
            </div>
            
            <a href="{rel}contact.html">اتصل بنا</a>
        </div>
    </nav>
"""

def update_file(file_path, is_arabic):
    print(f"Updating: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Determine relative path correctly
    rel_path = os.path.relpath(os.path.dirname(file_path), BASE_DIR)
    if rel_path == ".":
        rel = ""
    else:
        # Count segments
        rel = "../" * (rel_path.count(os.sep) + 1)

    # 1. Replace Styles
    if "/* ========== FIXED: UNIFIED NAVIGATION STYLES ========== */" in content:
        # Already has unified styles, replace the whole block
        content = re.sub(r'/\* ========== FIXED: UNIFIED NAVIGATION STYLES ========== \*/.*?@media \(min-width: 768px\) \{.*?\}', NAV_STYLES, content, flags=re.DOTALL)
    else:
        # Inject into head style block or create one
        if "</head>" in content:
            style_injection = f"<style>{NAV_STYLES}</style>\n"
            content = content.replace("</head>", f"{style_injection}</head>")

    # 2. Replace Nav Tag
    nav_html = AR_NAV_TEMPLATE.format(rel=rel) if is_arabic else EN_NAV_TEMPLATE.format(rel=rel)
    # Target common nav patterns
    content = re.sub(r'<nav.*?</nav>', nav_html, content, flags=re.DOTALL)

    # 3. Replace/Inject Script
    if "<!-- ======================= NAVIGATION SCRIPT ======================= -->" in content:
        content = re.sub(r'<!-- ======================= NAVIGATION SCRIPT ======================= -->.*?<script>.*?</script>', NAV_SCRIPT, content, flags=re.DOTALL)
    else:
        # Inject before </body>
        if "</body>" in content:
            content = content.replace("</body>", f"{NAV_SCRIPT}</body>")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Main execution
for page in EN_PAGES:
    path = os.path.join(BASE_DIR, page)
    if os.path.exists(path):
        update_file(path, False)

for page in AR_PAGES:
    path = os.path.join(BASE_DIR, page)
    if os.path.exists(path):
        update_file(path, True)

# Update Blog Articles
BLOG_EN_DIR = os.path.join(BASE_DIR, "blog/en")
BLOG_AR_DIR = os.path.join(BASE_DIR, "blog/ar")

if os.path.exists(BLOG_EN_DIR):
    for f in os.listdir(BLOG_EN_DIR):
        if f.endswith(".html"):
            update_file(os.path.join(BLOG_EN_DIR, f), False)

if os.path.exists(BLOG_AR_DIR):
    for f in os.listdir(BLOG_AR_DIR):
        if f.endswith(".html"):
            update_file(os.path.join(BLOG_AR_DIR, f), True)

print("Standardization complete.")
