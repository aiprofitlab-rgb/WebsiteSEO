import os, glob, re, subprocess

def get_scripts_with_positions(content):
    """Returns list of (script_tag, script_content, start_pos, end_pos)"""
    results = []
    for m in re.finditer(r'(<script\b[^>]*>)([\s\S]*?)(</script>)', content, re.IGNORECASE):
        results.append({
            'tag': m.group(1),
            'content': m.group(2),
            'full': m.group(0),
            'start': m.start(),
            'end': m.end()
        })
    return results

def fix_youtube_facade(script):
    """Fix missing closing brace for if(facade) in YouTube facade script"""
    pattern = r"""(document\.addEventListener\('DOMContentLoaded',\s*\(\)\s*=>\s*\{[\s\S]*?facade\.addEventListener\('click',[\s\S]*?\}\);\s*)\n\s*\}\);"""
    if re.search(pattern, script):
        return script  # already fixed
    # The pattern where if(facade){ ... }); is missing the } before });
    script = re.sub(
        r"(facade\.addEventListener\('click',[\s\S]*?\}\);\s*)\n(\s*\}\);)",
        r"\1\n            }\n\2",
        script
    )
    return script

def fix_mobile_menu(script):
    """Fix missing closing braces in mobile menu toggle script"""
    # Fix: mobileMenuDropdown.classList.remove('open');\n\n                });\n\n        });
    # Should be: .remove('open');\n                    }\n                });\n            }\n        });
    fixed = re.sub(
        r"(mobileMenuDropdown\.classList\.remove\('open'\);)\s*\n(\s*\}\);\s*\n\s*\}\);)",
        r"\1\n                    }\n                });\n            }\n        });",
        script
    )
    return fixed

def fix_standard_nav(script):
    """Standard nav should be fine - check and return"""
    return script

def check_script_syntax(code, is_async=False):
    tmpfile = '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/tmp_fix.js'
    if is_async:
        code = f'(async () => {{\n{code}\n}})();'
    with open(tmpfile, 'w', encoding='utf-8') as f:
        f.write(code)
    res = subprocess.run(['node', '-c', tmpfile], capture_output=True, text=True)
    return res.returncode == 0

# Files and their broken script indices (0-based)
files_to_fix = [
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/index.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/about-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/contact-en.html',
    '/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/process-en.html',
]

# The common broken scripts that appear in all pages are:
# - YouTube facade (missing `}` to close `if(facade)`)
# - Mobile menu (missing `}` after classList.remove('open') inside click handler)

youtube_broken = """        // YouTube Facade Logic for Speed
        document.addEventListener('DOMContentLoaded', () => {
            const facade = document.querySelector('.youtube-facade');
            if(facade) {
                facade.addEventListener('click', function() {
                    const videoId = this.getAttribute('data-videoid');
                    const iframe = document.createElement('iframe');
                    iframe.setAttribute('src', `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&modestbranding=1&autoplay=1`);
                    iframe.setAttribute('frameborder', '0');
                    iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
                    iframe.setAttribute('allowfullscreen', 'true');
                    iframe.className = 'w-full h-full absolute inset-0';
                    this.innerHTML = '';
                    this.appendChild(iframe);
                });

        });"""

youtube_fixed = """        // YouTube Facade Logic for Speed
        document.addEventListener('DOMContentLoaded', () => {
            const facade = document.querySelector('.youtube-facade');
            if(facade) {
                facade.addEventListener('click', function() {
                    const videoId = this.getAttribute('data-videoid');
                    const iframe = document.createElement('iframe');
                    iframe.setAttribute('src', `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&modestbranding=1&autoplay=1`);
                    iframe.setAttribute('frameborder', '0');
                    iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
                    iframe.setAttribute('allowfullscreen', 'true');
                    iframe.className = 'w-full h-full absolute inset-0';
                    this.innerHTML = '';
                    this.appendChild(iframe);
                });
            }
        });"""

# Mobile menu (unified system) broken - missing closing braces
mobile_broken_pattern = r"(mobileMenuDropdown\.classList\.remove\('open'\);)\s*\n\s*\}\);\s*\n\s*\}\);"
mobile_fixed_replace = r"""\1
                    }
                });
            }
        });"""

# STANDARD NAV JS - also has broken pattern in some files
nav_broken_pattern = r"(m\.classList\.remove\('open'\);\s*\n\s*\}\);\s*\n\s*\}\);\s*\n\s*\}\)\(\);\s*)"

for filepath in files_to_fix:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    orig = content
    
    # Fix YouTube facade
    if youtube_broken in content:
        content = content.replace(youtube_broken, youtube_fixed)
        print(f"Fixed YouTube facade in {os.path.basename(filepath)}")
    
    # Fix mobile menu toggle
    content = re.sub(mobile_broken_pattern, mobile_fixed_replace, content)
    
    if content != orig:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed mobile menu in {os.path.basename(filepath)}")

print("Done with YouTube/mobile fixes")
