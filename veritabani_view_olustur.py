"""
Bu betik, veritabanında kullanışlı view'lar (görünümler) oluşturur.
"""
import pyodbc
from sqlalchemy import create_engine, text
import sys

# MSSQL bağlantı bilgileri
server = "46.221.49.106"
database = "arsa_db"
username = "altan"
password = "Yxrkt2bb7q8."

# Oluşturulacak view'lar ve sorguları
VIEWS_TO_CREATE = [
    {
        "name": "ArsaAnalizRaporu",
        "query": """
        SELECT 
            a.id, 
            u.email as kullanici_email,
            u.ad + ' ' + u.soyad as kullanici_adsoyad,
            a.il, 
            a.ilce, 
            a.mahalle, 
            a.ada, 
            a.parsel,
            a.metrekare,
            a.fiyat,
            a.bolge_fiyat,
            a.imar_durumu,
            a.taks,
            a.kaks,
            a.created_at as olusturma_tarihi,
            COUNT(m.id) as medya_sayisi
        FROM 
            arsa_analizleri a
        LEFT JOIN 
            users u ON a.user_id = u.id
        LEFT JOIN 
            analiz_medya m ON a.id = m.analiz_id
        GROUP BY 
            a.id, u.email, u.ad, u.soyad, a.il, a.ilce, a.mahalle, a.ada, a.parsel, 
            a.metrekare, a.fiyat, a.bolge_fiyat, a.imar_durumu, a.taks, a.kaks, a.created_at
        """
    },
    {
        "name": "CRMDashboard",
        "query": """
        SELECT 
            u.email as kullanici_email,
            u.ad + ' ' + u.soyad as kullanici_adsoyad,
            COUNT(DISTINCT con.id) as toplam_kisi_sayisi,
            COUNT(DISTINCT com.id) as toplam_sirket_sayisi,
            COUNT(DISTINCT d.id) as toplam_firsatlar,
            SUM(CASE WHEN d.stage = 'closed_won' THEN d.value ELSE 0 END) as kazanilan_firsatlar_degeri,
            COUNT(DISTINCT t.id) as toplam_gorevler,
            COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id ELSE NULL END) as tamamlanan_gorevler
        FROM 
            users u
        LEFT JOIN 
            crm_contacts con ON u.id = con.user_id
        LEFT JOIN 
            crm_companies com ON u.id = com.user_id
        LEFT JOIN 
            crm_deals d ON u.id = d.user_id
        LEFT JOIN 
            crm_tasks t ON u.id = t.user_id
        GROUP BY 
            u.email, u.ad, u.soyad
        """
    },
    {
        "name": "KullaniciPerformansi",
        "query": """
        SELECT 
            u.id as kullanici_id,
            u.email as kullanici_email,
            u.ad + ' ' + u.soyad as kullanici_adsoyad,
            COUNT(a.id) as toplam_analiz_sayisi,
            SUM(a.fiyat) as toplam_analiz_degeri,
            AVG(a.fiyat) as ortalama_analiz_degeri,
            MAX(a.fiyat) as en_yuksek_deger,
            MIN(a.fiyat) as en_dusuk_deger,
            MAX(a.created_at) as son_analiz_tarihi,
            COUNT(DISTINCT a.il) as farkli_il_sayisi
        FROM 
            users u
        LEFT JOIN 
            arsa_analizleri a ON u.id = a.user_id
        GROUP BY 
            u.id, u.email, u.ad, u.soyad
        """
    },
    {
        "name": "BolgeAnalizOzeti",
        "query": """
        SELECT 
            il,
            ilce,
            COUNT(*) as arsalar_sayisi,
            SUM(metrekare) as toplam_metrekare,
            AVG(metrekare) as ortalama_metrekare,
            SUM(fiyat) as toplam_deger,
            AVG(fiyat) as ortalama_deger,
            AVG(fiyat/metrekare) as ortalama_metrekare_fiyat,
            MIN(fiyat/metrekare) as min_metrekare_fiyat,
            MAX(fiyat/metrekare) as max_metrekare_fiyat
        FROM 
            arsa_analizleri
        GROUP BY 
            il, ilce
        """
    }
]

def create_views():
    """Belirtilen viewleri veritabanında oluşturur"""
    print("Veritabanında view oluşturma işlemi başlatılıyor...")
    
    try:
        # SQLAlchemy bağlantısı
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        engine = create_engine(connection_string)
        
        # Bağlantı kontrolü
        connection = engine.connect()
        print("Veritabanı bağlantısı başarılı!")
        
        # Viewleri oluştur
        for view_info in VIEWS_TO_CREATE:
            view_name = view_info["name"]
            view_query = view_info["query"]
            
            # Önce mevcut view'ı sil
            try:
                sql = text(f"DROP VIEW IF EXISTS {view_name}")
                connection.execute(sql)
                connection.commit()
                print(f"🔄 '{view_name}' view'ı yeniden oluşturmak için silindi.")
            except Exception as e:
                connection.rollback()
                print(f"⚠️ '{view_name}' view'ı silinirken hata: {str(e)}")
            
            # View'ı oluştur
            try:
                sql = text(f"CREATE VIEW {view_name} AS {view_query}")
                connection.execute(sql)
                connection.commit()
                print(f"✅ '{view_name}' view'ı başarıyla oluşturuldu.")
            except Exception as e:
                connection.rollback()
                print(f"❌ '{view_name}' view'ı oluşturulurken hata: {str(e)}")
        
        print("\nView oluşturma işlemi tamamlandı.")
        
        # Oluşturulan viewları kontrol et
        print("\nOluşturulan viewlar:")
        sql = text("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'dbo'
        """)
        result = connection.execute(sql)
        
        for row in result:
            print(f"- {row[0]}")
            
        # View içeriklerini kontrol et
        for view_info in VIEWS_TO_CREATE:
            view_name = view_info["name"]
            try:
                sample_sql = text(f"SELECT TOP 3 * FROM {view_name}")
                result = connection.execute(sample_sql)
                columns = result.keys()
                
                print(f"\n{view_name} view'ı sütunları:")
                print(", ".join([col for col in columns]))
                
                rows = result.fetchall()
                if rows:
                    print(f"{view_name} view'ında {len(rows)} kayıt bulundu.")
                else:
                    print(f"{view_name} view'ında kayıt bulunamadı.")
            except Exception as e:
                print(f"{view_name} view'ı test edilirken hata: {str(e)}")
        
        # Bağlantıyı kapat
        connection.close()
        
    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Kullanıcıdan onay al
    confirm = input("Bu işlem veritabanında view'lar oluşturacaktır. Devam etmek istiyor musunuz? (E/H): ")
    
    if confirm.upper() == "E":
        create_views()
    else:
        print("İşlem iptal edildi.")
