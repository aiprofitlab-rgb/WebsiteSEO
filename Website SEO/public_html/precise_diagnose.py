import re, subprocess, os

files_to_check = {
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html': [5],
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html': [5],
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html': [5],
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html': [5],
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html': [5],
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html': [5],
}

tmpfile = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/tmp_fix.js'

for filepath, script_indices in files_to_check.items():
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
    for i in script_indices:
        script = scripts[i]
        with open(tmpfile, 'w', encoding='utf-8') as f:
            f.write(f'(async () => {{\n{script}\n}})();')
        res = subprocess.run(['node', '--check', tmpfile], capture_output=True, text=True)
        if res.returncode != 0:
            # Find the error line
            err = res.stderr
            lines = f'(async () => {{\n{script}\n}})();'.splitlines()
            lineno_match = re.search(r':(\d+)', err)
            if lineno_match:
                ln = int(lineno_match.group(1))
                print(f"\n=== {os.path.basename(filepath)} script #{i+1}, error at line {ln} ===")
                start = max(0, ln-4)
                end = min(len(lines), ln+3)
                for j, line in enumerate(lines[start:end], start=start+1):
                    marker = ">>>" if j == ln else "   "
                    print(f"{marker} {j}: {line}")
