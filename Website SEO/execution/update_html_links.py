import os
import re

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False
        
    original_content = content
    
    # 1. Handle index.html cases
    # href="/index.html" -> href="/"
    # href="/en/index.html" -> href="/en/"
    # href="https://aiprofitlab.io/index.html" -> href="https://aiprofitlab.io/"
    content = re.sub(r'(href|content)=([\'"])(.*?)(?:/)?index\.html\2', lambda m: f'{m.group(1)}={m.group(2)}{m.group(3)}/{m.group(2)}' if not m.group(3).endswith('/') else f'{m.group(1)}={m.group(2)}{m.group(3)}{m.group(2)}', content)
    
    # Special cleanups if the above leaves double slashes or similar
    content = content.replace('href="//"', 'href="/"')
    content = content.replace("href='//'", "href='/'")
                     
    # 2. Handle standard .html cases ending in .html
    # href="/about.html" -> href="/about/"
    def replace_html(match):
        attr = match.group(1)
        quote = match.group(2)
        url = match.group(3)
        
        # Don't modify external links that end in .html unless they are aiprofitlab.io
        if url.startswith('http') and 'aiprofitlab.io' not in url:
            return match.group(0)
            
        if not url.endswith('/'):
            url += '/'
            
        return f'{attr}={quote}{url}{quote}'
        
    content = re.sub(r'(href|content|hreflang)=([\'"])(.*?)\.html\2', replace_html, content)
    
    # 3. Handle XML/sitemap loc tags
    # <loc>https://aiprofitlab.io/about.html</loc> -> <loc>https://aiprofitlab.io/about/</loc>
    def replace_loc(match):
        url = match.group(1)
        
        if url.endswith('/index'):
            url = url[:-5] # remove index
        elif url.endswith('index'):
            url = url[:-5] + '/'
        elif not url.endswith('/'):
            url += '/'
            
        return f'<loc>{url}</loc>'
        
    content = re.sub(r'<loc>(.*?)\.html</loc>', replace_loc, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    directory = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html'
    modified_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.js', '.xml')):
                filepath = os.path.join(root, file)
                if process_file(filepath):
                    print(f"Updated: {filepath}")
                    modified_count += 1
                    
    print(f"Total files updated: {modified_count}")

if __name__ == "__main__":
    main()
