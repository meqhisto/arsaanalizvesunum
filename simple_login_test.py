#!/usr/bin/env python3
"""
Basit login test
"""

import requests
import json

def test_login():
    try:
        url = 'http://localhost:5000/api/v1/auth/login'
        data = {
            'email': 'test@example.com',
            'password': '123456'
        }
        
        print(f"🔄 Testing: {url}")
        print(f"📤 Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📥 Status: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        print(f"📥 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login başarılı!")
            return True
        else:
            print("❌ Login başarısız!")
            return False
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    test_login()
