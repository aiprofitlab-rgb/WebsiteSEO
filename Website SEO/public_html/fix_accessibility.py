import os
import glob
import re
from bs4 import BeautifulSoup

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix 3: Color Contrast
    # Upgrading grays to lighter shades for better contrast on dark backgrounds
    content = re.sub(r'\btext-gray-500\b', 'text-gray-400', content)
    content = re.sub(r'\btext-gray-600\b', 'text-gray-400', content)
    
    # Use bs4 for structural changes
    soup = BeautifulSoup(content, 'html.parser')
    
    changed = False

    # Fix 1 & 2: Buttons and Links missing accessible names
    for tag_name in ['button', 'a']:
        for tag in soup.find_all(tag_name):
            has_aria = tag.has_attr('aria-label') or tag.has_attr('aria-labelledby')
            text_content = tag.get_text(strip=True)
            has_img_alt = False
            for img in tag.find_all('img'):
                if img.get('alt', '').strip():
                    has_img_alt = True
                    break
            
            if not has_aria and not text_content and not has_img_alt:
                # Add an aria-label based on context or a generic one
                if 'class' in tag.attrs and 'hamburger' in tag['class']:
                    tag['aria-label'] = 'Toggle Menu'
                elif 'href' in tag.attrs and 'wa.me' in tag['href']:
                    tag['aria-label'] = 'WhatsApp Contact'
                elif 'href' in tag.attrs and 'youtube.com' in tag['href']:
                    tag['aria-label'] = 'YouTube Channel'
                elif 'href' in tag.attrs and 'linkedin.com' in tag['href']:
                    tag['aria-label'] = 'LinkedIn Profile'
                elif 'href' in tag.attrs and 'facebook.com' in tag['href']:
                    tag['aria-label'] = 'Facebook Profile'
                elif 'href' in tag.attrs and 'instagram.com' in tag['href']:
                    tag['aria-label'] = 'Instagram Profile'
                else:
                    tag['aria-label'] = f"{tag_name.capitalize()} Action"
                changed = True

    # Fix 4: Heading Hierarchy
    # Headings should not skip levels.
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    expected_level = 1
    for h in headings:
        level = int(h.name[1])
        if level > expected_level:
            # Demote the heading (e.g., if we expect h2 but got h3, change to h2)
            # We must be careful not to break tailwind styles, but the user requested fix
            new_level = expected_level
            h.name = f'h{new_level}'
            changed = True
            expected_level = new_level + 1
        else:
            expected_level = level + 1

    # Fix 5: Missing <main> Landmark
    # Check if main exists
    if not soup.find('main'):
        # Find where to wrap. Usually after nav, before footer.
        navs = soup.find_all('nav')
        footers = soup.find_all('footer')
        
        start_element = navs[-1] if navs else None
        end_element = footers[0] if footers else None
        
        if start_element and end_element:
            # We want to wrap elements between nav and footer.
            # This is tricky with bs4.
            # Let's fallback to regex or string manipulation on the raw HTML for the main tag.
            pass

    # Save BS4 changes back to string
    new_html = str(soup)
    
    # Implement main tag wrapping via string manipulation if needed
    if '<main' not in new_html.lower() and '<nav' in new_html.lower() and '<footer' in new_html.lower():
        # Find the end of the last </nav> tag
        nav_end_idx = new_html.rfind('</nav>')
        if nav_end_idx != -1:
            nav_end_idx += len('</nav>')
            footer_start_idx = new_html.find('<footer')
            if footer_start_idx != -1 and footer_start_idx > nav_end_idx:
                # Wrap the content between nav and footer with <main>
                part1 = new_html[:nav_end_idx]
                part2 = new_html[nav_end_idx:footer_start_idx]
                part3 = new_html[footer_start_idx:]
                new_html = part1 + '\n<main id="main-content">\n' + part2 + '\n</main>\n' + part3
                changed = True
    
    # If there's no footer, maybe just wrap everything after nav until before script tags at the end of body
    elif '<main' not in new_html.lower() and '<nav' in new_html.lower():
         nav_end_idx = new_html.rfind('</nav>')
         if nav_end_idx != -1:
             nav_end_idx += len('</nav>')
             body_end_idx = new_html.find('</body>')
             
             # Find the first <script> before </body>
             script_idx = new_html.rfind('<script', nav_end_idx, body_end_idx)
             end_idx = script_idx if script_idx != -1 else body_end_idx
             
             if end_idx != -1 and end_idx > nav_end_idx:
                part1 = new_html[:nav_end_idx]
                part2 = new_html[nav_end_idx:end_idx]
                part3 = new_html[end_idx:]
                new_html = part1 + '\n<main id="main-content">\n' + part2 + '\n</main>\n' + part3
                changed = True

    # Check if content changed
    if content != new_html:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"Updated {filepath}")
    else:
        print(f"No changes needed for {filepath}")

if __name__ == '__main__':
    html_files = glob.glob('**/*.html', recursive=True)
    for f in html_files:
        process_file(f)
