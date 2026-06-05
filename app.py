import streamlit as st
import pandas as pd
import json
import time
import os
import tempfile
import re
from io import BytesIO
from datetime import datetime

import vessel_db as db
from doc_processor import SurveyDocumentProcessor, run_cross_document_checks
from rules_engine import REGULATIONS_DB, get_rule_by_keyword, check_rule_applicability
from create_sample_pdf import generate_sample_pdf

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Klas Sörveyörü Asistanı V3 | Refactored Engine",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MONTH NAMES IN TURKISH ---
MONTH_NAMES = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

# --- V3 PREMIUM TASARIM SİSTEMİ (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Reset & Typography */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Gradient Banner */
    .premium-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    .premium-header::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 60%);
        border-radius: 50%;
    }
    .header-title-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .header-main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(to right, #ffffff, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-badge {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 0.2rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .premium-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }

    /* Metric Panels */
    .metric-panel {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-panel:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.25rem;
    }
    
    /* Custom Cards */
    .vessel-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .status-pill {
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .status-active { background: #d1fae5; color: #065f46; }
    .status-warning { background: #fef3c7; color: #92400e; }
    .status-critical { background: #fee2e2; color: #991b1b; }

    /* Findings Cards */
    .finding-card {
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.2rem;
        border-left: 6px solid;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
        transition: transform 0.2s ease;
        background: #ffffff;
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    .finding-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
    }
    .card-critical { border-left-color: #ef4444; background: #fef2f2; }
    .card-error { border-left-color: #f43f5e; background: #fff1f2; }
    .card-warning { border-left-color: #f59e0b; background: #fffbeb; }
    .card-info { border-left-color: #3b82f6; background: #eff6ff; }
    .card-success { border-left-color: #10b981; background: #f0fdf4; }
    
    .finding-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .finding-rule {
        display: inline-block;
        padding: 0.2rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-critical { background: #fee2e2; color: #b91c1c; }
    .badge-warning { background: #fef3c7; color: #b45309; }
    .badge-info { background: #dbeafe; color: #1d4ed8; }
    .badge-success { background: #d1fae5; color: #047857; }
    
    .finding-desc {
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 0.8rem;
        white-space: pre-line;
    }
    .finding-rec {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 6px;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
        border-left: 4px solid #cbd5e1;
        color: #475569;
        margin-top: 0.5rem;
    }
    .rec-border-critical { border-left-color: #ef4444; }
    .rec-border-warning { border-left-color: #f59e0b; }
    .rec-border-success { border-left-color: #10b981; }

    /* Custom Reg Cards */
    .reg-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
    }
    .reg-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
    }
    .reg-chapter {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    
    /* Progress score circle */
    .score-circle {
        border-radius: 50%;
        width: 110px;
        height: 110px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        border: 4px solid;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- STATE MANAGEMENT ---
if 'active_view' not in st.session_state:
    st.session_state['active_view'] = "Fleet Dashboard"
if 'selected_vessel_id' not in st.session_state:
    st.session_state['selected_vessel_id'] = None
if 'analysis_data' not in st.session_state:
    st.session_state['analysis_data'] = None
if 'analysis_vessel_name' not in st.session_state:
    st.session_state['analysis_vessel_name'] = ""
if 'search_query' not in st.session_state:
    st.session_state['search_query'] = ""
if 'filter_type' not in st.session_state:
    st.session_state['filter_type'] = "All"
if 'filter_flag' not in st.session_state:
    st.session_state['filter_flag'] = "All"
if 'filter_status' not in st.session_state:
    st.session_state['filter_status'] = "All"
if 'fleet_page' not in st.session_state:
    st.session_state['fleet_page'] = 0

# --- COLUMN NORMALIZATION HELPER ---
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

# --- DATA LOADERS ---
def load_phrs_certificates():
    f1 = os.path.join(os.path.dirname(__file__), "PHRS_Acil_Sertifikalar.xlsx")
    f2 = os.path.join(os.path.dirname(__file__), "PHRS_CERT_DUE_DATE.xlsx")
    
    dfs = []
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

    if os.path.exists(f1):
        try:
            df1 = pd.read_excel(f1)
            df1 = normalize_excel_columns(df1)
            
            if 'Vessel' in df1.columns and 'Certificate' in df1.columns and 'DueDate' in df1.columns:
                df1['ParsedDate'] = df1['DueDate'].apply(parse_date)
                df1 = df1.dropna(subset=['ParsedDate'])
                if 'IMO' not in df1.columns:
                    df1['IMO'] = "N/A"
                if 'Status' not in df1.columns:
                    df1['Status'] = df1['ParsedDate'].apply(lambda d: "Süresi Doldu!" if d < today else "Süresi Yaklaşıyor")
                if 'Flag' in df1.columns:
                    df1 = df1[~df1['Flag'].astype(str).str.upper().isin(["COMOROS", "MALTA"])]
                dfs.append(df1[['Vessel', 'Certificate', 'DueDate', 'ParsedDate', 'Status', 'IMO']])
        except Exception as e:
            print("Error loading f1:", e)
            
    if os.path.exists(f2):
        try:
            df2 = pd.read_excel(f2)
            df2 = normalize_excel_columns(df2)
            df2 = df2[df2['Vessel'].astype(str).str.strip().str.lower() != 'company/vessel']
            
            if 'Vessel' in df2.columns and 'Certificate' in df2.columns and 'DueDate' in df2.columns:
                df2['ParsedDate'] = df2['DueDate'].apply(parse_date)
                df2 = df2.dropna(subset=['ParsedDate'])
                df2['DueDate'] = df2['ParsedDate'].dt.strftime("%d/%m/%Y")
                df2['Status'] = df2['ParsedDate'].apply(lambda d: "Süresi Doldu!" if d < today else "Süresi Yaklaşıyor")
                if 'IMO' not in df2.columns:
                    df2['IMO'] = "N/A"
                if 'Flag' in df2.columns:
                    df2 = df2[~df2['Flag'].astype(str).str.upper().isin(["COMOROS", "MALTA"])]
                dfs.append(df2[['Vessel', 'Certificate', 'DueDate', 'ParsedDate', 'Status', 'IMO']])
        except Exception as e:
            print("Error loading f2:", e)
            
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        df = df.drop_duplicates(subset=['Vessel', 'Certificate', 'DueDate'])
        df['DaysLeft'] = (df['ParsedDate'] - today).dt.days
        df = df.sort_values(by=['DaysLeft', 'Vessel'])
        return df
        
    return None

def get_cert_category_tr(cert_name):
    c = str(cert_name).upper().strip()
    if any(x in c for x in ["LSA", "LIFEBOAT", "LIFERAFT", "LIFEBUOY", "LIFEJACKET", "CAN KURTARMA", "PERSONAL LIFE"]):
        return "Can Kurtarma Araçları (LSA)"
    elif any(x in c for x in ["FFE", "FIRE", "EXTINGUISHER", "YANGIN", "SÖNDÜRME", "DONANIM"]):
        return "Yangın Güvenlik Donanımları (FFE)"
    elif any(x in c for x in ["IOPP", "OIL POLLUTION", "PETROL KİRLİLİĞİ", "OIL RECORD"]):
        return "Petrol Kirliliğini Önleme (MARPOL Annex I)"
    elif any(x in c for x in ["IAPPC", "IAPP", "AIR POLLUTION", "HAVA KİRLİLİĞİ", "EMISSION"]):
        return "Hava Kirliliğini Önleme (MARPOL Annex VI)"
    elif any(x in c for x in ["ISPP", "SEWAGE", "LAĞIM"]):
        return "Atık Su / Sewage (MARPOL Annex IV)"
    elif any(x in c for x in ["GARBAGE", "ÇÖP"]):
        return "Çöp Kirliliği (MARPOL Annex V)"
    elif any(x in c for x in ["SRT", "RADIO", "TELSİZ", "TELEGRAPHY", "TELEFON", "DSC"]):
        return "Telsiz Telgraf Emniyeti (SRT)"
    elif any(x in c for x in ["SC ", "SAFETY CONSTRUCTION", "EMNİYET İNŞAAT", "SAFCON"]):
        return "Gemi Emniyet İnşaat (SC)"
    elif any(x in c for x in ["CL ", "CLASS ", "KLAS", "CLASSIFICATION"]):
        return "Klas Sertifikası (CL)"
    elif any(x in c for x in ["LL ", "LOAD LINE", "YÜK SINIRI", "FREEBOARD"]):
        return "Yük Sınırı (LL)"
    elif any(x in c for x in ["BWM", "BALLAST WATER", "BALAST SUYU"]):
        return "Balast Suyu Yönetimi (BWM)"
    elif any(x in c for x in ["AFS", "ANTI-FOULING", "KARIŞIK BOYA", "ZEHİRLİ BOYA"]):
        return "Zehirli Boya Sistemleri (AFS)"
    elif any(x in c for x in ["SMC", "DOC", "SAFETY MANAGEMENT", "ISM"]):
        return "Emniyetli Yönetim (ISM/SMC)"
    elif any(x in c for x in ["ISSC", "SECURITY", "GÜVENLİK"]):
        return "Gemi Güvenlik (ISSC)"
    elif any(x in c for x in ["MLC", "LABOUR", "DENİZ İŞ"]):
        return "Denizcilik Çalışma (MLC)"
    else:
        return "Diğer Emniyet Sertifikaları"

def generate_local_evaluation(findings, vessel_name, vessel_type):
    total = len(findings)
    if total == 0:
        return "Yüklenen belgelerde kontrol edilecek bulgu bulunamadı."
        
    failures = sum(1 for f in findings if f["status"] == "Uygun Değil")
    warnings = sum(1 for f in findings if f["status"] == "Düzeltilmeli")
    compliant = sum(1 for f in findings if f["status"] == "Uygun")
    
    summary = f"🚢 **{vessel_name}** ({vessel_type}) için denetim ve çapraz kontrol tamamlandı. "
    summary += f"Toplam **{total}** madde kurallara ve yüklenen belgelere göre incelendi.\n\n"
    
    if failures > 0:
        summary += f"🔴 **Kritik Uyuşmazlıklar**: Çapraz dosya kontrolünde veya sörvey checklistinde **{failures}** adet kural ihlali / evrak uyuşmazlığı tespit edilmiştir. "
        summary += "Sertifika geçerlilik tarihleri, tonaj veya IMO eşleşmeleri ve kural çelişkileri bu alanda listelenmiştir. SOLAS/MARPOL kuralları gereği bu durumların ivedilikle giderilmesi zorunludur.\n"
    else:
        summary += "🟢 **Kritik Bulgular**: Herhangi bir kritik kural ihlali veya evrak uyuşmazlığı tespit edilmemiştir.\n"
        
    if warnings > 0:
        summary += f"🟡 **Eksik veya Yaklaşan İşaretlemeler**: Formlarda boş bırakılan veya süresi yaklaşan **{warnings}** madde tespit edilmiştir.\n"
        
    summary += f"\n📊 **Özet**: {compliant} Uygun | {failures} Uygunsuz | {warnings} Düzeltilmeli."
    return summary

def generate_excel(findings, vessel_info_dict):
    df = pd.DataFrame(findings)
    desired_cols = ["item_no", "title", "rule", "status", "severity", "description", "recommendation"]
    existing_cols = [c for c in desired_cols if c in df.columns]
    df = df[existing_cols]
    df.columns = [c.replace("item_no", "Madde Sıra").replace("title", "Madde Başlığı").replace("rule", "Kural Kodu").replace("status", "Bulgu Durumu").replace("severity", "Derece").replace("description", "Açıklama").replace("recommendation", "Düzeltici Eylem Önerisi") for c in df.columns]
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Survey Report')
    processed_data = output.getvalue()
    return processed_data

def generate_html_report(findings, vessel_name):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{vessel_name} Sörvey Denetim Raporu</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #1e293b; background-color: #f8fafc; line-height: 1.6; }}
            .report-card {{ background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); max-width: 900px; margin: 0 auto; border: 1px solid #e2e8f0; }}
            .header {{ border-bottom: 3px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
            .header-title {{ font-size: 28px; font-weight: 800; color: #0f172a; margin: 0; }}
            .header-meta {{ color: #64748b; font-size: 14px; margin-top: 5px; }}
            .finding-item {{ border: 1px solid #e2e8f0; border-left: 6px solid; padding: 20px; margin-bottom: 20px; border-radius: 8px; background: #fff; }}
            .status-pill {{ display: inline-block; padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }}
            .rule-badge {{ display: inline-block; background: #1e293b; color: white; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 10px; }}
            
            .st-uygun {{ border-left-color: #10b981; }}
            .st-uygun .status-pill {{ background: #d1fae5; color: #065f46; }}
            
            .st-uygunsuz {{ border-left-color: #ef4444; }}
            .st-uygunsuz .status-pill {{ background: #fee2e2; color: #991b1b; }}
            
            .st-duzeltilmeli {{ border-left-color: #f59e0b; }}
            .st-duzeltilmeli .status-pill {{ background: #fef3c7; color: #92400e; }}
            
            .item-title {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 0; margin-bottom: 8px; }}
            .item-desc {{ font-size: 14px; color: #334155; margin-bottom: 10px; white-space: pre-line; }}
            .item-rec {{ background: #f1f5f9; border-left: 3px solid #64748b; padding: 10px 15px; font-size: 13px; color: #475569; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="report-card">
            <div class="header">
                <h1 class="header-title">🚢 {vessel_name} - Sörvey Çapraz Kontrol Raporu</h1>
                <div class="header-meta">SOLAS / MARPOL / BWM / AFS Mevzuat Uyumluluk Denetimi &copy; {time.strftime('%Y')}</div>
            </div>
    """
    for f in findings:
        st_class = "st-uygun" if f.get('status') == "Uygun" else "st-uygunsuz" if f.get('status') == "Uygun Değil" else "st-duzeltilmeli"
        html_content += f"""
        <div class="finding-item {st_class}">
            <div>
                <span class="status-pill">{f.get('status', 'Bilinmiyor')}</span>
                <span class="rule-badge">{f.get('rule', 'N/A')}</span>
            </div>
            <div class="item-title">{f.get('item_no', '-')}. {f.get('title', '')}</div>
            <div class="item-desc"><b>Açıklama:</b><br/>{f.get('description', '').replace('\n', '<br/>')}</div>
            {f'<div class="item-rec"><b>🔧 Düzeltici Eylem Önerisi:</b> {f.get("recommendation")}</div>' if f.get("recommendation") else ''}
        </div>
        """
    html_content += "</div></body></html>"
    return html_content.encode('utf-8')

# --- SIDEBAR NAVİGASYONU ---
with st.sidebar:
    st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-anchor-maritime-flatart-icons-flat-flatarticons.png", width=70)
    st.title("Sörvey Portal V3")
    st.write("---")
    
    st.markdown("### 🧭 Menü Navigasyonu")
    if st.button("📊 Filo Dashboard", use_container_width=True, type="primary" if st.session_state.active_view == "Fleet Dashboard" else "secondary"):
        st.session_state.active_view = "Fleet Dashboard"
        st.rerun()
        
    if st.button("🚢 Gemi Bilgi & Sertifikalar", use_container_width=True, type="primary" if st.session_state.active_view == "Vessel Profile" else "secondary"):
        if st.session_state.selected_vessel_id is None:
            first_vessels, _ = db.search_vessels(limit=1)
            if first_vessels:
                st.session_state.selected_vessel_id = first_vessels[0][0]
            else:
                st.session_state.selected_vessel_id = 1
        st.session_state.active_view = "Vessel Profile"
        st.rerun()
        
    if st.button("📅 PHRS Sertifika Takip (Yeni)", use_container_width=True, type="primary" if st.session_state.active_view == "PHRS Certs" else "secondary"):
        st.session_state.active_view = "PHRS Certs"
        st.rerun()
        
    if st.button("🔍 Sörvey Denetim Konsolu", use_container_width=True, type="primary" if st.session_state.active_view == "Audit Console" else "secondary"):
        st.session_state.active_view = "Audit Console"
        st.rerun()
        
    if st.button("📚 SOLAS / MARPOL Kütüphanesi", use_container_width=True, type="primary" if st.session_state.active_view == "Reg Library" else "secondary"):
        st.session_state.active_view = "Reg Library"
        st.rerun()
        
    st.write("---")
    
    # Dynamic vessel counts to show actual db status excluding Malta/Comoros
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM vessels")
    actual_db_vessels = c.fetchone()[0]
    conn.close()
    
    st.caption(f"Veritabanı: **{actual_db_vessels} Aktif Gemi**")
    st.caption("Motor: **Advanced Audit Engine**")

# --- HEADER RENDERING ---
st.markdown(f"""
<div class="premium-header">
    <div class="header-title-container">
        <h1 class="header-main-title">🚢 Klas Sörveyörü Asistanı</h1>
        <span class="header-badge">YeniDeneyi V2 Refactored</span>
    </div>
    <div class="premium-subtitle">SOLAS, MARPOL, BWM, AFS ve ICLL Uyum & Çapraz Kontrol Portalı</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# VIEW 1: FLEET SUMMARY & DASHBOARD
# ==========================================
if st.session_state.active_view == "Fleet Dashboard":
    metrics = db.get_fleet_summary_metrics()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-panel">
            <div class="metric-label">Takip Edilen Gemi</div>
            <div class="metric-value">🚢 {metrics['total_vessels']} Adet</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-panel">
            <div class="metric-label">Filo Emniyet Uyumluluğu</div>
            <div class="metric-value" style="color: #10b981;">📈 % {metrics['avg_compliance_score']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-panel">
            <div class="metric-label">Süresi Geçmiş Sertifikalar</div>
            <div class="metric-value" style="color: #ef4444;">🚨 {metrics['expired_certificates']} Adet</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-panel">
            <div class="metric-label">Yaklaşan Yenilemeler (<30 Gün)</div>
            <div class="metric-value" style="color: #f59e0b;">⏳ {metrics['expiring_certificates']} Adet</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("---")
    
    st.subheader("🔍 Filoda Gemi Arama & Filtreleme")
    col_s1, col_s2, col_s3, col_s4 = st.columns([1.5, 1, 1, 1])
    
    with col_s1:
        search_q = st.text_input("Gemi Adı veya IMO Numarası", value=st.session_state.search_query, placeholder="Arama kelimesini girip Enter'a basın...")
        if search_q != st.session_state.search_query:
            st.session_state.search_query = search_q
            st.session_state.fleet_page = 0
            st.rerun()
            
    unique_types = db.get_unique_vessel_types()
    unique_flags = db.get_unique_flags()
    
    if st.session_state.filter_type not in ["All"] + unique_types:
        st.session_state.filter_type = "All"
    if st.session_state.filter_flag not in ["All"] + unique_flags:
        st.session_state.filter_flag = "All"

    with col_s2:
        type_options = ["All"] + unique_types
        type_filter = st.selectbox("Gemi Türü Filtresi", type_options, index=type_options.index(st.session_state.filter_type))
        if type_filter != st.session_state.filter_type:
            st.session_state.filter_type = type_filter
            st.session_state.fleet_page = 0
            st.rerun()
            
    with col_s3:
        flag_options = ["All"] + unique_flags
        flag_filter = st.selectbox("Bayrak Devleti Filtresi", flag_options, index=flag_options.index(st.session_state.filter_flag))
        if flag_filter != st.session_state.filter_flag:
            st.session_state.filter_flag = flag_filter
            st.session_state.fleet_page = 0
            st.rerun()
            
    with col_s4:
        status_filter = st.selectbox("Durum Filtresi", ["All", "Active", "Warning", "Critical"], index=["All", "Active", "Warning", "Critical"].index(st.session_state.filter_status))
        if status_filter != st.session_state.filter_status:
            st.session_state.filter_status = status_filter
            st.session_state.fleet_page = 0
            st.rerun()
        
    limit = 12
    offset = st.session_state.fleet_page * limit
    
    vessels, total_count = db.search_vessels(
        query=st.session_state.search_query,
        filter_type=st.session_state.filter_type,
        filter_flag=st.session_state.filter_flag,
        filter_status=st.session_state.filter_status,
        limit=limit,
        offset=offset
    )
    
    st.markdown(f"**Arama Sonuçları ({total_count} gemi bulundu)**")
    
    if total_count == 0:
        st.warning("Aranan kriterlere uygun gemi bulunamadı. Lütfen arama metnini veya filtreleri değiştirin.")
    else:
        cols = st.columns(3)
        for idx, v in enumerate(vessels):
            v_id, name, imo, grt, dwt, v_type, flag, class_soc, status, comp_score = v
            status_class = "status-active" if status == "Active" else "status-warning" if status == "Warning" else "status-critical"
            status_tr = "Sorunsuz" if status == "Active" else "Uyarı" if status == "Warning" else "Kritik"
            score_color = "#ef4444" if comp_score < 60 else ("#f59e0b" if comp_score < 85 else "#10b981")
            
            col_cell = cols[idx % 3]
            with col_cell:
                st.markdown(f"""
                <div class="vessel-card">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #0f172a;">{name}</div>
                        <span class="status-pill {status_class}">{status_tr}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 1rem;">
                        <b>IMO:</b> {imo} &bull; <b>Flag:</b> {flag}<br/>
                        <b>Type:</b> {v_type}<br/>
                        <b>Tonnage:</b> {grt:,} GRT / {dwt:,} DWT<br/>
                        <b>Classification:</b> {class_soc}
                    </div>
                    <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #f1f5f9; padding-top: 0.75rem;">
                        <div>
                            <span style="font-size: 0.8rem; font-weight: 600; color: #94a3b8;">UYUMLULUK</span>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {score_color};">% {comp_score}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚢 Detayları Gör: {name}", key=f"v_btn_{v_id}", use_container_width=True):
                    st.session_state.selected_vessel_id = v_id
                    st.session_state.active_view = "Vessel Profile"
                    st.rerun()

        st.write("---")
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p1:
            if st.session_state.fleet_page > 0:
                if st.button("⬅️ Önceki Sayfa", use_container_width=True):
                    st.session_state.fleet_page -= 1
                    st.rerun()
        with col_p2:
            max_pages = max(1, (total_count + limit - 1) // limit)
            st.markdown(f"<div style='text-align: center; color: #64748b; padding-top: 8px;'>Sayfa {st.session_state.fleet_page + 1} / {max_pages}</div>", unsafe_allow_html=True)
        with col_p3:
            if (st.session_state.fleet_page + 1) * limit < total_count:
                if st.button("Sonraki Sayfa ➡️", use_container_width=True):
                    st.session_state.fleet_page += 1
                    st.rerun()


# ==========================================
# VIEW 2: VESSEL PROFILE & CERTIFICATES
# ==========================================
elif st.session_state.active_view == "Vessel Profile":
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, imo FROM vessels ORDER BY name ASC")
    all_vessels_list = cursor.fetchall()
    conn.close()
    
    vessel_options = {f"{row[1]} (IMO: {row[2]})": row[0] for row in all_vessels_list}
    
    v_id = st.session_state.selected_vessel_id
    if v_id is None:
        v_id = all_vessels_list[0][0] if all_vessels_list else 1
        
    selected_key = next((k for k, v in vessel_options.items() if v == v_id), list(vessel_options.keys())[0] if vessel_options else None)
    
    if selected_key:
        selected_vessel_name = st.selectbox("🚢 İncelemek İstediğiniz Gemiyi Seçin:", list(vessel_options.keys()), index=list(vessel_options.keys()).index(selected_key))
        new_v_id = vessel_options[selected_vessel_name]
        
        if new_v_id != v_id:
            st.session_state.selected_vessel_id = new_v_id
            st.rerun()
            
        vessel = db.get_vessel_by_id(new_v_id)
        
        if not vessel:
            st.warning("Lütfen listeden bir gemi seçin.")
        else:
            v_id, name, imo, grt, dwt, v_type, flag, class_soc, status, comp_score = vessel
            st.subheader(f"🚢 {name} - Detaylı Gemi Kartı")
            
            col_c1, col_c2 = st.columns([1.5, 1])
            
            with col_c1:
                st.markdown("### 📋 Gemi Kimlik Bilgileri")
                v_data = {
                    "Detay / Particulars": ["Gemi Adı", "IMO Numarası", "Bayrak Devleti", "Klas Kuruluşu", "Gemi Türü", "Brüt Tonaj (GRT)", "Detveyt Tonaj (DWT)"],
                    "Değer / Value": [name, imo, flag, class_soc, v_type, f"{grt:,} RT", f"{dwt:,} MT"]
                }
                st.table(pd.DataFrame(v_data))
                
                if st.button("🚀 Bu Gemi İçin Yeni Sörvey Raporu Denetle", type="primary", use_container_width=True):
                    st.session_state.active_view = "Audit Console"
                    st.rerun()
                    
            with col_c2:
                st.markdown("### 🌡️ Risk & Uyumluluk Analizi")
                score_color = "#ef4444" if comp_score < 60 else ("#f59e0b" if comp_score < 85 else "#10b981")
                status_text = "SORUNSUZ" if status == "Active" else "UYARI/EKSİKLİK" if status == "Warning" else "KRİTİK UYGUNSUZLUK"
                
                st.markdown(f"""
                <div class="vessel-card" style="text-align: center;">
                    <div style="font-weight: 600; color: #64748b; margin-bottom: 1rem; font-size: 0.9rem;">MEVCUT UYUMLULUK PUANI</div>
                    <div class="score-circle" style="border-color: {score_color}; color: {score_color}; background: {score_color}0a;">
                        <div style="font-size: 2.2rem; font-weight: 800;">{comp_score}%</div>
                    </div>
                    <div style="margin-top: 1.5rem; font-weight: 700; font-size: 1.1rem; color: {score_color};">
                        DURUM: {status_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("---")
            
            st.markdown("### 📄 Aktif Emniyet ve Çevre Sertifikaları Durumu")
            certs = db.get_vessel_certificates(v_id)
            
            if not certs:
                st.info("Bu gemiye ait kayıtlı sertifika bulunmamaktadır.")
            else:
                cert_rows = []
                for cert_name, issue_date, expiry_date, c_status in certs:
                    badge_style = "status-active" if c_status == "Valid" else "status-warning" if c_status == "Expiring Soon" else "status-critical"
                    c_status_tr = "Geçerli" if c_status == "Valid" else "Yaklaşıyor (<30 Gün)" if c_status == "Expiring Soon" else "Süresi Dolmuş"
                    
                    cert_rows.append(f"<tr><td style='padding: 10px; font-weight: 600; color: #0f172a;'>{cert_name}</td><td style='padding: 10px;'>{issue_date}</td><td style='padding: 10px; font-weight: 600;'>{expiry_date}</td><td style='padding: 10px;'><span class='status-pill {badge_style}'>{c_status_tr}</span></td></tr>")
                    
                st.markdown(f"""<table style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; background: white; border-radius: 8px; overflow: hidden;">
    <thead>
    <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
    <th style="padding: 12px 10px;">Sertifika Adı</th>
    <th style="padding: 12px 10px;">Düzenlenme Tarihi</th>
    <th style="padding: 12px 10px;">Son Geçerlilik Tarihi</th>
    <th style="padding: 12px 10px;">Geçerlilik Durumu</th>
    </tr>
    </thead>
    <tbody>
    {"".join(cert_rows)}
    </tbody>
    </table>""", unsafe_allow_html=True)


# ==========================================
# VIEW 3: PHRS CERTIFICATE TRACKING
# ==========================================
elif st.session_state.active_view == "PHRS Certs":
    st.subheader("📅 PHRS Sertifika Son Kullanma Tarihi Takip Ekranı")
    st.markdown("PHRS B2B sisteminden çekilen (scraped) güncel sertifika bitiş tarihlerine göre planlama ve uyarı ekranı.")
    
    # B2B Integration Panel
    with st.expander("🔄 B2B Entegrasyonu ve Veri Güncelleme Konsolu", expanded=False):
        st.markdown("""
        Bu konsol aracılığıyla PHRS B2B sistemindeki güncel gemi ve sertifika bilgilerini doğrudan çekebilirsiniz.
        """)
        
        is_windows = (os.name == 'nt')
        bot_script_certs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sertifika.py")
        bot_script_fleet = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrape_vessels.py")
        
        if not is_windows:
            st.warning("⚠️ **Bulut Sunucu Uyarısı**: PHRS B2B Selenium Tarayıcıları (Chrome/ChromeDriver gerektirdiğinden) **Streamlit Cloud üzerinde çalıştırılamaz.**")
        else:
            col_b1, col_b2 = st.columns(2)
            run_script = None
            script_name = ""
            
            with col_b1:
                if st.button("🚀 B2B Sertifika Tarihlerini Güncelle", use_container_width=True, key="btn_certs_run"):
                    run_script = bot_script_certs
                    script_name = "Sertifika Tarayıcısı (sertifika.py)"
            with col_b2:
                if st.button("🚀 B2B Filo Listesini Güncelle (Gemileri Çek)", use_container_width=True, key="btn_fleet_run"):
                    run_script = bot_script_fleet
                    script_name = "Filo Listesi Tarayıcısı (scrape_vessels.py)"
            
            if run_script is not None:
                import subprocess
                import sys
                
                log_placeholder = st.empty()
                status_placeholder = st.empty()
                status_placeholder.info(f"⏳ {script_name} başlatılıyor... Lütfen bekleyin. Tarayıcı penceresi açılacaktır.")
                
                try:
                    process = subprocess.Popen(
                        [sys.executable, "-u", run_script],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    log_content = []
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        log_content.append(line)
                        log_placeholder.code("".join(log_content[-15:]))
                        
                    process.wait()
                    
                    if process.returncode == 0:
                        status_placeholder.success(f"✅ {script_name} başarıyla tamamlandı! Veritabanı güncelleniyor...")
                        db.refresh_db()
                        st.success("🎉 Veritabanı başarıyla senkronize edildi! Sayfayı yenileyiniz.")
                        if st.button("Sayfayı Şimdi Yenile", key="btn_refresh_page"):
                            st.rerun()
                    else:
                        status_placeholder.error(f"❌ Tarayıcı hata ile sonlandı (Hata kodu: {process.returncode}).")
                except Exception as ex:
                    status_placeholder.error(f"Hata oluştu: {ex}")
                
    st.write("---")
    
    cert_df = load_phrs_certificates()
    
    if cert_df is None or cert_df.empty:
        st.warning("⚠️ Sistemde yüklü taranmış sertifika dosyası bulunamadı. Lütfen `PHRS_Acil_Sertifikalar.xlsx` dosyasını kontrol edin.")
    else:
        total_alerts = len(cert_df)
        expired_count = sum(1 for d in cert_df['DaysLeft'] if d < 0)
        expiring_30_count = sum(1 for d in cert_df['DaysLeft'] if 0 <= d <= 30)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-panel">
                <div class="metric-label">Toplam Takip Edilen Uyarı</div>
                <div class="metric-value">📅 {total_alerts} Adet</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-panel">
                <div class="metric-label">Tarihi GEÇENLER (Süresi Dolan)</div>
                <div class="metric-value" style="color: #ef4444;">🚨 {expired_count} Gemi/Sertifika</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-panel">
                <div class="metric-label">Süresi Yaklaşanlar (<30 Gün)</div>
                <div class="metric-value" style="color: #f59e0b;">⚠️ {expiring_30_count} Adet</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("---")
        
        # 1. Expired ones inside expander
        expired_df = cert_df[cert_df['DaysLeft'] < 0]
        if not expired_df.empty:
            with st.expander("🚨 SÜRESİ GEÇMİŞ SERTİFİKALAR (Acil Aksiyon Gerekenler)", expanded=True):
                expired_df = expired_df.copy()
                expired_df['Category'] = expired_df['Certificate'].apply(get_cert_category_tr)
                grouped_expired = expired_df.groupby('Category')
                
                for cat_name, cat_group in sorted(grouped_expired.groups.items()):
                    st.markdown(f"#### 🏷️ {cat_name}")
                    rows_html = []
                    for _, r in expired_df.loc[cat_group].iterrows():
                        rows_html.append(f"<tr><td style='padding: 10px; font-weight: 700; color: #991b1b;'>{r['Vessel']}</td><td style='padding: 10px;'>{r.get('IMO', 'N/A')}</td><td style='padding: 10px; font-weight: 600;'>{r['Certificate']}</td><td style='padding: 10px; color: #ef4444; font-weight: 700;'>{r['DueDate']}</td><td style='padding: 10px;'><span class='status-pill status-critical'>{abs(r['DaysLeft'])} Gün Önce Geçti</span></td></tr>")
                    
                    st.markdown(f"""<table style="width: 100%; border-collapse: collapse; border: 1px solid #fee2e2; background: #fff5f5; border-radius: 8px; overflow: hidden; margin-bottom: 1.5rem;">
<thead>
<tr style="background: #fee2e2; text-align: left; color: #991b1b;">
<th style="padding: 12px 10px; width: 25%;">Gemi Adı</th>
<th style="padding: 12px 10px; width: 15%;">IMO No</th>
<th style="padding: 12px 10px; width: 30%;">Sertifika</th>
<th style="padding: 12px 10px; width: 15%;">Bitiş Tarihi</th>
<th style="padding: 12px 10px; width: 15%;">Kalan Süre</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>""", unsafe_allow_html=True)

        # 2. Upcoming grouped month by month and category
        future_df = cert_df[cert_df['DaysLeft'] >= 0]
        if not future_df.empty:
            future_df = future_df.copy()
            future_df['Month'] = future_df['ParsedDate'].dt.month
            future_df['Year'] = future_df['ParsedDate'].dt.year
            future_df['Category'] = future_df['Certificate'].apply(get_cert_category_tr)
            
            grouped_keys = sorted(future_df.groupby(['Year', 'Month']).groups.keys())
            
            st.markdown("### 📅 Gelecek Aylara Göre Sertifika Yenileme Takvimi")
            
            tab_labels = []
            for year, month in grouped_keys:
                month_name = MONTH_NAMES.get(month, f"Ay: {month}")
                tab_labels.append(f"📅 {month_name} {year}")
                
            month_tabs = st.tabs(tab_labels)
            
            for idx, (year, month) in enumerate(grouped_keys):
                with month_tabs[idx]:
                    month_df = future_df[(future_df['Year'] == year) & (future_df['Month'] == month)]
                    grouped_cat = month_df.groupby('Category')
                    
                    for cat_name, cat_group in sorted(grouped_cat.groups.items()):
                        st.markdown(f"#### 🏷️ {cat_name}")
                        rows_html = []
                        for _, r in month_df.loc[cat_group].iterrows():
                            days = r['DaysLeft']
                            pill_style = "status-warning" if days <= 30 else "status-active"
                            pill_text = f"{days} Gün Kaldı" if days > 0 else "Bugün Son Gün!"
                            
                            rows_html.append(f"<tr><td style='padding: 10px; font-weight: 600; color: #1e293b;'>{r['Vessel']}</td><td style='padding: 10px;'>{r.get('IMO', 'N/A')}</td><td style='padding: 10px;'>{r['Certificate']}</td><td style='padding: 10px; font-weight: 600;'>{r['DueDate']}</td><td style='padding: 10px;'><span class='status-pill {pill_style}'>{pill_text}</span></td></tr>")
                            
                        st.markdown(f"""<table style="width: 100%; border-collapse: collapse; border: 1px solid #e2e8f0; background: white; border-radius: 8px; overflow: hidden; margin-bottom: 1.5rem;">
<thead>
<tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left;">
<th style="padding: 12px 10px; width: 25%;">Gemi Adı</th>
<th style="padding: 12px 10px; width: 15%;">IMO No</th>
<th style="padding: 12px 10px; width: 30%;">Sertifika</th>
<th style="padding: 12px 10px; width: 15%;">Bitiş Tarihi</th>
<th style="padding: 12px 10px; width: 15%;">Kalan Süre</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>""", unsafe_allow_html=True)


# ==========================================
# VIEW 4: SURVEY AUDIT CONSOLE
# ==========================================
elif st.session_state.active_view == "Audit Console":
    st.subheader("🔍 Sörvey Denetim ve Çapraz Kontrol Konsolu")
    st.markdown("Yüklediğiniz sörvey formları ve sertifika PDF'lerini analiz ederek kural uyumluluğunu denetler.")
    
    # -------------------------------------------------------------
    # AUTO-EXTRACT VESSEL INFO FROM UPLOADED PDF ON THE FLY
    # -------------------------------------------------------------
    uploaded_files_state = st.session_state.get("audit_file_uploader")
    if uploaded_files_state:
        uploaded_keys = ",".join(sorted([f.name for f in uploaded_files_state]))
        if st.session_state.get('last_uploaded_keys') != uploaded_keys:
            st.session_state.last_uploaded_keys = uploaded_keys
            try:
                # Process the first uploaded file to auto-detect particulars
                f = uploaded_files_state[0]
                pdf_bytes = f.getvalue()
                
                # Use SurveyDocumentProcessor to parse details
                proc = SurveyDocumentProcessor(pdf_bytes)
                
                extracted_imo = None
                extracted_name = None
                extracted_type = "Seçiniz"
                extracted_grt_dwt = ""
                
                if proc.doc_type == "certificate" and proc.certificate_info:
                    extracted_imo = proc.certificate_info.get("imo")
                    extracted_name = proc.certificate_info.get("vessel_name")
                    grt = proc.certificate_info.get("grt", "")
                    dwt = proc.certificate_info.get("dwt", "")
                    if grt or dwt:
                        extracted_grt_dwt = f"{grt} / {dwt}"
                else:
                    extracted_imo = proc.vessel_info.get("imo")
                    extracted_name = proc.vessel_info.get("name")
                    extracted_grt_dwt = proc.vessel_info.get("grt_dwt", "")
                    extracted_type = proc.vessel_info.get("vessel_type", "Seçiniz")
                
                if extracted_imo:
                    extracted_imo = str(extracted_imo).strip()
                if extracted_name:
                    extracted_name = str(extracted_name).strip().upper()
                
                found_in_db = False
                if extracted_imo:
                    v_db = db.get_vessel_by_imo(extracted_imo)
                    if v_db:
                        st.session_state.selected_vessel_id = v_db[0]
                        found_in_db = True
                        st.toast(f"🚢 IMO '{extracted_imo}' tespit edildi ve filo eşleştirmesi yapıldı: {v_db[1]}", icon="✅")
                        st.rerun()
                        
                if not found_in_db and extracted_name:
                    conn = db.get_db_connection()
                    c = conn.cursor()
                    c.execute("SELECT id, name FROM vessels")
                    all_v = c.fetchall()
                    conn.close()
                    for v_id, v_name in all_v:
                        if extracted_name == v_name.upper():
                            st.session_state.selected_vessel_id = v_id
                            found_in_db = True
                            st.toast(f"🚢 Gemi adı '{extracted_name}' tespit edildi ve filo eşleştirmesi yapıldı.", icon="✅")
                            st.rerun()
                            break
                            
                if not found_in_db:
                    st.session_state.uploaded_vessel_info = {
                        "name": extracted_name or "",
                        "imo": extracted_imo or "",
                        "grt_dwt": extracted_grt_dwt or "",
                        "vessel_type": extracted_type or "Seçiniz"
                    }
                    st.toast("📝 Yeni gemi bilgileri belgeden okunarak form alanlarına yerleştirildi.", icon="ℹ️")
                    st.rerun()
            except Exception as ex:
                print("Error extracting uploaded vessel info:", ex)

    col_a1, col_a2 = st.columns([1.2, 1])
    
    with col_a1:
        st.markdown("### 📋 Gemi ve Denetim Bağlantısı")
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, imo, vessel_type FROM vessels ORDER BY name ASC")
        db_vessels = cursor.fetchall()
        conn.close()
        
        v_options = ["Manuel Bilgi Girişi / Yeni Gemi"] + [f"{row[1]} (IMO: {row[2]})" for row in db_vessels]
        
        # Auto-populate target vessel if selected_vessel_id is in session state
        default_index = 0
        if st.session_state.selected_vessel_id is not None:
            for i, row in enumerate(db_vessels):
                if row[0] == st.session_state.selected_vessel_id:
                    default_index = i + 1
                    break
                    
        selected_v_option = st.selectbox("Filodan Hedef Gemi Bağla", v_options, index=default_index)
        
        v_name_val = ""
        v_imo_val = ""
        v_type_val = "Seçiniz"
        v_grt_dwt_val = ""
        
        if selected_v_option != "Manuel Bilgi Girişi / Yeni Gemi":
            match_name = selected_v_option.split(" (IMO:")[0]
            conn = db.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, imo, vessel_type, grt, dwt FROM vessels WHERE name = ?", (match_name,))
            v_row = cursor.fetchone()
            conn.close()
            
            if v_row:
                v_name_val = v_row[0]
                v_imo_val = v_row[1]
                v_type_val = v_row[2]
                v_grt_dwt_val = f"{v_row[3]:,} / {v_row[4]:,}"
        elif st.session_state.get("uploaded_vessel_info") is not None:
            # Auto-populate from uploaded PDF if manual entry is active
            info = st.session_state.uploaded_vessel_info
            v_name_val = info.get("name", "")
            v_imo_val = info.get("imo", "")
            v_type_val = info.get("vessel_type", "Seçiniz")
            v_grt_dwt_val = info.get("grt_dwt", "")
        
        vessel_name = st.text_input("Gemi Adı (Reference)", value=v_name_val)
        
        col_sub_x, col_sub_y = st.columns(2)
        with col_sub_x:
            imo_number = st.text_input("IMO Numarası", value=v_imo_val)
        with col_sub_y:
            grt_dwt = st.text_input("GRT / DWT", value=v_grt_dwt_val)
            
        vessel_type = st.selectbox("Gemi Sınıfı / Türü", ["Seçiniz"] + db.VESSEL_TYPES, index=(["Seçiniz"] + db.VESSEL_TYPES).index(v_type_val) if v_type_val in (["Seçiniz"] + db.VESSEL_TYPES) else 0)
        surveyor_notes = st.text_area("✍️ Sörveyör Özel Notları / Odak Noktaları", placeholder="Örn: 1.1.2 maddesindeki limit anahtarlarına dikkat edilsin, eksiği olabilir.")

    with col_a2:
        st.markdown("### 📁 Belgeleri Yükle & Test Et")
        st.info("IACS sörvey raporu PDF'leri ile birlikte gemi klas/pollution sertifikalarını yükleyebilirsiniz. Sistem bunları otomatik ayırt edip çapraz kontrol edecektir.")
        
        uploaded_files = st.file_uploader(
            "Çoklu PDF Dosyaları Yükleme (Rapor + Sertifika)",
            type=["pdf"],
            accept_multiple_files=True,
            key="audit_file_uploader"
        )
        
        st.write("---")
        st.markdown("#### 🛠️ Hızlı Test Alanı")
        st.markdown("Denemek için örnek bir IACS sörvey raporu PDF'i indirebilir veya doğrudan test verisi olarak kullanabilirsiniz.")
        
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            sample_path = "sample_survey_report.pdf"
            if not os.path.exists(sample_path):
                generate_sample_pdf(sample_path)
            
            with open(sample_path, "rb") as f:
                pdf_bytes = f.read()
                
            st.download_button(
                label="📥 Örnek Rapor PDF'ini İndir",
                data=pdf_bytes,
                file_name="sample_survey_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col_test2:
            if st.button("🚢 Örnek PDF Verilerini Yükle", type="secondary", use_container_width=True):
                st.session_state.selected_vessel_id = 1
                st.session_state.analysis_vessel_name = "MV OCEAN VOYAGER"
                st.toast("Örnek gemi ve sörvey verileri forma yüklendi. 'Belgeleri Oku ve Denetimi Başlat' butonuna basın!", icon="🚢")
                st.rerun()

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🔄 Ekranı Temizle", use_container_width=True):
            st.session_state.analysis_data = None
            st.session_state.analysis_vessel_name = ""
            st.session_state.selected_vessel_id = None
            st.session_state.uploaded_vessel_info = None
            st.session_state.last_uploaded_keys = None
            if "audit_file_uploader" in st.session_state:
                del st.session_state["audit_file_uploader"]
            st.rerun()
    with col_b2:
        analyze_btn = st.button("🚀 Belgeleri Oku ve Denetimi Başlat", type="primary", use_container_width=True)

    if analyze_btn:
        target_bytes_list = []
        if uploaded_files:
            for f in uploaded_files:
                target_bytes_list.append((f.name, f.getvalue()))
        elif vessel_name == "MV OCEAN VOYAGER" or selected_v_option.startswith("MV OCEAN VOYAGER"):
            sample_path = "sample_survey_report.pdf"
            if not os.path.exists(sample_path):
                generate_sample_pdf(sample_path)
            with open(sample_path, "rb") as f:
                target_bytes_list.append(("sample_survey_report.pdf", f.read()))
                
        if not target_bytes_list:
            st.error("Lütfen denetlemek için en az bir PDF belgesi yükleyin.")
        elif vessel_type == "Seçiniz":
            st.error("Lütfen gemi sınıfı / türünü seçin.")
        else:
            try:
                findings_all = []
                checklists_processed = []
                certificates_extracted = []
                
                with st.spinner("📥 PDF belgeleri sınıflandırılıyor ve okunuyor..."):
                    for filename, pdf_bytes in target_bytes_list:
                        processor = SurveyDocumentProcessor(pdf_bytes)
                        if processor.doc_type == "certificate":
                            certificates_extracted.append(processor.certificate_info)
                        else:
                            checklists_processed.append(processor)
                            
                # Process checklist items
                for proc in checklists_processed:
                    doc_findings = proc.process_findings(vessel_type, grt_dwt)
                    findings_all.extend(doc_findings)
                    
                # Run cross-document validation checks if certificates were uploaded
                cross_checks = run_cross_document_checks(
                    vessel_name=vessel_name,
                    imo_number=imo_number,
                    grt_dwt=grt_dwt,
                    certificates_info=certificates_extracted,
                    checklist_findings=findings_all
                )
                
                # Prepend cross check findings to the main findings list
                findings_all = cross_checks + findings_all
                
                compliance_score = 100
                total_findings = len(findings_all)
                if total_findings > 0:
                    failures = sum(1 for f in findings_all if f["status"] == "Uygun Değil")
                    warnings = sum(1 for f in findings_all if f["status"] == "Düzeltilmeli")
                    compliance_score = max(0, int(((total_findings - (failures * 1.5) - (warnings * 0.5)) / total_findings) * 100))
                
                vessel_evaluation = generate_local_evaluation(findings_all, vessel_name, vessel_type)
                
                structured_data = {
                    "vessel_name": vessel_name,
                    "imo_number": imo_number,
                    "vessel_type": vessel_type,
                    "tonnage": grt_dwt,
                    "surveyor_notes": surveyor_notes,
                    "compliance_score": compliance_score,
                    "findings": findings_all,
                    "vessel_evaluation": vessel_evaluation,
                    "certificates": certificates_extracted
                }
                
                st.session_state.analysis_data = structured_data
                st.session_state.analysis_vessel_name = vessel_name
                
            except Exception as e:
                st.error(f"Sistem Analiz Hatası: {str(e)}")

    if st.session_state.analysis_data:
        data = st.session_state.analysis_data
        findings = data["findings"]
        current_vessel = st.session_state.analysis_vessel_name
        comp_score = data.get("compliance_score", 100)
        uploaded_certs = data.get("certificates", [])
        
        # Display Certificate particulars card if any were uploaded
        if uploaded_certs:
            st.markdown("### 📇 Tespit Edilen Sertifika Detayları")
            for cert in uploaded_certs:
                with st.expander(f"📄 {cert['cert_type']} (No: {cert['cert_number']})", expanded=True):
                    col_cert_a, col_cert_b = st.columns(2)
                    with col_cert_a:
                        st.markdown(f"**Gemi Adı:** {cert['vessel_name']}")
                        st.markdown(f"**IMO:** {cert['imo']}")
                        st.markdown(f"**Tonaj:** {cert['grt']} GRT / {cert['dwt']} DWT")
                    with col_cert_b:
                        st.markdown(f"**Düzenlenme Tarihi:** {cert['issue_date']}")
                        st.markdown(f"**Son Geçerlilik Tarihi:** {cert['expiry_date']}")
                        
        st.write("---")
        st.markdown(f"## 📊 Sörvey ve Çapraz Kontrol Denetim Raporu: {current_vessel}")
        
        c_crit = sum(1 for f in findings if f.get("severity") in ["critical", "error"] or f.get("status") == "Uygun Değil")
        c_warn = sum(1 for f in findings if f.get("status") == "Düzeltilmeli" or f.get("severity") == "warning")
        c_succ = sum(1 for f in findings if f.get("status") == "Uygun" or f.get("severity") == "success")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns([1.2, 1, 1, 1])
        with col_m1:
            score_color = "#ef4444" if comp_score < 60 else ("#f59e0b" if comp_score < 85 else "#10b981")
            st.markdown(f"""
            <div class="metric-panel" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div class="metric-label" style="margin-bottom: 0.5rem;">UYUMLULUK SKORU</div>
                <div class="score-circle" style="border-color: {score_color}; color: {score_color}; background: {score_color}0d; width: 85px; height: 85px; font-size: 1.6rem; font-weight: 800;">
                    {comp_score}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class="metric-panel" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div class="metric-label" style="margin-bottom: 0.5rem;">🚨 KRİTİK EKSİKLİKLER</div>
                <div class="metric-value" style="font-size: 3rem; color: #ef4444;">{c_crit}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class="metric-panel" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div class="metric-label" style="margin-bottom: 0.5rem;">⚠️ UYARI & DÜZELTMELER</div>
                <div class="metric-value" style="font-size: 3rem; color: #f59e0b;">{c_warn}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m4:
            st.markdown(f"""
            <div class="metric-panel" style="text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div class="metric-label" style="margin-bottom: 0.5rem;">✅ UYGUN MADDELER</div>
                <div class="metric-value" style="font-size: 3rem; color: #10b981;">{c_succ}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("### 🔍 Sörvey Denetim Analiz Özeti")
        st.info(data.get("vessel_evaluation", ""))
        
        st.markdown("### 📥 Raporu Dışa Aktar")
        btn_d1, btn_d2 = st.columns(2)
        with btn_d1:
            excel_data = generate_excel(findings, data)
            st.download_button(
                label="📥 Raporu Excel (XLSX) Formatında İndir",
                data=excel_data,
                file_name=f"{current_vessel}_Audit_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        with btn_d2:
            html_data = generate_html_report(findings, current_vessel)
            st.download_button(
                label="📄 Raporu Yazdırılabilir Çıktı (HTML) Olarak İndir",
                data=html_data,
                file_name=f"{current_vessel}_Audit_Report.html",
                mime="text/html",
                type="secondary",
                use_container_width=True
            )
            
        st.write("---")
        st.markdown("### 📋 Denetim Bulgu Detayları")
        tab1, tab2, tab3, tab4 = st.tabs([
            f"🔍 Tüm Bulgular ({len(findings)})",
            f"❌ Uygunsuzluklar ({c_crit})",
            f"⚠️ Düzeltilmesi Gerekenler ({c_warn})",
            f"✅ Uygun Olanlar ({c_succ})"
        ])
        
        def render_findings_list(filtered):
            if not filtered:
                st.success("Bu kategoride bulgu tespit edilmedi.")
                return
                
            for f in filtered:
                sev = f.get("severity", "info").lower()
                title = f.get("title", "")
                rule = f.get("rule", "Kural Belirtilmemiş")
                desc = f.get("description", "")
                status = f.get("status", "")
                item_no = f.get("item_no", "-")
                rec = f.get("recommendation", "")
                
                card_style = f"card-{sev}"
                badge_style = f"badge-{sev}"
                rec_border = f"rec-border-{sev}"
                icon = "🚨" if sev in ["critical", "error"] or status == "Uygun Değil" else "⚠️" if status == "Düzeltilmeli" else "✅"
                
                st.markdown(f"""
                <div class="finding-card {card_style}">
                    <span class="finding-rule {badge_style}">{rule}</span>
                    <div class="finding-title">{item_no}. {icon} {title} &mdash; ({status})</div>
                    <div class="finding-desc">{desc}</div>
                    {f'<div class="finding-rec {rec_border}"><b>🔧 Düzeltici Eylem Önerisi:</b> {rec}</div>' if rec else ''}
                </div>
                """, unsafe_allow_html=True)

        with tab1:
            render_findings_list(findings)
        with tab2:
            render_findings_list([f for f in findings if f.get("status") == "Uygun Değil"])
        with tab3:
            render_findings_list([f for f in findings if f.get("status") == "Düzeltilmeli"])
        with tab4:
            render_findings_list([f for f in findings if f.get("status") == "Uygun"])


# ==========================================
# VIEW 5: IMO REGULATIONS LIBRARY
# ==========================================
elif st.session_state.active_view == "Reg Library":
    st.subheader("📚 SOLAS / MARPOL / BWM / AFS / ICLL Mevzuat Kütüphanesi")
    st.markdown("Sistemimizde yüklü olan ve sörvey denetimi sırasında kullanılan temel uluslararası kurallar.")
    
    col_l1, col_l2 = st.columns([1, 2.5])
    with col_l1:
        st.markdown("### 📋 Kural Başlıkları")
        selected_category = st.radio(
            "Mevzuat Kategorisi Seçin",
            ["Tümü", "LSA (Can Kurtarma)", "FFE (Yangın Güvenliği)", "Çevre ve Kirlilik (MARPOL/BWM/AFS)", "Navigasyon & Telsiz", "Yük Sınırı & Bütünlük (ICLL)"]
        )
        search_reg = st.text_input("Kural Arama (SOLAS, MARPOL, vb.)", placeholder="Örn: Reg 10...")
        
    with col_l2:
        st.markdown("### 📖 Mevzuat Detayları")
        filtered_regs = {}
        for code, info in REGULATIONS_DB.items():
            cat_match = True
            if selected_category == "LSA (Can Kurtarma)":
                cat_match = info["category"] == "LSA (Life Saving Appliances)"
            elif selected_category == "FFE (Yangın Güvenliği)":
                cat_match = info["category"] in ["FFE (Fire Fighting Equipment)", "Fire Safety"]
            elif selected_category == "Çevre ve Kirlilik (MARPOL/BWM/AFS)":
                cat_match = info["category"] in ["Environmental / Pollution", "Documentation"] or "BWM" in info["category"] or "AFS" in info["category"]
            elif selected_category == "Navigasyon & Telsiz":
                cat_match = info["category"] in ["Navigation", "Radio / GMDSS"]
            elif selected_category == "Yük Sınırı & Bütünlük (ICLL)":
                cat_match = "Draft" in info["category"] or "Load Line" in info["category"]
                
            text_match = True
            if search_reg:
                text_match = search_reg.lower() in code.lower() or search_reg.lower() in info["title"].lower() or search_reg.lower() in info["description"].lower()
                
            if cat_match and text_match:
                filtered_regs[code] = info
                
        if not filtered_regs:
            st.info("Kriterlere uygun mevzuat kaydı bulunamadı.")
        else:
            for code, info in filtered_regs.items():
                st.markdown(f"""
                <div class="reg-card">
                    <div class="reg-chapter">{info['chapter']} &bull; {info['category']}</div>
                    <div class="reg-title">{code}: {info['title']}</div>
                    <div style="font-size: 0.9rem; color: #475569; margin-bottom: 0.75rem; line-height: 1.5;">
                        {info['description']}
                    </div>
                    <div style="border-top: 1px solid #f1f5f9; padding-top: 0.75rem; font-size: 0.85rem; color: #64748b;">
                        <b>Hedef Kelimeler:</b> {', '.join(info['checklist_keywords'])} <br/>
                        <b>Uygulanabilirlik:</b> {info['applicability']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
