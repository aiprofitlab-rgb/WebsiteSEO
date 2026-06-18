---
name: article-creator
description: Automatically writes dual-language (English and Arabic) SEO articles for the AI Profit Lab blog when given a keyword. Generates an image and applies the website's dark-mode glassmorphism HTML structure. Triggers when the user asks to "write an article about [keyword]" or "generate blog post for [keyword]".
---

# AI Profit Lab Article Creator

This skill automates the end-to-end creation of high-quality, story-driven, fully formatted SEO articles for the AI Profit Lab website.

When the user asks you to write an article for a given keyword/topic, follow these steps exactly:

## Step 1: Research and Outline
- **Transform H2 Headers into Questions**: Transform all `<h2>` headers into specific business questions.
- **Direct Answers**: Write a concise, 40-word direct answer immediately below each `<h2>`.
- **Factual Density**: Eliminate adjectives (e.g., "amazing", "incredible") and replace with hard data (e.g., "30% increase"). AI prioritizes data over fluff. When discussing boosting ROI, back it up.
- **Data Tables**: Add HTML Data Tables within the content showing ROI, time savings, or tool comparisons or .
- **High-Authority Links**: Link out to high-authority tech docs (e.g., OpenAI docs, Omani Gov Tech portals, strong news) whenever it is related.
- **Internal Links**: Each article should be linked to other website pages only if it seems natural, not deliberately forced. Ensure all internal links point to the clean URL version.
- The article must be a rich, highly SEO-friendly article between 800 to 1000 words long.
- **External Links & References**: Each article MUST have links to outside source(s) in the text, and you must mention all those references at the end in the References section, linking them to the source. Verify that references exist and are not broken.
- Generate an extensive FAQ section at the end containing AT LEAST 10 Frequently Asked Questions. These should be questions that people in Oman and the GCC actually ask about the subject from LLMs.
- Designate a hero image concept that matches the futuristic, semi-realistic AI vibe of the other articles. Add Alt Text for all images describing its value to the brand (e.g., "[Image Name] - Empowering AI Solutions by AI Profit Lab to scale your business operations." for English, and "[Image Name] - حلول الذكاء الاصطناعي المبتكرة من AI Profit Lab لتطوير أعمالك." for Arabic).
- **SEO & GEO Friendliness**: Every article must be optimized for search engines and localized for the **Oman/GCC market**. Generate energetic, unique Meta Descriptions (under 150 chars) starting with "Supercharge your business with [Title]" for English, and "ارتقِ بعملك مع [Title]" for Arabic. Include local keywords (e.g., "Muscat", "Oman Vision 2040", "GCC Business Automation") and ensure all meta tags, structured data, and content reflect this regional focus.
- **Forum Snippet**: Generate a short promotional snippet (or pitch) for a local GCC business forum at the end of the generation process, related to the article topic.

## Step 2: Generate the English Version
Draft the English article content. Then wrap it in the exact HTML structure expected for the blog. Ensure it follows the dark-mode glassmorphism style.
Ensure you strictly populate the embedded JSON-LD Schema Markup in the `<head>` with the article's specific `Article` data, the 10+ `FAQPage` data, and the `Organization` details, as AI search engines prioritize highly structured schema paths.
In the navbar, ensure the logo is identical to the one on the blog page. For the English version, the logo is linked to the English home page (`/en/`), and the "Back to Hub" button in the header is linked to the English blog (`/blog/`).
Save it to: `public_html/blog/en/YYYY-MM-DD-[slug-title].html` (use the current date).

## Step 3: Generate the Arabic Version
Translate and adapt the article into Arabic. Make sure the tone remains professional and culturally relevant for the GCC/Oman market.
Set `lang="ar"` and `dir="rtl"`.
In the navbar, change "Back to Hub" to "العودة إلى المدونة" and link to the Arabic blog (`/blog-ar/`). Also, ensure the logo in the Arabic version is identical to the English one but retains `dir="ltr"` to display correctly, and links to the Arabic home page (`/`).
Save it to: `public_html/blog/ar/YYYY-MM-DD-[slug-title-in-english].html`.

## Step 4: Generate the Image
Use your `generate_image` tool to create the hero image based on the designated concept.
Save the generated image to: `public_html/blog/images/[image_name].png`. Make sure both HTML files point to this exact absolute path (`/blog/images/[image_name].png`).

