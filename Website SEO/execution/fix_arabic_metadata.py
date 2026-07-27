import os
import re
import glob

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    
    # 1. Fix the broken viewport tag
    content = content.replace(
        '<meta name="description" content="width=device-width, initial-scale=1.0" name="viewport">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    )
    
    # 2. Remove the broken left-over content tags (usually ending in ..."> and near the title or end of head)
    # The broken description looks like: <meta content="وفر وقتك وز...">
    content = re.sub(r'<meta content="[^"]*\.\.\.">', '', content)
    
    # Also clean up any empty lines left behind by the removal
    content = re.sub(r'\n\s*\n\s*</head>', '\n</head>', content)
    
    # 3. Check if a proper meta description exists
    if not re.search(r'<meta\s+name=["\']description["\']', content, re.IGNORECASE):
        # Extract title to use as base for description
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        base_title = "حلول الذكاء الاصطناعي"
        if title_match:
            title_text = title_match.group(1).split('|')[0].strip()
            if title_text:
                base_title = title_text
                
        # Generate new description
        new_desc = f"{base_title} - أتمتة الذكاء الاصطناعي في عمان. اكتشف كيف يمكننا مساعدة عملك في مسقط ودعم رؤية عمان 2040."
        if len(new_desc) > 155:
            new_desc = new_desc[:152].strip() + "..."
            
        new_meta = f'<meta name="description" content="{new_desc}">'
        
        # Insert before </head>
        content = content.replace("</head>", f"  {new_meta}\n</head>")
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    base_dir = "./public_html"
    files = glob.glob(f"{base_dir}/**/*.html", recursive=True)
    
    count = 0
    for filepath in files:
        if fix_file(filepath):
            # print(f"Fixed: {filepath}")
            count += 1
            
    print(f"Total files fixed: {count}")

if __name__ == "__main__":
    main()
