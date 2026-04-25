import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

print("Reverting image extensions in HTML files since WebP conversion failed...")
html_files = glob.glob(os.path.join(path, "*.html"))

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We replaced .jpg and .png with .webp. We need to revert them based on known images.
    # Known JPGs
    content = content.replace('hero-bg.webp', 'hero-bg.jpg')
    content = content.replace('audit-bg.webp', 'audit-bg.jpg')
    content = content.replace('IMG_7275.webp', 'IMG_7275.jpg')
    content = content.replace('twitter-image.webp', 'twitter-image.jpg')
    content = content.replace('og-image.webp', 'og-image.jpg')
    
    # Known PNGs (blog images and logos)
    # Just replace all remaining .webp with .png as a fallback since almost all generated images were PNGs
    content = content.replace('.webp', '.png')
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Revert complete! Canonical tags remain intact.")
