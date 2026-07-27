#!/usr/bin/env python3
"""
fix_canonicals_and_sitemap.py
=================================
DevOps/SEO fix script for aiprofitlab.io
-------------------------------------------
Tasks:
  1. Fix missing trailing slashes on canonical tags for all root-level .html pages.
  2. Fix wrong/non-canonical slugs on stale pages (Customized_CEO_Dashboard.html,
     whatsapp_receptionist_demo.html, missed-call-simulator-en.html).
  3. Regenerate a clean sitemap.xml that:
     - Covers ALL blog/ar, blog/en, academy/ar, academy/en posts from disk.
     - Uses correct trailing-slash clean URLs (no .html).
     - Excludes draft/junk pages (test.html, onboarding.html, *-new.html,
       preview-templates.html, medflow-*.html, whatsapp_receptionist_demo.html,
       Customized_CEO_Dashboard.html).
  4. Verify robots.txt Sitemap directive is correct.

Run from repo root:
    python3 execution/fix_canonicals_and_sitemap.py
"""

import os
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://aiprofitlab.io"
PUBLIC_HTML = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public_html")
SITEMAP_OUT = os.path.join(PUBLIC_HTML, "sitemap.xml")
ROBOTS_PATH = os.path.join(PUBLIC_HTML, "robots.txt")

# ---------------------------------------------------------------------------
# 1. CANONICAL FIX MAP
# Each tuple: (html_file_rel_to_public_html, wrong_canonical, correct_canonical)
# ---------------------------------------------------------------------------
CANONICAL_FIXES = [
    # Root-level Arabic pages (missing trailing slash)
    ("about.html",                         "/about",                      "/about/"),
    ("contact.html",                       "/contact",                    "/contact/"),
    ("services.html",                      "/services",                   "/services/"),
    ("process.html",                       "/process",                    "/process/"),
    ("campaign-roi-simulator-ar.html",     "/campaign-roi-simulator-ar",  "/campaign-roi-simulator-ar/"),
    ("campaign-roi-simulator.html",        "/campaign-roi-simulator",     "/campaign-roi-simulator/"),
    ("customized-ceo-dashboard-demo-ar.html", "/customized-ceo-dashboard-demo-ar", "/customized-ceo-dashboard-demo-ar/"),
    ("customized-ceo-dashboard-demo.html", "/customized-ceo-dashboard-demo",    "/customized-ceo-dashboard-demo/"),
    ("missed-call-simulator-ar.html",      "/missed-call-simulator-ar",   "/missed-call-simulator-ar/"),
    ("whatsapp-receptionist-demo-ar.html", "/whatsapp-receptionist-demo-ar", "/whatsapp-receptionist-demo-ar/"),
    # Root-level English pages (missing trailing slash + wrong base path)
    ("about-en.html",                      "/about-en",                   "/en/about-en/"),
    ("contact-en.html",                    "/contact-en",                 "/en/contact-en/"),
    ("services-en.html",                   "/services-en",                "/en/services-en/"),
    ("process-en.html",                    "/process-en",                 "/en/process-en/"),
    # Missed-call simulator EN lives under /en/
    ("missed-call-simulator-en.html",      "/missed-call-simulator-en",   "/en/missed-call-simulator-en/"),
    # WhatsApp demo EN lives under /en/
    ("whatsapp-receptionist-demo.html",    "/whatsapp-receptionist-demo", "/en/whatsapp-receptionist-demo/"),
    # Stale pages with completely wrong slugs
    ("Customized_CEO_Dashboard.html",      "/Customized_CEO_Dashboard",   "/customized-ceo-dashboard-demo/"),
    ("whatsapp_receptionist_demo.html",    "/whatsapp_receptionist_demo", "/en/whatsapp-receptionist-demo/"),
]


def fix_canonical(html_path, wrong_slug, correct_slug):
    """Replace the wrong canonical href with the correct trailing-slash version."""
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    wrong_without = wrong_slug.rstrip("/")
    pattern = re.compile(
        r'(<link\s+rel=["\']canonical["\']\s+href=["\'])' +
        re.escape(BASE_URL + wrong_without) +
        r'/?(["\'])',
        re.IGNORECASE
    )
    new_href = BASE_URL + correct_slug
    new_content, count = pattern.subn(r'\g<1>' + new_href + r'\2', content)

    if count:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


# ---------------------------------------------------------------------------
# 2. SITEMAP GENERATION
# ---------------------------------------------------------------------------

EXCLUDED_FILENAMES = {
    "test.html",
    "onboarding.html",
    "privacy.html",
    "Customized_CEO_Dashboard.html",
    "whatsapp_receptionist_demo.html",
    "medflow-sales-automation-demo.html",
    "medflow-sales-automation-demo-ar.html",
}

EXCLUDED_PATTERNS = re.compile(r"(-new\.html|preview-templates\.html)$", re.IGNORECASE)

STATIC_URLS = [
    # Arabic core (root)
    ("/",                                  1.0),
    ("/about/",                            0.8),
    ("/contact/",                          0.8),
    ("/process/",                          0.8),
    ("/services/",                         0.8),
    ("/blog-ar/",                          0.8),
    ("/academy-ar/",                       0.8),
    ("/campaign-roi-simulator-ar/",        0.7),
    ("/customized-ceo-dashboard-demo-ar/", 0.7),
    ("/missed-call-simulator-ar/",         0.7),
    ("/whatsapp-receptionist-demo-ar/",    0.7),
    # English core (/en/ prefix)
    ("/en/",                               0.9),
    ("/en/about-en/",                      0.8),
    ("/en/contact-en/",                    0.8),
    ("/en/process-en/",                    0.8),
    ("/en/services-en/",                   0.8),
    ("/en/blog/",                          0.8),
    ("/en/academy/",                       0.8),
    ("/campaign-roi-simulator/",           0.7),
    ("/customized-ceo-dashboard-demo/",    0.7),
    ("/en/missed-call-simulator-en/",      0.7),
    ("/en/whatsapp-receptionist-demo/",    0.7),
]


