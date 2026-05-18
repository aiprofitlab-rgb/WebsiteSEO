import os
import re

def generate_sitemap():
    root_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    base_url = "https://aiprofitlab.io"
    
    urls = []
    
    # 1. Main pages
    main_pages = [
        {"loc": "/", "priority": "1.0", "ar": "/", "en": "/en/"},
        {"loc": "/en/", "priority": "1.0", "ar": "/", "en": "/en/"},
        {"loc": "/about/", "priority": "0.8", "ar": "/about/", "en": "/about-en/"},
        {"loc": "/about-en/", "priority": "0.8", "ar": "/about/", "en": "/about-en/"},
        {"loc": "/contact/", "priority": "0.8", "ar": "/contact/", "en": "/contact-en/"},
        {"loc": "/contact-en/", "priority": "0.8", "ar": "/contact/", "en": "/contact-en/"},
        {"loc": "/services/", "priority": "0.8", "ar": "/services/", "en": "/services-en/"},
        {"loc": "/services-en/", "priority": "0.8", "ar": "/services/", "en": "/services-en/"},
        {"loc": "/process/", "priority": "0.8", "ar": "/process/", "en": "/process-en/"},
        {"loc": "/process-en/", "priority": "0.8", "ar": "/process/", "en": "/process-en/"},
        {"loc": "/blog-ar/", "priority": "0.9", "ar": "/blog-ar/", "en": "/blog/"},
        {"loc": "/blog/", "priority": "0.9", "ar": "/blog-ar/", "en": "/blog/"},
    ]
    
    for p in main_pages:
        urls.append({
            "loc": base_url + p["loc"],
            "priority": p["priority"],
            "hreflang": [
                {"lang": "ar", "href": base_url + p["ar"]},
                {"lang": "en", "href": base_url + p["en"]}
            ]
        })

    # 2. Blog posts
    blog_dir_ar = os.path.join(root_dir, "blog/ar")
    blog_dir_en = os.path.join(root_dir, "blog/en")
    
    ar_posts = [f for f in os.listdir(blog_dir_ar) if f.endswith(".html")]
    en_posts = [f for f in os.listdir(blog_dir_en) if f.endswith(".html")]
    
    all_post_names = set([f.replace(".html", "") for f in ar_posts + en_posts])
    
    for post in all_post_names:
        has_ar = os.path.exists(os.path.join(blog_dir_ar, post + ".html"))
        has_en = os.path.exists(os.path.join(blog_dir_en, post + ".html"))
        
        if has_ar:
            hreflangs = []
            hreflangs.append({"lang": "ar", "href": f"{base_url}/blog/ar/{post}/"})
            if has_en:
                hreflangs.append({"lang": "en", "href": f"{base_url}/blog/en/{post}/"})
            
            urls.append({
                "loc": f"{base_url}/blog/ar/{post}/",
                "priority": "0.6",
                "hreflang": hreflangs
            })
            
        if has_en:
            hreflangs = []
            hreflangs.append({"lang": "en", "href": f"{base_url}/blog/en/{post}/"})
            if has_ar:
                hreflangs.append({"lang": "ar", "href": f"{base_url}/blog/ar/{post}/"})
                
            urls.append({
                "loc": f"{base_url}/blog/en/{post}/",
                "priority": "0.6",
                "hreflang": hreflangs
            })

    # 3. Academy
    # (Similar logic if academy posts exist)
    
    # 4. Demos
    demos = [
        {"ar": "/customized-ceo-dashboard-demo-ar/", "en": "/customized-ceo-dashboard-demo/"},
        {"ar": "/whatsapp-receptionist-demo-ar/", "en": "/en/whatsapp-receptionist-demo/"},
        {"ar": "/missed-call-simulator-ar/", "en": "/missed-call-simulator-en/"},
        {"ar": "/campaign-roi-simulator-ar/", "en": "/campaign-roi-simulator/"},
        {"ar": "/medflow-sales-automation-demo.html", "en": "/medflow-sales-automation-demo.html"},
    ]
    for d in demos:
        urls.append({
            "loc": base_url + d["ar"],
            "priority": "0.7",
            "hreflang": [
                {"lang": "ar", "href": base_url + d["ar"]},
                {"lang": "en", "href": base_url + d["en"]}
            ]
        })
        urls.append({
            "loc": base_url + d["en"],
            "priority": "0.7",
            "hreflang": [
                {"lang": "ar", "href": base_url + d["ar"]},
                {"lang": "en", "href": base_url + d["en"]}
            ]
        })

    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    
    from datetime import date
    today = date.today().isoformat()
    
    for u in urls:
        xml += '  <url>\n'
        xml += f'    <loc>{u["loc"]}</loc>\n'
        xml += f'    <lastmod>{today}</lastmod>\n'
        xml += '    <changefreq>weekly</changefreq>\n'
        xml += f'    <priority>{u["priority"]}</priority>\n'
        for h in u["hreflang"]:
            xml += f'    <xhtml:link rel="alternate" hreflang="{h["lang"]}" href="{h["href"]}"/>\n'
        xml += '  </url>\n'
        
    xml += '</urlset>'
    
    with open(os.path.join(root_dir, "sitemap.xml"), "w") as f:
        f.write(xml)
    print("Sitemap generated successfully.")

if __name__ == "__main__":
    generate_sitemap()
