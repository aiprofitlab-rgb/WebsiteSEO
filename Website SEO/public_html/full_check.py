import os, glob, subprocess, re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)
errors = {}

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
    file_errors = []
    for idx, script in enumerate(scripts):
        if not script.strip(): continue
        # Skip JSON-LD (type="application/ld+json")
        positions = [m.start() for m in re.finditer(r'<script\b([^>]*)>', content, re.IGNORECASE)]
        if idx < len(positions):
            tag = content[positions[idx]:positions[idx]+200]
            if 'application/ld+json' in tag: continue
        with open('tmp_script.js', 'w', encoding='utf-8') as f:
            f.write(script)
        res = subprocess.run(['node', '-c', 'tmp_script.js'], capture_output=True, text=True)
        if res.returncode != 0:
            wrapped = f'(async () => {{\n{script}\n}})();'
            with open('tmp_script.js', 'w', encoding='utf-8') as f:
                f.write(wrapped)
            res2 = subprocess.run(['node', '--check', 'tmp_script.js'], capture_output=True, text=True)
            if res2.returncode != 0:
                err_line = res2.stderr.splitlines()[0] if res2.stderr else 'unknown'
                file_errors.append(f"  script #{idx+1}: {err_line}")
    if file_errors:
        errors[file] = file_errors

if errors:
    for f, errs in errors.items():
        print(f"\n{f}")
        for e in errs:
            print(e)
else:
    print("ALL CLEAN!")