def scan_content_dir(rel_dir, url_prefix, priority):
    entries = []
    abs_dir = os.path.join(PUBLIC_HTML, rel_dir)
    if not os.path.isdir(abs_dir):
        print(f"  [WARN] Directory not found: {abs_dir}")
        return entries
    for fname in sorted(os.listdir(abs_dir)):
        if not fname.endswith(".html") or fname == "index.html":
            continue
        if fname in EXCLUDED_FILENAMES or EXCLUDED_PATTERNS.search(fname):
            continue
        slug = fname[:-5]  # strip .html
        entries.append((f"{url_prefix}{slug}/", priority))
    return entries


def build_sitemap_entries():
    urls = list(STATIC_URLS)
    urls += scan_content_dir("blog/ar",    "/blog/ar/",    0.6)
    urls += scan_content_dir("blog/en",    "/blog/en/",    0.6)
    urls += scan_content_dir("academy/ar", "/academy/ar/", 0.6)
    urls += scan_content_dir("academy/en", "/academy/en/", 0.6)
    return urls


def generate_sitemap(urls):
    lastmod = datetime.now().strftime("%Y-%m-%d")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
    )
    for loc, priority in sorted(set(urls)):
        lines.append("  <url>")
        lines.append(f"    <loc>{BASE_URL}{loc}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("    <changefreq>weekly</changefreq>")
        lines.append(f"    <priority>{priority:.1f}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. ROBOTS.TXT CHECK
# ---------------------------------------------------------------------------
EXPECTED_SITEMAP_DIRECTIVE = f"Sitemap: {BASE_URL}/sitemap.xml"


def check_robots():
    if not os.path.isfile(ROBOTS_PATH):
        print(f"  [ERROR] robots.txt not found at {ROBOTS_PATH}")
        return False
    with open(ROBOTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    if EXPECTED_SITEMAP_DIRECTIVE in content:
        print(f"  [OK] robots.txt contains correct: {EXPECTED_SITEMAP_DIRECTIVE}")
        return True
    fixed = re.sub(r"Sitemap:.*", EXPECTED_SITEMAP_DIRECTIVE, content)
    if fixed != content:
        with open(ROBOTS_PATH, "w", encoding="utf-8") as f:
            f.write(fixed)
        print(f"  [FIXED] robots.txt Sitemap directive updated.")
    else:
        with open(ROBOTS_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{EXPECTED_SITEMAP_DIRECTIVE}\n")
        print(f"  [ADDED] Sitemap directive appended to robots.txt.")
    return True


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  aiprofitlab.io — Canonical Fix + Sitemap Regeneration")
    print("=" * 60)

    # Step 1: Fix canonical tags
    print("\n[1/3] Fixing canonical tags on root-level pages...")
    fix_count = 0
    skip_count = 0
    for rel_path, wrong_slug, correct_slug in CANONICAL_FIXES:
        html_path = os.path.join(PUBLIC_HTML, rel_path)
        if not os.path.isfile(html_path):
            print(f"  [SKIP] File not found: {rel_path}")
            skip_count += 1
            continue
        fixed = fix_canonical(html_path, wrong_slug, correct_slug)
        if fixed:
            print(f"  [FIXED] {rel_path}  {wrong_slug} -> {correct_slug}")
            fix_count += 1
        else:
            print(f"  [OK]    {rel_path}: canonical already correct")
    print(f"  -> {fix_count} canonical tags fixed, {skip_count} files skipped.")

    # Step 2: Regenerate sitemap
    print("\n[2/3] Regenerating sitemap.xml...")
    urls = build_sitemap_entries()
    sitemap_xml = generate_sitemap(urls)
    with open(SITEMAP_OUT, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
    print(f"  -> Written to: {SITEMAP_OUT}")
    print(f"  -> Total URLs: {len(urls)}")
    blog_ar_count = sum(1 for u, _ in urls if u.startswith("/blog/ar/"))
    blog_en_count = sum(1 for u, _ in urls if u.startswith("/blog/en/"))
    acad_ar_count = sum(1 for u, _ in urls if u.startswith("/academy/ar/"))
    acad_en_count = sum(1 for u, _ in urls if u.startswith("/academy/en/"))
    print(f"     Static pages : {len(STATIC_URLS)}")
    print(f"     Blog AR      : {blog_ar_count}")
    print(f"     Blog EN      : {blog_en_count}")
    print(f"     Academy AR   : {acad_ar_count}")
    print(f"     Academy EN   : {acad_en_count}")

    # Step 3: Verify robots.txt
    print("\n[3/3] Verifying robots.txt...")
    check_robots()

    # Step 4: Preview first 30 URLs
    print("\n[PREVIEW] First 30 URLs in new sitemap:")
    for loc, pri in sorted(set(urls))[:30]:
        print(f"  {pri:.1f}  {BASE_URL}{loc}")

    print("\nDone. Review the output above, then push public_html to production.")


if __name__ == "__main__":
    main()
