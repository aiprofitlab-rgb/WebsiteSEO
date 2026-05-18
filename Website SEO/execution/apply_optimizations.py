import os
import glob
import re

# 1. Update .htaccess
htaccess_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/.htaccess"
with open(htaccess_path, 'r', encoding='utf-8') as f:
    htaccess_content = f.read()

# Check if compression is already added
if "mod_deflate.c" not in htaccess_content:
    optimization_rules = """# ----------------------------------------------------------------------
# | Compression & Caching Optimization                                 |
# ----------------------------------------------------------------------
<IfModule mod_deflate.c>
    # Compress HTML, CSS, JavaScript, Text, XML and fonts
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/vnd.ms-fontobject
    AddOutputFilterByType DEFLATE application/x-font
    AddOutputFilterByType DEFLATE application/x-font-opentype
    AddOutputFilterByType DEFLATE application/x-font-otf
    AddOutputFilterByType DEFLATE application/x-font-truetype
    AddOutputFilterByType DEFLATE application/x-font-ttf
    AddOutputFilterByType DEFLATE application/x-javascript
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE font/opentype
    AddOutputFilterByType DEFLATE font/otf
    AddOutputFilterByType DEFLATE font/ttf
    AddOutputFilterByType DEFLATE image/svg+xml
    AddOutputFilterByType DEFLATE image/x-icon
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/javascript
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/xml

    # Remove browser bugs (only needed for really old browsers)
    BrowserMatch ^Mozilla/4 gzip-only-text/html
    BrowserMatch ^Mozilla/4\.0[678] no-gzip
    BrowserMatch \\bMSIE !no-gzip !gzip-only-text/html
    Header append Vary User-Agent
</IfModule>

<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType text/javascript "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType font/ttf "access plus 1 year"
    ExpiresByType font/woff "access plus 1 year"
    ExpiresByType font/woff2 "access plus 1 year"
</IfModule>

<IfModule mod_headers.c>
    <FilesMatch "\.(jpeg|jpg|png|webp|svg|css|js|woff|woff2|ttf)$">
        Header set Cache-Control "public, max-age=31536000, immutable"
    </FilesMatch>
</IfModule>

"""
    new_htaccess = optimization_rules + htaccess_content
    with open(htaccess_path, 'w', encoding='utf-8') as f:
        f.write(new_htaccess)
    print("Updated .htaccess with caching and compression rules.")
else:
    print(".htaccess already contains compression rules.")

# 2. Update HTML files for deferring scripts
html_files = glob.glob("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html", recursive=True)

modified_files = 0
for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add defer to tailwind
    content = content.replace('<script src="https://cdn.tailwindcss.com"></script>', '<script defer src="https://cdn.tailwindcss.com"></script>')
    content = content.replace('<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>', '<script defer src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>')
    
    # Add defer to Chart.js
    content = content.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>', '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>')

    if content != original_content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
        modified_files += 1

print(f"Updated {modified_files} HTML files to defer scripts.")
