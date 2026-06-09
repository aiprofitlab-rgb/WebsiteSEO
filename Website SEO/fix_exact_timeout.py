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
        
    # Replace the whole if(!sessionStorage) ... block with exactly what the user wants
    
    # regex to match:
    # if (!sessionStorage.getItem('aidenPopped')) { ... }
    # and any setTimeout inside
    
    new_content = re.sub(
        r"if\s*\(\!sessionStorage\.getItem\('aidenPopped'\)\)\s*\{\s*setTimeout\(\(\)\s*=>\s*\{[\s\S]*?\},?\s*10000\);\s*\}",
        r"setTimeout(() => toggleChat(), 10000);",
        content
    )
    
    # In some files it might be one-liner:
    new_content = re.sub(
        r"if\(!sessionStorage\.getItem\('aidenPopped'\)\)\{\s*setTimeout\(\(\)=>\{\s*if\(!document\.getElementById\('aiden-ui'\)\.classList\.contains\('active'\)\)\{\s*toggleChat\(\);\s*sessionStorage\.setItem\('aidenPopped','true'\);\s*\}\s*\},10000\);\s*\}",
        r"setTimeout(() => toggleChat(), 10000);",
        new_content
    )

    with open(path, "w") as file:
        file.write(new_content)
        
print("Timeout exact matched in 10 files")
