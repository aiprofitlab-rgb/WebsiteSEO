import os
import json
import re

paths = [
    "public_html/blog/en/2026-07-31-whatsapp-business-api-vs-app-oman.html",
    "public_html/blog/ar/2026-07-31-whatsapp-business-api-vs-app-oman.html"
]

results = []

for path in paths:
    issues = []
    if not os.path.exists(path):
        issues.append("File does not exist!")
        results.append({"file": path, "issues": issues})
        continue

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    is_ar = "/ar/" in path
    
    # 1. HTML lang & dir
    if is_ar:
        if 'lang="ar"' not in content or 'dir="rtl"' not in content:
            issues.append("HTML lang/dir incorrect for Arabic")
    else:
        if 'lang="en"' not in content or 'dir="ltr"' not in content:
            issues.append("HTML lang/dir incorrect for English")
            
    # 2. Check Title & H1 match
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
    
    if not title_match or not h1_match:
        issues.append("Missing title or h1 tag")
    else:
        clean_title = title_match.group(1).split(" | ")[0].strip()
        clean_h1 = h1_match.group(1).strip()
        if clean_title != clean_h1:
            issues.append(f"Title ({clean_title}) does not match H1 ({clean_h1})")
            
    # 3. Check Meta Description length
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    desc_len = 0
    if desc_match:
        desc_text = desc_match.group(1).strip()
        desc_len = len(desc_text)
        if desc_len < 140 or desc_len > 155:
            issues.append(f"Meta description length is {desc_len} (must be 140-155 chars)")
    else:
        issues.append("Missing meta description")

    # 4. Check JSON-LD
    json_scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    has_org = False
    has_article = False
    has_faq = False
    faq_count_json = 0
    
    for s in json_scripts:
        try:
            data = json.loads(s.strip())
            if isinstance(data, dict) and "@graph" in data:
                for item in data["@graph"]:
                    if item.get("@type") == "Organization":
                        has_org = True
                        if item.get("legalName") != "International Gulf Lotus SPC":
                            issues.append("Organization missing legalName: International Gulf Lotus SPC")
                    if item.get("@type") == "Article":
                        has_article = True
                    if item.get("@type") == "FAQPage":
                        has_faq = True
                        faq_count_json = len(item.get("mainEntity", []))
        except Exception as e:
            issues.append(f"JSON-LD parse error: {e}")
            
    if not has_org: issues.append("Missing Organization schema")
    if not has_article: issues.append("Missing Article schema")
    if not has_faq: issues.append("Missing FAQPage schema")
    if faq_count_json < 10: issues.append(f"FAQ count in JSON is {faq_count_json} (needs >= 10)")
    
    # 5. Check Footer Legal Entity
    if "International Gulf Lotus SPC" not in content:
        issues.append("Footer missing legal entity International Gulf Lotus SPC")

    results.append({
        "file": os.path.basename(path),
        "lang": "AR" if is_ar else "EN",
        "issues": issues,
        "desc_length": desc_len
    })

print(json.dumps(results, indent=2, ensure_ascii=False))
