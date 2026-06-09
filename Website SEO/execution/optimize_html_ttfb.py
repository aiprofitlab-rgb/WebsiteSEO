#!/usr/bin/env python3
"""
Batch optimize all HTML files for TTFB/LCP performance.

Changes applied:
1. Add `defer` to the Tailwind CDN <script> tag
2. Remove the duplicate/placeholder gtag block (G-XXXXXXXXXX)
3. Ensure preconnect hints for fonts.googleapis.com and fonts.gstatic.com 
   are placed early in <head> (before other external loads)
"""

import os
import re
import glob

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

# Find ALL .html files recursively
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)

# Skip test files
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

stats = {"total": 0, "tailwind_fixed": 0, "gtag_removed": 0, "preconnect_added": 0}

for filepath in sorted(html_files):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    original = content
    changed = False
    
    # --- 1. Add `defer` to Tailwind CDN script ---
    # Match <script src="https://cdn.tailwindcss.com"> (with or without query params)
    # but NOT if it already has defer
    tailwind_pattern = r'<script\s+src="https://cdn\.tailwindcss\.com([^"]*)">\s*</script>'
    
    def add_defer(match):
        full = match.group(0)
        # Only add defer if not already present
        if 'defer' not in full:
            query = match.group(1)
            return f'<script defer src="https://cdn.tailwindcss.com{query}"></script>'
        return full
    
    new_content = re.sub(tailwind_pattern, add_defer, content)
    if new_content != content:
        content = new_content
        changed = True
        stats["tailwind_fixed"] += 1
    
    # --- 2. Remove duplicate/placeholder G-XXXXXXXXXX gtag block ---
    # This pattern matches the second <script> block with the placeholder config ID
    gtag_placeholder = re.compile(
        r'\s*<script>\s*'
        r"window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];\s*"
        r"function\s+gtag\(\)\{dataLayer\.push\(arguments\);\}\s*"
        r"gtag\('js',\s*new\s+Date\(\)\);\s*"
        r"gtag\('config',\s*'G-XXXXXXXXXX'\);\s*"
        r"</script>",
        re.DOTALL
    )
    
    new_content = gtag_placeholder.sub("", content)
    if new_content != content:
        content = new_content
        changed = True
        stats["gtag_removed"] += 1
    
    # --- 3. Ensure preconnect hints exist early in <head> ---
    preconnect_googleapis = '<link rel="preconnect" href="https://fonts.googleapis.com">'
    preconnect_gstatic = '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    
    # Check if they already exist
    has_googleapis = 'preconnect" href="https://fonts.googleapis.com"' in content
    has_gstatic = 'preconnect" href="https://fonts.gstatic.com"' in content
    
    if not has_googleapis or not has_gstatic:
        # Insert right after <head> or after the first <meta charset> line
        inject = ""
        if not has_googleapis:
            inject += f"\n    {preconnect_googleapis}"
        if not has_gstatic:
            inject += f"\n    {preconnect_gstatic}"
        
        # Try to insert after <meta charset="UTF-8">
        charset_pattern = r'(<meta\s+charset="UTF-8"\s*/?>)'
        if re.search(charset_pattern, content, re.IGNORECASE):
            content = re.sub(charset_pattern, r'\1' + inject, content, count=1)
            changed = True
            stats["preconnect_added"] += 1
        # Fallback: insert after <head>
        elif "<head>" in content:
            content = content.replace("<head>", "<head>" + inject, 1)
            changed = True
            stats["preconnect_added"] += 1
    
    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        stats["total"] += 1
        rel_path = os.path.relpath(filepath, PUBLIC_HTML)
        print(f"  ✅ {rel_path}")

print(f"\n{'='*50}")
print(f"Total files modified:      {stats['total']}")
print(f"Tailwind defer added:      {stats['tailwind_fixed']}")
print(f"Placeholder gtag removed:  {stats['gtag_removed']}")
print(f"Preconnect hints added:    {stats['preconnect_added']}")
print(f"{'='*50}")
