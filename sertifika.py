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
                    flag = clean_tds[3] if len(clean_tds) > 3 else "Panama"
                    cert_name = clean_tds[6]
                    
                    expiry_date_text = clean_tds[7].strip()
                    if not expiry_date_text and len(clean_tds) >= 9:
                        expiry_date_text = clean_tds[8].strip()
                    
                    # Verify date format is valid
                    if expiry_date_text:
                        page_certs.append({
                            "Gemi Adı": ship_name,
                            "IMO": imo,
                            "Flag": flag,
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

def get_total_pages_with_temp_session(cert_path, key_path):
    print("Geçici oturum ile toplam sayfa adedi alınıyor...")
    session = requests.Session()
    session.cert = (cert_path, key_path)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        session.get("https://b2b.phrs.gr/Home/Login", timeout=15)
        payload = {
            "Username": "b.yener",
            "password": "940523Begg?!?."
        }
        r_login = session.post("https://b2b.phrs.gr/Home/Login", data=payload, timeout=15)
        if r_login.text.strip().strip('"') != "OK":
            print("Geçici oturum girişi başarısız!")
            return 228
            
        r_parent = session.get("https://b2b.phrs.gr/Vessels/VesselsQueries", timeout=15)
        match_items = re.search(r"items:\s*(\d+)", r_parent.text)
        total_items = int(match_items.group(1)) if match_items else 5681
        items_on_page = 25
        total_pages = (total_items + items_on_page - 1) // items_on_page
        print(f"Toplam sayfa: {total_pages} (Kayıt sayısı: {total_items})")
        return total_pages
    except Exception as e:
        print(f"Geçici oturum sorgu hatası: {e}")
        return 228
    finally:
        session.close()

def login_session(cert_path, key_path):
    session = requests.Session()
    session.cert = (cert_path, key_path)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    session.get("https://b2b.phrs.gr/Home/Login", timeout=15)
    payload = {
        "Username": "b.yener",
        "password": "940523Begg?!?."
    }
    r = session.post("https://b2b.phrs.gr/Home/Login", data=payload, timeout=15)
    if r.text.strip().strip('"') != "OK":
        raise ValueError("Login failed")
    return session

def scrape_with_session(session, page_range, desc=""):
    print(f"[{desc}] Sertifikalar paralel olarak çekiliyor (Sayfa {min(page_range)}-{max(page_range)})...")
    results = []
    completed_pages = 0
    total_to_fetch = len(page_range)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_page = {executor.submit(parse_cert_page, session, p): p for p in page_range}
        for future in as_completed(future_to_page):
            page_data = future.result()
            if page_data:
                results.extend(page_data)
            completed_pages += 1
            if completed_pages % 20 == 0 or completed_pages == total_to_fetch:
                print(f"[{desc}] {completed_pages}/{total_to_fetch} sayfa tamamlandı...")
    return results

def main():
    print("PHRS B2B Sertifika Tarihleri Scraper başlatılıyor...")
    
    try:
        if os.path.exists(TEMP_CERT) and os.path.exists(TEMP_KEY):
            print("Using existing temp PEM certificates.")
            cert_path, key_path = TEMP_CERT, TEMP_KEY
        else:
            cert_path, key_path = extract_cert_key()
    except Exception as e:
        print(f"Hata: İstemci sertifikası yüklenemedi: {e}")
        sys.exit(1)
        
    total_pages = get_total_pages_with_temp_session(cert_path, key_path)
    
    all_certs = []
    
    # 1. Tainted Session (visiting VesselsQueries) to get historical/expired records
    try:
        print("\n--- 1/2: Tainted Oturum (VesselsQueries ziyaret ediliyor) ---")
        session_tainted = login_session(cert_path, key_path)
        session_tainted.get("https://b2b.phrs.gr/Vessels/VesselsQueries", timeout=15)
        
        certs_tainted = scrape_with_session(session_tainted, range(1, total_pages + 1), "Tainted")
        print(f"Tainted oturum ile {len(certs_tainted)} kayıt çekildi.")
        all_certs.extend(certs_tainted)
        session_tainted.close()
    except Exception as e:
        print(f"Tainted oturum taramasında hata oluştu: {e}")

    # 2. Untainted Session (NOT visiting VesselsQueries) to get future/active records
    try:
        print("\n--- 2/2: Temiz Grid Oturumu (VesselsQueries ziyaret edilmiyor) ---")
        session_untainted = login_session(cert_path, key_path)
        
        # Scrape pages 1 to 10 to cover the future active records (~70 records)
        certs_untainted = scrape_with_session(session_untainted, range(1, 11), "Untainted")
        print(f"Temiz grid oturumu ile {len(certs_untainted)} kayıt çekildi.")
        all_certs.extend(certs_untainted)
        session_untainted.close()
    except Exception as e:
        print(f"Temiz grid oturumu taramasında hata oluştu: {e}")

    # 3. Merge & Deduplicate
    if not all_certs:
        print("Hata: Hiçbir sertifika verisi çekilemedi.")
        if os.path.exists(TEMP_CERT): os.remove(TEMP_CERT)
        if os.path.exists(TEMP_KEY): os.remove(TEMP_KEY)
        return
        
    df_raw = pd.DataFrame(all_certs)
    # Deduplicate based on ship name, certificate name, and expiry date
    df_raw = df_raw.drop_duplicates(subset=["Gemi Adı", "Sertifika", "Bitiş Tarihi"])
    print(f"Tekilleştirme sonrası toplam {len(df_raw)} sertifika kaydı kaldı.")
    
    # 4. Filter expired and expiring (< 365 days) certificates
    today = datetime.now()
    critical_ships = []
    
    for _, c in df_raw.iterrows():
        date_str = str(c["Bitiş Tarihi"])
        try:
            expiry_date = datetime.strptime(date_str, "%d/%m/%Y")
        except:
            try:
                expiry_date = pd.to_datetime(date_str)
            except:
                continue
                
        status = "Süresi Dolan!" if expiry_date < today else "Süresi Yaklaşıyor"
        critical_ships.append({
            "Gemi Adı": c["Gemi Adı"],
            "IMO": c["IMO"],
            "Flag": c.get("Flag", "Panama"),
            "Sertifika": c["Sertifika"],
            "Bitiş Tarihi": date_str,
            "Durum": status
        })
            
    # 5. Export results to Excel
    if not critical_ships:
        print("Harika, sistemde kritik durumda olan hiçbir sertifika bulunamadı.")
        if os.path.exists(TEMP_CERT): os.remove(TEMP_CERT)
        if os.path.exists(TEMP_KEY): os.remove(TEMP_KEY)
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
            
    # Clean up temp PEM files
    if os.path.exists(TEMP_CERT): os.remove(TEMP_CERT)
    if os.path.exists(TEMP_KEY): os.remove(TEMP_KEY)
    print("Geçici sertifika dosyaları temizlendi.")

if __name__ == "__main__":
    main()

