---
name: article-creator
description: Automatically writes dual-language (English and Arabic) SEO articles for the AI Profit Lab blog when given a keyword. Supports Compact Keywords and Reddit-focused community curation strategies. Generates an image and applies the website's dark-mode glassmorphism HTML structure. Triggers when the user asks to "write an article about [keyword]" or "generate blog post for [keyword]".
---

# AI Profit Lab Article Creator

This skill automates the end-to-end creation of high-quality, story-driven, fully formatted SEO articles for the AI Profit Lab website, with specialized optimization for "Compact Keywords" and "Reddit Thread" search queries to rank against community discussions and capture LLM query fan-outs (Perplexity, ChatGPT, Gemini).

When the user asks you to write an article for a given keyword/topic, follow these steps exactly:

## Step 0: Title Similarity & Overlap Pre-Check (MANDATORY PRE-CHECK)
Before starting any research or outlining, perform a strict similarity/overlap check against all existing published articles on the website:
1. **Scan Existing Articles**: Check all `.html` files in `public_html/blog/en/` and `public_html/blog/ar/` (or inspect `blog_hub_data.json` / hub lists).
2. **Calculate Similarity/Overlap**: Compare the proposed article title/topic against existing article titles and target keywords using token overlap / Jaccard similarity / character n-gram overlap.
3. **Pushback Rule (>65% Similarity)**:
   - If the similarity or overlap with any existing article title/topic is **greater than 65%**, **STOP IMMEDIATELY**.
   - Do NOT proceed to research, outline, image generation, or HTML creation.
   - Output a clear pushback message stating:
     > 🛑 **Article Generation Pushed Back**: An article with >65% similarity/overlap already exists on the website.
     > - **Proposed Title/Topic**: "[Proposed Title]"
     > - **Existing Article**: "[Existing Article Title]" (`[file_path]`)
     > - **Similarity Score**: [Calculated %]
     >
     > Please provide a different topic or a unique strategic angle before proceeding.

## Step 1: Research and Outline
To ensure all generated articles achieve a **STRONG** rating under the quality audit suite, you must strictly satisfy all the following criteria during the research and outlining phase:

### Core Requirements & Quality Audit Criteria

1. **Title & H1 Match (Strength and Specifics)**:
   - The `<title>` tag and the main `<h1>` tag inside the body must be identical (or the title must start with the first 30 characters of the H1).
   - The title must NOT be generic (e.g. avoid patterns like "supercharge your business", "ai for business", "unlock the power of ai", "revolutionize your", "transform your business", "take your business to the next level").
   - The title must contain a specific number, location, or outcome (e.g. including Muscat, Oman, GCC, or outcomes/topics like "how to", "why", "cost", "roi", "guide", "free", "best", "top").
   - Title tag length must be >20 characters.

2. **Compact Keywords & Reddit Search Strategy**:
   - **Target Keyword Formulation**: When targeting search queries containing "Reddit" or community discussion intent, format the target keyword with the word "Reddit" and the current/upcoming year (e.g., `[Niche Topic] Reddit 2026`) to capture "query fan outs" used by LLMs (Perplexity, ChatGPT, Gemini).
   - **Slug & Title Alignment**: The page `<title>` tag and URL slug must be nearly identical to the target keyword. This provides ~90% of document relevance for low-competition terms.
   - **Avoid Over-Optimization**: Do NOT repeat the exact target keyword in the first line of text. Focus on document-level topical relevance rather than artificial keyword density.

3. **Opening Hook (No Self-Promotion)**:
   - The first paragraph (first 100 words of the body) must NOT be self-promotional. It must NOT contain phrases like "we are", "we provide", "our company", "ai profit lab is", "welcome to", or "at ai profit lab".
   - The hook must speak directly to the reader's business problems, pain points, or questions.

4. **Word Count & Compact Depth**:
   - The main body text (visible text inside the `<article>` tag, excluding navigation, header, footer, references, and schema) must be between **800 to 1200 words** (keeping it "Compact").
   - The text must contain at least **3+ concrete examples, step-by-step guides, or specific data points/numbers** (e.g. specific OMR/USD pricing, % growth, hours/days saved).

