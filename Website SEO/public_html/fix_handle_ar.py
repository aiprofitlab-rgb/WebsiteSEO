import os
import glob
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content

    # Look for broken handleSend in Arabic files
    # The broken catch block:
    pattern = r"\} catch \(error\) \{\s*document\.getElementById\('typing-indicator'\)\?\.remove\(\);\s*box\.innerHTML \+= `<div class=\"bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-\[85%\] text-red-300\">عذراً، حدث خطأ</div>`;\s*box\.scrollTop = box\.scrollHeight;\s*function toggleChat\(\) \{"

    if re.search(pattern, content):
        rep = """} catch (error) {
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tr-none max-w-[85%] text-red-300">عذراً، حدث خطأ</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        function toggleChat() {"""
        content = re.sub(pattern, rep, content)

    if content != orig:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed handleSend in", file)

