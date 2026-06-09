#!/usr/bin/env python3
"""
Batch process all HTML files to extract/strip inline chatbot, form, and nav scripts,
and replace them with a unified lazy-loading script loader and defer links.
"""

import os
import re
import glob

PUBLIC_HTML = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
html_files = glob.glob(os.path.join(PUBLIC_HTML, "**/*.html"), recursive=True)
html_files = [f for f in html_files if not os.path.basename(f).startswith("test")]

LAZY_LOAD_BLOCK = """    <!-- Unified Performance Optimized Scripts Loader -->
    <script defer src="/js/main.js"></script>
    <script>
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

stats = {"total": 0, "modified": 0}

for filepath in sorted(html_files):
    stats["total"] += 1
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Locate all occurrences of "<script"
    script_indices = []
    start = 0
    while True:
        idx = content.lower().find("<script", start)
        if idx == -1:
            break
        script_indices.append(idx)
        start = idx + 7
        
    # We want to find the first script tag that contains "auditModal", "auditForm", or "MULTI-STEP"
    target_idx = -1
    for idx in script_indices:
        # Look ahead to the end of this script or next parts
        # Let's search inside the script content
        script_end = content.find("</script>", idx)
        if script_end != -1:
            script_block = content[idx:script_end]
            if "auditmodal" in script_block.lower() or "auditform" in script_block.lower() or "multi-step" in script_block.lower() or "detectcountry" in script_block.lower():
                target_idx = idx
                break
                
    if target_idx != -1:
        # Find the </body> tag after target_idx
        body_end_idx = content.lower().find("</body>", target_idx)
        if body_end_idx != -1:
            # Replace from target_idx to body_end_idx + 7
            new_content = content[:target_idx] + LAZY_LOAD_BLOCK + content[body_end_idx + 7:]
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            stats["modified"] += 1
            rel_path = os.path.relpath(filepath, PUBLIC_HTML)
            print(f"  Optimized script payload: {rel_path}")
        else:
            print(f"  ⚠️ Warning: Found target script but no </body> in {filepath}")
    else:
        # If there is no audit form/chatbot script, check if there are standard nav script blocks at the bottom
        # Let's check if there is standard nav JS
        nav_idx = -1
        for idx in script_indices:
            script_end = content.find("</script>", idx)
            if script_end != -1:
                script_block = content[idx:script_end]
                if "initnav" in script_block.lower() or "standard nav js" in script_block.lower() or "mobilemenutoggle" in script_block.lower():
                    nav_idx = idx
                    break
        if nav_idx != -1:
            body_end_idx = content.lower().find("</body>", nav_idx)
            if body_end_idx != -1:
                # Replace with just main.js defer loader
                replacement = '    <script defer src="/js/main.js"></script>\n</body>'
                new_content = content[:nav_idx] + replacement + content[body_end_idx + 7:]
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                stats["modified"] += 1
                rel_path = os.path.relpath(filepath, PUBLIC_HTML)
                print(f"  Optimized nav script payload: {rel_path}")

print(f"\n{'='*50}")
print(f"Total files scanned:  {stats['total']}")
print(f"Total files modified: {stats['modified']}")
print(f"{'='*50}")
