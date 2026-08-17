import os
import re
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Run hub update logic directly
from update_blog_hubs import update_hub

blog_en_html = os.path.join(base_dir, "public_html", "blog", "index.html")
blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")
update_hub(blog_en_html, "en", blog_en_dir)

blog_ar_html = os.path.join(base_dir, "public_html", "blog-ar", "index.html")
blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")
update_hub(blog_ar_html, "ar", blog_ar_dir)

# 2. Run sitemap generation directly
public_html = os.path.join(base_dir, "public_html")
base_url = "https://aiprofitlab.io"

urls = [
    ("/", 1.0),
    ("/about/", 0.8),
    ("/contact/", 0.8),
    ("/process/", 0.8),
    ("/services/", 0.8),
    ("/blog-ar/", 0.8),
    ("/academy-ar/", 0.8),
    ("/campaign-roi-simulator-ar/", 0.7),
    ("/customized-ceo-dashboard-demo-ar/", 0.7),
    ("/missed-call-simulator-ar/", 0.7),
    ("/whatsapp-receptionist-demo-ar/", 0.7),
    ("/en/", 0.9),
    ("/en/about-en/", 0.8),
    ("/en/contact-en/", 0.8),
    ("/en/process-en/", 0.8),
    ("/en/services-en/", 0.8),
    ("/en/blog/", 0.8),
    ("/en/academy/", 0.8),
    ("/campaign-roi-simulator/", 0.7),
    ("/customized-ceo-dashboard-demo/", 0.7),
    ("/en/missed-call-simulator-en/", 0.7),
    ("/en/whatsapp-receptionist-demo/", 0.7),
]

blog_ar_path = os.path.join(public_html, "blog", "ar")
if os.path.exists(blog_ar_path):
    for file in os.listdir(blog_ar_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/ar/{slug}/", 0.6))

blog_en_path = os.path.join(public_html, "blog", "en")
if os.path.exists(blog_en_path):
    for file in os.listdir(blog_en_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/en/{slug}/", 0.6))

lastmod = datetime.now().strftime("%Y-%m-%d")
xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

for loc, priority in sorted(urls):
    xml_content += '  <url>\n'
    xml_content += f'    <loc>{base_url}{loc}</loc>\n'
    xml_content += f'    <lastmod>{lastmod}</lastmod>\n'
    xml_content += '    <changefreq>weekly</changefreq>\n'
    xml_content += f'    <priority>{priority}</priority>\n'
    xml_content += '  </url>\n'

xml_content += '</urlset>'

sitemap_file = os.path.join(public_html, "sitemap.xml")
with open(sitemap_file, "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"Generated sitemap.xml with {len(urls)} URLs.")

# 3. Make the new article visible to Aiden.
#    add_aiden_widget puts the chat widget on the new page; build_aiden_index
#    refreshes the knowledge file the chatbot backend reads, so Aiden can cite
#    the article as soon as the site is deployed.
import subprocess
import sys

for script in ("add_aiden_widget.py", "build_aiden_index.py"):
    result = subprocess.run(
        [sys.executable, os.path.join(base_dir, "tools", script)],
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode != 0:
        print(f"WARNING: {script} failed — Aiden may not know about the new article.")
