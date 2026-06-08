import os
import glob

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        has_button = 'onclick="toggleChat()"' in content
        has_aiden_ui = 'id="aiden-ui"' in content
        has_css = '#aiden-ui.active' in content
        has_js = 'function toggleChat' in content
        
        if has_button:
            issues = []
            if not has_aiden_ui: issues.append("Missing aiden-ui div")
            if not has_css: issues.append("Missing #aiden-ui.active CSS")
            if not has_js: issues.append("Missing function toggleChat()")
            
            if issues:
                print(f"File: {file} has issues: {', '.join(issues)}")

