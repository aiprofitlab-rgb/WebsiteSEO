import re

file = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/en/index.html'

with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)

# Print scripts 8, 9, 10 (index 7, 8, 9)
for i in [7, 8, 9]:
    print(f"\n{'='*60}\nScript #{i+1}:\n{'='*60}")
    print(scripts[i][:3000])

