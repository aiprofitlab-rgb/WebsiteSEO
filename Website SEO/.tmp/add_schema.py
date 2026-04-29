import os

schema_script = """
    <!-- Local Business Schema -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "ProfessionalService",
      "name": "AI Profit Lab",
      "url": "https://aiprofitlab.io",
      "logo": "https://aiprofitlab.io/logo.webp",
      "image": "https://aiprofitlab.io/Nahid_Business_Banner.png",
      "description": "Helping non-technical managers leverage AI, automation, and technology to increase ROI and business efficiency.",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "Al Seeb",
        "addressLocality": "Muscat",
        "addressRegion": "Muscat Governorate",
        "postalCode": "000",
        "addressCountry": "OM"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 23.635950490475295, 
        "longitude": 58.207628165445385
      },
      "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+968-99245250",
        "contactType": "customer service",
        "areaServed": "GCC",
        "availableLanguage": ["en", "ar"]
      },
      "sameAs": [
        "https://www.youtube.com/@AI_for_Managers",
        "https://www.linkedin.com/in/nahid-aby"
      ]
    }
    </script>
</head>"""

target_dir = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "ProfessionalService" in content and "Al Seeb" in content:
        # Already has the schema
        return
        
    if "</head>" in content:
        content = content.replace("</head>", schema_script)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"No </head> found in {filepath}")

for root, _, files in os.walk(target_dir):
    for file in files:
        if file.endswith(".html"):
            process_file(os.path.join(root, file))

print("Schema insertion complete.")
