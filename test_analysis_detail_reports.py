#!/usr/bin/env python3
"""
Analysis detail sayfasında rapor oluşturma özelliklerini test eden script
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class AnalysisDetailReportTester:
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
        """Analysis detail sayfasını kontrol et"""
        print(f"📊 Analiz {analysis_id} detay sayfası kontrol ediliyor...")
        response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
        
        if response.status_code == 200:
            print("✅ Analiz detay sayfası başarıyla alındı")
            
            # Sayfada rapor butonları var mı kontrol et
            page_content = response.text
            
            # Word raporu butonu
            if "Word Raporu İndir" in page_content:
                print("✅ Word raporu butonu bulundu")
            else:
                print("⚠️ Word raporu butonu bulunamadı")
            
            # PDF raporu butonu
            if "PDF Raporu İndir" in page_content:
                print("✅ PDF raporu butonu bulundu")
            else:
                print("⚠️ PDF raporu butonu bulunamadı")
            
            # PowerPoint raporu butonu (eğer varsa)
            if "PowerPoint" in page_content or "Sunum" in page_content:
                print("✅ PowerPoint/Sunum butonu bulundu")
            else:
                print("⚠️ PowerPoint/Sunum butonu bulunamadı")
            
            return True
        else:
            print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
            return False
    
    def test_word_report_from_detail(self, analysis_id=1):
        """Analysis detail sayfasından Word raporu oluştur"""
        print(f"📄 Word raporu test ediliyor (Analiz ID: {analysis_id})...")
        
        start_time = time.time()
        response = self.session.get(f"{BASE_URL}/analysis/report/generate/word/{analysis_id}")
        end_time = time.time()
        
        print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print("✅ Word raporu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                
                # Content-Disposition header'ını kontrol et (dosya adı için)
                content_disposition = response.headers.get('Content-Disposition', '')
                if content_disposition:
                    print(f"   Dosya adı: {content_disposition}")
                
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
    
    def test_pdf_report_from_detail(self, analysis_id=1):
        """Analysis detail sayfasından PDF raporu oluştur"""
        print(f"📄 PDF raporu test ediliyor (Analiz ID: {analysis_id})...")
        
        start_time = time.time()
        response = self.session.get(f"{BASE_URL}/analysis/report/generate/pdf/{analysis_id}")
        end_time = time.time()
        
        print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' in content_type:
                print("✅ PDF raporu başarıyla oluşturuldu")
                print(f"   Dosya boyutu: {len(response.content)} bytes")
                
                # Content-Disposition header'ını kontrol et
                content_disposition = response.headers.get('Content-Disposition', '')
                if content_disposition:
                    print(f"   Dosya adı: {content_disposition}")
                
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
    
    def test_powerpoint_report_from_detail(self, analysis_id=1):
        """Analysis detail sayfasından PowerPoint raporu oluştur"""
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
                
                # Content-Disposition header'ını kontrol et
                content_disposition = response.headers.get('Content-Disposition', '')
                if content_disposition:
                    print(f"   Dosya adı: {content_disposition}")
                
                return True
            else:
                print(f"⚠️ PowerPoint raporu oluşturuldu ama format beklenmedik: {content_type}")
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
    
    def test_all_formats_for_analysis(self, analysis_id):
        """Belirli bir analiz için tüm rapor formatlarını test et"""
        print(f"\n📊 Analiz {analysis_id} için tüm rapor formatları test ediliyor...")
        print("-" * 50)
        
        results = []
        
        # Analysis detail sayfasını kontrol et
        detail_result = self.test_analysis_detail_page(analysis_id)
        results.append((f"Detail Page-{analysis_id}", detail_result))
        
        # Word raporu test et
        word_result = self.test_word_report_from_detail(analysis_id)
        results.append((f"Word-{analysis_id}", word_result))
        
        # PDF raporu test et
        pdf_result = self.test_pdf_report_from_detail(analysis_id)
        results.append((f"PDF-{analysis_id}", pdf_result))
        
        # PowerPoint raporu test et
        pptx_result = self.test_powerpoint_report_from_detail(analysis_id)
        results.append((f"PowerPoint-{analysis_id}", pptx_result))
        
        return results
    
    def test_multiple_analyses(self):
        """Birden fazla analiz için tüm rapor formatlarını test et"""
        print("🔄 Birden fazla analiz için rapor testleri...")
        
        analysis_ids = [1, 2, 3]  # Test edilecek analiz ID'leri
        all_results = []
        
        for analysis_id in analysis_ids:
            results = self.test_all_formats_for_analysis(analysis_id)
            all_results.extend(results)
        
        return all_results
    
    def run_all_tests(self):
        """Tüm analysis detail rapor testlerini çalıştır"""
        print("🚀 Analysis Detail Rapor Sistemi Test Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Çoklu analiz testleri
        all_results = self.test_multiple_analyses()
        
        # Sonuçları özetle
        print("\n" + "=" * 60)
        print("📊 ANALYSIS DETAIL RAPOR TEST SONUÇLARI")
        print("=" * 60)
        
        passed = 0
        total = len(all_results)
        
        # Analiz bazında grupla
        analysis_groups = {}
        for test_name, result in all_results:
            if '-' in test_name:
                analysis_id = test_name.split('-')[1]
                if analysis_id not in analysis_groups:
                    analysis_groups[analysis_id] = []
                analysis_groups[analysis_id].append((test_name, result))
        
        for analysis_id in sorted(analysis_groups.keys()):
            print(f"\n📊 Analiz {analysis_id} Sonuçları:")
            for test_name, result in analysis_groups[analysis_id]:
                status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
                print(f"   {test_name}: {status}")
                if result:
                    passed += 1
        
        print(f"\nToplam: {passed}/{total} test başarılı")
        
        if passed == total:
            print("🎉 Tüm analysis detail rapor testleri başarılı!")
        else:
            print("⚠️ Bazı analysis detail rapor testleri başarısız oldu.")
        
        # Özet istatistikler
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")

def main():
    tester = AnalysisDetailReportTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
