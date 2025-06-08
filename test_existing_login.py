#!/usr/bin/env python3
"""
Mevcut test@example.com kullanıcısı ile login testi
"""

import requests
import json

def test_existing_login():
    """Mevcut test@example.com kullanıcısı ile login testi"""
    
    # Mevcut kullanıcı bilgileri
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    print("🔐 Testing login with existing user: test@example.com")
    print(f"📤 Login data: {json.dumps(login_data, indent=2)}")
    
    try:
        url = 'http://localhost:5000/api/v1/auth/login'
        
        print(f"🔄 Sending POST request to: {url}")
        
        response = requests.post(
            url, 
            json=login_data, 
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
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
                print(f"👤 User: {data['data']['user']['ad']} {data['data']['user']['soyad']}")
                return True
            else:
                print("❌ Response'da token bulunamadı!")
                return False
        else:
            print(f"❌ Login başarısız! Status: {response.status_code}")
            if response.status_code == 401:
                print("🔍 401 Unauthorized - Kullanıcı bulunamadı veya şifre yanlış")
            return False
            
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False

def test_other_users():
    """Diğer mevcut kullanıcılar ile test"""
    
    # Bilinen çalışan kullanıcılar
    test_users = [
        {"email": "altanbariscomert@gmail.com", "password": "123456"},
        {"email": "altanbariscomert@inovanettechs.com", "password": "123456"},
        {"email": "dffhhgfh@kljklj.com", "password": "123456"}
    ]
    
    for user in test_users:
        print(f"\n🔐 Testing login with: {user['email']}")
        
        try:
            url = 'http://localhost:5000/api/v1/auth/login'
            
            response = requests.post(
                url, 
                json=user, 
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {user['email']} ile login başarılı!")
                return True
            else:
                print(f"❌ {user['email']} ile login başarısız!")
                
        except Exception as e:
            print(f"❌ {user['email']} test hatası: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 Mevcut Kullanıcı Login Testleri Başlıyor...\n")
    
    # 1. test@example.com ile test
    print("1. test@example.com ile Login Testi:")
    success1 = test_existing_login()
    
    # 2. Diğer kullanıcılar ile test
    print("\n2. Diğer Kullanıcılar ile Login Testleri:")
    success2 = test_other_users()
    
    print(f"\n🏁 Test Sonuçları:")
    print(f"   test@example.com: {'✅ Başarılı' if success1 else '❌ Başarısız'}")
    print(f"   Diğer kullanıcılar: {'✅ Başarılı' if success2 else '❌ Başarısız'}")
    
    if success1 or success2:
        print("\n🎉 En az bir kullanıcı ile login başarılı!")
    else:
        print("\n❌ Hiçbir mevcut kullanıcı ile login başarılı değil!")
    
    print("\n🏁 Test tamamlandı!")
