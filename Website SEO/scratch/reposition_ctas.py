#!/usr/bin/env python3
import os
import re
from pathlib import Path

BLOG_DIR = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/en")

CTA_HTML = """
<!-- CTA Block -->
<div class="glass-card rounded-2xl p-8 mt-12 mb-8 text-center border-blue-500/30 border">
    <h3 class="text-2xl font-bold text-white mb-4">Ready to Automate Your Business Operations?</h3>
    <p class="text-gray-300 mb-6">AI Profit Lab helps non-technical managers in Oman and the GCC deploy custom AI solutions, automated customer service systems, and real-time dashboards to slash overhead costs and eliminate manual busywork.</p>
    <a class="inline-block bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-full transition shadow-[0_0_15px_rgba(37,99,235,0.5)]" href="/en/contact/">Book a Free 30-Minute AI Consultation</a>
</div>
"""

def main():
    files = sorted([f for f in BLOG_DIR.glob("*.html")])
    updated = 0
    
    for f in files:
        with open(f, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()
            
        original = content
        
        # Remove any existing CTA block
        content = re.sub(r'<!-- CTA Block -->\s*<div[^>]*>.*?</div>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Inject the new CTA block right before </article> if it exists, otherwise </main>
        article_end_match = re.search(r'(</article>)', content, re.IGNORECASE)
        if article_end_match:
            content = content.replace(article_end_match.group(1), CTA_HTML + "\n" + article_end_match.group(1))
        else:
            main_end_match = re.search(r'(</main>)', content, re.IGNORECASE)
            if main_end_match:
                content = content.replace(main_end_match.group(1), CTA_HTML + "\n" + main_end_match.group(1))
                
        if content != original:
            with open(f, "w", encoding="utf-8") as file:
                file.write(content)
            updated += 1
            
    print(f"Repositioned CTA block in {updated} files.")

if __name__ == "__main__":
    main()
