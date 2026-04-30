import os
import re

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

CORE_PAGES = ["services.html", "services-en.html", "contact.html"]

def clean_and_fix(file_path):
    print(f"Final manual fix v2: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
    chat_pos = "left: 8px; right: auto;" if is_arabic else "right: 8px; left: auto;"
    font_family = "'Cairo', sans-serif" if is_arabic else "'Outfit', sans-serif"
    text_align = "right" if is_arabic else "left"

    clean_styles = f"""
    <style>
        body {{ font-family: {font_family}; background-color: #050505; color: #ffffff; margin: 0; overflow-x: hidden; }}
        .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }}
        .glass-card {{ background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }}
        .glass-card:hover {{ border-color: #3B82F6; transform: translateY(-5px); }}
        
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
        .pulse {{ animation: pulse-animation 2s infinite; }}
        @keyframes pulse-animation {{ 0% {{ box-shadow: 0 0 0 0px rgba(59, 130, 246, 0.4); }} 100% {{ box-shadow: 0 0 0 20px rgba(59, 130, 246, 0); }} }}
        
        /* Multi-step Form & Modal Styles */
        .form-modal-overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); z-index: 2000; display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s ease; }}
        .form-modal-overlay.active {{ display: flex; opacity: 1; }}
        .form-modal-content {{ width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 2.5rem; border-radius: 1.5rem; background: #0a0a0a; border: 1px solid rgba(255,255,255,0.1); position: relative; transform: scale(0.95); transition: transform 0.3s ease; }}
        .form-modal-overlay.active .form-modal-content {{ transform: scale(1); }}
        .close-btn {{ position: absolute; top: 20px; left: 20px; background: none; border: none; color: #aaa; font-size: 2rem; cursor: pointer; }}
        .progress-bar {{ display: flex; justify-content: space-between; margin-bottom: 2rem; max-width: 400px; margin: 0 auto 2rem; position: relative; }}
        .progress-bar::before {{ content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 2px; background: rgba(255,255,255,0.1); transform: translateY(-50%); z-index: 0; }}
        .progress-step {{ width: 35px; height: 35px; border-radius: 50%; background: #1a1a1a; border: 2px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; color: #fff; position: relative; z-index: 1; transition: all 0.3s; }}
        .progress-step.active {{ background: linear-gradient(135deg, #3B82F6, #22C55E); border-color: transparent; transform: scale(1.1); }}
        .form-step {{ display: none; }}
        .form-step.active {{ display: block; animation: fadeIn 0.5s; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        input, textarea, select {{ width: 100%; padding: 0.75rem 1rem; margin-bottom: 1rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; color: #fff; text-align: {text_align}; }}
        .checkbox-group {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-bottom: 1rem; }}
        .checkbox-item {{ background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 0.5rem; display: flex; align-items: center; cursor: pointer; border: 1px solid transparent; transition: all 0.2s; }}
        .checkbox-item:hover {{ background: rgba(59,130,246,0.1); border-color: #3B82F6; }}
        .nav-btn {{ padding: 0.75rem 2rem; border-radius: 0.5rem; font-weight: bold; cursor: pointer; transition: all 0.3s; }}
        .nav-btn.next, .nav-btn.submit {{ background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; }}
        .nav-btn.prev {{ background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.1); }}
    </style>
"""
    # Remove existing style blocks
    content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
    content = content.replace("</head>", clean_styles + "\n</head>")

    # 2. Fix Script Redundancy
    # Remove redundant toggleChat and window.onload blocks
    content = re.sub(r'function toggleChat\(.*?\).*?\}\s*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'// Unified Menu Logic.*?}\)\(\);', '', content, flags=re.DOTALL)
    content = re.sub(r'window\.onload = async.*?;', '', content, flags=re.DOTALL)
    
    final_js = f"""
    <script>
        // Chatbot & Menu Logic
        function toggleChat() {{ 
            const chat = document.getElementById('aiden-ui'); 
            if (!chat) return;
            chat.classList.toggle('active'); 
            if(chat.classList.contains('active')) {{ 
                const msgs = document.getElementById('chat-messages'); 
                const greeting = getPageSpecificGreeting(); 
                const welcomeMsg = document.getElementById('welcome-message')?.textContent || ''; 
                if(msgs && msgs.children.length === 1) {{
                    msgs.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tr-none max-w-[85%]">${{greeting}} <span class="block text-xs text-gray-500 mt-1">${{welcomeMsg}}</span></div>`; 
                }}
            }} 
        }}

        (function() {{
            const mobileToggleBtn = document.getElementById('mobileMenuToggle');
            const mobileMenuDropdown = document.getElementById('mobileDropdownMenu');
            if (mobileToggleBtn && mobileMenuDropdown) {{
                mobileToggleBtn.addEventListener('click', (e) => {{ e.stopPropagation(); mobileMenuDropdown.classList.toggle('open'); }});
                document.addEventListener('click', (e) => {{ if (!mobileToggleBtn.contains(e.target) && !mobileMenuDropdown.contains(e.target)) mobileMenuDropdown.classList.remove('open'); }});
                mobileMenuDropdown.querySelectorAll('a').forEach(link => {{ link.addEventListener('click', () => mobileMenuDropdown.classList.remove('open')); }});
            }}
        }})();

        window.onload = async () => {{ 
            if (typeof detectCountry === 'function') await detectCountry(); 
            if(!sessionStorage.getItem('aidenPopped')) {{ 
                setTimeout(() => {{ 
                    const chat = document.getElementById('aiden-ui'); 
                    if(chat && !chat.classList.contains('active')) {{ 
                        toggleChat(); 
                        sessionStorage.setItem('aidenPopped','true'); 
                    }} 
                }}, 10000); 
            }} 
        }};
    </script>
"""
    if "</body>" in content:
        content = content.replace("</body>", final_js + "\n</body>")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for page in CORE_PAGES:
    path = os.path.join(BASE_DIR, page)
    if os.path.exists(path):
        clean_and_fix(path)

print("Core pages fixed v2.")