## Step 5: Update the Blog Hub
After generating and saving the images and HTML files, use your `run_command` tool to execute the python script that automatically updates the hub pages with the new content:
`python3 update_blog_hubs.py` (run this from the `Website SEO` directory or use `python3 "Website SEO/update_blog_hubs.py"` relative to your current workspace root).

## Step 6: Regenerate the Sitemap
After the blog hub is updated, **always** regenerate the `sitemap.xml` by running the following inline Python script from the `public_html` directory. This ensures all new English and Arabic article pages are properly indexed by search engines with accurate `lastmod` dates.

```bash
python3 -c "
import os, datetime

base_dir = '.'
base_url = 'https://aiprofitlab.io'
priority_map = {
    'index.html_root': '1.0',
    'root': '0.8',
    'blog_hub': '0.8',
    'blog_article': '0.6',
    'academy': '0.6',
    'other': '0.7',
}

urls = []
for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in ['.git', 'assets', 'js', 'images']]
    for file in files:
        if not file.endswith('.html') or file in ['test.html']:
            continue
        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, base_dir).replace(os.sep, '/')
        mtime = os.path.getmtime(file_path)
        lastmod = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

        if file == 'index.html':
            dir_part = os.path.dirname(rel_path)
            url = base_url + '/' + (dir_part + '/' if dir_part and dir_part != '.' else '')
            priority = '1.0' if dir_part in ['', '.'] else '0.8'
        else:
            slug = rel_path[:-5]  # strip .html
            url = base_url + '/' + slug + '/'
            if '/blog/en/' in url or '/blog/ar/' in url:
                priority = '0.6'
            elif '/blog' in url or '/academy' in url:
                priority = '0.8'
            else:
                priority = '0.7'

        url = url.replace('//', '/').replace('https:/', 'https://')
        urls.append({'loc': url, 'lastmod': lastmod, 'changefreq': 'weekly', 'priority': priority})

urls.sort(key=lambda x: x['loc'])
xml = '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\" xmlns:xhtml=\"http://www.w3.org/1999/xhtml\">\n'
for u in urls:
    xml += f'  <url>\n    <loc>{u[\"loc\"]}</loc>\n    <lastmod>{u[\"lastmod\"]}</lastmod>\n    <changefreq>{u[\"changefreq\"]}</changefreq>\n    <priority>{u[\"priority\"]}</priority>\n  </url>\n'
xml += '</urlset>'
with open('sitemap.xml', 'w', encoding='utf-8') as f:
    f.write(xml)
print(f'sitemap.xml updated — {len(urls)} URLs indexed.')
"
```

Run this from the `public_html` directory:
```bash
cd "Website SEO/public_html" && python3 -c "[above script]"
```
Or use the equivalent `run_command` invocation. After running, confirm the output shows the updated URL count.

---

## HTML Template Requirements
Whenever you generate the files, use the following HTML template. Do NOT deviate from this structure, as it maintains the site's dark-mode glassmorphism design:

