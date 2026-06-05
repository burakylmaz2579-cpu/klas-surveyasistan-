import requests
import os
import re
import sys
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

# Global paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_CERT = os.path.join(SCRIPT_DIR, "temp_cert_vessels.pem")
TEMP_KEY = os.path.join(SCRIPT_DIR, "temp_key_vessels.pem")

def find_p12_cert():
    candidates = []
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\LIVAPC8")
    desktop_path = os.path.join(user_profile, "Desktop")
    if os.path.exists(desktop_path):
        for item in os.listdir(desktop_path):
            if item.lower().endswith(".p12"):
                candidates.append(os.path.join(desktop_path, item))
    for item in os.listdir(SCRIPT_DIR):
        if item.lower().endswith(".p12"):
            candidates.append(os.path.join(SCRIPT_DIR, item))
            
    if candidates:
        candidates.sort(key=lambda x: "begum" in os.path.basename(x).lower(), reverse=True)
        return candidates[0]
    return None

def extract_cert_key():
    p12_path = find_p12_cert()
    if not p12_path:
        raise FileNotFoundError("Could not find any .p12 certificate file on the Desktop or script directory.")
    
    print(f"Using client certificate: {p12_path}")
    
    password = b"838173"
    match = re.search(r'\d+', os.path.basename(p12_path))
    if match:
        password = match.group(0).encode('utf-8')
        
    with open(p12_path, 'rb') as f:
        data = f.read()
        
    private_key, certificate, _ = pkcs12.load_key_and_certificates(data, password)
    
    cert_pem = certificate.public_bytes(Encoding.PEM)
    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    
    with open(TEMP_CERT, "wb") as f:
        f.write(cert_pem)
    with open(TEMP_KEY, "wb") as f:
        f.write(key_pem)
        
    return TEMP_CERT, TEMP_KEY

def get_vessel_details(session, v_id):
    retries = 3
    for attempt in range(retries):
        try:
            r_param = session.get(f"https://b2b.phrs.gr/Leads/GetParam?ID={v_id}", timeout=10)
            token = r_param.text.strip().strip('"')
            if not token:
                continue
                
            r_detail = session.get(f"https://b2b.phrs.gr/Vessels/ViewVesselDetails?Val={token}", timeout=10)
            html = r_detail.text
            
            gt_match = re.search(r'id="GT"[^>]*value="([^"]*)"', html)
            dwt_match = re.search(r'id="DWT"[^>]*value="([^"]*)"', html)
            
            if not gt_match:
                gt_match = re.search(r'\$\("#GT"\)\.val\(([^)]+)\);', html)
            if not dwt_match:
                dwt_match = re.search(r'\$\("#DWT"\)\.val\(([^)]+)\);', html)
                
            prev_class_match = re.search(r'id="Previous_Class"[^>]*value="([^"]*)"', html)
            hull_match = re.search(r'id="Hull_Notation"[^>]*value="([^"]*)"', html)
            
            gt_val = gt_match.group(1).strip().strip('"').strip("'") if gt_match else "0"
            dwt_val = dwt_match.group(1).strip().strip('"').strip("'") if dwt_match else "0"
            
            try: gt = int(float(gt_val))
            except: gt = 5000
            try: dwt = int(float(dwt_val))
            except: dwt = 8000
            
            hull = hull_match.group(1).strip() if hull_match else ""
            prev_class = prev_class_match.group(1).strip() if prev_class_match else ""
            
            if "NOT UNDER PHRS" in hull.upper() and prev_class:
                v_class = prev_class
            else:
                v_class = "PHRS"
                
            return gt, dwt, v_class
        except Exception as e:
            if attempt == retries - 1:
                print(f"Error fetching details for ID {v_id} after {retries} attempts: {e}")
            time.sleep(1)
    return None

