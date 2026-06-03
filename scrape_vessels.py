from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
import time
import sys
import re
import os

# CLI options setup
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')

if '--headless' in sys.argv:
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    print("Selenium tarayici arka plan (headless) modunda calistiriliyor.")
else:
    print("Selenium tarayici normal pencere modunda calistiriliyor.")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

def login_and_navigate():
    print("B2B portalina baglaniliyor...")
    driver.get("https://b2b.phrs.gr/Home/Login")
    time.sleep(3)
    
    # Giriş bilgileri
    driver.find_element(By.ID, "UserName").send_keys("b.yener")
    driver.find_element(By.ID, "Password").send_keys("940523Begg?!?.")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    print("Giris yapildi. Dashboard'un yuklenmesi bekleniyor...")
    time.sleep(6)
    
    print("MyVessels sayfasina gidiliyor...")
    driver.get("https://b2b.phrs.gr/Vessels/MyVessels")
    time.sleep(5)

def scrape_all_vessels():
    all_vessels = []
    sayfa_no = 1
    scraped_names = set() # Track unique vessel names to prevent infinite loop
    
    while True:
        print(f"Sayfa {sayfa_no} taraniyor...")
        
        # B2B MyVessels grid uses custom divs containing 'nameClass' class for the vessel name column
        name_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'nameClass')]")
        print(f"Bu sayfada {len(name_divs)} gemi satiri bulundu.")
        
        if not name_divs:
            print("Gemi listesi bulunamadi veya sayfa yuklenemedi!")
            break
            
        new_vessels_on_this_page = 0
        
        for nd in name_divs:
            try:
                # The row container is the parent element of the name div
                row = nd.find_element(By.XPATH, "..")
                cells = row.find_elements(By.XPATH, "./div")
                if len(cells) < 8:
                    continue
                    
                vessel_name = cells[1].text.strip()
                # Skip header row if matches 'Όνομα' or 'Name'
                if not vessel_name or vessel_name.lower() in ["name", "gemi adi", "gemi adi", "όνομα"]:
                    continue
                
                # If we've already scraped this vessel, skip it
                if vessel_name in scraped_names:
                    continue
                    
                scraped_names.add(vessel_name)
                new_vessels_on_this_page += 1
                
                phrs_no = cells[2].text.strip()
                imo = cells[3].text.strip()
                flag = cells[4].text.strip()
                reg_no = cells[5].text.strip()
                v_type = cells[6].text.strip()
                status = cells[7].text.strip()
                
                # Normalize IMO (vessel_db expects valid string digits)
                if not imo or imo == "nan" or not imo.isdigit():
                    imo = ""
                    
                # Setup defaults for Class, GRT, DWT (which are not in this list)
                class_soc = "DNV"
                grt = 5000
                dwt = 8000
                
                all_vessels.append({
                    "Vessel": vessel_name,
                    "IMO": imo,
                    "Type": v_type,
                    "Flag": flag,
                    "Class": class_soc,
                    "GRT": grt,
                    "DWT": dwt,
                    "PHRS_No": phrs_no,
                    "Reg_No": reg_no,
                    "Status": status
                })
            except Exception as e:
                continue
                
        print(f"Bu sayfadan {new_vessels_on_this_page} yeni gemi eklendi.")
        
        # Self-healing: if no new vessels were added, we reached the end or are looping
        if new_vessels_on_this_page == 0:
            print("Yeni gemi bulunamadi (sayfa sonu veya tekrar). Tarama sonlandiriliyor.")
            break
            
        # --- PAGINATION ---
        try:
            # Locate next button link element (specifically target the anchor <a> tag with class containing 'next')
            next_button = driver.find_element(By.XPATH, "//a[contains(@class, 'next')]")
            if "disabled" in next_button.get_attribute("class") or next_button.get_attribute("disabled"):
                print("Son sayfaya ulasildi, tarama bitti.")
                break
                
            driver.execute_script("arguments[0].click();", next_button)
            sayfa_no += 1
            time.sleep(4) # Wait for page grid load
        except Exception as ex:
            # Fallback to page number click if next button fails
            try:
                hedef_sayfa = str(sayfa_no + 1)
                numara_butonu = driver.find_element(By.XPATH, f"//a[normalize-space(text())='{hedef_sayfa}']")
                driver.execute_script("arguments[0].click();", numara_butonu)
                sayfa_no += 1
                time.sleep(4)
            except:
                print("Sonraki sayfa dugmesi bulunamadi veya tiklanamadi. Tarama bitti.")
                break
                
    return all_vessels

def export_to_excel(data):
    import os
    if not data:
        print("Sistemde kaydedilecek gemi bulunamadi!")
        return
        
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime('%d_%m_%Y')
    
    # Save a dated copy in local execution dir
    filename_local = f"PHRS_Tum_Gemiler_{date_str}.xlsx"
    df.to_excel(filename_local, index=False)
    print(f"Islem tamamlandi! Filo listesi kaydedildi: {filename_local}")
    
    # Sync file to the target paths
    target_dirs = [
        r"C:\Users\LIVAPC8\Desktop\KODLAR\YENI DENEYİŞ",
        r"C:\Users\LIVAPC8\Desktop\PHRS_Bot"
    ]
    
    for t_dir in target_dirs:
        if os.path.exists(t_dir):
            target_path = os.path.join(t_dir, "PHRS_Tum_Gemiler.xlsx")
            try:
                df.to_excel(target_path, index=False)
                print(f"Dosya kopyalandi ve guncellendi: {target_path}")
            except Exception as e:
                print(f"Hata ({target_path}): {e}")

try:
    login_and_navigate()
    data = scrape_all_vessels()
    export_to_excel(data)
finally:
    time.sleep(3)
    driver.quit()
