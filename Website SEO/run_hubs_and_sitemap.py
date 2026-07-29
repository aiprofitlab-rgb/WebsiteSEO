import os
import re
from datetime import datetime

# 1. UPDATE BLOG HUBS
CATEGORY_MAP = {
    "AI Business Strategy": "cat_0",
    "استراتيجية الذكاء الاصطناعي للأعمال": "cat_0",
    "AI Security & Governance": "cat_1",
    "أمن وحوكمة الذكاء الاصطناعي": "cat_1",
    "Implementation & Automation": "cat_2",
    "التنفيذ والأتمتة": "cat_2",
    "Middle East AI": "cat_3",
    "الذكاء الاصطناعي في الشرق الأوسط": "cat_3",
    "Business Efficiency": "cat_2",
    "كفاءة الأعمال": "cat_2",
    "AI Governance & Compliance": "cat_1",
    "حوكمة الذكاء الاصطناعي والامتثال": "cat_1"
}

def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    date_str = date_match.group(1) if date_match else "1970-01-01"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else filename
    title = title.split(' | ')[0]

    meta_cat_match = re.search(r'<meta\s+name=["\']category["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    category = meta_cat_match.group(1).strip() if meta_cat_match else "Implementation & Automation"
    cat_id = CATEGORY_MAP.get(category, "cat_2")

    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if meta_desc_match:
        desc = meta_desc_match.group(1).strip()
    else:
        hook_match = re.search(r'<p class="[^"]*text-xl[^"]*text-gray-400[^"]*">(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        desc = hook_match.group(1).strip() if hook_match else "Read our latest updates and news."

    hero_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*rounded-3xl[^"\']*["\']', content, re.IGNORECASE)
    img_src = hero_match.group(1) if hero_match else "/blog/images/default.png"

    return {
        "filename": filename,
        "date": date_str,
        "title": title,
        "category": category,
        "cat_id": cat_id,
        "desc": desc,
        "img_src": img_src,
        "filepath": filepath
    }

def generate_card_html(article, lang="en"):
    if lang == "en":
        link = f"/blog/en/{article['filename']}"
    else:
        link = f"/blog/ar/{article['filename']}"
    
    read_more = "Read More →" if lang == "en" else "اقرأ المزيد ←"
    
    return f"""
            <a href="{link}" class="article-card glass-card rounded-2xl overflow-hidden block relative group" data-category="{article['cat_id']}">
                <img src="{article['img_src']}" alt="{article['title']}" class="w-full h-48 object-cover">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-3">
                        <span class="bg-blue-500/10 text-blue-400 text-xs px-3 py-1 rounded-full border border-blue-500/20">{article['category']}</span>
                        <p class="text-sm text-gray-500 font-semibold">{article['date']}</p>
                    </div>
                    <h2 class="text-xl font-bold mb-3 text-white group-hover:text-blue-400 transition">{article['title']}</h2>
                    <p class="text-gray-400 line-clamp-3 mb-4">{article['desc']}</p>
                    <span class="text-blue-500 font-bold text-sm inline-block">{read_more}</span>
                </div>
            </a>"""

def update_hub(hub_file, lang, article_dir):
    if not os.path.exists(hub_file):
        print(f"File not found: {hub_file}")
        return

    articles = []
    if os.path.exists(article_dir):
        for f in os.listdir(article_dir):
            if f.endswith('.html'):
                filepath = os.path.join(article_dir, f)
                articles.append(extract_metadata(filepath))
    
    articles.sort(key=lambda x: x['date'], reverse=True)
    cards_html = "\n".join([generate_card_html(a, lang) for a in articles])

    with open(hub_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">).*?(</div>\s*</main>)'
    replacement = f"\\1\n{cards_html}\n        </div>\n    "
    
    if not re.search(pattern, content, flags=re.DOTALL):
        print(f"Could not find article grid in {hub_file}")
        return

    new_content = re.sub(pattern, replacement + "</main>", content, flags=re.DOTALL)
    with open(hub_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {hub_file} with {len(articles)} articles.")

base_dir = os.path.abspath('.')
blog_en_html = os.path.join(base_dir, "public_html", "blog", "index.html")
blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")
update_hub(blog_en_html, "en", blog_en_dir)

blog_ar_html = os.path.join(base_dir, "public_html", "blog-ar", "index.html")
blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")
update_hub(blog_ar_html, "ar", blog_ar_dir)

# 2. REGENERATE SITEMAP
public_html = "public_html"
base_url = "https://aiprofitlab.io"

urls = [
    ("/", 1.0),
    ("/about/", 0.8),
    ("/contact/", 0.8),
    ("/process/", 0.8),
    ("/services/", 0.8),
    ("/blog-ar/", 0.8),
    ("/academy-ar/", 0.8),
    ("/campaign-roi-simulator-ar/", 0.7),
    ("/customized-ceo-dashboard-demo-ar/", 0.7),
    ("/missed-call-simulator-ar/", 0.7),
    ("/whatsapp-receptionist-demo-ar/", 0.7),

    ("/en/", 0.9),
    ("/en/about-en/", 0.8),
    ("/en/contact-en/", 0.8),
    ("/en/process-en/", 0.8),
    ("/en/services-en/", 0.8),
    ("/en/blog/", 0.8),
    ("/en/academy/", 0.8),
    ("/campaign-roi-simulator/", 0.7),
    ("/customized-ceo-dashboard-demo/", 0.7),
    ("/en/missed-call-simulator-en/", 0.7),
    ("/en/whatsapp-receptionist-demo/", 0.7),
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

sitemap_path = os.path.join(public_html, "sitemap.xml")
with open(sitemap_path, "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"Generated sitemap.xml with {len(urls)} URLs.")
