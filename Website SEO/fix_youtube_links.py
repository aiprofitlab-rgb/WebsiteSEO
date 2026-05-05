import glob
import os

files_to_check = [
    'public_html/blog/en/2026-05-05-oman-vision-2040-ai-goals.html',
    'public_html/blog/ar/2026-05-05-oman-vision-2040-ai-goals.html',
    'public_html/blog/en/2026-05-05-omantel-otech-sovereign-cloud.html',
    'public_html/blog/ar/2026-05-05-omantel-otech-sovereign-cloud.html'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content.replace('dQw4w9WgXcQ', 'Xq5N9D2VfGk')
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed youtube link in {file_path}")
