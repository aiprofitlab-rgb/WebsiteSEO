import os
import re
import glob
import json

def update_title(content):
    match = re.search(r'<title>(.*?)</title>', content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return content
    
    current_title = match.group(1).strip()
    
    # Extract core title: remove existing suffix if any
    core_title = current_title.split('|')[0].strip()
    
    # We might have added " | AI Profit Lab عمان" already in the first pass
    
    suffix = " | AI Profit Lab عمان"
    
    if len(core_title) + len(suffix) > 60:
        core_title = core_title[:60 - len(suffix) - 3].strip() + "..."
        
    new_title = core_title + suffix
    
    return re.sub(r'<title>.*?</title>', f'<title>{new_title}</title>', content, flags=re.IGNORECASE | re.DOTALL)

def update_description(content):
    # Find existing description tag regardless of attribute order
    desc_regex = re.compile(
        r'<meta\s+(?:name=["\']description["\']\s+content=["\'](.*?)["\']|content=["\'](.*?)["\']\s+name=["\']description["\'])\s*/?>',
        re.IGNORECASE | re.DOTALL
    )
    
    matches = list(desc_regex.finditer(content))
    base_desc = ""
    
    # In case there are multiple, get the first non-empty
    for match in matches:
        extracted = match.group(1) or match.group(2)
        if extracted and not extracted.startswith(" - "):
            base_desc = extracted.strip()
            break
            
    if not base_desc:
        # If still empty, maybe we couldn't extract a valid one from multiple passes
        base_desc = "حلول أتمتة الذكاء الاصطناعي للمؤسسات"
    
    keywords = ["أتمتة الذكاء الاصطناعي في عمان", "مسقط", "عمان 2040"]
    has_keyword = any(kw in base_desc for kw in keywords)
    
    if not has_keyword:
        base_desc += " - أتمتة الذكاء الاصطناعي في عمان."
        
    if len(base_desc) < 130:
        base_desc += " اكتشف كيف يمكننا مساعدة عملك في مسقط ودعم رؤية عمان 2040."
        
    if len(base_desc) > 155:
        base_desc = base_desc[:152].strip() + "..."
        
    new_meta = f'<meta name="description" content="{base_desc}">'
    
    # Remove all existing description meta tags
    content = desc_regex.sub('', content)
    
    # Ensure there are no leftover empty lines from removal (optional, but good for cleanliness)
    
    # Insert new meta tag before </head>
    return content.replace("</head>", f"  {new_meta}\n</head>")

def inject_schema(content):
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": "AI Profit Lab",
        "legalName": "Lotus Gulf International",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Muscat",
            "addressCountry": "OM"
        },
        "areaServed": ["Oman", "GCC"]
    }
    
    schema_str = f'<script type="application/ld+json">\n{json.dumps(schema, indent=2, ensure_ascii=False)}\n</script>'
    
    if '"ProfessionalService"' in content or '"Lotus Gulf International"' in content:
        # Schema might already exist, don't inject again
        return content
        
    return content.replace("</head>", f"{schema_str}\n</head>")

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
    content = update_title(content)
    content = update_description(content)
    content = inject_schema(content)
    
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
        if "/ar/" in filepath or "-ar" in filepath or "ar.html" in filepath:
            if process_file(filepath):
                print(f"Updated: {filepath}")
                count += 1
                
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    main()
