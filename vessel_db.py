import sqlite3
import os
import random
import re
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "vessels.db")

VESSEL_PREFIXES = ["MV", "MT", "MS", "MSC", "APL", "COSCO", "MAERSK", "OCEAN", "SEA", "GOLDEN", "BLUE", "PACIFIC", "ATLANTIC", "NORTHERN", "SOUTHERN", "PIONEER", "STAR", "GULF", "GLOBAL", "ROYAL"]
VESSEL_NAMES = ["VOYAGER", "EXPLORER", "CHALLENGER", "CRUISER", "TRADER", "LEADER", "RANGER", "VICTOR", "HERO", "PRIDE", "SPIRIT", "GLORY", "FREEDOM", "HORIZON", "AURORA", "MARINER", "NAVIGATOR", "CENTURY", "CLASSIC", "TITAN", "NEPTUNE", "POSEIDON", "ATHENA", "ZEUS", "HERMES"]
VESSEL_TYPES = ["Dökme Yük (Bulk Carrier)", "Petrol Tankeri (Oil Tanker)", "Konteyner Gemisi (Container Ship)", "Kimyasal Tanker (Chemical Tanker)", "Yolcu Gemisi (Passenger Ship)", "Ro-Ro Gemisi", "Genel Kargo (General Cargo)", "Diğer"]
FLAGS = ["Panama", "Liberya", "Marshall Adaları", "Singapur", "Malta", "Bahamalar", "Yunanistan", "Çin", "Türkiye", "Kıbrıs"]
CLASS_SOCIETIES = ["DNV (Det Norske Veritas)", "ABS (American Bureau of Shipping)", "LR (Lloyd's Register)", "BV (Bureau Veritas)", "NK (ClassNK)", "RINA", "TL (Türk Loydu)"]
CERTIFICATE_NAMES = ["Sertifika - Can Kurtarma Araçları (LSA)", "Sertifika - Yangın Söndürme Donanımları (FFE)", "Sertifika - Petrol Kirliliği Önleme (IOPP)", "Sertifika - Hava Kirliliği Önleme (IAPP)", "Sertifika - Telsiz Telgraf Emniyeti (SRT)", "Sertifika - Gemi Emniyet İnşaat (SC)"]

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
                # Handles ISO dates like 2026-06-14 00:00:00
                return pd.to_datetime(d)
            except:
                return None

    def generate_imo_stable(name):
        val = 0
        for char in name.strip().upper():
            val = (val * 31 + ord(char)) & 0xFFFFFFFF
        return str(9000000 + (val % 1000000))

    # Read f2 first because it has IMOs
    if os.path.exists(f2):
        try:
            df2 = pd.read_excel(f2)
            df2 = normalize_excel_columns(df2)
            # Filter out headers
            df2 = df2[df2['Vessel'].astype(str).str.strip().str.lower() != 'company/vessel']
            
            for _, r in df2.iterrows():
                v_name = normalize_vessel_name(r['Vessel'])
                imo = str(r.get('IMO', '')).strip().split('.')[0]
                if not imo or imo == 'nan' or not imo.isdigit():
                    imo = generate_imo_stable(v_name)
                    
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
                    vessels_data[v_name] = {
                        "name": v_name,
                        "imo": imo,
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
            
    # Read f1 next
    if os.path.exists(f1):
        try:
            df1 = pd.read_excel(f1)
            df1 = normalize_excel_columns(df1)
            for _, r in df1.iterrows():
                v_name = normalize_vessel_name(r['Vessel'])
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
                    
                if v_name in vessels_data:
                    imo = vessels_data[v_name]["imo"]
                else:
                    imo = generate_imo_stable(v_name)
                    vessels_data[v_name] = {
                        "name": v_name,
                        "imo": imo,
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
    
    cursor.execute("SELECT COUNT(*) FROM vessels")
    count = cursor.fetchone()[0]
    
    # Check if a real vessel from Excel exists in the db
    cursor.execute("SELECT COUNT(*) FROM vessels WHERE imo = '9076466' OR name = 'CANOPUS S'")
    has_real = cursor.fetchone()[0] > 0
    
    if count < 2000 or not has_real:
        # Re-build cleanly
        cursor.execute("DELETE FROM certificates")
        cursor.execute("DELETE FROM vessels")
        conn.commit()
        
        print("Populating database with real vessels from Excel files...")
        real_vessels_dict = load_excel_vessels()
        
        used_imos = set()
        vessels_to_insert = []
        vessels_certs_map = {}
        
        # 1. Insert real vessels first
        for v_name, v_info in real_vessels_dict.items():
            imo = v_info["imo"]
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
                
            flag = random.choice(FLAGS)
            class_soc = random.choice(CLASS_SOCIETIES)
            vessel_type = random.choice(VESSEL_TYPES)
            
            if "Tanker" in vessel_type:
                grt = random.randint(20000, 160000)
                dwt = int(grt * random.uniform(1.6, 2.0))
            elif "Bulk" in vessel_type or "Dökme" in vessel_type:
                grt = random.randint(15000, 90000)
                dwt = int(grt * random.uniform(1.5, 1.8))
            elif "Konteyner" in vessel_type:
                grt = random.randint(10000, 220000)
                dwt = int(grt * random.uniform(0.9, 1.2))
            elif "Yolcu" in vessel_type:
                grt = random.randint(5000, 150000)
                dwt = int(grt * random.uniform(0.1, 0.25))
            else:
                grt = random.randint(2000, 30000)
                dwt = int(grt * random.uniform(1.2, 1.5))
                
            vessels_to_insert.append((v_name, imo, grt, dwt, vessel_type, flag, class_soc, status, score))
            vessels_certs_map[imo] = v_info["certs"]
            
        # 2. Add synthetic vessels up to 2050
        target = 2050
        while len(vessels_to_insert) < target:
            prefix = random.choice(VESSEL_PREFIXES)
            name = random.choice(VESSEL_NAMES)
            vessel_name = f"{prefix} {name}"
            if len(vessels_to_insert) > 300:
                vessel_name += f" {random.randint(1, 99)}"
                
            imo = f"{random.randint(9000000, 9999999)}"
            if imo in used_imos:
                continue
            used_imos.add(imo)
            vessel_type = random.choice(VESSEL_TYPES)
            flag = random.choice(FLAGS)
            class_soc = random.choice(CLASS_SOCIETIES)
            
            if "Tanker" in vessel_type:
                grt = random.randint(20000, 160000)
                dwt = int(grt * random.uniform(1.6, 2.0))
            elif "Bulk" in vessel_type or "Dökme" in vessel_type:
                grt = random.randint(15000, 90000)
                dwt = int(grt * random.uniform(1.5, 1.8))
            elif "Konteyner" in vessel_type:
                grt = random.randint(10000, 220000)
                dwt = int(grt * random.uniform(0.9, 1.2))
            elif "Yolcu" in vessel_type:
                grt = random.randint(5000, 150000)
                dwt = int(grt * random.uniform(0.1, 0.25))
            else:
                grt = random.randint(2000, 30000)
                dwt = int(grt * random.uniform(1.2, 1.5))
                
            status_prob = random.random()
            if status_prob < 0.70:
                status = "Active"
                score = random.randint(85, 100)
            elif status_prob < 0.92:
                status = "Warning"
                score = random.randint(65, 84)
            else:
                status = "Critical"
                score = random.randint(30, 64)
                
            vessels_to_insert.append((vessel_name, imo, grt, dwt, vessel_type, flag, class_soc, status, score))
            
        cursor.executemany("""
        INSERT INTO vessels (name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vessels_to_insert)
        conn.commit()
        
        # 3. Insert certificates linked to vessels
        cursor.execute("SELECT id, imo, status FROM vessels")
        all_inserted_vessels = cursor.fetchall()
        
        certs_to_insert = []
        today = datetime.now()
        
        for v_id, v_imo, v_status in all_inserted_vessels:
            if v_imo in vessels_certs_map:
                real_certs = vessels_certs_map[v_imo]
                for rc in real_certs:
                    certs_to_insert.append((v_id, rc["name"], rc["issue_date"], rc["expiry_date"], rc["status"]))
                
                existing_names = [c["name"].lower() for c in real_certs]
                other_certs = [name for name in CERTIFICATE_NAMES if name.lower() not in existing_names]
                if other_certs:
                    num_add = random.randint(1, min(3, len(other_certs)))
                    for cert_name in random.sample(other_certs, num_add):
                        days_to_expiry = random.randint(90, 1000)
                        expiry_dt = today + timedelta(days=days_to_expiry)
                        issue_dt = expiry_dt - timedelta(days=365*5)
                        certs_to_insert.append((v_id, cert_name, issue_dt.strftime("%Y-%m-%d"), expiry_dt.strftime("%Y-%m-%d"), "Valid"))
            else:
                num_certs = random.randint(4, 6)
                selected_certs = random.sample(CERTIFICATE_NAMES, num_certs)
                
                for cert_name in selected_certs:
                    if v_status == "Active":
                        days_to_expiry = random.randint(90, 1000)
                    elif v_status == "Warning":
                        days_to_expiry = random.randint(-5, 60)
                    else:
                        days_to_expiry = random.randint(-90, 5)
                        
                    expiry_dt = today + timedelta(days=days_to_expiry)
                    issue_dt = expiry_dt - timedelta(days=365*5)
                    
                    if days_to_expiry < 0:
                        c_status = "Expired"
                    elif days_to_expiry < 30:
                        c_status = "Expiring Soon"
                    else:
                        c_status = "Valid"
                        
                    certs_to_insert.append((v_id, cert_name, issue_dt.strftime("%Y-%m-%d"), expiry_dt.strftime("%Y-%m-%d"), c_status))
                    
        chunk_size = 1000
        for i in range(0, len(certs_to_insert), chunk_size):
            cursor.executemany("""
            INSERT INTO certificates (vessel_id, name, issue_date, expiry_date, status)
            VALUES (?, ?, ?, ?, ?)
            """, certs_to_insert[i:i+chunk_size])
        conn.commit()
        print("Vessel database populated!")
        
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
    
    sql += " ORDER BY compliance_score ASC, name ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(sql, params)
    vessels = cursor.fetchall()
    conn.close()
    return vessels, total_count

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
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS certificates")
                cursor.execute("DROP TABLE IF EXISTS vessels")
                conn.commit()
                conn.close()
            except Exception as ex:
                print(f"Error clearing tables: {ex}")
    
    # We force count < 2000 behavior in init_db by doing a clean populate
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS certificates")
    cursor.execute("DROP TABLE IF EXISTS vessels")
    conn.commit()
    conn.close()
    
    init_db()

# Initialize on import
init_db()
