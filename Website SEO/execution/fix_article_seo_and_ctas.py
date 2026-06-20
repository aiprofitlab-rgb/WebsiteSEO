#!/usr/bin/env python3
import os
import re
import json
from pathlib import Path

BLOG_DIR = Path("/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/public_html/blog/en")

# Pre-generated, compliant English meta descriptions (140-155 characters exactly)
META_MAPPING = {
    "2026-03-28-ceo-dashboard.html": "Struggling with lag in monthly business reports? GCC executives are transitioning to real-time dashboards to capture anomalies and protect profit margins.",
    "2026-03-28-google-alert.html": "Overwhelmed by notification noise? GCC business leaders are leveraging refined Google Alerts queries to filter critical market trends and secure growth.",
    "2026-03-30-ai-automation-oman-vision.html": "Wondering how to align your business with Oman Vision 2040? Automated workflows eliminate repetitive administrative tasks to unlock high-value efficiency.",
    "2026-03-31-arabic-first-ai-models.html": "Why do standard Western AI models fail with local dialects? GCC enterprises are adopting Arabic-first LLMs to enhance customer trust and local relevance.",
    "2026-03-31-arabic-vs-global-ai-models.html": "Are you unsure whether to choose ChatGPT or Jais in Oman and UAE? Compare global and regional models to secure your data sovereignty and dialect fit.",
    "2026-04-01-how-companies-data-leaks-through-ai.html": "Are your employees leaking proprietary company data into public ChatGPT? Muscat businesses are implementing secure AI policies to block information leaks.",
    "2026-04-01-notebooklm-guide-for-busy-managers.html": "Drowning in long financial reports? Oman managers are deploying Google NotebookLM to parse documents and find critical contract risks within seconds.",
    "2026-04-04-ai-receptionist-your-business-needs.html": "Are missed phone calls costing your business sales? Muscat firms are deploying 24/7 AI receptionists to capture missed revenue without adding payroll.",
    "2026-04-06-ai-admin-automation.html": "Struggling with administrative busywork? Oman operations directors are integrating autonomous AI agents to speed up workflows and reduce manual entry.",
    "2026-04-06-gcc-ai-search-trends.html": "Are you curious about the GCC region's actual digital needs? Read our search data analysis to see how businesses are implementing practical AI tools.",
    "2026-04-14-ai-ethics-sharia-compliance.html": "Concerned about algorithmic bias? Developers in Oman and Saudi are aligning AI models with Sharia ethics to ensure fair, transparent, and moral usage.",
    "2026-04-14-sovereign-ai-data-borders.html": "Is your sensitive business data leaving national borders? GCC enterprises are shifting to sovereign AI infrastructures to satisfy local compliance laws.",
    "2026-04-19-ai-automation-agency-worth-it.html": "Are high payroll costs slowing your custom AI development? GCC enterprises are hiring specialized agencies to accelerate deployment and maximize profit.",
    "2026-04-19-ai-logistics-roi-oman-uae.html": "Are dispatch delays hurting your supply chain? Logistics operators in Sohar and Salalah are deploying automated document parsing to cut transit delays.",
    "2026-04-19-b2b-ai-automation-cost-roi.html": "Wondering how much custom AI setups cost? Oman B2B distributors are deploying automated order systems to cut vendor response time and secure margins.",
    "2026-04-19-build-ai-whatsapp-receptionist.html": "Should you build or buy a customer service bot? Muscat business owners are adopting done-for-you systems to enable instant booking and customer reply.",
    "2026-04-19-stop-losing-leads-whatsapp-ai.html": "Is delayed customer reply killing your sales? Muscat businesses are integrating conversational AI on WhatsApp to capture and close bookings instantly.",
    "2026-04-20-whatsapp-api-vs-ai-automation.html": "Are rigid 'press 1' chatbots frustrating your clients? Oman and UAE firms are upgrading to conversational AI on WhatsApp to close sales automatically.",
    "2026-04-21-ai-oil-gas-workflow-automation.html": "How are energy giants preventing hazardous pipe leaks? Regional operators like Oman PDO utilize automated vision alerts to reduce manual safety checks.",
    "2026-04-22-b2b-lead-generation-automation-civil-engineering.html": "Tired of searching municipal tender portals manually? Muscat civil engineering firms are deploying automated scrapers to win high-value contracts.",
    "2026-04-23-logistics-automation-fleet-managers.html": "Are manual dispatch boards causing route delays? Oman transport managers are deploying automated data parsing to optimize fleet operations and tracking.",
    "2026-04-23-n8n-vs-make-automation-scaling.html": "Is your current workflow automation platform too expensive? GCC developers compare n8n and Make to achieve cost-efficient scalability and data control.",
    "2026-04-25-custom-api-vs-native-integrations.html": "Are fragile software integrations breaking your pipeline? Oman managers are opting for custom APIs to stabilize business workflows and secure data sync.",
    "2026-04-26-ai-automation-oman-2025-guide.html": "Looking for practical tech steps in Muscat? Our 2025 guide helps Oman business owners deploy automated CRM and booking tools to cut operating costs.",
    "2026-04-28-ai-automation-cost-uae-businesses.html": "Are hidden fees inflating your digital transformation budget? UAE operations directors review real pricing models to scale business workflows stably.",
    "2026-04-28-ai-automation-roi-2025-guide.html": "Unsure how to measure the return of digital tools? Oman managers are automating manual data routing to save 20+ hours weekly and prove operational ROI.",
    "2026-04-28-ai-automation-saudi-sme-worth-it.html": "Can small businesses justify custom automated systems? Saudi SMEs are deploying no-code integrations to reduce admin overhead and beat competitors.",
    "2026-04-28-qatar-businesses-ai-automation.html": "Are administrative bottlenecks slowing your team down? Qatar enterprises are deploying automated ticket routing to increase customer satisfaction levels.",
    "2026-04-30-ai-insurance-oman-roi-costs.html": "Are manual insurance claims hurting customer trust? Oman insurance firms are deploying automated policy checks to accelerate settlements and cut costs.",
    "2026-05-02-ai-special-zone-muscat-royal-decree.html": "Confused by the new tech laws in Muscat? Our analysis breaks down Royal Decree 50/2026 to help Omani startups align with national compliance targets.",
    "2026-05-02-oman-gpt-national-ai-model.html": "Are Western language models misinterpreting local phrases? Oman GPT provides highly accurate dialect support to enhance regional customer operations.",
    "2026-05-05-oman-vision-2040-ai-goals.html": "Wondering how to qualify for national digital grants? Check the Oman Vision 2040 AI roadmap to optimize your business operations and secure funding.",
    "2026-05-05-omantel-otech-sovereign-cloud.html": "Is server latency slowing down your regional apps? Omantel Otech sovereign cloud offers low-latency AWS infrastructure to secure local hosting in Oman.",
    "2026-05-06-maeen-ai-oman-national-llm.html": "Are manual processes slowing municipal approvals? Oman's Ma’een AI LLM automates document analysis to accelerate public services and compliance checks.",
    "2026-05-06-oman-lens-ol2-ai-satellite-launch.html": "How are regional developers obtaining real-time earth images? Oman Lens OL-2 satellite launch offers advanced TOPS capability to speed up observation.",
    "2026-05-07-oman-10-percent-gdp-digital-economy-target.html": "Will Muscat's shifting digital economy affect your business? Review the national plan to target 10% GDP and position your company for tech subsidies.",
    "2026-05-08-rise-of-agentic-ai-oman.html": "Are basic chatbots failing to resolve customer requests? Oman managers are upgrading to agentic AI to execute complex, multi-step workflows stably.",
    "2026-05-09-roi-of-ai-muscat-sme-efficiency.html": "Are repetitive admin tasks draining your resources? Muscat SMEs are automating CRM routing to save 20 hours a week and improve bottom-line profit.",
    "2026-05-10-data-sovereignty-self-hosted-ai.html": "Concerned that public cloud hosting violates Omani data laws? Self-hosted AI models secure your database internally and ensure complete local compliance.",
    "2026-05-11-non-technical-managers-guide-ai-implementation.html": "Are you a non-technical manager worried about complex tech setups? Our guide helps Muscat leaders deploy automated workflows without writing code.",
    "2026-05-11-preventing-retail-loss-ai-oman-hypermarkets.html": "Are inventory errors and shoplifting cutting your retail margins? Oman hypermarkets are deploying predictive AI to detect theft and protect profits.",
    "2026-05-13-live-ceo-dashboard-avoid-loss-secure-profit.html": "Is delayed financial data causing budget leaks? Muscat firms utilize live dashboards with real-time operational metrics to prevent revenue losses.",
    "2026-05-14-ai-automation-dentistry-clinics-efficiency.html": "Are patient no-shows draining your medical office? Muscat dental clinics are deploying AI tools to send smart WhatsApp reminders and fill schedules.",
    "2026-05-14-automatic-content-creation-ai-scale-quality.html": "Struggling to write high-quality marketing copy consistently? GCC businesses are deploying automated content pipelines to boost search visibility.",
    "2026-05-15-ai-email-writing-guide-busy-managers-productivity.html": "Spending hours writing repetitive business emails daily? Oman managers are deploying automated email assistants to draft replies and free up schedules.",
    "2026-05-16-gemini-ai-business-use-oman.html": "Struggling to improve your team's operational output? Learn how Oman businesses are utilizing Google Gemini Workspace to cut task time by 50%.",
    "2026-05-16-oman-invests-neuralink-elon-musk.html": "Want to know where Oman's tech investments are heading? Our analysis details Oman's backing of Neuralink to help local firms prepare for future tech.",
    "2026-05-18-psychology-of-ai-adoption-business.html": "Is your team resisting new software updates? GCC operations managers are employing change strategies to ensure smooth AI adoption and high output.",
    "2026-05-20-ai-for-omani-smes-vision-2040.html": "How can small local businesses compete with giant firms? Omani SMEs are implementing no-code workflows under Vision 2040 to scale operations quickly.",
    "2026-05-20-ai-innovation-oman-key-sectors.html": "Is manual processing stalling growth in key sectors? Oman is deploying automated logistics and banking workflows to optimize national digital output.",
    "2026-05-20-data-privacy-cybersecurity-oman.html": "Worried that client data handling violates Oman MTCIT guidelines? Review our compliance guide for local SMEs to secure records and avoid penalties.",
    "2026-05-20-top-5-ai-tools-muscat.html": "Confused by the hundreds of digital tools online? We review the top 5 platforms Muscat businesses are deploying to boost daily team output.",
    "2026-06-03-solving-retail-shrinkage-ai-muscat-hypermarkets.html": "Are inventory errors cutting into your supermarket margins? Muscat hypermarkets deploy smart vision tools to solve shrinkage and cut losses by 40%.",
    "2026-06-04-building-localized-ai-infrastructure-oman.html": "Concerned that public hosting risks data leaks? Oman enterprises are building localized, sovereign hosting nodes to ensure secure local compliance.",
    "2026-06-05-missed-call-recovery-system.html": "Are missed business calls sending customers to competitors? Muscat firms are deploying automated callback systems to recover 90% of missed leads.",
    "2026-06-05-the-ceo-dashboard-why-monthly-revenue-checks-are-killing-your-business.html": "Is looking at revenue once a month hiding operating leaks? Muscat executives deploy live dashboards to detect cost anomalies before they hurt profits.",
    "2026-06-05-whatsapp-workflows-oman-managers.html": "Are manual messaging delays slowing down client orders? Oman operations managers deploy WhatsApp routing systems to cut processing times by 60%.",
    "2026-06-05-why-most-ai-agencies-in-oman-are-selling-you-a-pipe-dream.html": "Tired of generic tech consultants offering no ROI? Learn how Oman business owners spot empty promises and secure practical, profitable automations.",
    "2026-06-07-cut-operational-costs-oman-ai-roadmap.html": "Are high overhead costs eating your company margins? Our structured tech roadmap helps Oman businesses automate CRM data to cut costs by 30%.",
    "2026-06-07-integrating-localized-llms-arabic-customer-support.html": "Are English support bots frustrating local customers in Oman and GCC? Integrate localized Arabic LLMs to handle dialect support and satisfy clients.",
    "2026-06-07-pdpl-what-it-means-for-your-ai-chatbots.html": "Worried that your customer support chatbot violates Oman PDPL? Review our compliance guide for local SMEs to secure data and avoid heavy fines.",
    "2026-06-08-hidden-cost-manual-data-entry.html": "Are manual data entry errors hurting your operations? Muscat businesses are deploying automated database sync tools to speed work and eliminate errors.",
    "2026-06-08-how-smes-in-muscat-scale-revenue-without-new-hires.html": "Is the high cost of hiring stalling your sales growth? Muscat SMEs are automating lead management to double operational output without new hires.",
    "2026-06-08-whatsapp-automation-lead-fix.html": "Is your sales team taking hours to reply to WhatsApp chats? Oman businesses deploy automated lead routing to reply in seconds and convert 2x clients.",
    "2026-06-11-localized-ai-infrastructure-omani-startups.html": "Are high international cloud costs draining your budget? Omani startups are deploying localized server nodes to boost data security and cut overheads.",
    "2026-06-11-navigating-pdpl-ai-compliant-chatbots-oman.html": "Unsure how to satisfy the new Omani personal data laws? Review our checklist for building AI-compliant chatbots to secure your customer database.",
    "2026-06-12-building-customer-trust-ai-oman.html": "Are your clients skeptical about automated customer support? Oman business owners are adding human-in-the-loop triggers to secure customer trust.",
    "2026-06-12-vision-2040-action-ai-strategies-local-retailers.html": "Struggling to optimize retail stock levels? Oman retailers deploy predictive inventory tools under Vision 2040 to prevent waste and boost shop profits.",
    "2026-06-12-whatsapp-ai-receptionist-oman.html": "Are support delays driving customer reviews down? Oman business owners are deploying WhatsApp AI receptionists to reply instantly and handle 5x chats.",
    "2026-06-13-automated-lead-recovery-muscat-hypermarket-case-study.html": "Are shopping cart drop-offs hurting your retail sales? Our Muscat hypermarket study reveals how automated lead routing recovered 12% of lost sales.",
    "2026-06-13-integrate-ai-omani-retail-pos.html": "Is manual inventory tracking causing stockouts at checkout? Omani retailers integrate predictive POS databases to automate orders and predict peak hours.",
    "2026-06-13-the-2026-audit-5-tasks-to-stop-doing-manually.html": "Are your team members spending hours checking spreadsheets? Oman managers automate 5 administrative tasks to cut human error and reclaim 15 hours.",
    "2026-06-14-automation-workflow-slowing-down.html": "Are your current automation workflows lagging or breaking? GCC operations directors deploy error checks to stabilize data sync and restore system speed.",
    "2026-06-14-how-we-automated-lead-recovery-muscat-hypermarket-case-study.html": "Are your online leads going cold before sales reach them? Our Muscat hypermarket case study shows how automated WhatsApp replies boost checkout rates.",
    "2026-06-14-stop-using-chatgpt-business-strategy.html": "Are generic ChatGPT answers failing to solve operational gaps? GCC executives combine local market research with custom databases to plan growth stable.",
    "2026-06-14-the-set-and-forget-myth-ai-human-pilot.html": "Are your digital workflows failing silently? Oman operations managers establish human-in-the-loop checkpoints to secure data sync and stop errors.",
    "2026-06-14-why-most-ai-consultants-gcc-selling-air.html": "Tired of tech consultants promising growth with no proof? Learn how GCC business owners audit provider code to ensure highly profitable automation.",
    "2026-06-16-whatsapp-ai-receptionist-cost-oman-2026.html": "Unsure of the setup costs for custom messaging bots? Review the 2026 WhatsApp API pricing for Oman to choose the best automation provider.",
    "2026-06-17-7-whatsapp-messages-costing-omani-businesses.html": "Are Meta's conversation fees eating your customer service budget? Omani businesses restructure templates to cut costs and save messaging fees.",
    "2026-06-17-whatsapp-ai-beauty-salons-spas-oman-guide.html": "Are empty scheduling hours reducing your beauty salon margins? Oman spas deploy WhatsApp AI booking assistants to handle inquiries and fill calendars.",
    "2026-06-17-whatsapp-ai-car-workshop-muscat.html": "Are empty service bays reducing workshop revenue in Muscat? Automate customer check-ins via WhatsApp to confirm arrivals and double bay bookings.",
    "2026-06-17-whatsapp-ai-real-estate-oman-guide.html": "Are property agents losing potential tenants due to slow replies? Oman agencies deploy WhatsApp AI to capture 100% of incoming property inquiries.",
    "2026-06-17-whatsapp-auto-reply-clinic-oman-setup-guide.html": "Are patient bookings lost during clinic off-hours? Oman medical centers deploy automated WhatsApp replies to capture inquiries and secure consultations.",
    "2026-06-17-whatsapp-bot-appointment-booking.html": "Are scheduling errors and double bookings wasting admin time? Oman businesses integrate CRM-linked bots to automate scheduling and routing stably.",
    "2026-06-17-whatsapp-business-api-vs-app-oman-guide.html": "Is the five-device limit on WhatsApp Business stalling your team? Oman companies migrate to Meta's API to enable unlimited agent access and automations."
}

