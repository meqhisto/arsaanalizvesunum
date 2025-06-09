#!/usr/bin/env python3
"""
PowerPoint sunum oluşturma özelliğini test eden script
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class PowerPointTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="altanbariscomert@inovanettechs.com", password="123456"):
        """Kullanıcı girişi yap"""
        print("🔐 Kullanıcı girişi yapılıyor...")
        
        # Önce login sayfasını al
        login_page = self.session.get(f"{BASE_URL}/auth/login")
        if login_page.status_code != 200:
            print(f"❌ Login sayfası alınamadı: {login_page.status_code}")
            return False
        
        # Login verilerini gönder
        login_data = {
            "email": email,
            "password": password
        }
        
        response = self.session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect = başarılı login
            print("✅ Başarıyla giriş yapıldı")
            self.logged_in = True
            return True
        else:
            print(f"❌ Giriş başarısız: {response.status_code}")
            return False
    
    def test_analysis_detail_page(self, analysis_id=1):
        """Analiz detay sayfasını kontrol et"""
        print(f"📊 Analiz {analysis_id} detay sayfası kontrol ediliyor...")
        response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
        
        if response.status_code == 200:
            print("✅ Analiz detay sayfası başarıyla alındı")
            # Sayfada sunum oluşturma butonu var mı kontrol et
            if "Sunum Oluştur" in response.text:
                print("✅ Sunum oluşturma butonu bulundu")
                return True
            else:
                print("⚠️ Sunum oluşturma butonu bulunamadı")
                return False
        else:
            print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
            return False
    
    def test_powerpoint_creation_direct(self, analysis_id=1):
        """PowerPoint oluşturmayı doğrudan test et"""
        print(f"🎯 PowerPoint oluşturma test ediliyor (Analiz ID: {analysis_id})...")
        
        # Sunum oluşturma POST isteği
        presentation_data = {
            "sections": "genel_bilgiler,analiz_sonuclari,swot_analizi",
            "color_scheme": "blue"
        }
        
        response = self.session.post(f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}",
                                   data=presentation_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type:
                print("✅ PowerPoint sunumu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️ Sunum oluşturuldu ama format beklenmedik: {content_type}")
                print(f"Response başlangıcı: {response.text[:200]}...")
                return False
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        elif response.status_code == 500:
            print(f"❌ Sunucu hatası: {response.status_code}")
            print(f"Hata detayı: {response.text[:500]}...")
            return False
        else:
            print(f"❌ PowerPoint oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def test_powerpoint_with_different_options(self, analysis_id=1):
        """Farklı seçeneklerle PowerPoint oluşturmayı test et"""
        print(f"🎨 Farklı seçeneklerle PowerPoint test ediliyor...")
        
        test_options = [
            {
                "name": "Minimal Seçenekler",
                "data": {
                    "sections": "genel_bilgiler",
                    "color_scheme": "blue"
                }
            },
            {
                "name": "Tüm Seçenekler",
                "data": {
                    "sections": "genel_bilgiler,analiz_sonuclari,swot_analizi,finansal_analiz,sonuc_oneriler",
                    "color_scheme": "green"
                }
            },
            {
                "name": "Farklı Renk Şeması",
                "data": {
                    "sections": "genel_bilgiler,analiz_sonuclari",
                    "color_scheme": "red"
                }
            }
        ]
        
        results = []
        for option in test_options:
            print(f"\n🔸 {option['name']} test ediliyor...")
            response = self.session.post(f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}",
                                       data=option['data'])
            
            success = response.status_code == 200
            results.append((option['name'], success))
            
            if success:
                print(f"✅ {option['name']} başarılı")
            else:
                print(f"❌ {option['name']} başarısız: {response.status_code}")
        
        return results
    
    def run_all_tests(self):
        """Tüm PowerPoint testlerini çalıştır"""
        print("🚀 PowerPoint Sunum Sistemi Test Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 50)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Test sırası
        tests = [
            ("Analiz Detay Sayfası", lambda: self.test_analysis_detail_page(1)),
            ("PowerPoint Oluşturma (Temel)", lambda: self.test_powerpoint_creation_direct(1)),
            ("PowerPoint Farklı Seçenekler", lambda: self.test_powerpoint_with_different_options(1)),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            print("-" * 30)
            try:
                result = test_func()
                if isinstance(result, list):  # Çoklu test sonucu
                    for sub_name, sub_result in result:
                        results.append((f"{test_name} - {sub_name}", sub_result))
                else:
                    results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test hatası: {str(e)}")
                results.append((test_name, False))
        
        # Sonuçları özetle
        print("\n" + "=" * 50)
        print("📊 POWERPOINT TEST SONUÇLARI")
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
            print("🎉 Tüm PowerPoint testleri başarılı!")
        else:
            print("⚠️ Bazı PowerPoint testleri başarısız oldu.")

def main():
    tester = PowerPointTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
