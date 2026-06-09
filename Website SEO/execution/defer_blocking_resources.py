#!/usr/bin/env python3
"""
Batch script to defer all render-blocking CSS link tags in the <head> of HTML files.

Matches:
  <link href="URL" rel="stylesheet">
  <link rel="stylesheet" href="URL">
  (including with trailing slash, variations in spaces/quotes)

Replaces with:
  <link rel="preload" as="style" href="URL" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="URL"></noscript>
"""

import os
import re
import glob

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

# Regex pattern to match any <link> tag
LINK_PATTERN = re.compile(r'<link\s+([^>]+)>', re.IGNORECASE)

stats = {
    "scanned": 0,
    "modified_files": 0,
    "replaced_links": 0
}

for filepath in sorted(html_files):
    stats["scanned"] += 1
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    head_start = content.lower().find("<head>")
    head_end = content.lower().find("</head>")
    if head_start == -1 or head_end == -1:
        continue
    
    head_content = content[head_start:head_end + 7]
    original_head = head_content
    
    # We will look for links in this head content
    matches = list(LINK_PATTERN.finditer(head_content))
    if not matches:
        continue
        
    changed = False
    # Process from end to start so indices don't shift
    for match in reversed(matches):
        full_tag = match.group(0)
        attrs_str = match.group(1)
        
        # Parse attributes
        attrs = {}
        for attr_match in re.finditer(r'(\b\w+)\s*=\s*(["\'])(.*?)\2', attrs_str, re.IGNORECASE):
            attrs[attr_match.group(1).lower()] = attr_match.group(3)
        
        rel = attrs.get("rel", "")
        href = attrs.get("href", "")
        onload = attrs.get("onload", "")
        as_attr = attrs.get("as", "")
        
        # We target links that are stylesheets, have a href, are not preloads, and don't already have onload
        if "stylesheet" in rel.lower() and href and not onload and "preload" not in rel.lower():
            # Build replacement tag
            # We keep other attributes like media, media queries, etc. if any.
            # Usually only href and rel are present. Let's rebuild cleanly:
            replacement = (
                f'<link rel="preload" as="style" href="{href}" onload="this.onload=null;this.rel=\'stylesheet\'">\n'
                f'    <noscript><link rel="stylesheet" href="{href}"></noscript>'
            )
            
            # Find the match span and replace
            start_idx, end_idx = match.span()
            head_content = head_content[:start_idx] + replacement + head_content[end_idx:]
            changed = True
            stats["replaced_links"] += 1
            
    if changed:
        new_content = content[:head_start] + head_content + content[head_end + 7:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        stats["modified_files"] += 1
        rel_path = os.path.relpath(filepath, PUBLIC_HTML)
        print(f"  Processed: {rel_path}")

print(f"\n{'='*50}")
print(f"Total files scanned:      {stats['scanned']}")
print(f"Total files modified:     {stats['modified_files']}")
print(f"Total link tags deferred: {stats['replaced_links']}")
print(f"{'='*50}")
