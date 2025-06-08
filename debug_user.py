#!/usr/bin/env python3
"""
Test kullanıcısının durumunu kontrol etme scripti
"""

from app import create_app
from models import db
from models.user_models import User

def debug_user():
    app = create_app()
    with app.app_context():
        try:
            # Test kullanıcısını bul
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                print(f"✅ Kullanıcı bulundu:")
                print(f"   Email: {user.email}")
                print(f"   Ad: {user.ad} {user.soyad}")
                print(f"   Role: {user.role}")
                print(f"   is_active (property): {user.is_active}")
                print(f"   _is_active (column): {user._is_active}")
                print(f"   Office ID: {user.office_id}")
                print(f"   Manager ID: {user.manager_id}")
                
                # Şifre kontrolü
                test_password = "123456"
                password_check = user.check_password(test_password)
                print(f"   Şifre kontrolü ('{test_password}'): {password_check}")
                
                # Hash kontrolü
                print(f"   Password hash: {user.password_hash[:50]}...")
                
            else:
                print("❌ Test kullanıcısı bulunamadı!")
                
                # Tüm kullanıcıları listele
                all_users = User.query.all()
                print(f"\n📋 Veritabanındaki tüm kullanıcılar ({len(all_users)} adet):")
                for u in all_users:
                    print(f"   - {u.email} ({u.ad} {u.soyad}) - Role: {u.role} - Active: {u.is_active}")
                    
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_user()