import pdfplumber
import fitz  # PyMuPDF
import re
import os
from rules_engine import REGULATIONS_DB, get_rule_by_keyword, check_rule_applicability

CONTRADICTION_KEYWORDS = [
    "deficiency", "defect", "expired", "overdue", "broken", "corroded", 
    "missing", "leak", "damaged", "fail", "not tested", "stiff", 
    "unauthorized", "degraded", "not functional", "inoperable",
    "hata", "eksik", "hasarlı", "bozuk", "çürük", "paslı", "uygunsuz",
    "tarihi geçmiş", "çalışmıyor", "bulunamadı", "kaçırılmış"
]

class SurveyDocumentProcessor:
    def __init__(self, file_path_or_bytes):
        self.file_path_or_bytes = file_path_or_bytes
        self.raw_text = ""
        self.pages_count = 0
        self.tables = []
        self.vessel_info = {}
        self._load_document()

    def _load_document(self):
        if isinstance(self.file_path_or_bytes, bytes):
            doc = fitz.open(stream=self.file_path_or_bytes, filetype="pdf")
        else:
            doc = fitz.open(self.file_path_or_bytes)
            
        self.pages_count = len(doc)
        text_list = []
        for page in doc:
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

    def _extract_tables(self, pdf_obj):
        for page_idx, page in enumerate(pdf_obj.pages):
            extracted_tables = page.extract_tables()
            for t in extracted_tables:
                cleaned_table = []
                for row in t:
                    cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                    if any(cleaned_row):
                        cleaned_table.append(cleaned_row)
                if len(cleaned_table) > 1:
                    self.tables.append({
                        "page": page_idx + 1,
                        "data": cleaned_table
                    })

    def process_findings(self, vessel_type=None, grt=None):
        if not vessel_type:
            vessel_type = self.vessel_info.get("vessel_type", "General Cargo")
        if not grt:
            grt = self.vessel_info.get("grt_dwt", "5000")
            
        findings = []
        item_counter = 1
        
        for table_dict in self.tables:
            table_data = table_dict["data"]
            header = [h.lower() for h in table_data[0]]
            
            desc_idx = -1
            status_idx = -1
            remarks_idx = -1
            
            for i, h in enumerate(header):
                if any(x in h for x in ["item", "description", "madd", "konu", "tanım"]):
                    desc_idx = i
                elif any(x in h for x in ["status", "durum", "check", "onay", "uygunluk"]):
                    status_idx = i
                elif any(x in h for x in ["remark", "deficiency", "açıklama", "not", "bulgu", "düşünce"]):
                    remarks_idx = i
            
            if status_idx == -1:
                for col_idx in range(len(header)):
                    column_cells = [str(r[col_idx]).lower() for r in table_data[1:] if len(r) > col_idx]
                    status_words = ["satisfactory", "deficiency", "uygun", "uygunsuz", "☑", "☐", "☒", "satisfy", "y / n", "yes", "no"]
                    if any(any(sw in cell for sw in status_words) for cell in column_cells):
                        status_idx = col_idx
                        break
            
            if status_idx == -1:
                continue
                
            if desc_idx == -1:
                desc_idx = 0 if status_idx != 0 else 1
                
            if remarks_idx == -1 and len(header) > 2:
                for col_idx in range(len(header)):
                    if col_idx != desc_idx and col_idx != status_idx:
                        remarks_idx = col_idx
                        break
                
            for row in table_data[1:]:
                if len(row) <= max(desc_idx, status_idx):
                    continue
                
                # Search all cells in row for hierarchical numbering pattern (e.g., 1. or 1.1 or 1.1.1)
                h_num, h_idx = None, -1
                for idx, cell in enumerate(row):
                    val = str(cell).strip()
                    match = re.match(r'^(\d+)(?:\.(\d+)){0,4}\.?$', val)
                    if match:
                        groups = [g for g in match.groups() if g is not None]
                        # Exclude long numbers (like IMO 9076466)
                        if len(groups) == 1 and len(groups[0]) >= 5:
                            continue
                        h_num = val
                        h_idx = idx
                        break
                
                row_cells = list(row)
                temp_desc_idx = desc_idx
                
                # If hierarchical number is found in the description column,
                # shift description index to the next cell
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
                
                # Clear hierarchical number from remarks or description if it matches exactly
                if h_num is not None:
                    if remarks.strip() == h_num:
                        remarks = ""
                    if item_desc.strip() == h_num:
                        item_desc = "Survey Item"
                
                if not item_desc or item_desc.lower() in ["inspection item", "madde", "gemi adı", "imo"]:
                    continue
                    
                rule_code = get_rule_by_keyword(item_desc)
                is_applicable, app_reason = check_rule_applicability(rule_code, vessel_type, grt)
                
                status_lower = reported_status.lower()
                clean_status = "Uygun"
                severity = "success"
                
                is_empty_box = "☐" in reported_status or status_lower in ["", "none", "nan", "[ ]"]
                is_deficiency = "deficiency" in status_lower or "uygunsuz" in status_lower or "no" == status_lower or "n" == status_lower or "☒" in reported_status
                is_na = "n/a" in status_lower or "na" == status_lower or "not applicable" in status_lower or "geçersiz" in status_lower
                
                if is_deficiency:
                    clean_status = "Uygun Değil"
                    severity = "error"
                elif is_na:
                    clean_status = "Uygun"
                    severity = "info"
                elif is_empty_box:
                    clean_status = "Düzeltilmeli"
                    severity = "warning"
                elif "satisfactory" in status_lower or "uygun" in status_lower or "yes" in status_lower or "y" == status_lower or "☑" in reported_status:
                    clean_status = "Uygun"
                    severity = "success"
                else:
                    clean_status = "Uygun"
                    severity = "success"
                    
                notes_text = (item_desc + " " + remarks).lower()
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
                else: # Satisfactory and compliant!
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
                    "title": item_desc[:80] + ("..." if len(item_desc) > 80 else ""),
                    "rule": rule_code,
                    "status": final_status,
                    "severity": severity,
                    "description": final_desc,
                    "recommendation": recommendation
                })
                
                if h_num is None:
                    item_counter += 1
                    
        return findings

class BytesIO_wrapper:
    def __init__(self, data_bytes):
        from io import BytesIO
        self.stream = BytesIO(data_bytes)
        
    def __enter__(self):
        return self.stream
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stream.close()
