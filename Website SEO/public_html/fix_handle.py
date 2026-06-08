import os
import glob
import re

html_files = glob.glob('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/**/*.html', recursive=True)

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    orig = content

    # Look for broken handleSend in English files
    # The broken catch block:
    pattern = r"\} catch \(error\) \{\s*document\.getElementById\('typing-indicator'\)\?\.remove\(\);\s*box\.innerHTML \+= `<div class=\"bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-\[85%\] text-red-300\">Sorry, please try again</div>`;\s*box\.scrollTop = box\.scrollHeight;\s*function toggleChat\(\) \{"

    if re.search(pattern, content):
        rep = """} catch (error) {
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-red-300">Sorry, please try again</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        function toggleChat() {"""
        content = re.sub(pattern, rep, content)
        
    # Same but with console.error included (for en/index.html)
    pattern2 = r"\} catch \(error\) \{\s*console\.error\('Chat error:', error\);\s*document\.getElementById\('typing-indicator'\)\?\.remove\(\);\s*box\.innerHTML \+= `<div class=\"bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-\[85%\] text-red-300\">Sorry, please try again</div>`;\s*box\.scrollTop = box\.scrollHeight;\s*function toggleChat\(\) \{"
    if re.search(pattern2, content):
        rep2 = """} catch (error) {
                console.error('Chat error:', error);
                document.getElementById('typing-indicator')?.remove();
                box.innerHTML += `<div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none max-w-[85%] text-red-300">Sorry, please try again</div>`;
            }
            box.scrollTop = box.scrollHeight;
        }

        function toggleChat() {"""
        content = re.sub(pattern2, rep2, content)

    if content != orig:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Fixed handleSend in", file)

