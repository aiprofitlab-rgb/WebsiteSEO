import os
import glob
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

# Pattern for Arabic pages
pattern_ar = r"function toggleChat\(\) \{\s*document\.getElementById\('aiden-ui'\)\.classList\.toggle\('active'\);\s*/ ==================== INIT ====================\s*window\.onload = async function\(\) \{\s*await detectCountry\(\);\s*if \(!sessionStorage\.getItem\('aidenPopped'\)\) \{\s*setTimeout\(\(\) => \{\s*if \(!document\.getElementById\('aiden-ui'\)\.classList\.contains\('active'\)\) \{\s*toggleChat\(\);\s*sessionStorage\.setItem\('aidenPopped', 'true'\);\s*\}, 10000\);\s*\};\s*"

replacement_ar = """function toggleChat() {
            document.getElementById('aiden-ui').classList.toggle('active');
        }

        // ==================== INIT ====================
        window.onload = async function() {
            await detectCountry();
            if (!sessionStorage.getItem('aidenPopped')) {
                setTimeout(() => {
                    const chat = document.getElementById('aiden-ui');
                    if (chat && !chat.classList.contains('active')) {
                        toggleChat();
                        sessionStorage.setItem('aidenPopped', 'true');
                    }
                }, 10000);
            }
        };
"""

# Pattern for English pages (about-en, contact-en, process-en)
pattern_en = r"function toggleChat\(\) \{\s*document\.getElementById\('aiden-ui'\)\.classList\.toggle\('active'\);\s*// Close menu when clicking a link\s*mobileMenu\.querySelectorAll\('a'\)\.forEach\(link => \{\s*link\.addEventListener\('click', function\(\) \{\s*mobileMenu\.classList\.remove\('active'\);\s*\}\);\s*\}\);\s*// Close menu when clicking outside\s*document\.addEventListener\('click', function\(event\) \{\s*if \(!mobileToggle\.contains\(event\.target\) && !mobileMenu\.contains\(event\.target\)\) \{\s*mobileMenu\.classList\.remove\('active'\);\s*\}\);\s*\}\);\s*/ ==================== INIT ====================\s*window\.onload = async function\(\) \{\s*"

# Actually it's easier to just use a broader regex matching from "function toggleChat" down to "window.onload = async function() {"
# Let's replace the whole section from "function toggleChat() {" to the end of window.onload block (which ends with "};")

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig = content
    
    # 1. Fix en/index.html
    if 'en/index.html' in path:
        # It has a specific getPageSpecificGreeting inside toggleChat
        block_start = "function toggleChat() {"
        # We find the broken toggleChat block
        if "chatMessages.innerHTML = " in content and "// Close menu when clicking a link" in content:
            # We use regex to replace from "function toggleChat() {" to the end of window.onload
            pattern = r"function toggleChat\(\) \{[\s\S]*?\}, 10000\);\s*\};\s*"
            
            replacement = """function toggleChat() {
            const chat = document.getElementById('aiden-ui');
            chat.classList.toggle('active');
            
            // Update greeting when chat opens
            if (chat.classList.contains('active')) {
                const chatMessages = document.getElementById('chat-messages');
                const greeting = getPageSpecificGreeting();
                const welcomeMsg = document.getElementById('welcome-message')?.textContent || '';
                
                // Only update if it's the first message
                if (chatMessages.children.length === 1) {
                    chatMessages.innerHTML = `<div class="bg-gray-800 p-4 rounded-2xl rounded-tl-none max-w-[85%]">${greeting} <span class="block text-xs text-gray-500 mt-1">${welcomeMsg}</span></div>`;
                }
            }
        }

        // ==================== INIT ====================
        window.onload = async function() {
            await detectCountry();
            
            // Auto-pop chat for new visitors (after 10 seconds)
            if (!sessionStorage.getItem('aidenPopped')) {
                setTimeout(() => {
                    const chat = document.getElementById('aiden-ui');
                    if (chat && !chat.classList.contains('active')) {
                        toggleChat();
                        sessionStorage.setItem('aidenPopped', 'true');
                    }
                }, 10000);
            }
        };
"""
            # But wait, there's another toggleChat in en/index.html at line 785? No, the line 785 was public_html/index.html.
            # Wait, grep showed toggleChat at line 1224 in en/index.html. Let's just do a string replacement on that specific block.
            content = re.sub(pattern, replacement, content)

    else:
        # Arabic pages and other EN pages (process-en, about-en)
        # They have a simple toggleChat
        pattern1 = r"function toggleChat\(\) \{[\s]*document\.getElementById\('aiden-ui'\)\.classList\.toggle\('active'\);[\s]*// Close menu when clicking a link[\s\S]*?\}, 10000\);\s*\};\s*"
        pattern2 = r"function toggleChat\(\) \{[\s]*document\.getElementById\('aiden-ui'\)\.classList\.toggle\('active'\);[\s]*/ ==================== INIT ====================[\s\S]*?\}, 10000\);\s*\};\s*"
        
        rep = """function toggleChat() {
            const chat = document.getElementById('aiden-ui');
            if (chat) chat.classList.toggle('active');
        }

        // ==================== INIT ====================
        window.onload = async function() {
            await detectCountry();
            if (!sessionStorage.getItem('aidenPopped')) {
                setTimeout(() => {
                    const chat = document.getElementById('aiden-ui');
                    if (chat && !chat.classList.contains('active')) {
                        toggleChat();
                        sessionStorage.setItem('aidenPopped', 'true');
                    }
                }, 10000);
            }
        };
"""
        content = re.sub(pattern1, rep, content)
        content = re.sub(pattern2, rep, content)
    
    if content != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {path}")

for file in html_files:
    fix_file(file)

