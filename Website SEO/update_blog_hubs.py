import os
import re
from datetime import datetime

# Category mappings for the data-category attribute
CATEGORY_MAP = {
    "AI Business Strategy": "cat_0",
    "استراتيجية الذكاء الاصطناعي للأعمال": "cat_0",
    "AI Security & Governance": "cat_1",
    "أمن وحوكمة الذكاء الاصطناعي": "cat_1",
    "Implementation & Automation": "cat_2",
    "التنفيذ والأتمتة": "cat_2",
    "Middle East AI": "cat_3",
    "الذكاء الاصطناعي في الشرق الأوسط": "cat_3"
}

def extract_metadata(filepath):
    filename = os.path.basename(filepath)
    # Match YYYY-MM-DD
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    date_str = date_match.group(1) if date_match else "1970-01-01"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Title
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else filename
    title = title.split(' | ')[0]  # Remove brand suffix if present

    # Category
    meta_cat_match = re.search(r'<meta\s+name=["\']category["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    category = meta_cat_match.group(1).strip() if meta_cat_match else "Implementation & Automation"
    
    if category not in CATEGORY_MAP:
        # Default to cat_2 if unknown
        cat_id = "cat_2"
    else:
        cat_id = CATEGORY_MAP[category]

    # Description
    meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
    if meta_desc_match:
        desc = meta_desc_match.group(1).strip()
    else:
        # Fallback to finding the first paragraph that looks like a subtitle hook
        hook_match = re.search(r'<p class="[^"]*text-xl[^"]*text-gray-400[^"]*">(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        desc = hook_match.group(1).strip() if hook_match else "Read our latest updates and news."

    # Image
    img_match = re.search(r'<img[^>]+src=["\'](.*?)["\']', content, re.IGNORECASE)
    img_src = img_match.group(1) if img_match else "../../blog/images/default.png"
    # Convert src to match blog hub relative path
    img_src = img_src.replace("../../", "") 

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
    # Determine the link path
    link = f"blog/{lang}/{article['filename']}"
    read_more = "Read More →" if lang == "en" else "اقرأ المزيد ←"
    
    html = f"""
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
    return html

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
    
    # Sort articles by date descending
    articles.sort(key=lambda x: x['date'], reverse=True)

    cards_html = "\n".join([generate_card_html(a, lang) for a in articles])

    with open(hub_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find the grid container and replace its contents
    pattern = r'(<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">).*?(</main>)'
    
    # Ensure replacement has the newline for formatting
    replacement = f"\\1\n{cards_html}\n        </div>\n    \\2"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(hub_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Successfully updated {hub_file} with {len(articles)} articles.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # English
    blog_en_html = os.path.join(base_dir, "public_html", "blog.html")
    blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")
    update_hub(blog_en_html, "en", blog_en_dir)
    
    # Arabic
    blog_ar_html = os.path.join(base_dir, "public_html", "blog_ar.html")
    blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")
    update_hub(blog_ar_html, "ar", blog_ar_dir)
