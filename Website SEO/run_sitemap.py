import os
from datetime import datetime

public_html = "public_html"
base_url = "https://aiprofitlab.io"

urls = [
    # --- English, the v4 set (launched 2026-08-21) --------------------------
    ("/", 1.0),
    ("/en/services/", 0.9),
    ("/en/process/", 0.8),
    ("/en/about/", 0.8),
    ("/en/contact/", 0.8),
    ("/en/demos/", 0.7),
    ("/en/simulators/", 0.7),
    ("/en/checkout/", 0.7),
    ("/blog/", 0.8),
    ("/en/academy/", 0.8),
    ("/en/smart-website-offer.html", 0.9),

    # --- Arabic, still on the previous skin ---------------------------------
    ("/ar/", 0.9),
    ("/services/", 0.8),
    ("/process/", 0.8),
    ("/about/", 0.8),
    ("/contact/", 0.8),
    ("/blog-ar/", 0.8),
    ("/academy-ar/", 0.8),
    ("/campaign-roi-simulator-ar/", 0.7),
    ("/customized-ceo-dashboard-demo-ar/", 0.7),
    ("/missed-call-simulator-ar/", 0.7),
    ("/whatsapp-receptionist-demo-ar/", 0.7),
    ("/smart-website-offer.html", 0.9),

    # /en/order/ is a payment-return page and /en/checkout/?plan=... are query
    # variants of one URL - neither belongs in a sitemap. The English demo and
    # simulator pages that used to be listed here now 301 into the two above.
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

academy_ar_path = os.path.join(public_html, "academy", "ar")
if os.path.exists(academy_ar_path):
    for file in os.listdir(academy_ar_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/academy/ar/{slug}/", 0.6))

academy_en_path = os.path.join(public_html, "academy", "en")
if os.path.exists(academy_en_path):
    for file in os.listdir(academy_en_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/academy/en/{slug}/", 0.6))

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

print(f"SUCCESS: Generated {sitemap_file} with {len(urls)} URLs.")
