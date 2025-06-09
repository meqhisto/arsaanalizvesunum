#!/usr/bin/env python3
"""
DocumentGenerator ile rapor oluşturmayı test eden script
"""

import os
import sys
import json
from datetime import datetime

# Flask uygulamasının modüllerini import etmek için path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.document_generator import DocumentGenerator
from modules.analiz import ArsaAnalizci

def create_test_data():
    """Test için örnek arsa verisi oluştur"""
    return {
        "il": "İstanbul",
        "ilce": "Kadıköy",
        "mahalle": "Moda",
        "ada": "123",
        "parsel": "45",
        "metrekare": 1000.0,
        "fiyat": 5000000.0,
        "bolge_fiyat": 5500.0,
        "imar_durumu": "Konut",
        "taks": 0.4,
        "kaks": 1.2,
        "altyapi": ["yol", "elektrik", "su", "dogalgaz"],
        "koordinatlar": "40.9876, 29.1234",
        "notlar": "Test analizi için oluşturulan örnek veri",
        "created_at": datetime.now(),
        "konum": {
            "il": "İstanbul",
            "ilce": "Kadıköy", 
            "mahalle": "Moda"
        }
    }

def create_test_profile():
    """Test için profil bilgisi oluştur"""
    return {
        "ad": "Test",
        "soyad": "Kullanıcı",
        "email": "test@example.com",
        "telefon": "+90 555 123 4567",
        "sirket": "Test Gayrimenkul",
        "unvan": "Gayrimenkul Uzmanı"
    }

def test_word_generation():
    """Word raporu oluşturmayı test et"""
    print("📄 Word raporu oluşturma testi...")
    
    try:
        # Test verilerini hazırla
        arsa_data = create_test_data()
        profile_info = create_test_profile()
        
        # ArsaAnalizci ile analiz sonuçlarını hesapla
        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et(arsa_data.copy())
        
        # Output directory
        output_dir = "static/presentations"
        file_id = f"test_word_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # DocumentGenerator oluştur
        doc_gen = DocumentGenerator(
            arsa_data=arsa_data,
            analiz_ozeti=analiz_sonuclari,
            file_id=file_id,
            output_dir=output_dir,
            profile_info=profile_info,
            settings={"theme": "classic", "color_scheme": "blue"}
        )
        
        # Word dosyası oluştur
        word_path = doc_gen.create_word()
        
        if word_path and os.path.exists(word_path):
            print(f"✅ Word raporu başarıyla oluşturuldu: {word_path}")
            print(f"   Dosya boyutu: {os.path.getsize(word_path)} bytes")
            return True
        else:
            print("❌ Word raporu oluşturulamadı")
            return False
            
    except Exception as e:
        print(f"❌ Word raporu oluşturma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_generation():
    """PDF raporu oluşturmayı test et"""
    print("📄 PDF raporu oluşturma testi...")
    
    try:
        # Test verilerini hazırla
        arsa_data = create_test_data()
        profile_info = create_test_profile()
        
        # ArsaAnalizci ile analiz sonuçlarını hesapla
        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et(arsa_data.copy())
        
        # Output directory
        output_dir = "static/presentations"
        file_id = f"test_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # DocumentGenerator oluştur
        doc_gen = DocumentGenerator(
            arsa_data=arsa_data,
            analiz_ozeti=analiz_sonuclari,
            file_id=file_id,
            output_dir=output_dir,
            profile_info=profile_info,
            settings={"theme": "classic", "color_scheme": "blue"}
        )
        
        # PDF dosyası oluştur
        pdf_path = doc_gen.create_pdf()
        
        if pdf_path and os.path.exists(pdf_path):
            print(f"✅ PDF raporu başarıyla oluşturuldu: {pdf_path}")
            print(f"   Dosya boyutu: {os.path.getsize(pdf_path)} bytes")
            return True
        else:
            print("❌ PDF raporu oluşturulamadı")
            return False
            
    except Exception as e:
        print(f"❌ PDF raporu oluşturma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_powerpoint_generation():
    """PowerPoint sunumu oluşturmayı test et"""
    print("🎯 PowerPoint sunumu oluşturma testi...")
    
    try:
        # Test verilerini hazırla
        arsa_data = create_test_data()
        profile_info = create_test_profile()
        
        # ArsaAnalizci ile analiz sonuçlarını hesapla
        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et(arsa_data.copy())
        
        # Output directory
        output_dir = "static/presentations"
        file_id = f"test_pptx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # DocumentGenerator oluştur
        doc_gen = DocumentGenerator(
            arsa_data=arsa_data,
            analiz_ozeti=analiz_sonuclari,
            file_id=file_id,
            output_dir=output_dir,
            profile_info=profile_info,
            settings={
                "theme": "classic", 
                "color_scheme": "blue",
                "sections": ["genel_bilgiler", "analiz_sonuclari", "swot_analizi"]
            }
        )
        
        # PowerPoint dosyası oluştur
        pptx_path = doc_gen.create_pptx()
        
        if pptx_path and os.path.exists(pptx_path):
            print(f"✅ PowerPoint sunumu başarıyla oluşturuldu: {pptx_path}")
            print(f"   Dosya boyutu: {os.path.getsize(pptx_path)} bytes")
            return True
        else:
            print("❌ PowerPoint sunumu oluşturulamadı")
            return False
            
    except Exception as e:
        print(f"❌ PowerPoint sunumu oluşturma hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_all_formats():
    """Tüm rapor formatlarını test et"""
    print("🚀 DocumentGenerator Rapor Oluşturma Testi Başlıyor...")
    print(f"Test Zamanı: {datetime.now()}")
    print("=" * 60)
    
    # Test sırası
    tests = [
        ("Word Raporu", test_word_generation),
        ("PDF Raporu", test_pdf_generation),
        ("PowerPoint Sunumu", test_powerpoint_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test hatası: {str(e)}")
            results.append((test_name, False))
    
    # Sonuçları özetle
    print("\n" + "=" * 60)
    print("📊 DOCUMENT GENERATOR TEST SONUÇLARI")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ BAŞARILI" if result else "❌ BAŞARISIZ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nToplam: {passed}/{total} test başarılı")
    
    if passed == total:
        print("🎉 Tüm DocumentGenerator testleri başarılı!")
    else:
        print("⚠️ Bazı DocumentGenerator testleri başarısız oldu.")
    
    # Oluşturulan dosyaları listele
    print("\n📁 Oluşturulan dosyalar:")
    presentations_dir = "static/presentations"
    if os.path.exists(presentations_dir):
        for root, dirs, files in os.walk(presentations_dir):
            for file in files:
                if file.startswith("test_"):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    print(f"   {file_path} ({file_size} bytes)")

def main():
    """Ana test fonksiyonu"""
    test_all_formats()

if __name__ == "__main__":
    main()