```html
<!DOCTYPE html>
<html lang="en" dir="ltr"> <!-- Change to ar and rtl for Arabic -->
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-2GPVY4Z5KR"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'G-2GPVY4Z5KR');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="category" content="[Category]">
    <title>[SEO Title] | AI Profit Lab</title>
    <meta name="description" content="[Energetic, unique SEO Description starting with 'Supercharge your business with [Title]...' (max 150 chars)]"> <!-- Note: For Arabic use 'ارتقِ بعملك مع [Title]...' -->
    <meta name="keywords" content="[SEO Keywords]">
    <link rel="canonical" href="https://aiprofitlab.io/blog/en/YYYY-MM-DD-[slug-title]/"> <!-- Note: Update path for Arabic: /blog/ar/... -->
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="apple-touch-icon" href="/favicon.svg">
    
    <!-- JSON-LD Schema Markup -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Organization",
          "@id": "https://aiprofitlab.io/#organization",
          "name": "AI Profit Lab",
          "url": "https://aiprofitlab.io/",
          "logo": {
            "@type": "ImageObject",
            "url": "https://aiprofitlab.io/favicon.svg"
          }
        },
        {
          "@type": "Article",
          "headline": "[SEO Title]",
          "description": "[SEO Description]",
          "image": "https://aiprofitlab.io/blog/images/[image_name].png",
          "author": {
            "@type": "Organization",
            "name": "AI Profit Lab"
          },
          "publisher": {
            "@id": "https://aiprofitlab.io/#organization"
          },
          "datePublished": "YYYY-MM-DD"
        },
        {
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "[Question 1]",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "[Answer 1]"
              }
            }
            // Generate for ALL 10+ FAQs sequentially
          ]
        }
      ]
    }
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Outfit', sans-serif; background-color: #050505; color: #ffffff; }
        .logo-font { font-family: 'Outfit', sans-serif !important; }
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .glass-card { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }
        .glass-card:hover { border-color: #3B82F6; transform: translateY(-5px); box-shadow: 0 20px 40px rgba(59, 130, 246, 0.1); }
        .prose h2 { color: #60A5FA; margin-top: 2.5em; margin-bottom: 1em; font-weight: 800; font-size: 1.875rem; }
        .prose h3 { color: #93C5FD; margin-top: 2em; margin-bottom: 1em; font-weight: 700; font-size: 1.5rem; }
        .prose p { margin-bottom: 1.5em; line-height: 1.8; color: #D1D5DB; }
        .prose strong { color: #F3F4F6; }
        .prose blockquote { border-left: 4px solid #3B82F6; padding-left: 1rem; font-style: italic; color: #9CA3AF; margin-left: 0; }
    </style>
    <!-- Local Business Schema -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "ProfessionalService",
      "name": "AI Profit Lab",
      "legalName": "International Gulf Lotus SPC",
      "url": "https://aiprofitlab.io",
      "logo": "https://aiprofitlab.io/logo.webp",
      "image": "https://aiprofitlab.io/nahid-business-banner.png",
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
</head>
<body class="antialiased">
    <!-- Navigation -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 w-full z-50 glass sticky top-0 bg-black/30" id="header">
        <a href="/en/" class="font-extrabold text-3xl md:text-4xl tracking-tighter hover:opacity-80 transition logo-font">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        <a href="/blog/" class="text-gray-300 hover:text-white font-semibold transition">Back to Hub</a>
    </nav> <!-- Note: For ARABIC, update Logo link to "/" with dir="ltr", and "Back to Hub" to "العودة إلى المدونة" linking to "/blog-ar/". -->

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-6 py-16">
        <article>
            <div class="mb-12 text-center text-right-ar"> <!-- Use appropriate text-align for rtl reading -->
                <span class="bg-blue-500/10 text-blue-400 text-sm font-bold px-4 py-2 rounded-full border border-blue-500/20 mb-6 inline-block">[Category]</span>
                <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">[Article Title]</h1>
                <p class="text-xl text-gray-400 max-w-2xl mx-auto">[Subtitle / Hook]</p>
            </div>

            <img src="/blog/images/[image_name].png" alt="[Image Name] - Empowering AI Solutions by AI Profit Lab to scale your business operations." class="w-full rounded-3xl mb-16 shadow-[0_0_50px_rgba(59,130,246,0.15)] border border-white/5 object-cover h-[500px]"> <!-- Note: For Arabic Alt use '[Image Name] - حلول الذكاء الاصطناعي المبتكرة من AI Profit Lab لتطوير أعمالك.' -->

            <div class="prose max-w-none">
                [PARAGRAPHS, HEADINGS, BLOCKQUOTES. MUST BE 800 TO 1000 WORDS TOTAL, USING STORYTELLING NARRATIVE]
            </div>

            <!-- FAQ Section ( MUST CONTAIN AT LEAST 10 FAQs optimized for AI Search / LLMs ) -->
            <section class="mt-16 pt-8 border-t border-white/10" id="faq">
                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">Frequently Asked Questions</h2>
                <div class="space-y-6">
                    <!-- Repeat this glass-card block at least 10 times -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-lg font-bold text-white mb-2">[Question 1]</h3>
                        <p class="text-gray-400 mb-0">[Answer 1]</p>
                    </div>
                    <!-- ... -->
                </div>
            </section>

            <hr class="border-gray-800 my-10">

            <!-- References -->
            <div class="mt-8">
                <h3 class="text-xl font-bold mb-4 text-white">References</h3>
                <ul class="list-disc list-inside text-gray-500 space-y-2 text-sm max-w-full overflow-hidden">
                    <li><a href="[URL]" class="hover:text-blue-400 break-words" target="_blank">[Reference Citation]</a></li>
                </ul>
            </div>
        </article>
    </main>

    <!-- Footer -->
    <footer class="py-8 border-t border-gray-900 text-center text-sm text-gray-600">
        © 2025 <span class="text-blue-500">A</span><span class="text-red-500">I</span> Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved
    </footer> <!-- Note: For ARABIC, use: © ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة -->
</body>
</html>
```
