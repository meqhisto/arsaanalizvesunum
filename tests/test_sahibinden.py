"""
Arsa Yatırım Danışmanlığı - Emlak Sitesi Test Modülü
Bu modül, sahibinden.com entegrasyonunu test etmek için kullanılır.
"""

import sys
import os
import json

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Web scraping modülünü içe aktar
from modules.web_scraping import SahibindenScraper

def test_sahibinden_scraper():
    """
    SahibindenScraper sınıfını test eder.
    """
    print("SahibindenScraper testi başlatılıyor...")
    
    # Test parametreleri
    test_il = "istanbul"
    test_ilce = "kadikoy"
    test_mahalle = "caddebostan"
    test_imar_durumu = "konut"
    
    # SahibindenScraper örneği oluştur
    scraper = SahibindenScraper()
    
    try:
        # Arsa fiyatlarını çek
        print(f"Bölge fiyat bilgileri çekiliyor: {test_il}, {test_ilce}, {test_mahalle}, {test_imar_durumu}")
        sonuc = scraper.get_arsa_fiyatlari(test_il, test_ilce, test_mahalle, test_imar_durumu)
        
        # Sonuçları yazdır
        print("Sonuç:")
        print(json.dumps(sonuc, indent=4, ensure_ascii=False))
        
        if "error" in sonuc:
            print(f"Hata: {sonuc['error']}")
            return False
        
        print("Test başarılı!")
        return True
    
    except Exception as e:
        print(f"Test sırasında hata oluştu: {e}")
        return False

if __name__ == "__main__":
    # Testi çalıştır
    test_sahibinden_scraper()
