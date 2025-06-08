#!/usr/bin/env python3
"""
Detaylı login debug scripti
"""

from app import create_app
from models.user_models import User
from werkzeug.security import check_password_hash, generate_password_hash
import requests
import json

def debug_password_hash():
    """Şifre hash'ini detaylı debug et"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        if user:
            print("🔍 Kullanıcı Şifre Debug:")
            print(f"   Email: {user.email}")
            print(f"   Stored Hash: {user.password_hash}")
            print(f"   Hash Length: {len(user.password_hash)}")
            print(f"   Hash Type: {type(user.password_hash)}")
            
            # Test şifresi
            test_password = '123456'
            print(f"\n🧪 Test Şifresi: '{test_password}'")
            
            # User model metodu ile test
            user_method_result = user.check_password(test_password)
            print(f"   User.check_password() sonucu: {user_method_result}")
            
            # Direkt Werkzeug ile test
            werkzeug_result = check_password_hash(user.password_hash, test_password)
            print(f"   check_password_hash() sonucu: {werkzeug_result}")
            
            # Yeni hash oluştur ve karşılaştır
            new_hash = generate_password_hash(test_password)
            print(f"\n🆕 Yeni Hash: {new_hash}")
            new_hash_check = check_password_hash(new_hash, test_password)
            print(f"   Yeni hash ile test: {new_hash_check}")
            
            # Eğer mevcut hash çalışmıyorsa, yenisini kaydet
            if not user_method_result:
                print("\n🔧 Mevcut hash çalışmıyor, yenisini kaydediyorum...")
                user.set_password(test_password)
                from models import db
                db.session.commit()
                print("✅ Yeni hash kaydedildi!")
                
                # Tekrar test et
                final_test = user.check_password(test_password)
                print(f"   Final test sonucu: {final_test}")
            
            return user_method_result
        else:
            print("❌ Kullanıcı bulunamadı!")
            return False

def test_api_with_debug():
    """API'yi debug bilgileri ile test et"""
    try:
        url = 'http://localhost:5000/api/v1/auth/login'
        data = {
            'email': 'test@example.com',
            'password': '123456'
        }
        
        print(f"\n🔄 API Login test ediliyor: {url}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login başarılı!")
            print(f"   Access Token: {result.get('data', {}).get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Login başarısız!")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Detaylı Login Debug Başlıyor...\n")
    
    # 1. Şifre hash debug
    print("1. Şifre Hash Debug:")
    password_ok = debug_password_hash()
    
    # 2. API test
    if password_ok:
        print("\n2. API Login Testi:")
        test_api_with_debug()
    else:
        print("\n⚠️ Şifre sorunu çözülene kadar API test edilmiyor.")
    
    print("\n🏁 Debug tamamlandı!")
