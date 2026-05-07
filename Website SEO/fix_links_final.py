import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def fix_broken_links_final():
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.html'): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Fix mixed-case links
            content = content.replace("/Campaign_ROI_Simulator.html", "/campaign-roi-simulator/")
            content = content.replace("/Campaign_ROI_Simulator-ar.html", "/campaign-roi-simulator-ar/")
            content = content.replace("/whatsapp_receptionist_demo.html", "/whatsapp-receptionist-demo/")
            content = content.replace("/whatsapp_receptionist_demo_ar.html", "/whatsapp-receptionist-demo-ar/")
            content = content.replace("/Missed-Call-Simulator-en.html", "/en/missed-call-simulator-en/")
            content = content.replace("/Missed-Call-Simulator-ar.html", "/missed-call-simulator-ar/")
            
            # 2. Fix Blog Hub references
            content = content.replace("blog.html", "blog/")
            content = content.replace("blog_ar.html", "blog-ar/")
            
            # 3. Fix En Subpaths in index.html and others
            # e.g. href="services-en.html" -> href="/en/services-en/"
            def en_link_fixer(match):
                attr = match.group(1)
                link = match.group(2)
                
                # If it's -en.html and doesn't have /en/ already
                if link.endswith('-en.html') and not link.startswith('/en/'):
                    slug = link.replace('.html', '')
                    return f'{attr}="/en/{slug}/"'
                
                # If it's a clean URL without /en/ but should have it
                if link in ['services-en/', 'about-en/', 'contact-en/', 'process-en/']:
                    return f'{attr}="/en/{link}"'
                
                return match.group(0)

            new_content = re.sub(r'(href|src)=["\']([^"\']+)["\']', en_link_fixer, content)
            
            # 4. Remove all remaining .html from internal links
            def clean_html_links(match):
                attr = match.group(1)
                link = match.group(2)
                if link.endswith('.html') and not link.startswith(('/blog/', '/academy/', '/favicon', 'http', 'https')):
                    clean = link.replace('.html', '')
                    if not clean.endswith('/'): clean += '/'
                    if not clean.startswith('/'): clean = '/' + clean
                    return f'{attr}="{clean}"'
                return match.group(0)

            new_content = re.sub(r'(href)=["\']([^"\']+)["\']', clean_html_links, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Fixed links in: {file}")

if __name__ == "__main__":
    fix_broken_links_final()
