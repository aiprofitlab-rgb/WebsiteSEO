import os, re

# ============================================================
# Fix 1: about.html - / === comment before detectCountry
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
content = content.replace(
    "        / ==================== COUNTRY DETECTION ====================",
    "        // ==================== COUNTRY DETECTION ===================="
)
content = content.replace(
    "        / ==================== CHAT ====================",
    "        // ==================== CHAT ===================="
)
content = content.replace(
    "        / ==================== GREETING ====================",
    "        // ==================== GREETING ===================="
)
# Generic fix for all single-slash section headers
content = re.sub(r'\n        / (={5,})', r'\n        // \1', content)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed about.html single-slash comments")

# ============================================================
# Fix 2: contact.html - different Arabic missing } before catch
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
content = content.replace(
    "                        alert('حدث خطأ. الرجاء المحاولة مرة أخرى أو استخدام نموذج حجز المكالمة.');\n\n                } catch (error) {",
    "                        alert('حدث خطأ. الرجاء المحاولة مرة أخرى أو استخدام نموذج حجز المكالمة.');\n                    }\n                }\n                } catch (error) {"
)
# Also fix single-slash comments
content = re.sub(r'\n        / (={5,})', r'\n        // \1', content)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed contact.html")

# ============================================================
# Fix 3: about-en.html, contact-en.html, process-en.html
# Missing } after alert("An error occurred...") before } catch
# ============================================================
for fname in ['about-en.html', 'contact-en.html', 'process-en.html']:
    fpath = f'/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/{fname}'
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    content = content.replace(
        '                } else {\n                    alert("An error occurred. Please try again.");\n\n            } catch (error) {',
        '                } else {\n                    alert("An error occurred. Please try again.");\n                    }\n                }\n            } catch (error) {'
    )
    # Fix single-slash comments
    content = re.sub(r'\n        / (={5,})', r'\n        // \1', content)
    if content != orig:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {fname}")
    else:
        print(f"No change: {fname}")

# ============================================================
# Fix 4: process.html - same form click handler missing braces
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
BROKEN = """                        showStep(currentStep);


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
content = content.replace(BROKEN, FIXED)
# Fix single-slash comments
content = re.sub(r'\n        / (={5,})', r'\n        // \1', content)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed process.html form click handler")

# ============================================================
# Fix 5: index.html script #10 - mobile menu link listener
# Has `}` instead of `});` for the arrow function
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
content = content.replace(
    "                    link.addEventListener('click', () => {\n                        mobileMenuDropdown.classList.remove('open');\n                    }\n                });",
    "                    link.addEventListener('click', () => {\n                        mobileMenuDropdown.classList.remove('open');\n                    });\n                });"
)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed index.html mobile menu link listener")

