"""
Bu betik, veritabanından kullanılmayan tabloları siler.
"""
import pyodbc
from sqlalchemy import create_engine, text
import sys

# MSSQL bağlantı bilgileri
server = "46.221.49.106"
database = "arsa_db"
username = "altan"
password = "Yxrkt2bb7q8."

# Silinecek tablolar listesi
TABLES_TO_DROP = [
    "emlak_ofisleri",
    "emlak_personel_gorusmeleri",
    "emlak_personel_hedefleri",
    "emlak_personel_portfoyleri",
    "emlak_personelleri",
    "emlak_rol_tanimlari"
]

def delete_tables():
    """Belirtilen tabloları veritabanından siler"""
    print("Kullanılmayan tabloları silme işlemi başlatılıyor...")
    
    try:
        # SQLAlchemy bağlantısı
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        engine = create_engine(connection_string)
        
        # Bağlantı kontrolü
        connection = engine.connect()
        print("Veritabanı bağlantısı başarılı!")
        
        for table in TABLES_TO_DROP:
            try:
                # SQL ifadesi: Tabloyu sil
                sql = text(f"DROP TABLE IF EXISTS {table}")
                connection.execute(sql)
                connection.commit()
                print(f"✅ '{table}' tablosu başarıyla silindi.")
            except Exception as e:
                print(f"❌ '{table}' tablosu silinirken hata oluştu: {str(e)}")
                connection.rollback()
        
        print("\nTablo silme işlemi tamamlandı.")
        
        # Bağlantıyı kapat
        connection.close()
        
    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Kullanıcıdan onay al
    confirm = input("Bu işlem belirtilen tabloları veritabanından kalıcı olarak silecektir. Devam etmek istiyor musunuz? (E/H): ")
    
    if confirm.upper() == "E":
        delete_tables()
    else:
        print("İşlem iptal edildi.")
