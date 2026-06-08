import os
import glob
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)
files_to_fix = []

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "function toggleChat" in content and "document.getElementById('aiden-ui').classList.toggle('active');" in content:
        if "// Close menu" in content or "window.onload = async function() {" in content:
             if "mobileMenu.querySelectorAll" in content and "function toggleChat" in content and "window.onload = async function() {" in content:
                # Let's see if contact.html is still broken
                if file.endswith('contact.html'):
                    files_to_fix.append(file)

print(files_to_fix)