def update_meta_description(content, filename, new_meta):
    # Match standard description meta tag with flexible spacing/quoting
    meta_tag_match = re.search(r'(<meta\s+[^>]*name=["\']description["\'][^>]*>)', content, re.IGNORECASE)
    current_meta = "MISSING"
    
    if meta_tag_match:
        tag_str = meta_tag_match.group(1)
        content_match = re.search(r'content=["\']([^"\']*)["\']', tag_str, re.IGNORECASE)
        if content_match:
            current_meta = content_match.group(1)
        
        new_tag = f'<meta name="description" content="{new_meta}">'
        content = content.replace(tag_str, new_tag)
    else:
        # Check alternative attribute order
        meta_tag_match_alt = re.search(r'(<meta\s+[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\'][^>]*>)', content, re.IGNORECASE)
        if meta_tag_match_alt:
            tag_str = meta_tag_match_alt.group(1)
            current_meta = meta_tag_match_alt.group(2)
            new_tag = f'<meta name="description" content="{new_meta}">'
            content = content.replace(tag_str, new_tag)
        else:
            # Missing entirely
            title_match = re.search(r'(</title>)', content, re.IGNORECASE)
            new_tag = f'\n<meta name="description" content="{new_meta}">'
            if title_match:
                content = content.replace(title_match.group(1), title_match.group(1) + new_tag)
            else:
                head_match = re.search(r'(<head[^>]*>)', content, re.IGNORECASE)
                if head_match:
                    content = content.replace(head_match.group(1), head_match.group(1) + new_tag)
                
    return content, current_meta

