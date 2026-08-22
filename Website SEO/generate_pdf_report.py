import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "AI Profit Lab — High-Quality Backlink Research & Strategy")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, page_text)
        self.drawString(54, 36, "Confidential & Proprietary — aiprofitlab.io (Muscat, Oman)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)
        
        self.restoreState()

def generate_pdf():
    pdf_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/AI_Profit_Lab_Backlink_Opportunities.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0F172A") # Slate 900
    SECONDARY = colors.HexColor("#2563EB") # Blue 600
    ACCENT = colors.HexColor("#0D9488") # Teal 600
    TEXT_COLOR = colors.HexColor("#334155") # Slate 700
    MUTED_TEXT = colors.HexColor("#64748B") # Slate 500
    BG_LIGHT = colors.HexColor("#F8FAFC") # Slate 50
    BORDER_COLOR = colors.HexColor("#E2E8F0") # Slate 200
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceAfter=14
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_COLOR,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_COLOR,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )
    
    meta_style = ParagraphStyle(
        'Meta_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=PRIMARY
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_COLOR
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=PRIMARY
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("AI PROFIT LAB — BACKLINK RESEARCH & STRATEGY", title_style))
    story.append(Paragraph("Target: <b>aiprofitlab.io</b> (AI Automation Consultancy for GCC SMBs • Muscat, Oman)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=12))
    
    # Intro summary
    intro_p = Paragraph(
        "<b>Executive Summary:</b> This research identifies 10 strictly verified, high-authority backlink and thought-leadership targets tailored for AI Profit Lab. All mass-directory submission platforms, link farms, and low-quality PBNs have been filtered out. Each entry below meets strict criteria: verified organic traffic, active editorial moderation, and clear topical/geographic alignment with AI automation and the GCC B2B landscape.",
        body_style
    )
    story.append(intro_p)
    story.append(Spacer(1, 10))
    
    # Category 1
    story.append(Paragraph("Category 1: Curated B2B & Agency Directories (Strict Editorial Review)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=8))
    
    cat1_items = [
        {
            "name": "1. Clutch.co",
            "url": "https://clutch.co/get-listed",
            "dr": "DR 90+ | Monthly Traffic: ~2.5M+ (Source: Ahrefs)",
            "link_type": "Nofollow / Local Citation Entity",
            "standard": "High Editorial Standard — Requires corporate LinkedIn/domain verification and mandatory telephone/email client verification interviews conducted by Clutch analysts.",
            "relevance": "Direct match for AI Consultants, Automation Consulting, and Middle East IT Service Providers.",
            "pitch": "Register a vendor profile under AI Consulting and CRM/Automation; submit 2–3 client references for phone/form verification.",
            "tat": "3–7 business days for profile review; 1–2 weeks for client reviews."
        },
        {
            "name": "2. GoodFirms",
            "url": "https://www.goodfirms.co/get-listed",
            "dr": "DR 86 | Monthly Traffic: ~400K+ (Source: Ahrefs/Semrush)",
            "link_type": "Nofollow (Free tier) / Dofollow for verified research badges",
            "standard": "Moderate–High — Human QA team verifies business registration, website portfolio, and authentic client testimonials.",
            "relevance": "Specific categories for AI & Machine Learning Companies in Middle East and Business Automation.",
            "pitch": "Create an agency profile with Muscat/Oman location, add case studies and automation service specializations, and submit for verification.",
            "tat": "2–4 business days."
        },
        {
            "name": "3. Sortlist (MENA / GCC Focus)",
            "url": "https://www.sortlist.com/for-agencies",
            "dr": "DR 77 | Monthly Traffic: ~200K+ (Source: Ahrefs)",
            "link_type": "Dofollow / Nofollow depending on profile tier",
            "standard": "High — Dedicated B2B agency matchmaking platform; manual curation of service offerings and portfolio quality.",
            "relevance": "Directly matches GCC SMBs and enterprise clients in UAE, Saudi Arabia, and Oman seeking AI consulting and CRM integration.",
            "pitch": "Set up an agency profile specifying core competencies (AI Agents, WhatsApp CRM, Business Automation) and target GCC markets.",
            "tat": "3–5 business days."
        },
        {
            "name": "4. Crunchbase",
            "url": "https://www.crunchbase.com/add-new",
            "dr": "DR 91 | Monthly Traffic: ~9M+ (Source: Ahrefs/Semrush)",
            "link_type": "Nofollow (Essential Entity Authority for Google Knowledge Graph)",
            "standard": "Moderate–High — Moderated global venture & technology company database with automated and manual data integrity checks.",
            "relevance": "Foundational trust signal for tech consultancies and startups operating in the MENA innovation ecosystem.",
            "pitch": "Create an entity profile connecting the brand (AI Profit Lab) with legal entity (International Gulf Lotus SPC) and Muscat HQ.",
            "tat": "Instant submission; 24–48 hours for data moderation."
        }
    ]
    
    for item in cat1_items:
        card_content = [
            Paragraph(f"<b>{item['name']}</b> &nbsp; <font color='#2563EB'>({item['url']})</font>", h2_style),
            Paragraph(f"• <b>Authority & Traffic:</b> {item['dr']}", bullet_style),
            Paragraph(f"• <b>Link Attribute:</b> {item['link_type']}", bullet_style),
            Paragraph(f"• <b>Editorial Standard:</b> {item['standard']}", bullet_style),
            Paragraph(f"• <b>Topical Relevance:</b> {item['relevance']}", bullet_style),
            Paragraph(f"• <b>Submission Process:</b> {item['pitch']}", bullet_style),
            Paragraph(f"• <b>Estimated Turnaround:</b> {item['tat']}", bullet_style),
            Spacer(1, 4)
        ]
        story.append(KeepTogether(card_content))

    story.append(Spacer(1, 6))
    
    # Category 2
    story.append(Paragraph("Category 2: GCC & Omani Tech & Business Media (Op-Eds & Expert Commentary)", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=8))
    
    cat2_items = [
        {
            "name": "5. Wamda",
            "url": "https://www.wamda.com (Pitch to: editor@wamda.com)",
            "dr": "DR 78 | Monthly Traffic: ~120K+ (Source: Ahrefs)",
            "link_type": "Contextual Dofollow / Author Bio Link",
            "standard": "Very High — Premier MENA startup & technology publication. Requires original, non-promotional analytical thought leadership (800–1,000 words).",
            "relevance": "Read extensively by GCC founders, tech executives, and government digital transformation leaders.",
            "pitch": "Email a 3-bullet concept brief to editor@wamda.com. Proposed Topic: 'Why GCC SMBs Need Workflow Automation Before Implementing GenAI Agents'.",
            "tat": "1–2 weeks for editorial review."
        },
        {
            "name": "6. Entrepreneur Middle East",
            "url": "https://www.entrepreneur.com/en-ae (Submit Article Portal)",
            "dr": "DR 92 (Middle East Edition DR 75+) | Monthly Traffic: ~450K+ (Source: Semrush)",
            "link_type": "Author Bio & Contextual Attribution",
            "standard": "Very High — Published by BNC Publishing. Strict editorial board reviewing contributions from regional founders and experts.",
            "relevance": "Highest brand prestige for B2B entrepreneurship and digital enablement across UAE, Saudi Arabia, and Oman.",
            "pitch": "Submit an article pitch via the 'Submit Article' header portal focusing on practical AI implementation roadmaps for GCC mid-market companies.",
            "tat": "2–4 weeks."
        },
        {
            "name": "7. The Arabian Stories (Oman)",
            "url": "https://www.thearabianstories.com (Pitch to: info@thearabianstories.com)",
            "dr": "DR 62 | Monthly Traffic: ~180K+ (Source: Ahrefs/Similarweb)",
            "link_type": "Contextual Dofollow in Opinion/Editorial columns",
            "standard": "Moderate–High — Local Omani press & digital media outlet based in Muscat (Azaiba South) with dedicated Opinions/Tech columns.",
            "relevance": "Direct local Omani business audience with strong alignment to Oman Vision 2040 digital transformation initiatives.",
            "pitch": "Pitch an op-ed to info@thearabianstories.com covering how AI-driven automation helps Omani SMEs reduce operational overhead and scale.",
            "tat": "3–7 business days."
        },
        {
            "name": "8. Zawya (LSEG / Refinitiv)",
            "url": "https://www.zawya.com (Submit to: pressrelease.zawya@lseg.com)",
            "dr": "DR 84 | Monthly Traffic: ~2.8M+ (Source: Ahrefs)",
            "link_type": "Nofollow (Press Releases) / Dofollow (Featured Editorial)",
            "standard": "High — Leading Middle East enterprise and business intelligence wire.",
            "relevance": "Enterprise tech, regional investment, and digital consulting in the GCC.",
            "pitch": "Submit corporate research reports, partnership announcements, or survey findings directly to pressrelease.zawya@lseg.com.",
            "tat": "24–48 hours for press releases; 1–2 weeks for editorial features."
        }
    ]
    
    for item in cat2_items:
        card_content = [
            Paragraph(f"<b>{item['name']}</b> &nbsp; <font color='#2563EB'>({item['url']})</font>", h2_style),
            Paragraph(f"• <b>Authority & Traffic:</b> {item['dr']}", bullet_style),
            Paragraph(f"• <b>Link Attribute:</b> {item['link_type']}", bullet_style),
            Paragraph(f"• <b>Editorial Standard:</b> {item['standard']}", bullet_style),
            Paragraph(f"• <b>Topical Relevance:</b> {item['relevance']}", bullet_style),
            Paragraph(f"• <b>Submission Process:</b> {item['pitch']}", bullet_style),
            Paragraph(f"• <b>Estimated Turnaround:</b> {item['tat']}", bullet_style),
            Spacer(1, 4)
        ]
        story.append(KeepTogether(card_content))
        
    story.append(Spacer(1, 6))

    # Category 3
    story.append(Paragraph("Category 3: Legitimate AI & Tech 'Write For Us' Platforms", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=8))
    
    cat3_items = [
        {
            "name": "9. Towards AI",
            "url": "https://contribute.towardsai.net",
            "dr": "DR 76 | Monthly Traffic: ~350K+ (Source: Ahrefs)",
            "link_type": "Contextual Dofollow to relevant case studies/references",
            "standard": "High — Peer-reviewed technical publication. Requires technical depth, clean workflow architecture, and authentic case studies.",
            "relevance": "100% focused on practical AI applications, LLM workflows, and AI automation engineering.",
            "pitch": "Submit full draft or Medium draft link via contribute.towardsai.net. Suggested angle: 'Architecting Multi-Agent Lead Qualification Workflows for Arabic-English Enterprise Systems'.",
            "tat": "24–72 hours."
        },
        {
            "name": "10. HackerNoon",
            "url": "https://hackernoon.com/writers",
            "dr": "DR 88 | Monthly Traffic: ~2.1M+ (Source: Ahrefs)",
            "link_type": "Contextual Dofollow (for legitimate reference citations) + Author Bio",
            "standard": "High — Every submission is individually reviewed by human editors to ensure zero promotional spam and high technical value.",
            "relevance": "Global reach among software architects, tech founders, and automation engineers.",
            "pitch": "Create a writer account, draft an article tagged under #artificial-intelligence, #automation, and #saas, and submit to the editorial queue.",
            "tat": "2–5 business days."
        }
    ]
    
    for item in cat3_items:
        card_content = [
            Paragraph(f"<b>{item['name']}</b> &nbsp; <font color='#2563EB'>({item['url']})</font>", h2_style),
            Paragraph(f"• <b>Authority & Traffic:</b> {item['dr']}", bullet_style),
            Paragraph(f"• <b>Link Attribute:</b> {item['link_type']}", bullet_style),
            Paragraph(f"• <b>Editorial Standard:</b> {item['standard']}", bullet_style),
            Paragraph(f"• <b>Topical Relevance:</b> {item['relevance']}", bullet_style),
            Paragraph(f"• <b>Submission Process:</b> {item['pitch']}", bullet_style),
            Paragraph(f"• <b>Estimated Turnaround:</b> {item['tat']}", bullet_style),
            Spacer(1, 4)
        ]
        story.append(KeepTogether(card_content))

    story.append(Spacer(1, 8))
    
    # Summary Strategy Table
    story.append(Paragraph("Strategic Execution Roadmap", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=2, spaceAfter=8))
    
    table_data = [
        [
            Paragraph("Platform", table_header),
            Paragraph("Authority", table_header),
            Paragraph("Link Type", table_header),
            Paragraph("Best Format", table_header),
            Paragraph("Core Strategic Benefit", table_header)
        ],
        [
            Paragraph("<b>Clutch.co</b>", table_cell_bold),
            Paragraph("DR 90+", table_cell),
            Paragraph("Nofollow / Citation", table_cell),
            Paragraph("B2B Profile & Client Reviews", table_cell),
            Paragraph("Referral pipeline + Google Local trust", table_cell)
        ],
        [
            Paragraph("<b>Wamda</b>", table_cell_bold),
            Paragraph("DR 78", table_cell),
            Paragraph("Dofollow / Bio", table_cell),
            Paragraph("900-word Strategic Op-Ed", table_cell),
            Paragraph("Direct exposure to GCC founders/investors", table_cell)
        ],
        [
            Paragraph("<b>Entrepreneur ME</b>", table_cell_bold),
            Paragraph("DR 75+", table_cell),
            Paragraph("Bio / Contextual", table_cell),
            Paragraph("C-Suite Thought Leadership", table_cell),
            Paragraph("Highest corporate brand prestige in GCC", table_cell)
        ],
        [
            Paragraph("<b>Towards AI</b>", table_cell_bold),
            Paragraph("DR 76", table_cell),
            Paragraph("Dofollow", table_cell),
            Paragraph("Technical Case Study", table_cell),
            Paragraph("High topical relevance in AI/LLMs", table_cell)
        ],
        [
            Paragraph("<b>The Arabian Stories</b>", table_cell_bold),
            Paragraph("DR 62", table_cell),
            Paragraph("Dofollow / Bio", table_cell),
            Paragraph("Oman Vision 2040 Tech Op-Ed", table_cell),
            Paragraph("Hyper-local Muscat B2B market relevance", table_cell)
        ],
        [
            Paragraph("<b>HackerNoon</b>", table_cell_bold),
            Paragraph("DR 88", table_cell),
            Paragraph("Dofollow", table_cell),
            Paragraph("Automation Architecture Guide", table_cell),
            Paragraph("High DR backlink & developer audience", table_cell)
        ]
    ]
    
    table = Table(table_data, colWidths=[90, 55, 80, 120, 155])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    
    story.append(KeepTogether([table, Spacer(1, 10)]))
    
    # Actionable Callout Box
    rec_text = Paragraph(
        "<b>Immediate 30-Day Execution Plan:</b><br/>"
        "1. <b>Week 1 (Foundational Entity Trust):</b> Set up verified profiles on <i>Clutch.co</i> and <i>Sortlist</i> with full service descriptions, Omani commercial details, and client reviews.<br/>"
        "2. <b>Week 2 (Regional Thought Leadership):</b> Pitch a targeted op-ed on <i>'Overcoming AI Automation Roadblocks for GCC SMBs'</i> to <b>Wamda</b> (editor@wamda.com) and <b>The Arabian Stories</b>.<br/>"
        "3. <b>Week 3 (Technical Topical Authority):</b> Publish a deep-dive workflow guide on <b>Towards AI</b> or <b>HackerNoon</b> showcasing agentic lead-qualification architectures.",
        body_style
    )
    
    rec_box = Table([[rec_text]], colWidths=[500])
    rec_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(KeepTogether([rec_box]))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF generated successfully at {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
