import os
import re

def restore_aesthetics(file_path, lang='en'):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()

    # Unified CSS with ALL closing braces
    font_family = "'Cairo', sans-serif" if lang == 'ar' else "'Outfit', sans-serif"
    
    css_content = f"""
        /* ========== UNIFIED NAVIGATION STYLES ========== */
        .desktop-menu-container {{ display: none; }}
        .mobile-controls {{ display: flex; align-items: center; gap: 1rem; }}
        .mobile-dropdown-menu {{
            display: none; position: absolute; top: 100%; left: 0; right: 0;
            background-color: #0a0a0a; padding: 1.25rem; flex-direction: column; gap: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); z-index: 1000;
        }}
        .mobile-dropdown-menu a {{
            padding: 0.75rem 0; text-align: center; font-weight: 600; font-size: 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08); transition: color 0.2s;
        }}
        .mobile-dropdown-menu a:last-child {{ border-bottom: none; }}
        .mobile-dropdown-menu a:hover {{ color: #60a5fa; }}
        .mobile-dropdown-menu.open {{ display: flex; }}
        .desktop-nav-links {{ display: flex; gap: 2rem; align-items: center; }}
        .desktop-nav-links a {{ font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; transition: color 0.2s; }}
        .desktop-nav-links a:hover {{ color: #3b82f6; }}
        @media (min-width: 768px) {{
            .desktop-menu-container {{ display: block !important; }}
            .mobile-controls {{ display: none !important; }}
            .mobile-dropdown-menu {{ display: none !important; }}
        }}

        /* ========== NAV SUBMENU FIX ========== */
        .group-submenu:hover .submenu-content {{ opacity: 1 !important; visibility: visible !important; }}
        @media (min-width: 768px) {{
            .submenu-content {{ left: 100% !important; top: 0 !important; }}
        }}

        /* ========== CORE AESTHETICS ========== */
        body {{ font-family: {font_family}; background-color: #050505; color: #ffffff; margin: 0; overflow-x: hidden; }}
        .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }}
        .glass-card {{ background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }}
        .glass-card:hover {{ border-color: #3B82F6; transform: translateY(-5px); }}

        /* ========== USER CUSTOM DESIGNS (RESTORED) ========== */
        .comparison-table {{ border-collapse: separate; border-spacing: 0 8px; width: 100%; }}
        .comparison-table th {{ background: rgba(59, 130, 246, 0.1); padding: 1rem; font-weight: 700; text-align: left; }}
        .comparison-table td {{ padding: 1rem; background: rgba(255, 255, 255, 0.02); border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}
        .comparison-table tr:hover td {{ background: rgba(59, 130, 246, 0.05); }}
        
        .addon-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 1rem; padding: 1.5rem; transition: all 0.3s ease; height: 100%; }}
        .addon-card:hover {{ border-color: #3B82F6; transform: translateY(-5px); box-shadow: 0 10px 30px rgba(59, 130, 246, 0.1); }}
        .addon-title {{ font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; color: #3B82F6; }}
        .addon-price {{ font-size: 1.3rem; font-weight: bold; color: #22C55E; margin-bottom: 0.75rem; }}
        .addon-price span {{ font-size: 0.9rem; font-weight: normal; color: #9CA3AF; }}
        .addon-desc {{ color: #9CA3AF; font-size: 0.9rem; line-height: 1.6; }}
        .addon-desc strong {{ color: white; }}

        .why-ai-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 1rem; padding: 1.5rem; transition: all 0.3s; }}
        .why-ai-card:hover {{ border-color: #3B82F6; background: rgba(59, 130, 246, 0.03); }}

        .product-card {{ background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 1rem; padding: 1.5rem; transition: all 0.3s ease; display: flex; flex-direction: column; gap: 0.75rem; }}
        .product-card:hover {{ border-color: #22C55E; transform: translateY(-4px); box-shadow: 0 10px 30px rgba(34, 197, 94, 0.08); }}

        /* ========== CHATBOT STYLES ========== */
        #aiden-ui {{ transform: translateY(120%); transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1); visibility: hidden; z-index: 1000; right: 8px; left: auto; }}
        #aiden-ui.active {{ transform: translateY(0); visibility: visible; }}
        .pulse {{ animation: pulse-animation 2s infinite; }}
        @keyframes pulse-animation {{ 0% {{ box-shadow: 0 0 0 0px rgba(59, 130, 246, 0.4); }} 100% {{ box-shadow: 0 0 0 20px rgba(59, 130, 246, 0); }} }}

        /* ========== FORM MODAL STYLES ========== */
        .form-modal-overlay {{
            position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(8px); z-index: 2000;
            display: none; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.3s ease;
        }}
        .form-modal-overlay.active {{ display: flex; opacity: 1; }}
        .form-modal-content {{
            width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 2rem;
            border-radius: 1.5rem; background: #0a0a0a; border: 1px solid rgba(255, 255, 255, 0.1);
            transform: scale(0.95); transition: transform 0.3s ease; position: relative;
        }}
        .form-modal-overlay.active .form-modal-content {{ transform: scale(1); }}
        .close-btn {{ position: absolute; top: 20px; right: 20px; background: none; border: none; color: #aaa; font-size: 2rem; cursor: pointer; }}
        .close-btn:hover {{ color: #fff; }}
        .progress-bar {{ display: flex; justify-content: space-between; margin-bottom: 2rem; max-width: 400px; margin-left: auto; margin-right: auto; position: relative; }}
        .progress-bar::before {{ content: ''; position: absolute; top: 50%; left: 0; right: 0; height: 2px; background-color: rgba(255,255,255,0.2); transform: translateY(-50%); z-index: -1; }}
        .progress-step {{ width: 35px; height: 35px; border-radius: 50%; background: rgba(255,255,255,0.1); border: 2px solid rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; color: #fff; transition: all 0.3s; }}
        .progress-step.active {{ background: linear-gradient(135deg, #3B82F6, #22C55E); border-color: transparent; transform: scale(1.1); }}
        .form-step {{ display: none; }}
        .form-step.active {{ display: block; animation: fadeIn 0.5s; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        input, textarea, select {{ width: 100%; padding: 0.75rem; margin-bottom: 1rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; color: #fff; }}
        .checkbox-group {{ display: grid; grid-template-columns: repeat(2,1fr); gap: 0.75rem; }}
        .checkbox-item {{ background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 0.5rem; display: flex; align-items: center; cursor: pointer; }}
        .checkbox-item:hover {{ background: rgba(59,130,246,0.1); }}
        .checkbox-item input[type="checkbox"] {{ display: none; }}
        .checkbox-item .checkmark {{ width: 20px; height: 20px; border: 2px solid #3B82F6; border-radius: 4px; margin-right: 10px; display: flex; align-items: center; justify-content: center; }}
        .checkbox-item .checkmark svg {{ display: none; width: 14px; height: 14px; }}
        .checkbox-item input[type="checkbox"]:checked + .checkmark {{ background: linear-gradient(135deg, #3B82F6, #22C55E); }}
        .checkbox-item input[type="checkbox"]:checked + .checkmark svg {{ display: block; }}
        .slider-output {{ text-align: center; font-weight: bold; color: #22C55E; }}
        .form-navigation {{ display: flex; justify-content: space-between; margin-top: 2rem; }}
        .nav-btn {{ padding: 0.75rem 2rem; background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; border-radius: 0.5rem; font-weight: bold; cursor: pointer; transition: all 0.3s; }}
        .nav-btn.prev {{ background: rgba(255,255,255,0.1); }}
        .nav-btn:hover {{ opacity: 0.9; transform: translateY(-2px); }}
    """

    # Replace the ENTIRE FIRST <style> block
    content = re.sub(r'<style>.*?</style>', f'<style>\\n        {css_content}\\n    </style>', content, count=1, flags=re.DOTALL)
    
    # Fix RTL for Arabic Chatbot
    if lang == 'ar':
        content = content.replace('right: 8px; left: auto;', 'left: 8px; right: auto;')
        content = content.replace('margin-right: 10px;', 'margin-left: 10px;')
        content = content.replace('right: 20px;', 'left: 20px;')
        content = content.replace('text-align: left;', 'text-align: right;')

    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Fully restored and cleaned CSS in {file_path}")

# Run for all pages
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
    restore_aesthetics(page, lang)
