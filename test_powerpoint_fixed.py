#!/usr/bin/env python3
"""
Düzeltilmiş PowerPoint rapor oluşturmayı test eden script
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class PowerPointFixedTester:
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
    
    def test_powerpoint_report(self, analysis_id=1):
        """PowerPoint raporu oluşturmayı test et"""
        print(f"🎯 PowerPoint raporu test ediliyor (Analiz ID: {analysis_id})...")
        
        # PowerPoint için POST verisi
        pptx_data = {
            "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
            "color_scheme": "blue"
        }
        
        start_time = time.time()
        response = self.session.post(f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}", 
                                   data=pptx_data)
        end_time = time.time()
        
        print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type:
                print("✅ PowerPoint raporu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                
                # Dosyayı kaydet (test için)
                filename = f"test_pptx_fixed_{analysis_id}_{int(time.time())}.pptx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   Test dosyası kaydedildi: {filename}")
                return True
            else:
                print(f"⚠️ PowerPoint raporu oluşturuldu ama format beklenmedik: {content_type}")
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
            print(f"❌ PowerPoint raporu oluşturulamadı: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def test_multiple_powerpoint_reports(self):
        """Birden fazla analiz için PowerPoint raporu test et"""
        print("🔄 Birden fazla analiz için PowerPoint testi...")
        
        analysis_ids = [1, 2, 3]  # Test edilecek analiz ID'leri
        results = []
        
        for analysis_id in analysis_ids:
            print(f"\n📊 Analiz {analysis_id} için PowerPoint testi:")
            result = self.test_powerpoint_report(analysis_id)
            results.append((f"PowerPoint-{analysis_id}", result))
        
        return results
    
    def test_different_color_schemes(self, analysis_id=1):
        """Farklı renk şemaları ile PowerPoint test et"""
        print(f"🎨 Farklı renk şemaları ile PowerPoint test ediliyor...")
        
        color_schemes = ["blue", "green", "red", "orange"]
        results = []
        
        for color in color_schemes:
            print(f"\n🔸 {color.upper()} renk şeması test ediliyor...")
            
            pptx_data = {
                "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
                "color_scheme": color
            }
            
            response = self.session.post(f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}", 
                                       data=pptx_data)
            
            success = response.status_code == 200
            results.append((f"PowerPoint-{color}", success))
            
            if success:
                print(f"✅ {color.upper()} renk şeması başarılı")
                # Dosyayı kaydet
                filename = f"test_pptx_{color}_{analysis_id}_{int(time.time())}.pptx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   Test dosyası kaydedildi: {filename}")
            else:
                print(f"❌ {color.upper()} renk şeması başarısız: {response.status_code}")
        
        return results
    
    def run_all_tests(self):
        """Tüm PowerPoint testlerini çalıştır"""
        print("🚀 Düzeltilmiş PowerPoint Rapor Sistemi Test Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Test sırası
        tests = [
            ("PowerPoint Raporu (ID: 1)", lambda: self.test_powerpoint_report(1)),
            ("Çoklu Analiz PowerPoint Testleri", self.test_multiple_powerpoint_reports),
            ("Farklı Renk Şemaları", lambda: self.test_different_color_schemes(1)),
        ]
        
        all_results = []
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            print("-" * 40)
            try:
                result = test_func()
                if isinstance(result, list):  # Çoklu test sonucu
                    all_results.extend(result)
                else:
                    all_results.append((test_name, result))
            except Exception as e:
                print(f"❌ Test hatası: {str(e)}")
                all_results.append((test_name, False))
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 DÜZELTILMIŞ POWERPOINT TEST SONUÇLARI")
        print("=" * 60)
        
        passed = 0
        total = len(all_results)
        
        for test_name, result in all_results:
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
    tester = PowerPointFixedTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
