import os

# Use literal string replacement (no regex) based on exact content
BROKEN = """                        showStep(currentStep);


            } else if (e.target.matches('.prev')) {
                if (currentStep > 0) {
                    currentStep--;
                    showStep(currentStep);


        });"""

FIXED = """                        showStep(currentStep);
                    }
                }
            } else if (e.target.matches('.prev')) {
                if (currentStep > 0) {
                    currentStep--;
                    showStep(currentStep);
                }
            }
        });"""

files = [
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html',
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    if BROKEN in content:
        content = content.replace(BROKEN, FIXED)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")
    else:
        # Try with different whitespace
        print(f"No exact match: {os.path.basename(filepath)} - checking variants...")
        # Find the area
        idx = content.find("} else if (e.target.matches('.prev')) {")
        if idx != -1:
            print(repr(content[idx-100:idx+200]))
