import os
import re

# ======================== CONFIGURATION ========================

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

PAGES = [
    "index.html", "services.html", "contact.html", "about.html", 
    "process.html", "blog_ar.html", "academy_ar.html",
    "en.html", "services-en.html", "contact-en.html", "about-en.html", 
    "process-en.html", "blog.html", "academy.html"
]

def repair_file(file_path):
    print(f"Repairing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix Broken CSS blocks
    # Remove redundant/broken navigation style blocks
    content = re.sub(r'/\* ========== FIXED: UNIFIED NAVIGATION STYLES ========== \*/.*?@media \(min-width: 768px\) \{.*?\}', '', content, flags=re.DOTALL)
    # Remove stray braces and duplicate blocks
    content = re.sub(r'\.mobile-controls \{ display: none !important; \}.*?\.group-submenu:hover \.submenu-content \{ opacity: 1; visibility: visible; \}', '', content, flags=re.DOTALL)
    
    # Re-inject CLEAN Navigation Styles into <head>
    nav_styles = """
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
    if "</head>" in content:
        # First remove any old ones again to be safe
        content = re.sub(r'<style>\s*/\* ========== FIXED: UNIFIED NAVIGATION STYLES ========== \*/.*?</style>', '', content, flags=re.DOTALL)
        content = content.replace("</head>", f"<style>{nav_styles}</style>\n</head>")

    # 2. Fix Chatbot CSS
    # Ensure #aiden-ui has correct positioning for AR/EN
    is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
    chat_pos = "left: 8px; right: auto;" if is_arabic else "right: 8px; left: auto;"
    
    chatbot_css = f"""
        #aiden-ui {{ 
            transform: translateY(120%); 
            transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1); 
            visibility: hidden; 
            z-index: 1000; 
            position: absolute;
            bottom: 6rem;
            {chat_pos}
        }}
        #aiden-ui.active {{ 
            transform: translateY(0); 
            visibility: visible; 
        }}
"""
    # Replace existing #aiden-ui styles if found
    content = re.sub(r'#aiden-ui \{.*?\}', chatbot_css, content, flags=re.DOTALL)
    content = re.sub(r'#aiden-ui\.active \{.*?\}', '', content, flags=re.DOTALL) # Clean up separate active block if exists

    # 3. Fix Redundant Scripts
    # Remove duplicate navigation scripts
    content = re.sub(r'<!-- ======================= NAVIGATION SCRIPT ======================= -->.*?<script>.*?</script>', '', content, flags=re.DOTALL)
    
    # Ensure the main script block has the menu logic if it doesn't already
    menu_js = """
        // Unified Menu Logic
        const mobileToggleBtn = document.getElementById('mobileMenuToggle');
        const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
        if (mobileToggleBtn && mobileMenuDropdown) {
            mobileToggleBtn.addEventListener('click', (e) => { e.stopPropagation(); mobileMenuDropdown.classList.toggle('open'); });
            document.addEventListener('click', (e) => { if (!mobileToggleBtn.contains(e.target) && !mobileMenuDropdown.contains(e.target)) mobileMenuDropdown.classList.remove('open'); });
            mobileMenuDropdown.querySelectorAll('a').forEach(link => { link.addEventListener('click', () => mobileMenuDropdown.classList.remove('open')); });
        }
"""
    if "</script>" in content:
        # Try to find the last script block or the one containing chatbot logic
        if "toggleChat" in content:
            # Inject into the existing script block before the closing tag
            content = re.sub(r'(function toggleChat\(.*?\s*\{.*?\})', r'\1\n' + menu_js, content, flags=re.DOTALL)
        else:
            # Inject as a new script block
            content = content.replace("</body>", f"<script>{menu_js}</script>\n</body>")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for page in PAGES:
    path = os.path.join(BASE_DIR, page)
    if os.path.exists(path):
        repair_file(path)

print("Repair complete.")
