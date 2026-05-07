import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def fix_malformed_links():
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.html'): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Fix double /en/en/
            new_content = content.replace('href="/en/en/"', 'href="/en/"')
            new_content = new_content.replace('href="/en/en"', 'href="/en/"')
            
            # 2. Fix /blog_ar/ and others that should be hyphenated
            new_content = new_content.replace('href="/blog_ar/"', 'href="/blog-ar/"')
            new_content = new_content.replace('href="/academy_ar/"', 'href="/academy-ar/"')
            
            # 3. Fix legacy Simulator links that missed the mapping
            new_content = new_content.replace('/Campaign_ROI_Simulator/', '/campaign-roi-simulator/')
            new_content = new_content.replace('/whatsapp_receptionist_demo/', '/whatsapp-receptionist-demo/')
            new_content = new_content.replace('/Missed-Call-Simulator-en/', '/en/missed-call-simulator-en/')
            new_content = new_content.replace('/Missed-Call-Simulator-ar/', '/missed-call-simulator-ar/')
            
            # 4. Correct casing for some specific targets found in auditor
            new_content = new_content.replace('/blog/en/2026-04-28-ai-automation-ROI-2025-guide/', '/blog/en/2026-04-28-ai-automation-roi-2025-guide/')

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed malformed links in: {file}")

if __name__ == "__main__":
    fix_malformed_links()
