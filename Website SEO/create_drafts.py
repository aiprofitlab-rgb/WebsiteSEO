import re, os

# Verification helper
def verify_article(path, is_arabic=False):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Check title
    title = re.search(r'<title>(.*?)</title>', html).group(1)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html).group(1)
    assert title.startswith(h1[:30]), f"Title/H1 mismatch: {title} vs {h1}"
    
    # Check meta desc
    m = re.search(r'<meta name="description" content="(.*?)">', html)
    desc = m.group(1)
    print(f"[{'AR' if is_arabic else 'EN'}] Meta desc ({len(desc)} chars): {desc}")
    assert 140 <= len(desc) <= 155, f"Meta description length {len(desc)} not in 140-155"
    
    # Check FAQs
    faqs = re.findall(r'<h3 class="text-lg font-bold text-white mb-2">(.*?)</h3>', html)
    print(f"[{'AR' if is_arabic else 'EN'}] Found {len(faqs)} FAQs")
    assert len(faqs) == 10, f"Expected 10 FAQs, got {len(faqs)}"
    
    # Check References
    ref_match = re.search(r'<h3 class="text-xl font-bold mb-4 text-white">(?:References|المراجع)</h3>\s*<ul[^>]*>(.*?)</ul>', html, re.DOTALL)
    assert ref_match, "References block missing or misformatted"
    refs = re.findall(r'<a href="(.*?)"', ref_match.group(1))
    print(f"[{'AR' if is_arabic else 'EN'}] Found {len(refs)} references")
    assert len(refs) >= 3, f"Expected >=3 references, got {len(refs)}"

    # Body word count (prose text)
    prose = re.search(r'<div class="prose max-w-none[^"]*">(.*?)</div>\s*<!-- CTA Block', html, re.DOTALL)
    assert prose, "Prose block missing"
    text = re.sub(r'<[^>]+>', ' ', prose.group(1))
    words = len(text.split())
    print(f"[{'AR' if is_arabic else 'EN'}] Body prose word count: {words} words")
    assert 750 <= words <= 1300, f"Body word count {words} outside target range"

print("Helper ready")
