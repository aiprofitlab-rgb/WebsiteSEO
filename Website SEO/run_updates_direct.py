import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import update_blog_hubs
import generate_final_sitemap

print("Running update_blog_hubs...")
update_blog_hubs.main() if hasattr(update_blog_hubs, 'main') else None

print("Running sitemap generation...")
if hasattr(generate_final_sitemap, 'main'):
    generate_final_sitemap.main()
elif hasattr(generate_final_sitemap, 'generate_sitemap'):
    generate_final_sitemap.generate_sitemap()
