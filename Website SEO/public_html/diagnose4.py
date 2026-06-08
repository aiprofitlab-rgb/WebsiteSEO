import re, subprocess, os

files_to_check = {
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html': 5,
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html': 9,
}

tmpfile = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/tmp_fix.js'

for filepath, script_idx in files_to_check.items():
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
    script = scripts[script_idx]
    with open(tmpfile, 'w', encoding='utf-8') as f:
        f.write(f'(async () => {{\n{script}\n}})();')
    res = subprocess.run(['node', '--check', tmpfile], capture_output=True, text=True)
    if res.returncode != 0:
        lines = f'(async () => {{\n{script}\n}})();'.splitlines()
        lineno_match = re.search(r':(\d+)', res.stderr)
        if lineno_match:
            ln = int(lineno_match.group(1))
            print(f"\n=== {os.path.basename(filepath)} script #{script_idx+1} err@{ln} ===")
            start = max(0, ln-4)
            end = min(len(lines), ln+4)
            for j, line in enumerate(lines[start:end], start=start+1):
                marker = ">>>" if j == ln else "   "
                print(f"{marker} {j}: {line}")
