"""
Bu betik, veritabanında oluşturulan view'ları kontrol eder ve örnek veri çeker.
"""
import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd
import sys

# MSSQL bağlantı bilgileri
server = "46.221.49.106"
database = "arsa_db"
username = "altan"
password = "Yxrkt2bb7q8."

# Kontrol edilecek view'lar
VIEWS = ["ArsaAnalizRaporu", "CRMDashboard", "KullaniciPerformansi", "BolgeAnalizOzeti"]

def check_views():
    """Oluşturulan view'ları kontrol eder ve örnek veri çeker"""
    print("Veritabanında view kontrolü başlatılıyor...")
    
    try:
        # SQLAlchemy bağlantısı
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        engine = create_engine(connection_string)
        
        # Bağlantı kontrolü
        connection = engine.connect()
        print("Veritabanı bağlantısı başarılı!")
        
        # MS SQL Server'da view'ları sorgula
        sql = text("""
            SELECT name 
            FROM sys.views
        """)
        result = connection.execute(sql)
        
        views_in_db = [row[0] for row in result]
        print(f"\nVeritabanında bulunan viewlar: {len(views_in_db)}")
        for view in views_in_db:
            print(f"- {view}")
        
        # Her view'dan veri çek
        for view_name in VIEWS:
            if view_name in views_in_db:
                print(f"\n📊 {view_name} view'ı bulundu!")
                
                # View'ın sütunlarını al
                metadata_sql = text(f"""
                    SELECT COLUMN_NAME, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{view_name}'
                """)
                columns_result = connection.execute(metadata_sql)
                columns = list(columns_result)
                
                print(f"  Sütunlar ({len(columns)}):")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                
                # View'dan veri çek
                try:
                    data_sql = text(f"SELECT TOP 5 * FROM {view_name}")
                    df = pd.read_sql(data_sql, connection)
                    
                    if not df.empty:
                        print(f"  View'da {len(df)} kayıt bulundu.")
                        print("  Örnek veri:")
                        print("  " + "-" * 80)
                        for i, row in df.iterrows():
                            for col in df.columns[:5]:  # İlk 5 sütunu göster
                                print(f"  {col}: {row[col]}")
                            print("  " + "-" * 80)
                    else:
                        print("  View'da veri bulunamadı.")
                        
                except Exception as e:
                    print(f"  Veri çekilirken hata: {str(e)}")
            else:
                print(f"\n⚠️ {view_name} view'ı veritabanında bulunamadı!")
        
        # Bağlantıyı kapat
        connection.close()
        
    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_views()
