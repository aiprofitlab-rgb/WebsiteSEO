import os
import re

def standardize_css(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r') as f:
        content = f.read()

    unified_css = """/* ========== UNIFIED NAVIGATION STYLES ========== */
        .desktop-menu-container {
            display: none;
        }
        
        .mobile-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
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
        
        .mobile-dropdown-menu a {
            padding: 0.75rem 0;
            text-align: center;
            font-weight: 600;
            font-size: 1.1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            transition: color 0.2s;
        }
        
        .mobile-dropdown-menu a:last-child {
            border-bottom: none;
        }
        
        .mobile-dropdown-menu a:hover {
            color: #60a5fa;
        }
        
        .mobile-dropdown-menu.open {
            display: flex;
        }
        
        .desktop-nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .desktop-nav-links a {
            font-weight: 700;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: color 0.2s;
        }
        
        .desktop-nav-links a:hover {
            color: #3b82f6;
        }
        
        @media (min-width: 768px) {
            .desktop-menu-container {
                display: block !important;
            }
            .mobile-controls {
                display: none !important;
            }
            .mobile-dropdown-menu {
                display: none !important;
            }
        }"""

    # Cleanup old navigation styles
    content = re.sub(r'/\* ========== UNIFIED NAVIGATION STYLES ========== \*/.*?@media.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.desktop-menu.*?\{.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.mobile-nav-toggle.*?\{.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.mobile-menu-dropdown.*?\{.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.mobile-dropdown-menu.*?\{.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.desktop-nav-links.*?\{.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\.nav-links.*?\{.*?\}', '', content, flags=re.DOTALL)
    
    # Insert unified CSS at the beginning of the first <style> tag
    if '<style>' in content:
        content = re.sub(r'<style>', f'<style>\\n        {unified_css}', content, count=1)
    else:
        # Fallback if no style tag exists, insert before </head>
        content = content.replace('</head>', f'<style>\\n{unified_css}\\n</style>\\n</head>')
    
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Standardized CSS in {file_path}")

# Run for all pages
pages = [
    'public_html/index.html',
    'public_html/en.html',
    'public_html/services.html',
    'public_html/services-en.html',
    'public_html/process.html',
    'public_html/process-en.html',
    'public_html/contact.html',
    'public_html/contact-en.html',
    'public_html/about.html',
    'public_html/about-en.html',
    'public_html/blog.html',
    'public_html/blog_ar.html'
]

for page in pages:
    standardize_css(page)
