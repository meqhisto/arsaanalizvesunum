-- Kullanıcılar (users) tablosuna rol ve rapor verme alanlarını ekle
ALTER TABLE users ADD
    role NVARCHAR(20) DEFAULT 'danışman',
    report_to_id INT NULL;

-- Yabancı anahtar kısıtlaması ekle (user'ın kime rapor verdiği)
ALTER TABLE users 
ADD CONSTRAINT FK_User_ReportsTo 
FOREIGN KEY (report_to_id) REFERENCES users(id);

-- Task tablosundaki yeni alanları ekleyin
-- Eğer bu tablo henüz yoksa, hata verebilir - o durumda sadece model değişikliklerini yapabilirsiniz
ALTER TABLE crm_tasks ADD
    task_type NVARCHAR(20) DEFAULT 'personal',
    previous_assignee_id INT NULL,
    reassigned_at DATETIME NULL,
    reassigned_by_id INT NULL,
    reassignment_reason NVARCHAR(MAX) NULL;

-- Task tablosuna yabancı anahtar kısıtlamaları ekle
ALTER TABLE crm_tasks
ADD CONSTRAINT FK_Task_PreviousAssignee 
FOREIGN KEY (previous_assignee_id) REFERENCES users(id);

ALTER TABLE crm_tasks
ADD CONSTRAINT FK_Task_ReassignedBy
FOREIGN KEY (reassigned_by_id) REFERENCES users(id);

-- Brokerları varsayılan olarak ekleyin (örnektir, uygun değerleri kendi veritabanınıza göre değiştirin)
-- Gerçek bir örnek:
-- UPDATE users SET role = 'broker' WHERE id IN (1, 5, 10);

-- İlişkileri ayarla - danışmanların broker'a bağlanması (örnektir)
-- Gerçek bir örnek:
-- UPDATE users SET report_to_id = 1 WHERE id IN (2, 3, 4);  -- 2, 3, 4 numaralı danışmanları 1 numaralı broker'a bağla
