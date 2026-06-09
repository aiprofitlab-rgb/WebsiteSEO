#!/usr/bin/env python3
"""
Simplify the script loader block in HTML files by delegating GTM loading to main.js.
"""

import os
import glob

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

OLD_LAZY_LOAD_START = '<!-- Unified Performance Optimized Scripts Loader -->'
CLEAN_LAZY_LOAD_BLOCK = """    <!-- Unified Performance Optimized Scripts Loader -->
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

stats = {"total": 0, "cleaned": 0}

for filepath in sorted(html_files):
    stats["total"] += 1
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    idx = content.find(OLD_LAZY_LOAD_START)
    if idx != -1:
        # Find </html>
        html_end_idx = content.lower().find("</html>", idx)
        if html_end_idx != -1:
            # We replace from idx to the end of the file (since it ends with </body>\n</html>)
            new_content = content[:idx] + CLEAN_LAZY_LOAD_BLOCK + "\n</html>"
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                stats["cleaned"] += 1
                rel_path = os.path.relpath(filepath, PUBLIC_HTML)
                print(f"  Cleaned loader: {rel_path}")

print(f"\n{'='*50}")
print(f"Total files scanned: {stats['total']}")
print(f"Total files cleaned: {stats['cleaned']}")
print(f"{'='*50}")
