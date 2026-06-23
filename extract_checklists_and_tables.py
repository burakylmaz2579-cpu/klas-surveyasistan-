import os
import zipfile
import re
import xml.etree.ElementTree as ET
import json

directory = r"C:\Users\LIVAPC8\Desktop\VESSELS & REPORT\+++PHRS TUM REPORT+++"
output_json = r"C:\Users\LIVAPC8\Desktop\KODLAR\YeniDeneyi_V2\checklists_extracted.json"

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def clean_text(text):
    if not text:
        return ""
    # Remove multiple spaces, newlines, and non-breaking spaces
    text = text.replace("\xa0", " ").replace("\u2002", " ").replace("\u2003", " ")
    return " ".join(str(text).split())

def parse_docx_tables(filepath):
    if not zipfile.is_zipfile(filepath):
        return []
    try:
        with zipfile.ZipFile(filepath) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            tables_data = []
            for tbl in root.findall('.//w:tbl', ns):
                rows_data = []
                for tr in tbl.findall('.//w:tr', ns):
                    cells_data = []
                    for tc in tr.findall('.//w:tc', ns):
                        text_parts = [t.text for t in tc.findall('.//w:t', ns) if t.text]
                        cells_data.append("".join(text_parts).strip())
                    rows_data.append(cells_data)
                tables_data.append(rows_data)
            return tables_data
    except Exception as e:
        print(f"Error reading zip XML from {filepath}: {e}")
        return []

def extract_checklist_and_tables(tables):
    checklist_items = []
    data_tables = []
    metadata_fields = set()
    
    standard_fields = {
        "name of ship", "name of vessel", "gemi adi", "gemi adı",
        "imo no.", "imo number", "imo no", "imo numara",
        "gross tonnage", "gross tonnage (grt)", "gt", "grt", "rt",
        "deadweight", "dwt", "deadweight (dwt)", "mt",
        "port of registry", "baglama limani", "flag", "bayrak",
        "vessel type", "gemi tipi", "vessel_type",
        "call sign", "c/sign", "class", "classification"
    }
    
    particulars_kws = ["name of ship", "imo no", "call sign", "port of registry", "gross tonnage", "deadweight"]
    
    for tbl_idx, table in enumerate(tables):
        if not table or len(table) == 0:
            continue
            
        # 1. Skip if it is a particulars table
        is_particulars = False
        for row in table[:2]:
            row_lower = [c.lower() for c in row]
            if any(any(kw in cell for kw in particulars_kws) for cell in row_lower):
                is_particulars = True
                break
        if is_particulars:
            # Extract metadata fields from particulars table
            for row in table:
                for cell in row:
                    cell_clean = clean_text(cell)
                    if cell_clean and len(cell_clean) < 50:
                        field_name = cell_clean.replace(":", "").strip()
                        if len(field_name) > 2 and field_name.lower() not in standard_fields:
                            if not re.match(r'^\d+$', field_name) and not field_name.startswith("-"):
                                metadata_fields.add(field_name)
            continue
            
        # 2. Check if it is a checklist or data table
        is_checklist = False
        first_col_numeric = 0
        
        # Determine Title and Headers
        title = ""
        headers = []
        start_row = 0
        
        # If the first row is a single cell, it is the title
        if len(table[0]) == 1 or (len(table) > 1 and len(set(table[0])) == 1):
            title = clean_text(table[0][0])
            start_row = 1
            
        if start_row < len(table):
            headers = [clean_text(c) for c in table[start_row]]
            start_row += 1
            
        headers_lower = [h.lower() for h in headers]
        if any(x in headers_lower for x in ["condition", "remarks", "yes", "no", "n/a", "uygun", "uygunsuz"]):
            is_checklist = True
            
        # Fallback check on first column values
        total_rows = len(table) - start_row
        for r_idx in range(start_row, len(table)):
            row = table[r_idx]
            if len(row) > 0:
                val = clean_text(row[0])
                if val and (re.match(r'^\d+(\.\d+)*\.?$', val) or re.match(r'^[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)*\.?$', val)):
                    first_col_numeric += 1
                    
        if total_rows > 0 and (first_col_numeric / total_rows) >= 0.3:
            is_checklist = True
            
        # Refinement: if it has very few columns (e.g. 2 columns) and contains specific headers, it is a checklist
        if len(headers) == 2 and any(x in headers_lower for x in ["item", "description", "action", "status"]):
            is_checklist = True
            
        # Special check: if title or headers indicate equipment data entry (like "TEST OF LIFTING CAPACITY" or "BOILER" or "PUMPS"), it is a Data Table
        equipment_kws = ["test of lifting", "boiler", "pump", "compressor", "air bottle", "purifier", "battery", "steering", "engine", "generator", "windlass", "lifeboat", "liferaft", "apparatus"]
        if any(kw in title.lower() for kw in equipment_kws) or any(any(kw in h.lower() for kw in equipment_kws) for h in headers):
            is_checklist = False
            
        if is_checklist:
            # Extract checklist items
            for r_idx in range(start_row, len(table)):
                row = [clean_text(c) for c in table[r_idx]]
                if len(row) < 2:
                    continue
                item_no = row[0]
                desc = row[1]
                if not desc:
                    desc = item_no
                    item_no = f"{r_idx}"
                if desc.lower() in ["description", "description of item", "guidelines", "item"]:
                    continue
                
                status = "Y"
                if len(row) >= 3:
                    last_val = row[-1].upper()
                    if "N/A" in last_val or "NA" in last_val:
                        status = "N/A"
                    elif "N" in last_val:
                        status = "N"
                checklist_items.append({
                    "item_no": item_no,
                    "description": desc,
                    "default_status": status
                })
        else:
            # Extract as structured data table
            rows = []
            for r_idx in range(start_row, len(table)):
                row = [clean_text(c) for c in table[r_idx]]
                # Ignore completely empty rows
                if any(row):
                    rows.append(row)
            if headers or rows:
                data_tables.append({
                    "title": title if title else f"Equipment Table {len(data_tables)+1}",
                    "headers": headers,
                    "rows": rows
                })
                
    return checklist_items, data_tables, list(metadata_fields)

