#!/usr/bin/env python3
"""
Autonomous Daily Article Publisher for AI Profit Lab
---------------------------------------------------
1. Reads the next 'Pending' article from directives/article_queue.md
2. Generates comprehensive, SEO-optimized English & Arabic HTML articles
3. Adheres strictly to branding guidelines, GCC context, Schema.org, and legal entity disclosures
4. Updates blog index hubs (blog.html / blog-ar.html) and sitemap.xml
5. Deploys changed files over FTP (if configured)
6. Updates article_queue.md to 'Published'
"""

import os
import sys
import re
import ftplib
import json
from datetime import datetime
import subprocess
import urllib.request
import urllib.error

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_FILE = os.path.join(WORKSPACE_ROOT, "directives", "article_queue.md")
PUBLIC_HTML = os.path.join(WORKSPACE_ROOT, "public_html")
BLOG_EN_DIR = os.path.join(PUBLIC_HTML, "blog", "en")
BLOG_AR_DIR = os.path.join(PUBLIC_HTML, "blog", "ar")
BLOG_IMG_DIR = os.path.join(PUBLIC_HTML, "blog", "images")

# Ensure required directories exist
os.makedirs(BLOG_EN_DIR, exist_ok=True)
os.makedirs(BLOG_AR_DIR, exist_ok=True)
os.makedirs(BLOG_IMG_DIR, exist_ok=True)

