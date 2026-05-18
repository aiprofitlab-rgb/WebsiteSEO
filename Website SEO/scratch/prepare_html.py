import re
import os

with open('../USER_REQUEST.txt', 'r') as f:
    content = f.read()

# Extract the HTML part
html_start = content.find('<!DOCTYPE html>')
html_content = content[html_start:]

# 1. Add SEO Meta Tags, Google Tag Manager, LocalBusiness schema
seo_tags = """<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="https://aiprofitlab.io/medflow-sales-automation-demo.html" />

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-2GPVY4Z5KR"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-2GPVY4Z5KR');
</script>

<title>MedFlow Sales & Invoice Automation Demo | AI Profit Lab</title>
<meta name="description" content="Experience MedFlow Sales & Invoice Automation. Discover how AI Profit Lab delivers 10x ROI for medical businesses in Oman and the GCC.">
<meta name="keywords" content="medical sales automation, invoice automation, MedFlow, AI Profit Lab, Oman business automation, GCC">
<meta name="author" content="AI Profit Lab">
<meta name="robots" content="index, follow">

<!-- Open Graph / Social Media -->
<meta property="og:title" content="MedFlow Sales & Invoice Automation Demo | AI Profit Lab">
<meta property="og:description" content="Watch how orders turn into invoices automatically without manual work.">
<meta property="og:url" content="https://aiprofitlab.io/medflow-sales-automation-demo.html">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="MedFlow Sales & Invoice Automation Demo | AI Profit Lab">
<meta name="twitter:description" content="Automate medical sales and invoice processing.">

<!-- LocalBusiness Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "AI Profit Lab",
  "image": "https://aiprofitlab.io/og-image.jpg",
  "url": "https://aiprofitlab.io",
  "telephone": "+96899245250", 
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Muscat",
    "addressRegion": "Muscat Governorate",
    "addressCountry": "OM"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 23.5880,
    "longitude": 58.3829
  },
  "description": "AI Profit Lab specializes in AI automation solutions for businesses in Oman, Qatar, UAE and the GCC. We provide smart medical sales automation and workflow automation.",
  "priceRange": "$$"
}
</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
"""

html_content = html_content.replace("""<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedFlow — Sales & Invoice Automation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">""", seo_tags)

# 2. Replace Logo
old_logo = """<a class="logo" href="#">
    <div class="logo-mark">
      <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 110 20A10 10 0 0112 2zm0 4a1 1 0 00-1 1v4H7a1 1 0 000 2h4v4a1 1 0 002 0v-4h4a1 1 0 000-2h-4V7a1 1 0 00-1-1z"/></svg>
    </div>
    <span class="logo-type">Med<em>Flow</em></span>
  </a>"""

new_logo = """<a href="/en/" class="logo" style="text-decoration:none;">
    <span style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 24px; letter-spacing: -0.05em; color: #0c0f0e;">
        <span style="color: #3B82F6;">A</span><span style="color: #EF4444;">I</span> <span style="font-size: 18px;">Profit Lab</span>
    </span>
  </a>"""

html_content = html_content.replace(old_logo, new_logo)

# Also update the footer logo to maintain some consistency or at least mention AI Profit Lab
old_footer = """<span class="f-logo">Med<em style="font-style:italic;color:var(--text3);">Flow</em></span>"""
new_footer = """<span class="f-logo" style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 20px; letter-spacing: -0.05em; color: #0c0f0e;"><span style="color: #3B82F6;">A</span><span style="color: #EF4444;">I</span> <span style="font-size: 16px;">Profit Lab</span></span>"""
html_content = html_content.replace(old_footer, new_footer)

old_copyright = """© 2026 MedFlow · Sales & Invoice Automation for Medical Teams · Muscat, Oman"""
new_copyright = """© 2026 AI Profit Lab · Sales & Invoice Automation for Medical Teams · Muscat, Oman"""
html_content = html_content.replace(old_copyright, new_copyright)

with open('../public_html/medflow-sales-automation-demo.html', 'w') as f:
    f.write(html_content)

print("HTML file created successfully.")
