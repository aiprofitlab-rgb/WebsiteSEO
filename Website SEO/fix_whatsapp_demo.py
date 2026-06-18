#!/usr/bin/env python3
"""
Fix WhatsApp Receptionist Demo pages.
Same root cause as CEO Dashboard: <nav id="header"> hijacked by site-wide CSS.
Fixes: layout, logo, language switcher, responsive, SEO schema, legal footer.
"""

import re

# ── Responsive CSS for WhatsApp demo ────────────────────────────────────────
RESPONSIVE_CSS = """
/* ── LANGUAGE SWITCHER BAR ── */
#wa-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  font-size: 12px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.wa-topbar-logo {
  font-weight: 900;
  font-size: 14px;
  text-decoration: none;
  letter-spacing: -0.5px;
}
.wa-topbar-links { display: flex; align-items: center; gap: 10px; }
.wa-topbar-link {
  color: #495057;
  text-decoration: none;
  padding: 3px 10px;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  transition: background 0.15s;
}
.wa-topbar-link:hover { background: #e9ecef; }

/* ── MOBILE NAV (hamburger for WA tabs) ── */
#wa-mobile-toggle {
  display: none;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  padding: 5px 9px;
  font-size: 18px;
  line-height: 1;
}
.nav-tabs-mobile-open { flex-direction: column !important; position: absolute !important;
  top: 100% !important; left: 0 !important; right: 0 !important;
  background: #075E54 !important; padding: 8px 16px 16px !important; gap: 6px !important;
  z-index: 200 !important; }

/* ── LEGAL FOOTER ── */
.wa-footer {
  text-align: center;
  font-size: 11px;
  color: #6c757d;
  padding: 14px 20px;
  border-top: 1px solid #e9ecef;
  background: #fff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.7;
}

/* ── MOBILE LEAD TOGGLE ── */
#mobile-lead-toggle {
  display: none;
  width: 100%;
  padding: 10px 16px;
  background: #f8f9fa;
  border: none;
  border-bottom: 1px solid #dee2e6;
  font-size: 13px;
  font-weight: 600;
  color: #075E54;
  cursor: pointer;
  text-align: left;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  /* Nav tabs: stack on mobile */
  .nav { position: relative; flex-wrap: wrap; height: auto !important; min-height: 52px; padding: 0 14px; }
  .nav-brand { font-size: 14px; }
  .nav-tabs { display: none; width: 100%; }
  .nav-tabs.open { display: flex; flex-direction: column; gap: 6px; padding: 8px 0 14px; width: 100%; }
  .nav-tab { width: 100%; text-align: center; border-radius: 8px; }
  #wa-mobile-toggle { display: block; }

  /* Layout: stack sidebar above chat */
  .layout { grid-template-columns: 1fr !important; grid-template-rows: auto 1fr; height: auto !important; }
  .sidebar { max-height: 220px; overflow-y: auto; display: none; }
  .sidebar.open { display: block; }
  #mobile-lead-toggle { display: block; }

  /* Full height chat on mobile */
  #tab-chat { height: calc(100vh - 52px) !important; flex-direction: column !important; }
  #tab-chat .layout { height: 100% !important; grid-template-rows: auto 1fr; }
  #tab-chat .layout > div:last-child { flex: 1; min-height: 0; }

  /* Dashboard: 2-col KPI → 1-col */
  .dash-grid { grid-template-columns: 1fr 1fr !important; gap: 10px !important; }
  .dash-row { grid-template-columns: 1fr !important; gap: 10px !important; }

  /* Messages don't overflow */
  .msg { max-width: 90% !important; }

  /* Quick replies wrap nicely */
  .quick-replies { gap: 6px; }
  .qr-btn { font-size: 12px; padding: 5px 10px; }

  /* Chat header stack */
  .chat-header { flex-wrap: wrap; gap: 8px; padding: 10px 14px; }
  .chat-header-actions { width: 100%; display: flex; gap: 6px; }
  .chat-header-actions .btn { flex: 1; text-align: center; font-size: 12px; }

  .dashboard { padding: 14px; }
  .appt-view { padding: 14px; }
  .time-slots { grid-template-columns: 1fr 1fr !important; }
}

@media (max-width: 480px) {
  .dash-grid { grid-template-columns: 1fr !important; }
  .nav-brand { font-size: 13px; gap: 6px; }
  .stat-value { font-size: 22px !important; }
}
"""

