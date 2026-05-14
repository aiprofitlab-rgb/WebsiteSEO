import os
import re

def fix_article(file_path, lang):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix "Back to Hub" link
    nav_pattern = re.compile(r'(<nav[^>]*>.*?)(</nav>)', re.DOTALL)
    
    back_link_en = '<a href="/blog/" class="text-gray-300 hover:text-white font-semibold transition">Back to Hub</a>'
    back_link_ar = '<a href="/blog-ar/" class="text-gray-300 hover:text-white font-semibold transition">العودة إلى المدونة</a>'
    
    def nav_replacement(match):
        nav_content = match.group(1)
        closing_tag = match.group(2)
        if 'Back to Hub' in nav_content or 'العودة' in nav_content:
            if lang == 'en':
                nav_content = re.sub(r'href="/blog/en/"', 'href="/blog/"', nav_content)
                nav_content = re.sub(r'href="/en/blog/"', 'href="/blog/"', nav_content)
            else:
                nav_content = re.sub(r'href="/blog/ar/"', 'href="/blog-ar/"', nav_content)
                nav_content = re.sub(r'href="/ar/blog-ar/"', 'href="/blog-ar/"', nav_content)
            return nav_content + closing_tag
        else:
            link = back_link_en if lang == 'en' else back_link_ar
            return nav_content + '\n        ' + link + '\n    ' + closing_tag

    content = nav_pattern.sub(nav_replacement, content)

    # 2. Cleanup Meta Tags inside Title (Fixing the previous error)
    content = re.sub(r'(<title.*?>)\s*(<meta.*?>)\s*(<meta.*?>)', r'\2\n    \3\n    \1', content, flags=re.DOTALL)

    # 3. SEO & GEO Friendly Check
    title_match = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    
    if '<meta name="description"' not in content:
        desc = f"Learn more about {title}. Expert insights on AI, automation, and business efficiency in Oman and the GCC."
        if lang == 'ar':
            desc = f"تعرف على المزيد حول {title}. رؤى الخبراء حول الذكاء الاصطناعي والأتمتة وكفاءة الأعمال في عمان والخليج."
        meta_desc = f'\n    <meta name="description" content="{desc}">'
        # Insert BEFORE title
        content = re.sub(r'(<title.*?>)', meta_desc + r'\n    \1', content)

    if '<meta name="keywords"' not in content:
        keywords = "AI, Automation, Oman, GCC, Muscat, Business Efficiency, AI Profit Lab"
        if lang == 'ar':
            keywords = "الذكاء الاصطناعي, الأتمتة, عمان, الخليج, مسقط, كفاءة الأعمال, مختبر الربح"
        meta_keywords = f'\n    <meta name="keywords" content="{keywords}">'
        # Insert AFTER description
        content = re.sub(r'(<meta name="description".*?>)', r'\1' + meta_keywords, content)

    # 4. GEO keywords in content
    geo_keywords = ["Oman", "GCC", "Muscat", "Omani"]
    if lang == 'ar':
        geo_keywords = ["عمان", "الخليج", "مسقط", "العماني"]
    
    if not any(kw in content for kw in geo_keywords):
        geo_mention = "\n<p class='mt-8 text-gray-500 text-sm'>Expertly crafted for business leaders in Oman and the GCC by AI Profit Lab.</p>"
        if lang == 'ar':
            geo_mention = "\n<p class='mt-8 text-gray-500 text-sm'>تم إعداده بخبرة لقادة الأعمال في عمان والخليج بواسطة مختبر الربح (AI Profit Lab).</p>"
        if '<div class="prose' in content:
             content = content.replace('</div>', geo_mention + '</div>', 1)

    # 5. JSON-LD Article Schema
    if '"@type": "Article"' not in content:
        schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "author": {{
        "@type": "Organization",
        "name": "AI Profit Lab"
      }},
      "publisher": {{
        "@type": "Organization",
        "name": "AI Profit Lab",
        "logo": {{
          "@type": "ImageObject",
          "url": "https://aiprofitlab.io/favicon.svg"
        }}
      }}
    }}
    </script>"""
        content = content.replace('</head>', schema + '\n</head>')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Process all files
en_dir = 'public_html/blog/en/'
ar_dir = 'public_html/blog/ar/'

for filename in os.listdir(en_dir):
    if filename.endswith('.html'):
        fix_article(os.path.join(en_dir, filename), 'en')

for filename in os.listdir(ar_dir):
    if filename.endswith('.html'):
        fix_article(os.path.join(ar_dir, filename), 'ar')

print("All articles updated successfully.")