5. **Table of Contents (TOC)**:
   - **Mandatory TOC Component**: Every article must include a styled glassmorphism Table of Contents (TOC) right after the hero image / header area to give the page a well-thought-out, structured appearance.
   - Anchor links must map directly to each `<h2>` section ID (e.g. `#section-1`, `#section-2`, `#section-3`) and the `#faq` section.

6. **Headings & LLM Citation Structure**:
   - Use `<h2>` subheadings based on primary keyword variations, related questions from People Also Ask (PAA) data, or key Reddit thread topics.
   - Every article must contain at least **3+ `<h2>` subheadings** structured as questions.
   - Immediately below each `<h2>`, write a concise, direct answer (~40 words) in an "X is Y" or "To do X, you need Y" format for LLM SEO indexing.
   - The article body must contain at least **1 statistic/percentage/number** (using %, percent, OMR, USD, Rial, hours, days, etc.).

7. **Writing Style, Curation & Authentic Voice**:
   - **Resource & Curation Focus**: Position the article as a "Resources Page" or compilation of "Lessons from Reddit". Instead of standard long-winded definitions, compile the best responses/threads from community discussions and provide definitive takeaways or links.
   - **Proprietary Insight**: Incorporate proprietary observations, founder statements, or distinct ("spicy") titles to stand out from generic listicles.
   - **Anti-AI Tone (No Slop)**: Ensure an authentic human voice. Edit out generic AI giveaways and fluff (e.g., avoid "in today's fast-paced digital world", "delve", "tapestry", "supercharge", "game-changer", "unleash", "seamless").

