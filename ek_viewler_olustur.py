"""
Bu betik, veritabanında 5 yeni yararlı view oluşturur.
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
        "name": "ZamanBasinaArsaAnalizi",
        "query": """
        SELECT 
            DATEPART(YEAR, a.created_at) as yil,
            DATEPART(MONTH, a.created_at) as ay,
            COUNT(*) as toplam_analiz,
            SUM(a.metrekare) as toplam_metrekare,
            SUM(a.fiyat) as toplam_deger,
            AVG(a.fiyat) as ortalama_deger,
            AVG(a.fiyat/a.metrekare) as ortalama_birim_fiyat,
            COUNT(DISTINCT a.user_id) as aktif_kullanici_sayisi,
            COUNT(DISTINCT a.il) as analiz_yapilan_il_sayisi
        FROM 
            arsa_analizleri a
        GROUP BY 
            DATEPART(YEAR, a.created_at), DATEPART(MONTH, a.created_at)
        ORDER BY 
            yil DESC, ay DESC
        """
    },
    {
        "name": "ImardurumunagoreArsalar",
        "query": """
        SELECT 
            a.imar_durumu,
            COUNT(*) as arsalar_sayisi,
            SUM(a.metrekare) as toplam_metrekare,
            AVG(a.metrekare) as ortalama_metrekare,
            SUM(a.fiyat) as toplam_deger,
            AVG(a.fiyat) as ortalama_deger,
            AVG(a.fiyat/a.metrekare) as ortalama_birim_fiyat,
            MIN(a.fiyat/a.metrekare) as min_birim_fiyat,
            MAX(a.fiyat/a.metrekare) as max_birim_fiyat,
            COUNT(DISTINCT a.il) as il_sayisi,
            COUNT(DISTINCT a.ilce) as ilce_sayisi
        FROM 
            arsa_analizleri a
        WHERE 
            a.imar_durumu IS NOT NULL
        GROUP BY 
            a.imar_durumu
        ORDER BY 
            arsalar_sayisi DESC
        """
    },
    {
        "name": "ArsaFiyatKarsilastirma",
        "query": """
        SELECT 
            a.id,
            a.il,
            a.ilce, 
            a.mahalle,
            a.metrekare,
            a.fiyat,
            a.bolge_fiyat,
            (a.fiyat / a.metrekare) as birim_fiyat,
            (a.bolge_fiyat) as bolge_birim_fiyat,
            (CASE 
                WHEN a.bolge_fiyat > 0 THEN ((a.fiyat/a.metrekare) - a.bolge_fiyat) / a.bolge_fiyat * 100 
                ELSE 0 
            END) as fiyat_farki_yuzdesi,
            (CASE 
                WHEN ((a.fiyat/a.metrekare) > a.bolge_fiyat AND a.bolge_fiyat > 0) THEN 'Pahalı' 
                WHEN ((a.fiyat/a.metrekare) < a.bolge_fiyat AND a.bolge_fiyat > 0) THEN 'Ucuz' 
                ELSE 'Normal' 
            END) as fiyat_degerlendirmesi,
            a.created_at
        FROM 
            arsa_analizleri a
        WHERE 
            a.metrekare > 0
        ORDER BY 
            fiyat_farki_yuzdesi DESC
        """
    },
    {
        "name": "CrmEtkinlikRaporu",
        "query": """
        SELECT 
            u.email as kullanici_email,
            u.ad + ' ' + u.soyad as kullanici_adsoyad,
            CAST(t.created_at as DATE) as tarih,
            COUNT(DISTINCT t.id) as toplam_gorev,
            COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id ELSE NULL END) as tamamlanan_gorev,
            COUNT(DISTINCT CASE WHEN t.status = 'in_progress' THEN t.id ELSE NULL END) as devam_eden_gorev,
            COUNT(DISTINCT CASE WHEN t.status = 'pending' THEN t.id ELSE NULL END) as bekleyen_gorev,
            COUNT(DISTINCT CASE WHEN t.due_date < GETDATE() AND t.status != 'completed' THEN t.id ELSE NULL END) as geciken_gorev,
            AVG(DATEDIFF(HOUR, t.created_at, t.completed_at)) as ortalama_tamamlanma_suresi_saat
        FROM 
            crm_tasks t
        LEFT JOIN 
            users u ON t.user_id = u.id
        GROUP BY 
            u.email, u.ad, u.soyad, CAST(t.created_at as DATE)
        ORDER BY 
            tarih DESC
        """
    },
    {
        "name": "ArsaSWOTAnalizi",
        "query": """
        SELECT 
            a.id as arsa_id,
            a.il,
            a.ilce,
            a.mahalle,
            a.metrekare,
            a.fiyat,
            a.imar_durumu,
            a.swot_analizi,
            COUNT(CASE WHEN JSON_VALUE(a.swot_analizi, '$.strengths[0]') IS NOT NULL THEN 1 ELSE NULL END) as guclu_yon_sayisi,
            COUNT(CASE WHEN JSON_VALUE(a.swot_analizi, '$.weaknesses[0]') IS NOT NULL THEN 1 ELSE NULL END) as zayif_yon_sayisi,
            COUNT(CASE WHEN JSON_VALUE(a.swot_analizi, '$.opportunities[0]') IS NOT NULL THEN 1 ELSE NULL END) as firsat_sayisi,
            COUNT(CASE WHEN JSON_VALUE(a.swot_analizi, '$.threats[0]') IS NOT NULL THEN 1 ELSE NULL END) as tehdit_sayisi
        FROM 
            arsa_analizleri a
        WHERE 
            a.swot_analizi IS NOT NULL
        GROUP BY 
            a.id, a.il, a.ilce, a.mahalle, a.metrekare, a.fiyat, a.imar_durumu, a.swot_analizi
        """
    },
    {
        "name": "CrmFirsatAnaliziRaporu",
        "query": """
        SELECT 
            u.email as kullanici_email,
            u.ad + ' ' + u.soyad as kullanici_adsoyad,
            d.title as firsat_adi,
            d.stage as asama,
            com.name as sirket_adi,
            CONCAT(con.first_name, ' ', con.last_name) as kisi_adi,
            d.value as potansiyel_deger,
            d.expected_close_date as tahmini_kapanma_tarihi,
            d.created_at as olusturma_tarihi,
            DATEDIFF(DAY, d.created_at, GETDATE()) as gecen_gun,
            DATEDIFF(DAY, GETDATE(), d.expected_close_date) as kalan_gun,
            COUNT(t.id) as ilgili_gorev_sayisi,
            (CASE 
                WHEN d.stage = 'closed_won' THEN 'Kazanıldı'
                WHEN d.stage = 'closed_lost' THEN 'Kaybedildi'
                WHEN DATEDIFF(DAY, GETDATE(), d.expected_close_date) < 0 THEN 'Gecikmiş'
                WHEN DATEDIFF(DAY, GETDATE(), d.expected_close_date) < 7 THEN 'Kritik'
                ELSE 'Normal'
            END) as durum
        FROM 
            crm_deals d
        LEFT JOIN 
            users u ON d.user_id = u.id
        LEFT JOIN 
            crm_companies com ON d.company_id = com.id
        LEFT JOIN 
            crm_contacts con ON d.contact_id = con.id
        LEFT JOIN 
            crm_tasks t ON t.deal_id = d.id
        GROUP BY 
            u.email, u.ad, u.soyad, d.title, d.stage, com.name, con.first_name, con.last_name,
            d.value, d.expected_close_date, d.created_at
        """
    },
    {
        "name": "KullaniciYetkiRaporu",
        "query": """
        SELECT 
            u.id as kullanici_id,
            u.email,
            u.ad,
            u.soyad,
            u.role as rol,
            u.registered_on as kayit_tarihi,
            u.son_giris,
            (CASE 
                WHEN u.is_active = 1 THEN 'Aktif'
                ELSE 'Pasif'
            END) as durum,
            (CASE 
                WHEN u.role = 'admin' THEN 'Yönetici'
                WHEN u.role = 'manager' THEN 'Müdür'
                WHEN u.role = 'agent' THEN 'Acente'
                WHEN u.role = 'analyst' THEN 'Analist'
                ELSE 'Standart Kullanıcı'
            END) as rol_aciklamasi,
            COUNT(DISTINCT a.id) as analiz_sayisi,
            COUNT(DISTINCT p.id) as portfolyo_sayisi,
            COUNT(DISTINCT c.id) as kisi_sayisi,
            DATEDIFF(DAY, u.registered_on, GETDATE()) as uyelik_suresi_gun
        FROM 
            users u
        LEFT JOIN 
            arsa_analizleri a ON u.id = a.user_id
        LEFT JOIN 
            portfolios p ON u.id = p.user_id
        LEFT JOIN 
            crm_contacts c ON u.id = c.user_id
        GROUP BY 
            u.id, u.email, u.ad, u.soyad, u.role, u.registered_on, u.son_giris, u.is_active
        """
    }
]

def create_views():
    """Belirtilen viewleri veritabanında oluşturur"""
    print("Veritabanında ek view'lar oluşturma işlemi başlatılıyor...")
    
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
                error_msg = str(e)
                print(f"❌ '{view_name}' view'ı oluşturulurken hata: {error_msg}")
                if "JSON_VALUE" in error_msg:
                    print("   Not: JSON fonksiyonları SQL Server sürümünüz tarafından desteklenmiyor olabilir.")
                    # JSON desteği olmayan sunucular için alternatif sorgu
                    if view_name == "ArsaSWOTAnalizi":
                        basic_query = """
                        SELECT 
                            a.id as arsa_id,
                            a.il,
                            a.ilce,
                            a.mahalle,
                            a.metrekare,
                            a.fiyat,
                            a.imar_durumu,
                            a.swot_analizi
                        FROM 
                            arsa_analizleri a
                        WHERE 
                            a.swot_analizi IS NOT NULL
                        """
                        try:
                            sql = text(f"CREATE VIEW {view_name} AS {basic_query}")
                            connection.execute(sql)
                            connection.commit()
                            print(f"✅ '{view_name}' view'ı basitleştirilmiş olarak oluşturuldu.")
                        except Exception as inner_e:
                            print(f"   Alternatif view oluşturmada da hata: {str(inner_e)}")
        
        print("\nEk view oluşturma işlemi tamamlandı.")
        
        # Oluşturulan viewları kontrol et
        print("\nTüm viewlar:")
        sql = text("""
            SELECT name FROM sys.views
        """)
        result = connection.execute(sql)
        
        for row in result:
            print(f"- {row[0]}")
            
        # Bağlantıyı kapat
        connection.close()
        
    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Kullanıcıdan onay al
    confirm = input("Bu işlem veritabanında ek view'lar oluşturacaktır. Devam etmek istiyor musunuz? (E/H): ")
    
    if confirm.upper() == "E":
        create_views()
    else:
        print("İşlem iptal edildi.")
