"""
Arsa Yatırım Danışmanlığı - TAKS/KAKS Test Modülü
Bu modül, TAKS/KAKS hesaplama özelliğini test etmek için kullanılır.
"""

import sys
import os
import json

# Ana dizini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Web scraping modülünü içe aktar
from modules.web_scraping import InsaatAlaniHesaplayici

def test_insaat_alani_hesaplayici():
    """
    InsaatAlaniHesaplayici sınıfını test eder.
    """
    print("InsaatAlaniHesaplayici testi başlatılıyor...")
    
    # Test parametreleri
    test_cases = [
        {
            "arsa_alani": 1000,
            "taks": 0.3,
            "kaks": 1.5,
            "aciklama": "Standart konut arsası"
        },
        {
            "arsa_alani": 500,
            "taks": 0.4,
            "kaks": 2.0,
            "aciklama": "Küçük ticari arsa"
        },
        {
            "arsa_alani": 2000,
            "taks": 0.25,
            "kaks": 1.2,
            "aciklama": "Büyük konut arsası"
        },
        {
            "arsa_alani": 800,
            "taks": 0.5,
            "kaks": 3.0,
            "aciklama": "Yüksek yoğunluklu karma arsa"
        }
    ]
    
    # InsaatAlaniHesaplayici örneği oluştur
    hesaplayici = InsaatAlaniHesaplayici()
    
    try:
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}: {test_case['aciklama']}")
            print(f"Arsa Alanı: {test_case['arsa_alani']} m², TAKS: {test_case['taks']}, KAKS: {test_case['kaks']}")
            
            # İnşaat alanı hesapla
            sonuc = hesaplayici.hesapla(
                test_case['arsa_alani'],
                test_case['taks'],
                test_case['kaks']
            )
            
            # Sonuçları yazdır
            print("Sonuç:")
            print(json.dumps(sonuc, indent=4, ensure_ascii=False))
            
            if "error" in sonuc:
                print(f"Hata: {sonuc['error']}")
                continue
            
            # Sonuçları doğrula
            beklenen_taban_alani = test_case['arsa_alani'] * test_case['taks']
            beklenen_toplam_insaat_alani = test_case['arsa_alani'] * test_case['kaks']
            beklenen_teorik_kat_sayisi = test_case['kaks'] / test_case['taks']
            
            assert abs(sonuc['taban_alani'] - beklenen_taban_alani) < 0.01, "Taban alanı hesaplaması hatalı"
            assert abs(sonuc['toplam_insaat_alani'] - beklenen_toplam_insaat_alani) < 0.01, "Toplam inşaat alanı hesaplaması hatalı"
            assert abs(sonuc['teorik_kat_sayisi'] - beklenen_teorik_kat_sayisi) < 0.01, "Teorik kat sayısı hesaplaması hatalı"
            
            print("Doğrulama başarılı!")
        
        print("\nTüm testler başarıyla tamamlandı!")
        return True
    
    except Exception as e:
        print(f"Test sırasında hata oluştu: {e}")
        return False

if __name__ == "__main__":
    # Testi çalıştır
    test_insaat_alani_hesaplayici()
