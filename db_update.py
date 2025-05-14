"""
Veritabanı Güncelleme Betiği
Bu betik, kullanıcı atama sistemi için gerekli veritabanı şema değişikliklerini uygular.
"""
from app import db, app
import sqlalchemy as sa
from sqlalchemy import inspect
import sys

def add_column(engine, table_name, column):
    """Veritabanına sütun ekler, eğer sütun zaten varsa pas geçer"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    column_name = column.compile(dialect=engine.dialect)
    column_name = column_name.split()[0].strip('"').strip('`').strip("'")
    
    if column_name not in columns:
        column_type = column.type.compile(engine.dialect)
        engine.execute(f'ALTER TABLE {table_name} ADD {column_name} {column_type}')
        print(f"'{column_name}' sütunu '{table_name}' tablosuna eklendi.")
    else:
        print(f"'{column_name}' sütunu zaten '{table_name}' tablosunda var.")

def update_schema():
    """Veritabanı şemasını günceller"""
    try:
        with app.app_context():
            engine = db.engine
            
            # User tablosuna 'role' ve 'report_to_id' alanlarını ekle
            print("\n---- USERS TABLOSU GÜNCELLENİYOR ----")
            add_column(engine, 'users', sa.Column('role', sa.String(20), server_default='danışman'))
            add_column(engine, 'users', sa.Column('report_to_id', sa.Integer, nullable=True))
            
            # Yabancı anahtar kısıtlaması ekle (users -> users ilişkisi)
            # NOT: Yabancı anahtar kısıtlamaları doğrudan SQL ile kontrol edilmeli - 
            # SQLAlchemy tablo zaten varsa bu tür kısıtlamaları eklemekte zorlanabilir
            try:
                engine.execute("""
                IF NOT EXISTS (
                    SELECT * FROM sys.foreign_keys 
                    WHERE name = 'FK_User_ReportsTo'
                )
                BEGIN
                    ALTER TABLE users 
                    ADD CONSTRAINT FK_User_ReportsTo 
                    FOREIGN KEY (report_to_id) REFERENCES users(id)
                END
                """)
                print("'FK_User_ReportsTo' yabancı anahtar kısıtlaması eklendi.")
            except Exception as e:
                print(f"Yabancı anahtar kısıtlaması eklenirken hata oluştu: {str(e)}")
            
            # Task tablosuna yeni alanlar ekle
            print("\n---- CRM_TASKS TABLOSU GÜNCELLENİYOR ----")
            add_column(engine, 'crm_tasks', sa.Column('task_type', sa.String(20), server_default='personal'))
            add_column(engine, 'crm_tasks', sa.Column('previous_assignee_id', sa.Integer, nullable=True))
            add_column(engine, 'crm_tasks', sa.Column('reassigned_at', sa.DateTime, nullable=True))
            add_column(engine, 'crm_tasks', sa.Column('reassigned_by_id', sa.Integer, nullable=True))
            add_column(engine, 'crm_tasks', sa.Column('reassignment_reason', sa.Text, nullable=True))
            
            # Yabancı anahtar kısıtlamaları ekle (tasks -> users ilişkileri)
            try:
                engine.execute("""
                IF NOT EXISTS (
                    SELECT * FROM sys.foreign_keys 
                    WHERE name = 'FK_Task_PreviousAssignee'
                )
                BEGIN
                    ALTER TABLE crm_tasks 
                    ADD CONSTRAINT FK_Task_PreviousAssignee 
                    FOREIGN KEY (previous_assignee_id) REFERENCES users(id)
                END
                """)
                print("'FK_Task_PreviousAssignee' yabancı anahtar kısıtlaması eklendi.")
            except Exception as e:
                print(f"Yabancı anahtar kısıtlaması eklenirken hata oluştu: {str(e)}")
                
            try:
                engine.execute("""
                IF NOT EXISTS (
                    SELECT * FROM sys.foreign_keys 
                    WHERE name = 'FK_Task_ReassignedBy'
                )
                BEGIN
                    ALTER TABLE crm_tasks 
                    ADD CONSTRAINT FK_Task_ReassignedBy 
                    FOREIGN KEY (reassigned_by_id) REFERENCES users(id)
                END
                """)
                print("'FK_Task_ReassignedBy' yabancı anahtar kısıtlaması eklendi.")
            except Exception as e:
                print(f"Yabancı anahtar kısıtlaması eklenirken hata oluştu: {str(e)}")
            
            print("\n---- VERİTABANI GÜNCELLEMESİ TAMAMLANDI ----")
            print("\nBu betiği çalıştırdıktan sonra lütfen:")
            print("1. app.py dosyasında yorum satırına alınan kod parçalarını tekrar aktif hale getirin")
            print("2. Sistemi yeniden başlatın ve test edin\n")
            
    except Exception as e:
        print(f"\nVERİTABANI GÜNCELLENİRKEN HATA OLUŞTU: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Veritabanı şema güncellemesi başlatılıyor...")
    success = update_schema()
    if success:
        print("İşlem başarıyla tamamlandı!")
    else:
        print("İşlem sırasında hatalar oluştu, lütfen yukarıdaki mesajları kontrol edin.")
        sys.exit(1)
