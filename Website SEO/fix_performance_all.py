import os
import glob
import re
from bs4 import BeautifulSoup

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
# ignore files starting with test
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

CRITICAL_CSS = """
/* === ANTI-BLACK-SCREEN: Critical layout fallback (pre-Tailwind) === */
.text-white { color: #fff; }
.text-gray-300 { color: #d1d5db; }
.text-gray-400 { color: #9ca3af; }
.text-blue-500 { color: #3b82f6; }
.text-red-500 { color: #ef4444; }
.text-red-400 { color: #f87171; }
.text-green-400 { color: #4ade80; }
.text-green-500 { color: #22c55e; }
.text-purple-400 { color: #c084fc; }
.text-transparent { color: transparent; }
.bg-clip-text { -webkit-background-clip: text; background-clip: text; }
.bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops, #3b82f6, #22c55e)); }
.from-blue-500 { --tw-gradient-from: #3b82f6; --tw-gradient-stops: #3b82f6, #22c55e; }
.text-sm { font-size: 0.875rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }
.text-2xl { font-size: 1.5rem; }
.text-3xl { font-size: 1.875rem; }
.text-4xl { font-size: 2.25rem; }
.text-5xl { font-size: 3rem; }
.font-bold { font-weight: 700; }
.font-extrabold { font-weight: 800; }
.flex { display: flex; }
.hidden { display: none; }
.block { display: block; }
.grid { display: grid; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.flex-col { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }
.text-center { text-align: center; }
.text-left { text-align: left; }
.mx-auto { margin-left: auto; margin-right: auto; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.py-8 { padding-top: 2rem; padding-bottom: 2rem; }
.py-16 { padding-top: 4rem; padding-bottom: 4rem; }
.py-24 { padding-top: 6rem; padding-bottom: 6rem; }
.pt-16 { padding-top: 4rem; }
.pt-24 { padding-top: 6rem; }
.pb-8 { padding-bottom: 2rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-6 { margin-top: 1.5rem; }
.mt-8 { margin-top: 2rem; }
.mt-10 { margin-top: 2.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.gap-4 { gap: 1rem; }
.gap-8 { gap: 2rem; }
.gap-12 { gap: 3rem; }
.max-w-4xl { max-width: 56rem; }
.max-w-6xl { max-width: 72rem; }
.min-h-screen { min-height: 100vh; }
.w-full { width: 100%; }
.fixed { position: fixed; }
.relative { position: relative; }
.absolute { position: absolute; }
.z-50 { z-index: 50; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-2xl { border-radius: 1rem; }
.rounded-3xl { border-radius: 1.5rem; }
.overflow-hidden { overflow: hidden; }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
.leading-relaxed { line-height: 1.625; }
.leading-tight { line-height: 1.25; }
.transition { transition-property: all; transition-duration: 0.15s; }
.inline-block { display: inline-block; }
.inline-flex { display: inline-flex; }
@media (min-width: 768px) {
  .md\:flex { display: flex; }
  .md\:hidden { display: none; }
  .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .md\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .md\:px-12 { padding-left: 3rem; padding-right: 3rem; }
  .md\:text-3xl { font-size: 1.875rem; }
  .md\:text-4xl { font-size: 2.25rem; }
  .md\:text-5xl { font-size: 3rem; }
  .md\:text-7xl { font-size: 4.5rem; }
  .md\:w-1\/2 { width: 50%; }
  .md\:flex-row { flex-direction: row; }
  .md\:col-span-2 { grid-column: span 2; }
}
@media (min-width: 640px) {
  .sm\:text-6xl { font-size: 3.75rem; }
  .sm\:flex-row { flex-direction: row; }
}
/* === CLS FIX: Constrain all chevron/arrow/scroll SVGs === */
.chevron, [class*="chevron"], [class*="arrow"], [class*="scroll"] svg,
.swiper-button-next, .swiper-button-prev {
  width: 40px !important; height: 40px !important;
  max-width: 40px !important; max-height: 40px !important;
}
svg { max-width: 100%; height: auto; overflow: hidden; }
svg:not([width]) { width: 24px; height: 24px; }
/* Nav chevron SVGs: lock to exact inline dimensions */
nav svg[width="16"][height="16"] { width: 16px !important; height: 16px !important; max-width: 16px !important; max-height: 16px !important; }
"""

updated_files = []

for filepath in html_files:
    if "index.html" in filepath and filepath.endswith("index.html") and len(filepath.split("/")) <= 9:
        # Already manually fixed the main index and en/index
        pass
        
    rel_path = os.path.relpath(filepath, PUBLIC_HTML)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    modified = False

    # 1. Add CRITICAL_CSS to head if not present
    if not soup.find(string=re.compile(r"ANTI-BLACK-SCREEN")):
        style_tag = soup.new_tag("style")
        style_tag.string = CRITICAL_CSS
        # Find where to insert it: after the tailwind noscript or just at end of head
        if soup.head:
            # Just append to the end of head
            soup.head.append(style_tag)
            modified = True
            
    # 2. Add fetchpriority to preload images if present
    for preload in soup.find_all('link', rel='preload', as_='image'):
        if not preload.has_attr('fetchpriority'):
            preload['fetchpriority'] = 'high'
            modified = True

    # 3. Clean up the duplicate generic SVG style block if it exists
    for style in soup.find_all('style'):
        if style.string and "svg { max-width: 100%; height: auto; overflow: hidden; } svg:not([width]) { width: 24px; height: 24px; }" in style.string:
            if "ANTI-BLACK-SCREEN" not in style.string: # keep the critical css one
                style.decompose()
                modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Prevent bs4 from messing up script tags formatting too much
            # We use a formatter to keep it similar
            html_str = soup.encode(formatter="html5").decode('utf-8')
            # Fix duplicate html tags if bs4 added them
            html_str = html_str.replace("<html>\n<html>", "<html>").replace("</html>\n</html>", "</html>")
            
            f.write(html_str)
        updated_files.append(rel_path)

print(f"Total HTML files updated with critical CSS and fixes: {len(updated_files)}")
