import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def fix_image_references_v2():
    image_files = {}
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                clean = f.lower().replace('_', '-')
                image_files[clean] = f

    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.html'): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            def img_replacer(match):
                prefix = match.group(1) 
                quote = match.group(2) or ''
                link = match.group(3)
                suffix = match.group(4) or ''
                
                if not link.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                    return match.group(0)
                
                basename = os.path.basename(link)
                dirname = os.path.dirname(link)
                clean_basename = basename.lower().replace('_', '-')
                
                if clean_basename in image_files:
                    new_link = os.path.join(dirname, image_files[clean_basename]).replace("\\", "/")
                    return f'{prefix}{quote}{new_link}{quote}{suffix}'
                return match.group(0)

            # Fix url() and src=
            new_content = re.sub(r'(url\()(["\']?)([^"\')]+)(["\']?\))', img_replacer, content)
            
            def attr_replace(match):
                attr = match.group(1)
                link = match.group(2)
                if link.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                    basename = os.path.basename(link)
                    dirname = os.path.dirname(link)
                    clean_basename = basename.lower().replace('_', '-')
                    if clean_basename in image_files:
                        new_path = os.path.join(dirname, image_files[clean_basename]).replace("\\", "/")
                        return f'{attr}="{new_path}"'
                return match.group(0)
            
            new_content = re.sub(r'(src|href)=["\']([^"\']+)["\']', attr_replace, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed image refs in: {file}")

if __name__ == "__main__":
    fix_image_references_v2()
