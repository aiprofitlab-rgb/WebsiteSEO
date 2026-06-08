import re, os

# Fix 1: about.html, contact.html, about-en.html, contact-en.html, process-en.html
# Error at line 57 in form script - the form click handler has missing closing braces
# Pattern: showStep(currentStep);\n\n\n        });
# Should add: }\n                }\n            } else if (...) { ...close... }

FORM_CLICK_BROKEN = r"""(form\.addEventListener\('click', \(e\) => \{
            if \(e\.target\.matches\('\.next'\)\) \{
                if \(validateStep\(currentStep\)\) \{
                    if \(currentStep < steps\.length - 1\) \{
                        currentStep\+\+;
                        showStep\(currentStep\);)\s*\n\s*\n\s*\}\);"""

FORM_CLICK_FIXED = r"""\1
                    }
                }
            } else if (e.target.matches('.prev')) {
                if (currentStep > 0) {
                    currentStep--;
                    showStep(currentStep);
                }
            }
        });"""

# Fix 2: process.html - different script (nav) with missing } for if block
PROCESS_NAV_BROKEN = r"""(if \(!mobileMenu\.contains\(event\.target\) && !toggleBtn\.contains\(event\.target\)\) \{
                        mobileMenu\.classList\.remove\('active'\);)\s*\n\s*\}\);"""

PROCESS_NAV_FIXED = r"""\1
                    }
                });"""

files_form = [
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html',
]

for filepath in files_form:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    content = re.sub(FORM_CLICK_BROKEN, FORM_CLICK_FIXED, content)
    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed form click handler: {os.path.basename(filepath)}")
    else:
        print(f"No match for form click: {os.path.basename(filepath)}")

# Fix process.html nav script
filepath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
content = re.sub(PROCESS_NAV_BROKEN, PROCESS_NAV_FIXED, content)
if content != orig:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed nav script: {os.path.basename(filepath)}")
else:
    print(f"No nav match in: {os.path.basename(filepath)}")
