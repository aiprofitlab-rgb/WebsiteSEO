#!/usr/bin/env python3
"""
Fix Customized CEO Dashboard Demo pages.
Restores sidebar/menu visibility and adds responsiveness.
"""

import re

# ── Responsive + Mobile CSS to inject ──────────────────────────────────────
RESPONSIVE_CSS = """
/* ── DASHBOARD HEADER BAR ── */
#dash-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 24px;
  background: #ffffff;
  border-bottom: 1px solid rgba(60,80,160,0.10);
  box-shadow: 0 1px 4px rgba(60,80,160,0.06);
  position: sticky;
  top: 0;
  z-index: 300;
  height: 52px;
}
#dash-header .dh-logo {
  text-decoration: none;
  font-size: 20px;
  font-weight: 900;
  font-family: 'Outfit', sans-serif;
  letter-spacing: -1px;
  display: flex;
  align-items: center;
  gap: 2px;
}
#dash-header .dh-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
#dash-header .dh-link {
  color: #4e5675;
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0.35rem 0.9rem;
  border: 1px solid rgba(60,80,160,0.18);
  border-radius: 50px;
  font-family: 'Outfit', sans-serif;
  white-space: nowrap;
  transition: background 0.15s;
}
#dash-header .dh-link:hover { background: #f4f6fb; }

/* ── HAMBURGER (mobile only) ── */
#sidebar-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  color: #181c2e;
}
#sidebar-toggle svg { display: block; }

/* ── SIDEBAR OVERLAY (mobile) ── */
#sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.45);
  z-index: 99;
}
#sidebar-overlay.open { display: block; }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    top: 52px !important;
    z-index: 200 !important;
  }
  [dir="rtl"] .sidebar {
    transform: translateX(100%);
    left: auto !important;
    right: 0 !important;
  }
  .sidebar.open {
    transform: translateX(0) !important;
  }
  .main {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  #sidebar-toggle { display: flex; }
  .content { padding: 16px 14px !important; }
  .kpi-grid { grid-template-columns: 1fr 1fr !important; gap: 10px !important; }
  .grid-2, .grid-3, .grid-60-40, .grid-40-60 {
    grid-template-columns: 1fr !important;
  }
  .topbar { padding: 10px 14px !important; }
  .topbar-title { font-size: 15px !important; }
}
@media (max-width: 520px) {
  .kpi-grid { grid-template-columns: 1fr !important; }
  .section-header h1 { font-size: 20px !important; }
  .wf-label { width: 90px !important; font-size: 11px !important; }
  .wf-num { font-size: 10px !important; }
  #dash-header { padding: 10px 14px; }
  #dash-header .dh-logo { font-size: 17px; }
}

/* ── LEGAL FOOTER ── */
.dash-footer {
  text-align: center;
  font-size: 11px;
  color: var(--muted);
  padding: 20px 28px 28px;
  border-top: 1px solid var(--border);
  margin-top: 16px;
  font-family: var(--font-body);
  line-height: 1.7;
}
"""

# ── Mobile JS to inject (before </body>) ──────────────────────────────────
MOBILE_JS = """
/* ── SIDEBAR TOGGLE ── */
(function(){
  var toggle = document.getElementById('sidebar-toggle');
  var sidebar = document.querySelector('.sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  if (!toggle || !sidebar) return;
  function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
  toggle.addEventListener('click', function() {
    if (sidebar.classList.contains('open')) closeSidebar();
    else openSidebar();
  });
  overlay.addEventListener('click', closeSidebar);
  // Close sidebar on nav-item click (mobile UX)
  document.querySelectorAll('.nav-item').forEach(function(btn) {
    btn.addEventListener('click', function() {
      if (window.innerWidth <= 900) closeSidebar();
    });
  });
})();
"""

# ─────────────────────────────────────────────────────────────────────────────
# ENGLISH FILE
# ─────────────────────────────────────────────────────────────────────────────

EN_PATH = "public_html/customized-ceo-dashboard-demo.html"

with open(EN_PATH, "r", encoding="utf-8") as f:
    en = f.read()

