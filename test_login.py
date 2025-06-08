#!/usr/bin/env python3
"""
Login test scripti
"""

from app import create_app
from models.user_models import User
import requests
import json

def test_user_exists():
    """Test kullanıcısının varlığını kontrol et"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email='test@example.com').first()
        if user:
            print("✅ Test kullanıcısı bulundu:")
            print(f"   Email: {user.email}")
            print(f"   Ad: {user.ad} {user.soyad}")
            print(f"   Role: {user.role}")
            print(f"   Aktif: {user.is_active}")
            
            # Şifre kontrolü
            if user.check_password('123456'):
                print("✅ Şifre doğru!")
            else:
                print("❌ Şifre yanlış!")
                # Şifreyi yeniden ayarla
                user.set_password('123456')
                from models import db
                db.session.commit()
                print("✅ Şifre 123456 olarak yeniden ayarlandı")
            
            return True
        else:
            print("❌ Test kullanıcısı bulunamadı!")
            return False

def test_api_login():
    """API login endpoint'ini test et"""
    try:
        url = 'http://localhost:5000/api/v1/auth/login'
        data = {
            'email': 'test@example.com',
            'password': '123456'
        }
        
        print(f"\n🔄 API Login test ediliyor: {url}")
        print(f"   Data: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"✅ Response Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login başarılı!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Login başarısız!")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API sunucusuna bağlanılamadı! Flask uygulaması çalışıyor mu?")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def test_api_health():
    """API health check"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check başarılı")
            return True
        else:
            print(f"❌ API Health Check başarısız: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check hatası: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Login Test Başlıyor...\n")
    
    # 1. API Health Check
    print("1. API Health Check:")
    test_api_health()
    
    # 2. Kullanıcı varlık kontrolü
    print("\n2. Kullanıcı Kontrolü:")
    user_exists = test_user_exists()
    
    # 3. API Login testi
    if user_exists:
        print("\n3. API Login Testi:")
        test_api_login()
    
    print("\n🏁 Test tamamlandı!")
