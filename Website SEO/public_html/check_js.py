import os
import glob
import subprocess
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)
has_errors = False

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
    
    for idx, script in enumerate(scripts):
        if not script.strip(): continue
        
        with open('tmp_script.js', 'w', encoding='utf-8') as f:
            f.write(script)
            
        res = subprocess.run(['node', '-c', 'tmp_script.js'], capture_output=True, text=True)
        if res.returncode != 0:
            if "await is only valid in async functions" in res.stderr:
                with open('tmp_script.js', 'w', encoding='utf-8') as f:
                    f.write('(async () => {\n' + script + '\n})();')
                res2 = subprocess.run(['node', '-c', 'tmp_script.js'], capture_output=True, text=True)
                if res2.returncode != 0:
                    print(f"Syntax Error in {file} script #{idx + 1}")
                    print(res2.stderr.splitlines()[0])
                    has_errors = True
            elif "Return statement is not allowed here" in res.stderr:
                with open('tmp_script.js', 'w', encoding='utf-8') as f:
                    f.write('function dummy() {\n' + script + '\n}')
                res2 = subprocess.run(['node', '-c', 'tmp_script.js'], capture_output=True, text=True)
                if res2.returncode != 0:
                    print(f"Syntax Error in {file} script #{idx + 1}")
                    has_errors = True
            else:
                print(f"Syntax Error in {file} script #{idx + 1}")
                print(res.stderr.splitlines()[0])
                has_errors = True

if not has_errors:
    print("All scripts passed syntax check!")
