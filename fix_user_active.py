#!/usr/bin/env python3
"""
Test kullanıcısının is_active değerini düzeltme scripti
"""

from app import create_app
from models import db
from models.user_models import User

def fix_user_active():
    app = create_app()
    with app.app_context():
        try:
            # Test kullanıcısını bul
            user = User.query.filter_by(email='test@example.com').first()
            if user:
                print(f"📝 Kullanıcı bulundu: {user.email}")
                print(f"   Mevcut is_active: {user.is_active}")
                print(f"   Mevcut _is_active: {user._is_active}")
                
                # is_active değerini True yap
                user.is_active = True
                db.session.commit()
                
                print(f"✅ is_active değeri güncellendi!")
                print(f"   Yeni is_active: {user.is_active}")
                print(f"   Yeni _is_active: {user._is_active}")
                
            else:
                print("❌ Test kullanıcısı bulunamadı!")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Hata oluştu: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_user_active()