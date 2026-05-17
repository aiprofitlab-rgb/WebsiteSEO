import os
import subprocess
from datetime import datetime

public_html = "public_html"
base_url = "https://aiprofitlab.io"

urls = [
    # Static pages (Arabic)
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

    # Static pages (English)
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

# Add Blog posts (Arabic)
blog_ar_path = os.path.join(public_html, "blog", "ar")
if os.path.exists(blog_ar_path):
    for file in os.listdir(blog_ar_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/ar/{slug}/", 0.6))

# Add Blog posts (English)
blog_en_path = os.path.join(public_html, "blog", "en")
if os.path.exists(blog_en_path):
    for file in os.listdir(blog_en_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/en/{slug}/", 0.6))

# Add Academy pages (Arabic)
academy_ar_path = os.path.join(public_html, "academy", "ar")
if os.path.exists(academy_ar_path):
    for file in os.listdir(academy_ar_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/academy/ar/{slug}/", 0.6))

# Add Academy pages (English)
academy_en_path = os.path.join(public_html, "academy", "en")
if os.path.exists(academy_en_path):
    for file in os.listdir(academy_en_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/academy/en/{slug}/", 0.6))

# Generate XML
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

with open(os.path.join(public_html, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"Generated sitemap.xml with {len(urls)} URLs.")

# Automatically submit to IndexNow
print("Calling IndexNow submission script...")
try:
    subprocess.run(["python3", "execution/submit_indexnow.py"], check=True)
except Exception as e:
    print(f"Failed to submit to IndexNow: {e}")
