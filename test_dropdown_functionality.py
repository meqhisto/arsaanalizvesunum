#!/usr/bin/env python3
"""
Dropdown menüsü fonksiyonalitesini test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class DropdownTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="altanbariscomert@inovanettechs.com", password="123456"):
        """Kullanıcı girişi yap"""
        print("🔐 Kullanıcı girişi yapılıyor...")
        
        try:
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
        except Exception as e:
            print(f"❌ Login hatası: {str(e)}")
            return False
    
    def test_analysis_detail_page(self, analysis_id=1):
        """Analysis detail sayfasını test et"""
        print(f"📊 Analiz {analysis_id} detay sayfası test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Bootstrap kontrolü
                bootstrap_css = 'bootstrap@5.3.0/dist/css/bootstrap.min.css' in page_content
                bootstrap_js = 'bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js' in page_content
                
                # Dropdown HTML kontrolü
                dropdown_button = 'id="reportDropdown"' in page_content
                dropdown_toggle = 'data-bs-toggle="dropdown"' in page_content
                dropdown_menu = 'aria-labelledby="reportDropdown"' in page_content
                
                # Rapor butonları kontrolü
                word_button = 'generateWordReport' in page_content
                pdf_button = 'generatePDFReport' in page_content
                powerpoint_button = 'generatePowerPointReport' in page_content
                
                print("✅ Analiz detay sayfası başarıyla alındı")
                print(f"   Bootstrap CSS: {'✅' if bootstrap_css else '❌'}")
                print(f"   Bootstrap JS: {'✅' if bootstrap_js else '❌'}")
                print(f"   Dropdown Button ID: {'✅' if dropdown_button else '❌'}")
                print(f"   Dropdown Toggle: {'✅' if dropdown_toggle else '❌'}")
                print(f"   Dropdown Menu: {'✅' if dropdown_menu else '❌'}")
                print(f"   Word Button: {'✅' if word_button else '❌'}")
                print(f"   PDF Button: {'✅' if pdf_button else '❌'}")
                print(f"   PowerPoint Button: {'✅' if powerpoint_button else '❌'}")
                
                # Genel başarı kontrolü
                all_checks = [
                    bootstrap_css, bootstrap_js, dropdown_button, 
                    dropdown_toggle, dropdown_menu, word_button, 
                    pdf_button, powerpoint_button
                ]
                
                success_count = sum(all_checks)
                total_count = len(all_checks)
                
                print(f"   Toplam Kontrol: {success_count}/{total_count}")
                
                if success_count == total_count:
                    print("🎉 Tüm dropdown kontrolleri başarılı!")
                    return True
                else:
                    print("⚠️ Bazı dropdown kontrolleri başarısız.")
                    return False
            else:
                print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analiz detay sayfası hatası: {str(e)}")
            return False
    
    def test_report_endpoints(self, analysis_id=1):
        """Rapor endpoint'lerini test et"""
        print(f"📄 Rapor endpoint'leri test ediliyor (Analiz ID: {analysis_id})...")
        
        endpoints = [
            ("Word", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/word"),
            ("PDF", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/pdf"),
            ("PowerPoint", "POST", f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}")
        ]
        
        results = []
        
        for name, method, url in endpoints:
            try:
                print(f"   {name} endpoint test ediliyor...")
                
                if method == "GET":
                    response = self.session.get(url)
                else:  # POST
                    data = {
                        "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
                        "color_scheme": "blue"
                    }
                    response = self.session.post(url, data=data)
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    file_size = len(response.content)
                    
                    print(f"   ✅ {name}: {response.status_code} - {file_size} bytes")
                    results.append((name, True))
                else:
                    print(f"   ❌ {name}: {response.status_code}")
                    results.append((name, False))
                    
            except Exception as e:
                print(f"   ❌ {name}: Hata - {str(e)}")
                results.append((name, False))
        
        return results
    
    def run_comprehensive_test(self):
        """Kapsamlı dropdown ve rapor testi"""
        print("🚀 Dropdown Menüsü ve Rapor Sistemi Kapsamlı Testi")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Analysis detail sayfası kontrolü
        page_test_result = self.test_analysis_detail_page()
        
        # Rapor endpoint'leri kontrolü
        endpoint_results = self.test_report_endpoints()
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 DROPDOWN VE RAPOR TEST SONUÇLARI")
        print("=" * 60)
        
        print(f"\n🌐 Analysis Detail Sayfası: {'✅ BAŞARILI' if page_test_result else '❌ BAŞARISIZ'}")
        
        print(f"\n📄 Rapor Endpoint'leri:")
        endpoint_success = 0
        for name, result in endpoint_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                endpoint_success += 1
        
        total_tests = 1 + len(endpoint_results)  # Page test + endpoint tests
        total_success = (1 if page_test_result else 0) + endpoint_success
        
        print(f"\nToplam: {total_success}/{total_tests} test başarılı")
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if total_success == total_tests:
            print("🎉 Tüm dropdown ve rapor testleri başarılı!")
            print("\n✅ Dropdown menüsü artık çalışıyor olmalı!")
        else:
            print("⚠️ Bazı testler başarısız oldu.")
        
        print(f"\n🔧 Yapılan Düzeltmeler:")
        print(f"   ✅ Bootstrap JavaScript eklendi (dashboard_base.html)")
        print(f"   ✅ Dropdown HTML yapısı düzeltildi (analysis_detail.html)")
        print(f"   ✅ PowerPoint butonu eklendi")
        print(f"   ✅ make_response import'u eklendi")

def main():
    tester = DropdownTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
