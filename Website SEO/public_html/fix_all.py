import os
import glob
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content
    
    # contact.html case
    if "function toggleChat() {" in content and "document.getElementById('aiden-ui').classList.toggle('active');" in content and "FIXED: MOBILE MENU TOGGLE" in content:
        # replace the unclosed toggleChat
        pattern = r"function toggleChat\(\) \{[\s]*document\.getElementById\('aiden-ui'\)\.classList\.toggle\('active'\);[\s]*/ ==================== FIXED: MOBILE MENU TOGGLE"
        rep = """function toggleChat() {
            document.getElementById('aiden-ui').classList.toggle('active');
        }

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

        // ==================== FIXED: MOBILE MENU TOGGLE"""
        content = re.sub(pattern, rep, content)
        
    if content != orig:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed", file)

