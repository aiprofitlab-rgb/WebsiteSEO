#!/usr/bin/env python3
"""
Batch process all HTML files to strip Google Tag Manager from the head and schedule
its lazy-load after rendering has completed.
"""

import os
import re
import glob

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

# GTM pattern in <head>
GTM_PATTERN = re.compile(
    r'\s*<!-- Google tag \(gtag\.js\) -->\s*'
    r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-2GPVY4Z5KR"></script>\s*'
    r'<script>\s*'
    r'window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];\s*'
    r'function\s+gtag\(\)\{\s*dataLayer\.push\(arguments\);\s*\}\s*'
    r"gtag\('js',\s*new\s+Date\(\)\);\s*"
    r"gtag\('config',\s*'G-2GPVY4Z5KR'\);\s*"
    r'</script>',
    re.DOTALL
)

# Alternative simple GTM patterns if comments differ
ALT_GTM_PATTERN_1 = re.compile(
    r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=G-2GPVY4Z5KR"></script>\s*'
    r'<script>\s*'
    r'window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];\s*'
    r'function\s+gtag\(\)\{\s*dataLayer\.push\(arguments\);\s*\}\s*'
    r"gtag\('js',\s*new\s+Date\(\)\);\s*"
    r"gtag\('config',\s*'G-2GPVY4Z5KR'\);\s*"
    r'</script>',
    re.DOTALL
)

OLD_LAZY_LOAD_START = '<!-- Unified Performance Optimized Scripts Loader -->'
NEW_LAZY_LOAD_BLOCK = """    <!-- Unified Performance Optimized Scripts Loader -->
    <script defer src="/js/main.js"></script>
    <script>
        // Placeholder tracking queue to prevent reference errors during lazy-load
        window.dataLayer = window.dataLayer || [];
        window.gtag = window.gtag || function(){ dataLayer.push(arguments); };
        
        function loadScript(src) {
            return new Promise((resolve, reject) => {
                const s = document.createElement('script');
                s.src = src;
                s.async = true;
                s.onload = resolve;
                s.onerror = reject;
                document.body.appendChild(s);
            });
        }
        
        let chatLoading = false;
        window.toggleChat = function() {
            if (window.aidenChat) {
                window.aidenChat.toggle();
            } else if (!chatLoading) {
                chatLoading = true;
                loadScript('/js/aiden-chat.js').then(() => {
                    window.aidenChat.init();
                    window.aidenChat.toggle();
                });
            }
        };
        
        window.handleSend = function() {
            if (window.aidenChat) {
                window.aidenChat.send();
            }
        };
        
        let formLoading = false;
        window.openAuditForm = function() {
            if (window.auditForm) {
                window.auditForm.open();
            } else if (!formLoading) {
                formLoading = true;
                loadScript('/js/audit-form.js').then(() => {
                    window.auditForm.init();
                    window.auditForm.open();
                });
            }
        };
        
        window.closeAuditForm = function() {
            if (window.auditForm) {
                window.auditForm.close();
            }
        };
        
        // Lazy-load GTM after 3s idle period
        const lazyLoadGTM = () => {
            const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 50));
            schedule(() => {
                setTimeout(() => {
                    loadScript("https://www.googletagmanager.com/gtag/js?id=G-2GPVY4Z5KR").then(() => {
                        gtag('js', new Date());
                        gtag('config', 'G-2GPVY4Z5KR');
                    });
                }, 3000);
            });
        };
        lazyLoadGTM();
        
        // Lazy-load chatbot after 10s delay to keep initial load completely clean
        setTimeout(() => {
            if (!chatLoading && !window.aidenChat) {
                chatLoading = true;
                loadScript('/js/aiden-chat.js').then(() => {
                    window.aidenChat.init();
                });
            }
        }, 10000);
    </script>
</body>"""

stats = {"total": 0, "gtm_removed": 0, "loader_updated": 0}

for filepath in sorted(html_files):
    stats["total"] += 1
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    original = content
    changed = False
    
    # 1. Remove GTM from head
    new_content, count = GTM_PATTERN.subn("", content)
    if count > 0:
        content = new_content
        changed = True
        stats["gtm_removed"] += 1
    else:
        new_content, count = ALT_GTM_PATTERN_1.subn("", content)
        if count > 0:
            content = new_content
            changed = True
            stats["gtm_removed"] += 1
            
    # 2. Update the loader block at the bottom
    # We find from OLD_LAZY_LOAD_START to the closing </html>
    loader_start_idx = content.find(OLD_LAZY_LOAD_START)
    if loader_start_idx != -1:
        # Find </html>
        html_end_idx = content.lower().find("</html>", loader_start_idx)
        if html_end_idx != -1:
            # We replace from loader_start_idx to the end of the file (since it ends with </body>\n</html>)
            content = content[:loader_start_idx] + NEW_LAZY_LOAD_BLOCK + "\n</html>"
            changed = True
            stats["loader_updated"] += 1
            
    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        rel_path = os.path.relpath(filepath, PUBLIC_HTML)
        print(f"  Optimized TBT: {rel_path}")

print(f"\n{'='*50}")
print(f"Total files scanned:      {stats['total']}")
print(f"GTM tags removed from head: {stats['gtm_removed']}")
print(f"Loader blocks modernized: {stats['loader_updated']}")
print(f"{'='*50}")
