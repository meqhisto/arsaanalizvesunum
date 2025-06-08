"""
Bu betik, veritabanı performansını artırmak için tablolara indeks ekler.
"""
import pyodbc
from sqlalchemy import create_engine, text
import sys

# MSSQL bağlantı bilgileri
server = "46.221.49.106"
database = "arsa_db"
username = "altan"
password = "Yxrkt2bb7q8."

# İndeks eklenecek tablolar ve alanlar
INDEXES_TO_CREATE = [
    # Arsa Analizleri Tablosu İndeksleri
    {
        "table": "arsa_analizleri",
        "indexes": [
            {"name": "ix_arsa_analizleri_user_id", "columns": ["user_id"]},
            {"name": "ix_arsa_analizleri_il_ilce", "columns": ["il", "ilce"]},
            {"name": "ix_arsa_analizleri_created_at", "columns": ["created_at"]},
            {"name": "ix_arsa_analizleri_fiyat", "columns": ["fiyat"]},
            {"name": "ix_arsa_analizleri_metrekare", "columns": ["metrekare"]},
        ]
    },
    # CRM Contacts Tablosu İndeksleri
    {
        "table": "crm_contacts",
        "indexes": [
            {"name": "ix_crm_contacts_user_id", "columns": ["user_id"]},
            {"name": "ix_crm_contacts_status", "columns": ["status"]},
            {"name": "ix_crm_contacts_created_at", "columns": ["created_at"]},
        ]
    },
    # CRM Companies Tablosu İndeksleri
    {
        "table": "crm_companies",
        "indexes": [
            {"name": "ix_crm_companies_user_id", "columns": ["user_id"]},
            {"name": "ix_crm_companies_name", "columns": ["name"]},
        ]
    },
    # CRM Tasks Tablosu İndeksleri
    {
        "table": "crm_tasks",
        "indexes": [
            {"name": "ix_crm_tasks_user_id", "columns": ["user_id"]},
            {"name": "ix_crm_tasks_status", "columns": ["status"]},
            {"name": "ix_crm_tasks_priority", "columns": ["priority"]},
            {"name": "ix_crm_tasks_due_date", "columns": ["due_date"]},
        ]
    },
    # Portfolios Tablosu İndeksleri
    {
        "table": "portfolios",
        "indexes": [
            {"name": "ix_portfolios_user_id", "columns": ["user_id"]},
            {"name": "ix_portfolios_created_at", "columns": ["created_at"]},
        ]
    },
    # Portfolio_arsalar Tablosu İndeksleri
    {
        "table": "portfolio_arsalar",
        "indexes": [
            {"name": "ix_portfolio_arsalar_portfolio_id", "columns": ["portfolio_id"]},
            {"name": "ix_portfolio_arsalar_arsa_id", "columns": ["arsa_id"]},
        ]
    },
    # Deals Tablosu İndeksleri
    {
        "table": "crm_deals",
        "indexes": [
            {"name": "ix_crm_deals_user_id", "columns": ["user_id"]},
            {"name": "ix_crm_deals_stage", "columns": ["stage"]},
            {"name": "ix_crm_deals_company_id", "columns": ["company_id"]},
            {"name": "ix_crm_deals_contact_id", "columns": ["contact_id"]},
            {"name": "ix_crm_deals_expected_close_date", "columns": ["expected_close_date"]},
        ]
    },
]

def create_indexes():
    """Belirtilen tablolara indeks ekler"""
    print("Veritabanı indeksleme işlemi başlatılıyor...")
    
    try:
        # SQLAlchemy bağlantısı
        connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
        engine = create_engine(connection_string)
        
        # Bağlantı kontrolü
        connection = engine.connect()
        print("Veritabanı bağlantısı başarılı!")
        
        # Mevcut indeksleri kontrol et
        existing_indexes = {}
        for table_info in INDEXES_TO_CREATE:
            table = table_info["table"]
            sql = text(f"""
                SELECT name 
                FROM sys.indexes 
                WHERE object_id = OBJECT_ID('{table}')
            """)
            result = connection.execute(sql)
            existing_indexes[table] = [row[0] for row in result]
            
        # İndeksleri oluştur
        for table_info in INDEXES_TO_CREATE:
            table = table_info["table"]
            
            # Önce tablonun varlığını kontrol et
            sql = text(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table}'")
            result = connection.execute(sql).scalar()
            
            if result == 0:
                print(f"⚠️ '{table}' tablosu veritabanında bulunmadı, geçiliyor.")
                continue
                
            print(f"\n▶️ '{table}' tablosu için indeks oluşturma işlemi:")
            
            for index in table_info["indexes"]:
                index_name = index["name"]
                
                # İndeksin zaten var olup olmadığını kontrol et
                if index_name in existing_indexes.get(table, []):
                    print(f"  ⏩ '{index_name}' indeksi zaten mevcut, geçiliyor.")
                    continue
                
                # İndeks oluştur
                columns = ", ".join(index["columns"])
                sql = text(f"CREATE INDEX {index_name} ON {table} ({columns})")
                
                try:
                    connection.execute(sql)
                    connection.commit()
                    print(f"  ✅ '{index_name}' indeksi başarıyla oluşturuldu.")
                except Exception as e:
                    connection.rollback()
                    error_msg = str(e)
                    if "already exists" in error_msg:
                        print(f"  ⏩ '{index_name}' indeksi zaten mevcut.")
                    else:
                        print(f"  ❌ '{index_name}' indeksi oluşturulurken hata: {error_msg}")
        
        print("\nİndeksleme işlemi tamamlandı.")
        
        # Bağlantıyı kapat
        connection.close()
        
    except Exception as e:
        print(f"Veritabanı işlemi sırasında hata oluştu: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Kullanıcıdan onay al
    confirm = input("Bu işlem veritabanı performansını artırmak için indeksler ekleyecektir. Devam etmek istiyor musunuz? (E/H): ")
    
    if confirm.upper() == "E":
        create_indexes()
    else:
        print("İşlem iptal edildi.")