8. **GCC / Oman Local Relevance**:
   - You must weave in at least **3+ unique local GCC or Oman references** (from keywords like Muscat, Oman, GCC, UAE, Saudi, Vision 2040, Omani PDPL, Sohar, Salalah, Royal Decree, Omantel, Ma'een, otech, etc.) naturally in the body text (do not limit them only to the title).

9. **Call to Action (CTA) Card**:
   - Every article must end with a styled glassmorphism CTA card encouraging readers to book an audit or consultation.
   - **CRITICAL:** The CTA block must be placed **inside the `<article>` tag**, right before the FAQ section, or before the closing `</article>` tag. This is because the quality auditor only parses text within the `<article>` tag, and the CTA must fall within the last 200 words of the parsed article body.
   - The CTA must have a clickable link (English: `/en/contact-en/`, Arabic: `/contact/`) and a strong action verb (e.g., "Book a Free 30-Minute AI Consultation").

10. **SEO Meta Description (CRITICAL)**:
    - Write unique meta descriptions that strictly follow these rules:
      - **140–155 characters exactly** in length.
      - Must include a specific business pain point or question the article answers.
      - Must include at least one GCC or Oman reference.
      - Must end with a concrete benefit or outcome.
      - Must **NOT** start with "AI Profit Lab", "Learn how", "Discover", or "Supercharge your business with".
      - Must be a complete sentence (no cut-offs).
      - *Arabic Version Meta Rules:* Must start with a specific regional business pain point (e.g., "هل تعاني من...") and be between 140–155 characters, ending with a clear benefit.

11. **FAQ Section**:
    - Generate an extensive FAQ section at the end of the article containing **exactly 10 Frequently Asked Questions** that people in Oman and the GCC actually ask about the subject.

12. **Duplicate & Similarity Pushback (Strict >65% Limit)**:
    - Enforce the Step 0 Pre-Check: Do not generate an article if title/topic similarity with an existing article exceeds 65%. If passed, ensure the new article maintains a unique strategic angle.

13. **JSON-LD Schema Markup**:
    - Embedded JSON-LD schema in `<head>` must include the article's `Article` data, the `FAQPage` data with all 10 FAQs, and `Organization` details.
    - Ensure the Organization schema and LocalBusiness/ProfessionalService schema have the correct properties:
      - `name`: "AI Profit Lab"
      - `legalName`: "International Gulf Lotus SPC"
      - `url`: "https://aiprofitlab.io"

14. **Legal Footer Copyright**:
    - English: `© 2025 AI Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved`
    - Arabic: `© ٢٠٢٥ AI Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة`

## Step 2: Generate the English Version
Draft the English article content. Wrap it in the exact HTML structure expected for the blog. Ensure it follows the dark-mode glassmorphism style.
Save it to: `public_html/blog/en/YYYY-MM-DD-[slug-title].html` (use the current date).

## Step 3: Generate the Arabic Version
Translate and adapt the article into Arabic. Make sure the tone remains professional and culturally relevant for the GCC/Oman market.
Set `lang="ar"` and `dir="rtl"`.
Save it to: `public_html/blog/ar/YYYY-MM-DD-[slug-title-in-english].html`.

## Step 4: Generate the Image
Use your `generate_image` tool to create the hero image based on the designated concept.
Save the generated image to: `public_html/blog/images/[image_name].png`. Make sure both HTML files point to this exact absolute path (`/blog/images/[image_name].png`).

## Step 4.5: Internal Linking & Cornerstoning Workflow
- **Cornerstoning**: Target low-competition keywords first. Once ranked, insert internal links to higher-competition "money" pages on the site to pass domain authority.
- **Bi-Directional Interlinking**:
  1. Add internal contextual links within the new article pointing to existing related blog posts on the site.
  2. Locate an existing high-ranking page on `aiprofitlab.io` and insert a contextual link pointing to the newly published article so search engine crawlers easily discover and index it.

## Step 5: Update the Blog Hub
After generating and saving the images and HTML files, use your `run_command` tool to execute the python script that automatically updates the hub pages with the new content:
`python3 update_blog_hubs.py` (run this from the `Website SEO` directory).

## Step 6: Regenerate the Sitemap
After the blog hub is updated, **always** regenerate the `sitemap.xml` by running the following inline Python script from the `public_html` directory:
```bash
cd "Website SEO/public_html" && python3 generate_sitemap.py
```
Or use the sitemap command. Confirm that sitemap output shows the updated URL count.

---

## HTML Template Requirements

### 1. English HTML Template
```html
<!DOCTYPE html>
<html lang="en" dir="ltr">
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
    <title>[SEO Title matching H1] | AI Profit Lab</title>
    <meta name="description" content="[140-155 chars unique description: start with pain point, include GCC/Oman ref, end with outcome, no forbidden start words]">
    <meta name="keywords" content="[SEO Keywords]">
    <link rel="canonical" href="https://aiprofitlab.io/blog/en/YYYY-MM-DD-[slug-title]/">
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
          "legalName": "International Gulf Lotus SPC",
          "url": "https://aiprofitlab.io/",
          "logo": {
            "@type": "ImageObject",
            "url": "https://aiprofitlab.io/favicon.svg"
          }
        },
        {
          "@type": "Article",
          "headline": "[SEO Title]",
          "description": "[140-155 chars unique description]",
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
            // Generate for ALL 10 FAQs sequentially
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
</head>
<body class="antialiased">
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 w-full z-50 glass sticky top-0 bg-black/30" id="header">
        <a href="/en/" class="font-extrabold text-3xl md:text-4xl tracking-tighter hover:opacity-80 transition logo-font">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        <a href="/blog/" class="text-gray-300 hover:text-white font-semibold transition">Back to Hub</a>
    </nav>

    <main class="max-w-4xl mx-auto px-6 py-16">
        <article>
            <div class="mb-12 text-center">
                <span class="bg-blue-500/10 text-blue-400 text-sm font-bold px-4 py-2 rounded-full border border-blue-500/20 mb-6 inline-block">[Category]</span>
                <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">[Article Title matching SEO Title]</h1>
                <p class="text-xl text-gray-400 max-w-2xl mx-auto">[Subtitle / Hook]</p>
            </div>

            <img src="/blog/images/[image_name].png" alt="[image_name] - Empowering AI Solutions by AI Profit Lab to scale your business operations." class="w-full rounded-3xl mb-16 shadow-[0_0_50px_rgba(59,130,246,0.15)] border border-white/5 object-cover h-[500px]">

            <!-- Table of Contents -->
            <nav class="glass-card rounded-2xl p-6 mb-12 border border-blue-500/20" id="table-of-contents">
                <h2 class="text-xl font-bold text-white mb-4 mt-0 border-b border-white/10 pb-2">Table of Contents</h2>
                <ul class="space-y-2 text-gray-300 text-sm">
                    <li><a href="#section-1" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">1.</span> [H2 Section 1 Question/Heading]</a></li>
                    <li><a href="#section-2" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">2.</span> [H2 Section 2 Question/Heading]</a></li>
                    <li><a href="#section-3" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">3.</span> [H2 Section 3 Question/Heading]</a></li>
                    <li><a href="#faq" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">4.</span> Frequently Asked Questions</a></li>
                </ul>
            </nav>

            <div class="prose max-w-none">
                [PARAGRAPHS, HEADINGS, BLOCKQUOTES]
            </div>

            <!-- CTA Block (MUST be inside <article> at the very end to pass word analysis) -->
            <div class="glass-card rounded-2xl p-8 mt-12 mb-8 text-center border-blue-500/30 border">
                <h3 class="text-2xl font-bold text-white mb-4">Ready to Automate Your Business Operations?</h3>
                <p class="text-gray-300 mb-6">AI Profit Lab helps non-technical managers in Oman and the GCC deploy custom AI solutions, automated customer service systems, and real-time dashboards to slash overhead costs and eliminate manual busywork.</p>
                <a class="inline-block bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-full transition shadow-[0_0_15px_rgba(37,99,235,0.5)]" href="/en/contact-en/">Book a Free 30-Minute AI Consultation</a>
            </div>

            <section class="mt-16 pt-8 border-t border-white/10" id="faq">
                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">Frequently Asked Questions</h2>
                <div class="space-y-6">
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-lg font-bold text-white mb-2">[Question 1]</h3>
                        <p class="text-gray-400 mb-0">[Answer 1]</p>
                    </div>
                </div>
            </section>

            <hr class="border-gray-800 my-10">

            <div class="mt-8">
                <h3 class="text-xl font-bold mb-4 text-white">References</h3>
                <ul class="list-disc list-inside text-gray-500 space-y-2 text-sm max-w-full overflow-hidden">
                    <li><a href="[URL]" class="hover:text-blue-400 break-words" target="_blank">[Reference Citation]</a></li>
                </ul>
            </div>
        </article>
    </main>

    <footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">
        <p>© 2025 <span class="text-blue-500">A</span><span class="text-red-500">I</span> Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved</p>
    </footer>
</body>
</html>
```

### 2. Arabic HTML Template
```html
<!DOCTYPE html>
<html lang="ar" dir="rtl">
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
    <meta name="category" content="[Category in Arabic]">
    <title>[SEO Title in Arabic matching H1] | AI Profit Lab</title>
    <meta name="description" content="[140-155 chars unique description: start with regional pain point 'هل تعاني من...', include GCC/Oman ref, end with outcome, no forbidden start words]">
    <meta name="keywords" content="[SEO Keywords in Arabic and English]">
    <link rel="canonical" href="https://aiprofitlab.io/blog/ar/YYYY-MM-DD-[slug-title-in-english]/">
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
          "legalName": "International Gulf Lotus SPC",
          "url": "https://aiprofitlab.io/",
          "logo": {
            "@type": "ImageObject",
            "url": "https://aiprofitlab.io/favicon.svg"
          }
        },
        {
          "@type": "Article",
          "headline": "[SEO Title in Arabic]",
          "description": "[140-155 chars unique description in Arabic]",
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
              "name": "[Question 1 in Arabic]",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "[Answer 1 in Arabic]"
              }
            }
          ]
        }
      ]
    }
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Outfit', sans-serif; background-color: #050505; color: #ffffff; text-align: right; }
        .logo-font { font-family: 'Outfit', sans-serif !important; }
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .glass-card { background: rgba(255, 255, 255, 0.02); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.05); transition: all 0.3s ease; }
        .glass-card:hover { border-color: #3B82F6; transform: translateY(-5px); box-shadow: 0 20px 40px rgba(59, 130, 246, 0.1); }
        .prose h2 { color: #60A5FA; margin-top: 2.5em; margin-bottom: 1em; font-weight: 800; font-size: 1.875rem; }
        .prose h3 { color: #93C5FD; margin-top: 2em; margin-bottom: 1em; font-weight: 700; font-size: 1.5rem; }
        .prose p { margin-bottom: 1.5em; line-height: 1.8; color: #D1D5DB; }
        .prose strong { color: #F3F4F6; }
        .prose blockquote { border-right: 4px solid #3B82F6; border-left: none; padding-right: 1rem; padding-left: 0; font-style: italic; color: #9CA3AF; margin-right: 0; }
        .text-right-ar { text-align: right; }
    </style>
</head>
<body class="antialiased">
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 w-full z-50 glass sticky top-0 bg-black/30" id="header" dir="ltr">
        <a href="/" class="font-extrabold text-3xl md:text-4xl tracking-tighter hover:opacity-80 transition logo-font">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        <a href="/blog-ar/" class="text-gray-300 hover:text-white font-semibold transition" dir="rtl">العودة إلى المدونة</a>
    </nav>

    <main class="max-w-4xl mx-auto px-6 py-16">
        <article>
            <div class="mb-12 text-center text-right-ar">
                <span class="bg-blue-500/10 text-blue-400 text-sm font-bold px-4 py-2 rounded-full border border-blue-500/20 mb-6 inline-block">[Category in Arabic]</span>
                <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">[Article Title in Arabic matching SEO Title]</h1>
                <p class="text-xl text-gray-400 max-w-2xl mx-auto">[Subtitle / Hook in Arabic]</p>
            </div>

            <img src="/blog/images/[image_name].png" alt="[image_name] - حلول الذكاء الاصطناعي المبتكرة من AI Profit Lab لتطوير أعمالك." class="w-full rounded-3xl mb-16 shadow-[0_0_50px_rgba(59,130,246,0.15)] border border-white/5 object-cover h-[500px]">

            <!-- جدول المحتويات -->
            <nav class="glass-card rounded-2xl p-6 mb-12 border border-blue-500/20 text-right-ar" id="table-of-contents">
                <h2 class="text-xl font-bold text-white mb-4 mt-0 border-b border-white/10 pb-2">جدول المحتويات</h2>
                <ul class="space-y-2 text-gray-300 text-sm">
                    <li><a href="#section-1" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">١.</span> [عنوان القسم الأول]</a></li>
                    <li><a href="#section-2" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">٢.</span> [عنوان القسم الثاني]</a></li>
                    <li><a href="#section-3" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">٣.</span> [عنوان القسم الثالث]</a></li>
                    <li><a href="#faq" class="hover:text-blue-400 transition flex items-center gap-2"><span class="text-blue-500">٤.</span> الأسئلة الشائعة</a></li>
                </ul>
            </nav>

            <div class="prose max-w-none text-right-ar">
                [PARAGRAPHS, HEADINGS, BLOCKQUOTES IN ARABIC]
            </div>

            <div class="glass-card rounded-2xl p-8 mt-12 mb-8 text-center border-blue-500/30 border">
                <h3 class="text-2xl font-bold text-white mb-4">هل أنت مستعد لأتمتة عمليات شركتك؟</h3>
                <p class="text-gray-300 mb-6">تساعد AI Profit Lab المديرين غير التقنيين في عُمان ودول الخليج على نشر حلول الذكاء الاصطناعي المخصصة، وأنظمة خدمة العملاء المؤتمتة، ولوحات المعلومات الفورية لتقليل النفقات العامة والتخلص من المهام اليدوية المكررة.</p>
                <a class="inline-block bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-full transition shadow-[0_0_15px_rgba(37,99,235,0.5)]" href="/contact/">احجز استشارة مجانية في الذكاء الاصطناعي لمدة 30 دقيقة</a>
            </div>

            <section class="mt-16 pt-8 border-t border-white/10" id="faq">
                <h2 class="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400 mb-8">الأسئلة الشائعة</h2>
                <div class="space-y-6">
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-lg font-bold text-white mb-2">[Question 1 in Arabic]</h3>
                        <p class="text-gray-400 mb-0">[Answer 1 in Arabic]</p>
                    </div>
                </div>
            </section>

            <hr class="border-gray-800 my-10">

            <div class="mt-8">
                <h3 class="text-xl font-bold mb-4 text-white">المراجع</h3>
                <ul class="list-disc list-inside text-gray-500 space-y-2 text-sm max-w-full overflow-hidden">
                    <li><a href="[URL]" class="hover:text-blue-400 break-words" target="_blank">[Reference Citation in Arabic]</a></li>
                </ul>
            </div>
        </article>
    </main>

    <footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">
        <p>© ٢٠٢٥ <span class="text-blue-500">A</span><span class="text-red-500">I</span> Profit Lab — علامة تجارية لشركة International Gulf Lotus SPC • جميع الحقوق محفوظة</p>
    </footer>
</body>
</html>
```
