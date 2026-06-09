import os
import glob
from PIL import Image
import re
from bs4 import BeautifulSoup

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

def get_image_size(src, base_dir):
    if not src:
        return None
    if src.startswith('http') or src.startswith('//'):
        return None
    
    src = src.split('?')[0].split('#')[0]
    if src.startswith('/'):
        filepath = os.path.join(base_dir, src[1:])
    else:
        filepath = os.path.join(base_dir, src)
        
    try:
        if os.path.exists(filepath):
            with Image.open(filepath) as img:
                return img.width, img.height
    except Exception as e:
        pass
    return None

updated_files = []

for filepath in html_files:
    rel_path = os.path.relpath(filepath, PUBLIC_HTML)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    modified = False
    
    # Track what changed for this file
    changes = []

    # 1. Step 2 - Fix CLS
    # Add width and height to img, video, iframe
    for tag in soup.find_all(['img', 'video', 'iframe']):
        if not tag.has_attr('width') or not tag.has_attr('height'):
            src = tag.get('src')
            if tag.name == 'img' and src:
                size = get_image_size(src, PUBLIC_HTML)
                if size:
                    tag['width'] = str(size[0])
                    tag['height'] = str(size[1])
                    modified = True
                    if "Added width/height to images/media" not in changes:
                        changes.append("Added width/height to images/media")
            elif tag.name in ['video', 'iframe']:
                # Provide reasonable defaults if none exist
                if not tag.has_attr('width'):
                    tag['width'] = "640"
                    modified = True
                if not tag.has_attr('height'):
                    tag['height'] = "360"
                    modified = True
                if "Added width/height to images/media" not in changes:
                    changes.append("Added width/height to images/media")

    # Add aspect-ratio CSS and min-height for dynamic content
    cls_css = "img, video, iframe { aspect-ratio: attr(width) / attr(height); } .youtube-facade, #aiden-ui, .dynamic-content { min-height: 200px; }"
    if not soup.find(string=re.compile(r"aspect-ratio: attr\(width\) / attr\(height\)")):
        style_tag = soup.new_tag("style")
        style_tag.string = cls_css
        if soup.head:
            soup.head.append(style_tag)
            modified = True
            changes.append("Added CLS aspect-ratio & min-height CSS")

    # 2. Step 3 - Fix main landmark
    if not soup.find('main'):
        # Only wrap if missing
        body = soup.body
        if body:
            main_tag = soup.new_tag("main")
            main_tag['id'] = "main-content"
            # Move all content except nav, header, footer, scripts to main
            elements_to_move = []
            for child in list(body.children):
                if child.name in ['nav', 'header', 'footer', 'script']:
                    continue
                elements_to_move.append(child)
            
            nav = body.find('nav') or body.find('header')
            if nav:
                nav.insert_after(main_tag)
            else:
                body.insert(0, main_tag)
                
            for el in elements_to_move:
                main_tag.append(el.extract())
            modified = True
            changes.append("Wrapped body content in <main> landmark")

    # Remove http-equiv="refresh"
    for meta in soup.find_all('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'refresh'}):
        meta.decompose()
        modified = True
        changes.append("Removed http-equiv='refresh' meta tag")

    # Remove noindex
    for meta in soup.find_all('meta', attrs={'name': lambda x: x and x.lower() == 'robots'}):
        if 'noindex' in (meta.get('content') or '').lower():
            meta.decompose()
            modified = True
            changes.append("Removed noindex robots meta tag")

    # 3. Step 4 - Fix SEO meta description
    new_desc = "وفر وقتك وزد أرباحك مع AI Profit Lab - منصة الذكاء الاصطناعي للتداول الآلي"
    desc_meta = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    if desc_meta:
        if desc_meta.get('content') != new_desc:
            desc_meta['content'] = new_desc
            modified = True
            changes.append("Updated SEO meta description")
    else:
        new_meta = soup.new_tag('meta', attrs={'name': 'description', 'content': new_desc})
        if soup.head:
            soup.head.append(new_meta)
            modified = True
            changes.append("Added SEO meta description")

    # 4. Step 5 - Fix render-blocking
    for script in soup.find_all('script'):
        if script.has_attr('src'):
            if not script.has_attr('defer') and not script.has_attr('async'):
                script['defer'] = ""
                modified = True
                if "Added defer to <script>" not in changes:
                    changes.append("Added defer to <script>")

    for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in x):
        # Convert to preload pattern if not critical
        href = link.get('href', '')
        if href and 'fonts.googleapis.com' not in href and not link.find_parent('noscript'):
            link['rel'] = "preload"
            link['as'] = "style"
            link['onload'] = "this.onload=null;this.rel='stylesheet'"
            
            noscript = soup.new_tag('noscript')
            fallback = soup.new_tag('link', rel='stylesheet', href=href)
            noscript.append(fallback)
            link.insert_after(noscript)
            modified = True
            if "Moved CSS to preload pattern" not in changes:
                changes.append("Moved CSS to preload pattern")

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        updated_files.append((rel_path, changes))

print(f"Total files updated: {len(updated_files)}")
for f, changes in updated_files:
    print(f"\n{f}:")
    for change in changes:
        print(f"  - {change}")
