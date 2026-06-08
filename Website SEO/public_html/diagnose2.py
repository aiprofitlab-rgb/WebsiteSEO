import re, subprocess

files_to_check = [
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html',
]

# For each file, get scripts 6 and 7 (index 5, 6) which are still broken
for filepath in files_to_check[:2]:  # just check 2 to see pattern
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    scripts = re.findall(r'<script\b[^>]*>([\s\S]*?)<\/script>', content, re.IGNORECASE)
    for i in [5, 6]:
        if i < len(scripts):
            print(f"\n=== {filepath.split('/')[-1]} Script #{i+1} ===")
            print(scripts[i][:1500])
