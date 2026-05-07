import os
import re

root_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def check_links():
    broken_links = []
    found_relative = []
    found_extensions = []
    
    # Files that physically exist
    physical_files = set()
    for root, dirs, files in os.walk(root_path):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), root_path)
            # Standardize to forward slashes
            rel_path = rel_path.replace("\\", "/")
            physical_files.add("/" + rel_path)

    for root, dirs, files in os.walk(root_path):
        for file in files:
            if not file.endswith(".html"): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all href and src
            links = re.findall(r'(?:href|src)=["\']([^"\']+)["\']', content)
            
            for link in links:
                # Skip external, hash, mailto, tel, data
                if link.startswith(('http', '#', 'mailto:', 'tel:', 'data:')): continue
                
                # Check for relative paths
                if not link.startswith('/'):
                    found_relative.append((file, link))
                
                # Check for .html extension in internal links (excluding assets)
                if link.endswith('.html') and not link.startswith(('/blog/', '/academy/', '/favicon')):
                     found_extensions.append((file, link))
                
                # Check for 404
                # Normalize link for lookup
                path_part = link.split('#')[0].split('?')[0]
                if not path_part.endswith('/') and not '.' in os.path.basename(path_part):
                    # It's a clean URL like /services/
                    lookup = path_part.rstrip('/') + ".html"
                else:
                    lookup = path_part
                
                if lookup not in physical_files:
                    # Special check for directories
                    if lookup + "/index.html" in physical_files or lookup + "index.html" in physical_files:
                        continue
                    broken_links.append((file, link, lookup))

    print(f"--- BROKEN LINKS ---")
    for f, l, look in set(broken_links):
        print(f"In {f}: {l} (Target {look} not found)")
        
    print(f"\n--- RELATIVE LINKS (Should be absolute) ---")
    for f, l in set(found_relative):
        print(f"In {f}: {l}")
        
    print(f"\n--- LINKS WITH .HTML (Should be extensionless) ---")
    for f, l in set(found_extensions):
        print(f"In {f}: {l}")

if __name__ == "__main__":
    check_links()
