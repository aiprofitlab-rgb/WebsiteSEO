import os
import glob
import re
from bs4 import BeautifulSoup

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

tailwind_sizes = {
    'w-3': 12, 'h-3': 12,
    'w-4': 16, 'h-4': 16,
    'w-5': 20, 'h-5': 20,
    'w-6': 24, 'h-6': 24,
    'w-8': 32, 'h-8': 32,
    'w-10': 40, 'h-10': 40,
    'w-12': 48, 'h-12': 48,
    'w-16': 64, 'h-16': 64,
}

updated_files = []

for filepath in html_files:
    rel_path = os.path.relpath(filepath, PUBLIC_HTML)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    for svg in soup.find_all('svg'):
        width = None
        height = None
        
        classes = svg.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
            
        # 1. Determine size from tailwind classes
        for cls in classes:
            if cls in tailwind_sizes and cls.startswith('w-'):
                width = tailwind_sizes[cls]
            if cls in tailwind_sizes and cls.startswith('h-'):
                height = tailwind_sizes[cls]
                
        # 2. Fallback to viewBox
        if not width or not height:
            vb = svg.get('viewbox') or svg.get('viewBox')
            if vb:
                parts = vb.split()
                if len(parts) == 4:
                    if not width: width = parts[2]
                    if not height: height = parts[3]
                    
        # 3. Apply width and height attributes
        if width and not svg.has_attr('width'):
            svg['width'] = str(width)
            modified = True
        if height and not svg.has_attr('height'):
            svg['height'] = str(height)
            modified = True
            
        # Add will-change for animated SVGs
        is_animated = any('rotate' in cls or 'transform' in cls or 'transition' in cls for cls in classes)
        if is_animated:
            style = svg.get('style', '')
            if 'will-change' not in style:
                new_style = (style + '; will-change: transform;').strip('; ')
                svg['style'] = new_style
                modified = True

    # Global CSS for SVGs to prevent full-width rendering before CSS loads
    svg_css = "svg { max-width: 100%; height: auto; overflow: hidden; } svg:not([width]) { width: 24px; height: 24px; }"
    if not soup.find(string=re.compile(r"svg \{ max-width: 100%; height: auto; overflow: hidden; \}")):
        style_tag = soup.new_tag("style")
        style_tag.string = svg_css
        if soup.head:
            soup.head.append(style_tag)
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        updated_files.append(rel_path)

print(f"Total files updated with SVG fixes: {len(updated_files)}")
