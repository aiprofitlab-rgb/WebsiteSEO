import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def fix_image_references():
    image_files = {}
    # Build a map of lowercase-hyphenated names to actual filenames on disk
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
                prefix = match.group(1) # src= or url(
                quote = match.group(2) or ''
                link = match.group(3)
                suffix = match.group(4) or ''
                
                # Only process images
                if not link.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                    return match.group(0)
                
                basename = os.path.basename(link)
                dirname = os.path.dirname(link)
                
                clean_basename = basename.lower().replace('_', '-')
                
                if clean_basename in image_files:
                    new_basename = image_files[clean_basename]
                    new_link = os.path.join(dirname, new_basename)
                    # Standardize slash
                    new_link = new_link.replace('\\', '/')
                    return f'{prefix}{quote}{new_link}{quote}{suffix}'
                
                return match.group(0)

            # Match src="..." or url(...)
            new_content = re.sub(r'(src|href)=["\']([^"\']+)["\']', lambda m: img_replacer(m.group(1), m.group(2), m.group(2)), content)
            # Re-running with a better regex for url() too
            new_content = re.sub(r'(url\()(["\']?)([^"\')]+)(["\']?\))', img_replacer, new_content)
            # Simple attribute match
            def attr_replace(match):
                 attr = match.group(1)
                 link = match.group(2)
                 if link.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
                     basename = os.path.basename(link)
                     dirname = os.path.dirname(link)
                     clean_basename = basename.lower().replace('_', '-')
                     if clean_basename in image_files:
                         return f'{attr}="{os.path.join(dirname, image_files[clean_basename]).replace("\\", "/")}"'
                 return match.group(0)
            
            new_content = re.sub(r'(src|href)=["\']([^"\']+)["\']', attr_replace, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed image refs in: {file}")

if __name__ == "__main__":
    fix_image_references()
