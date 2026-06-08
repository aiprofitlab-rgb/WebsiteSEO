import re

def fix_file(fpath, sub_funcs):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    for func in sub_funcs:
        content = func(content)
    if content != orig:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {fpath}")

# about.html, about-en.html, process-en.html missing brace at the end
for fname in ['about.html', 'about-en.html', 'process-en.html']:
    fix_file(
        f'/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/{fname}',
        [lambda c: c.replace("            }\n        };\n\n</script>", "            }\n        };\n    });\n</script>")]
    )

# contact.html
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    [
        lambda c: c.replace(
            "                    submitBtn.textContent = originalText;\n                    submitBtn.disabled = false;\n\n            });",
            "                    submitBtn.textContent = originalText;\n                    submitBtn.disabled = false;\n                }\n            });"
        )
    ]
)

# contact-en.html
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    [
        lambda c: c.replace(
            "                        alert('Something went wrong. Please try again or use the call booking form.');\n\n                } catch (error) {",
            "                        alert('Something went wrong. Please try again or use the call booking form.');\n                    }\n                }\n                } catch (error) {"
        )
    ]
)

# process.html
fix_file(
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html',
    [
        lambda c: c.replace(
            "                        showStep(currentStep);\n\n\n        });",
            "                        showStep(currentStep);\n                    }\n                }\n            } else if (e.target.matches('.prev')) {\n                if (currentStep > 0) {\n                    currentStep--;\n                    showStep(currentStep);\n                }\n            }\n        });"
        )
    ]
)
