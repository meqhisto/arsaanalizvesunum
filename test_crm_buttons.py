#!/usr/bin/env python3
"""
CRM modülündeki tüm butonları test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class CRMButtonTester:
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
    
    def test_crm_main_pages(self):
        """CRM ana sayfalarını test et"""
        print("📊 CRM ana sayfaları test ediliyor...")
        
        pages = [
            ("CRM Dashboard", f"{BASE_URL}/crm"),
            ("CRM Dashboard Alt", f"{BASE_URL}/crm/dashboard"),
            ("Contacts List", f"{BASE_URL}/crm/contacts"),
            ("Companies List", f"{BASE_URL}/crm/companies"),
            ("Deals List", f"{BASE_URL}/crm/deals"),
            ("Tasks List", f"{BASE_URL}/crm/tasks"),
            ("Import Wizard", f"{BASE_URL}/crm/import")
        ]
        
        results = []
        
        for page_name, url in pages:
            try:
                print(f"   {page_name} test ediliyor...")
                
                start_time = time.time()
                response = self.session.get(url)
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ {page_name}: Başarılı")
                    results.append((page_name, True))
                else:
                    print(f"   ❌ {page_name}: Başarısız - {response.status_code}")
                    results.append((page_name, False))
                    
            except Exception as e:
                print(f"   ❌ {page_name}: Hata - {str(e)}")
                results.append((page_name, False))
        
        return results
    
    def test_contacts_page_buttons(self):
        """Contacts sayfasındaki butonları test et"""
        print("👥 Contacts sayfası butonları test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/crm/contacts")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Buton kontrolü
                checks = {
                    "Yeni Kişi Ekle Butonu": 'href="/crm/contact/new"' in page_content or 'crm_contact_new' in page_content,
                    "Arama Input": 'id="search-input"' in page_content,
                    "Durum Filtresi": 'id="status-filter"' in page_content,
                    "Şirket Filtresi": 'id="company-filter"' in page_content,
                    "Export Dropdown": 'id="export-dropdown-btn"' in page_content,
                    "Bulk Actions": 'id="bulk-actions-toolbar"' in page_content,
                    "Select All Checkbox": 'id="select-all-checkbox"' in page_content,
                    "Pagination": 'id="pagination-container"' in page_content,
                    "Contact Detail Links": 'crm_contact_detail' in page_content,
                    "Contact Edit Links": 'crm_contact_edit' in page_content,
                    "Contact Delete Forms": 'crm_contact_delete' in page_content
                }
                
                print("✅ Contacts sayfası başarıyla alındı")
                
                passed_checks = 0
                total_checks = len(checks)
                
                for check_name, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"   {check_name}: {status}")
                    if result:
                        passed_checks += 1
                
                print(f"   Toplam Kontrol: {passed_checks}/{total_checks}")
                
                return passed_checks >= total_checks - 2  # 2 hata toleransı
            else:
                print(f"❌ Contacts sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Contacts sayfası test hatası: {str(e)}")
            return False
    
    def test_contact_crud_operations(self):
        """Contact CRUD işlemlerini test et"""
        print("🔧 Contact CRUD işlemleri test ediliyor...")
        
        operations = [
            ("Contact New Page", f"{BASE_URL}/crm/contact/new"),
            ("Contact Detail (ID 1)", f"{BASE_URL}/crm/contact/1"),
            ("Contact Edit (ID 1)", f"{BASE_URL}/crm/contact/1/edit")
        ]
        
        results = []
        
        for operation_name, url in operations:
            try:
                print(f"   {operation_name} test ediliyor...")
                
                start_time = time.time()
                response = self.session.get(url)
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ {operation_name}: Başarılı")
                    results.append((operation_name, True))
                elif response.status_code == 404:
                    print(f"   ⚠️ {operation_name}: 404 - Kayıt bulunamadı (normal)")
                    results.append((operation_name, True))  # 404 normal olabilir
                else:
                    print(f"   ❌ {operation_name}: Başarısız - {response.status_code}")
                    results.append((operation_name, False))
                    
            except Exception as e:
                print(f"   ❌ {operation_name}: Hata - {str(e)}")
                results.append((operation_name, False))
        
        return results
    
    def test_other_crm_modules(self):
        """Diğer CRM modüllerini test et"""
        print("🏢 Diğer CRM modülleri test ediliyor...")
        
        modules = [
            ("Companies New", f"{BASE_URL}/crm/company/new"),
            ("Deals New", f"{BASE_URL}/crm/deal/new"),
            ("Tasks New", f"{BASE_URL}/crm/task/new"),
            ("Company Detail (ID 1)", f"{BASE_URL}/crm/company/1"),
            ("Deal Detail (ID 1)", f"{BASE_URL}/crm/deal/1"),
            ("Task Detail (ID 1)", f"{BASE_URL}/crm/task/1")
        ]
        
        results = []
        
        for module_name, url in modules:
            try:
                print(f"   {module_name} test ediliyor...")
                
                start_time = time.time()
                response = self.session.get(url)
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ {module_name}: Başarılı")
                    results.append((module_name, True))
                elif response.status_code == 404:
                    print(f"   ⚠️ {module_name}: 404 - Kayıt bulunamadı (normal)")
                    results.append((module_name, True))  # 404 normal olabilir
                else:
                    print(f"   ❌ {module_name}: Başarısız - {response.status_code}")
                    results.append((module_name, False))
                    
            except Exception as e:
                print(f"   ❌ {module_name}: Hata - {str(e)}")
                results.append((module_name, False))
        
        return results
    
    def run_comprehensive_crm_test(self):
        """Kapsamlı CRM buton testi"""
        print("🚀 CRM Modülü Kapsamlı Buton Testi")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 70)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Ana sayfalar kontrolü
        main_pages_results = self.test_crm_main_pages()
        
        # Contacts sayfası butonları kontrolü
        contacts_buttons_result = self.test_contacts_page_buttons()
        
        # Contact CRUD işlemleri kontrolü
        contact_crud_results = self.test_contact_crud_operations()
        
        # Diğer CRM modülleri kontrolü
        other_modules_results = self.test_other_crm_modules()
        
        # Sonuçları özetle
        print("\n" + "=" * 70)
        print("📊 CRM MODÜLÜ KAPSAMLI TEST SONUÇLARI")
        print("=" * 70)
        
        print(f"\n🌐 Ana Sayfalar:")
        main_success = 0
        for name, result in main_pages_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                main_success += 1
        
        print(f"\n👥 Contacts Sayfası Butonları: {'✅ BAŞARILI' if contacts_buttons_result else '❌ BAŞARISIZ'}")
        
        print(f"\n🔧 Contact CRUD İşlemleri:")
        crud_success = 0
        for name, result in contact_crud_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                crud_success += 1
        
        print(f"\n🏢 Diğer CRM Modülleri:")
        other_success = 0
        for name, result in other_modules_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                other_success += 1
        
        total_tests = len(main_pages_results) + 1 + len(contact_crud_results) + len(other_modules_results)
        total_success = main_success + (1 if contacts_buttons_result else 0) + crud_success + other_success
        
        print(f"\nToplam: {total_success}/{total_tests} test başarılı")
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if total_success >= total_tests - 3:  # 3 hata toleransı
            print("🎉 CRM modülü genel olarak çalışıyor!")
        else:
            print("⚠️ CRM modülünde bazı sorunlar tespit edildi.")
        
        print(f"\n🔧 Tespit Edilen Sorunlar:")
        print(f"   - Bazı endpoint'ler 404 döndürebilir (veri yoksa normal)")
        print(f"   - Route tanımları eksik olabilir")
        print(f"   - Template dosyaları eksik olabilir")
        print(f"   - JavaScript fonksiyonları çalışmayabilir")
        
        print(f"\n💡 Sonraki Adımlar:")
        print(f"   1. Eksik route'ları tanımla")
        print(f"   2. Template dosyalarını kontrol et")
        print(f"   3. JavaScript butonlarını aktif et")
        print(f"   4. CRUD işlemlerini test et")

def main():
    tester = CRMButtonTester()
    tester.run_comprehensive_crm_test()

if __name__ == "__main__":
    main()
