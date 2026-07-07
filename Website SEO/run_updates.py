import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Update blog hubs
print("Updating blog hubs...")
subprocess.run(["python3", "update_blog_hubs.py"], cwd=base_dir, check=True)

# 3. Generate sitemap
print("Generating sitemap...")
subprocess.run(["python3", "generate_sitemap.py"], cwd=os.path.join(base_dir, "public_html"), check=True)

print("All tasks completed.")
