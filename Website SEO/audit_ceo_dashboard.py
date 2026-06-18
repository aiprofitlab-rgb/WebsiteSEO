#!/usr/bin/env python3
"""Final comprehensive audit of both CEO Dashboard pages."""

import re

def audit(path, label):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"\n{'='*58}")
    print(f"  AUDIT: {label}")
    print(f"{'='*58}")

    checks = []

    # 1. Design fidelity — all 8 nav sections present
    nav_items = ['overview', 'pl', 'products', 'inventory', 'clients', 'loyalty', 'cashflow', 'automation']
    missing = [n for n in nav_items if f"go('{n}'" not in content]
    checks.append(('All 8 nav sections', not missing, f"Missing: {missing}" if missing else "All present"))

    # 2. No broken #header hijack
    checks.append(('No id="header" on nav', 'id="header"' not in content, ''))

    # 3. dashboard-nav present
    checks.append(('dashboard-nav on nav', 'id="dashboard-nav"' in content, ''))

    # 4. sidebar-footer inside <aside>
    aside_pos = content.find('</aside>')
    footer_pos = content.find('class="sidebar-footer"')
    checks.append(('sidebar-footer inside aside', 0 < footer_pos < aside_pos, f'footer@{footer_pos}, aside@{aside_pos}'))

    # 5. SEO
    checks.append(('Canonical URL', 'rel="canonical"' in content, ''))
    checks.append(('JSON-LD Schema', 'application/ld+json' in content, ''))
    checks.append(('legalName in schema', '"legalName": "International Gulf Lotus SPC"' in content, ''))
    checks.append(('Meta title', '<title>' in content, ''))
    checks.append(('Meta description', 'name="description"' in content, ''))
    checks.append(('OG title tag', 'og:title' in content, ''))

    # 6. Logo
    checks.append(('Logo text present', 'Profit Lab' in content and 'dh-logo' in content, ''))
    checks.append(('No conflicting img logo', '<img src="/logo.webp"' not in content, ''))

    # 7. Home page links
    checks.append(('Link back to website', 'href="/en/"' in content or 'href="/"' in content, ''))

    # 8. Language switcher
    has_switcher = ('customized-ceo-dashboard-demo-ar' in content or 'customized-ceo-dashboard-demo/' in content)
    has_lang = 'عربي' in content or 'English' in content
    checks.append(('Language switcher', has_switcher and has_lang, ''))

    # 9. Responsive
    checks.append(('Hamburger button', 'id="sidebar-toggle"' in content, ''))
    checks.append(('Mobile media query', '@media (max-width: 900px)' in content, ''))
    checks.append(('Sidebar slide transform', 'translateX' in content, ''))
    checks.append(('Sidebar overlay', 'id="sidebar-overlay"' in content, ''))
    checks.append(('Mobile sidebar JS', 'sidebar-toggle' in content and 'classList.add' in content, ''))

    # 10. Legal footer
    checks.append(('Legal footer text', 'International Gulf Lotus SPC' in content, ''))
    checks.append(('dash-footer class', 'dash-footer' in content, ''))

    # 11. All 8 content sections
    sections = ['sec-overview', 'sec-pl', 'sec-products', 'sec-inventory',
                'sec-clients', 'sec-loyalty', 'sec-cashflow', 'sec-automation']
    missing_sec = [s for s in sections if s not in content]
    checks.append(('All 8 content sections', not missing_sec, f"Missing: {missing_sec}" if missing_sec else ''))

    # 12. Interactive elements intact
    checks.append(('Donut chart (canvas)', 'donutCost' in content, ''))
    checks.append(('Loyalty simulator', 'calcLoyalty' in content, ''))
    checks.append(('Bar chart animation', 'animateBars' in content, ''))
    checks.append(('Date display', 'date-display' in content, ''))
    checks.append(('Refresh button', 'refresh-btn' in content, ''))
    checks.append(('KPI grid', 'kpi-grid' in content, ''))
    checks.append(('Waterfall chart rows', 'wf-row' in content, ''))

    # Print results
    passed = 0
    failed = 0
    for name, ok, detail in checks:
        icon = 'OK' if ok else 'FAIL'
        line = f"  [{icon}] {name}"
        if detail:
            line += f"  — {detail}"
        print(line)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n  Result: {passed}/{passed+failed} passed", '-- ALL CLEAN' if failed == 0 else f'-- {failed} FAILED')
    return failed

total_failures = 0
total_failures += audit('public_html/customized-ceo-dashboard-demo.html', 'ENGLISH DASHBOARD')
total_failures += audit('public_html/customized-ceo-dashboard-demo-ar.html', 'ARABIC DASHBOARD')

print(f"\n{'='*58}")
if total_failures == 0:
    print("  ALL CHECKS PASSED -- Both files ready to deploy!")
else:
    print(f"  {total_failures} issues need attention")
print(f"{'='*58}\n")
