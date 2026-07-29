import os
import update_blog_hubs

base_dir = os.path.abspath('.')
blog_en_html = os.path.join(base_dir, "public_html", "blog", "index.html")
blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")
update_blog_hubs.update_hub(blog_en_html, "en", blog_en_dir)

blog_ar_html = os.path.join(base_dir, "public_html", "blog-ar", "index.html")
blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")
update_blog_hubs.update_hub(blog_ar_html, "ar", blog_ar_dir)
print("Hub update complete!")
