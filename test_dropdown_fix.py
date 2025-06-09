#!/usr/bin/env python3
"""
Dropdown düzeltmelerini test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class DropdownFixTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="altanbariscomert@inovanettechs.com", password="123456"):
        """Kullanıcı girişi yap"""
        print("🔐 Kullanıcı girişi yapılıyor...")
        
        try:
            login_data = {
                "email": email,
                "password": password
            }
            
            response = self.session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=False)
            
            if response.status_code == 302:
                print("✅ Başarıyla giriş yapıldı")
                self.logged_in = True
                return True
            else:
                print(f"❌ Giriş başarısız: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login hatası: {str(e)}")
            return False
    
    def test_dropdown_html_structure(self):
        """Dropdown HTML yapısını test et"""
        print("📊 Dropdown HTML yapısı test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/list")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Bootstrap dropdown attribute'larını kontrol et
                checks = {
                    "Export Dropdown ID": 'id="exportBtn"' in page_content,
                    "Export Dropdown aria-expanded": 'aria-expanded="false"' in page_content,
                    "Export Dropdown aria-labelledby": 'aria-labelledby="exportBtn"' in page_content,
                    "Action Dropdown ID Pattern": 'id="actionDropdown' in page_content,
                    "Report Dropdown ID Pattern": 'id="reportDropdown' in page_content,
                    "Bootstrap JavaScript": 'bootstrap.bundle.min.js' in page_content,
                    "Dropdown Toggle Class": 'dropdown-toggle' in page_content,
                    "Data BS Toggle": 'data-bs-toggle="dropdown"' in page_content
                }
                
                print("✅ Analysis list sayfası başarıyla alındı")
                
                passed_checks = 0
                total_checks = len(checks)
                
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"   {check_name}: {status}")
                    if result:
                        passed_checks += 1
                
                print(f"   Toplam Kontrol: {passed_checks}/{total_checks}")
                
                if passed_checks == total_checks:
                    print("🎉 Tüm dropdown HTML kontrolleri başarılı!")
                    return True
                else:
                    print("⚠️ Bazı dropdown HTML kontrolleri başarısız.")
                    return False
            else:
                print(f"❌ Analysis list sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Dropdown HTML test hatası: {str(e)}")
            return False
    
    def test_export_dropdown_functions(self):
        """Export dropdown fonksiyonlarını test et"""
        print("📤 Export dropdown fonksiyonları test ediliyor...")
        
        tests = [
            ("Excel Export", f"{BASE_URL}/analysis/export/excel"),
            ("PDF Export", f"{BASE_URL}/analysis/export/pdf")
        ]
        
        results = []
        
        for test_name, url in tests:
            try:
                print(f"   {test_name} test ediliyor...")
                
                start_time = time.time()
                response = self.session.get(url)
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    file_size = len(response.content)
                    
                    print(f"     Content-Type: {content_type}")
                    print(f"     Dosya boyutu: {file_size} bytes")
                    
                    # Format kontrolü
                    if 'excel' in test_name.lower() and 'spreadsheetml.sheet' in content_type:
                        print(f"   ✅ {test_name}: Excel dosyası başarılı")
                        results.append((test_name, True))
                    elif 'pdf' in test_name.lower() and 'application/pdf' in content_type:
                        print(f"   ✅ {test_name}: PDF dosyası başarılı")
                        results.append((test_name, True))
                    else:
                        print(f"   ⚠️ {test_name}: Beklenmedik format - {content_type}")
                        results.append((test_name, False))
                else:
                    print(f"   ❌ {test_name}: Başarısız - {response.status_code}")
                    results.append((test_name, False))
                    
            except Exception as e:
                print(f"   ❌ {test_name}: Hata - {str(e)}")
                results.append((test_name, False))
        
        return results
    
    def test_report_dropdown_functions(self, analysis_id=1):
        """Rapor dropdown fonksiyonlarını test et"""
        print(f"📄 Analiz {analysis_id} rapor dropdown fonksiyonları test ediliyor...")
        
        tests = [
            ("Word Report", f"{BASE_URL}/analysis/{analysis_id}/report/word"),
            ("PDF Report", f"{BASE_URL}/analysis/{analysis_id}/report/pdf")
        ]
        
        results = []
        
        for test_name, url in tests:
            try:
                print(f"   {test_name} test ediliyor...")
                
                start_time = time.time()
                response = self.session.get(url)
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    file_size = len(response.content)
                    
                    print(f"     Content-Type: {content_type}")
                    print(f"     Dosya boyutu: {file_size} bytes")
                    
                    # Format kontrolü
                    if 'word' in test_name.lower() and 'wordprocessingml.document' in content_type:
                        print(f"   ✅ {test_name}: Word raporu başarılı")
                        results.append((test_name, True))
                    elif 'pdf' in test_name.lower() and 'application/pdf' in content_type:
                        print(f"   ✅ {test_name}: PDF raporu başarılı")
                        results.append((test_name, True))
                    else:
                        print(f"   ⚠️ {test_name}: Beklenmedik format - {content_type}")
                        results.append((test_name, False))
                else:
                    print(f"   ❌ {test_name}: Başarısız - {response.status_code}")
                    results.append((test_name, False))
                    
            except Exception as e:
                print(f"   ❌ {test_name}: Hata - {str(e)}")
                results.append((test_name, False))
        
        return results
    
    def run_dropdown_fix_tests(self):
        """Dropdown düzeltme testlerini çalıştır"""
        print("🚀 Dropdown Düzeltme Testleri")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # HTML yapısı kontrolü
        html_test_result = self.test_dropdown_html_structure()
        
        # Export dropdown testleri
        export_results = self.test_export_dropdown_functions()
        
        # Rapor dropdown testleri
        report_results = self.test_report_dropdown_functions()
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 DROPDOWN DÜZELTMESİ TEST SONUÇLARI")
        print("=" * 60)
        
        print(f"\n🌐 HTML Yapısı: {'✅ BAŞARILI' if html_test_result else '❌ BAŞARISIZ'}")
        
        print(f"\n📤 Export Dropdown:")
        export_success = 0
        for name, result in export_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                export_success += 1
        
        print(f"\n📄 Rapor Dropdown:")
        report_success = 0
        for name, result in report_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                report_success += 1
        
        total_tests = 1 + len(export_results) + len(report_results)
        total_success = (1 if html_test_result else 0) + export_success + report_success
        
        print(f"\nToplam: {total_success}/{total_tests} test başarılı")
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if total_success == total_tests:
            print("🎉 Tüm dropdown düzeltme testleri başarılı!")
            print("\n✅ Dropdown'lar artık çalışıyor olmalı!")
        else:
            print("⚠️ Bazı dropdown testleri başarısız oldu.")
        
        print(f"\n🔧 Yapılan Düzeltmeler:")
        print(f"   ✅ Export dropdown: id, aria-expanded, aria-labelledby eklendi")
        print(f"   ✅ Action dropdown: id, aria-expanded, aria-labelledby eklendi")
        print(f"   ✅ Report dropdown: id, aria-expanded, aria-labelledby eklendi")
        print(f"   ✅ Bootstrap JavaScript zaten mevcut")
        print(f"   ✅ Unique ID'ler: analysis.id ile dinamik ID'ler")

def main():
    tester = DropdownFixTester()
    tester.run_dropdown_fix_tests()

if __name__ == "__main__":
    main()
