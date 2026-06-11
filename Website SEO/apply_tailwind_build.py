import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(path, "**/*.html"), recursive=True)

tailwind_cdn_regex = re.compile(r'<script[^>]*src="https://cdn\.tailwindcss\.com"[^>]*></script>')
tailwind_link = '<link rel="stylesheet" href="/assets/css/tailwind.min.css">'

fouc_style_regex = re.compile(r'<style>body\s*\{\s*visibility:\s*hidden;\s*\}</style>\s*')
fouc_script_regex = re.compile(r'<script>document\.body\.style\.visibility\s*=\s*\'visible\';</script>\s*')

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Replace tailwind CDN with local CSS
    if tailwind_cdn_regex.search(content):
        content = tailwind_cdn_regex.sub(tailwind_link, content)
    
    # Remove visibility: hidden style
    content = fouc_style_regex.sub('', content)

    # Remove visible script
    content = fouc_script_regex.sub('', content)

    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(html_file)}")

print("Tailwind local CSS applied and FOUC hacks removed.")
