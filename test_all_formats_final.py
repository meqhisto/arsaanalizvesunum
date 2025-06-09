#!/usr/bin/env python3
"""
Analysis detail sayfasından tüm rapor formatlarını test eden final script
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class AllFormatsReportTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self, email="altanbariscomert@inovanettechs.com", password="123456"):
        """Kullanıcı girişi yap"""
        print("🔐 Kullanıcı girişi yapılıyor...")
        
        try:
            # Login sayfasını al
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
        except Exception as e:
            print(f"❌ Login hatası: {str(e)}")
            return False
    
    def test_analysis_detail_page(self, analysis_id):
        """Analysis detail sayfasını kontrol et"""
        print(f"📊 Analiz {analysis_id} detay sayfası kontrol ediliyor...")
        
        try:
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}")
            
            if response.status_code == 200:
                print("✅ Analiz detay sayfası başarıyla alındı")
                
                # Sayfada rapor butonları var mı kontrol et
                page_content = response.text
                
                buttons_found = []
                if "Word Raporu İndir" in page_content:
                    buttons_found.append("Word")
                if "PDF Raporu İndir" in page_content:
                    buttons_found.append("PDF")
                if "PowerPoint Sunumu İndir" in page_content:
                    buttons_found.append("PowerPoint")
                
                print(f"   Bulunan rapor butonları: {', '.join(buttons_found)}")
                return True
            else:
                print(f"❌ Analiz detay sayfası alınamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Analiz detay sayfası hatası: {str(e)}")
            return False
    
    def test_word_report_new_endpoint(self, analysis_id):
        """Yeni endpoint ile Word raporu test et"""
        print(f"📄 Word raporu test ediliyor (Yeni Endpoint - Analiz ID: {analysis_id})...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}/report/word")
            end_time = time.time()
            
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'wordprocessingml.document' in content_type:
                    print(f"✅ Word raporu başarıyla oluşturuldu ({len(response.content)} bytes)")
                    return True
                else:
                    print(f"⚠️ Word raporu oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            else:
                print(f"❌ Word raporu oluşturulamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Word raporu test hatası: {str(e)}")
            return False
    
    def test_pdf_report_new_endpoint(self, analysis_id):
        """Yeni endpoint ile PDF raporu test et"""
        print(f"📄 PDF raporu test ediliyor (Yeni Endpoint - Analiz ID: {analysis_id})...")
        
        try:
            start_time = time.time()
            response = self.session.get(f"{BASE_URL}/analysis/{analysis_id}/report/pdf")
            end_time = time.time()
            
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type:
                    print(f"✅ PDF raporu başarıyla oluşturuldu ({len(response.content)} bytes)")
                    return True
                else:
                    print(f"⚠️ PDF raporu oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            else:
                print(f"❌ PDF raporu oluşturulamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ PDF raporu test hatası: {str(e)}")
            return False
    
    def test_powerpoint_report_old_endpoint(self, analysis_id):
        """Eski endpoint ile PowerPoint raporu test et"""
        print(f"🎯 PowerPoint raporu test ediliyor (Eski Endpoint - Analiz ID: {analysis_id})...")
        
        try:
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
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'presentationml.presentation' in content_type:
                    print(f"✅ PowerPoint raporu başarıyla oluşturuldu ({len(response.content)} bytes)")
                    return True
                else:
                    print(f"⚠️ PowerPoint raporu oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            else:
                print(f"❌ PowerPoint raporu oluşturulamadı: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ PowerPoint raporu test hatası: {str(e)}")
            return False
    
    def test_all_formats_for_analysis(self, analysis_id):
        """Belirli bir analiz için tüm rapor formatlarını test et"""
        print(f"\n📊 Analiz {analysis_id} için tüm rapor formatları test ediliyor...")
        print("-" * 60)
        
        results = []
        
        # Analysis detail sayfasını kontrol et
        detail_result = self.test_analysis_detail_page(analysis_id)
        results.append((f"Detail Page-{analysis_id}", detail_result))
        
        # Word raporu test et (yeni endpoint)
        word_result = self.test_word_report_new_endpoint(analysis_id)
        results.append((f"Word-{analysis_id}", word_result))
        
        # PDF raporu test et (yeni endpoint)
        pdf_result = self.test_pdf_report_new_endpoint(analysis_id)
        results.append((f"PDF-{analysis_id}", pdf_result))
        
        # PowerPoint raporu test et (eski endpoint)
        pptx_result = self.test_powerpoint_report_old_endpoint(analysis_id)
        results.append((f"PowerPoint-{analysis_id}", pptx_result))
        
        return results
    
    def run_comprehensive_test(self):
        """Kapsamlı tüm format testi çalıştır"""
        print("🚀 Analysis Detail Tüm Format Rapor Testi Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 70)
        
        # Login kontrolü
        if not self.login():
            print("❌ Login başarısız, testler durduruluyor")
            return
        
        # Test edilecek analiz ID'leri
        analysis_ids = [1, 2, 3]
        all_results = []
        
        for analysis_id in analysis_ids:
            results = self.test_all_formats_for_analysis(analysis_id)
            all_results.extend(results)
        
        # Sonuçları özetle
        print("\n" + "=" * 70)
        print("📊 TÜM FORMAT RAPOR TEST SONUÇLARI")
        print("=" * 70)
        
        passed = 0
        total = len(all_results)
        
        # Analiz bazında grupla
        analysis_groups = {}
        for test_name, result in all_results:
            if '-' in test_name:
                parts = test_name.split('-')
                format_type = parts[0]
                analysis_id = parts[1]
                
                if analysis_id not in analysis_groups:
                    analysis_groups[analysis_id] = {}
                analysis_groups[analysis_id][format_type] = result
        
        for analysis_id in sorted(analysis_groups.keys()):
            print(f"\n📊 Analiz {analysis_id} Sonuçları:")
            for format_type, result in analysis_groups[analysis_id].items():
                status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
                print(f"   {format_type}: {status}")
                if result:
                    passed += 1
        
        print(f"\nToplam: {passed}/{total} test başarılı")
        
        # Başarı oranı
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Başarı oranı: {success_rate:.1f}%")
        
        if passed == total:
            print("🎉 Tüm analysis detail rapor testleri başarılı!")
        else:
            print("⚠️ Bazı analysis detail rapor testleri başarısız oldu.")
        
        # Format bazında özet
        print(f"\n📈 Format Bazında Özet:")
        format_stats = {}
        for analysis_id in analysis_groups:
            for format_type, result in analysis_groups[analysis_id].items():
                if format_type not in format_stats:
                    format_stats[format_type] = {"success": 0, "total": 0}
                format_stats[format_type]["total"] += 1
                if result:
                    format_stats[format_type]["success"] += 1
        
        for format_type, stats in format_stats.items():
            success_rate = (stats["success"] / stats["total"]) * 100
            print(f"   {format_type.upper()}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Endpoint özeti
        print(f"\n🔗 Kullanılan Endpoint'ler:")
        print(f"   Word: /analysis/{{id}}/report/word (Yeni)")
        print(f"   PDF: /analysis/{{id}}/report/pdf (Yeni)")
        print(f"   PowerPoint: /analysis/report/generate_pptx/{{id}} (Eski)")

def main():
    tester = AllFormatsReportTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
