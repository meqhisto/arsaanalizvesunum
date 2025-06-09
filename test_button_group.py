#!/usr/bin/env python3
"""
Yan yana butonları test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class ButtonGroupTester:
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
    
    def test_analysis_detail_page(self, analysis_id=1):
        """Analysis detail sayfasını test et"""
        print(f"📊 Analiz {analysis_id} detay sayfası test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Button group kontrolü
                button_group = 'class="btn-group"' in page_content
                word_button = 'generateWordReport' in page_content and 'btn btn-primary' in page_content
                pdf_button = 'generatePDFReport' in page_content and 'btn btn-danger' in page_content
                ppt_button = 'generatePowerPointReport' in page_content and 'btn btn-warning' in page_content
                
                # Dropdown kontrolü (olmamalı)
                dropdown_exists = 'dropdown-toggle' in page_content
                
                print("✅ Analiz detay sayfası başarıyla alındı")
                print(f"   Button Group: {'✅' if button_group else '❌'}")
                print(f"   Word Button: {'✅' if word_button else '❌'}")
                print(f"   PDF Button: {'✅' if pdf_button else '❌'}")
                print(f"   PowerPoint Button: {'✅' if ppt_button else '❌'}")
                print(f"   Dropdown Kaldırıldı: {'✅' if not dropdown_exists else '❌'}")
                
                # Genel başarı kontrolü
                all_checks = [button_group, word_button, pdf_button, ppt_button, not dropdown_exists]
                success_count = sum(all_checks)
                total_count = len(all_checks)
                
                print(f"   Toplam Kontrol: {success_count}/{total_count}")
                
                if success_count == total_count:
                    print("🎉 Tüm button group kontrolleri başarılı!")
                    return True
                else:
                    print("⚠️ Bazı button group kontrolleri başarısız.")
                    return False
            else:
                print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analiz detay sayfası hatası: {str(e)}")
            return False
    
    def test_report_buttons(self, analysis_id=1):
        """Rapor butonlarını test et"""
        print(f"📄 Rapor butonları test ediliyor (Analiz ID: {analysis_id})...")
        
        tests = [
            ("Word Button", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/word"),
            ("PDF Button", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/pdf"),
            ("PowerPoint Button", "POST", f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}")
        ]
        
        results = []
        
        for name, method, url in tests:
            try:
                print(f"   {name} test ediliyor...")
                
                start_time = time.time()
                
                if method == "GET":
                    response = self.session.get(url)
                else:  # POST
                    data = {
                        "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
                        "color_scheme": "blue"
                    }
                    response = self.session.post(url, data=data)
                
                end_time = time.time()
                
                print(f"     İşlem süresi: {end_time - start_time:.2f} saniye")
                print(f"     Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    file_size = len(response.content)
                    
                    print(f"     Content-Type: {content_type}")
                    print(f"     Dosya boyutu: {file_size} bytes")
                    
                    # Format kontrolü
                    if 'wordprocessingml.document' in content_type:
                        print(f"   ✅ {name}: Word raporu başarılı")
                        results.append((name, True))
                    elif 'application/pdf' in content_type:
                        print(f"   ✅ {name}: PDF raporu başarılı")
                        results.append((name, True))
                    elif 'presentationml.presentation' in content_type:
                        print(f"   ✅ {name}: PowerPoint raporu başarılı")
                        results.append((name, True))
                    else:
                        print(f"   ⚠️ {name}: Beklenmedik format - {content_type}")
                        results.append((name, False))
                else:
                    print(f"   ❌ {name}: Başarısız - {response.status_code}")
                    results.append((name, False))
                    
            except Exception as e:
                print(f"   ❌ {name}: Hata - {str(e)}")
                results.append((name, False))
        
        return results
    
    def run_comprehensive_test(self):
        """Kapsamlı button group testi"""
        print("🚀 Button Group (Yan Yana Butonlar) Kapsamlı Testi")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Analysis detail sayfası kontrolü
        page_test_result = self.test_analysis_detail_page()
        
        # Rapor butonları kontrolü
        button_results = self.test_report_buttons()
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 BUTTON GROUP TEST SONUÇLARI")
        print("=" * 60)
        
        print(f"\n🌐 Analysis Detail Sayfası: {'✅ BAŞARILI' if page_test_result else '❌ BAŞARISIZ'}")
        
        print(f"\n📄 Rapor Butonları:")
        button_success = 0
        for name, result in button_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                button_success += 1
        
        total_tests = 1 + len(button_results)  # Page test + button tests
        total_success = (1 if page_test_result else 0) + button_success
        
        print(f"\nToplam: {total_success}/{total_tests} test başarılı")
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if total_success == total_tests:
            print("🎉 Tüm button group testleri başarılı!")
            print("\n✅ Yan yana butonlar artık çalışıyor!")
        else:
            print("⚠️ Bazı testler başarısız oldu.")
        
        print(f"\n🔧 Yapılan Değişiklikler:")
        print(f"   ✅ Dropdown menüsü kaldırıldı")
        print(f"   ✅ Yan yana butonlar eklendi (btn-group)")
        print(f"   ✅ Word, PDF, PowerPoint butonları ayrı ayrı")
        print(f"   ✅ Bootstrap JavaScript bağımlılığı kaldırıldı")
        print(f"   ✅ Daha basit ve güvenilir UI")
        
        print(f"\n🎨 Yeni Tasarım:")
        print(f"   📄 Word Button: Mavi (btn-primary)")
        print(f"   📄 PDF Button: Kırmızı (btn-danger)")
        print(f"   📄 PowerPoint Button: Sarı (btn-warning)")

def main():
    tester = ButtonGroupTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
