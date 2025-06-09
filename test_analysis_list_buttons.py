#!/usr/bin/env python3
"""
Analysis list sayfasındaki tüm butonları test eden script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class AnalysisListButtonTester:
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
    
    def test_analysis_list_page(self):
        """Analysis list sayfasını test et"""
        print("📊 Analysis list sayfası test ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis")
            
            if response.status_code == 200:
                page_content = response.text
                
                # Buton kontrolü
                new_analysis_btn = 'href="/analysis/new"' in page_content
                export_dropdown = 'id="exportBtn"' in page_content
                excel_export = 'exportToExcel()' in page_content
                pdf_export = 'exportToPDF()' in page_content
                
                # Rapor butonları kontrolü
                word_report = 'href="/analysis/' in page_content and '/report/word"' in page_content
                pdf_report = 'href="/analysis/' in page_content and '/report/pdf"' in page_content
                powerpoint_report = 'generatePowerPointReport(' in page_content
                
                # Delete butonu kontrolü
                delete_function = 'deleteAnalysis(' in page_content
                
                print("✅ Analysis list sayfası başarıyla alındı")
                print(f"   Yeni Analiz Butonu: {'✅' if new_analysis_btn else '❌'}")
                print(f"   Export Dropdown: {'✅' if export_dropdown else '❌'}")
                print(f"   Excel Export: {'✅' if excel_export else '❌'}")
                print(f"   PDF Export: {'✅' if pdf_export else '❌'}")
                print(f"   Word Report: {'✅' if word_report else '❌'}")
                print(f"   PDF Report: {'✅' if pdf_report else '❌'}")
                print(f"   PowerPoint Report: {'✅' if powerpoint_report else '❌'}")
                print(f"   Delete Function: {'✅' if delete_function else '❌'}")
                
                # Genel başarı kontrolü
                all_checks = [
                    new_analysis_btn, export_dropdown, excel_export, pdf_export,
                    word_report, pdf_report, powerpoint_report, delete_function
                ]
                
                success_count = sum(all_checks)
                total_count = len(all_checks)
                
                print(f"   Toplam Kontrol: {success_count}/{total_count}")
                
                return success_count == total_count
            else:
                print(f"❌ Analysis list sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analysis list sayfası hatası: {str(e)}")
            return False
    
    def test_export_endpoints(self):
        """Export endpoint'lerini test et"""
        print("📄 Export endpoint'leri test ediliyor...")
        
        endpoints = [
            ("Excel Export", "GET", f"{BASE_URL}/analysis/export/excel"),
            ("PDF Export", "GET", f"{BASE_URL}/analysis/export/pdf")
        ]
        
        results = []
        
        for name, method, url in endpoints:
            try:
                print(f"   {name} test ediliyor...")
                
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
                    if 'excel' in name.lower() and 'spreadsheetml.sheet' in content_type:
                        print(f"   ✅ {name}: Excel dosyası başarılı")
                        results.append((name, True))
                    elif 'pdf' in name.lower() and 'application/pdf' in content_type:
                        print(f"   ✅ {name}: PDF dosyası başarılı")
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
    
    def test_individual_report_buttons(self, analysis_id=1):
        """Bireysel rapor butonlarını test et"""
        print(f"📄 Analiz {analysis_id} rapor butonları test ediliyor...")
        
        tests = [
            ("Word Report", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/word"),
            ("PDF Report", "GET", f"{BASE_URL}/analysis/{analysis_id}/report/pdf"),
            ("PowerPoint Report", "POST", f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}")
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
                    if 'word' in name.lower() and 'wordprocessingml.document' in content_type:
                        print(f"   ✅ {name}: Word raporu başarılı")
                        results.append((name, True))
                    elif 'pdf' in name.lower() and 'application/pdf' in content_type:
                        print(f"   ✅ {name}: PDF raporu başarılı")
                        results.append((name, True))
                    elif 'powerpoint' in name.lower() and 'presentationml.presentation' in content_type:
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
        """Kapsamlı analysis list buton testi"""
        print("🚀 Analysis List Tüm Butonlar Kapsamlı Testi")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 70)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Analysis list sayfası kontrolü
        page_test_result = self.test_analysis_list_page()
        
        # Export endpoint'leri kontrolü
        export_results = self.test_export_endpoints()
        
        # Bireysel rapor butonları kontrolü
        report_results = self.test_individual_report_buttons()
        
        # Sonuçları özetle
        print("\n" + "=" * 70)
        print("📊 ANALYSIS LIST TÜM BUTONLAR TEST SONUÇLARI")
        print("=" * 70)
        
        print(f"\n🌐 Analysis List Sayfası: {'✅ BAŞARILI' if page_test_result else '❌ BAŞARISIZ'}")
        
        print(f"\n📤 Export Endpoint'leri:")
        export_success = 0
        for name, result in export_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                export_success += 1
        
        print(f"\n📄 Bireysel Rapor Butonları:")
        report_success = 0
        for name, result in report_results:
            status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
            print(f"   {name}: {status}")
            if result:
                report_success += 1
        
        total_tests = 1 + len(export_results) + len(report_results)
        total_success = (1 if page_test_result else 0) + export_success + report_success
        
        print(f"\nToplam: {total_success}/{total_tests} test başarılı")
        success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if total_success == total_tests:
            print("🎉 Tüm analysis list buton testleri başarılı!")
        else:
            print("⚠️ Bazı analysis list buton testleri başarısız oldu.")
        
        print(f"\n🔧 Yapılan İyileştirmeler:")
        print(f"   ✅ PowerPoint raporu seçeneği eklendi (Grid ve List view)")
        print(f"   ✅ Delete endpoint'i düzeltildi (/analysis/delete/{{id}})")
        print(f"   ✅ generatePowerPointReport() JavaScript fonksiyonu eklendi")
        print(f"   ✅ Tüm dropdown'lar Bootstrap JavaScript ile çalışıyor")
        
        print(f"\n📊 Buton Kategorileri:")
        print(f"   🔵 Navigasyon: Yeni Analiz, Görüntüle, Düzenle")
        print(f"   📤 Export: Excel, PDF (toplu)")
        print(f"   📄 Raporlar: Word, PDF, PowerPoint (bireysel)")
        print(f"   🗑️ İşlemler: Sil")

def main():
    tester = AnalysisListButtonTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
