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
    def __init__(self, file_path_or_bytes):
        self.file_path_or_bytes = file_path_or_bytes
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

    def _classify_document(self):
        text_lower = self.raw_text.lower()
        cert_keywords = [
            "this is to certify", 
            "issued under the provisions", 
            "certify that", 
            "sertifikası", 
            "certificate of", 
            "load line certificate", 
            "pollution prevention certificate",
            "safety equipment certificate",
            "safety radio certificate",
            "safety construction certificate",
            "tonnage certificate"
        ]
        
        is_cert = any(kw in text_lower for kw in cert_keywords)
        
        # Count checkboxes in document
        checkbox_count = len(re.findall(r'[☐☒☑\[\s]\]', self.raw_text)) + self.raw_text.count("☐") + self.raw_text.count("☒") + self.raw_text.count("☑")
        
        if is_cert and checkbox_count < 5:
            self.doc_type = "certificate"
            self._extract_certificate_info()
        else:
            self.doc_type = "checklist"

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
            
        # Extract Vessel Name
        vessel_name = ""
        v_match = re.search(r'(?:name of ship|name of vessel|gemi adı|gemi adi)\s*:?\s*([a-zA-Z0-9\s\-_]+)', text_lower)
        if v_match:
            vessel_name = v_match.group(1).strip().upper()
        else:
            lines = text.splitlines()
            for line in lines:
                if "name of ship" in line.lower() or "name of vessel" in line.lower():
                    parts = re.split(r'[:\s]{2,}', line)
                    if len(parts) > 1:
                        vessel_name = parts[-1].strip().upper()
                        break
        if not vessel_name:
            for line in lines[:15]:
                if any(x in line.upper() for x in ["M/V", "M.V.", "M/T", "M.T."]):
                    vessel_name = line.strip().upper()
                    break
                    
        # Extract IMO Number
        imo = ""
        imo_match = re.search(r'(?:imo number|imo no|imo|ımo)\s*:?\s*(\d{7})', text_lower)
        if imo_match:
            imo = imo_match.group(1).strip()
        else:
            digit_matches = re.findall(r'\b\d{7}\b', text)
            if digit_matches:
                imo = digit_matches[0]
                
        # Extract Gross Tonnage (GRT)
        grt = ""
        grt_match = re.search(r'(?:gross tonnage|gross weight|grt|gt)\s*:?\s*([\d\s,\.]+)', text_lower)
        if grt_match:
            grt = grt_match.group(1).strip()
            grt = re.sub(r'[^\d]', '', grt.split('.')[0].split(',')[0])
            
        # Extract Deadweight (DWT)
        dwt = ""
        dwt_match = re.search(r'(?:deadweight|dwt)\s*:?\s*([\d\s,\.]+)', text_lower)
        if dwt_match:
            dwt = dwt_match.group(1).strip()
            dwt = re.sub(r'[^\d]', '', dwt.split('.')[0].split(',')[0])
            
        # Extract Date of Expiry
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
                
        # Extract Issue Date
        issue_date = ""
        iss_match = re.search(r'(?:date of issue|issued at|issued on|düzenleme tarihi|duzenleme tarihi)\s*:?\s*([\d\-\/a-zA-Z\s]{8,15})', text_lower)
        if iss_match:
            issue_date = iss_match.group(1).strip()
            
        # Extract Certificate Number
        cert_number = ""
        num_match = re.search(r'(?:certificate number|cert\.? no|sertifika no|certificate no)\s*:?\s*([a-zA-Z0-9\-_]+)', text_lower)
        if num_match:
            cert_number = num_match.group(1).strip()
            
        self.certificate_info = {
            "cert_type": cert_type,
            "cert_number": cert_number if cert_number else "N/A",
            "vessel_name": vessel_name if vessel_name else "N/A",
            "imo": imo if imo else "N/A",
            "grt": grt if grt else "N/A",
            "dwt": dwt if dwt else "N/A",
            "issue_date": issue_date if issue_date else "N/A",
            "expiry_date": expiry_date if expiry_date else "N/A"
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
                cols_count = len(header)
                if cols_count == 3:
                    desc_idx = 0
                    status_idx = 1
                    remarks_idx = 2
                elif cols_count == 4:
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
                    
                if remarks_idx == -1 and len(header) > 2:
                    for col_idx in range(len(header)):
                        if col_idx != desc_idx and col_idx != status_idx:
                            remarks_idx = col_idx
                            break
                
            for row in table_data[1:]:
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
    
    def clean_name(n):
        return re.sub(r'[^A-Z0-9]', '', str(n).upper())

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
                exp_date = None
                for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        exp_date = datetime.strptime(expiry_date_str.strip(), fmt)
                        break
                    except:
                        continue
                if not exp_date:
                    import pandas as pd
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
                pass

        # 5. Cross-Check Certificate validity against checklist findings (Contradictions)
        if checklist_findings:
            if "IOPP" in cert_type or "Oil Pollution" in cert_type:
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
