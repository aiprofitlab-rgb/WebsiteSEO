import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 11 * 72 - 30, "AI Profit Lab — High-Quality Organic Backlink Platforms")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(45, 11 * 72 - 35, 8.5 * 72 - 45, 11 * 72 - 35)
        
        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 45, 30, page_text)
        self.drawString(45, 30, "Confidential — aiprofitlab.io • a brand of International Gulf Lotus SPC")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(45, 40, 8.5 * 72 - 45, 40)
        
        self.restoreState()

def generate_pdf():
    pdf_path = "/Users/nahid/Desktop/Nahid/AI Profit Lab/Website/Website SEO/AI_Profit_Lab_Free_Backlink_Platforms.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Brand Palette
    PRIMARY = colors.HexColor("#0F172A")    # Slate 900
    SECONDARY = colors.HexColor("#2563EB")  # Blue 600
    ACCENT = colors.HexColor("#0D9488")     # Teal 600
    TEXT_COLOR = colors.HexColor("#334155") # Slate 700
    MUTED_TEXT = colors.HexColor("#64748B") # Slate 500
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Slate 50
    BORDER_COLOR = colors.HexColor("#CBD5E1") # Slate 300
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=SECONDARY,
        spaceAfter=8
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=TEXT_COLOR,
        spaceAfter=4
    )
    
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_COLOR
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=PRIMARY
    )
    
    table_cell_link = ParagraphStyle(
        'TableCellLink',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9.5,
        textColor=SECONDARY
    )

    story = []
    
    # Title & Metadata
    story.append(Paragraph("AI PROFIT LAB — ORGANIC BACKLINK DIRECTORY & STRATEGY", title_style))
    story.append(Paragraph("Target: <b>aiprofitlab.io</b> | Niche: AI Consultancy, Tech Agency, SME Automation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=8))
    
    # Executive Summary
    summary_text = (
        "<b>Executive Summary:</b> This document outlines 12 vetted, high-authority platforms for organic backlink acquisition, "
        "brand entity validation, and Generative Engine Optimization (GEO). All low-quality directories, link farms, and PBNs have "
        "been filtered out to prioritize genuine referral traffic, indexation speed, and domain authority."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 4))
    
    # Master Table
    story.append(Paragraph("Master Directory: Vetted High-DA Platforms", h1_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR, spaceBefore=1, spaceAfter=6))
    
    raw_data = [
        ("Hashnode", "https://hashnode.com", "DoFollow (Canonical)", "DA 88 | 2M+ visits", 
         "1. Create agency blog.<br/>2. Post AI/SME automation case studies.<br/>3. Set canonical URL to aiprofitlab.io."),
        ("Dev.to", "https://dev.to", "NoFollow / UGC", "DA 83 | 10M+ visits", 
         "1. Register founder/agency profile.<br/>2. Syndicate AI technical guides.<br/>3. Set canonical_url in frontmatter."),
        ("Hacker Noon", "https://hackernoon.com", "NoFollow / UGC", "DA 87 | 4M+ visits", 
         "1. Contributor account.<br/>2. Submit SME AI thought leadership.<br/>3. 2-4 day review for live contextual link."),
        ("Product Hunt", "https://producthunt.com", "DoFollow (Profile)", "DA 91 | 5M+ visits", 
         "1. Create maker profile.<br/>2. List AI audit tool / framework.<br/>3. Add website link in Maker profile."),
        ("SaaSHub", "https://saashub.com", "DoFollow", "DA 72 | 1.5M+ visits", 
         "1. Submit AI consulting/tools profile.<br/>2. Add service categories & URL.<br/>3. Instant live listing."),
        ("AlternativeTo", "https://alternativeto.net", "NoFollow (Referral)", "DA 81 | 8M+ visits", 
         "1. Register creator account.<br/>2. List custom AI alternative to off-the-shelf bots.<br/>3. Embed site link."),
        ("Indie Hackers", "https://indiehackers.com", "DoFollow / NoFollow", "DA 83 | 1.2M+ visits", 
         "1. Add AI Profit Lab under Products.<br/>2. Share milestone case studies linking to site."),
        ("Crunchbase", "https://crunchbase.com", "NoFollow (Entity)", "DA 91 | 12M+ visits", 
         "1. Register Organization under International Gulf Lotus SPC.<br/>2. Add website, founder, and HQ data."),
        ("GitHub", "https://github.com", "DoFollow (Org/Profile)", "DA 96 | 400M+ visits", 
         "1. Create github.com/aiprofitlab org.<br/>2. Publish free AI prompt packs / scripts.<br/>3. Link in READMEs & bio."),
        ("Medium", "https://medium.com", "NoFollow (Publications)", "DA 95 | 120M+ visits", 
         "1. Publish SME AI playbooks.<br/>2. Submit to Towards AI / The Startup.<br/>3. Embed contextual links."),
        ("Quora", "https://quora.com", "NoFollow (GEO)", "DA 93 | 300M+ visits", 
         "1. Answer top-ranked SME AI questions.<br/>2. Reference aiprofitlab.io case studies."),
        ("Reddit", "https://reddit.com", "NoFollow (AI Crawled)", "DA 97 | 1B+ visits", 
         "1. Post in r/smallbusiness, r/entrepreneur.<br/>2. Share actionable automation teardowns.")
    ]
    
    table_rows = [[
        Paragraph("Platform", table_header),
        Paragraph("URL", table_header),
        Paragraph("Link Type", table_header),
        Paragraph("DA & Traffic", table_header),
        Paragraph("Submission Method & Instructions", table_header)
    ]]
    
    for name, url, link_type, da, instructions in raw_data:
        table_rows.append([
            Paragraph(f"<b>{name}</b>", table_cell_bold),
            Paragraph(url.replace("https://", ""), table_cell_link),
            Paragraph(link_type, table_cell),
            Paragraph(da, table_cell),
            Paragraph(instructions, table_cell)
        ])
        
    master_table = Table(table_rows, colWidths=[65, 75, 80, 75, 227])
    master_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ]))
    story.append(master_table)
    story.append(Spacer(1, 10))
    
    # Strategic Recommendations Box
    rec_title = Paragraph("<b>Strategic Playbook for AI Profit Lab (Muscat, Oman)</b>", h1_style)
    rec_content = Paragraph(
        "• <b>Entity Linking & Knowledge Graph:</b> Complete Crunchbase, GitHub, and Product Hunt first. These act as authoritative seed sites confirming brand identity for Google's Knowledge Graph.<br/>"
        "• <b>Canonical Syndication:</b> When publishing on Hashnode and Dev.to, always declare the canonical link pointing to <code>aiprofitlab.io</code> to pass link equity without risking duplicate content penalties.<br/>"
        "• <b>Generative Engine Optimization (GEO):</b> Platforms like Reddit, Quora, and Medium are actively scraped by LLMs (Perplexity, ChatGPT Search, Gemini). Contextual brand mentions establish AI Profit Lab as a top citation source for SME AI queries.<br/>"
        "• <b>Legal Entity Consistency:</b> Ensure organizational submissions reference <i>International Gulf Lotus SPC</i> as the parent legal entity with <i>AI Profit Lab</i> as the brand.",
        body_style
    )
    
    rec_box = Table([[ [rec_title, Spacer(1, 3), rec_content] ]], colWidths=[522])
    rec_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#93C5FD")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(KeepTogether([rec_box]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully written to {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
