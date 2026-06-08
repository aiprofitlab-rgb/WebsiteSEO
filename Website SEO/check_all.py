import os
import re

html_files = []
for root, dirs, files in os.walk('public_html'):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

issues = []
for f in html_files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    has_btn = 'onclick="toggleChat()"' in content
    has_div = 'id="aiden-ui"' in content
    has_toggle = 'function toggleChat()' in content
    has_onload = 'window.onload = ' in content
    has_add = 'window.addEventListener(\'load\',' in content
    
    if has_btn and not has_toggle:
        issues.append(f"{f}: Has button but NO toggleChat() function")
    
    if has_div and has_onload:
        issues.append(f"{f}: Still has window.onload override!")

if issues:
    print("\n".join(issues))
else:
    print("No obvious issues found.")
