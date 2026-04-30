import os
import re

PUBLIC_HTML = "public_html"
BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), PUBLIC_HTML))

def repair_all():
    # 1. Fix index.html (visible text above menu)
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        print("Repairing index.html...")
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Wrap the stray CSS in a style tag
        bad_text = "/* ========== UNIFIED NAVIGATION STYLES ========== */"
        if bad_text in content and f"<style>\n{bad_text}" not in content:
            content = content.replace(bad_text, f"<style>\n{bad_text}")
        
        # Ensure the closing </style> is correct
        # Look for the block and make sure it's clean
        content = re.sub(r'</style>\s*</head>', '</style>\n</head>', content)
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

    # 2. Restore styles for core pages
    pages_to_restore = ["services.html", "services-en.html", "process.html", "process-en.html", "contact.html", "contact-en.html"]
    
    for page in pages_to_restore:
        path = os.path.join(BASE_DIR, page)
        if not os.path.exists(path): continue
        print(f"Restoring styles for {page}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        is_arabic = 'lang="ar"' in content or 'dir="rtl"' in content
        font_family = "'Cairo', sans-serif" if is_arabic else "'Outfit', sans-serif"
        text_align = "right" if is_arabic else "left"
        chat_pos = "left: 8px; right: auto;" if is_arabic else "right: 8px; left: auto;"

        # Build the FULL ORIGINAL CSS BLOCK
        full_css = f"""
    <style>
        body {{ font-family: {font_family}; background-color: #050505; color: #ffffff; margin: 0; overflow-x: hidden; }}
        .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }}
        .glass-card {{ background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }}
        .glass-card:hover {{ border-color: #3B82F6; transform: translateY(-5px); }}
        
        /* Unified Navigation Styles */
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

        /* Pricing Table Styles */
        .comparison-table {{ border-collapse: separate; border-spacing: 0 8px; width: 100%; }}
        .comparison-table th {{ background: rgba(59,130,246,0.1); padding: 1rem; font-weight: 700; text-align: {text_align}; }}
        .comparison-table td {{ padding: 1rem; background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.05); text-align: {text_align}; }}
        .comparison-table tr:hover td {{ background: rgba(59,130,246,0.05); }}

        /* Timeline Styles */
        .timeline-line {{ position: absolute; left: 50%; transform: translateX(-50%); width: 2px; height: 100%; background: linear-gradient(to bottom, #3B82F6, #22C55E); opacity: 0.3; }}
        @media (max-width: 768px) {{ .timeline-line {{ display: none; }} .checkbox-group {{ grid-template-columns: 1fr; }} }}

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
        input, textarea, select {{ width: 100%; padding: 0.75rem 1rem; margin-bottom: 1rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 0.5rem; color: #fff; text-align: {text_align}; }}
        .checkbox-group {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-bottom: 1rem; }}
        .checkbox-item {{ background: rgba(255,255,255,0.03); padding: 0.75rem; border-radius: 0.5rem; display: flex; align-items: center; cursor: pointer; border: 1px solid transparent; transition: all 0.2s; }}
        .checkbox-item:hover {{ background: rgba(59,130,246,0.1); border-color: #3B82F6; }}
        .nav-btn {{ padding: 0.75rem 2rem; border-radius: 0.5rem; font-weight: bold; cursor: pointer; transition: all 0.3s; }}
        .nav-btn.next, .nav-btn.submit {{ background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; }}
        .nav-btn.prev {{ background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.1); }}
    </style>
"""
        # Remove ALL existing style blocks to start clean
        content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
        # Inject the full CSS block
        content = content.replace("</head>", f"{full_css}\n</head>")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    repair_all()
    print("Done.")