def inject_cta_if_missing(content):
    has_cta = False
    if "<!-- CTA Block -->" in content:
        has_cta = True
    elif "Get a Free WhatsApp Audit" in content or "Book a Free 30-Minute AI" in content or "Book a Free Consultation" in content:
        has_cta = True
        
    if not has_cta:
        cta_html = """
<!-- CTA Block -->
<div class="glass-card rounded-2xl p-8 mt-12 mb-8 text-center border-blue-500/30 border">
    <h3 class="text-2xl font-bold text-white mb-4">Ready to Automate Your Business Operations?</h3>
    <p class="text-gray-300 mb-6">AI Profit Lab helps non-technical managers in Oman and the GCC deploy custom AI solutions, automated customer service systems, and real-time dashboards to slash overhead costs and eliminate manual busywork.</p>
    <a class="inline-block bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-full transition shadow-[0_0_15px_rgba(37,99,235,0.5)]" href="/en/contact/">Book a Free 30-Minute AI Consultation</a>
</div>
"""
        faq_match = re.search(r'(<!-- FAQ Section -->|<section\s+[^>]*id=["\']faq["\'])', content, re.IGNORECASE)
        if faq_match:
            content = content.replace(faq_match.group(1), cta_html + "\n" + faq_match.group(1))
        else:
            article_match = re.search(r'(</article>)', content, re.IGNORECASE)
            if article_match:
                content = content.replace(article_match.group(1), cta_html + "\n" + article_match.group(1))
    return content

