import os
import glob
import re
import subprocess

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

print("Converting images to WebP using macOS sips...")
for root, dirs, files in os.walk(path):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(root, file)
            webp_path = os.path.splitext(img_path)[0] + '.webp'
            if not os.path.exists(webp_path):
                try:
                    # use sips to convert
                    subprocess.run(["sips", "-s", "format", "webp", img_path, "--out", webp_path], check=True, stdout=subprocess.DEVNULL)
                    print(f"Converted {file} to WebP")
                except Exception as e:
                    print(f"Error converting {file}: {e}")

print("\nUpdating HTML files with Canonical tags and WebP links...")
html_files = glob.glob(os.path.join(path, "*.html"))

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace .jpg and .png with .webp
    content = re.sub(r'\.jpg', '.webp', content, flags=re.IGNORECASE)
    content = re.sub(r'\.png', '.webp', content, flags=re.IGNORECASE)
    
    # Clean URL for Canonical
    filename = os.path.basename(html_file)
    clean_name = filename.replace('.html', '')
    if clean_name == 'index':
        canonical_url = "https://aiprofitlab.io/"
    elif clean_name == 'en':
        canonical_url = "https://aiprofitlab.io/en/"
    else:
        canonical_url = f"https://aiprofitlab.io/{clean_name}/"
        
    # Update Canonical Tag
    if '<link rel="canonical"' in content:
        content = re.sub(r'<link\s+rel="canonical"\s+href="[^"]*"\s*>', f'<link rel="canonical" href="{canonical_url}">', content)
    else:
        canonical_tag = f'\n    <!-- Canonical URL -->\n    <link rel="canonical" href="{canonical_url}">\n'
        content = content.replace('</head>', canonical_tag + '</head>')
        
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Optimization complete!")
