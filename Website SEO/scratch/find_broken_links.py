import os
import re

root_dir = 'public_html'
html_files = []

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith('.html'):
            html_files.append(os.path.join(root, file))

broken_links = []

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        links = re.findall(r'href="([^"|#]+)\.html"', content)
        for link in links:
            if link.startswith('http') or link.startswith('//'):
                continue
            
            # Construct target path
            if link.startswith('/'):
                target_path = os.path.join(root_dir, link.lstrip('/') + '.html')
            else:
                target_path = os.path.join(os.path.dirname(html_file), link + '.html')
            
            if not os.path.exists(target_path):
                broken_links.append((html_file, link + '.html'))

if broken_links:
    print("Found broken links:")
    for source, target in broken_links:
        print(f"File: {source} -> Broken Link: {target}")
else:
    print("No broken links found.")