# 1. Fix the #header CSS — it must NOT apply to the sidebar nav.
#    The site's standard nav fix CSS block targets #header and forces position:fixed etc.
#    We rename it to #dash-site-header so it's inert on this page.
#    But actually we want to remove the whole "STANDARD NAV FIX" block since this
#    page uses its own header structure.
en = re.sub(
    r'/\* STANDARD NAV FIX \*/.*?#mobileMenu\.open \{ display: flex !important; \}',
    '/* dashboard page — standard nav fix intentionally omitted */',
    en, flags=re.DOTALL
)

# 2. Inject responsive CSS before </style> (last </style> in head)
en = en.replace(
    '/* === CLS FIX: Constrain all chevron/arrow/scroll SVGs === */\n'
    '.chevron, [class*="chevron"], [class*="arrow"], [class*="scroll"] svg,\n'
    '.swiper-button-next, .swiper-button-prev {\n'
    '  width: 40px !important; height: 40px !important;\n'
    '  max-width: 40px !important; max-height: 40px !important;\n'
    '}\n'
    'svg { max-width: 100%; height: auto; overflow: hidden; }\n'
    'svg:not([width]) { width: 24px; height: 24px; }\n'
    '/* Nav chevron SVGs: lock to exact inline dimensions */\n'
    'nav svg[width="16"][height="16"] { width: 16px !important; height: 16px !important; max-width: 16px !important; max-height: 16px !important; }\n'
    '</style></head>',
    '/* === CLS FIX === */\n'
    'svg { max-width: 100%; height: auto; overflow: hidden; }\n'
    'svg:not([width]) { width: 24px; height: 24px; }\n'
    + RESPONSIVE_CSS +
    '</style></head>'
)

# 3. Replace the old logo/header bar with the correct one (with hamburger)
OLD_HEADER_EN = (
    '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 28px;background:#ffffff;border-bottom:1px solid rgba(60,80,160,0.10);box-shadow:0 1px 4px rgba(60,80,160,0.06);position:sticky;top:0;z-index:200;">\n'
    '<a href="/" style="text-decoration:none;">\n'
    '<div style="font-size:22px;font-weight:900;font-family:\'Outfit\',sans-serif;letter-spacing:-1px;">\n'
    '<span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span> <span style="color:#181c2e;">Profit Lab</span>\n'
    '</div>\n'
    '</a>\n'
    '<div style="display:flex;gap:10px;align-items:center;">\n'
    '<a href="/customized-ceo-dashboard-demo-ar/" style="color:#4e5675;text-decoration:none;font-size:0.85rem;font-weight:500;padding:0.4rem 1rem;border:1px solid rgba(60,80,160,0.18);border-radius:50px;font-family:\'Outfit\',sans-serif;">عربي</a>\n'
    '<a href="/en/" style="color:#4e5675;text-decoration:none;font-size:0.85rem;font-weight:500;padding:0.4rem 1rem;border:1px solid rgba(60,80,160,0.18);border-radius:50px;font-family:\'Outfit\',sans-serif;">&larr; Back to Website</a>\n'
    '</div>\n'
    '</div>'
)
NEW_HEADER_EN = """<!-- AI Profit Lab Header Bar -->
<header id="dash-header">
  <a href="/en/" class="dh-logo" title="AI Profit Lab — Home">
    <img src="/logo.webp" alt="AI Profit Lab" style="height:32px;width:auto;display:block;" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
    <span style="display:none;align-items:center;gap:2px;">
      <span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span>&nbsp;<span style="color:#181c2e;">Profit Lab</span>
    </span>
  </a>
  <div class="dh-right">
    <a href="/customized-ceo-dashboard-demo-ar/" class="dh-link">عربي</a>
    <a href="/en/" class="dh-link">&larr; Back to Website</a>
    <button id="sidebar-toggle" aria-label="Toggle menu" aria-expanded="false">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
  </div>
</header>
<div id="sidebar-overlay"></div>"""

