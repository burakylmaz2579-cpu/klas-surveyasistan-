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
            with pdfplumber.open(BytesIO_wrapper(self.file_path_or_bytes)) as pdf:
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
                    
                item_desc = row[desc_idx]
                reported_status = row[status_idx]
                remarks = row[remarks_idx] if remarks_idx != -1 and len(row) > remarks_idx else ""
                
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
                found_keyword = ""
                
                if clean_status == "Uygun":
                    for kw in CONTRADICTION_KEYWORDS:
                        if kw in notes_text:
                            if f"no {kw}" in notes_text or f"not {kw}" in notes_text or f"no outstanding {kw}" in notes_text:
                                continue
                            has_contradiction = True
                            found_keyword = kw
                            break
                            
                if "see attachment" in notes_text or "eke atıf" in notes_text:
                    clean_status = "Uygun"
                    severity = "success"
                    has_contradiction = False
                    
                final_status = clean_status
                final_desc = remarks if remarks else f"Sörvey raporu maddesi denetlendi."
                recommendation = ""
                
                if has_contradiction:
                    final_status = "Uygun Değil"
                    severity = "critical"
                    final_desc = f"[ÇAPRAZ KONTROL UYARISI] Raporda bu madde '{reported_status}' olarak işaretlenmiş, ancak sörveyör notlarında '{found_keyword}' ifadesi geçmektedir: \"{remarks}\""
                    if rule_code != "N/A" and rule_code in REGULATIONS_DB:
                        recommendation = REGULATIONS_DB[rule_code]["deficiency_action"]
                    else:
                        recommendation = "Maddedeki eksikliğin giderilmesi ve sörveyöre raporlanması gerekmektedir."
                elif is_empty_box:
                    final_status = "Düzeltilmeli"
                    severity = "warning"
                    final_desc = "[ÇAPRAZ KONTROL UYARISI] Formdaki ilgili onay kutusu boş bırakılmıştır. Sörveyörün bu alanı doğrulaması veya açıklaması gerekir."
                    recommendation = "Kutunun uygunluk durumunu (☑/☒) işaretleyin veya açıklama ekleyin."
                elif not is_applicable:
                    final_status = "Düzeltilmeli"
                    severity = "info"
                    final_desc = f"[ÇAPRAZ KONTROL UYARISI] Bu kural ({rule_code}) sadece '{REGULATIONS_DB[rule_code]['applicability']}' için geçerlidir. Mevcut gemi türü '{vessel_type}'. Lütfen N/A işaretlendiğinden emin olun."
                    recommendation = "Durumu N/A (Not Applicable) olarak revize edin."
                    
                findings.append({
                    "item_no": str(item_counter),
                    "title": item_desc[:80] + ("..." if len(item_desc) > 80 else ""),
                    "rule": rule_code,
                    "status": final_status,
                    "severity": severity,
                    "description": final_desc,
                    "recommendation": recommendation
                })
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
