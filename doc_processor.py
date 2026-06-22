import pdfplumber
import fitz  # PyMuPDF
import re
import os
from datetime import datetime
from rules_engine import REGULATIONS_DB, get_rule_by_keyword, check_rule_applicability

CONTRADICTION_KEYWORDS = [
    "deficiency", "defect", "expired", "overdue", "broken", "corroded", 
    "missing", "leak", "damaged", "fail", "not tested", "stiff", 
    "unauthorized", "degraded", "not functional", "inoperable",
    "hata", "eksik", "hasarlı", "bozuk", "çürük", "paslı", "uygunsuz",
    "tarihi geçmiş", "çalışmıyor", "bulunamadı", "kaçırılmış"
]

class SurveyDocumentProcessor:
    def __init__(self, file_path_or_bytes, filename=None):
        self.file_path_or_bytes = file_path_or_bytes
        self.filename = filename
        self.raw_text = ""
        self.pages_count = 0
        self.tables = []
        self.vessel_info = {}
        self.doc_type = "checklist"  # default
        self.certificate_info = {}
        
        self._load_document()
        self._classify_document()

    def _load_document(self):
        if isinstance(self.file_path_or_bytes, bytes):
            self.doc = fitz.open(stream=self.file_path_or_bytes, filetype="pdf")
        else:
            self.doc = fitz.open(self.file_path_or_bytes)
            
        self.pages_count = len(self.doc)
        text_list = []
        for page in self.doc:
            text_list.append(page.get_text())
        self.raw_text = "\n".join(text_list)
        
        self._extract_vessel_info()
        
        if isinstance(self.file_path_or_bytes, bytes):
            from io import BytesIO
            with BytesIO(self.file_path_or_bytes) as stream:
                with pdfplumber.open(stream) as pdf:
                    self._extract_tables(pdf)
        else:
            with pdfplumber.open(self.file_path_or_bytes) as pdf:
                self._extract_tables(pdf)

    def _classify_document(self):
        text_lower = self.raw_text.lower()
        
        # Fallback for scanned/non-searchable PDFs based on filename
        filename = self.filename
        if not filename and not isinstance(self.file_path_or_bytes, bytes):
            filename = os.path.basename(self.file_path_or_bytes)
            
        if filename:
            filename = filename.lower()
            
        if len(self.raw_text.strip()) < 100 and filename:
            if "_ft" in filename or "cert" in filename or "certificate" in filename:
                self.doc_type = "certificate"
                self._extract_certificate_info()
            else:
                self.doc_type = "checklist"
            return
            
        # Check first 800 characters for explicit certificate and checklist keywords
        first_800 = text_lower[:800]
        
        cert_kws = [
            "certificate", "sertifika", "sertifikası", "certify", "certifies", 
            "document of compliance", "particulars of ship", "this is to certify", 
            "issued under the authority", "attest", "attestation", "safety management certificate",
            "record of equipment"
        ]
        checklist_kws = [
            "examination", "checklist", "check list", "kontrol listesi", 
            "survey report", "inspection report", "sörvey raporu", "denetim raporu"
        ]
        
        first_cert_idx = -1
        for kw in cert_kws:
            idx = first_800.find(kw)
            if idx != -1:
                if first_cert_idx == -1 or idx < first_cert_idx:
                    first_cert_idx = idx
                    
        first_checklist_idx = -1
        for kw in checklist_kws:
            idx = first_800.find(kw)
            if idx != -1:
                if first_checklist_idx == -1 or idx < first_checklist_idx:
                    first_checklist_idx = idx
                    
        # Check for status codes inside the text
        has_text_status_codes = (
            "- y -" in text_lower or "- n -" in text_lower or "- n/a -" in text_lower or
            "-y-" in text_lower or "-n-" in text_lower or "-n/a-" in text_lower
        )
        
        checkbox_count = self.raw_text.count("☐") + self.raw_text.count("☒") + self.raw_text.count("☑")
        checkbox_count += len(re.findall(r'\[\s*[xX✓✔]\s*\]', self.raw_text))
        checkbox_count += len(re.findall(r'\[\s*\]', self.raw_text))
        
        # Decide type
        if first_cert_idx != -1:
            if first_checklist_idx == -1 or first_cert_idx < first_checklist_idx:
                self.doc_type = "certificate"
            else:
                self.doc_type = "checklist"
        elif has_text_status_codes or checkbox_count >= 10:
            self.doc_type = "checklist"
        else:
            # Fallback
            if "certificate" in text_lower or "sertifika" in text_lower:
                self.doc_type = "certificate"
            else:
                self.doc_type = "checklist"
                
        if self.doc_type == "certificate":
            self._extract_certificate_info()

    def _extract_vessel_info(self):
        vessel_name_match = re.search(r"Vessel Name\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
        if not vessel_name_match:
            vessel_name_match = re.search(r"Gemi Adı\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
            
        imo_match = re.search(r"IMO Number\s*:\s*([^\n\r\s]+)", self.raw_text, re.IGNORECASE)
        if not imo_match:
            imo_match = re.search(r"IMO No\s*:\s*([^\n\r\s]+)", self.raw_text, re.IGNORECASE)
            
        grt_match = re.search(r"Gross Tonnage\s*\(GRT\)\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
        if not grt_match:
            grt_match = re.search(r"GT\s*/\s*DWT\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
            
        vessel_type_match = re.search(r"Vessel Type\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
        if not vessel_type_match:
            vessel_type_match = re.search(r"Gemi Türü\s*:\s*([^\n\r]+)", self.raw_text, re.IGNORECASE)
            
        self.vessel_info = {
            "name": vessel_name_match.group(1).strip() if vessel_name_match else "MV OCEAN VOYAGER",
            "imo": imo_match.group(1).strip() if imo_match else "9876543",
            "grt_dwt": grt_match.group(1).strip() if grt_match else "38,500 / 64,200",
            "vessel_type": vessel_type_match.group(1).strip() if vessel_type_match else "Bulk Carrier (Dökme Yük)"
        }

    def _extract_certificate_info(self):
        text = self.raw_text
        text_upper = text.upper()
        text_lower = text.lower()
        
        # Determine Certificate Type
        cert_type = "Bilinmeyen Sertifika"
        if "safety equipment" in text_lower or "safel" in text_lower:
            cert_type = "Cargo Ship Safety Equipment Certificate"
        elif "safety construction" in text_lower or "safcon" in text_lower:
            cert_type = "Cargo Ship Safety Construction Certificate"
        elif "safety radio" in text_lower or "safrad" in text_lower:
            cert_type = "Cargo Ship Safety Radio Certificate"
        elif "load line" in text_lower:
            cert_type = "International Load Line Certificate"
        elif "iopp" in text_lower or "prevention of oil pollution" in text_lower:
            cert_type = "International Oil Pollution Prevention (IOPP) Certificate"
        elif "iapp" in text_lower or "prevention of air pollution" in text_lower:
            cert_type = "International Air Pollution Prevention (IAPP) Certificate"
        elif "ballast water" in text_lower or "bwm" in text_lower:
            cert_type = "International Ballast Water Management Certificate"
        elif "anti-fouling" in text_lower or "afs" in text_lower:
            cert_type = "International Anti-Fouling System Certificate"
        elif "sewage" in text_lower:
            cert_type = "International Sewage Pollution Prevention Certificate"
        elif "document of compliance" in text_lower or "doc" in text_lower:
            cert_type = "Document of Compliance (DOC)"
        elif "safety management certificate" in text_lower or "smc" in text_lower:
            cert_type = "Safety Management Certificate (SMC)"
        elif "tonnage" in text_lower:
            cert_type = "International Tonnage Certificate"
        elif "classification certificate" in text_lower or "class certificate" in text_lower:
            cert_type = "Classification Certificate"

        # 1. DB-Assisted Extraction
        found_name = None
        found_imo = None
        found_grt = None
        found_dwt = None
        
        try:
            import vessel_db as db
            conn = db.get_db_connection()
            c = conn.cursor()
            c.execute("SELECT imo, name, grt, dwt FROM vessels")
            db_rows = c.fetchall()
            conn.close()
            
            # Search for known IMOs first (exact 7-digit check in raw text)
            for db_imo, db_name, db_grt, db_dwt in db_rows:
                if db_imo and len(db_imo) == 7 and db_imo in text_upper:
                    found_imo = db_imo
                    found_name = db_name
                    found_grt = str(db_grt)
                    found_dwt = str(db_dwt)
                    break
                    
            # If IMO not matched, search for known Names (matching word boundaries)
            if not found_name:
                db_rows_sorted = sorted(db_rows, key=lambda x: len(x[1]), reverse=True)
                for db_imo, db_name, db_grt, db_dwt in db_rows_sorted:
                    if len(db_name) > 3:
                        pattern = r'\b' + re.escape(db_name) + r'\b'
                        if re.search(pattern, text_upper):
                            found_name = db_name
                            found_imo = db_imo
                            found_grt = str(db_grt)
                            found_dwt = str(db_dwt)
                            break
        except Exception as e:
            print("DB-assisted extraction error:", e)

        # 2. Fallbacks for completely new vessels
        vessel_name = found_name
        if not vessel_name:
            v_match = re.search(r'(?:name of ship|name of vessel|gemi adı|gemi adi)\s*[:\s]\s*([^\n\r]+)', text_lower)
            if v_match:
                val = v_match.group(1).strip()
                val = re.split(r'\b(imo|port|distinctive|official|call|gross|gt|dwt|flag|class|type)\b', val)[0].strip()
                val = re.sub(r'[^a-zA-Z0-9\s\-_]', '', val).strip().upper()
                if val and val not in ["IMO", "IMO NO", "IMO NUMBER"]:
                    vessel_name = val
            if not vessel_name:
                lines = text.splitlines()
                for line in lines[:15]:
                    if any(x in line.upper() for x in ["M/V", "M.V.", "M/T", "M.T."]):
                        vessel_name = line.strip().upper()
                        break
                        
        imo = found_imo
        if not imo:
            imo_match = re.search(r'(?:imo number|imo no|imo|ımo)\s*:?\s*(\d{7})', text_lower)
            if imo_match:
                imo = imo_match.group(1).strip()
            else:
                digit_matches = re.findall(r'\b\d{7}\b', text)
                if digit_matches:
                    imo = digit_matches[0]
                    
        grt = found_grt
        if not grt:
            grt_match = re.search(r'(?:gross tonnage|gross weight|grt|gt)\s*:?\s*([\d\s,\.]+)', text_lower)
            if grt_match:
                grt = grt_match.group(1).strip()
                grt = re.sub(r'[^\d]', '', grt.split('.')[0].split(',')[0])
                
        dwt = found_dwt
        if not dwt:
            dwt_match = re.search(r'(?:deadweight|dwt)\s*:?\s*([\d\s,\.]+)', text_lower)
            if dwt_match:
                dwt = dwt_match.group(1).strip()
                dwt = re.sub(r'[^\d]', '', dwt.split('.')[0].split(',')[0])
            
        expiry_date = ""
        exp_match = re.search(r'(?:expiry date|expires on|valid until|valid to|gecerlilik tarihi|until|bitis tarihi|bitiş tarihi)\s*:?\s*([\d\-\/a-zA-Z\s]{8,15})', text_lower)
        if exp_match:
            expiry_date = exp_match.group(1).strip()
        else:
            date_matches = re.findall(r'\b\d{2}[/\-]\d{2}[/\-]\d{4}\b', text)
            if len(date_matches) >= 2:
                expiry_date = date_matches[-1]
            elif len(date_matches) == 1:
                expiry_date = date_matches[0]
                
        issue_date = ""
        iss_match = re.search(r'(?:date of issue|issued at|issued on|düzenleme tarihi|duzenleme tarihi)\s*:?\s*([\d\-\/a-zA-Z\s]{8,15})', text_lower)
        if iss_match:
            issue_date = iss_match.group(1).strip()
            
        cert_number = ""
        num_match = re.search(r'(?:certificate number|cert\.? no|sertifika no|certificate no)\s*:?\s*([a-zA-Z0-9\-_]+)', text_lower)
        if num_match:
            cert_number = num_match.group(1).strip()
            
        # Check if OWS is fitted or not based on text keywords
        ows_fitted = True
        text_clean_spaces = re.sub(r'\s+', ' ', text_lower)
        if any(x in text_clean_spaces for x in [
            "15 ppm bilge separator is not fitted", 
            "15 ppm bilge separator not fitted", 
            "oil filtering equipment is not fitted", 
            "filtering equipment not fitted", 
            "filtering equipment is not fitted",
            "oily water separator is not fitted",
            "oily water separator not fitted",
            "ows is not fitted",
            "ows not fitted"
        ]):
            ows_fitted = False
        else:
            # check regex for "15 ppm bilge separator" followed by "not fitted", "exempt", or "---"
            ows_match = re.search(r'15\s*ppm\s*(?:bilge|oil)?\s*(?:separator|filtering|equipment)[^.]{0,100}(not fitted|not installed|exemp|\-\-\-|n/a)', text_lower)
            if ows_match:
                ows_fitted = False
                
        # Check if BWMS is fitted (D-2 performance standard)
        bwms_fitted = True
        if "ballast" in text_lower or "bwm" in text_lower:
            if "d-2" in text_lower and any(x in text_lower for x in ["not fitted", "not approved", "not installed", "not applicable"]):
                bwms_fitted = False
            elif "d-1" in text_lower and "d-2" not in text_lower:
                bwms_fitted = False

        self.certificate_info = {
            "cert_type": cert_type,
            "cert_number": cert_number if cert_number else "N/A",
            "vessel_name": vessel_name if vessel_name else "N/A",
            "imo": imo if imo else "N/A",
            "grt": grt if grt else "N/A",
            "dwt": dwt if dwt else "N/A",
            "issue_date": issue_date if issue_date else "N/A",
            "expiry_date": expiry_date if expiry_date else "N/A",
            "ows_fitted": ows_fitted,
            "bwms_fitted": bwms_fitted
        }

    def _resolve_cell_text_with_ticks(self, cell_text, cell_bbox, page_ticks):
        if not page_ticks:
            return cell_text
            
        cx0, cy0, cx1, cy1 = cell_bbox
        cell_w = cx1 - cx0
        
        ticks_in_cell = []
        for tr in page_ticks:
            tx = (tr.x0 + tr.x1) / 2
            ty = (tr.y0 + tr.y1) / 2
            # Check if tick center is inside cell boundaries with a tiny margin
            if cx0 - 2 <= tx <= cx1 + 2 and cy0 - 2 <= ty <= cy1 + 2:
                ticks_in_cell.append(tx)
                
        if not ticks_in_cell:
            return cell_text
            
        t_clean = cell_text.strip()
        if not t_clean:
            return "☑"
            
        t_lower = t_clean.lower()
        tick_x = ticks_in_cell[0]
        rel_x = (tick_x - cx0) / max(1.0, cell_w)
        
        if "yes" in t_lower and "no" in t_lower:
            if rel_x < 0.5:
                return "Yes"
            else:
                return "No"
        elif "y" in t_lower and "n" in t_lower:
            if "n/a" in t_lower or "na" in t_lower:
                if rel_x < 0.33:
                    return "Y"
                elif rel_x < 0.66:
                    return "N"
                else:
                    return "N/A"
            else:
                if rel_x < 0.5:
                    return "Y"
                else:
                    return "N"
                    
        return cell_text

    def _extract_tables(self, pdf_obj):
        for page_idx, page in enumerate(pdf_obj.pages):
            # Extract ticks/checkmarks for this page using PyMuPDF drawings
            page_ticks = []
            if hasattr(self, "doc") and self.doc and page_idx < len(self.doc):
                pymupdf_page = self.doc[page_idx]
                try:
                    drawings = pymupdf_page.get_drawings()
                    for d in drawings:
                        rect = d["rect"]
                        w = rect.x1 - rect.x0
                        h = rect.y1 - rect.y0
                        if 2 <= w <= 20 and 2 <= h <= 20:
                            items = d.get("items", [])
                            has_lines = any(item[0] == 'l' for item in items)
                            if has_lines:
                                page_ticks.append(rect)
                except Exception as e:
                    print("Error extracting vector drawings:", e)
                    
            tables = page.find_tables()
            for table in tables:
                cleaned_table = []
                for row in table.rows:
                    cleaned_row = []
                    for cell_bbox in row.cells:
                        if cell_bbox is None:
                            cleaned_row.append("")
                            continue
                            
                        # Extract cell text
                        cell_text = page.crop(cell_bbox).extract_text()
                        if cell_text is None:
                            cell_text = ""
                        else:
                            cell_text = str(cell_text).strip()
                            
                        # Resolve with ticks
                        resolved_text = self._resolve_cell_text_with_ticks(cell_text, cell_bbox, page_ticks)
                        cleaned_row.append(resolved_text)
                        
                    if any(cleaned_row):
                        cleaned_table.append(cleaned_row)
                        
                if len(cleaned_table) > 1:
                    self.tables.append({
                        "page": page_idx + 1,
                        "data": cleaned_table
                    })

    def _analyze_table_columns(self, table_data):
        if not table_data:
            return -1, -1, -1
            
        num_cols = len(table_data[0])
        col_scores = []
        for col_idx in range(num_cols):
            item_no_score = 0
            status_score = 0
            desc_score = 0
            empty_count = 0
            
            sample_rows = table_data[1:] if len(table_data) > 1 else table_data
            total_sampled = len(sample_rows)
            
            for row in sample_rows:
                if col_idx >= len(row):
                    continue
                val = str(row[col_idx]).strip()
                if not val:
                    empty_count += 1
                    continue
                    
                if re.match(r'^\d+(\.\d+)*\.?$', val):
                    item_no_score += 1
                    
                val_lower = val.lower()
                val_clean = val_lower.replace("-", "").replace(" ", "").replace("/", "")
                
                if val in ["☐", "☒", "☑", "✓", "✔"] or val_clean in ["y", "n", "x", "yes", "no", "na", "satisfactory", "uygun", "uygunsuz", "durum"]:
                    status_score += 2
                elif len(val) <= 6 and val_clean in ["y", "n", "na", "yes", "no", "yc", "nc", "nac", "ok"]:
                    status_score += 2
                elif len(val) <= 4:
                    status_score += 0.5
                    
                if len(val) > 15:
                    desc_score += 1
                    
            non_empty = total_sampled - empty_count
            col_scores.append({
                "idx": col_idx,
                "item_no": item_no_score / max(1, non_empty),
                "status": status_score / max(1, non_empty),
                "desc": desc_score / max(1, non_empty),
                "empty_ratio": empty_count / max(1, total_sampled)
            })
            
        desc_idx = -1
        status_idx = -1
        remarks_idx = -1
        item_idx = -1
        
        best_item_score = 0.3
        for col in col_scores:
            if col["item_no"] > best_item_score:
                best_item_score = col["item_no"]
                item_idx = col["idx"]
                
        best_status_score = 0.3
        for col in col_scores:
            if col["idx"] == item_idx:
                continue
            if col["status"] > best_status_score:
                best_status_score = col["status"]
                status_idx = col["idx"]
                
        best_desc_score = 0.2
        for col in col_scores:
            if col["idx"] in [item_idx, status_idx]:
                continue
            if col["desc"] > best_desc_score:
                best_desc_score = col["desc"]
                desc_idx = col["idx"]
                
        if desc_idx == -1:
            max_len = -1
            for col in col_scores:
                if col["idx"] in [item_idx, status_idx]:
                    continue
                avg_len = sum(len(str(r[col["idx"]])) for r in sample_rows if col["idx"] < len(r)) / max(1, total_sampled)
                if avg_len > max_len:
                    max_len = avg_len
                    desc_idx = col["idx"]
                    
        for col in col_scores:
            if col["idx"] not in [item_idx, status_idx, desc_idx]:
                remarks_idx = col["idx"]
                break
                
        return desc_idx, status_idx, remarks_idx

    def process_findings(self, vessel_type=None, grt=None):
        if self.doc_type == "certificate":
            return []  # Certificates don't have checklist findings
            
        if not vessel_type:
            vessel_type = self.vessel_info.get("vessel_type", "General Cargo")
        if not grt:
            grt = self.vessel_info.get("grt_dwt", "5000")
            
        findings = []
        item_counter = 1
        
        for table_dict in self.tables:
            table_data = table_dict["data"]
            
            # Skip reference matrices / dangerous goods class tables (cols > 5)
            if len(table_data[0]) > 5:
                continue
                
            # Skip title blocks / vessel particulars tables
            first_row_str = " ".join([str(cell).lower() for cell in table_data[0] if cell])
            particulars_kws = ["name of ship", "gemi adı", "gemi adi", "imo no", "imo number", "nameofship", "imono", "gross tonnage", "gros tonaj"]
            if any(kw in first_row_str for kw in particulars_kws):
                continue
                
            # Skip equipment lists / inventories (e.g. fire extinguishers or lifeboats lists)
            header_str = " ".join([str(h).lower() for h in table_data[0] if h])
            if any(kw in header_str for kw in ["capacity", "space protected", "hydraulic test", "date serviced", "date of last hydraulic"]):
                continue
                
            header = [h.lower() for h in table_data[0]]
            
            desc_idx = -1
            status_idx = -1
            remarks_idx = -1
            
            # 1. Try to find column indices using header keywords
            for i, h in enumerate(table_data[0]):
                if h is None:
                    continue
                h_lower = str(h).lower()
                if any(x in h_lower for x in ["description", "descrip", "konu", "tanım", "madde açıklaması"]):
                    desc_idx = i
                elif any(x in h_lower for x in ["status", "durum", "check", "onay", "uygunluk", "kod"]):
                    status_idx = i
                elif any(x in h_lower for x in ["remark", "deficiency", "açıklama", "not", "bulgu", "düşünce"]):
                    remarks_idx = i
            
            # 2. If header mapping failed or is incomplete, use dynamic column profile analyzer
            if desc_idx == -1 or status_idx == -1:
                anal_desc, anal_status, anal_remarks = self._analyze_table_columns(table_data)
                if desc_idx == -1:
                    desc_idx = anal_desc
                if status_idx == -1:
                    status_idx = anal_status
                if remarks_idx == -1:
                    remarks_idx = anal_remarks
                    
            # 3. Fallbacks if still not found
            if status_idx == -1:
                cols_count = len(table_data[0])
                if cols_count == 3:
                    # Item No, Description, Status
                    desc_idx = 1
                    status_idx = 2
                    remarks_idx = -1
                elif cols_count >= 4:
                    # Item No, Description, Status, Remarks
                    desc_idx = 1
                    status_idx = 2
                    remarks_idx = 3
                elif cols_count == 2:
                    desc_idx = 0
                    status_idx = 1
                    remarks_idx = -1
                else:
                    continue
            else:
                if desc_idx == -1:
                    desc_idx = 0 if status_idx != 0 else 1
                    
                if remarks_idx == -1 and len(table_data[0]) > 2:
                    for col_idx in range(len(table_data[0])):
                        if col_idx != desc_idx and col_idx != status_idx:
                            remarks_idx = col_idx
                            break
                
            start_row_idx = 1
            # Check if first row is a header row
            first_row_str = " ".join([str(cell).lower() for cell in table_data[0] if cell])
            header_keywords = [
                "item", "description", "descrip", "status", "remark", "comment", "check", 
                "konu", "tanım", "durum", "onay", "uygunluk", "açıklama", "not", "bulgu"
            ]
            if not any(kw in first_row_str for kw in header_keywords):
                start_row_idx = 0
                
            for row in table_data[start_row_idx:]:
                if len(row) <= max(desc_idx, status_idx):
                    continue
                
                h_num, h_idx = None, -1
                for idx, cell in enumerate(row):
                    val = str(cell).strip()
                    match = re.match(r'^(\d+)(?:\.(\d+)){0,4}\.?$', val)
                    if match:
                        groups = [g for g in match.groups() if g is not None]
                        if len(groups) == 1 and len(groups[0]) >= 5:
                            continue
                        h_num = val
                        h_idx = idx
                        break
                
                row_cells = list(row)
                temp_desc_idx = desc_idx
                
                if h_num is not None and h_idx == desc_idx:
                    found_new_desc = False
                    for idx in range(h_idx + 1, len(row_cells)):
                        if idx != status_idx and idx != remarks_idx and row_cells[idx].strip():
                            temp_desc_idx = idx
                            found_new_desc = True
                            break
                    if not found_new_desc:
                        temp_desc_idx = desc_idx
                        
                item_desc = row_cells[temp_desc_idx]
                if h_num is not None and item_desc == h_num:
                    for idx, cell in enumerate(row_cells):
                        if idx != h_idx and idx != status_idx and idx != remarks_idx and cell.strip():
                            item_desc = cell
                            break
                            
                reported_status = row_cells[status_idx]
                remarks = row_cells[remarks_idx] if remarks_idx != -1 and len(row_cells) > remarks_idx else ""
                
                if h_num is not None:
                    if remarks.strip() == h_num:
                        remarks = ""
                    if item_desc.strip() == h_num:
                        item_desc = "Survey Item"
                
                if not item_desc or item_desc.lower() in ["inspection item", "madde", "gemi adı", "imo"]:
                    continue
                    
                rule_code = get_rule_by_keyword(item_desc)
                is_applicable, app_reason = check_rule_applicability(rule_code, vessel_type, grt)
                
                status_lower = reported_status.lower().strip()
                s_clean = status_lower.replace("-", "").replace(" ", "").replace("/", "")
                
                clean_status = "Uygun"
                severity = "success"
                
                is_empty_box = "☐" in reported_status or s_clean in ["", "none", "nan", "[]"]
                is_deficiency = (
                    "deficiency" in status_lower or 
                    "uygunsuz" in status_lower or 
                    s_clean in ["n", "no", "notincompliance"] or 
                    "☒" in reported_status or 
                    "✗" in reported_status or 
                    "✘" in reported_status or 
                    status_lower == "x"
                )
                is_na = (
                    "n/a" in status_lower or 
                    s_clean in ["na", "notapplicable", "gecersiz"]
                )
                is_success = (
                    "satisfactory" in status_lower or 
                    "uygun" in status_lower or 
                    s_clean in ["y", "yes", "incompliance"] or 
                    "☑" in reported_status or 
                    "✔" in reported_status or 
                    "✓" in reported_status
                )
                
                if is_deficiency:
                    clean_status = "Uygun Değil"
                    severity = "error"
                elif is_na:
                    clean_status = "Uygun"
                    severity = "info"
                elif is_empty_box:
                    clean_status = "Düzeltilmeli"
                    severity = "warning"
                elif is_success:
                    clean_status = "Uygun"
                    severity = "success"
                else:
                    clean_status = "Uygun"
                    severity = "success"
                    
                notes_text = remarks.lower() if remarks else ""
                has_contradiction = False
                
                if clean_status == "Uygun":
                    for kw in CONTRADICTION_KEYWORDS:
                        if kw in notes_text:
                            if f"no {kw}" in notes_text or f"not {kw}" in notes_text or f"no outstanding {kw}" in notes_text:
                                continue
                            has_contradiction = True
                            break
                            
                if "see attachment" in notes_text or "eke atıf" in notes_text:
                    clean_status = "Uygun"
                    severity = "success"
                    has_contradiction = False
                    
                final_status = clean_status
                final_desc = ""
                recommendation = ""
                
                rule_title = ""
                rule_desc = ""
                satisfactory_condition = ""
                if rule_code != "N/A" and rule_code in REGULATIONS_DB:
                    rule_info = REGULATIONS_DB[rule_code]
                    rule_title = rule_info["title"]
                    rule_desc = rule_info["description"]
                    satisfactory_condition = rule_info["satisfactory_condition"]
                
                if has_contradiction:
                    final_status = "Uygun Değil"
                    severity = "critical"
                    if rule_code != "N/A":
                        final_desc = (
                            f"İlgili Kural: {rule_code} ({rule_title})\n\n"
                            f"Neden: Çelişkili Durum Tespit Edilmiştir. Gemi formunda bu madde '{reported_status}' "
                            f"(Uygun) olarak işaretlenmiş olmasına rağmen, sörveyör açıklamalarında uygunsuzluk/hasar belirtilmiştir: \"{remarks}\".\n"
                            f"{rule_code} kuralı gereğince '{satisfactory_condition}' koşulu tam olarak sağlanmalıdır. Sörveyörün notu bu kuralla çelişmektedir."
                        )
                        recommendation = REGULATIONS_DB[rule_code]["deficiency_action"]
                    else:
                        final_desc = (
                            f"Neden: Çelişkili Durum Tespit Edilmiştir. Gemi formunda bu madde '{reported_status}' "
                            f"(Uygun) olarak işaretlenmiş olmasına rağmen, sörveyör açıklamalarında eksiklik belirtilmiştir: \"{remarks}\"."
                        )
                        recommendation = "Maddedeki eksikliğin giderilmesi ve sörveyöre raporlanması gerekmektedir."
                elif is_empty_box:
                    final_status = "Düzeltilmeli"
                    severity = "warning"
                    if rule_code != "N/A":
                        final_desc = (
                            f"İlgili Kural: {rule_code} ({rule_title})\n\n"
                            f"Neden: Kontrol formundaki onay kutusu boş bırakılmıştır.\n"
                            f"{rule_code} kuralı gereğince '{satisfactory_condition}' durumunun doğrulanması ve formda işaretlenerek onaylanması gerekmektedir."
                        )
                        recommendation = REGULATIONS_DB[rule_code]["deficiency_action"]
                    else:
                        final_desc = "Neden: Kontrol formundaki onay kutusu boş bırakılmıştır. Sörveyörün bu alanı doğrulaması ve doldurması gerekmektedir."
                        recommendation = "Kutunun uygunluk durumunu (☑/☒) işaretleyin veya açıklama ekleyin."
                elif not is_applicable:
                    final_status = "Düzeltilmeli"
                    severity = "info"
                    app_spec = REGULATIONS_DB[rule_code]['applicability']
                    final_desc = (
                        f"İlgili Kural: {rule_code} ({rule_title})\n\n"
                        f"Neden (Kapsam Dışı): Bu kural ({rule_code}) sadece '{app_spec}' sınıfı için geçerlidir.\n"
                        f"Mevcut gemi türü '{vessel_type}' olduğu için bu kurala tabi değildir.\n"
                        f"Gemi formunda '{reported_status}' olarak işaretlenmiş olan bu madde, kural uyumluluğu açısından N/A (Geçersiz) olarak düzeltilmelidir."
                    )
                    recommendation = "Durumu N/A (Not Applicable) olarak revize edin."
                elif clean_status == "Uygun Değil":
                    final_status = "Uygun Değil"
                    severity = "error"
                    if rule_code != "N/A":
                        final_desc = (
                            f"İlgili Kural: {rule_code} ({rule_title})\n\n"
                            f"Neden: Gemi sörveyör formunda bu madde direkt olarak Uygunsuz ('{reported_status}') olarak işaretlenmiştir. Sörveyörün notu: \"{remarks}\".\n"
                            f"{rule_code} kuralı gereğince '{satisfactory_condition}' koşulunun sağlanması zorunludur."
                        )
                        recommendation = REGULATIONS_DB[rule_code]["deficiency_action"]
                    else:
                        final_desc = f"Neden: Uygunsuzluk Tespit Edilmiştir. Sörveyör açıklaması: \"{remarks}\""
                        recommendation = "Eksikliğin giderilmesi ve sörveyörün yeniden denetlemesi gerekmektedir."
                else:
                    final_status = "Uygun"
                    severity = "success"
                    if rule_code != "N/A":
                        final_desc = (
                            f"İlgili Kural: {rule_code} ({rule_title})\n\n"
                            f"Neden: {rule_code} kuralına göre gemide '{satisfactory_condition}' sağlanmış olmalıdır. "
                            f"Sörveyör raporunda da bu durum '{reported_status}' olarak onaylanmıştır. (Sörveyör notu: \"{remarks if remarks else 'Sorunsuz'}\")"
                        )
                    else:
                        final_desc = f"Neden: Bu kontrol maddesinde herhangi bir uygunsuzluk veya çelişki tespit edilmemiştir. Maddenin durumu uygundur. (Sörveyör notu: \"{remarks if remarks else 'Sorunsuz'}\")"
                    recommendation = ""
                    
                item_no_val = h_num if h_num is not None else str(item_counter)
                
                findings.append({
                    "item_no": item_no_val,
                    "title": item_desc,
                    "rule": rule_code,
                    "status": final_status,
                    "severity": severity,
                    "description": final_desc,
                    "recommendation": recommendation
                })
                
                if h_num is None:
                    item_counter += 1
                    
        if not findings and self.raw_text:
            lines = self.raw_text.splitlines()
            for idx, line in enumerate(lines):
                line = line.strip()
                match = re.match(r'^(\d+(?:\.\d+)+)\.?\s+(.+)$', line)
                if match:
                    item_no = match.group(1)
                    rest = match.group(2).strip()
                    
                    status_str = "Uygun"
                    status_match = re.search(r'\b(satisfactory|deficiency|uygun|uygunsuz|yes|no)\b', rest, re.IGNORECASE)
                    if status_match:
                        s_word = status_match.group(1).lower()
                        if s_word in ["deficiency", "uygunsuz", "no"]:
                            status_str = "Uygun Değil"
                        rest = rest[:status_match.start()].strip()
                    
                    remarks = ""
                    if idx + 1 < len(lines):
                        next_line = lines[idx+1].strip()
                        if len(next_line) > 5 and not re.match(r'^\d', next_line):
                            remarks = next_line
                            
                    rule_code = get_rule_by_keyword(rest)
                    
                    final_desc = rest
                    recommendation = ""
                    severity = "success"
                    
                    rule_title = ""
                    rule_desc = ""
                    satisfactory_condition = ""
                    if rule_code != "N/A" and rule_code in REGULATIONS_DB:
                        rule_info = REGULATIONS_DB[rule_code]
                        rule_title = rule_info["title"]
                        rule_desc = rule_info["description"]
                        satisfactory_condition = rule_info["satisfactory_condition"]
                        recommendation = rule_info["deficiency_action"]
                        
                    if status_str == "Uygun Değil":
                        severity = "error"
                        if rule_code != "N/A":
                            final_desc = f"İlgili Kural: {rule_code} ({rule_title})\n\nNeden: Kural ihlali tespit edilmiştir: {rest}\n\n{rule_code} kuralı gereğince '{satisfactory_condition}' koşulunun sağlanması zorunludur."
                        else:
                            final_desc = f"Neden: Uygunsuzluk tespit edilmiştir: {rest}"
                            recommendation = "Eksikliğin giderilmesi gerekmektedir."
                    else:
                        severity = "success"
                        if rule_code != "N/A":
                            final_desc = f"İlgili Kural: {rule_code} ({rule_title})\n\nNeden: {rule_code} kuralına uygunluk doğrulanmıştır. {rest}"
                        else:
                            final_desc = f"Maddenin durumu uygundur: {rest}"
                            
                    findings.append({
                        "item_no": item_no,
                        "title": rest[:60] if len(rest) > 60 else rest,
                        "rule": rule_code,
                        "status": status_str,
                        "severity": severity,
                        "description": final_desc,
                        "recommendation": recommendation
                    })
        return findings

def run_cross_document_checks(vessel_name, imo_number, grt_dwt, certificates_info, checklist_findings=None):
    cross_findings = []
    
    # Standardize names for comparison
    def clean_name(n):
        return re.sub(r'[^A-Z0-9]', '', str(n).upper())

    # Standardize tonnage comparison
    def clean_ton(t):
        if not t or t == "N/A":
            return None
        return re.sub(r'[^\d]', '', str(t))

    for cert in certificates_info:
        cert_type = cert.get("cert_type", "Sertifika")
        cert_vessel = cert.get("vessel_name", "N/A")
        cert_imo = cert.get("imo", "N/A")
        cert_grt = cert.get("grt", "N/A")
        cert_dwt = cert.get("dwt", "N/A")
        expiry_date_str = cert.get("expiry_date", "N/A")
        
        # 1. Vessel Name Check
        if vessel_name and cert_vessel != "N/A":
            if clean_name(vessel_name) not in clean_name(cert_vessel) and clean_name(cert_vessel) not in clean_name(vessel_name):
                cross_findings.append({
                    "item_no": "C-1",
                    "title": f"Gemi Adı Uyuşmazlığı ({cert_type})",
                    "rule": "CERT-CHECK",
                    "status": "Uygun Değil",
                    "severity": "critical",
                    "description": f"Yüklenen {cert_type} sertifikasındaki gemi adı ('{cert_vessel}'), denetlenen gemi adı ('{vessel_name}') ile eşleşmemektedir. Lütfen doğru gemiye ait sertifikayı yüklediğinizden emin olun.",
                    "recommendation": "Gemi adlarını evraklardan doğrulayın ve doğru sertifika dosyasını yükleyin."
                })
                
        # 2. IMO Number Check
        if imo_number and cert_imo != "N/A":
            clean_imo_ui = re.sub(r'[^\d]', '', str(imo_number))
            clean_imo_cert = re.sub(r'[^\d]', '', str(cert_imo))
            if clean_imo_ui and clean_imo_cert and clean_imo_ui != clean_imo_cert:
                cross_findings.append({
                    "item_no": "C-2",
                    "title": f"IMO Numarası Uyuşmazlığı ({cert_type})",
                    "rule": "CERT-CHECK",
                    "status": "Uygun Değil",
                    "severity": "critical",
                    "description": f"Sertifikadaki IMO Numarası ('{cert_imo}'), seçilen/girilen IMO Numarası ('{imo_number}') ile uyuşmamaktadır. Bu durum evrak sahteciliği veya yanlış gemi belgesi yükleme riskine işaret eder.",
                    "recommendation": "IMO numarasının doğruluğunu evraklardan ve resmi kayıtlardan (B2B/Equasis) kontrol edin."
                })
                
        # 3. Tonnage Check
        if grt_dwt and (cert_grt != "N/A" or cert_dwt != "N/A"):
            parts = grt_dwt.split('/')
            ui_grt = clean_ton(parts[0]) if len(parts) > 0 else None
            ui_dwt = clean_ton(parts[1]) if len(parts) > 1 else None
            cert_grt_cleaned = clean_ton(cert_grt)
            cert_dwt_cleaned = clean_ton(cert_dwt)
            
            if ui_grt and cert_grt_cleaned and ui_grt != cert_grt_cleaned:
                # Allow a small discrepancy margin of 5% in tonnage representations, otherwise flag
                if abs(int(ui_grt) - int(cert_grt_cleaned)) / int(cert_grt_cleaned) > 0.05:
                    cross_findings.append({
                        "item_no": "C-3",
                        "title": f"Brüt Tonaj (GRT) Uyuşmazlığı ({cert_type})",
                        "rule": "CERT-CHECK",
                        "status": "Düzeltilmeli",
                        "severity": "warning",
                        "description": f"Sertifikadaki Brüt Tonaj ('{cert_grt} GRT'), sörvey raporundaki/seçilen gemi tonajı ('{parts[0].strip()} GRT') ile uyuşmamaktadır.",
                        "recommendation": "Tüm evraklardaki ve veritabanındaki GRT bilgisini güncelleyerek eşitleyin."
                    })
                    
        # 4. Validity & Expiry Check
        if expiry_date_str != "N/A":
            try:
                # Find date using flexible parsing
                exp_date = None
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        exp_date = datetime.strptime(expiry_date_str.strip(), fmt)
                        break
                    except:
                        continue
                if not exp_date:
                    exp_date = pd.to_datetime(expiry_date_str)
                    
                if exp_date:
                    today = datetime.now()
                    days_left = (exp_date - today).days
                    
                    if days_left < 0:
                        cross_findings.append({
                            "item_no": "C-4",
                            "title": f"Sertifika Geçerlilik Süresi Dolan Belge ({cert_type})",
                            "rule": "CERT-EXPIRY",
                            "status": "Uygun Değil",
                            "severity": "critical",
                            "description": f"Yüklenen {cert_type} belgesinin geçerlilik süresi {expiry_date_str} tarihinde ({abs(days_left)} gün önce) dolmuştur. Geçersiz sertifika ile gemi sefere çıkamaz.",
                            "recommendation": "Yenileme sörveyini derhal planlayarak sertifikayı güncelleyin."
                        })
                    elif days_left <= 30:
                        cross_findings.append({
                            "item_no": "C-5",
                            "title": f"Sertifika Süresi Yaklaşıyor ({cert_type})",
                            "rule": "CERT-EXPIRY",
                            "status": "Düzeltilmeli",
                            "severity": "warning",
                            "description": f"Yüklenen {cert_type} belgesinin geçerlilik süresinin dolmasına {days_left} gün kalmıştır. (Bitiş Tarihi: {expiry_date_str})",
                            "recommendation": "30 gün içerisinde yenileme veya yıllık ara sörveyin tamamlanmasını sağlayın."
                        })
            except Exception as e:
                # If date format is text-based or could not be parsed, skip date comparison
                pass

        # 5. Cross-Check Certificate validity against checklist findings (Contradictions)
        if checklist_findings:
            # Check OWS presence in checklist
            if not cert.get("ows_fitted", True):
                ows_items = [f for f in checklist_findings if "ows" in f["title"].lower() or "oily water separator" in f["title"].lower() or "15 ppm bilge" in f["title"].lower() or "15ppm bilge" in f["title"].lower()]
                for item in ows_items:
                    if item["status"] == "Uygun": # marked as Y
                        cross_findings.append({
                            "item_no": "C-10",
                            "title": f"OWS Donanım Uyuşmazlığı ({cert_type})",
                            "rule": "MARPOL Annex I Reg 14",
                            "status": "Uygun Değil",
                            "severity": "critical",
                            "description": f"Yüklenen {cert_type} sertifikasında 15 ppm Sintine Separatörünün (OWS) kurulu olmadığı / muaf olduğu belirtilmesine rağmen, sörvey checklistinde OWS maddesi ({item['item_no']}) Uygun (Y) olarak işaretlenmiştir! OWS bulunmayan gemide bu maddenin muaf (N/A) veya uygunsuz (N) olması gerekir.",
                            "recommendation": "Sörvey checklistindeki OWS maddesini N/A (Geçersiz) olarak düzeltin."
                        })
                        
            # Check BWMS presence in checklist
            if not cert.get("bwms_fitted", True):
                bwms_items = [f for f in checklist_findings if "bwms" in f["title"].lower() or "ballast water treatment" in f["title"].lower() or "active substances" in f["title"].lower() or "d-2 performance" in f["title"].lower()]
                for item in bwms_items:
                    if item["status"] == "Uygun":
                        cross_findings.append({
                            "item_no": "C-11",
                            "title": f"BWMS Donanım Uyuşmazlığı ({cert_type})",
                            "rule": "BWM D-2",
                            "status": "Uygun Değil",
                            "severity": "critical",
                            "description": f"Yüklenen {cert_type} sertifikasında D-2 Balast Suyu Arıtma Sisteminin (BWMS) kurulu olmadığı (D-1 standardı geçerli olduğu) belirtilmesine rağmen, sörvey checklistinde BWMS arıtma maddesi ({item['item_no']}) Uygun (Y) olarak işaretlenmiştir! Arıtma ünitesi bulunmayan gemide D-2 arıtma maddelerinin N/A (Geçersiz) olması gerekir.",
                            "recommendation": "Sörvey checklistindeki D-2 arıtma maddelerini N/A (Geçersiz) olarak düzeltin."
                        })

            # Check for specific rules based on certificate type
            if "IOPP" in cert_type or "Oil Pollution" in cert_type:
                # Search if there is a critical OWS failure in the checklist
                ows_failures = [f for f in checklist_findings if f["rule"] == "MARPOL Annex I Reg 14" and f["status"] == "Uygun Değil"]
                if ows_failures:
                    cross_findings.append({
                        "item_no": "C-6",
                        "title": "IOPP Sertifikası & OWS Uygunsuzluk Çelişkisi",
                        "rule": "MARPOL Annex I Reg 14",
                        "status": "Uygun Değil",
                        "severity": "critical",
                        "description": f"Gemi geçerli bir IOPP (Petrol Kirliliğini Önleme) sertifikası beyan etmesine rağmen, sörvey raporunda OWS (Oily Water Separator) 15ppm filtresinde veya alarm ünitesinde doğrudan uygunsuzluk ('Uygun Değil') tespit edilmiştir. Bu durum sertifikanın geçerliliğini geçersiz kılabilir.",
                        "recommendation": "OWS ünitesindeki arızayı derhal giderin ve test raporunu ekleyerek sertifikayı güvenceye alın."
                    })
            
            if "Ballast Water" in cert_type or "BWM" in cert_type:
                bwm_failures = [f for f in checklist_findings if f["rule"] == "BWM D-2" and f["status"] == "Uygun Değil"]
                if bwm_failures:
                    cross_findings.append({
                        "item_no": "C-7",
                        "title": "BWM Sertifikası & Arıtma Sistemi Çelişkisi",
                        "rule": "BWM D-2",
                        "status": "Uygun Değil",
                        "severity": "critical",
                        "description": "BWM (Balast Suyu Yönetimi) sertifikası bulunmasına rağmen, sörvey checklistinde Balast Suyu Arıtma Ünitesinin (BWMS) çalışmadığı veya kayıt defterinde eksiklik olduğu belirtilmiştir. Bu durum BWM D-2 kural ihlalidir.",
                        "recommendation": "BWMS sistemini servis çağırarak onarın; arıtmasız balast deşarjı yapmayın."
                    })
                    
            if "Safety Equipment" in cert_type:
                lsa_failures = [f for f in checklist_findings if f["rule"] in ["SOLAS Ch III Reg 20", "SOLAS Ch III Reg 7"] and f["status"] == "Uygun Değil"]
                if lsa_failures:
                    cross_findings.append({
                        "item_no": "C-8",
                        "title": "Safety Equipment Sertifikası & Can Kurtarma Araçları Çelişkisi",
                        "rule": "SOLAS Ch III Reg 20",
                        "status": "Uygun Değil",
                        "severity": "critical",
                        "description": "Cargo Ship Safety Equipment (Emniyet Teçhizatı) sertifikası geçerli görünmesine rağmen, sörvey checklistinde can filikaları, can salları veya limit anahtarlarında kritik derecede arıza veya eksiklik tespit edilmiştir. Bu durum SOLAS kurallarına göre geminin limandan kalkışına engel teşkil eder.",
                        "recommendation": "Filika limit anahtarlarını, serbest bırakma mekanizmalarını onarın ve acilen test edin."
                    })
                    
            if "Anti-Fouling" in cert_type or "AFS" in cert_type:
                afs_failures = [f for f in checklist_findings if f["rule"] == "AFS Convention" and f["status"] == "Uygun Değil"]
                if afs_failures:
                    cross_findings.append({
                        "item_no": "C-9",
                        "title": "AFS Sertifikası & Zehirli Boya Uygunsuzluk Çelişkisi",
                        "rule": "AFS Convention",
                        "status": "Uygun Değil",
                        "severity": "critical",
                        "description": "Anti-Fouling sertifikası beyan edilmiştir ancak checklist bulgularında gemi karinasında organotin bazlı (TBT) yasaklı boya kullanıldığı veya sertifikada boya beyanının eksik olduğu belirtilmiştir.",
                        "recommendation": "Boyanın TBT içermediğine dair üretici beyanını klas kuruluşuna sunun veya ilk havuzlamada uygun boya ile kaplayın."
                    })

    return cross_findings
