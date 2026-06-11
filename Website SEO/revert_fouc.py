import os
import glob
import re

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)

fouc_style = """
<style>
  #fouc-overlay {
    position: fixed;
    inset: 0;
    z-index: 999999;
    background: #050505;
    transition: opacity 0.3s ease;
  }
</style>
"""

fouc_div = '\n<div id="fouc-overlay"></div>\n'

fouc_script = """
<script>
  (function() {
    var overlay = document.getElementById('fouc-overlay');
    function removeOverlay() {
      if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(function() {
          if (overlay && overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
          }
        }, 320);
      }
    }
    if (document.readyState === 'complete') {
      setTimeout(removeOverlay, 100);
    } else {
      window.addEventListener('load', function() {
        setTimeout(removeOverlay, 100);
      });
    }
  })();
</script>
"""

for filepath in html_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Revert Tailwind Link to CDN
    # We replace any variation of the local link with the CDN script
    content = re.sub(
        r'<link\s+rel="stylesheet"\s+href="/assets/css/tailwind\.min\.css"\s*>',
        '<script src="https://cdn.tailwindcss.com"></script>',
        content
    )

    # 2. Add FOUC overlay style to <head> if not present
    if '#fouc-overlay' not in content:
        # Try to put it after <head>
        content = re.sub(r'(<head[^>]*>)', r'\1' + fouc_style, content, count=1, flags=re.IGNORECASE)

    # 3. Add <div id="fouc-overlay"></div> after <body>
    if 'id="fouc-overlay"' not in content:
        content = re.sub(r'(<body[^>]*>)', r'\1' + fouc_div, content, count=1, flags=re.IGNORECASE)

    # 4. Add removal script before </body>
    if 'var overlay = document.getElementById(\'fouc-overlay\');' not in content:
        content = re.sub(r'(</body>)', fouc_script + r'\n\1', content, count=1, flags=re.IGNORECASE)

    # 5. Remove leftover hacks
    # Removing visibility hidden hack
    content = re.sub(r'<style>body\s*\{\s*visibility:\s*hidden;\s*\}</style>', '', content, flags=re.IGNORECASE)
    # Removing visibility visible hack
    content = re.sub(r'<script>document\.body\.style\.visibility\s*=\s*[\'"]visible[\'"];</script>', '', content, flags=re.IGNORECASE)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {os.path.basename(filepath)}")

# 6. Delete the tailwind.min.css file
css_file = os.path.join(PUBLIC_HTML, "assets/css/tailwind.min.css")
if os.path.exists(css_file):
    os.remove(css_file)
    print("Deleted public_html/assets/css/tailwind.min.css")

print("Reversion and FOUC overlay implementation completed.")
