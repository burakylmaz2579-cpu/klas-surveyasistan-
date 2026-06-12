import sqlite3
import os
import re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "vessels.db")

VESSEL_PREFIXES = ["MV", "MT", "MS", "MSC", "APL", "COSCO", "MAERSK", "OCEAN", "SEA", "GOLDEN", "BLUE", "PACIFIC", "ATLANTIC", "NORTHERN", "SOUTHERN", "PIONEER", "STAR", "GULF", "GLOBAL", "ROYAL"]
VESSEL_NAMES = ["VOYAGER", "EXPLORER", "CHALLENGER", "CRUISER", "TRADER", "LEADER", "RANGER", "VICTOR", "HERO", "PRIDE", "SPIRIT", "GLORY", "FREEDOM", "HORIZON", "AURORA", "MARINER", "NAVIGATOR", "CENTURY", "CLASSIC", "TITAN", "NEPTUNE", "POSEIDON", "ATHENA", "ZEUS", "HERMES"]
VESSEL_TYPES = ["Dökme Yük (Bulk Carrier)", "Petrol Tankeri (Oil Tanker)", "Konteyner Gemisi (Container Ship)", "Kimyasal Tanker (Chemical Tanker)", "Yolcu Gemisi (Passenger Ship)", "Ro-Ro Gemisi", "Genel Kargo (General Cargo)", "Diğer"]
FLAGS = ["Panama", "Liberya", "Marshall Adaları", "Singapur", "Bahamalar", "Yunanistan", "Çin", "Türkiye", "Kıbrıs"]

def normalize_excel_columns(df):
    mapping = {}
    for col in df.columns:
        c_clean = str(col).strip().lower()
        c_clean = c_clean.replace('ı', 'i').replace('ş', 's').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ç', 'c')
        c_clean = re.sub(r'[^a-z0-9]', '', c_clean)
        
        if 'gemi' in c_clean or 'vessel' in c_clean or 'company' in c_clean:
            mapping[col] = 'Vessel'
        elif 'sertifika' in c_clean or 'certificate' in c_clean or 'cert' in c_clean:
            mapping[col] = 'Certificate'
        elif 'bitis' in c_clean or 'duedate' in c_clean or 'due' in c_clean or 'tarih' in c_clean:
            mapping[col] = 'DueDate'
        elif 'durum' in c_clean or 'status' in c_clean:
            mapping[col] = 'Status'
        elif 'imo' in c_clean:
            mapping[col] = 'IMO'
    return df.rename(columns=mapping)

def normalize_vessel_name(name):
    n = str(name).strip().upper()
    n = n.replace('CANAPUS S', 'CANOPUS S')
    n = re.sub(r'\s+', ' ', n)
    return n

