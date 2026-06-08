import os
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    changed = False

    # Fix the broken script tag in en/index.html
    if '<!-- ======    <script>' in content:
        content = content.replace('<!-- ======    <script>', '<script>')
        changed = True

    # Fix window.onload overwriting
    if 'window.onload = async function()' in content:
        content = content.replace('window.onload = async function()', "window.addEventListener('load', async function() {")
        # We also need to add an extra '});' at the end of the function block.
        # Wait, if we replace `window.onload = ... {` with `window.addEventListener('load', ... {`,
        # then the closing `};` will be unmatched and should be `});`
        # Let's just do a targeted regex or string replacement for the end.
        content = content.replace('        };\n    </script>', '        });\n    </script>')
        content = content.replace('        };\n\n    <script>', '        });\n\n    <script>')
        changed = True

    if "window.onload=async()=>{" in content:
        content = content.replace("window.onload=async()=>{", "window.addEventListener('load', async () => {")
        content = content.replace(" } };", " } });")
        changed = True

    if "window.onload = async () => {" in content:
        content = content.replace("window.onload = async () => {", "window.addEventListener('load', async () => {")
        content = content.replace(" } };", " } });")
        changed = True

    if changed:
        # One last pass to ensure the ending }; was changed if the first one missed it.
        # This is simpler with regex.
        import re
        content = re.sub(r'window\.addEventListener\((.*?)\}(?:\s*);(?=\s*<\/script>)', r'window.addEventListener(\1});', content, flags=re.DOTALL)
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for root, _, files in os.walk('public_html'):
    for file in files:
        if file.endswith('.html'):
            fix_file(os.path.join(root, file))