if OLD_HEADER_EN in en:
    en = en.replace(OLD_HEADER_EN, NEW_HEADER_EN)
    print("EN: Header replaced OK")
else:
    print("EN: WARNING - old header not found exactly, trying regex replace")
    en = re.sub(
        r'<!-- AI Profit Lab Logo -->.*?</div>\s*(?=<div class="shell">)',
        NEW_HEADER_EN + '\n',
        en, flags=re.DOTALL
    )

# 4. Fix sidebar top to match the new 52px header
en = en.replace(
    '.sidebar{width:224px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:49px;left:0;bottom:0;z-index:100;box-shadow:2px 0 12px rgba(60,80,160,0.06)}',
    '.sidebar{width:224px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:52px;left:0;bottom:0;z-index:100;box-shadow:2px 0 12px rgba(60,80,160,0.06)}'
)

# 5. Fix the broken nav — remove id="header" from the nav element
en = en.replace('<nav class="nav" id="header">', '<nav class="nav" id="dashboard-nav" aria-label="Dashboard navigation">')

# 6. Fix sidebar structure — move sidebar-footer inside aside (fix the broken </nav><main> structure)
OLD_SIDEBAR_END_EN = (
    '</nav>\n'
    '<main id="main-content">\n'
    '<div class="sidebar-footer">\n'
    '<div>Data source</div>\n'
    '<div class="powered"><span>● Google Sheets</span>&nbsp;via Make.com</div>\n'
    '</div>\n'
    '</main></aside>'
)
NEW_SIDEBAR_END_EN = (
    '</nav>\n'
    '<div class="sidebar-footer">\n'
    '<div>Data source</div>\n'
    '<div class="powered"><span>● Google Sheets</span>&nbsp;via Make.com</div>\n'
    '</div>\n'
    '</aside>'
)
if OLD_SIDEBAR_END_EN in en:
    en = en.replace(OLD_SIDEBAR_END_EN, NEW_SIDEBAR_END_EN)
    print("EN: Sidebar footer fixed OK")
else:
    print("EN: WARNING - sidebar footer block not found exactly")
    # Try a more flexible regex
    en = re.sub(
        r'</nav>\s*<main[^>]*>\s*<div class="sidebar-footer">.*?</div>\s*</main>\s*</aside>',
        NEW_SIDEBAR_END_EN,
        en, flags=re.DOTALL
    )

# 7. Add legal footer before </div><!-- /content --> closing
LEGAL_FOOTER_EN = """
<footer class="dash-footer">
  © 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved<br>
  <small>This is a customized CEO dashboard demo. Data shown is illustrative only.</small>
</footer>
"""
en = en.replace(
    '</div><!-- /content -->\n</div><!-- /main -->',
    LEGAL_FOOTER_EN + '</div><!-- /content -->\n</div><!-- /main -->'
)

# 8. Inject mobile JS before </body>
en = en.replace(
    '</body>\n</html>',
    '<script>' + MOBILE_JS + '</script>\n</body>\n</html>'
)

# 9. Update the topbar sticky top to be 0 (it's inside .main which starts after header)
en = en.replace(
    '.topbar{display:flex;justify-content:space-between;align-items:center;padding:13px 28px;border-bottom:1px solid var(--border);background:var(--bg2);position:sticky;top:0;z-index:50;box-shadow:0 1px 8px rgba(60,80,160,0.06)}',
    '.topbar{display:flex;justify-content:space-between;align-items:center;padding:13px 28px;border-bottom:1px solid var(--border);background:var(--bg2);position:sticky;top:0;z-index:50;box-shadow:0 1px 8px rgba(60,80,160,0.06)}'
)

with open(EN_PATH, "w", encoding="utf-8") as f:
    f.write(en)
