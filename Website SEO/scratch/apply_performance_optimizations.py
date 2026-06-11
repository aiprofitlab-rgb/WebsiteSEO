import os
import re

base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. TAILWIND CDN
    tailwind_script = '<script src="https://cdn.tailwindcss.com"></script>'
    preconnects = '<link rel="preconnect" href="https://cdn.tailwindcss.com">\n<link rel="dns-prefetch" href="https://cdn.tailwindcss.com">\n'
    if tailwind_script in content and '<link rel="preconnect" href="https://cdn.tailwindcss.com">' not in content:
        content = content.replace(tailwind_script, preconnects + tailwind_script)

    # 2. GOOGLE FONTS
    fonts_preconnects = '\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    if '<link rel="preconnect" href="https://fonts.googleapis.com">' not in content:
        content = re.sub(r'(<meta charset="[^"]+"[^>]*>)', r'\1' + fonts_preconnects, content, count=1, flags=re.IGNORECASE)
        if original_content == content:
            content = re.sub(r'(<head[^>]*>)', r'\1' + fonts_preconnects, content, count=1, flags=re.IGNORECASE)

    # 3. HERO IMAGE for index.html only
    if os.path.basename(filepath) == 'index.html':
        preload_tag = '\n<link rel="preload" as="image" href="/nahid-business-banner.png">'
        if preload_tag.strip() not in content:
            content = re.sub(r'(</head>)', preload_tag + r'\n\1', content, flags=re.IGNORECASE)

    # 4. IMAGES: loading="lazy" to non-hero images
    img_pattern = re.compile(r'<img\s+[^>]*>', re.IGNORECASE)
    imgs = list(img_pattern.finditer(content))
    for i, match in enumerate(imgs):
        if i == 0:
            continue # skip the first image
        img_tag = match.group(0)
        if 'loading="lazy"' not in img_tag.lower() and "loading='lazy'" not in img_tag.lower():
            if img_tag.endswith('/>'):
                new_img_tag = img_tag[:-2] + ' loading="lazy"/>'
            else:
                new_img_tag = img_tag[:-1] + ' loading="lazy">'
            content = content.replace(img_tag, new_img_tag)

    # 5. SCRIPT TAGS: defer
    # Match <script src="..."> but not <script src="..."></script> just the opening tag
    script_pattern = re.compile(r'<script([^>]*)>', re.IGNORECASE)
    scripts = list(script_pattern.finditer(content))
    for match in scripts:
        script_attrs = match.group(1)
        if 'src=' in script_attrs.lower():
            if 'cdn.tailwindcss.com' in script_attrs.lower():
                continue
            if 'defer' not in script_attrs.lower():
                original_tag = match.group(0)
                new_tag = original_tag[:-1] + ' defer>'
                content = content.replace(original_tag, new_tag)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")

for root, _, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.html'):
            process_file(os.path.join(root, f))
