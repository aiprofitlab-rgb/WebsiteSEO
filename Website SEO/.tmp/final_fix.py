import os
import re

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

PAGES = [
    "index.html", "services.html", "contact.html", "about.html", 
    "process.html", "blog_ar.html", "academy_ar.html",
    "en.html", "services-en.html", "contact-en.html", "about-en.html", 
    "process-en.html", "blog.html", "academy.html"
]

def fix_file(file_path):
    print(f"Fixing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix the destroyed script structure (syntax errors in toggleChat)
    # The bad code looks like: if(msgs.children.length === 1) msgs.innerHTML = `...greeting... // Unified Menu Logic ...welcomeMsg...`;
    # We need to restore the correct toggleChat function.
    
    correct_toggle_chat = """
        function toggleChat() { 
            const chat = document.getElementById('aiden-ui'); 
            if (!chat) return;
            chat.classList.toggle('active'); 
            if(chat.classList.contains('active')) { 
                const msgs = document.getElementById('chat-messages'); 
                const greeting = getPageSpecificGreeting(); 
                const welcomeMsg = document.getElementById('welcome-message')?.textContent || ''; 
                if(msgs && msgs.children.length === 1) {
                    msgs.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tr-none max-w-[85%]">${greeting} <span class="block text-xs text-gray-500 mt-1">${welcomeMsg}</span></div>`; 
                }
            } 
        }
"""
    
    # Identify the broken function block and replace it
    # This regex is broad enough to catch the mess
    content = re.sub(r'function toggleChat\(.*?\).*?msgs\.innerHTML = `.*?welcomeMsg.*?`;\s*\}\s*\}', correct_toggle_chat, content, flags=re.DOTALL)

    # 2. Fix Unified Menu Logic (ensure it exists once and in a clean script block)
    menu_js = """
    // Unified Menu Logic
    (function() {
        const mobileToggleBtn = document.getElementById('mobileMenuToggle');
        const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
        if (mobileToggleBtn && mobileMenuDropdown) {
            mobileToggleBtn.addEventListener('click', (e) => { e.stopPropagation(); mobileMenuDropdown.classList.toggle('open'); });
            document.addEventListener('click', (e) => { if (!mobileToggleBtn.contains(e.target) && !mobileMenuDropdown.contains(e.target)) mobileMenuDropdown.classList.remove('open'); });
            mobileMenuDropdown.querySelectorAll('a').forEach(link => { link.addEventListener('click', () => mobileMenuDropdown.classList.remove('open')); });
        }
    })();
"""
    # Remove any existing injected menu logic to avoid duplicates
    content = re.sub(r'// Unified Menu Logic.*?}\)\(\);', '', content, flags=re.DOTALL)
    content = re.sub(r'// Unified Menu Logic.*?}\s*$', '', content, flags=re.MULTILINE | re.DOTALL) # Catch non-IIFE versions
    
    # Inject it before </body> in a fresh script block
    if "</body>" in content:
        content = content.replace("</body>", f"<script>{menu_js}</script>\n</body>")

    # 3. Fix CSS mess (stray braces and missing styles)
    # Remove any broken "FIXED: UNIFIED NAVIGATION STYLES" blocks
    content = re.sub(r'/\* ========== FIXED: UNIFIED NAVIGATION STYLES ========== \*/.*?@media \(min-width: 768px\) \{.*?\}', '', content, flags=re.DOTALL)
    # Remove the stray braces block my previous script left
    content = re.sub(r'\s*\.mobile-controls \{ display: none !important; \}.*?\.group-submenu:hover \.submenu-content \{ opacity: 1; visibility: visible; \}\s*}', '', content, flags=re.DOTALL)
    content = re.sub(r'\s*\.mobile-controls \{\s*display: none !important;\s*\}\s*\.mobile-dropdown-menu \{\s*display: none !important;\s*\}\s*}', '', content, flags=re.DOTALL)

    is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
    chat_pos = "left: 8px; right: auto;" if is_arabic else "right: 8px; left: auto;"

    clean_styles = f"""
    <style>
        /* ========== CLEAN UNIFIED NAVIGATION STYLES ========== */
        .desktop-menu-container {{ display: none; }}
        .mobile-controls {{ display: flex; align-items: center; gap: 1rem; }}
        .mobile-dropdown-menu {{
            display: none; position: absolute; top: 100%; left: 0; right: 0;
            background-color: #0a0a0a; padding: 1.25rem; flex-direction: column; gap: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); z-index: 1000;
        }}
        .mobile-dropdown-menu a {{ padding: 0.75rem 0; text-align: center; font-weight: 600; font-size: 1.1rem; border-bottom: 1px solid rgba(255,255,255,0.08); transition: color 0.2s; }}
        .mobile-dropdown-menu.open {{ display: flex; }}
        .desktop-nav-links {{ display: flex; gap: 2rem; align-items: center; }}
        .desktop-nav-links a {{ font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; transition: color 0.2s; }}
        .group-submenu:hover .submenu-content {{ opacity: 1; visibility: visible; }}
        @media (min-width: 768px) {{
            .desktop-menu-container {{ display: block; }}
            .mobile-controls {{ display: none !important; }}
            .mobile-dropdown-menu {{ display: none !important; }}
        }}
        
        /* Chatbot Fixes */
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
            transform: translateY(0) !important; 
            visibility: visible !important; 
        }}
    </style>
"""
    if "</head>" in content:
        content = content.replace("</head>", f"{clean_styles}\n</head>")

    # 4. Fix broken JSON-LD schema (missing closing braces)
    if '"geo": {' in content and '/* ========== UNIFIED NAVIGATION STYLES ==========' in content:
        # We need to restore the geo coordinates and closing braces
        geo_fix = """
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
    </script>
"""
        # Replace the broken part
        content = re.sub(r'"geo": \{\s*/\* ========== UNIFIED NAVIGATION STYLES ==========', geo_fix + "\n/* ========== UNIFIED NAVIGATION STYLES ==========", content, flags=re.DOTALL)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for page in PAGES:
    path = os.path.join(BASE_DIR, page)
    if os.path.exists(path):
        fix_file(path)

print("Final fix complete.")
