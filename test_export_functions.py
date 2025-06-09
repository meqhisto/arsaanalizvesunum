#!/usr/bin/env python3
"""
Export fonksiyonlarını test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class ExportTester:
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
    
    def test_excel_export(self):
        """Excel export'u test et"""
        print("📊 Excel export test ediliyor...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/analysis/export/excel")
            end_time = time.time()
            
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                file_size = len(response.content)
                
                print(f"   Content-Type: {content_type}")
                print(f"   Dosya boyutu: {file_size} bytes")
                
                if 'spreadsheetml.sheet' in content_type:
                    print("✅ Excel export başarılı")
                    return True
                else:
                    print(f"⚠️ Excel export oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            else:
                print(f"❌ Excel export başarısız: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Excel export test hatası: {str(e)}")
            return False
    
    def test_pdf_export(self):
        """PDF export'u test et"""
        print("📄 PDF export test ediliyor...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/analysis/export/pdf")
            end_time = time.time()
            
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                file_size = len(response.content)
                
                print(f"   Content-Type: {content_type}")
                print(f"   Dosya boyutu: {file_size} bytes")
                
                if 'application/pdf' in content_type:
                    print("✅ PDF export başarılı")
                    return True
                else:
                    print(f"⚠️ PDF export oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            else:
                print(f"❌ PDF export başarısız: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ PDF export test hatası: {str(e)}")
            return False
    
    def run_export_tests(self):
        """Export testlerini çalıştır"""
        print("🚀 Export Fonksiyonları Testi")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 50)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Export testleri
        excel_result = self.test_excel_export()
        pdf_result = self.test_pdf_export()
        
        # Sonuçları özetle
        print("\n" + "=" * 50)
        print("📊 EXPORT TEST SONUÇLARI")
        print("=" * 50)
        
        print(f"Excel Export: {'✅ BAŞARILI' if excel_result else '❌ BAŞARISIZ'}")
        print(f"PDF Export: {'✅ BAŞARILI' if pdf_result else '❌ BAŞARISIZ'}")
        
        total_tests = 2
        passed_tests = sum([excel_result, pdf_result])
        
        print(f"\nToplam: {passed_tests}/{total_tests} test başarılı")
        success_rate = (passed_tests / total_tests) * 100
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 Tüm export testleri başarılı!")
        else:
            print("⚠️ Bazı export testleri başarısız oldu.")
        
        print(f"\n🔧 Yapılan Düzeltmeler:")
        print(f"   ✅ datetime import'u eklendi (Excel export)")
        print(f"   ✅ datetime import'u eklendi (PDF export)")

def main():
    tester = ExportTester()
    tester.run_export_tests()

if __name__ == "__main__":
    main()
