"""
Arsa Yatırım Danışmanlığı - Veri İşleyici Modülü
Bu modül, arsa verilerini işlemek ve analiz etmek için kullanılır.
"""

import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
import aiofiles
import asyncio
from functools import lru_cache

class VeriIsleyici:
    def __init__(self, data_dir, db_session: Session = None):
        """
        Veri işleyici sınıfını başlatır.
        
        Args:
            data_dir (str): Veri dosyalarının saklanacağı dizin
            db_session (Session, optional): SQLAlchemy oturumu
        """
        self.data_dir = data_dir
        self.db_session = db_session
        os.makedirs(data_dir, exist_ok=True)
    
    async def async_kaydet(self, arsa_data):
        """
        Arsa verilerini JSON formatında asenkron olarak kaydeder.
        
        Args:
            arsa_data (dict): Kaydedilecek arsa verileri
            
        Returns:
            str: Oluşturulan dosyanın benzersiz ID'si
        """
        file_id = datetime.now().strftime('%Y%m%d%H%M%S')
        filepath = os.path.join(self.data_dir, f"arsa_{file_id}.json")
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(arsa_data, ensure_ascii=False, indent=4))
        
        return file_id

    @lru_cache(maxsize=100)
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
