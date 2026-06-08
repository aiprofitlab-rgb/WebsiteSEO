import re, os

# Exact pattern from inspection - the `else if` is there but missing closing braces
BROKEN = r"""(showStep\(currentStep\);)\s*\n\s*\n\s*\} else if \(e\.target\.matches\('\.prev'\)\) \{\s*\n\s*if \(currentStep > 0\) \{\s*\n\s*currentStep--;\s*\n\s*showStep\(currentStep\);)\s*\n\s*\n\s*\}\);"""

FIXED = r"""\1
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
    content = re.sub(BROKEN, FIXED, content)
    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(filepath)}")
    else:
        print(f"No match: {os.path.basename(filepath)}")
