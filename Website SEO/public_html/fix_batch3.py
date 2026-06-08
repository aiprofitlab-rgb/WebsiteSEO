import os, re

def fix_file(fpath, broken, fixed):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    content = content.replace(broken, fixed)
    if content != orig:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {os.path.basename(fpath)}")

# contact.html
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    "                        alert('حدث خطأ. الرجاء المحاولة مرة أخرى أو استخدام نموذج حجز المكالمة.');\n                    }\n                }\n                } catch (error) {",
    "                        alert('حدث خطأ. الرجاء المحاولة مرة أخرى أو استخدام نموذج حجز المكالمة.');\n                    }\n                } catch (error) {"
)

# about-en.html, contact-en.html, process-en.html
for fname in ['about-en.html', 'contact-en.html', 'process-en.html']:
    fix_file(
        f'/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/{fname}',
        '                } else {\n                    alert("An error occurred. Please try again.");\n                    }\n                }\n            } catch (error) {',
        '                } else {\n                    alert("An error occurred. Please try again.");\n                }\n            } catch (error) {'
    )

# index.html script 10
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html',
    "                    link.addEventListener('click', () => {\n                        mobileMenuDropdown.classList.remove('open');\n                    });\n                });\n            }\n        });\n                \n                // Close if user clicks outside\n                document.addEventListener('click', function(event) {\n                    if (!mobileToggleBtn.contains(event.target) && !mobileMenuDropdown.contains(event.target)) {\n                        mobileMenuDropdown.classList.remove('open');\n                    }\n                });\n            }\n        });",
    "                    link.addEventListener('click', () => {\n                        mobileMenuDropdown.classList.remove('open');\n                    });\n                });\n                \n                // Close if user clicks outside\n                document.addEventListener('click', function(event) {\n                    if (!mobileToggleBtn.contains(event.target) && !mobileMenuDropdown.contains(event.target)) {\n                        mobileMenuDropdown.classList.remove('open');\n                    }\n                });\n            }\n        });"
)

# process.html form click handler
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html',
    "        form.addEventListener('click', (e) => {\n            if (e.target.matches('.next')) {\n                if (validateStep(currentStep)) {\n                    if (currentStep < steps.length - 1) {\n                        currentStep++;\n                        showStep(currentStep);\n                    }\n                }\n            } else if (e.target.matches('.prev')) {\n                if (currentStep > 0) {\n                    currentStep--;\n                    showStep(currentStep);\n                }\n            }\n        });\n\n\n        });",
    "        form.addEventListener('click', (e) => {\n            if (e.target.matches('.next')) {\n                if (validateStep(currentStep)) {\n                    if (currentStep < steps.length - 1) {\n                        currentStep++;\n                        showStep(currentStep);\n                    }\n                }\n            } else if (e.target.matches('.prev')) {\n                if (currentStep > 0) {\n                    currentStep--;\n                    showStep(currentStep);\n                }\n            }\n        });"
)

# about.html
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    "            }\n        };\n\n})();",
    "        };\n"
)
