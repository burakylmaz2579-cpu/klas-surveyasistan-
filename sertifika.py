from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pandas as pd
import time

# Chrome güvenlik ayarlarını atla ve arka planda (headless) çalıştır
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def login_and_navigate():
    print("Sertifika uyarısı çıkarsa lütfen 'Tamam' butonuna bas...")
    driver.get("https://b2b.phrs.gr/Home/Login")
    time.sleep(2)
    
    # Giriş bilgileri
    driver.find_element(By.ID, "UserName").send_keys("b.yener")
    driver.find_element(By.ID, "Password").send_keys("940523Begg?!?.")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    time.sleep(5)
    driver.get("https://b2b.phrs.gr/Vessels/VesselsQueries")
    time.sleep(4) # Tablonun ilk yüklenmesi için biraz daha fazla bekliyoruz

def scan_certificates():
    warning_date = datetime.now() + timedelta(days=30)
    critical_ships = []
    sayfa_no = 1
    
    while True:
        print(f"Sayfa {sayfa_no} taranıyor...")
        
        # Tablodaki tüm satırları bul
        rows = driver.find_elements(By.XPATH, "//table[@id='CompanyTableBody']/tbody/tr")
        
        for row in rows:
            try:
                ship_name = row.find_element(By.XPATH, "./td[1]").text.strip()
                if not ship_name or ship_name == "Name":
                    continue
                    
                cert_name = row.find_element(By.XPATH, "./td[7]").text.strip()
                expiry_date_text = row.find_element(By.XPATH, "./td[9]").text.strip()
                expiry_date = datetime.strptime(expiry_date_text, "%d/%m/%Y")
                
                if expiry_date <= warning_date:
                    status = "Süresi Doldu!" if expiry_date < datetime.now() else "Süresi Yaklaşıyor"
                    critical_ships.append({
                        "Gemi Adı": ship_name,
                        "Sertifika": cert_name,
                        "Bitiş Tarihi": expiry_date_text,
                        "Durum": status
                    })
            except Exception as e:
                continue
                
        # --- BUTON YAKALAMA SİSTEMİ ---
        try:
            next_button = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'NEXT', 'next'), 'next')]")
            
            if "disabled" in next_button.get_attribute("class") or next_button.get_attribute("disabled"):
                print("Son sayfaya ulaşıldı, tarama bitti.")
                break
                
            driver.execute_script("arguments[0].click();", next_button)
            sayfa_no += 1
            time.sleep(3) 
            
        except:
            try:
                hedef_sayfa = str(sayfa_no + 1)
                numara_butonu = driver.find_element(By.XPATH, f"//*[normalize-space(text())='{hedef_sayfa}']")
                
                driver.execute_script("arguments[0].click();", numara_butonu)
                sayfa_no += 1
                time.sleep(3)
                
            except:
                print("Sonraki sayfa bulunamadı. Tarama tamamlandı.")
                break

    return critical_ships

def export_to_excel(data):
    import os
    if not data:
        print("Harika, sistemde kritik durumda olan hiçbir sertifika bulunamadı.")
        return
        
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime('%d_%m_%Y')
    
    # Save to local directory where script is run
    filename_local = f"PHRS_Acil_Sertifikalar_{date_str}.xlsx"
    df.to_excel(filename_local, index=False)
    print(f"İşlem tamamlandı! Rapor kaydedildi: {filename_local}")
    
    # Save to portal workspace (overwrite default name)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename_portal = os.path.join(script_dir, "PHRS_Acil_Sertifikalar.xlsx")
    try:
        df.to_excel(filename_portal, index=False)
        print(f"Portal veritabanı dosyası başarıyla güncellendi: {filename_portal}")
    except Exception as e:
        print(f"Portal dosyası güncellenirken hata oluştu: {e}")

try:
    login_and_navigate()
    data = scan_certificates()
    export_to_excel(data)
finally:
    time.sleep(3)
    driver.quit()
