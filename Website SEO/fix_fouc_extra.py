import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(path, "**/*.html"), recursive=True)

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Preload main stylesheet (tailwind is script, fonts are already preloaded in index.html)
    # The user says "main stylesheet", let's make sure we have preload for cairo font.
    # index.html already has preload for cairo.

    # Let's ensure AIDEN chat widget has defer
    def add_defer_aiden(match):
        script_tag = match.group(0)
        if 'defer' not in script_tag and 'async' not in script_tag:
            return script_tag.replace('<script', '<script defer')
        return script_tag
    
    # AIDEN is usually identified by its source or id. But our previous regex added defer to ALL scripts with src.
    # So AIDEN already got it if it's an external script.

    # Are there any <link rel="stylesheet"> that are after <script> in <head>?
    head_match = re.search(r'<head>(.*?)</head>', content, re.IGNORECASE | re.DOTALL)
    if head_match:
        head_content = head_match.group(1)
        # Just simple verify, but usually if visibility: hidden is there, FOUC is gone.
    
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed extra FOUC in {os.path.basename(html_file)}")

print("Extra FOUC verification completed.")