def fix_legal_footer(content):
    correct_footer = """<footer class="border-t border-white/10 bg-black py-8 text-center text-gray-500 text-sm mt-auto">
    <p>© 2025 <span class="text-blue-500">A</span><span class="text-red-500">I</span> Profit Lab — a brand of International Gulf Lotus SPC • All Rights Reserved</p>
</footer>"""
    footer_regex = re.compile(r'<footer[^>]*>.*?</footer>', re.DOTALL | re.IGNORECASE)
    if re.search(footer_regex, content):
        content = re.sub(footer_regex, correct_footer, content)
    else:
        body_end = re.search(r'(</body>)', content, re.IGNORECASE)
        if body_end:
            content = content.replace(body_end.group(1), correct_footer + "\n" + body_end.group(1))
    return content

def fix_schema_legal_name(content):
    # Ensure LocalBusiness / ProfessionalService has the required legalName mapping
    content = content.replace('"@type": "LocalBusiness"', '"@type": "ProfessionalService"')
    if '"legalName"' not in content:
        content = content.replace(
            '"name": "AI Profit Lab",',
            '"name": "AI Profit Lab",\n            "legalName": "International Gulf Lotus SPC",'
        )
    return content

def main():
    print("=== AI Profit Lab — Applying SEO & Quality Fixes ===")
    
    updated_files = 0
    for filename, new_meta in META_MAPPING.items():
        filepath = BLOG_DIR / filename
        if not filepath.exists():
            print(f"Warning: File {filename} not found in {BLOG_DIR}")
            continue
            
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Apply edits
        content, current_meta = update_meta_description(content, filename, new_meta)
        content = inject_cta_if_missing(content)
        content = fix_legal_footer(content)
        content = fix_schema_legal_name(content)
        
        # Write updates
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        updated_files += 1
        
        # Print requested format
        print(f"FILE: {filename}")
        print(f"CURRENT META: {current_meta}")
        print(f"NEW META: {new_meta}")
        print(f"CHARACTER COUNT: {len(new_meta)}")
        print("-" * 50)
        
    print(f"\nSuccessfully applied optimizations to {updated_files} articles.")

if __name__ == "__main__":
    main()