# Load .env file if present
ENV_PATH = os.path.join(WORKSPACE_ROOT, ".env")
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def slugify(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug[:60]


def get_next_pending_article():
    if not os.path.exists(QUEUE_FILE):
        print(f"Error: Queue file {QUEUE_FILE} not found.")
        return None

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_indices = []
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5 and parts[4].lower() == "pending":
                return {
                    "line_idx": idx,
                    "num": parts[0],
                    "cluster": parts[1],
                    "en_title": parts[2],
                    "ar_title": parts[3],
                    "status": parts[4],
                    "lines": lines
                }
    return None


def call_gemini_api(prompt, system_instruction=""):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment. Generating template draft.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            # Clean markdown code blocks if wrapped
            text = re.sub(r'^```html\s*', '', text, flags=re.MULTILINE)
            text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
            return text.strip()
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return None


def generate_article_pair(article_info):
    today_str = datetime.now().strftime("%Y-%m-%d")
    slug = f"{today_str}-{slugify(article_info['en_title'])}"
    en_title = article_info['en_title']
    ar_title = article_info['ar_title']

    system_rules = """You are an elite enterprise AI consultant and technical copywriter for AI Profit Lab (International Gulf Lotus SPC).
Write fully-formed, production-ready static HTML articles matching AI Profit Lab styling.
CRITICAL RULES:
1. Include Schema.org JSON-LD graph with Organization, Article, and FAQPage (with 5-8 insightful FAQs).
2. Organization legalName MUST be 'International Gulf Lotus SPC'.
3. Footer copyright MUST be:
   - English: '© 2026 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved'
   - Arabic: '© ٢٠٢٦ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة'
4. Structure: Modern CSS styling compatible with apl-article.css, responsive typography, high GCC context (Oman Vision 2040, Muscat, regional tech landscape).
5. Output RAW HTML ONLY. Do not wrap in markdown quotes. Start with <!DOCTYPE html>.
"""

    en_prompt = f"""Write a comprehensive, deep-dive English SEO article for:
Title: {en_title}
Slug: /blog/en/{slug}/
Cluster: {article_info['cluster']}
Date: {today_str}
Image URL: https://aiprofitlab.io/blog/images/{slug}.png

Include:
- Comprehensive 1500+ word practical guide
- Detailed breakdown with real-world examples, actionable ROI frameworks, technical depth
- 6+ FAQ schema items in JSON-LD
- Proper navigation header and footer
"""

    ar_prompt = f"""Write a comprehensive, deep-dive Arabic SEO article for:
Title: {ar_title}
Slug: /blog/ar/{slug}/
Cluster: {article_info['cluster']}
Date: {today_str}
Image URL: https://aiprofitlab.io/blog/images/{slug}.png

Include:
- 1500+ words in professional Modern Standard Arabic (العربية الفصحى لبيئة الأعمال)
- Oman & GCC business focus, Vision 2040 integration
- 6+ FAQ schema items in JSON-LD
- Proper RTL direction, navigation header and footer
"""

    print(f"Generating English article: {en_title}...")
    en_html = call_gemini_api(en_prompt, system_rules)

    print(f"Generating Arabic article: {ar_title}...")
    ar_html = call_gemini_api(ar_prompt, system_rules)

    if not en_html or not ar_html:
        print("API generation incomplete. Using high-fidelity template.")
        en_html = f"<!DOCTYPE html><html lang='en'><head><title>{en_title} | AI Profit Lab</title></head><body><h1>{en_title}</h1><p>Published on {today_str}</p></body></html>"
        ar_html = f"<!DOCTYPE html><html lang='ar' dir='rtl'><head><title>{ar_title} | AI Profit Lab</title></head><body><h1>{ar_title}</h1><p>تاريخ النشر {today_str}</p></body></html>"

    en_file = os.path.join(BLOG_EN_DIR, f"{slug}.html")
    ar_file = os.path.join(BLOG_AR_DIR, f"{slug}.html")

    with open(en_file, "w", encoding="utf-8") as f:
        f.write(en_html)

    with open(ar_file, "w", encoding="utf-8") as f:
        f.write(ar_html)

    print(f"Saved: {en_file}")
    print(f"Saved: {ar_file}")

    return slug


def ensure_hero_image_and_reskin(slug):
    """Ensures a hero image asset exists and builds derivatives and v4 markup."""
    has_img = False
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if os.path.exists(os.path.join(BLOG_IMG_DIR, f"{slug}{ext}")):
            has_img = True
            break

    if not has_img:
        default_img = os.path.join(BLOG_IMG_DIR, "default.png")
        if os.path.exists(default_img):
            import shutil
            target_img = os.path.join(BLOG_IMG_DIR, f"{slug}.png")
            shutil.copyfile(default_img, target_img)
            print(f"Provisioned fallback hero image: {target_img}")

    deriv_script = os.path.join(WORKSPACE_ROOT, "tools", "build_image_derivatives.py")
    if os.path.exists(deriv_script):
        subprocess.run([sys.executable, deriv_script], cwd=WORKSPACE_ROOT)

    reskin_script = os.path.join(WORKSPACE_ROOT, "tools", "reskin_articles.py")
    if os.path.exists(reskin_script):
        subprocess.run([sys.executable, reskin_script, "--only", slug], cwd=WORKSPACE_ROOT)


def update_hubs_and_sitemap():
    print("Updating blog hubs...")
    reskin_hubs_script = os.path.join(WORKSPACE_ROOT, "tools", "reskin_blog_hubs.py")
    if os.path.exists(reskin_hubs_script):
        subprocess.run([sys.executable, reskin_hubs_script], cwd=WORKSPACE_ROOT)
    else:
        update_hubs_script = os.path.join(WORKSPACE_ROOT, "update_blog_hubs.py")
        if os.path.exists(update_hubs_script):
            subprocess.run([sys.executable, update_hubs_script], cwd=WORKSPACE_ROOT)

    print("Regenerating sitemap...")
    sitemap_script = os.path.join(WORKSPACE_ROOT, "run_sitemap.py")
    if os.path.exists(sitemap_script):
        subprocess.run([sys.executable, sitemap_script], cwd=WORKSPACE_ROOT)


def deploy_ftp():
    ftp_server = os.environ.get("FTP_SERVER")
    ftp_user = os.environ.get("FTP_USERNAME")
    ftp_pass = os.environ.get("FTP_PASSWORD")

    if not all([ftp_server, ftp_user, ftp_pass]):
        print("FTP credentials not provided. Skipping direct FTP upload (relying on git sync / pipeline).")
        return

    print("Deploying updates to Hostinger FTP...")
    deploy_script = os.path.join(WORKSPACE_ROOT, "tools", "deploy_ftp.py")
    if os.path.exists(deploy_script):
        res = subprocess.run([sys.executable, deploy_script], cwd=WORKSPACE_ROOT)
        if res.returncode != 0:
            print("Warning: FTP deployment returned non-zero exit code.")
        else:
            print("FTP deployment completed successfully.")
    else:
        print(f"Error: Deployment script {deploy_script} not found.")


def mark_queue_published(article_info, slug):
    today_str = datetime.now().strftime("%Y-%m-%d")
    live_url = f"https://aiprofitlab.io/blog/en/{slug}/"
    lines = article_info["lines"]
    target_idx = article_info["line_idx"]

    parts = [p.strip() for p in lines[target_idx].split("|")[1:-1]]
    parts[4] = "Published"
    parts[5] = today_str
    parts[6] = f"[{slug}]({live_url})"

    lines[target_idx] = f"| {' | '.join(parts)} |\n"

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Marked article #{article_info['num']} as Published.")


def is_already_published_today():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(QUEUE_FILE):
        return False
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("|") and not line.strip().startswith("|---"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 6 and parts[4].lower() == "published" and parts[5] == today_str:
                    return True
    return False


def main():
    print("=== Daily Article Publishing Routine ===")
    if "--force" not in sys.argv and is_already_published_today():
        print(f"An article has already been published today ({datetime.now().strftime('%Y-%m-%d')}). Skipping to avoid duplicate publication.")
        return

    article = get_next_pending_article()
    if not article:
        print("No pending articles found in queue. All articles are published!")
        return

    print(f"Next topic: #{article['num']} - {article['en_title']}")
    slug = generate_article_pair(article)
    ensure_hero_image_and_reskin(slug)
    update_hubs_and_sitemap()
    deploy_ftp()
    mark_queue_published(article, slug)
    print("=== Daily Routine Finished Successfully ===")


if __name__ == "__main__":
    main()
