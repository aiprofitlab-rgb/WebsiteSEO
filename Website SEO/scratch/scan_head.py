#!/usr/bin/env python3
import os
import glob
from bs4 import BeautifulSoup

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

blocking_scripts = []
blocking_css = []

for filepath in sorted(html_files):
    rel_path = os.path.relpath(filepath, PUBLIC_HTML)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    try:
        start = content.lower().find("<head>")
        end = content.lower().find("</head>")
        if start != -1 and end != -1:
            head_content = content[start:end+7]
            soup = BeautifulSoup(head_content, "html.parser")
            
            # Find scripts
            for script in soup.find_all("script"):
                src = script.get("src")
                stype = script.get("type", "")
                if src:
                    if "application/ld+json" in stype:
                        continue
                    is_async = "async" in script.attrs
                    is_defer = "defer" in script.attrs
                    if not is_async and not is_defer:
                        blocking_scripts.append((rel_path, str(script)))
            
            # Find stylesheets
            for link in soup.find_all("link"):
                # Check if it has a noscript parent
                if link.find_parent("noscript"):
                    continue
                
                rel = link.get("rel", [])
                if isinstance(rel, str):
                    rel = [rel]
                href = link.get("href", "")
                if "stylesheet" in rel:
                    onload = link.get("onload")
                    media = link.get("media")
                    if not onload:
                        blocking_css.append((rel_path, str(link)))
    except Exception as e:
        print(f"Error parsing {rel_path}: {e}")

print(f"Total files scanned: {len(html_files)}")
print(f"\n--- Render-Blocking Script Tags found in <head> ({len(blocking_scripts)}) ---")
for f, tag in blocking_scripts[:15]:
    print(f"File: {f} | Tag: {tag}")
if len(blocking_scripts) > 15:
    print("...")

print(f"\n--- Render-Blocking Stylesheet Tags found in <head> ({len(blocking_css)}) ---")
for f, tag in blocking_css[:15]:
    print(f"File: {f} | Tag: {tag}")
if len(blocking_css) > 15:
    print("...")
