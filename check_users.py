#!/usr/bin/env python3
"""
Veritabanındaki kullanıcıları kontrol et
"""

from app import create_app
from models.user_models import User

def check_users():
    """Veritabanındaki tüm kullanıcıları listele"""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        
        print(f"📊 Toplam kullanıcı sayısı: {len(users)}")
        print("=" * 60)
        
        if not users:
            print("❌ Veritabanında hiç kullanıcı bulunamadı!")
            return False
        
        for i, user in enumerate(users, 1):
            print(f"{i}. Kullanıcı:")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Ad: {user.ad}")
            print(f"   Soyad: {user.soyad}")
            print(f"   Role: {user.role}")
            print(f"   Aktif: {user.is_active}")
            print(f"   Son Giriş: {user.son_giris}")
            print(f"   Başarısız Denemeler: {user.failed_attempts}")

            # Şifre kontrolü
            password_check = user.check_password('123456')
            print(f"   Şifre '123456' kontrolü: {password_check}")
            print("-" * 40)
        
        return True

def create_test_user():
    """Test kullanıcısı oluştur"""
    app = create_app()
    with app.app_context():
        # Önce var mı kontrol et
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            print("✅ Test kullanıcısı zaten mevcut!")
            return True
        
        # Yeni kullanıcı oluştur
        from models import db
        
        new_user = User(
            email='test@example.com',
            ad='Test',
            soyad='User',
            role='user',
            is_active=True
        )
        new_user.set_password('123456')
        
        db.session.add(new_user)
        db.session.commit()
        
        print("✅ Test kullanıcısı oluşturuldu!")
        return True

if __name__ == "__main__":
    print("🔍 Kullanıcı Kontrolü Başlıyor...\n")
    
    # 1. Mevcut kullanıcıları listele
    print("1. Mevcut Kullanıcılar:")
    users_exist = check_users()
    print()
    
    # 2. Test kullanıcısı yoksa oluştur
    if not users_exist:
        print("2. Test Kullanıcısı Oluşturuluyor:")
        create_test_user()
        print()
        
        print("3. Güncellenmiş Kullanıcı Listesi:")
        check_users()
    
    print("🏁 Kontrol tamamlandı!")
