#!/usr/bin/env python3
"""
Mevcut test kullanıcısı ile login testi
"""

import requests
import json

def test_existing_user_login():
    """Mevcut test kullanıcısı ile login testi"""
    
    # Test kullanıcısı bilgileri
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    print("🔐 Testing login with existing user...")
    print(f"📤 Login data: {json.dumps(login_data, indent=2)}")
    
    try:
        # Login endpoint'ini test et
        url = 'http://localhost:5000/api/v1/auth/login'
        
        print(f"🔄 Sending POST request to: {url}")
        
        response = requests.post(
            url, 
            json=login_data, 
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login başarılı!")
            data = response.json()
            if 'data' in data and 'access_token' in data['data']:
                print(f"🎫 Access Token alındı: {data['data']['access_token'][:50]}...")
                return True
            else:
                print("❌ Response'da token bulunamadı!")
                return False
        else:
            print(f"❌ Login başarısız! Status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Flask sunucusuna bağlanılamadı! Sunucu çalışıyor mu?")
        return False
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False

def test_api_health():
    """API health check"""
    try:
        print("🏥 Testing API health...")
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        print(f"📥 Health Status: {response.status_code}")
        print(f"📥 Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_api_info():
    """API info check"""
    try:
        print("ℹ️ Testing API info...")
        response = requests.get('http://localhost:5000/api/v1/', timeout=5)
        print(f"📥 API Info Status: {response.status_code}")
        print(f"📥 API Info Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API info check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Mevcut Kullanıcı Login Testi Başlıyor...\n")
    
    # 1. Health check
    print("1. API Health Check:")
    health_ok = test_api_health()
    print()
    
    # 2. API info check
    print("2. API Info Check:")
    info_ok = test_api_info()
    print()
    
    # 3. Login test
    if health_ok:
        print("3. Login Test:")
        login_ok = test_existing_user_login()
        print()
        
        if login_ok:
            print("🎉 Login testi başarılı!")
        else:
            print("❌ Login testi başarısız!")
    else:
        print("⚠️ API health check başarısız, login testi yapılmıyor.")
    
    print("\n🏁 Test tamamlandı!")
