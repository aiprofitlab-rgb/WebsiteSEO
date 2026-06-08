import os, re

# ============================================================
# Fix 1: about.html, contact.html, about-en.html, contact-en.html, process-en.html
# Missing } before } catch - in form submit try block
# Arabic: alert("حدث خطأ. الرجاء المحاولة مرة أخرى.");\n\n            } catch
# ============================================================
AR_MISSING_BRACE = """                    alert(\"حدث خطأ. الرجاء المحاولة مرة أخرى.\");

            } catch (error) {"""
AR_FIXED_BRACE = """                    alert(\"حدث خطأ. الرجاء المحاولة مرة أخرى.\");
                }

            } catch (error) {"""

for fname in ['about.html', 'contact.html', 'about-en.html', 'contact-en.html', 'process-en.html']:
    fpath = f'/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/{fname}'
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    if AR_MISSING_BRACE in content:
        content = content.replace(AR_MISSING_BRACE, AR_FIXED_BRACE)
    # Also fix the finally block missing }
    # submitBtn.disabled = false;\n\n        });  -> needs } before });
    FINALLY_BROKEN = """                submitBtn.disabled = false;

        });"""
    FINALLY_FIXED = """                submitBtn.disabled = false;
            }
        });"""
    content = content.replace(FINALLY_BROKEN, FINALLY_FIXED)
    
    if content != orig:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed AR form submit: {fname}")
    else:
        print(f"No change: {fname}")

# ============================================================
# Fix 2: index.html - / ==== comments should be // ====
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
# Replace / === with // === (only the ones that are single-slash comments)
content = re.sub(r'(?<!/)\s/ ={10,}', lambda m: m.group().replace('/ =', '// ='), content)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed / === comments in index.html")

# ============================================================
# Fix 3: process.html script #6 - missing } for escape key if block
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
PROCESS_BROKEN = """                        mobileMenu.classList.remove('active');

                });"""
PROCESS_FIXED = """                        mobileMenu.classList.remove('active');
                    }
                });"""
content = content.replace(PROCESS_BROKEN, PROCESS_FIXED)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed process.html escape key block")

# ============================================================
# Fix 4: onboarding.html - / ==== comments
# ============================================================
fpath = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/onboarding.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()
orig = content
# Find and replace all single-slash section comments
content = re.sub(r'(?<![/\w])\s*/ ={5,}', lambda m: m.group().replace('/ =', '// ='), content)
if content != orig:
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed / === comments in onboarding.html")

