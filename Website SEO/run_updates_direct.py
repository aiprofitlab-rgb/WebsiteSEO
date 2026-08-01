import os
import re

base_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Update EN Hub
blog_en_html_path = os.path.join(base_dir, "public_html", "blog", "index.html")
blog_en_dir = os.path.join(base_dir, "public_html", "blog", "en")

# 2. Update AR Hub
blog_ar_html_path = os.path.join(base_dir, "public_html", "blog-ar", "index.html")
blog_ar_dir = os.path.join(base_dir, "public_html", "blog", "ar")

# Import functions from update_blog_hubs
from update_blog_hubs import update_hub
update_hub(blog_en_html_path, "en", blog_en_dir)
update_hub(blog_ar_html_path, "ar", blog_ar_dir)

# 3. Generate sitemap
from process_new_article import *
print("Hubs updated and sitemap generated successfully.")
