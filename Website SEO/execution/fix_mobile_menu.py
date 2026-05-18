import os
import glob

html_files = glob.glob("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html", recursive=True)

old_bg = "background: rgba(255, 255, 255, 0.08) !important;"
new_bg = "background: rgba(10, 10, 10, 0.98) !important; backdrop-filter: blur(20px) !important;"

modified_files = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    if old_bg in content:
        content = content.replace(old_bg, new_bg)
    
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files += 1

print(f"Updated {modified_files} HTML files to fix mobile menu background.")
