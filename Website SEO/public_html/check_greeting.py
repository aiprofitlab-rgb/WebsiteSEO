import os
import glob

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
        has_toggle_chat = 'function toggleChat' in content
        calls_greeting = 'getPageSpecificGreeting()' in content
        has_greeting_def = 'function getPageSpecificGreeting' in content
        
        if has_toggle_chat and calls_greeting and not has_greeting_def:
            print(f"Missing greeting def: {file}")

