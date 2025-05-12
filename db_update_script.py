from app import db, app
import sqlalchemy as sa
from sqlalchemy import text

# Veritabanı bağlantısını al
with app.app_context():
    # Transaction ile veritabanı işlemlerini yürüt
    with db.engine.begin() as conn:
        try:
            print("\n--- ÖNCEKİ ALANLAR (CRM_CONTACTS) ---")
            # Segment sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_contacts') AND name = 'segment')
            BEGIN
                ALTER TABLE crm_contacts ADD segment NVARCHAR(50) DEFAULT 'Potansiyel'
            END
            """))
            print("Segment sütunu eklendi.")
            
            # Tags sütununu ekle (JSON verisi için NVARCHAR(MAX))
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_contacts') AND name = 'tags')
            BEGIN
                ALTER TABLE crm_contacts ADD tags NVARCHAR(MAX)
            END
            """))
            print("Tags sütunu eklendi.")
            
            # Value_score sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_contacts') AND name = 'value_score')
            BEGIN
                ALTER TABLE crm_contacts ADD value_score INT DEFAULT 0
            END
            """))
            print("Value_score sütunu eklendi.")
            
            # Last_contact_date sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_contacts') AND name = 'last_contact_date')
            BEGIN
                ALTER TABLE crm_contacts ADD last_contact_date DATETIME
            END
            """))
            print("Last_contact_date sütunu eklendi.")
            
            # KULLANICI ATAMA SİSTEMİ İÇİN YENİ ALANLAR
            print("\n--- YENİ ALANLAR: USERS ---")
            # role sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'users') AND name = 'role')
            BEGIN
                ALTER TABLE users ADD role NVARCHAR(20) DEFAULT 'danışman'
            END
            """))
            print("Role sütunu eklendi.")
            
            # report_to_id sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'users') AND name = 'report_to_id')
            BEGIN
                ALTER TABLE users ADD report_to_id INT NULL
            END
            """))
            print("Report_to_id sütunu eklendi.")
            
            # Yabancı anahtar kısıtlaması ekle (users -> users ilişkisi)
            conn.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.foreign_keys 
                WHERE name = 'FK_User_ReportsTo'
            )
            BEGIN
                ALTER TABLE users 
                ADD CONSTRAINT FK_User_ReportsTo 
                FOREIGN KEY (report_to_id) REFERENCES users(id)
            END
            """))
            print("FK_User_ReportsTo yabancı anahtar kısıtlaması eklendi.")
            
            print("\n--- YENİ ALANLAR: CRM_TASKS ---")
            
            # Task tablosuna yeni alanlar ekle
            # task_type sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'task_type')
            BEGIN
                ALTER TABLE crm_tasks ADD task_type NVARCHAR(20) DEFAULT 'personal'
            END
            """))
            print("Task_type sütunu eklendi.")
            
            # previous_assignee_id sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'previous_assignee_id')
            BEGIN
                ALTER TABLE crm_tasks ADD previous_assignee_id INT NULL
            END
            """))
            print("Previous_assignee_id sütunu eklendi.")
            
            # reassigned_at sütununu ekle 
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reassigned_at')
            BEGIN
                ALTER TABLE crm_tasks ADD reassigned_at DATETIME NULL
            END
            """))
            print("Reassigned_at sütunu eklendi.")
            
            # reassigned_by_id sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reassigned_by_id')
            BEGIN
                ALTER TABLE crm_tasks ADD reassigned_by_id INT NULL
            END
            """))
            print("Reassigned_by_id sütunu eklendi.")
            
            # reassignment_reason sütununu ekle
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reassignment_reason')
            BEGIN
                ALTER TABLE crm_tasks ADD reassignment_reason NVARCHAR(MAX) NULL
            END
            """))
            print("Reassignment_reason sütunu eklendi.")
            
            # Task tablosuna yabancı anahtarlar ekle
            conn.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.foreign_keys 
                WHERE name = 'FK_Task_PreviousAssignee'
            )
            BEGIN
                ALTER TABLE crm_tasks 
                ADD CONSTRAINT FK_Task_PreviousAssignee 
                FOREIGN KEY (previous_assignee_id) REFERENCES users(id)
            END
            """))
            print("FK_Task_PreviousAssignee yabancı anahtar kısıtlaması eklendi.")
            
            conn.execute(text("""
            IF NOT EXISTS (
                SELECT * FROM sys.foreign_keys 
                WHERE name = 'FK_Task_ReassignedBy'
            )
            BEGIN
                ALTER TABLE crm_tasks 
                ADD CONSTRAINT FK_Task_ReassignedBy 
                FOREIGN KEY (reassigned_by_id) REFERENCES users(id)
            END
            """))
            print("FK_Task_ReassignedBy yabancı anahtar kısıtlaması eklendi.")
            
            print("\n--- VERİTABANI ŞEMA GÜNCELLEMESİ TAMAMLANDI ---")
            print("\nBir sonraki adım: app.py dosyasındaki yorum satırlarını kaldırın ve uygulamayı yeniden başlatın.")
            
        except Exception as e:
            # with blokundaki işlem başarısız olursa otomatik olarak rollback yapılır
            print(f"Hata oluştu: {str(e)}")
            raise
