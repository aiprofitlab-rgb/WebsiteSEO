import os
import sys

# Add execution dir to path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "execution"))

import update_blog_hubs
import fix_canonicals_and_sitemap

print("--- Updating Blog Hubs ---")
update_blog_hubs.base_dir = base_dir
blog_en_html = os.path.join(base_dir, "public_html", "blog", "index.html")
blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")
update_blog_hubs.update_hub(blog_en_html, "en", blog_en_dir)

blog_ar_html = os.path.join(base_dir, "public_html", "blog-ar", "index.html")
blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")
update_blog_hubs.update_hub(blog_ar_html, "ar", blog_ar_dir)

print("\n--- Regenerating Sitemap ---")
fix_canonicals_and_sitemap.main()
