#!/usr/bin/env python3
"""
Analysis detail sayfasından final rapor testleri
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class FinalReportTester:
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
    
    def test_single_report(self, analysis_id, format_type, endpoint):
        """Tek bir rapor formatını test et"""
        print(f"📄 {format_type.upper()} raporu test ediliyor (Analiz ID: {analysis_id})...")
        
        try:
            start_time = time.time()
            
            if format_type == 'powerpoint':
                # PowerPoint için POST verisi
                data = {
                    "sections": '["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]',
                    "color_scheme": "blue"
                }
                response = self.session.post(endpoint, data=data)
            else:
                # Word ve PDF için GET
                response = self.session.get(endpoint)
            
            end_time = time.time()
            
            print(f"   İşlem süresi: {end_time - start_time:.2f} saniye")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                file_size = len(response.content)
                
                # Format kontrolü
                if format_type == 'word' and 'wordprocessingml.document' in content_type:
                    print(f"✅ {format_type.upper()} raporu başarıyla oluşturuldu ({file_size} bytes)")
                    return True
                elif format_type == 'pdf' and 'application/pdf' in content_type:
                    print(f"✅ {format_type.upper()} raporu başarıyla oluşturuldu ({file_size} bytes)")
                    return True
                elif format_type == 'powerpoint' and 'presentationml.presentation' in content_type:
                    print(f"✅ {format_type.upper()} raporu başarıyla oluşturuldu ({file_size} bytes)")
                    return True
                else:
                    print(f"⚠️ {format_type.upper()} raporu oluşturuldu ama format beklenmedik: {content_type}")
                    return False
            elif response.status_code == 404:
                print(f"⚠️ Analiz {analysis_id} bulunamadı")
                return False
            else:
                print(f"❌ {format_type.upper()} raporu oluşturulamadı: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ {format_type.upper()} raporu test hatası: {str(e)}")
            return False
    
    def test_all_formats_for_analysis(self, analysis_id):
        """Belirli bir analiz için tüm rapor formatlarını test et"""
        print(f"\n📊 Analiz {analysis_id} için tüm rapor formatları test ediliyor...")
        print("-" * 50)
        
        # Test edilecek formatlar ve endpoint'leri
        formats = [
            ("word", f"{BASE_URL}/analysis/report/generate/word/{analysis_id}"),
            ("pdf", f"{BASE_URL}/analysis/report/generate/pdf/{analysis_id}"),
            ("powerpoint", f"{BASE_URL}/analysis/report/generate_pptx/{analysis_id}")
        ]
        
        results = []
        for format_type, endpoint in formats:
            result = self.test_single_report(analysis_id, format_type, endpoint)
            results.append((f"{format_type.upper()}-{analysis_id}", result))
        
        return results
    
    def run_comprehensive_test(self):
        """Kapsamlı rapor testi çalıştır"""
        print("🚀 Analysis Detail Kapsamlı Rapor Testi Başlıyor...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test Zamanı: {datetime.now()}")
        print("=" * 60)
        
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
        print("\n" + "=" * 60)
        print("📊 KAPSAMLI RAPOR TEST SONUÇLARI")
        print("=" * 60)
        
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

def main():
    tester = FinalReportTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
