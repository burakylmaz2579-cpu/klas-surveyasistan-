import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def get_official_title(checklist_type):
    ct = str(checklist_type).upper()
    if "IOPP" in ct:
        return "EXAMINATION UNDER THE PROVISIONS OF ANNEX I TO MARPOL CONVENTION\nFOR THE INTERNATIONAL OIL POLLUTION PREVENTION CERTIFICATE"
    elif "SPP" in ct or "SEWAGE" in ct:
        return "EXAMINATION UNDER THE PROVISIONS OF ANNEX IV TO MARPOL CONVENTION\nFOR THE INTERNATIONAL SEWAGE POLLUTION PREVENTION CERTIFICATE"
    elif "IAPP" in ct or "AIR POLLUTION" in ct:
        return "EXAMINATION UNDER THE PROVISIONS OF ANNEX VI TO MARPOL CONVENTION\nFOR THE INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE"
    elif "BWM" in ct or "BALLAST" in ct:
        return "EXAMINATION UNDER THE PROVISIONS OF INTERNATIONAL CONVENTION FOR THE\nCONTROL AND MANAGEMENT OF SHIPS' BALLAST WATER AND SEDIMENTS"
    elif "LL" in ct or "LOAD LINE" in ct:
        return "EXAMINATION UNDER THE PROVISIONS OF THE INTERNATIONAL CONVENTION ON LOAD LINES"
    else:
        return f"EXAMINATION REPORT FOR {checklist_type.upper()}"

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
    
    # Custom Plain Colors for Black/White PHRS Official Draft
    LINE_COLOR = colors.HexColor("#000000")  # Plain Black
    BG_LIGHT = colors.HexColor("#f1f5f9")  # Light gray for table headers
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'OfficialTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    project_style = ParagraphStyle(
        'ProjectNo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    body_style = ParagraphStyle(
        'BodyTextPlain',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.black,
        leading=10
    )
    
    body_bold_style = ParagraphStyle(
        'BodyTextBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.black,
        leading=10
    )
    
    body_center_style = ParagraphStyle(
        'BodyTextCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=colors.black,
        alignment=TA_CENTER
    )
    
    # 1. Title & Project No
    story.append(Paragraph(get_official_title(checklist_type), title_style))
    story.append(Paragraph(f"Project No.: {project_code}", project_style))
    
    # 2. Particulars Table (Thin Black Lines)
    part_headers = [
        Paragraph("<b>Name of Ship</b>", body_center_style),
        Paragraph("<b>IMO No.</b>", body_center_style),
        Paragraph("<b>Port of Registry</b>", body_center_style),
        Paragraph("<b>Gross Tonnage</b>", body_center_style)
    ]
    
    # Extract port of registry and GRT
    port = vessel_info.get("flag", "MONROVIA")  # fallback to flag
    grt_dwt = vessel_info.get("grt_dwt", "4991 / 8000")
    grt = grt_dwt.split("/")[0].strip().replace(",", "")
    if not grt or grt == "N/A":
        grt = str(vessel_info.get("grt", "4991"))
        
    part_rows = [
        part_headers,
        [
            Paragraph(vessel_info.get("name", "N/A"), body_center_style),
            Paragraph(vessel_info.get("imo", "N/A"), body_center_style),
            Paragraph(port.upper(), body_center_style),
            Paragraph(grt, body_center_style)
        ]
    ]
    
    part_table = Table(part_rows, colWidths=[140, 120, 140, 135])
    part_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 1, LINE_COLOR),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(part_table)
    story.append(Spacer(1, 10))
    
    # 3. Instructions block
    instructions_text = """
    <b>Instructions for filling</b><br/>
    To enter in all boxes of the right-hand column one of following codes depending on the survey results:<br/>
    - Y - for "Yes" or "In compliance"<br/>
    - N - for "No" or "Not in compliance" *<br/>
    - N/A - for "Not applicable for this ship or for the survey"<br/>
    * For negative entries relevant comment / remark should be imposed by PhRS surveyor
    """
    story.append(Paragraph(instructions_text, body_style))
    story.append(Spacer(1, 10))
    
    # 4. Checklist Findings Table
    checklist_headers = [
        Paragraph("<b>Item No.</b>", body_style),
        Paragraph("<b>Description</b>", body_style),
        Paragraph("<b>Results</b>", body_center_style)
    ]
    
    table_rows = [checklist_headers]
    
    # Keep track of negative entries (deficiencies)
    deficiencies = []
    
    for item in items_data:
        item_id = item.get("id", "")
        question = item.get("item", "")
        status = item.get("status", "Y")
        deficiency_action = item.get("deficiency_action", "").strip()
        
        # Format Status Code as - Y -, - N -, - N/A -
        status_text = f"- {status} -"
        
        if status == "N":
            deficiencies.append({
                "id": item_id,
                "action": deficiency_action
            })
            
        # Draw table cell paragraphs
        table_rows.append([
            Paragraph(item_id, body_bold_style if not "." in item_id else body_style),
            Paragraph(question, body_bold_style if not "." in item_id else body_style),
            Paragraph(status_text, body_center_style)
        ])
        
    # Column widths: ID (55), Question (415), Results (65) -> Total 535
    findings_table = Table(table_rows, colWidths=[55, 415, 65])
    findings_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(findings_table)
    story.append(Spacer(1, 15))
    
    # 5. Surveyor Notes / Remarks (Only if there are negative entries)
    story.append(Paragraph("<b>SURVEYOR’S NOTES</b>", body_bold_style))
    story.append(Paragraph("For negative entries, major repairs and additional information, if any, described in detail. (Use attachment if necessary)", body_style))
    story.append(Spacer(1, 5))
    
    notes_headers = [
        Paragraph("<b>REF No.</b>", body_center_style),
        Paragraph("<b>TYPE (C/R)</b>", body_center_style),
        Paragraph("<b>COMMENTS (C) / REMARKS (R)</b>", body_style)
    ]
    
    notes_rows = [notes_headers]
    if deficiencies:
        for d in deficiencies:
            notes_rows.append([
                Paragraph(d["id"], body_center_style),
                Paragraph("C", body_center_style),
                Paragraph(d["action"], body_style)
            ])
    else:
        # Empty row if no deficiencies
        notes_rows.append([
            Paragraph("", body_center_style),
            Paragraph("", body_center_style),
            Paragraph("No deficiencies or remarks noted.", body_style)
        ])
        
    notes_table = Table(notes_rows, colWidths=[60, 60, 415])
    notes_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(notes_table)
    story.append(Spacer(1, 25))
    
    # 6. Date & Signatures Section
    story.append(Paragraph(f"Survey Date: {survey_date_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Surveyor Name: {surveyor_name}", body_bold_style))
    story.append(Spacer(1, 15))
    
    sig_data = [
        [
            Paragraph("___________________________<br/>PHRS Surveyor Representative", body_center_style),
            Paragraph("___________________________<br/>Vessel Master / Deck Officer", body_center_style)
        ]
    ]
    
    sig_table = Table(sig_data, colWidths=[260, 275])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 15),
    ]))
    story.append(sig_table)
    
    # Build document
    doc.build(story)
