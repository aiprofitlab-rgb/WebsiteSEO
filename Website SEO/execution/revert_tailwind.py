import os
import glob

html_files = glob.glob("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html", recursive=True)

modified_files = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Revert tailwind defer
    content = content.replace('<script defer src="https://cdn.tailwindcss.com"></script>', '<script src="https://cdn.tailwindcss.com"></script>')
    content = content.replace('<script defer src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>', '<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>')
    
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files += 1

print(f"Reverted {modified_files} HTML files to load Tailwind synchronously.")
