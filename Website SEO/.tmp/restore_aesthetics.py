import os
import re

def restore_aesthetics(file_path, lang='en'):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. Define Clean Unified Navigation CSS
    unified_nav_css = """/* ========== UNIFIED NAVIGATION STYLES ========== */
        .desktop-menu-container { display: none; }
        .mobile-controls { display: flex; align-items: center; gap: 1rem; }
        .mobile-dropdown-menu {
            display: none; position: absolute; top: 100%; left: 0; right: 0;
            background-color: #0a0a0a; padding: 1.25rem; flex-direction: column; gap: 1rem;
            border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); z-index: 1000;
        }
        .mobile-dropdown-menu a {
            padding: 0.75rem 0; text-align: center; font-weight: 600; font-size: 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08); transition: color 0.2s;
        }
        .mobile-dropdown-menu a:last-child { border-bottom: none; }
        .mobile-dropdown-menu a:hover { color: #60a5fa; }
        .mobile-dropdown-menu.open { display: flex; }
        .desktop-nav-links { display: flex; gap: 2rem; align-items: center; }
        .desktop-nav-links a { font-weight: 700; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.5px; transition: color 0.2s; }
        .desktop-nav-links a:hover { color: #3b82f6; }
        @media (min-width: 768px) {
            .desktop-menu-container { display: block !important; }
            .mobile-controls { display: none !important; }
            .mobile-dropdown-menu { display: none !important; }
        }"""

    # 2. Define Core Aesthetic CSS
    font_family = "'Cairo', sans-serif" if lang == 'ar' else "'Outfit', sans-serif"
    core_css = f"""
        body {{ font-family: {font_family}; background-color: #050505; color: #ffffff; margin: 0; overflow-x: hidden; }}
        .glass {{ background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }}
        .glass-card {{ background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }}
        .glass-card:hover {{ border-color: #3B82F6; transform: translateY(-5px); }}
    """

    # 3. CLEANUP: Remove ALL corrupted navigation and body styles
    # Remove everything between <style> and the first non-nav/non-body style we find
    # Or just replace the whole style block if it's messy
    
    # We'll use a more surgical approach to avoid removing page-specific styles
    content = re.sub(r'/\* ========== UNIFIED NAVIGATION STYLES ========== \*/.*?@media.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'body\s*\{[^}]*background-color:[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.glass\s*\{[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.glass-card\s*\{[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.desktop-menu-container\s*\{[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.mobile-controls\s*\{[^}]*\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.mobile-dropdown-menu\s*\{[^}]*\}', '', content, flags=re.DOTALL)
    
    # Remove those lone closing braces
    content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)
    
    # 4. INSERT: Add the clean CSS back
    if '<style>' in content:
        content = re.sub(r'<style>', f'<style>\\n        {unified_nav_css}\\n        {core_css}', content, count=1)
    
    # 5. STRAY TEXT CLEANUP: Remove the stray brace inside script tags if any
    content = re.sub(r'<script.*?>\s*\}\s*</script>', '', content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Restored aesthetics in {file_path}")

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
