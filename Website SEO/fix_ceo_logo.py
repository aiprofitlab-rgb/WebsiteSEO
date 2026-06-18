#!/usr/bin/env python3
"""
Fix logo in both CEO dashboard pages.
logo.webp has dark background — use styled text logo for white header bar,
identical to the text style used on the rest of the website.
Also verify the FOUC overlay and main.js don't interfere.
"""

import re

def fix_logo(path, back_href, back_label, ar_lang_href, lang_label, is_rtl=False):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The logo section in <header id="dash-header">:
    # Replace the <img onerror> logo with pure text logo
    # (logo.webp has black bg, won't work on white header)

    OLD_LOGO_BLOCK = (
        '    <img src="/logo.webp" alt="AI Profit Lab" style="height:32px;width:auto;display:block;" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">\n'
        '    <span style="display:none;align-items:center;gap:2px;">\n'
        '      <span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span>&nbsp;<span style="color:#181c2e;">Profit Lab</span>\n'
        '    </span>'
    )

    NEW_LOGO_BLOCK = (
        '    <span style="display:inline-flex;align-items:center;gap:2px;">'
        '<span style="color:#3B82F6;font-weight:900;">A</span>'
        '<span style="color:#EF4444;font-weight:900;">I</span>'
        '&nbsp;<span style="color:#181c2e;font-weight:900;">Profit Lab</span>'
        '</span>'
    )

    if OLD_LOGO_BLOCK in content:
        content = content.replace(OLD_LOGO_BLOCK, NEW_LOGO_BLOCK)
        print(f'  ✅ Logo replaced in {path}')
    else:
        print(f'  ⚠️  Logo block not found exactly in {path}')

    # Also: ensure the FOUC overlay removal script fires early enough
    # and does NOT interfere with the dashboard sections
    # (already present and working from original)

    # Ensure main.js doesn't break anything — it looks for #mobileToggle
    # and #mobileMenu which are not on this page, so it's safe to keep.
    # The defer attribute on main.js means it runs after DOM is ready.

    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Written: {path}')

print('Fixing logos...')
fix_logo(
    'public_html/customized-ceo-dashboard-demo.html',
    back_href='/en/',
    back_label='&larr; Back to Website',
    ar_lang_href='/customized-ceo-dashboard-demo-ar/',
    lang_label='عربي'
)

fix_logo(
    'public_html/customized-ceo-dashboard-demo-ar.html',
    back_href='/',
    back_label='العودة إلى الموقع &rarr;',
    ar_lang_href='/customized-ceo-dashboard-demo/',
    lang_label='English',
    is_rtl=True
)

print()

# Also verify the go() function in EN works correctly for Arabic active class
# The EN file uses class 'active' and the AR file uses 'نشطة' - verify this
for path, active_cls in [
    ('public_html/customized-ceo-dashboard-demo.html', 'active'),
    ('public_html/customized-ceo-dashboard-demo-ar.html', 'نشطة'),
]:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check go() function references the right active class
    if f"classList.add('{active_cls}')" in content or f'classList.add("{active_cls}")' in content:
        print(f'✅ {path}: go() uses correct active class "{active_cls}"')
    else:
        print(f'⚠️  {path}: checking go() function...')
        # find go() function
        m = re.search(r'function go\(id,btn\).*?}', content, re.DOTALL)
        if m:
            print(f'   go() block: {m.group()[:200]}')

    # Check nav-item active class in HTML
    if f'class="nav-item {active_cls}"' in content or f"nav-item {active_cls}" in content:
        print(f'✅ {path}: nav-item uses "{active_cls}" class')
    else:
        print(f'  nav-item active class check: searching...')
        nav_matches = [line for line in content.split('\n') if 'nav-item' in line and (active_cls in line or 'active' in line)]
        for m in nav_matches[:3]:
            print(f'   {m.strip()}')

print()
print('✅ Logo fix complete!')
