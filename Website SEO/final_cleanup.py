import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def final_global_cleanup():
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(('.html', '.js', '.xml')): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Fix Triple Slashes in protocols
            new_content = content.replace("https:/// ", "https://").replace("http:/// ", "http://") # In case of space
            new_content = new_content.replace("https:///", "https://").replace("http:///", "http://")
            
            # 2. Fix Double Slashes again just to be safe
            new_content = new_content.replace("https:/www", "https://www").replace("http:/www", "http://www")
            
            # 3. Fix the specific mixed-case banner name I found
            new_content = new_content.replace("Nahid_Business_Banner.png", "nahid-business-banner.png")
            
            # 4. Fix domain typos
            new_content = new_content.replace("aiprofitlab.com", "aiprofitlab.io")
            
            # 5. Fix og:url cases
            def og_replacer(match):
                url = match.group(1)
                return f'content="{url.replace("_", "-").lower()}"'
            new_content = re.sub(r'content="https://aiprofitlab\.io/([^"]+)"', og_replacer, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Final cleanup in: {file}")

if __name__ == "__main__":
    final_global_cleanup()
