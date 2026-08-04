import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

import update_blog_hubs

print("Updating blog hubs...")
update_blog_hubs.update_hub(
    os.path.join(base_dir, "public_html", "blog", "index.html"),
    "en",
    os.path.join(base_dir, "public_html", "blog", "en")
)
update_blog_hubs.update_hub(
    os.path.join(base_dir, "public_html", "blog-ar", "index.html"),
    "ar",
    os.path.join(base_dir, "public_html", "blog", "ar")
)

print("\nGenerating sitemap...")
import generate_final_sitemap
# generate_final_sitemap runs at import time or we can re-exec file
with open(os.path.join(base_dir, "generate_final_sitemap.py"), "r") as f:
    code = f.read()
    exec(code)

print("\nHubs and Sitemap script completed!")
