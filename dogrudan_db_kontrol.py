"""
Bu betik, uygulama kodunu kullanmadan doğrudan veritabanına bağlanır ve tabloları kontrol eder.
"""
import pyodbc
import pandas as pd
from sqlalchemy import create_engine, inspect

# MSSQL bağlantı bilgileri
server = "46.221.49.106"
database = "arsa_db"
username = "altan"
password = "Yxrkt2bb7q8."

print("Veritabanı Tabloları ve Yapısı Kontrolü başlatılıyor...")

try:
    # SQLAlchemy bağlantısı
    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    engine = create_engine(connection_string)
    
    # Bağlantı kontrolü
    connection = engine.connect()
    print("Veritabanı bağlantısı başarılı!")
    
    # Tablo listesini al
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\nVeritabanında toplam {len(tables)} tablo bulunuyor:")
    
    for i, table in enumerate(tables, 1):
        print(f"\n{i}. Tablo: {table}")
        
        # Tablo sütunlarını getir
        columns = inspector.get_columns(table)
        print(f"   Sütunlar ({len(columns)}):")
        for column in columns:
            print(f"   - {column['name']} ({column['type']})")
        
        # İlk 3 kaydı getir
        try:
            df = pd.read_sql(f"SELECT TOP 3 * FROM [{table}]", connection)
            if not df.empty:
                print(f"   İlk 3 kayıt sayısı: {len(df)}")
            else:
                print(f"   Tabloda kayıt bulunmuyor.")
        except Exception as e:
            print(f"   Tablo verilerini okuma hatası: {str(e)}")
        
        # İndeksleri kontrol et
        try:
            indexes = inspector.get_indexes(table)
            if indexes:
                print(f"   İndeksler ({len(indexes)}):")
                for index in indexes:
                    print(f"   - {index['name']} sütunları: {index['column_names']}")
            else:
                print("   İndeks tanımlanmamış")
        except Exception as e:
            print(f"   İndeks bilgisi alınamadı: {str(e)}")
            
    # Bağlantıyı kapat
    connection.close()
    
except Exception as e:
    print(f"Veritabanı kontrolü sırasında hata oluştu: {str(e)}")
