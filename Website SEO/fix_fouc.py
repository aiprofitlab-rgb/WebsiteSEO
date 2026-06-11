import os
import re
from bs4 import BeautifulSoup

def fix_fouc(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # 1. Add FOUC hidden style to head if not exists
    head = soup.head
    if not head:
        return False
    
    # 2. Add visibility hidden
    fouc_style_exists = False
    for style in head.find_all('style'):
        if 'body { visibility: hidden; }' in style.text:
            fouc_style_exists = True
            break
            
    if not fouc_style_exists:
        new_style = soup.new_tag('style')
        new_style.string = 'body { visibility: hidden; }'
        # Insert at top of head, after meta charset if possible
        head.insert(1, new_style)

    # 3. Move critical CSS and fonts to top, add preconnect
    # (Actually BeautifulSoup rearranging might be tricky, let's just use regex for precise insertions if needed, but bs4 is safer for DOM).
    
    # Google Fonts Preconnect
    preconnects = soup.find_all('link', rel='preconnect')
    has_gfonts_preconnect = any('fonts.googleapis.com' in str(link) for link in preconnects)
    has_gstatic_preconnect = any('fonts.gstatic.com' in str(link) for link in preconnects)
    
    if not has_gfonts_preconnect:
        link = soup.new_tag('link', rel='preconnect', href='https://fonts.googleapis.com')
        head.insert(1, link)
    if not has_gstatic_preconnect:
        link = soup.new_tag('link', rel='preconnect', href='https://fonts.gstatic.com', crossorigin='')
        head.insert(1, link)

    # 4. Defer all non-critical JS
    for script in soup.find_all('script'):
        if not script.has_attr('src'):
            continue
        if script.get('src') and not script.has_attr('defer') and not script.has_attr('async'):
            script['defer'] = ''

    # 5. Add FOUC visible script to bottom of body
    body = soup.body
    if body:
        # Check if already there
        fouc_script_exists = False
        for script in body.find_all('script'):
            if script.string and "document.body.style.visibility = 'visible';" in script.string:
                fouc_script_exists = True
                break
        
        if not fouc_script_exists:
            new_script = soup.new_tag('script')
            # Wait for tailwind or window load to be safe, or just bottom of body
            # If tailwind is used, it takes time to compile. So maybe just removing it at the bottom of the body isn't enough, we might need a small delay or window.onload. 
            # But the user asked for:
            new_script.string = "document.body.style.visibility = 'visible';"
            body.append(new_script)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    return True

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                print(f"Fixing {filepath}")
                fix_fouc(filepath)

if __name__ == "__main__":
    process_directory('public_html')