def main():
    print("PHRS B2B Filo Listesi Scraper başlatılıyor...")
    
    # 1. Load existing cache to preserve manually edited / previously scraped valid particulars
    existing_vessels = {}
    filename_portal = os.path.join(SCRIPT_DIR, "PHRS_Tüm_Gemiler.xlsx")
    if os.path.exists(filename_portal):
        try:
            df_old = pd.read_excel(filename_portal)
            for _, r in df_old.iterrows():
                name_key = str(r.get('Vessel', '')).strip().upper()
                if name_key:
                    existing_vessels[name_key] = {
                        "Class": r.get('Class', 'PHRS'),
                        "GRT": r.get('GRT', 5000),
                        "DWT": r.get('DWT', 8000)
                    }
            print(f"Loaded {len(existing_vessels)} vessels from existing local Excel sheet.")
        except Exception as e:
            print(f"Could not load existing Excel cache: {e}")
            
    # 2. Extract client certificate
    try:
        cert_path, key_path = extract_cert_key()
    except Exception as e:
        print(f"Hata: İstemci sertifikası yüklenemedi: {e}")
        sys.exit(1)
        
    session = requests.Session()
    session.cert = (cert_path, key_path)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    try:
        # 3. Log in to portal
        print("B2B portalına bağlanılıyor...")
        r_login_get = session.get("https://b2b.phrs.gr/Home/Login", timeout=15)
        
        payload = {
            "Username": "b.yener",
            "password": "940523Begg?!?."
        }
        print("Kimlik bilgileri gönderiliyor...")
        r_login_post = session.post("https://b2b.phrs.gr/Home/Login", data=payload, timeout=15)
        
        if r_login_post.text.strip().strip('"') != "OK":
            print("Hata: B2B portal girişi başarısız!")
            sys.exit(1)
            
        print("Giriş başarılı! Filo listesi indiriliyor...")
        
        # 4. Page through grid
        all_scraped_vessels = []
        page = 1
        scraped_names = set()
        
        while True:
            print(f"Sayfa {page} taranıyor...")
            grid_url = f"https://b2b.phrs.gr/Vessels/MyVesselsGrid?Page={page}&FromFilter=0"
            r_grid = session.get(grid_url, timeout=15)
            
            if r_grid.status_code != 200 or len(r_grid.text) < 1000:
                print("Son sayfaya ulaşıldı veya boş sayfa döndü.")
                break
                
            # Extract rows
            # Grid contains ViewVesselDetails(Id) and columns
            matches = list(re.finditer(r'ViewVesselDetails\((\d+)\)', r_grid.text))
            if not matches:
                print("Bu sayfada gemi kaydı bulunamadı. Tarama bitiriliyor.")
                break
                
            new_on_page = 0
            for i in range(len(matches)):
                start_pos = matches[i].start()
                end_pos = matches[i+1].start() if i + 1 < len(matches) else len(r_grid.text)
                
                chunk = r_grid.text[start_pos:end_pos]
                v_id = matches[i].group(1)
                
                # Extract text fields
                cells = re.findall(r'<div[^>]*class="lh-1 text-alternate"[^>]*>(.*?)</div>', chunk, re.DOTALL)
                clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                
                if len(clean_cells) >= 7:
                    v_name = clean_cells[0]
                    
                    if not v_name or v_name in scraped_names:
                        continue
                        
                    scraped_names.add(v_name)
                    new_on_page += 1
                    
                    phrs_no = clean_cells[1]
                    imo = clean_cells[2]
                    flag = clean_cells[3]
                    reg_no = clean_cells[4]
                    v_type = clean_cells[5]
                    status = clean_cells[6]
                    
                    if not imo or imo == "nan" or not imo.isdigit():
                        imo = ""
                        
                    all_scraped_vessels.append({
                        "id": v_id,
                        "Vessel": v_name,
                        "IMO": imo,
                        "Type": v_type,
                        "Flag": flag,
                        "PHRS_No": phrs_no,
                        "Reg_No": reg_no,
                        "Status": status
                    })
            
            print(f"Sayfa {page}'dan {new_on_page} yeni gemi eklendi.")
            if new_on_page == 0:
                print("Daha fazla yeni gemi bulunamadı. Tarama bitiriliyor.")
                break
                
            page += 1
            
        print(f"Toplam {len(all_scraped_vessels)} gemi listelendi. Detaylı particulars (GRT/DWT/Class) güncelleniyor...")
        
        # 5. Determine which vessels need details scraping (new ones or those with default values)
        vessels_to_scrape_details = []
        for v in all_scraped_vessels:
            v_key = v["Vessel"].upper()
            
            # Check if we have valid non-default particulars cached
            if v_key in existing_vessels:
                cached = existing_vessels[v_key]
                try:
                    grt_int = int(cached.get("GRT", 0))
                except:
                    grt_int = 0
                try:
                    dwt_int = int(cached.get("DWT", 0))
                except:
                    dwt_int = 0
                
                # Scrape if GRT or DWT are 0, missing, default (5000/8000), or Class is missing
                is_default_or_invalid = (
                    grt_int <= 0 or 
                    dwt_int <= 0 or 
                    (grt_int == 5000 and dwt_int == 8000) or 
                    not cached.get("Class")
                )
                if is_default_or_invalid:
                    vessels_to_scrape_details.append(v)
                else:
                    # Keep cached
                    v["Class"] = cached.get("Class", "PHRS")
                    v["GRT"] = grt_int
                    v["DWT"] = dwt_int
            else:
                # Completely new vessel
                vessels_to_scrape_details.append(v)
                
        print(f"{len(vessels_to_scrape_details)} gemi için B2B detay sayfası sorgulanacak (diğerleri önbellekten korundu)...")
        
        # 6. Fetch details in parallel using ThreadPoolExecutor
        scraped_count = 0
        
        def process_vessel_details(vessel):
            v_id = vessel["id"]
            details = get_vessel_details(session, v_id)
            if details:
                gt, dwt, v_class = details
                return vessel["Vessel"], gt, dwt, v_class
            return None

        # Execute parallel requests (max 15 workers to be polite and avoid rate limits)
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_vessel = {executor.submit(process_vessel_details, v): v for v in vessels_to_scrape_details}
            for future in as_completed(future_to_vessel):
                res = future.result()
                if res:
                    v_name, gt, dwt, v_class = res
                    # Update the vessel dict
                    for v in all_scraped_vessels:
                        if v["Vessel"] == v_name:
                            v["GRT"] = gt
                            v["DWT"] = dwt
                            v["Class"] = v_class
                            break
                    scraped_count += 1
                    if scraped_count % 10 == 0:
                        print(f"{scraped_count}/{len(vessels_to_scrape_details)} gemi detayı çekildi...")
                        
        # Fill defaults for any that failed details scraping
        for v in all_scraped_vessels:
            if "Class" not in v: v["Class"] = "PHRS"
            if "GRT" not in v: v["GRT"] = 5000
            if "DWT" not in v: v["DWT"] = 8000
            
        # 7. Write to Excel files
        df_out = pd.DataFrame(all_scraped_vessels)
        # Reorder columns to match original template
        desired_cols = ["Vessel", "IMO", "Type", "Flag", "Class", "GRT", "DWT", "PHRS_No", "Reg_No", "Status"]
        df_out = df_out[[c for c in desired_cols if c in df_out.columns]]
        
        date_str = datetime.now().strftime('%d_%m_%Y')
        filename_dated = f"PHRS_Tum_Gemiler_{date_str}.xlsx"
        df_out.to_excel(filename_dated, index=False)
        print(f"Yedek dated Excel dosyası kaydedildi: {filename_dated}")
        
        df_out.to_excel(filename_portal, index=False)
        print(f"Ana Excel dosyası güncellendi: {filename_portal}")
        
        # Synchronize with Desktop/PHRS_Bot directory
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\LIVAPC8")
        bot_cand = os.path.join(user_profile, "Desktop", "PHRS_Bot")
        if os.path.exists(bot_cand):
            target_path = os.path.join(bot_cand, "PHRS_Tüm_Gemiler.xlsx")
            try:
                df_out.to_excel(target_path, index=False)
                print(f"PHRS_Bot klasörüne senkronize edildi: {target_path}")
            except Exception as e:
                print(f"Senkronizasyon hatası: {e}")
                
    finally:
        session.close()
        # Clean up temp PEM files
        if os.path.exists(TEMP_CERT): os.remove(TEMP_CERT)
        if os.path.exists(TEMP_KEY): os.remove(TEMP_KEY)
        print("Geçici sertifika dosyaları temizlendi.")
        
if __name__ == "__main__":
    main()
