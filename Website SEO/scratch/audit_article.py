import os
import re
import sys

def audit_file(filepath):
    print(f"Auditing file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 1. HTML lang/dir
    is_ar = "/ar/" in filepath.replace("\\", "/")
    if is_ar:
        if 'lang="ar"' not in content or 'dir="rtl"' not in content:
            issues.append("Arabic file missing correct lang/dir in html tag")
    else:
        if 'lang="en"' not in content or 'dir="ltr"' not in content:
            issues.append("English file missing correct lang/dir in html tag")
            
    # 2. Title & H1 Match
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
    
    if not title_match:
        issues.append("Missing <title> tag")
    if not h1_match:
        issues.append("Missing <h1> tag")
        
    if title_match and h1_match:
        title_text = title_match.group(1).split('|')[0].strip()
        h1_text = h1_match.group(1).strip()
        if title_text != h1_text and not h1_text.startswith(title_text[:30]):
            issues.append(f"Title and H1 do not match. Title: '{title_text}', H1: '{h1_text}'")
            
    # 3. Meta Description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if not desc_match:
        issues.append("Missing meta description")
    else:
        desc_text = desc_match.group(1)
        length = len(desc_text)
        if length < 140 or length > 155:
            issues.append(f"Meta description length is {length} (needs 140-155 characters)")
        if "AI Profit Lab" in desc_text[:20] or desc_text.lower().startswith(("learn how", "discover", "supercharge")):
            issues.append("Meta description starts with forbidden phrases")
            
    # 4. Visible Word Count (inside <article>)
    article_match = re.search(r'<article>(.*?)</article>', content, re.DOTALL | re.IGNORECASE)
    if not article_match:
        issues.append("Missing <article> tag")
    else:
        article_text = article_match.group(1)
        # Strip script and style tags inside article
        article_text = re.sub(r'<script.*?>.*?</script>', '', article_text, flags=re.DOTALL | re.IGNORECASE)
        article_text = re.sub(r'<style.*?>.*?</style>', '', article_text, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        clean_text = re.sub(r'<[^>]+>', ' ', article_text)
        words = clean_text.split()
        word_count = len(words)
        if word_count < 900 or word_count > 1200:
            issues.append(f"Visible word count inside article is {word_count} (needs 900-1200 words)")
            
        # Hook check (first 100 words of body / article)
        hook_text = " ".join(words[:100]).lower()
        forbidden_hook = ["we are", "we provide", "our company", "ai profit lab is", "welcome to", "at ai profit lab"]
        for phrase in forbidden_hook:
            if phrase in hook_text:
                issues.append(f"Hook paragraph contains forbidden self-promotional phrase: '{phrase}'")
                
    # 5. GCC / Oman Local Relevance
    local_keywords = ["muscat", "oman", "gcc", "uae", "saudi", "vision 2040", "pdpl", "sohar", "salalah", "decree", "omantel", "otech", "ma'een", "مسقط", "عمان", "الخليج", "الإمارات", "السعودية", "رؤية 2040", "المرسوم", "عمانتل"]
    local_count = 0
    clean_all = re.sub(r'<[^>]+>', ' ', content).lower()
    for kw in local_keywords:
        local_count += clean_all.count(kw)
    if local_count < 3:
        issues.append(f"Local GCC/Oman references count is {local_count} (needs >= 3)")
        
    # 6. FAQ count
    faq_q_count = len(re.findall(r'<h3[^>]*>.*?</h3>', content, re.IGNORECASE))
    # Excluding navigation or sidebar h3s if any, but since it's just blog layout, it works.
    # Inside FAQ section specifically:
    faq_section = re.search(r'<section[^>]*id=["\']faq["\'].*?>(.*?)</section>', content, re.DOTALL | re.IGNORECASE)
    if not faq_section:
        issues.append("Missing FAQ section")
    else:
        faq_text = faq_section.group(1)
        faq_h3s = len(re.findall(r'<h3[^>]*>.*?</h3>', faq_text, re.IGNORECASE))
        if faq_h3s != 10:
            issues.append(f"FAQ count in HTML is {faq_h3s} (needs exactly 10)")
            
    # 7. Footer
    clean_footer = re.sub(r'<[^>]+>', '', content)
    # Collapse multiple spaces
    clean_footer = re.sub(r'\s+', ' ', clean_footer)
    if is_ar:
        if "© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة" not in clean_footer and "© ٢٠٢٥ AI Profit Lab" not in clean_footer:
            issues.append("Missing or incorrect Arabic footer copyright")
    else:
        if "© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved" not in clean_footer and "© 2025 AI Profit Lab" not in clean_footer:
            issues.append("Missing or incorrect English footer copyright")
            
    # 8. JSON-LD Schema
    schema_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
    if not schema_matches:
        issues.append("Missing JSON-LD schema")
    else:
        combined_schemas = " ".join(schema_matches)
        if "International Gulf Lotus SPC" not in combined_schemas:
            issues.append("JSON-LD schema missing legalName 'International Gulf Lotus SPC'")
        if "AI Profit Lab" not in combined_schemas:
            issues.append("JSON-LD schema missing brand name 'AI Profit Lab'")
            
    if not issues:
        print("✅ No issues found! Article is compliant.")
    else:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audit_article.py <path_to_html>")
    else:
        audit_file(sys.argv[1])
