"""
Arsa Yatırım Danışmanlığı - Veri İşleyici Modülü
Bu modül, arsa verilerini işlemek ve analiz etmek için kullanılır.
"""

import json
import os
from datetime import datetime

class VeriIsleyici:
    def __init__(self, data_dir):
        """
        Veri işleyici sınıfını başlatır.
        
        Args:
            data_dir (str): Veri dosyalarının saklanacağı dizin
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def kaydet(self, arsa_data):
        """
        Arsa verilerini JSON formatında kaydeder.
        
        Args:
            arsa_data (dict): Kaydedilecek arsa verileri
            
        Returns:
            str: Oluşturulan dosyanın benzersiz ID'si
        """
        # Benzersiz bir dosya adı oluştur
        file_id = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"arsa_{file_id}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        # Verileri JSON olarak kaydet
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(arsa_data, f, ensure_ascii=False, indent=4)
        
        return file_id
    
    def yukle(self, file_id):
        """
        Belirtilen ID'ye sahip arsa verilerini yükler.
        
        Args:
            file_id (str): Yüklenecek dosyanın ID'si
            
        Returns:
            dict: Yüklenen arsa verileri veya dosya bulunamazsa None
        """
        filepath = os.path.join(self.data_dir, f"arsa_{file_id}.json")
        
        # Dosya yoksa None döndür
        if not os.path.exists(filepath):
            return None
        
        # Verileri oku
        with open(filepath, 'r', encoding='utf-8') as f:
            arsa_data = json.load(f)
        
        return arsa_data
    
    def tum_arsalari_listele(self):
        """
        Tüm kayıtlı arsa verilerini listeler.
        
        Returns:
            list: Arsa verilerinin listesi
        """
        arsalar = []
        
        # data_dir içindeki tüm JSON dosyalarını tara
        for filename in os.listdir(self.data_dir):
            if filename.startswith("arsa_") and filename.endswith(".json"):
                file_id = filename[5:-5]  # "arsa_" ve ".json" kısımlarını çıkar
                arsa_data = self.yukle(file_id)
                if arsa_data:
                    arsa_data['file_id'] = file_id
                    arsalar.append(arsa_data)
        
        # Tarihe göre sırala (en yeniden en eskiye)
        arsalar.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return arsalar
