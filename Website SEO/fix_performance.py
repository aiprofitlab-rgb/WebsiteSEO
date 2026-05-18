import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(path, "**/*.html"), recursive=True)

preload_tag = '\n    <link rel="preload" as="image" href="/hero-bg.webp" type="image/webp">\n'

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # 1. Preload hero-bg.webp if it exists on page
    if 'hero-bg.webp' in content and 'rel="preload" as="image" href="/hero-bg.webp"' not in content:
        content = content.replace('</head>', f'{preload_tag}</head>')
        changed = True
        
    # 2. Add loading="lazy" to images that are not above the fold
    # Using a simple regex to add loading="lazy" to <img ...> if it doesn't have it.
    # Exclude images that might be above the fold (like logos), but here logo is not loaded via img tag.
    def add_lazy(match):
        img_tag = match.group(0)
        if 'loading=' not in img_tag:
            return img_tag.replace('<img ', '<img loading="lazy" ')
        return img_tag
        
    new_content = re.sub(r'<img [^>]+>', add_lazy, content)
    if new_content != content:
        content = new_content
        changed = True
        
    # 3. Add rel="preconnect" for google fonts
    preconnect_tags = """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
"""
    if 'fonts.googleapis.com' in content and 'rel="preconnect"' not in content:
        content = content.replace('</head>', f'{preconnect_tags}</head>')
        changed = True

    if changed:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Optimized {os.path.basename(html_file)}")

print("Performance optimization done.")