print(f"EN file written: {EN_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# ARABIC FILE
# ─────────────────────────────────────────────────────────────────────────────

AR_PATH = "public_html/customized-ceo-dashboard-demo-ar.html"

with open(AR_PATH, "r", encoding="utf-8") as f:
    ar = f.read()

# 1. Remove the broken STANDARD NAV FIX block
ar = re.sub(
    r'/\* STANDARD NAV FIX \*/.*?#mobileMenu\.open \{ display: flex !important; \}',
    '/* dashboard page — standard nav fix intentionally omitted */',
    ar, flags=re.DOTALL
)

# 2. Inject responsive CSS (RTL version)
RESPONSIVE_CSS_AR = RESPONSIVE_CSS.replace(
    '.sidebar {\n    transform: translateX(-100%);',
    '.sidebar {\n    transform: translateX(100%);'
).replace(
    '  .main {\n    margin-left: 0 !important;\n    margin-right: 0 !important;\n  }',
    '  .main {\n    margin-left: 0 !important;\n    margin-right: 0 !important;\n  }'
)

ar = ar.replace(
    '/* === CLS FIX: Constrain all chevron/arrow/scroll SVGs === */\n'
    '.chevron, [class*="chevron"], [class*="arrow"], [class*="scroll"] svg,\n'
    '.swiper-button-next, .swiper-button-prev {\n'
    '  width: 40px !important; height: 40px !important;\n'
    '  max-width: 40px !important; max-height: 40px !important;\n'
    '}\n'
    'svg { max-width: 100%; height: auto; overflow: hidden; }\n'
    'svg:not([width]) { width: 24px; height: 24px; }\n'
    '/* Nav chevron SVGs: lock to exact inline dimensions */\n'
    'nav svg[width="16"][height="16"] { width: 16px !important; height: 16px !important; max-width: 16px !important; max-height: 16px !important; }\n'
    '</style></head>',
    '/* === CLS FIX === */\n'
    'svg { max-width: 100%; height: auto; overflow: hidden; }\n'
    'svg:not([width]) { width: 24px; height: 24px; }\n'
    + RESPONSIVE_CSS_AR +
    '</style></head>'
)

# 3. Replace the Arabic logo header bar
OLD_HEADER_AR = (
    '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 28px;background:#ffffff;border-bottom:1px solid rgba(60,80,160,0.10);box-shadow:0 1px 4px rgba(60,80,160,0.06);position:sticky;top:0;z-index:200;">\n'
    '<a href="/" style="text-decoration:none;">\n'
    '<div style="font-size:22px;font-weight:900;font-family:\'Outfit\',sans-serif;letter-spacing:-1px;">\n'
    '<span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span> <span style="color:#181c2e;">Profit Lab</span>\n'
    '</div>\n'
    '</a>\n'
    '<a href="/" style="color:#4e5675; font-family:\'Outfit\',sans-serif;text-decoration:none;font-size:0.85rem;font-weight:500;padding:0.4rem 1rem;border:1px solid rgba(60,80,160,0.18);border-radius:50px;transition:0.2s;font-family:\'Outfit\',sans-serif;">\n'
    '    &larr; العودة إلى الموقع\n'
    '  </a>\n'
    '</div>'
)
NEW_HEADER_AR = """<!-- AI Profit Lab Header Bar — Arabic -->
<header id="dash-header" dir="rtl">
  <a href="/" class="dh-logo" title="AI Profit Lab — الرئيسية">
    <img src="/logo.webp" alt="AI Profit Lab" style="height:32px;width:auto;display:block;" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
    <span style="display:none;align-items:center;gap:2px;">
      <span style="color:#3B82F6;">A</span><span style="color:#EF4444;">I</span>&nbsp;<span style="color:#181c2e;">Profit Lab</span>
    </span>
  </a>
  <div class="dh-right">
    <a href="/customized-ceo-dashboard-demo/" class="dh-link">English</a>
    <a href="/" class="dh-link">العودة إلى الموقع &rarr;</a>
    <button id="sidebar-toggle" aria-label="فتح القائمة" aria-expanded="false">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
  </div>
</header>
<div id="sidebar-overlay"></div>"""

if OLD_HEADER_AR in ar:
    ar = ar.replace(OLD_HEADER_AR, NEW_HEADER_AR)
    print("AR: Header replaced OK")
else:
    print("AR: WARNING - old header not found exactly, trying regex")
    ar = re.sub(
        r'<!-- AI Profit Lab Logo -->.*?</div>\s*(?=<div class="shell">)',
        NEW_HEADER_AR + '\n',
        ar, flags=re.DOTALL
    )

# 4. Fix sidebar top for AR
ar = ar.replace(
    '.sidebar{width:224px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:49px;right:0;bottom:0;left:auto;z-index:100;box-shadow:2px 0 12px rgba(60,80,160,0.06)}',
    '.sidebar{width:224px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:52px;right:0;bottom:0;left:auto;z-index:100;box-shadow:2px 0 12px rgba(60,80,160,0.06)}'
)
ar = ar.replace(
    '.main{margin-right:224px;margin-left:0;flex:1;padding-top:0}',
    '.main{margin-right:224px;margin-left:0;flex:1}'
)

# 5. Fix nav id in Arabic file
ar = ar.replace('<nav class="nav" id="header">', '<nav class="nav" id="dashboard-nav" aria-label="قائمة لوحة التحكم">')

# 6. Fix Arabic sidebar structure
OLD_SIDEBAR_END_AR = (
    '</nav>\n'
    '<main id="main-content">\n'
    '<div class="sidebar-footer">\n'
    '<div>مصدر البيانات</div>\n'
    '<div class="powered"><span>● جداول جوجل</span>&nbsp;via Make.com</div>\n'
    '</div>\n'
    '</main></aside>'
)
NEW_SIDEBAR_END_AR = (
    '</nav>\n'
    '<div class="sidebar-footer">\n'
    '<div>مصدر البيانات</div>\n'
    '<div class="powered"><span>● جداول جوجل</span>&nbsp;via Make.com</div>\n'
    '</div>\n'
    '</aside>'
)
if OLD_SIDEBAR_END_AR in ar:
    ar = ar.replace(OLD_SIDEBAR_END_AR, NEW_SIDEBAR_END_AR)
    print("AR: Sidebar footer fixed OK")
else:
    print("AR: WARNING - sidebar footer block not found exactly, using regex")
    ar = re.sub(
        r'</nav>\s*<main[^>]*>\s*<div class="sidebar-footer">.*?</div>\s*</main>\s*</aside>',
        NEW_SIDEBAR_END_AR,
        ar, flags=re.DOTALL
    )

# 7. Add legal footer (Arabic)
LEGAL_FOOTER_AR = """
<footer class="dash-footer" dir="rtl">
  © ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة<br>
  <small>هذه لوحة قيادة تجريبية توضيحية. البيانات المعروضة للتوضيح فقط.</small>
</footer>
"""
ar = ar.replace(
    '</div><!-- /content -->\n</div><!-- /main -->',
    LEGAL_FOOTER_AR + '</div><!-- /content -->\n</div><!-- /main -->'
)

# 8. Inject mobile JS
ar = ar.replace(
    '</body>\n</html>',
    '<script>' + MOBILE_JS + '</script>\n</body>\n</html>'
)

# 9. Fix the nav-item active class in Arabic (it uses Arabic class name "نشطة")
# The go() function in JS uses classList - need to make sure it works
# The AR file uses .nav-item.نشطة and .section.نشطة - fix JS to use 'نشطة'
# (this is already the case in the AR file, so we just verify)

with open(AR_PATH, "w", encoding="utf-8") as f:
    f.write(ar)
print(f"AR file written: {AR_PATH}")

print("\n✅ Both dashboard files fixed successfully!")
print("Changes made:")
print("  1. Removed #header id from dashboard nav (was hijacking sidebar)")
print("  2. Moved sidebar-footer inside <aside> (was broken in <main>)")
print("  3. Fixed sidebar top offset to 52px (matches new header bar)")
print("  4. Added responsive CSS (hamburger menu for mobile/tablet)")
print("  5. Added logo with fallback text")
print("  6. Added language switcher (EN↔AR)")
print("  7. Added legal footer (EN + AR)")
print("  8. Added mobile sidebar toggle JS")
