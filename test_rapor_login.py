#!/usr/bin/env python3
"""
Login yaparak analiz rapor sistemini test eden script
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class RaporTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="altanbariscomert@inovanettechs.com", password="123456"):
        """Kullanıcı girişi yap"""
        print("🔐 Kullanıcı girişi yapılıyor...")
        
        # Önce login sayfasını al (CSRF token için)
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
            print(f"Response: {response.text[:200]}...")
            return False
    
    def test_analysis_list(self):
        """Analiz listesini test et"""
        print("📋 Analiz listesi test ediliyor...")
        response = self.session.get(f"{BASE_URL}/analysis/list")
        
        if response.status_code == 200:
            print("✅ Analiz listesi başarıyla alındı")
            return True
        else:
            print(f"❌ Analiz listesi alınamadı: {response.status_code}")
            return False
    
    def test_analysis_detail(self, analysis_id=1):
        """Analiz detayını test et"""
        print(f"📊 Analiz {analysis_id} detayı test ediliyor...")
        response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
        
        if response.status_code == 200:
            print("✅ Analiz detayı başarıyla alındı")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ Analiz detayı alınamadı: {response.status_code}")
            return False
    
    def test_word_report(self, analysis_id=1):
        """Word raporu oluşturmayı test et"""
        print(f"📄 Word raporu test ediliyor (Analiz ID: {analysis_id})...")
        response = self.session.get(f"{BASE_URL}/analysis/report/generate/word/{analysis_id}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print("✅ Word raporu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️ Word raporu oluşturuldu ama format beklenmedik: {content_type}")
                return False
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ Word raporu oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def test_pdf_report(self, analysis_id=1):
        """PDF raporu oluşturmayı test et"""
        print(f"📄 PDF raporu test ediliyor (Analiz ID: {analysis_id})...")
        response = self.session.get(f"{BASE_URL}/analysis/report/generate/pdf/{analysis_id}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                print("✅ PDF raporu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️ PDF raporu oluşturuldu ama format beklenmedik: {content_type}")
                return False
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ PDF raporu oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def test_presentation_form(self, analysis_id=1):
        """Sunum oluşturma formunu test et"""
        print(f"🎯 Sunum oluşturma formu test ediliyor (Analiz ID: {analysis_id})...")
        
        # Önce analiz detay sayfasını al
        response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
        if response.status_code != 200:
            print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
            return False
        
        # Sunum oluşturma POST isteği
        presentation_data = {
            "sections": ["genel_bilgiler", "analiz_sonuclari", "swot_analizi"],
            "color_scheme": "blue"
        }
        
        response = self.session.post(f"{BASE_URL}/analysis/create_presentation/{analysis_id}", 
                                   data=presentation_data)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type:
                print("✅ PowerPoint sunumu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                return True
            else:
                print(f"⚠️ Sunum oluşturuldu ama format beklenmedik: {content_type}")
                return False
        elif response.status_code == 404:
            print(f"⚠️ Analiz {analysis_id} bulunamadı")
            return False
        else:
            print(f"❌ Sunum oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def run_all_tests(self):
        """Tüm testleri çalıştır"""
        print("🚀 Analiz Rapor Sistemi Test Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 50)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Test sırası
        tests = [
            ("Analiz Listesi", self.test_analysis_list),
            ("Analiz Detayı (ID: 1)", lambda: self.test_analysis_detail(1)),
            ("Word Raporu (ID: 1)", lambda: self.test_word_report(1)),
            ("PDF Raporu (ID: 1)", lambda: self.test_pdf_report(1)),
            ("PowerPoint Sunumu (ID: 1)", lambda: self.test_presentation_form(1)),
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

def main():
    tester = RaporTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
