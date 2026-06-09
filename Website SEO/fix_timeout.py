import os
import re

files = [
    "contact.html", "about.html", "process.html", "services.html",
    "contact-en.html", "about-en.html", "process-en.html", "services-en.html",
    "index.html", "en/index.html"
]

for f in files:
    path = os.path.join("public_html", f)
    if not os.path.exists(path):
        continue
        
    with open(path, "r") as file:
        content = file.read()
        
    # We want to find the window.addEventListener('load' block and make sure setTimeout happens instantly, without awaiting detectCountry()
    
    # 1. replace window.addEventListener('load', async () => { await detectCountry();
    # with window.addEventListener('load', () => { detectCountry(); 
    content = re.sub(
        r"window\.addEventListener\('load',\s*async\s*\(\)\s*=>\s*\{\s*await\s*detectCountry\(\);",
        r"window.addEventListener('load', () => {\n            detectCountry();",
        content
    )
    
    # 2. replace window.addEventListener('load', async function() { await detectCountry();
    content = re.sub(
        r"window\.addEventListener\('load',\s*async\s*function\(\)\s*\{\s*await\s*detectCountry\(\);",
        r"window.addEventListener('load', function() {\n            detectCountry();",
        content
    )

    with open(path, "w") as file:
        file.write(content)
        
print("Timeout fixed in 10 files")
