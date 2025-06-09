#!/usr/bin/env python3
"""
Basit rapor testi
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_simple_reports():
    """Basit rapor testleri"""
    print("🚀 Basit Rapor Testleri Başlıyor...")
    
    session = requests.Session()
    
    # Login
    print("🔐 Login yapılıyor...")
    login_data = {
        "email": "altanbariscomert@inovanettechs.com",
        "password": "123456"
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
    if login_response.status_code == 302:
        print("✅ Login başarılı")
    else:
        print("❌ Login başarısız")
        return
    
    # Test edilecek endpoint'ler
    tests = [
        ("Word (Yeni)", "GET", f"{BASE_URL}/analysis/1/report/word"),
        ("PDF (Yeni)", "GET", f"{BASE_URL}/analysis/1/report/pdf"),
        ("PowerPoint (Eski)", "POST", f"{BASE_URL}/analysis/report/generate_pptx/1"),
    ]
    
    results = []
    
    for test_name, method, url in tests:
        print(f"\n📄 {test_name} test ediliyor...")
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = session.get(url)
            else:  # POST
                data = {
                    "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
                    "color_scheme": "blue"
                }
                response = session.post(url, data=data)
            
            end_time = time.time()
            
            print(f"   Status Code: {response.status_code}")
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                file_size = len(response.content)
                print(f"   Content-Type: {content_type}")
                print(f"   Dosya boyutu: {file_size} bytes")
                
                # Format kontrolü
                if 'wordprocessingml.document' in content_type:
                    print("✅ Word raporu başarılı")
                    results.append((test_name, True))
                elif 'application/pdf' in content_type:
                    print("✅ PDF raporu başarılı")
                    results.append((test_name, True))
                elif 'presentationml.presentation' in content_type:
                    print("✅ PowerPoint raporu başarılı")
                    results.append((test_name, True))
                else:
                    print(f"⚠️ Beklenmedik format: {content_type}")
                    results.append((test_name, False))
            else:
                print(f"❌ Başarısız: {response.status_code}")
                results.append((test_name, False))
                
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print("\n" + "=" * 50)
    print("📊 BASIT RAPOR TEST SONUÇLARI")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"Başarı oranı: {success_rate:.1f}%")
    
    if passed == total:
        print("🎉 Tüm basit rapor testleri başarılı!")
    else:
        print("⚠️ Bazı basit rapor testleri başarısız oldu.")

if __name__ == "__main__":
    test_simple_reports()
