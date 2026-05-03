import os
import re
import glob

files = glob.glob('public_html/**/*.html', recursive=True)

target_str = "budget: document.getElementById('budget')?.value || '',"
insert_str = '''source: Array.from(document.querySelectorAll('input[name="source"]:checked')).map(cb => cb.value).join(', '),
                otherSource: document.getElementById('otherSource')?.value || '',
                '''

for file_path in files:
    if "blog/" in file_path: continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    if target_str in content and "otherSource: document.getElementById" not in content:
        content = content.replace(target_str, insert_str + target_str)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated JS in {file_path}")