def main():
    all_checklists = {}
    
    # We map files to a clean category key
    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)
        if not os.path.isfile(filepath):
            continue
        if not zipfile.is_zipfile(filepath):
            print(f"Skipping non-zip file: {file}")
            continue
            
        # Determine template key and prefix from filename
        prefix = ""
        if "ISM_COMPANY" in file:
            prefix = "ISM COMPANY - "
        elif "ISM_SHIP" in file:
            prefix = "ISM SHIP - "
        elif "MLC_COMPANY" in file:
            prefix = "MLC COMPANY - "
        elif "MLC_SHIP" in file:
            prefix = "MLC SHIP - "
        elif "ISPS" in file:
            prefix = "ISPS - "
        elif "CLASSIFICATION" in file:
            prefix = "CLASS - "
        elif "STATUTORY" in file:
            prefix = "STATUTORY - "
        elif "CICA" in file:
            prefix = "CICA - "
        elif "OTHERS" in file:
            prefix = "OTHERS - "
            
        clean_name = file.replace("SURVEY REPORTS_INTERNATIONAL_STATUTORY_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_CLASSIFICATION_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_ISM_COMPANY_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_ISM_SHIP_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_ISPS_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_MLC_SHIP_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_MLC_COMPANY_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_OTHERS_", "")
        clean_name = clean_name.replace("SURVEY REPORTS_INTERNATIONAL_CICA_", "")
        
        clean_name = re.sub(r'\.docx.*|\.doc.*|\.DOC.*|\.docx$', '', clean_name, flags=re.IGNORECASE).strip()
        clean_name = re.sub(r'\(\d+\)', '', clean_name).strip()
        
        if prefix:
            clean_name = prefix + clean_name
            
        if not clean_name:
            continue
            
        print(f"Parsing: {file[:50]}... -> Key: {clean_name}")
        tables = parse_docx_tables(filepath)
        items, data_tbls, metadata = extract_checklist_and_tables(tables)
        
        # Format matching original structure
        all_checklists[clean_name] = {
            "items": [
                {"id": x["item_no"], "item": x["description"], "rule": "PHRS Reg", "default_status": x["default_status"]}
                for x in items
            ],
            "metadata_fields": metadata,
            "tables": data_tbls
        }
        
    # Write to output file
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_checklists, f, indent=2, ensure_ascii=False)
        
    print(f"Extraction completed! Total templates: {len(all_checklists)}")

if __name__ == "__main__":
    main()
