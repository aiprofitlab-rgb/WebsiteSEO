import os
import re
import subprocess

file = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/en/index.html'

with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)

for idx, script in enumerate(scripts):
    if not script.strip(): 
        continue
    
    with open('tmp_script.js', 'w', encoding='utf-8') as f:
        f.write(script)
        
    res = subprocess.run(['node', '-c', 'tmp_script.js'], capture_output=True, text=True)
    if res.returncode != 0:
        wrapped = f'(async () => {{\n{script}\n}})();'
        with open('tmp_script.js', 'w', encoding='utf-8') as f:
            f.write(wrapped)
        res2 = subprocess.run(['node', '--check', 'tmp_script.js'], capture_output=True, text=True)
        if res2.returncode != 0:
            print(f"\n=== Script #{idx + 1} ===")
            print(res2.stderr)
    else:
        pass

