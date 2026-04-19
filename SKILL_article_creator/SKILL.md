---
name: article-creator
description: Automatically writes dual-language (English and Arabic) SEO articles for the AI Profit Lab blog when given a keyword. Generates an image and applies the website's dark-mode glassmorphism HTML structure. Triggers when the user asks to "write an article about [keyword]" or "generate blog post for [keyword]".
---

# AI Profit Lab Article Creator

This skill automates the end-to-end creation of high-quality, story-driven, fully formatted SEO articles for the AI Profit Lab website.

When the user asks you to write an article for a given keyword/topic, follow these steps exactly:

## Step 1: Research and Outline
- **Lead with Provocative Expertise**: The article must be highly compelling, using a storytelling style based on reality and lived-experience. Do not write safe, generic tech guides. Tell the audience exactly why most tech implementations fail for non-technical leaders and how our framework fixes it.
- **The "Extractable" Content Structure**: Rip out long walls of text. Use clear `<h2>` and `<h3>` headings. Start every major section with a bolded direct answer or a quick "TL;DR." bulleted list so that AI models can instantly pull your exact bullet points.
- **Target "Fan-Out" Queries**: Optimize not just for short keywords, but for complex, long, conversational "fan-out" questions (e.g., "What is the most cost-effective AI implementation strategy for regional businesses looking to scale internationally?").
- **Factual Density**: AI prioritizes data over fluff. When discussing boosting ROI, back it up. Include real statistics, HTML comparison tables, and strict Q&A formats directly within the body content to increase citation rates.
- **Video-to-Text Synergy**: Embed relevant, energetic, high-retention YouTube videos directly into the written posts to skyrocket page engagement metrics.
- The article must be a rich, highly SEO-friendly article at least 1000 words long.
- Include a specific section for References at the end (verify that references exist and are not broken).
- Generate an extensive FAQ section at the end containing AT LEAST 10 Frequently Asked Questions. These questions should be optimized for AI search engines (like Perplexity, ChatGPT, and Google AI Overviews) by directly answering the most common, long-tail queries users or LLMs might have about the topic.
- Designate a hero image concept that matches the futuristic, semi-realistic AI vibe of the other articles.

## Step 2: Generate the English Version
Draft the English article content. Then wrap it in the exact HTML structure expected for the blog. Ensure it follows the dark-mode glassmorphism style.
Ensure you strictly populate the embedded JSON-LD Schema Markup in the `<head>` with the article's specific `Article` data, the 10+ `FAQPage` data, and the `Organization` details, as AI search engines prioritize highly structured schema paths.
Save it to: `public_html/blog/en/YYYY-MM-DD-[slug-title].html` (use the current date).

## Step 3: Generate the Arabic Version
Translate and adapt the article into Arabic. Make sure the tone remains professional and culturally relevant for the GCC/Oman market.
Set `lang="ar"` and `dir="rtl"`.
In the navbar, change "Back to Hub" to "العودة إلى المركز" and link to `../../blog_ar.html`.
Save it to: `public_html/blog/ar/YYYY-MM-DD-[slug-title-in-english].html`.

## Step 4: Generate the Image
Use your `generate_image` tool to create the hero image based on the designated concept.
Save the generated image to: `public_html/blog/images/[image_name].png`. Make sure both HTML files point to this exact relative path (`../../blog/images/[image_name].png`).

## Step 5: Update the Blog Hub
After generating and saving the images and HTML files, use your `run_command` tool to execute the python script that automatically updates the hub pages with the new content:
`python3 update_blog_hubs.py` (run this from the `Website SEO` directory or use `python3 "Website SEO/update_blog_hubs.py"` relative to your current workspace root).

---

## HTML Template Requirements
Whenever you generate the files, use the following HTML template. Do NOT deviate from this structure, as it maintains the site's dark-mode glassmorphism design:

```html
<!DOCTYPE html>
<html lang="en" dir="ltr"> <!-- Change to ar and rtl for Arabic -->
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="category" content="[Category]">
    <title>[SEO Title] | AI Profit Lab</title>
    <meta name="description" content="[SEO Description]">
    <meta name="keywords" content="[SEO Keywords]">
    <link rel="icon" type="image/svg+xml" href="../../favicon.svg">
    <link rel="apple-touch-icon" href="../../favicon.svg">
    
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
    <!-- Navbar -->
    <nav class="flex justify-between items-center px-6 md:px-12 py-8 w-full z-50 glass sticky top-0 bg-black/30">
        <a href="../../en.html" class="font-extrabold text-3xl md:text-4xl tracking-tighter hover:opacity-80 transition">
            <span class="text-blue-500">A</span><span class="text-red-500">I</span> <span class="text-white text-2xl md:text-3xl">Profit Lab</span>
        </a>
        <a href="../../blog.html" class="text-gray-300 hover:text-white font-semibold transition">Back to Hub</a>
    </nav> <!-- Note: update links to ar.html and blog_ar.html for the Arabic translation -->

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-6 py-16">
        <article>
            <div class="mb-12 text-center text-right-ar"> <!-- Use appropriate text-align for rtl reading -->
                <span class="bg-blue-500/10 text-blue-400 text-sm font-bold px-4 py-2 rounded-full border border-blue-500/20 mb-6 inline-block">[Category]</span>
                <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">[Article Title]</h1>
                <p class="text-xl text-gray-400 max-w-2xl mx-auto">[Subtitle / Hook]</p>
            </div>

            <img src="../../blog/images/[image_name].png" alt="[Image alt description]" class="w-full rounded-3xl mb-16 shadow-[0_0_50px_rgba(59,130,246,0.15)] border border-white/5 object-cover h-[500px]">

            <div class="prose max-w-none">
                [PARAGRAPHS, HEADINGS, BLOCKQUOTES. MUST BE AT LEAST 1000 WORDS TOTAL, USING STORYTELLING NARRATIVE]
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
</body>
</html>
```
