import os
import re

path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def finalize_all_links():
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith('.html'): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            def global_replacer(match):
                attr = match.group(1)
                link = match.group(2)
                
                # Skip external, hash, tel, mailto, data
                if link.startswith(('http', '#', 'mailto:', 'tel:', 'data:')):
                    return match.group(0)
                
                # If it's already absolute, just return it
                if link.startswith('/'):
                    return match.group(0)
                
                # Convert relative to absolute
                # For blog/academy posts, ../../ is common. We just want the root.
                clean_link = link.replace('../../', '/').replace('../', '/')
                if not clean_link.startswith('/'):
                    clean_link = '/' + clean_link
                
                # Clean up double slashes
                clean_link = re.sub(r'/+', '/', clean_link)
                
                # Handle Clean URLs (remove .html and add trailing slash for pages)
                # But keep .webp, .svg, .png, etc.
                if clean_link.endswith('.html') and not clean_link.startswith(('/blog/', '/academy/')):
                    clean_link = clean_link.replace('.html', '/')
                
                # Specifically for blog/academy internal inter-linking
                # /blog/en/post.html -> /blog/en/post/
                if clean_link.endswith('.html') and clean_link.startswith(('/blog/', '/academy/')):
                     clean_link = clean_link.replace('.html', '/')
                
                # Handle legacy names that are now redirected
                mapping = {
                    '/en.html': '/en/',
                    '/blog.html': '/blog/',
                    '/blog_ar.html': '/blog-ar/',
                    '/academy_ar.html': '/academy-ar/',
                    '/about-en.html': '/en/about-en/',
                    '/services-en.html': '/en/services-en/',
                    '/contact-en.html': '/en/contact-en/',
                    '/process-en.html': '/en/process-en/',
                    '/about.html': '/about/',
                    '/services.html': '/services/',
                    '/contact.html': '/contact/',
                    '/process.html': '/process/',
                    '/Campaign_ROI_Simulator.html': '/campaign-roi-simulator/',
                    '/Campaign_ROI_Simulator-ar.html': '/campaign-roi-simulator-ar/',
                    '/whatsapp_receptionist_demo.html': '/whatsapp-receptionist-demo/',
                    '/whatsapp_receptionist_demo_ar.html': '/whatsapp-receptionist-demo-ar/',
                    '/Missed-Call-Simulator-en.html': '/en/missed-call-simulator-en/',
                    '/Missed-Call-Simulator-ar.html': '/missed-call-simulator-ar/',
                    '/Customized_CEO_Dashboard_demo.html': '/customized-ceo-dashboard-demo/',
                    '/Customized_CEO_Dashboard_demo-ar.html': '/customized-ceo-dashboard-demo-ar/'
                }
                if clean_link in mapping:
                    clean_link = mapping[clean_link]
                
                return f'{attr}="{clean_link}"'

            new_content = re.sub(r'(href|src)=["\']([^"\']+)["\']', global_replacer, content)
            
            # Canonical URLs also need fixing
            new_content = re.sub(r'(href)="https://aiprofitlab\.io/([^"]+)"', global_replacer, new_content)

            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Finalized links in: {file}")

if __name__ == "__main__":
    finalize_all_links()
