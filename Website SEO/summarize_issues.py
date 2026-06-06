import os
import json
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from collections import defaultdict

base_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog"
en_dir = os.path.join(base_dir, "en")
ar_dir = os.path.join(base_dir, "ar")

files_to_check = []
for d in [en_dir, ar_dir]:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".html") and f != "index.html":
                files_to_check.append(os.path.join(d, f))

issue_counts = defaultdict(int)
all_ext_links = set()

for path in files_to_check:
    is_ar = "ar" in path
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    soup = BeautifulSoup(content, "html.parser")
    
    # 1. Check HTML lang/dir
    html_tag = soup.find("html")
    if is_ar:
        if html_tag.get("lang") != "ar" or html_tag.get("dir") != "rtl":
            issue_counts["AR HTML lang/dir incorrect"] += 1
    else:
        if html_tag.get("lang") != "en" or html_tag.get("dir") != "ltr":
            issue_counts["EN HTML lang/dir incorrect"] += 1

    # 2. Schema
    scripts = soup.find_all("script", type="application/ld+json")
    has_org = False; has_article = False; has_faq = False; has_lb = False
    faq_c = 0
    for s in scripts:
        try:
            data = json.loads(s.string)
            if isinstance(data, dict):
                if "@graph" in data:
                    for item in data["@graph"]:
                        if item.get("@type") == "Organization": has_org = True
                        if item.get("@type") == "Article": has_article = True
                        if item.get("@type") == "FAQPage": 
                            has_faq = True
                            faq_c = len(item.get("mainEntity", []))
                elif data.get("@type") in ["ProfessionalService", "LocalBusiness"]:
                    has_lb = True
                    if data.get("legalName") != "International Gulf Lotus SPC":
                        issue_counts["LocalBusiness missing legalName"] += 1
        except: pass
    if not has_org: issue_counts["Missing Organization schema"] += 1
    if not has_article: issue_counts["Missing Article schema"] += 1
    if not has_faq: issue_counts["Missing FAQPage schema"] += 1
    if faq_c < 10: issue_counts["FAQ count in JSON < 10"] += 1
    if not has_lb: issue_counts["Missing LocalBusiness schema"] += 1

    # 3. FAQ HTML
    faq_section = soup.find("section", id="faq")
    if faq_section:
        if len(faq_section.find_all("h3")) < 10:
            issue_counts["FAQ count in HTML < 10"] += 1
    else:
        issue_counts["Missing FAQ section in HTML"] += 1

    # 4. Footer
    footer = soup.find("footer")
    if footer:
        if is_ar:
            if "© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة" not in content and "© ٢٠٢٥ AI Profit Lab" not in content:
                issue_counts["Arabic footer text incorrect"] += 1
        else:
            if "© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved" not in content and "© 2025 AI Profit Lab" not in content:
                issue_counts["English footer text incorrect"] += 1
    else:
        issue_counts["Missing footer"] += 1

    # 5. Extract links
    links = soup.find_all("a", href=True)
    for a in links:
        href = a["href"]
        if href.startswith("http"):
            all_ext_links.add(href)

def check_link(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except:
        return 0

print("=== Issue Summary ===")
for k,v in issue_counts.items():
    print(f"{k}: {v} files")

print(f"\nChecking {len(all_ext_links)} unique external links...")
broken = []
vertex_links = []
for l in list(all_ext_links):
    if "vertexaisearch" in l:
        vertex_links.append(l)
    else:
        status = check_link(l)
        if status not in [200, 301, 302, 303, 307, 308, 403, 401]:
            broken.append((l, status))

print("\n=== Vertex AI Redirect Links (Broken/Temporary) ===")
print(f"Found {len(vertex_links)} Vertex links.")

print("\n=== Broken External Links ===")
for l, s in broken:
    print(f"Status {s}: {l}")

