---
name: seo-geo-validator
description: Reviews content visibility by auditing Markdown/HTML against GCC regional keyword trends and Generative Engine Optimization (GEO) best practices.
---

# SEO & GEO Validator Skill

## Trigger
Use this skill whenever the user asks to "Review content visibility" or perform a GEO/SEO audit on content.

## Instructions
1. **Understand the Goal**: The objective is to optimize the provided Markdown or HTML content for Generative Engine Optimization (GEO) and search engine visibility, specifically targeting the GCC (Gulf Cooperation Council) region.
2. **GCC Keyword Trends**: Ensure the content uses regionally appropriate terminology, localized context (e.g., Oman, UAE, Saudi Arabia markets), and relevant Arabic transliterations if applicable.
3. **GEO Best Practices**:
   - Ensure clear, direct answers to common queries.
   - Verify structured data formatting (lists, tables, bolded key terms) which LLMs prefer.
   - Check for authoritative tone and citation-friendly structure.
4. **Structural Validation**: Run the `validate_structure.py` script included in this skill directory against the target file to scan for structural layout anomalies (e.g., missing headers, improper tag nesting).
5. **Reporting**: Provide a summary of the audit, highlighting areas for improvement, GCC localization suggestions, and any structural errors found by the script.
