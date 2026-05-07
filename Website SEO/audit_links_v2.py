import os
import re

root_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def check_links_v2():
    broken_links = []
    
    physical_files = set()
    for root, dirs, files in os.walk(root_path):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), root_path)
            rel_path = rel_path.replace("\\", "/")
            physical_files.add("/" + rel_path)

    for root, dirs, files in os.walk(root_path):
        for file in files:
            if not file.endswith(".html"): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            links = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', content)
            
            for link in links:
                if link.startswith(('http', '#', 'mailto:', 'tel:', 'data:')): continue
                
                path_part = link.split('#')[0].split('?')[0]
                
                # Normalize clean URL to .html lookup
                lookup = path_part
                if path_part.endswith('/'):
                    # Case 1: /en/services-en/ -> services-en.html
                    if path_part.startswith('/en/'):
                        lookup = "/" + path_part[4:].rstrip('/') + ".html"
                    # Case 2: /blog/en/post/ -> /blog/en/post.html
                    elif path_part.startswith(('/blog/', '/academy/')):
                        lookup = path_part.rstrip('/') + ".html"
                    # Case 3: /services/ -> /services.html
                    else:
                        lookup = path_part.rstrip('/') + ".html"
                
                # Check existence
                if lookup not in physical_files:
                    # Check for directory index
                    if path_part.rstrip('/') + "/index.html" in physical_files:
                        continue
                    if path_part == "" or path_part == "/":
                        continue
                    broken_links.append((file, link, lookup))

    if not broken_links:
        print("SUCCESS: All internal links verified!")
    else:
        print(f"--- REMAINING BROKEN LINKS ---")
        for f, l, look in set(broken_links):
            print(f"In {f}: {l} (Looked for {look})")

if __name__ == "__main__":
    check_links_v2()
