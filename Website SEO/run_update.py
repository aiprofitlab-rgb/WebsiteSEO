import os
import re

base_dir = os.path.dirname(os.path.abspath(__file__))

def insert_article_to_hub(hub_path, card_html):
    with open(hub_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    target = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">'
    if target in content and card_html not in content:
        content = content.replace(target, target + "\n" + card_html)
        with open(hub_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully inserted card into {hub_path}")
    else:
        print(f"Skipped or card already present in {hub_path}")

# English card
en_card = """
            <a href="/blog/en/2026-08-04-connect-webhooks-make-n8n-enterprise-erp-oman.html" class="article-card glass-card rounded-2xl overflow-hidden block relative group" data-category="cat_2">
                <img src="/blog/images/connect-webhooks-make-n8n-enterprise-erp-oman.png" alt="How to Connect Webhooks, Make.com, and n8n with Enterprise ERPs in Oman" class="w-full h-48 object-cover">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-3">
                        <span class="bg-blue-500/10 text-blue-400 text-xs px-3 py-1 rounded-full border border-blue-500/20">Enterprise Automation</span>
                        <p class="text-sm text-gray-500 font-semibold">2026-08-04</p>
                    </div>
                    <h2 class="text-xl font-bold mb-3 text-white group-hover:text-blue-400 transition">How to Connect Webhooks, Make.com, and n8n with Enterprise ERPs in Oman</h2>
                    <p class="text-gray-400 line-clamp-3 mb-4">Struggling with SAP or Oracle integration in Muscat? Learn how to connect webhooks, Make.com, and n8n to enterprise ERPs securely under Oman PDPL rules.</p>
                    <span class="text-blue-500 font-bold text-sm inline-block">Read More →</span>
                </div>
            </a>"""

# Arabic card
ar_card = """
            <a href="/blog/ar/2026-08-04-connect-webhooks-make-n8n-enterprise-erp-oman.html" class="article-card glass-card rounded-2xl overflow-hidden block relative group" data-category="cat_2">
                <img src="/blog/images/connect-webhooks-make-n8n-enterprise-erp-oman.png" alt="كيفية ربط الويب هوك وأنظمة Make و n8n بأنظمة إدارة الموارد المؤسسية (ERP) في عُمان" class="w-full h-48 object-cover">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-3">
                        <span class="bg-blue-500/10 text-blue-400 text-xs px-3 py-1 rounded-full border border-blue-500/20">أتمتة المؤسسات</span>
                        <p class="text-sm text-gray-500 font-semibold">2026-08-04</p>
                    </div>
                    <h2 class="text-xl font-bold mb-3 text-white group-hover:text-blue-400 transition">كيفية ربط الويب هوك وأنظمة Make و n8n بأنظمة إدارة الموارد المؤسسية</h2>
                    <p class="text-gray-400 line-clamp-3 mb-4">هل تعاني من صعوبة ربط SAP أو Oracle في مسقط؟ تعرّف على كيفية ربط الويب هوك وMake وn8n بأنظمة ERP بأمان وفق قانون حماية البيانات العماني.</p>
                    <span class="text-blue-500 font-bold text-sm inline-block">اقرأ المزيد ←</span>
                </div>
            </a>"""

insert_article_to_hub(os.path.join(base_dir, "public_html", "blog", "index.html"), en_card)
insert_article_to_hub(os.path.join(base_dir, "public_html", "blog-ar", "index.html"), ar_card)

# Update sitemap
sitemap_path = os.path.join(base_dir, "public_html", "sitemap.xml")
with open(sitemap_path, 'r', encoding='utf-8') as f:
    sitemap = f.read()

new_urls = """  <url>
    <loc>https://aiprofitlab.io/blog/en/2026-08-04-connect-webhooks-make-n8n-enterprise-erp-oman/</loc>
    <lastmod>2026-08-04</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://aiprofitlab.io/blog/ar/2026-08-04-connect-webhooks-make-n8n-enterprise-erp-oman/</loc>
    <lastmod>2026-08-04</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
</urlset>"""

if "</urlset>" in sitemap and "2026-08-04-connect-webhooks-make-n8n-enterprise-erp-oman" not in sitemap:
    sitemap = sitemap.replace("</urlset>", new_urls)
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print("Added new article URLs to sitemap.xml")
