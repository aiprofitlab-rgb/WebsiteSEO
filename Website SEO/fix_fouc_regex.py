import os
import glob
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(path, "**/*.html"), recursive=True)

fouc_style = "\n<style>body { visibility: hidden; }</style>\n"
fouc_script = "\n<script>document.body.style.visibility = 'visible';</script>\n"

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Add FOUC style just after <head>
    if 'body { visibility: hidden; }' not in content:
        content = re.sub(r'(<head.*?>)', r'\1' + fouc_style, content, count=1, flags=re.IGNORECASE)

    # 2. Add FOUC script just before </body>
    if "document.body.style.visibility = 'visible';" not in content:
        content = re.sub(r'(</body>)', fouc_script + r'\1', content, count=1, flags=re.IGNORECASE)

    # 3. Add defer to non-critical JS scripts if not present
    def add_defer(match):
        script_tag = match.group(0)
        # Skip json scripts
        if 'application/ld+json' in script_tag:
            return script_tag
        if ' src=' in script_tag and 'defer' not in script_tag and 'async' not in script_tag:
            return script_tag.replace('<script', '<script defer')
        return script_tag
    
    content = re.sub(r'<script\b[^>]*>', add_defer, content)

    # 4. Move CSS links to the top of head (after meta charset)
    # This is a bit complex with regex, but we can try to extract all <link rel="stylesheet"> and put them high up.
    # The user says "main stylesheet" -> often tailwind is used. Here tailwind is loaded via script.
    
    # Let's save if changed
    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed FOUC in {os.path.basename(html_file)}")

print("FOUC fix completed.")
