import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

print("Finding all WebP images...")
webp_files = []
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.webp'):
            # Store the base name without extension
            base_name = os.path.splitext(file)[0]
            webp_files.append(base_name)

print(f"Found {len(webp_files)} WebP images. Updating HTML files...")

html_files = []
for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

updated_count = 0

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # For every found WebP base name, replace its .jpg or .png equivalent with .webp
    for base_name in webp_files:
        # Replace base_name.jpg with base_name.webp
        content = re.sub(f'{re.escape(base_name)}\\.jpg', f'{base_name}.webp', content, flags=re.IGNORECASE)
        # Replace base_name.png with base_name.webp
        content = re.sub(f'{re.escape(base_name)}\\.png', f'{base_name}.webp', content, flags=re.IGNORECASE)
        # Replace base_name.jpeg with base_name.webp
        content = re.sub(f'{re.escape(base_name)}\\.jpeg', f'{base_name}.webp', content, flags=re.IGNORECASE)
        
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        updated_count += 1

print(f"Successfully updated {updated_count} HTML files to use WebP images.")
