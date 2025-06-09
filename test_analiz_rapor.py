#!/usr/bin/env python3
"""
Analiz rapor sistemini test eden script
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def test_analysis_list():
    """Mevcut analizleri listele"""
    print("📋 Mevcut analizleri kontrol ediliyor...")
    try:
        response = requests.get(f"{BASE_URL}/analysis/list")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Analiz listesi başarıyla alındı")
            # HTML response olabilir, bu yüzden sadece status'u kontrol edelim
            return True
        else:
            print(f"❌ Analiz listesi alınamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

def test_analysis_detail(analysis_id=1):
    """Belirli bir analizin detayını kontrol et"""
    print(f"📊 Analiz {analysis_id} detayı kontrol ediliyor...")
    try:
        response = requests.get(f"{BASE_URL}/analysis/{analysis_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Analiz detayı başarıyla alındı")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ Analiz detayı alınamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

def test_report_generation(analysis_id=1, format_type='word'):
    """Rapor oluşturma endpoint'ini test et"""
    print(f"📄 {format_type.upper()} raporu oluşturma testi (Analiz ID: {analysis_id})...")
    try:
        response = requests.get(f"{BASE_URL}/analysis/report/generate/{format_type}/{analysis_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ {format_type.upper()} raporu başarıyla oluşturuldu")
            # Content-Type kontrolü
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            if format_type == 'word' and 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print("✅ Word dosyası doğru format")
            elif format_type == 'pdf' and 'application/pdf' in content_type:
                print("✅ PDF dosyası doğru format")
            
            return True
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ Rapor oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

def test_api_health():
    """API sağlık kontrolü"""
    print("🏥 API sağlık kontrolü...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API sağlıklı")
            print(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ API sağlık kontrolü başarısız: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 Analiz Rapor Sistemi Test Başlıyor...")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Zamanı: {datetime.now()}")
    print("=" * 50)
    
    # Test sırası
    tests = [
        ("API Sağlık Kontrolü", test_api_health),
        ("Analiz Listesi", test_analysis_list),
        ("Analiz Detayı (ID: 1)", lambda: test_analysis_detail(1)),
        ("Word Raporu (ID: 1)", lambda: test_report_generation(1, 'word')),
        ("PDF Raporu (ID: 1)", lambda: test_report_generation(1, 'pdf')),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test hatası: {str(e)}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print("\n" + "=" * 50)
    print("📊 TEST SONUÇLARI")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı!")
    else:
        print("⚠️ Bazı testler başarısız oldu.")

if __name__ == "__main__":
    main()
