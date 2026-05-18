import os
import glob
import re

html_files = glob.glob("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html", recursive=True)

original_font_link = '<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap" rel="stylesheet">'
preload_font_link = """<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800&display=swap"></noscript>"""

modified_files = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    if original_font_link in content:
        content = content.replace(original_font_link, preload_font_link)
    
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files += 1

print(f"Updated {modified_files} HTML files to preload Google Fonts.")
