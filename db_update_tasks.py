from app import db, app
import sqlalchemy as sa
from sqlalchemy import text

print("Görevler ve Hatırlatıcılar için veritabanı güncellemesi başlatılıyor...")

# Veritabanı bağlantısını al
with app.app_context():
    # Transaction ile veritabanı işlemlerini yürüt
    with db.engine.begin() as conn:
        try:
            # Task modeli için yeni sütunlar ekle
            print("Task tablosu güncelleniyor...")
            
            # Tekrarlanan görevler için alanlar
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'is_recurring')
            BEGIN
                ALTER TABLE crm_tasks ADD is_recurring BIT DEFAULT 0
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'recurrence_type')
            BEGIN
                ALTER TABLE crm_tasks ADD recurrence_type NVARCHAR(50)
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'recurrence_interval')
            BEGIN
                ALTER TABLE crm_tasks ADD recurrence_interval INT DEFAULT 1
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'recurrence_end_date')
            BEGIN
                ALTER TABLE crm_tasks ADD recurrence_end_date DATETIME
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'parent_task_id')
            BEGIN
                ALTER TABLE crm_tasks ADD parent_task_id INT
            END
            """))
            
            # Hatırlatıcı özellikleri için alanlar
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reminder_enabled')
            BEGIN
                ALTER TABLE crm_tasks ADD reminder_enabled BIT DEFAULT 0
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reminder_time')
            BEGIN
                ALTER TABLE crm_tasks ADD reminder_time DATETIME
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'reminder_sent')
            BEGIN
                ALTER TABLE crm_tasks ADD reminder_sent BIT DEFAULT 0
            END
            """))
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'crm_tasks') AND name = 'completed_at')
            BEGIN
                ALTER TABLE crm_tasks ADD completed_at DATETIME
            END
            """))
            
            # Parent-child ilişkisi için foreign key ekle (self-referential)
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID(N'crm_tasks') AND name = 'FK_task_parent')
            BEGIN
                ALTER TABLE crm_tasks ADD CONSTRAINT FK_task_parent FOREIGN KEY (parent_task_id) REFERENCES crm_tasks(id)
            END
            """))
            
            print("Task tablosu güncellendi.")
            
            # Reminder tablosunu oluştur
            print("Reminder tablosu oluşturuluyor...")
            
            conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'crm_reminders')
            BEGIN
                CREATE TABLE crm_reminders (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    user_id INT NOT NULL,
                    contact_id INT,
                    deal_id INT,
                    task_id INT,
                    title NVARCHAR(200) NOT NULL,
                    message NVARCHAR(MAX),
                    reminder_time DATETIME NOT NULL,
                    is_sent BIT DEFAULT 0,
                    sent_at DATETIME,
                    notification_type NVARCHAR(20) DEFAULT 'app',
                    created_at DATETIME DEFAULT GETDATE(),
                    updated_at DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (contact_id) REFERENCES crm_contacts(id),
                    FOREIGN KEY (deal_id) REFERENCES crm_deals(id),
                    FOREIGN KEY (task_id) REFERENCES crm_tasks(id)
                )
            END
            """))
            
            print("Reminder tablosu oluşturuldu.")
            print("Veritabanı başarıyla güncellendi!")
            
        except Exception as e:
            # with blokundaki işlem başarısız olursa otomatik olarak rollback yapılır
            print(f"Hata oluştu: {str(e)}")
            raise
