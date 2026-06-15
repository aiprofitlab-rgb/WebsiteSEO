import os
import json
import re
from bs4 import BeautifulSoup
import sys

base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog"
en_dir = os.path.join(base_dir, "en")
ar_dir = os.path.join(base_dir, "ar")

files_to_check = []
for d in [en_dir, ar_dir]:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".html") and f != "index.html":
                files_to_check.append(os.path.join(d, f))

results = []

for path in files_to_check:
    issues = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    soup = BeautifulSoup(content, "html.parser")
    
    # 1. Check HTML lang and dir
    html_tag = soup.find("html")
    is_ar = "/ar/" in path.replace("\\", "/")
    if is_ar:
        if html_tag.get("lang") != "ar" or html_tag.get("dir") != "rtl":
            issues.append("HTML lang/dir incorrect for Arabic")
    else:
        if html_tag.get("lang") != "en" or html_tag.get("dir") != "ltr":
            issues.append("HTML lang/dir incorrect for English")
            
    # 2. Check JSON-LD
    scripts = soup.find_all("script", type="application/ld+json")
    has_org = False
    has_article = False
    has_faq = False
    has_localbusiness = False
    faq_count_json = 0
    
    for s in scripts:
        try:
            data = json.loads(s.string)
            if isinstance(data, dict):
                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Organization":
                            has_org = True
                        if item.get("@type") == "Article":
                            has_article = True
                        if item.get("@type") == "FAQPage":
                            has_faq = True
                            faq_count_json = len(item.get("mainEntity", []))
                elif data.get("@type") == "ProfessionalService" or data.get("@type") == "LocalBusiness":
                    has_localbusiness = True
                    if data.get("legalName") != "International Gulf Lotus SPC":
                        issues.append("LocalBusiness missing correct legalName")
        except:
            pass
            
    if not has_org: issues.append("Missing Organization schema")
    if not has_article: issues.append("Missing Article schema")
    if not has_faq: issues.append("Missing FAQPage schema")
    if faq_count_json < 10: issues.append(f"FAQ count in JSON is {faq_count_json} (needs >= 10)")
    
    # 3. Check FAQ section in HTML
    faq_section = soup.find("section", id="faq")
    if faq_section:
        faq_count_html = len(faq_section.find_all("h3"))
        if faq_count_html < 10:
            issues.append(f"FAQ count in HTML is {faq_count_html} (needs >= 10)")
    else:
        issues.append("Missing FAQ section in HTML")
        
    # 4. Check Footer
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text().strip()
        if is_ar:
            if "© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة" not in content and "© ٢٠٢٥ AI Profit Lab" not in content:
                issues.append("Arabic footer incorrect")
        else:
            if "© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved" not in content and "© 2025 AI Profit Lab" not in content:
                issues.append("English footer incorrect")
    else:
        issues.append("Missing footer")
        
    # 5. Check Links
    links = soup.find_all("a", href=True)
    ext_links = []
    for a in links:
        href = a["href"]
        if href.startswith("http"):
            ext_links.append(href)
    
    results.append({
        "file": os.path.basename(path),
        "lang": "AR" if is_ar else "EN",
        "issues": issues,
        "external_links": ext_links
    })

print(json.dumps(results, indent=2, ensure_ascii=False))
