import os
import re

def process_html_file(filepath, base_dir):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, base_dir)
    rel_path = rel_path.replace('\\', '/')
    
    if rel_path.endswith('index.html'):
        if rel_path == 'index.html':
            clean_path = '/'
        else:
            clean_path = '/' + rel_path[:-10]
    else:
        clean_path = '/' + rel_path[:-5]

    # Clean existing canonical tags (any order of attributes)
    content = re.sub(r'<link[^>]*rel=["\']canonical["\'][^>]*>', '', content, flags=re.IGNORECASE)
    
    # Clean existing hreflang tags (any order of attributes)
    content = re.sub(r'<link[^>]*hreflang=["\'][^>]*>', '', content, flags=re.IGNORECASE)

    canonical_tag = f'<link rel="canonical" href="https://aiprofitlab.io{clean_path}" />'
    
    hreflang_tags = ""
    if 'blog/en/' in rel_path or 'blog/ar/' in rel_path:
        base_slug = rel_path.replace('blog/en/', '').replace('blog/ar/', '').replace('.html', '')
        hreflang_en = f'<link rel="alternate" hreflang="en" href="https://aiprofitlab.io/blog/en/{base_slug}" />'
        hreflang_ar = f'<link rel="alternate" hreflang="ar" href="https://aiprofitlab.io/blog/ar/{base_slug}" />'
        hreflang_xd = f'<link rel="alternate" hreflang="x-default" href="https://aiprofitlab.io/blog/en/{base_slug}" />'
        hreflang_tags = f"{hreflang_en}\n    {hreflang_ar}\n    {hreflang_xd}"
    
    elif rel_path.startswith('en/') or rel_path.startswith('ar/') or rel_path in ['index.html', 'about.html', 'contact.html', 'services.html', 'process.html'] or rel_path.endswith('-en.html') or rel_path.endswith('-ar.html'):
        if rel_path.startswith('en/'):
            path = rel_path[3:-5]
            if path == 'index': path = ''
        elif rel_path.startswith('ar/'):
            path = rel_path[3:-5]
            if path == 'index': path = ''
        else:
            path = rel_path[:-5]
            if path.endswith('-en'):
                path = path[:-3]
            elif path.endswith('-ar'):
                path = path[:-3]
            if path == 'index': path = ''
            
        path_str = path if path == '' else f"{path}"
        
        hreflang_en = f'<link rel="alternate" hreflang="en" href="https://aiprofitlab.io/en/{path_str}" />'
        hreflang_ar = f'<link rel="alternate" hreflang="ar" href="https://aiprofitlab.io/ar/{path_str}" />'
        hreflang_xd = f'<link rel="alternate" hreflang="x-default" href="https://aiprofitlab.io/en/{path_str}" />'
        
        hreflang_tags = f"{hreflang_en}\n    {hreflang_ar}\n    {hreflang_xd}"
        
    tags_to_inject = f"{canonical_tag}"
    if hreflang_tags:
        tags_to_inject += f"\n    {hreflang_tags}"
        
    if '</head>' in content:
        content = content.replace('</head>', f"    {tags_to_inject}\n</head>")
    elif '</HEAD>' in content:
        content = content.replace('</HEAD>', f"    {tags_to_inject}\n</HEAD>")
        
    # Clean up empty lines left by re.sub
    content = re.sub(r'\n\s*\n\s*</head>', '\n</head>', content, flags=re.IGNORECASE)
    # Also clean up multiple empty lines that might have been created where the old tags were
    content = re.sub(r'(\n\s*)+\n', '\n', content)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public_html'))
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.html'):
                process_html_file(os.path.join(root, file), base_dir)
    print("Done injecting SEO tags.")
