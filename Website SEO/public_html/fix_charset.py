import os
import glob
import re

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove any existing <meta charset="UTF-8">
    # We should handle cases like <meta charset="utf-8">, <meta charset="UTF-8" />
    content_without_meta = re.sub(r'<meta\s+charset\s*=\s*["\']utf-8["\']\s*/?>', '', content, flags=re.IGNORECASE)
    
    # Also handle <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> just in case
    content_without_meta = re.sub(r'<meta\s+http-equiv\s*=\s*["\']Content-Type["\']\s+content\s*=\s*["\']text/html;\s*charset=utf-8["\']\s*/?>', '', content_without_meta, flags=re.IGNORECASE)

    # Now, find the <head> tag and insert <meta charset="UTF-8"> right after it
    # <head> can have attributes like <head lang="en">
    
    def replacer(match):
        return match.group(0) + '\n    <meta charset="UTF-8">'
    
    new_content = re.sub(r'<head[^>]*>', replacer, content_without_meta, count=1, flags=re.IGNORECASE)

    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes needed for {filepath}")

if __name__ == '__main__':
    html_files = glob.glob('**/*.html', recursive=True)
    for f in html_files:
        process_file(f)
