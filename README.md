# 🚢 Klas Sörveyörü Asistanı V3

Bu portal, gemilerin emniyet, çevre koruma ve klas uyumluluk durumlarını izlemek, sörvey kontrol listelerini (checklist) ve gemi sertifikalarını otomatik denetleyip çapraz kontrol etmek amacıyla geliştirilmiş bir kararlar asistanıdır.

---

## 🌟 Temel Özellikler

1. **Gemi & Sertifika Takip Portalı**: PHRS B2B portalından çekilen gerçek gemi particulars (isim, IMO, tonaj, klas) ve sertifika geçerlilik tarihlerini izleme.
2. **Aylık Takvim Görünümü**: Yenileme süreleri yaklaşan sertifikaları ay bazında sekmeli (tab) arayüzde ve kategorilere göre (LSA, FFE, MARPOL vb.) gösterme.
3. **Sörvey Raporu Denetimi (Yerel Motor)**: Yüklenen PDF sörvey checklistlerindeki tabloları ve onay kutularını okuyup, SOLAS, MARPOL, BWM, AFS ve ICLL kurallarına göre analiz etme.
4. **Çapraz Kontrol (Cross-Check) Teknolojisi**: Checklist ile birlikte gemi klas/çevre sertifikalarını yüklediğinizde gemi ismi, IMO, tonaj, geçerlilik süresi ve teknik kural çelişkilerini otomatik denetleme.
5. **Malta & Comoros Bayrak Filtresi**: Sizin tarafınızdan yönetilmeyen Malta ve Comoros bayraklı gemilerin otomatik elenerek listelenmesi.

---

## 📁 Proje Dosya Yapısı

* `app.py`: Ana Streamlit web uygulaması arayüzü ve akışı.
* `doc_processor.py`: PDF belgelerini (checklist ve sertifika) okuma, sınıflandırma ve çapraz dosya analizi yapan motor.
* `rules_engine.py`: IMO, SOLAS ve MARPOL kural tanımlarını, anahtar kelime eşleşmelerini ve uygulanabilirlik koşullarını içeren kural bankası.
* `vessel_db.py`: SQLite veritabanı işlemlerini, Excel okuma ve Comoros/Malta filtrelemelerini yöneten yardımcı modül.
* `scrape_vessels.py`: PHRS B2B sisteminden gemi listesini ve detaylı particulars verilerini çeken Python betiği.
* `sertifika.py`: PHRS B2B sisteminden sertifika geçerlilik tarihlerini çeken Python betiği.
* `vessels.db`: Tüm güncel gemi ve sertifika verilerinin tutulduğu SQLite veritabanı.
* `PHRS_Tüm_Gemiler.xlsx` / `PHRS_Acil_Sertifikalar.xlsx` / `PHRS_CERT_DUE_DATE.xlsx`: Portal verilerinin temel kaynağını oluşturan Excel tabloları.
* `requirements.txt`: Uygulamanın çalışması için gerekli Python kütüphane bağımlılıkları.

---

## 🚀 Kurulum ve Yerel Çalıştırma

### 1. Gereksinimlerin Yüklenmesi
Uygulama klasöründe bir terminal/CMD açarak gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
