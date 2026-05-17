import os
import re

def update_seo_tags():
    root_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"
    
    # Generic energetic templates based on language
    en_desc_template = "Supercharge your business with {title}. Discover how AI Profit Lab delivers 10x ROI, eliminates bottlenecks, and drives unstoppable growth in 2026!"
    ar_desc_template = "ارتقِ بعملك مع {title}. اكتشف كيف يحقق مختبر الذكاء الاصطناعي (AI Profit Lab) عائداً استثمارياً مضاعفاً 10 مرات ويدفع عجلة النمو في عام 2026!"

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if not file.endswith(".html"):
                continue
                
            file_path = os.path.join(root, file)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).split('|')[0].strip()
            else:
                title = "AI Solutions"
                
            lang = "ar" if "/ar/" in file_path or "-ar.html" in file_path else "en"
            
            # Generate description
            desc_template = ar_desc_template if lang == "ar" else en_desc_template
            new_desc = desc_template.format(title=title)[:150]
            
            # Replace meta description
            meta_desc_pattern = r'<meta name="description" content="[^"]*">'
            new_meta_desc = f'<meta name="description" content="{new_desc}">'
            
            if re.search(meta_desc_pattern, content):
                content = re.sub(meta_desc_pattern, new_meta_desc, content)
            else:
                # Insert if not exists
                content = re.sub(r'</head>', f'    {new_meta_desc}\n</head>', content, flags=re.IGNORECASE)
            
            # Replace image alt text
            # Find all img tags
            def img_repl(match):
                img_tag = match.group(0)
                src_match = re.search(r'src="([^"]+)"', img_tag)
                if not src_match: return img_tag
                src = src_match.group(1)
                filename = os.path.basename(src).split('.')[0]
                
                # Create energetic alt text based on filename
                clean_name = filename.replace('-', ' ').replace('_', ' ').title()
                
                if lang == "en":
                    new_alt = f"{clean_name} - Empowering AI Solutions by AI Profit Lab to scale your business operations."
                else:
                    new_alt = f"{clean_name} - حلول الذكاء الاصطناعي المبتكرة من AI Profit Lab لتطوير أعمالك."
                    
                # Replace or add alt attribute
                if 'alt="' in img_tag:
                    img_tag = re.sub(r'alt="[^"]*"', f'alt="{new_alt}"', img_tag)
                else:
                    img_tag = img_tag.replace('<img ', f'<img alt="{new_alt}" ')
                return img_tag

            content = re.sub(r'<img [^>]+>', img_repl, content)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    print("Successfully updated Meta Descriptions and Image Alt Texts for all pages.")

if __name__ == "__main__":
    update_seo_tags()
