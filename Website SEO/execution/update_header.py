import os

def update_header_css(directory):
    # Mapping current updated values to even glassier ones
    replacements = {
        'background: rgba(15, 15, 15, 0.6) !important;': 'background: rgba(255, 255, 255, 0.05) !important;',
        'background: rgba(15, 15, 15, 0.7) !important;': 'background: rgba(255, 255, 255, 0.05) !important;',
        'background: rgba(20, 20, 20, 0.85) !important;': 'background: rgba(255, 255, 255, 0.08) !important;',
        'backdrop-filter: blur(25px) !important;': 'backdrop-filter: blur(30px) saturate(150%) !important;',
        'border-bottom: 1px solid rgba(255,255,255,0.05) !important;': 'border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;'
    }
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                for target, replacement in replacements.items():
                    content = content.replace(target, replacement)
                
                if content != original_content:
                    print(f"Updating {path}")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)

if __name__ == "__main__":
    update_header_css('/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/')
