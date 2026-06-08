import re

filepath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
script = scripts[5]  # script #6 (0-indexed = 5)

# Find around line 50-60
lines = script.splitlines()
for i, line in enumerate(lines[45:70], start=46):
    print(f"{i:3}: {repr(line)}")