MOBILE_JS = """
/* ── WA DEMO MOBILE JS ── */
(function(){
  // Tab nav hamburger
  var toggle = document.getElementById('wa-mobile-toggle');
  var tabs = document.querySelector('.nav-tabs');
  if (toggle && tabs) {
    toggle.addEventListener('click', function() {
      tabs.classList.toggle('open');
    });
    // Close after tab click
    tabs.querySelectorAll('.nav-tab').forEach(function(t) {
      t.addEventListener('click', function() { tabs.classList.remove('open'); });
    });
  }

  // Lead sidebar mobile toggle
  var leadToggle = document.getElementById('mobile-lead-toggle');
  var sidebar = document.querySelector('.sidebar');
  if (leadToggle && sidebar) {
    leadToggle.addEventListener('click', function() {
      sidebar.classList.toggle('open');
      leadToggle.textContent = sidebar.classList.contains('open')
        ? '▲ Hide Leads' : '▼ Show Leads (6)';
    });
  }
})();
"""

def fix_file(path, lang, home_href, other_demo_href, other_lang_label, is_ar=False):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"\nProcessing: {path}")

    # 1. Remove STANDARD NAV FIX CSS block
    before = len(content)
    content = re.sub(
        r'/\* STANDARD NAV FIX \*/.*?#mobileMenu\.open \{ display: flex !important; \}',
        '/* wa-demo: standard nav fix intentionally omitted */',
        content, flags=re.DOTALL
    )
    print(f"  {'✅' if len(content) != before else '⚠️ '} STANDARD NAV FIX removed")

    # 2. Remove the large Tailwind utility / anti-black-screen CSS block
    content = re.sub(
        r'/\* === ANTI-BLACK-SCREEN.*?/\* === CLS FIX:.*?nav svg\[width="16"\]\[height="16"\].*?\}',
        '/* wa-demo: utility CSS omitted */',
        content, flags=re.DOTALL
    )

    # 3. Inject responsive CSS before </style></head>
    content = content.replace(
        '</style></head>',
        RESPONSIVE_CSS + '\n</style></head>'
    )
    print("  ✅ Responsive CSS injected")

    # 4. Fix nav id: <nav class="nav" id="header"> → <nav class="nav" id="wa-nav">
    old_nav = '<nav class="nav" id="header">'
    new_nav = '<nav class="nav" id="wa-nav">'
    if old_nav in content:
        content = content.replace(old_nav, new_nav)
        print("  ✅ nav id fixed: 'header' → 'wa-nav'")
    else:
        print("  ⚠️  nav id='header' not found")

    # 5. Add hamburger button to nav (before </nav> that closes the wa-nav)
    # Insert mobile toggle before .nav-tabs div
    content = content.replace(
        '<div class="nav-tabs">',
        '<button id="wa-mobile-toggle" aria-label="Toggle navigation">☰</button>\n<div class="nav-tabs">'
    )

    # 6. Remove the wrapping <main id="main-content"> and its close tag
    #    (it was incorrectly added by previous automation and doesn't belong here)
    content = content.replace('<main id="main-content">\n', '')
    content = content.replace('</main>\n<script defer src="/js/main.js"></script>', '<script defer src="/js/main.js"></script>')
    # Also handle if there's no newline
    content = content.replace('<main id="main-content">', '')
    content = content.replace('</main>', '', 1)  # only remove the first stray </main>

    # 7. Add topbar (AI Profit Lab logo + language switcher + back link) after <body> / fouc-overlay
    topbar_en = f"""<!-- AI Profit Lab Topbar -->
<div id="wa-topbar">
  <a href="{home_href}" class="wa-topbar-logo" title="AI Profit Lab">
    <span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span><span style="color:#181c2e;"> Profit Lab</span>
  </a>
  <div class="wa-topbar-links">
    <a href="{other_demo_href}" class="wa-topbar-link">{other_lang_label}</a>
    <a href="{home_href}" class="wa-topbar-link">{"← Back to Website" if not is_ar else "العودة إلى الموقع →"}</a>
  </div>
</div>"""

    # Insert after fouc-overlay div
    content = content.replace(
        '<div id="fouc-overlay"></div>\n',
        '<div id="fouc-overlay"></div>\n\n' + topbar_en + '\n'
    )
    print("  ✅ Topbar (logo + language switcher) added")

    # 8. Add mobile lead toggle button inside the sidebar-header area
    content = content.replace(
        '<div id="lead-list"></div>',
        '<button id="mobile-lead-toggle">▼ Show Leads (6)</button><div id="lead-list"></div>'
    )

    # 9. Fix JSON-LD schema — add legalName
    if '"legalName"' not in content:
        content = content.replace(
            '"name": "AI Profit Lab",',
            '"name": "AI Profit Lab",\n  "legalName": "International Gulf Lotus SPC",'
        )
        print("  ✅ legalName added to JSON-LD schema")

    # 10. Fix schema type to ProfessionalService for consistency
    content = content.replace(
        '"@type": "LocalBusiness"',
        '"@type": "ProfessionalService"'
    )

    # 11. Update the showLeadPanel() top offset — keep at 56px (correct for WA nav height)
    # It's already correct in the original at top:56px, but FOUC nav was making it 90px.
    # With the fix, the nav stays 56px so no change needed here.

    # 12. Add legal footer before </body>
    footer_en = """<footer class="wa-footer">
  © 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved<br>
  <small>This is an interactive demo. Data shown is illustrative only.</small>
</footer>""" if not is_ar else """<footer class="wa-footer" dir="rtl">
  © ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة<br>
  <small>هذه نسخة تجريبية تفاعلية. البيانات المعروضة للتوضيح فقط.</small>
</footer>"""

    content = content.replace('</body>\n</html>', footer_en + '\n</body>\n</html>')

    # 13. Inject mobile JS before </body>
    content = content.replace(
        footer_en + '\n</body>\n</html>',
        footer_en + '\n<script>' + MOBILE_JS + '</script>\n</body>\n</html>'
    )
    print("  ✅ Legal footer + mobile JS added")

    # 14. Fix the layout height to account for topbar (28px) + nav (56px) = ~84px total
    # The topbar is small (about 34px). Adjust layout height.
    content = content.replace(
        '.layout { display: grid; grid-template-columns: 320px 1fr; gap: 0; height: calc(100vh - 56px); }',
        '.layout { display: grid; grid-template-columns: 320px 1fr; gap: 0; height: calc(100vh - 90px); }'
    )
    # Also update showLeadPanel top offset for the extra topbar
    content = content.replace(
        "panel.style.cssText = 'position:fixed;top:56px;right:0;width:320px;height:calc(100vh - 56px);",
        "panel.style.cssText = 'position:fixed;top:90px;right:0;width:320px;height:calc(100vh - 90px);"
    )
    print("  ✅ Layout heights adjusted for topbar")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ Written: {path}")
    return content


