import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_checklist_pdf(filepath, vessel_info, project_code, checklist_type, items_data, surveyor_name, survey_date_str):
    # Setup document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom colors
    PRIMARY_COLOR = colors.HexColor("#991b1b")  # Crimson Red
    SECONDARY_COLOR = colors.HexColor("#1e293b")  # Dark Slate
    TEXT_COLOR = colors.HexColor("#334155")
    LINE_COLOR = colors.HexColor("#cbd5e1")
    BG_LIGHT = colors.HexColor("#f8fafc")
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=SECONDARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=25
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=SECONDARY_COLOR,
        spaceBefore=15,
        spaceAfter=8,
        borderPadding=4
    )
    
    label_style = ParagraphStyle(
        'LabelText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=SECONDARY_COLOR
    )
    
    value_style = ParagraphStyle(
        'ValueText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=TEXT_COLOR
    )
    
    th_style = ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_LEFT
    )
    
    th_center_style = ParagraphStyle(
        'TableHeaderCenterText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    td_style = ParagraphStyle(
        'TableBodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=TEXT_COLOR,
        alignment=TA_LEFT
    )
    
    td_bold_style = ParagraphStyle(
        'TableBodyBoldText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        textColor=SECONDARY_COLOR,
        alignment=TA_LEFT
    )
    
    td_center_style = ParagraphStyle(
        'TableBodyCenterText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=TEXT_COLOR,
        alignment=TA_CENTER
    )
    
    status_yes_style = ParagraphStyle(
        'StatusYes',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#16a34a"),  # Green
        alignment=TA_CENTER
    )
    
    status_no_style = ParagraphStyle(
        'StatusNo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#dc2626"),  # Red
        alignment=TA_CENTER
    )
    
    status_na_style = ParagraphStyle(
        'StatusNA',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor("#475569"),  # Slate / Gray
        alignment=TA_CENTER
    )
    
    deficiency_text_style = ParagraphStyle(
        'DeficiencyText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor("#b91c1c")  # Crimson warning text
    )
    
    # 1. Header Banner
    story.append(Paragraph("PHRS STATUTORY SURVEYS PORTAL", title_style))
    story.append(Paragraph(f"SURVEY CHECKLIST REPORT - {checklist_type.upper()}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 2. Vessel & Audit Particulars Table
    story.append(Paragraph("Vessel & Audit Particulars", section_style))
    
    particulars_data = [
        [
            Paragraph("Vessel Name:", label_style), Paragraph(vessel_info.get("name", "N/A"), value_style),
            Paragraph("Project Code:", label_style), Paragraph(project_code, value_style)
        ],
        [
            Paragraph("IMO Number:", label_style), Paragraph(vessel_info.get("imo", "N/A"), value_style),
            Paragraph("Surveyor:", label_style), Paragraph(surveyor_name, value_style)
        ],
        [
            Paragraph("Vessel Type:", label_style), Paragraph(vessel_info.get("vessel_type", "N/A"), value_style),
            Paragraph("Survey Date:", label_style), Paragraph(survey_date_str, value_style)
        ],
        [
            Paragraph("GRT / DWT:", label_style), Paragraph(vessel_info.get("grt_dwt", "N/A"), value_style),
            Paragraph("Report Type:", label_style), Paragraph(checklist_type, value_style)
        ]
    ]
    
    particulars_table = Table(particulars_data, colWidths=[100, 160, 100, 175])
    particulars_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, LINE_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
    ]))
    
    story.append(particulars_table)
    story.append(Spacer(1, 20))
    
    # 3. Checklist Findings Table
    story.append(Paragraph("Survey Items & Findings", section_style))
    
    # Table headers
    checklist_headers = [
        Paragraph("ID", th_center_style),
        Paragraph("Checklist Question / Description", th_style),
        Paragraph("Status", th_center_style),
        Paragraph("Rule Reference", th_style)
    ]
    
    table_rows = [checklist_headers]
    
    for item in items_data:
        item_id = item.get("id", "")
        question = item.get("item", "")
        status = item.get("status", "Y")
        rule = item.get("rule", "")
        deficiency_action = item.get("deficiency_action", "").strip()
        
        # Format Status visual indicator
        if status == "Y":
            status_p = Paragraph("[ ✔ ] YES", status_yes_style)
        elif status == "N":
            status_p = Paragraph("[ ✘ ] NO", status_no_style)
        else:
            status_p = Paragraph("[ — ] N/A", status_na_style)
            
        # Question paragraph can include deficiency text underneath
        q_elements = [Paragraph(question, td_style)]
        if status == "N" and deficiency_action:
            q_elements.append(Spacer(1, 3))
            q_elements.append(Paragraph(f"<b>Deficiency Action:</b> {deficiency_action}", deficiency_text_style))
            
        table_rows.append([
            Paragraph(item_id, td_bold_style),
            q_elements,
            status_p,
            Paragraph(rule, td_bold_style)
        ])
        
    # Column widths: ID (45), Question (340), Status (65), Rule (85) -> Total 535 (matches A4 printable width)
    findings_table = Table(table_rows, colWidths=[45, 340, 65, 85])
    findings_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY_COLOR),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
    ]))
    
    story.append(findings_table)
    story.append(Spacer(1, 35))
    
    # 4. Signatures Section
    sig_data = [
        [
            Paragraph("<b>Surveyor Signature</b>", td_center_style),
            Paragraph("<b>Master / Ship Representative</b>", td_center_style)
        ],
        [
            Spacer(1, 40),
            Spacer(1, 40)
        ],
        [
            Paragraph("___________________________<br/>PHRS Surveyor Representative", td_center_style),
            Paragraph("___________________________<br/>Vessel Master / Deck Officer", td_center_style)
        ]
    ]
    
    sig_table = Table(sig_data, colWidths=[260, 275])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    
    story.append(sig_table)
    
    # Build document
    doc.build(story)
