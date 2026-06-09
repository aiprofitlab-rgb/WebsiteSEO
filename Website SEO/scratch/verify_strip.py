#!/usr/bin/env python3
import os
import glob
from bs4 import BeautifulSoup

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

unoptimized_files = []

for filepath in sorted(html_files):
    rel_path = os.path.relpath(filepath, PUBLIC_HTML)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if there is any script containing "MULTI-STEP", "auditForm", "detectCountry", or "initNav"
    soup = BeautifulSoup(content, "html.parser")
    for script in soup.find_all("script"):
        # We only check inline scripts (no src)
        if not script.get("src"):
            text = script.string or ""
            if "auditform" in text.lower() or "detectcountry" in text.lower() or "initnav" in text.lower():
                unoptimized_files.append((rel_path, script.string[:100].strip()))

print(f"Total files scanned: {len(html_files)}")
print(f"Unoptimized files containing inline scripts: {len(unoptimized_files)}")
for f, snippet in unoptimized_files[:20]:
    print(f"File: {f} | Snippet: {snippet}...")
if len(unoptimized_files) > 20:
    print("...")
