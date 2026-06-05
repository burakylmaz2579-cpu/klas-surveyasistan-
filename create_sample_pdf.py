import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sample_pdf(filename="sample_survey_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2b6cb0'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6
    )
    
    def_style = ParagraphStyle(
        'DeficiencyText',
        parent=body_style,
        textColor=colors.HexColor('#c53030')
    )

    story.append(Paragraph("CLASS SURVEY & INSPECTION REPORT (FORM: CL_0200)", title_style))
    story.append(Paragraph("<b>Document Reference:</b> SR-2026-0601-A<br/><b>Survey Type:</b> Annual Safety Equipment Survey", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. VESSEL PARTICULAR DETAILS", h2_style))
    
    vessel_data = [
        [Paragraph("<b>Vessel Name:</b>", body_style), Paragraph("MV OCEAN VOYAGER", body_style),
         Paragraph("<b>IMO Number:</b>", body_style), Paragraph("9876543", body_style)],
        [Paragraph("<b>Vessel Type:</b>", body_style), Paragraph("Bulk Carrier (Dökme Yük)", body_style),
         Paragraph("<b>Gross Tonnage (GRT):</b>", body_style), Paragraph("38,500 RT", body_style)],
        [Paragraph("<b>Deadweight (DWT):</b>", body_style), Paragraph("64,200 MT", body_style),
         Paragraph("<b>Flag State:</b>", body_style), Paragraph("Panama", body_style)],
        [Paragraph("<b>Port of Registry:</b>", body_style), Paragraph("Panama City", body_style),
         Paragraph("<b>Classification Society:</b>", body_style), Paragraph("Global Class (GC)", body_style)]
    ]
    
    t = Table(vessel_data, colWidths=[120, 130, 110, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f7fafc')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("2. LIFE SAVING APPLIANCES (SOLAS CHAPTER III)", h2_style))
    story.append(Paragraph("Inspections and tests carried out on Lifeboats, Liferafts, Lifebuoys, and Personal Life-Saving Appliances.", body_style))
    
    lsa_data = [
        [Paragraph("<b>Inspection Item</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Surveyor Remarks / Deficiencies Found</b>", body_style)],
        [Paragraph("Lifeboats No.1 & No.2 structural condition", body_style), Paragraph("Satisfactory", body_style), Paragraph("Hull and seats in good condition.", body_style)],
        [Paragraph("Lifeboat No.1 Launching Arrangement & Limit Switches", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> Lifeboat No.1 release mechanism limit switch has not been tested during the last quarterly drill. Limit switch lever was found slightly corroded and stiff to operate.", def_style)],
        [Paragraph("Inflatable Liferafts hydrostatic release units (HRU)", body_style), Paragraph("Satisfactory", body_style), Paragraph("HRUs serviced and valid until November 2026.", body_style)],
        [Paragraph("Lifebuoys and attachments", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> Three (3) lifebuoys located on the bridge wings and aft deck are missing the required retro-reflective tape. One lifebuoy self-igniting light battery is expired since February 2026.", def_style)],
        [Paragraph("Lifejackets & Immersion Suits", body_style), Paragraph("Satisfactory", body_style), Paragraph("All lifejackets checked. Lights are functional.", body_style)]
    ]
    
    t_lsa = Table(lsa_data, colWidths=[150, 80, 270])
    t_lsa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_lsa)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("3. FIRE SAFETY & FIRE FIGHTING EQUIPMENT (SOLAS CHAPTER II-2)", h2_style))
    
    fire_data = [
        [Paragraph("<b>Inspection Item</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Surveyor Remarks / Deficiencies Found</b>", body_style)],
        [Paragraph("Fire Main and Hydrants", body_style), Paragraph("Satisfactory", body_style), Paragraph("Pressure test carried out. Fire main is in sound condition.", body_style)],
        [Paragraph("Portable Fire Extinguishers (Dry Powder & CO2)", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> Portable fire extinguishers in the engine room and accommodation spaces were last serviced on 2024-03-15. The annual service and calibration/hydrostatic testing is overdue by 3 months.", def_style)],
        [Paragraph("Fixed Fire Extinguishing System (CO2 Room)", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> CO2 room entrance safety warning signs are degraded. The glass of the emergency key box is broken, leaving the key exposed to unauthorized access.", def_style)],
        [Paragraph("Fire dampers and ventilation shutdowns", body_style), Paragraph("Satisfactory", body_style), Paragraph("Tested and found fully operational.", body_style)]
    ]
    
    t_fire = Table(fire_data, colWidths=[150, 80, 270])
    t_fire.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_fire)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("4. POLLUTION PREVENTION (MARPOL CONVENTION)", h2_style))
    
    marpol_data = [
        [Paragraph("<b>Inspection Item</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Surveyor Remarks / Deficiencies Found</b>", body_style)],
        [Paragraph("Oily Water Separator (OWS) & 15ppm Alarm", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> OWS 15ppm alarm monitor is fully operational under test. However, the official calibration certificate for the 15ppm monitor has expired on 2026-02-10.", def_style)],
        [Paragraph("Oil Record Book (ORB) Part I", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> Oil Record Book Part I checked. Missing entry for bilge water discharge to shore reception facilities on 2026-05-15. Discrepancy observed between actual bilge holding tank level and log entry.", def_style)],
        [Paragraph("SOPEP (Shipboard Oil Pollution Emergency Plan)", body_style), Paragraph("Satisfactory", body_style), Paragraph("SOPEP locker fully stocked. Contact list is updated.", body_style)]
    ]
    
    t_marpol = Table(marpol_data, colWidths=[150, 80, 270])
    t_marpol.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_marpol)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("5. RADIO & SAFETY OF NAVIGATION (SOLAS CHAPTER IV & V)", h2_style))
    
    nav_data = [
        [Paragraph("<b>Inspection Item</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Surveyor Remarks / Deficiencies Found</b>", body_style)],
        [Paragraph("Emergency Position Indicating Radio Beacon (EPIRB)", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> EPIRB battery expiration date is 2026-04-30. The battery is EXPIRED and must be replaced immediately.", def_style)],
        [Paragraph("Magnetic Compass & Deviation Card", body_style), Paragraph("DEFICIENCY", def_style), Paragraph("<b>[DEFICIENCY]</b> Magnetic compass deviation card dates back to 2023. Real-time deviation observed on heading 090 exceeds 5 degrees, which is outside acceptable limits without an updated correction table.", def_style)],
        [Paragraph("VHF DSC and MF/HF DSC Radiotelephony", body_style), Paragraph("Satisfactory", body_style), Paragraph("Radio test carried out with coastal stations. Communication is clear.", body_style)]
    ]
    
    t_nav = Table(nav_data, colWidths=[150, 80, 270])
    t_nav.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#edf2f7')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_nav)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>CONCLUSION & SIGN-OFF:</b> The vessel has major outstanding deficiencies related to safety equipment calibration, SOLAS life-saving arrangements, and MARPOL logbook records. Immediate corrective action is required for compliance.", body_style))
    
    doc.build(story)

if __name__ == "__main__":
    generate_sample_pdf()
