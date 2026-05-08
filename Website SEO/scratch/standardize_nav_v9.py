import os
import re

CSS = """
        /* STANDARD NAV FIX */
        #header {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            z-index: 10000 !important;
            box-sizing: border-box !important;
            background: rgba(5, 5, 5, 0.98) !important;
            backdrop-filter: blur(15px) !important;
            border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        }

        @media (min-width: 1025px) {
            #header { height: 90px !important; padding: 0 5% !important; }
            #desktopMenu { display: flex !important; align-items: center !important; gap: 2.5rem !important; }
            .desktop-nav-links { display: flex !important; align-items: center !important; gap: 2rem !important; }
            .mobile-controls, #mobileMenu { display: none !important; }
            [dir="rtl"] #header { direction: rtl !important; }
            [dir="ltr"] #header { direction: ltr !important; }
        }

        @media (max-width: 1024px) {
            #header { height: 75px !important; padding: 0 1.5rem !important; overflow: visible !important; }
            #desktopMenu { display: none !important; }
            .mobile-controls { 
                display: flex !important; 
                align-items: center !important; 
                gap: 1.25rem !important; 
                z-index: 10002 !important; 
                position: relative !important; 
                pointer-events: auto !important;
            }
            #mobileToggle { 
                display: flex !important; 
                background: transparent !important;
                border: none !important;
                color: white !important;
                font-size: 2.4rem !important;
                cursor: pointer !important;
                pointer-events: auto !important;
                padding: 10px !important;
                z-index: 10003 !important;
                line-height: 1 !important;
            }
            #mobileMenu { 
                display: none !important; 
                position: absolute !important;
                top: 75px !important;
                left: 0 !important;
                right: 0 !important;
                background: rgba(10, 10, 10, 0.99) !important;
                flex-direction: column !important;
                padding: 2.5rem 1.5rem !important;
                gap: 1.5rem !important;
                z-index: 10001 !important;
                max-height: calc(100vh - 75px) !important;
                overflow-y: auto !important;
                text-align: center !important;
                border-bottom: 1px solid rgba(255,255,255,0.1) !important;
            }
            #mobileMenu.open { display: flex !important; }
        }
"""

JS = """
        // STANDARD NAV JS
        (function() {
            function initNav() {
                const btn = document.getElementById('mobileToggle');
                const m = document.getElementById('mobileMenu');
                if (!btn || !m) return;
                
                const toggleAction = (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    m.classList.toggle('open');
                };
                
                btn.onclick = toggleAction;
                btn.ontouchstart = toggleAction;
                
                document.addEventListener('click', (e) => {
                    if (m.classList.contains('open') && !btn.contains(e.target) && !m.contains(e.target)) {
                        m.classList.remove('open');
                    }
                });
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initNav);
            } else {
                initNav();
            }
            window.addEventListener('load', initNav);
        })();
"""

def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return

    # 1. Update HTML IDs
    # nav tag -> add id="header" (if not already there)
    if 'id="header"' not in content:
        content = re.sub(r'<nav([^>]*?)>', r'<nav\1 id="header">', content, 1)
    
    # mobileMenuToggle -> mobileToggle
    content = content.replace('id="mobileMenuToggle"', 'id="mobileToggle"')
    # mobileDropdownMenu -> mobileMenu
    content = content.replace('id="mobileDropdownMenu"', 'id="mobileMenu"')
    
    # Add id="desktopMenu" if missing
    if 'id="desktopMenu"' not in content:
        content = re.sub(r'(<!--\s*Desktop Menu\s*-->\s*<div[^>]*?)>', r'\1 id="desktopMenu">', content, 1)

    # 2. Add CSS
    if '</style>' in content:
        if "STANDARD NAV FIX" not in content:
            content = content.replace('</style>', CSS + '</style>', 1)
    
    # 3. Add JS
    if '</body>' in content:
        if "STANDARD NAV JS" not in content:
            content = content.replace('</body>', '<script>' + JS + '</script></body>')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    import os
    for r, d, files in os.walk('public_html'):
        for f in files:
            if f.endswith('.html'):
                fix_file(os.path.join(r, f))
