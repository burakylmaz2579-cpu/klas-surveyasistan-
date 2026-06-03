import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "vessels.db")

VESSEL_PREFIXES = ["MV", "MT", "MS", "MSC", "APL", "COSCO", "MAERSK", "OCEAN", "SEA", "GOLDEN", "BLUE", "PACIFIC", "ATLANTIC", "NORTHERN", "SOUTHERN", "PIONEER", "STAR", "GULF", "GLOBAL", "ROYAL"]
VESSEL_NAMES = ["VOYAGER", "EXPLORER", "CHALLENGER", "CRUISER", "TRADER", "LEADER", "RANGER", "VICTOR", "HERO", "PRIDE", "SPIRIT", "GLORY", "FREEDOM", "HORIZON", "AURORA", "MARINER", "NAVIGATOR", "CENTURY", "CLASSIC", "TITAN", "NEPTUNE", "POSEIDON", "ATHENA", "ZEUS", "HERMES"]
VESSEL_TYPES = ["Dökme Yük (Bulk Carrier)", "Petrol Tankeri (Oil Tanker)", "Konteyner Gemisi (Container Ship)", "Kimyasal Tanker (Chemical Tanker)", "Yolcu Gemisi (Passenger Ship)", "Ro-Ro Gemisi", "Genel Kargo (General Cargo)", "Diğer"]
FLAGS = ["Panama", "Liberya", "Marshall Adaları", "Singapur", "Malta", "Bahamalar", "Yunanistan", "Çin", "Türkiye", "Kıbrıs"]
CLASS_SOCIETIES = ["DNV (Det Norske Veritas)", "ABS (American Bureau of Shipping)", "LR (Lloyd's Register)", "BV (Bureau Veritas)", "NK (ClassNK)", "RINA", "TL (Türk Loydu)"]
CERTIFICATE_NAMES = ["Sertifika - Can Kurtarma Araçları (LSA)", "Sertifika - Yangın Söndürme Donanımları (FFE)", "Sertifika - Petrol Kirliliği Önleme (IOPP)", "Sertifika - Hava Kirliliği Önleme (IAPP)", "Sertifika - Telsiz Telgraf Emniyeti (SRT)", "Sertifika - Gemi Emniyet İnşaat (SC)"]

def init_db():
    db_exists = os.path.exists(DB_PATH)
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
    
    if count < 2000:
        print(f"Generating database for 2000+ vessels. Count: {count}")
        vessels_to_insert = []
        used_imos = set()
        
        sample_vessel = ("MV OCEAN VOYAGER", "9876543", 38500, 64200, "Dökme Yük (Bulk Carrier)", "Panama", "DNV (Det Norske Veritas)", "Warning", 72)
        vessels_to_insert.append(sample_vessel)
        used_imos.add("9876543")
        
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
                compliance_score = random.randint(85, 100)
            elif status_prob < 0.92:
                status = "Warning"
                compliance_score = random.randint(65, 84)
            else:
                status = "Critical"
                compliance_score = random.randint(30, 64)
                
            vessels_to_insert.append((vessel_name, imo, grt, dwt, vessel_type, flag, class_soc, status, compliance_score))
            
        cursor.executemany("""
        INSERT OR IGNORE INTO vessels (name, imo, grt, dwt, vessel_type, flag, class_society, status, compliance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vessels_to_insert)
        conn.commit()
        
        cursor.execute("SELECT id, status FROM vessels")
        all_vessels = cursor.fetchall()
        
        certs_to_insert = []
        today = datetime.now()
        
        for vessel_id, v_status in all_vessels:
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
                expiry_str = expiry_dt.strftime("%Y-%m-%d")
                issue_str = issue_dt.strftime("%Y-%m-%d")
                
                if days_to_expiry < 0:
                    c_status = "Expired"
                elif days_to_expiry < 30:
                    c_status = "Expiring Soon"
                else:
                    c_status = "Valid"
                certs_to_insert.append((vessel_id, cert_name, issue_str, expiry_str, c_status))
                
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

init_db()
