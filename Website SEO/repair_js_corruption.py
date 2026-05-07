import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def fix_broken_js_comments_and_protocols():
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(('.html', '.js')): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Fix protocols first
            new_content = content.replace("https:/", "https://").replace("http:/", "http://")
            
            # 2. Fix JS comments that were mangled from // to /
            # We look for lines that start with optional whitespace, then a single /, then a space, then a capital letter or common comment start.
            # Or just / followed by a space and a word at the start of a line.
            
            # Pattern: Start of line, optional spaces, single slash, space, any word character
            new_content = re.sub(r'^(\s*)/ (\w)', r'\1// \2', new_content, flags=re.MULTILINE)
            
            # Also handle cases where it might be at the end of a line or after a semicolon
            # But the grep showed them at the start of lines mostly.
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed JS/Protocols in: {file}")

if __name__ == "__main__":
    fix_broken_js_comments_and_protocols()
