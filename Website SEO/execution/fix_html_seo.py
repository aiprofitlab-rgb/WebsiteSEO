import os
import re

def fix_html_seo():
    root_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    base_url = "https://aiprofitlab.io"
    
    # Define mapping rules for main pages
    main_pages_map = {
        "/index.html": {"ar": "/", "en": "/en/"},
        "/en/index.html": {"ar": "/", "en": "/en/"},
        "/about.html": {"ar": "/about/", "en": "/about-en/"},
        "/about-en.html": {"ar": "/about/", "en": "/about-en/"},
        "/contact.html": {"ar": "/contact/", "en": "/contact-en/"},
        "/contact-en.html": {"ar": "/contact/", "en": "/contact-en/"},
        "/services.html": {"ar": "/services/", "en": "/services-en/"},
        "/services-en.html": {"ar": "/services/", "en": "/services-en/"},
        "/process.html": {"ar": "/process/", "en": "/process-en/"},
        "/process-en.html": {"ar": "/process/", "en": "/process-en/"},
        "/blog-ar/index.html": {"ar": "/blog-ar/", "en": "/blog/"},
        "/blog/index.html": {"ar": "/blog-ar/", "en": "/blog/"},
    }

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if not file.endswith(".html"):
                continue
                
            file_path = os.path.join(root, file)
            rel_path = "/" + os.path.relpath(file_path, root_dir)
            
            # Skip some files if needed
            if "google" in file.lower(): continue
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine Canonical and Hreflang
            canonical = ""
            hreflangs = []
            
            if rel_path in main_pages_map:
                m = main_pages_map[rel_path]
                lang = "ar" if "en" not in rel_path else "en"
                canonical = base_url + m[lang]
                hreflangs = [
                    {"lang": "ar", "href": base_url + m["ar"]},
                    {"lang": "en", "href": base_url + m["en"]}
                ]
            elif "/blog/ar/" in rel_path:
                post_name = file.replace(".html", "")
                canonical = f"{base_url}/blog/ar/{post_name}/"
                hreflangs.append({"lang": "ar", "href": f"{base_url}/blog/ar/{post_name}/"})
                # Check if English version exists
                en_file = file_path.replace("/blog/ar/", "/blog/en/")
                if os.path.exists(en_file):
                    hreflangs.append({"lang": "en", "href": f"{base_url}/blog/en/{post_name}/"})
            elif "/blog/en/" in rel_path:
                post_name = file.replace(".html", "")
                canonical = f"{base_url}/blog/en/{post_name}/"
                hreflangs.append({"lang": "en", "href": f"{base_url}/blog/en/{post_name}/"})
                # Check if Arabic version exists
                ar_file = file_path.replace("/blog/en/", "/blog/ar/")
                if os.path.exists(ar_file):
                    hreflangs.append({"lang": "ar", "href": f"{base_url}/blog/ar/{post_name}/"})
            elif "/academy/ar/" in rel_path:
                post_name = file.replace(".html", "")
                canonical = f"{base_url}/academy/ar/{post_name}/"
                hreflangs.append({"lang": "ar", "href": f"{base_url}/academy/ar/{post_name}/"})
                # Check if English version exists
                en_file = file_path.replace("/academy/ar/", "/academy/en/")
                if os.path.exists(en_file):
                    hreflangs.append({"lang": "en", "href": f"{base_url}/academy/en/{post_name}/"})
            elif "/academy/en/" in rel_path:
                post_name = file.replace(".html", "")
                canonical = f"{base_url}/academy/en/{post_name}/"
                hreflangs.append({"lang": "en", "href": f"{base_url}/academy/en/{post_name}/"})
                # Check if Arabic version exists
                ar_file = file_path.replace("/academy/en/", "/academy/ar/")
                if os.path.exists(ar_file):
                    hreflangs.append({"lang": "ar", "href": f"{base_url}/academy/ar/{post_name}/"})
            else:
                # Default logic for other pages
                clean_path = rel_path.replace(".html", "").replace("index", "")
                if not clean_path.endswith("/"): clean_path += "/"
                canonical = base_url + clean_path
            
            if not canonical: continue
            
            # 1. Remove existing canonical and hreflang
            content = re.sub(r'<link rel="canonical" [^>]*>', "", content)
            content = re.sub(r'<link rel="alternate" hreflang=[^>]*>', "", content)
            
            # 2. Insert new tags after <head>
            new_tags = f'\n    <link rel="canonical" href="{canonical}" />'
            for h in hreflangs:
                new_tags += f'\n    <link rel="alternate" hreflang="{h["lang"]}" href="{h["href"]}" />'
            
            if "<head>" in content:
                content = content.replace("<head>", "<head>" + new_tags)
            elif "<HEAD>" in content:
                content = content.replace("<HEAD>", "<HEAD>" + new_tags)
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    print("SEO tags fixed across all HTML files.")

if __name__ == "__main__":
    fix_html_seo()
