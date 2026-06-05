import requests
import os
import re
import sys
import time
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

# Global paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_CERT = os.path.join(SCRIPT_DIR, "temp_cert_certs.pem")
TEMP_KEY = os.path.join(SCRIPT_DIR, "temp_key_certs.pem")

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

def parse_cert_page(session, page_no):
    retries = 3
    for attempt in range(retries):
        try:
            url = f"https://b2b.phrs.gr/Vessels/VesselsQueriesGrid?Page={page_no}&FromFilter=0"
            # The grid uses POST as defined in Javascript
            r = session.post(url, timeout=30)
            if r.status_code != 200:
                continue
                
            # Extract rows using regex
            trs = re.findall(r'<tr[^>]*>.*?</tr>', r.text, re.DOTALL)
            page_certs = []
            
            # Skip header if it is present
            for row in trs:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                clean_tds = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]
                
                if len(clean_tds) >= 8:
                    ship_name = clean_tds[0]
                    if not ship_name or ship_name.lower() in ["name", "gemi adı", "όνομα"]:
                        continue
                        
                    imo = clean_tds[2]
                    cert_name = clean_tds[6]
                    expiry_date_text = clean_tds[7]
                    
                    # Verify date format is valid
                    if expiry_date_text:
                        page_certs.append({
                            "Gemi Adı": ship_name,
                            "IMO": imo,
                            "Sertifika": cert_name,
                            "Bitiş Tarihi": expiry_date_text
                        })
            
            if not page_certs:
                raise ValueError("No certificate rows found on page (possible rate limit or session redirect)")
                
            return page_certs
        except Exception as e:
            if attempt == retries - 1:
                print(f"Error parsing page {page_no} after {retries} attempts: {e}")
            time.sleep(1.5)
    return []

def main():
    print("PHRS B2B Sertifika Tarihleri Scraper başlatılıyor...")
    
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
        # 1. Log in to portal
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
            
        print("Giriş başarılı! Sayfa adetleri sorgulanıyor...")
        
        # 2. Get total item count from parent page
        r_parent = session.get("https://b2b.phrs.gr/Vessels/VesselsQueries", timeout=15)
        match_items = re.search(r"items:\s*(\d+)", r_parent.text)
        total_items = int(match_items.group(1)) if match_items else 5674
        items_on_page = 25
        total_pages = (total_items + items_on_page - 1) // items_on_page
        print(f"Sistemde toplam {total_items} sertifika kaydı ({total_pages} sayfa) tespit edildi.")
        
        # 3. Fetch all pages in parallel
        all_certs = []
        completed_pages = 0
        
        print("Sertifikalar paralel olarak çekiliyor...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_page = {executor.submit(parse_cert_page, session, p): p for p in range(1, total_pages + 1)}
            for future in as_completed(future_to_page):
                page_data = future.result()
                if page_data:
                    all_certs.extend(page_data)
                completed_pages += 1
                if completed_pages % 20 == 0 or completed_pages == total_pages:
                    print(f"{completed_pages}/{total_pages} sayfa tamamlandı...")
                    
        print(f"Toplam {len(all_certs)} sertifika kaydı başarıyla indirildi.")
        
        # 4. Filter expired and expiring (< 365 days) certificates
        warning_date = datetime.now() + timedelta(days=365)
        today = datetime.now()
        critical_ships = []
        
        for c in all_certs:
            date_str = c["Bitiş Tarihi"]
            try:
                expiry_date = datetime.strptime(date_str, "%d/%m/%Y")
            except:
                try:
                    expiry_date = pd.to_datetime(date_str)
                except:
                    continue
                    
            status = "Süresi Doldu!" if expiry_date < today else "Süresi Yaklaşıyor"
            critical_ships.append({
                "Gemi Adı": c["Gemi Adı"],
                "IMO": c["IMO"],
                "Sertifika": c["Sertifika"],
                "Bitiş Tarihi": date_str,
                "Durum": status
            })
                
        # 5. Export results to Excel
        if not critical_ships:
            print("Harika, sistemde kritik durumda olan hiçbir sertifika bulunamadı.")
            return
            
        df = pd.DataFrame(critical_ships)
        date_str_file = datetime.now().strftime('%d_%m_%Y')
        filename_dated = f"PHRS_Acil_Sertifikalar_{date_str_file}.xlsx"
        df.to_excel(filename_dated, index=False)
        print(f"Yedek dated Excel dosyası kaydedildi: {filename_dated}")
        
        filename_portal = os.path.join(SCRIPT_DIR, "PHRS_Acil_Sertifikalar.xlsx")
        df.to_excel(filename_portal, index=False)
        print(f"Ana Excel dosyası güncellendi: {filename_portal}")
        
        # Synchronize with Desktop/PHRS_Bot directory
        user_profile = os.environ.get("USERPROFILE", "C:\\Users\\LIVAPC8")
        bot_cand = os.path.join(user_profile, "Desktop", "PHRS_Bot")
        if os.path.exists(bot_cand):
            target_path = os.path.join(bot_cand, "PHRS_Acil_Sertifikalar.xlsx")
            try:
                df.to_excel(target_path, index=False)
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