# ── English file ─────────────────────────────────────────────────────────────
fix_file(
    path='public_html/whatsapp-receptionist-demo.html',
    lang='en',
    home_href='/en/',
    other_demo_href='/whatsapp-receptionist-demo-ar/',
    other_lang_label='عربي',
    is_ar=False
)

# ── Arabic file ───────────────────────────────────────────────────────────────
fix_file(
    path='public_html/whatsapp-receptionist-demo-ar.html',
    lang='ar',
    home_href='/',
    other_demo_href='/whatsapp-receptionist-demo/',
    other_lang_label='English',
    is_ar=True
)

# ── Audit ────────────────────────────────────────────────────────────────────
print("\n\n" + "="*60)
print("  FINAL AUDIT")
print("="*60)

for path, label in [
    ('public_html/whatsapp-receptionist-demo.html', 'ENGLISH'),
    ('public_html/whatsapp-receptionist-demo-ar.html', 'ARABIC'),
]:
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    checks = [
        ('No id="header" on nav',       'id="header"' not in c),
        ('wa-nav id present',            'id="wa-nav"' in c),
        ('STANDARD NAV FIX removed',     'STANDARD NAV FIX' not in c or 'intentionally omitted' in c),
        ('Topbar (AI Profit Lab logo)',   'wa-topbar' in c),
        ('Language switcher link',       'whatsapp-receptionist-demo' in c and ('عربي' in c or 'English' in c)),
        ('Back to website link',         'href="/en/"' in c or 'href="/"' in c),
        ('Responsive CSS',               '@media (max-width: 768px)' in c),
        ('Mobile hamburger',             'wa-mobile-toggle' in c),
        ('Mobile lead toggle',           'mobile-lead-toggle' in c),
        ('Legal footer',                 'International Gulf Lotus SPC' in c and 'wa-footer' in c),
        ('legalName in schema',          '"legalName"' in c),
        ('Canonical URL',                'rel="canonical"' in c),
        ('All 3 tab sections',           'tab-chat' in c and 'tab-dashboard' in c and 'tab-appointments' in c),
        ('Lead data intact (6 leads)',   c.count("id: '") >= 6),
        ('Chat interactivity (sendMsg)', 'sendMsg' in c),
        ('switchTab function',           'switchTab' in c),
        ('Calendar function',            'buildCalendar' in c),
        ('FOUC overlay',                 'fouc-overlay' in c),
    ]

    passed = sum(1 for _, ok in checks if ok)
    failed = [(n, ok) for n, ok in checks if not ok]

    print(f"\n  [{label}] {passed}/{len(checks)} passed")
    for name, _ in failed:
        print(f"    ❌ {name}")
    if not failed:
        print("    ✅ All checks passed!")

print("\n" + "="*60)
print("  Done! Upload both files to deploy the fix.")
print("="*60)