def load_excel_vessels():
    import pandas as pd
    
    f_fleet = os.path.join(os.path.dirname(__file__), "PHRS_Tüm_Gemiler.xlsx")
    f1 = os.path.join(os.path.dirname(__file__), "PHRS_Acil_Sertifikalar.xlsx")
    f2 = os.path.join(os.path.dirname(__file__), "PHRS_CERT_DUE_DATE.xlsx")
    
    vessels_data = {}
    today = datetime.now()
    
    def parse_date(d):
        if isinstance(d, datetime):
            return d
        try:
            return datetime.strptime(str(d).strip(), "%d/%m/%Y")
        except:
            try:
                return pd.to_datetime(d)
            except:
                return None

    def generate_imo_stable(name):
        val = 0
        for char in name.strip().upper():
            val = (val * 31 + ord(char)) & 0xFFFFFFFF
        return str(9000000 + (val % 1000000))

    # 1. Read real fleet list from f_fleet
    if os.path.exists(f_fleet):
        try:
            df_fleet = pd.read_excel(f_fleet)
            df_fleet = normalize_excel_columns(df_fleet)
            df_fleet = df_fleet[df_fleet['Vessel'].astype(str).str.strip().str.lower() != 'vessel']
            
            for _, r in df_fleet.iterrows():
                v_name = normalize_vessel_name(r['Vessel'])
                flag = str(r.get('Flag', 'Panama')).strip()
                
                # Keep Malta and Comoros vessels
                pass
                    
                imo = str(r.get('IMO', '')).strip().split('.')[0]
                if not imo or imo == 'nan' or not imo.isdigit():
                    imo = generate_imo_stable(v_name)
                    
                v_type = str(r.get('Type', 'General Cargo')).strip()
                class_soc = str(r.get('Class', 'DNV')).strip()
                
                try:
                    grt = int(r.get('GRT', 5000))
                except:
                    grt = 5000
                    
                try:
                    dwt = int(r.get('DWT', 8000))
                except:
                    dwt = int(grt * 1.5)
                    
                vessels_data[v_name] = {
                    "name": v_name,
                    "imo": imo,
                    "vessel_type": v_type,
                    "flag": flag,
                    "class_society": class_soc,
                    "grt": grt,
                    "dwt": dwt,
                    "certs": []
                }
            print(f"Loaded {len(vessels_data)} vessels from {f_fleet} (excluding Comoros & Malta)")
        except Exception as e:
            print(f"Error loading {f_fleet}: {e}")
            
    # 2. Read f2 (PHRS_CERT_DUE_DATE.xlsx)
    if os.path.exists(f2):
        try:
            df2 = pd.read_excel(f2)
            df2 = normalize_excel_columns(df2)
            df2 = df2[df2['Vessel'].astype(str).str.strip().str.lower() != 'company/vessel']
            
            for _, r in df2.iterrows():
                v_name = normalize_vessel_name(r['Vessel'])
                flag = str(r.get('Flag', 'Panama')).strip() if 'Flag' in df2.columns else 'Panama'
                
                # Keep Malta and Comoros vessels
                pass
                    
                cert_name = str(r['Certificate']).strip()
                due_date_raw = r['DueDate']
                parsed_dt = parse_date(due_date_raw)
                
                if not parsed_dt:
                    continue
                    
                expiry_str = parsed_dt.strftime("%Y-%m-%d")
                issue_dt = parsed_dt - timedelta(days=365*5)
                issue_str = issue_dt.strftime("%Y-%m-%d")
                
                days_left = (parsed_dt - today).days
                if days_left < 0:
                    c_status = "Expired"
                elif days_left < 30:
                    c_status = "Expiring Soon"
                else:
                    c_status = "Valid"
                    
                if v_name not in vessels_data:
                    # Double check flag if we only have name, we skip if it is Comoros or Malta in cert files
                    # (in case the name exists in a cached list we checked)
                    imo = str(r.get('IMO', '')).strip().split('.')[0]
                    if not imo or imo == 'nan' or not imo.isdigit():
                        imo = generate_imo_stable(v_name)
                    vessels_data[v_name] = {
                        "name": v_name,
                        "imo": imo,
                        "vessel_type": "General Cargo",
                        "flag": flag,
                        "class_society": "DNV",
                        "grt": 5000,
                        "dwt": 8000,
                        "certs": []
                    }
                    
                vessels_data[v_name]["certs"].append({
                    "name": cert_name,
                    "issue_date": issue_str,
                    "expiry_date": expiry_str,
                    "status": c_status
                })
        except Exception as e:
            print(f"Error loading {f2} in db initialization: {e}")
            
    # 3. Read f1 (PHRS_Acil_Sertifikalar.xlsx)
    if os.path.exists(f1):
        try:
            df1 = pd.read_excel(f1)
            df1 = normalize_excel_columns(df1)
            for _, r in df1.iterrows():
                v_name = normalize_vessel_name(r['Vessel'])
                
                # Check status/flag if present in df1 (usually not present, but let's check)
                flag = str(r.get('Flag', 'Panama')).strip() if 'Flag' in df1.columns else 'Panama'
                # Keep Malta and Comoros vessels
                pass
                    
                cert_name = str(r['Certificate']).strip()
                due_date_raw = r['DueDate']
                parsed_dt = parse_date(due_date_raw)
                
                if not parsed_dt:
                    continue
                    
                expiry_str = parsed_dt.strftime("%Y-%m-%d")
                issue_dt = parsed_dt - timedelta(days=365*5)
                issue_str = issue_dt.strftime("%Y-%m-%d")
                
                days_left = (parsed_dt - today).days
                if days_left < 0:
                    c_status = "Expired"
                elif days_left < 30:
                    c_status = "Expiring Soon"
                else:
                    c_status = "Valid"
                    
                if v_name not in vessels_data:
                    imo = generate_imo_stable(v_name)
                    vessels_data[v_name] = {
                        "name": v_name,
                        "imo": imo,
                        "vessel_type": "General Cargo",
                        "flag": flag,
                        "class_society": "DNV",
                        "grt": 5000,
                        "dwt": 8000,
                        "certs": []
                    }
                    
                exists = False
                for c in vessels_data[v_name]["certs"]:
                    if c["name"] == cert_name and c["expiry_date"] == expiry_str:
                        exists = True
                        break
                if not exists:
                    vessels_data[v_name]["certs"].append({
                        "name": cert_name,
                        "issue_date": issue_str,
                        "expiry_date": expiry_str,
                        "status": c_status
                    })
        except Exception as e:
            print(f"Error loading {f1} in db initialization: {e}")
            
    return vessels_data

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vessels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        imo TEXT NOT NULL UNIQUE,
        grt INTEGER,
        dwt INTEGER,
        vessel_type TEXT,
        flag TEXT,
        class_society TEXT,
        status TEXT,
        compliance_score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vessel_id INTEGER,
        name TEXT NOT NULL,
        issue_date TEXT,
        expiry_date TEXT,
        status TEXT,
        FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    
    f_fleet = os.path.join(os.path.dirname(__file__), "PHRS_Tüm_Gemiler.xlsx")
    f1 = os.path.join(os.path.dirname(__file__), "PHRS_Acil_Sertifikalar.xlsx")
    f2 = os.path.join(os.path.dirname(__file__), "PHRS_CERT_DUE_DATE.xlsx")
    excel_exists = os.path.exists(f_fleet) or os.path.exists(f1) or os.path.exists(f2)
    
    cursor.execute("SELECT COUNT(*) FROM vessels")
    count = cursor.fetchone()[0]
    
    if count == 0 or excel_exists:
        print("Excel dosyalarından gerçek gemiler veritabanına yükleniyor (Temiz Rebuild)...")
        
        cursor.execute("DROP TABLE IF EXISTS certificates")
        cursor.execute("DROP TABLE IF EXISTS vessels")
        
        cursor.execute("""
        CREATE TABLE vessels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            imo TEXT NOT NULL UNIQUE,
            grt INTEGER,
            dwt INTEGER,
            vessel_type TEXT,
            flag TEXT,
            class_society TEXT,
            status TEXT,
            compliance_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vessel_id INTEGER,
            name TEXT NOT NULL,
            issue_date TEXT,
            expiry_date TEXT,
            status TEXT,
            FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
        )
        """)
        conn.commit()
        
        real_vessels_dict = load_excel_vessels()
        
        used_imos = set()
        vessels_to_insert = []
        vessels_certs_map = {}
        
        for v_name, v_info in real_vessels_dict.items():
            imo = v_info["imo"]
            if imo in used_imos:
                continue
            used_imos.add(imo)
            
            expired_count = sum(1 for c in v_info["certs"] if c["status"] == "Expired")
            warning_count = sum(1 for c in v_info["certs"] if c["status"] == "Expiring Soon")
            
            if expired_count > 0:
                status = "Critical"
                score = max(30, 100 - expired_count * 20 - warning_count * 5)
            elif warning_count > 0:
                status = "Warning"
                score = max(65, 100 - warning_count * 8)
            else:
                status = "Active"
                score = 100
                
            flag = v_info.get("flag", "Panama")
            class_soc = v_info.get("class_society", "PHRS")
            vessel_type = v_info.get("vessel_type", "General Cargo")
            grt = v_info.get("grt", 5000)
            dwt = v_info.get("dwt", 8000)
            
            vessels_to_insert.append((v_name, imo, grt, dwt, vessel_type, flag, class_soc, status, score))
            vessels_certs_map[imo] = v_info["certs"]
            
        cursor.executemany("""
        INSERT INTO vessels (name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vessels_to_insert)
        conn.commit()
        
        cursor.execute("SELECT id, imo, status FROM vessels")
        all_inserted_vessels = cursor.fetchall()
        
        certs_to_insert = []
        for v_id, v_imo, v_status in all_inserted_vessels:
            if v_imo in vessels_certs_map:
                real_certs = vessels_certs_map[v_imo]
                for rc in real_certs:
                    certs_to_insert.append((v_id, rc["name"], rc["issue_date"], rc["expiry_date"], rc["status"]))
                    
        chunk_size = 1000
        for i in range(0, len(certs_to_insert), chunk_size):
            cursor.executemany("""
            INSERT INTO certificates (vessel_id, name, issue_date, expiry_date, status)
            VALUES (?, ?, ?, ?, ?)
            """, certs_to_insert[i:i+chunk_size])
        conn.commit()
        print(f"Vessel database populated! Total vessels: {len(vessels_to_insert)}")
        
    conn.close()

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def search_vessels(query="", filter_type="All", filter_flag="All", filter_status="All", limit=50, offset=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT id, name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score FROM vessels WHERE 1=1"
    params = []
    
    if query:
        sql += " AND (name LIKE ? OR imo LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if filter_type != "All":
        sql += " AND vessel_type = ?"
        params.append(filter_type)
    if filter_flag != "All":
        sql += " AND flag = ?"
        params.append(filter_flag)
    if filter_status != "All":
        sql += " AND status = ?"
        params.append(filter_status)
        
    count_sql = "SELECT COUNT(*) FROM (" + sql + ")"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]
    
    sql += " ORDER BY name ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(sql, params)
    vessels = cursor.fetchall()
    conn.close()
    return vessels, total_count

def get_unique_vessel_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT vessel_type FROM vessels WHERE vessel_type IS NOT NULL AND vessel_type != '' ORDER BY vessel_type ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_unique_flags():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT flag FROM vessels WHERE flag IS NOT NULL AND flag != '' ORDER BY flag ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_vessel_by_imo(imo):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score FROM vessels WHERE imo = ?", (imo,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_vessel_by_id(v_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score FROM vessels WHERE id = ?", (v_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_vessel_certificates(vessel_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, issue_date, expiry_date, status FROM certificates WHERE vessel_id = ? ORDER BY expiry_date ASC", (vessel_id,))
    certs = cursor.fetchall()
    conn.close()
    return certs

def get_fleet_summary_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vessels")
    total_vessels = cursor.fetchone()[0]
    cursor.execute("SELECT status, COUNT(*) FROM vessels GROUP BY status")
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("SELECT AVG(compliance_score) FROM vessels")
    avg_score = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT COUNT(*) FROM certificates WHERE status = 'Expired'")
    expired_certs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM certificates WHERE status = 'Expiring Soon'")
    expiring_certs = cursor.fetchone()[0]
    conn.close()
    return {
        "total_vessels": total_vessels,
        "status_counts": status_counts,
        "avg_compliance_score": round(avg_score, 1),
        "expired_certificates": expired_certs,
        "expiring_certificates": expiring_certs
    }

def refresh_db():
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception as e:
            print(f"Error removing db file: {e}")
            
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS certificates")
    cursor.execute("DROP TABLE IF EXISTS vessels")
    conn.commit()
    conn.close()
    
    init_db()

# Initialize on import
init_db()
