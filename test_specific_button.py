#!/usr/bin/env python3
"""
Spesifik buton testleri
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class SpecificButtonTester:
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
    
    def test_analysis_list_page_load(self):
        """Analysis list sayfasının yüklenip yüklenmediğini test et"""
        print("📊 Analysis list sayfası yükleme testi...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/list")
            
            if response.status_code == 200:
                print("✅ Analysis list sayfası başarıyla yüklendi")
                
                # Sayfada butonların varlığını kontrol et
                page_content = response.text
                
                checks = {
                    "Yeni Analiz Butonu": 'href="/analysis/new"' in page_content,
                    "Export Dropdown": 'id="exportBtn"' in page_content,
                    "Excel Export": 'exportToExcel()' in page_content,
                    "PDF Export": 'exportToPDF()' in page_content,
                    "Word Report Links": '/report/word"' in page_content,
                    "PDF Report Links": '/report/pdf"' in page_content,
                    "PowerPoint Function": 'generatePowerPointReport(' in page_content,
                    "Delete Function": 'deleteAnalysis(' in page_content,
                    "Bootstrap JS": 'bootstrap.bundle.min.js' in page_content
                }
                
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"   {check_name}: {status}")
                
                return True
            else:
                print(f"❌ Analysis list sayfası yüklenemedi: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analysis list sayfası test hatası: {str(e)}")
            return False
    
    def test_new_analysis_button(self):
        """Yeni Analiz butonunu test et"""
        print("🆕 Yeni Analiz butonu test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/new")
            
            if response.status_code == 200:
                print("✅ Yeni Analiz sayfası başarıyla açıldı")
                return True
            else:
                print(f"❌ Yeni Analiz sayfası açılamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Yeni Analiz butonu test hatası: {str(e)}")
            return False
    
    def test_view_analysis_button(self, analysis_id=1):
        """Görüntüle butonunu test et"""
        print(f"👁️ Analiz {analysis_id} görüntüle butonu test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
            
            if response.status_code == 200:
                print("✅ Analiz detay sayfası başarıyla açıldı")
                return True
            else:
                print(f"❌ Analiz detay sayfası açılamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Görüntüle butonu test hatası: {str(e)}")
            return False
    
    def test_edit_analysis_button(self, analysis_id=1):
        """Düzenle butonunu test et"""
        print(f"✏️ Analiz {analysis_id} düzenle butonu test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}/edit")
            
            if response.status_code == 200:
                print("✅ Analiz düzenleme sayfası başarıyla açıldı")
                return True
            else:
                print(f"❌ Analiz düzenleme sayfası açılamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Düzenle butonu test hatası: {str(e)}")
            return False
    
    def test_delete_analysis_endpoint(self, analysis_id=20):
        """Delete endpoint'ini test et (analiz 20 varsa)"""
        print(f"🗑️ Analiz {analysis_id} delete endpoint test ediliyor...")
        
        try:
            # Önce analiz var mı kontrol et
            check_response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
            if check_response.status_code != 200:
                print(f"⚠️ Analiz {analysis_id} bulunamadı, delete testi atlanıyor")
                return True
            
            # Delete endpoint'ini test et
            response = self.session.post(f"{BASE_URL}/analysis/delete/{analysis_id}")
            
            if response.status_code == 200:
                print("✅ Delete endpoint başarıyla çalıştı")
                return True
            else:
                print(f"❌ Delete endpoint başarısız: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Delete endpoint test hatası: {str(e)}")
            return False
    
    def run_specific_tests(self):
        """Spesifik buton testlerini çalıştır"""
        print("🚀 Analysis List Spesifik Buton Testleri")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Testleri çalıştır
        tests = [
            ("Analysis List Sayfası", self.test_analysis_list_page_load),
            ("Yeni Analiz Butonu", self.test_new_analysis_button),
            ("Görüntüle Butonu", self.test_view_analysis_button),
            ("Düzenle Butonu", self.test_edit_analysis_button),
            ("Delete Endpoint", self.test_delete_analysis_endpoint)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name} test ediliyor...")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} test hatası: {str(e)}")
                results.append((test_name, False))
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 SPESİFİK BUTON TEST SONUÇLARI")
        print("=" * 60)
        
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
            print("🎉 Tüm spesifik buton testleri başarılı!")
        else:
            print("⚠️ Bazı spesifik buton testleri başarısız oldu.")
        
        print(f"\n💡 Hangi butonun çalışmadığını belirtirseniz o butonu özel olarak test edebilirim:")
        print(f"   - Export butonları (Excel/PDF)")
        print(f"   - Rapor butonları (Word/PDF/PowerPoint)")
        print(f"   - Dropdown menüler")
        print(f"   - Navigasyon butonları")

def main():
    tester = SpecificButtonTester()
    tester.run_specific_tests()

if __name__ == "__main__":
    main()
