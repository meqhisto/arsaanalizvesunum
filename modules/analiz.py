"""
Arsa Yatırım Danışmanlığı - Analiz Modülü
Bu modül, arsa verilerini analiz etmek ve potansiyel getiri hesaplamak için kullanılır.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class AnalizMetrikleri:
    potansiyel_getiri: float
    risk_puani: int
    yatirim_suresi: int
    uygunluk_puani: float # Uygunluk puanı eklendi

class AnalizStratejisi(ABC):
    @abstractmethod
    def analiz_et(self, data: Dict) -> AnalizMetrikleri:
        pass

class SwotAnalizi(AnalizStratejisi):
    def analiz_et(self, data: Dict) -> AnalizMetrikleri:
        # SWOT analiz mantığı
        pass

class RaporBuilder:
    def __init__(self):
        self.rapor = {}
    
    def add_metrics(self, metrics: AnalizMetrikleri):
        self.rapor['metrikler'] = metrics
        return self

class ArsaAnalizci:
    def __init__(self, strateji: AnalizStratejisi = None):
        """
        Arsa analizci sınıfını başlatır.
        """
        self.strateji = strateji or SwotAnalizi()
        self.rapor_builder = RaporBuilder()
        # İmar durumuna göre potansiyel getiri katsayıları
        self.imar_katsayilari = {
            'konut': 1.05,
            'ticari': 1.08,
            'karma': 1.07,
            'sanayi': 1.04,
            'diger': 1.03
        }
        # İmar durumuna göre uygunluk puanı katsayıları (Örnek değerler)
        self.imar_uygunluk_katsayilari = {
            'konut': 0.9,
            'ticari': 0.8,
            'karma': 0.85,
            'sanayi': 0.7,
            'diger': 0.6
        }
        # Altyapı uygunluk puanları (Örnek değerler)
        self.altyapi_uygunluk_puanlari = {
            'yol': 0.1,
            'elektrik': 0.1,
            'su': 0.1,
            'dogalgaz': 0.05,
            'kanalizasyon': 0.05
        }

    def analiz_et(self, arsa_data):
        """
        Arsa verilerini analiz eder ve sonuçları hesaplar.
        
        Args:
            arsa_data (dict): Analiz edilecek arsa verileri
            
        Returns:
            dict: Analiz sonuçları eklenmiş arsa verileri
        """
        # Metrekare başına fiyat hesaplama
        arsa_data['metrekare_fiyat'] = arsa_data['fiyat'] / arsa_data['metrekare']
        
        # Bölge karşılaştırması (yüzde olarak)
        arsa_data['bolge_karsilastirma'] = round((arsa_data['metrekare_fiyat'] / arsa_data['bolge_fiyat'] - 1) * 100, 2)
        
        # Potansiyel getiri hesaplama
        arsa_data['potansiyel_getiri'] = self._hesapla_potansiyel_getiri(arsa_data)
        
        # Tavsiye edilen yatırım süresi hesaplama
        arsa_data['yatirim_suresi'] = self._hesapla_yatirim_suresi(arsa_data)
        
        # Yatırım değerlendirmesi
        arsa_data['yatirim_degerlendirmesi'] = self._degerlendir_yatirim(arsa_data)

        # Uygunluk puanı hesaplama (YENİ EKLENEN)
        arsa_data['uygunluk_puani'] = self._hesapla_uygunluk_puani(arsa_data)
        
        return arsa_data
    
    def _hesapla_potansiyel_getiri(self, arsa_data):
        """
        Potansiyel getiri oranını hesaplar.
        
        Args:
            arsa_data (dict): Arsa verileri
            
        Returns:
            float: Potansiyel yıllık getiri oranı (%)
        """
        # İmar durumuna göre baz getiri katsayısı
        imar_durumu = arsa_data['imar_durumu'].lower()
        katsayi = self.imar_katsayilari.get(imar_durumu, 1.03)
        
        # Bölge karşılaştırmasına göre getiri ayarlaması
        bolge_karsilastirma = arsa_data['bolge_karsilastirma']
        
        if bolge_karsilastirma < -15:  # Bölgeden çok daha ucuz
            getiri_carpani = 1.3
        elif bolge_karsilastirma < -10:  # Bölgeden oldukça ucuz
            getiri_carpani = 1.2
        elif bolge_karsilastirma < -5:  # Bölgeden ucuz
            getiri_carpani = 1.1
        elif bolge_karsilastirma > 15:  # Bölgeden çok daha pahalı
            getiri_carpani = 0.7
        elif bolge_karsilastirma > 10:  # Bölgeden oldukça pahalı
            getiri_carpani = 0.8
        elif bolge_karsilastirma > 5:  # Bölgeden pahalı
            getiri_carpani = 0.9
        else:
            getiri_carpani = 1.0
        
        # Metrekare büyüklüğüne göre ek ayarlama
        metrekare = arsa_data['metrekare']
        if metrekare > 10000:  # Çok büyük arsalar
            buyukluk_carpani = 1.1
        elif metrekare > 5000:  # Büyük arsalar
            buyukluk_carpani = 1.05
        elif metrekare < 100:  # Çok küçük arsalar
            buyukluk_carpani = 0.9
        else:
            buyukluk_carpani = 1.0
        
        # Potansiyel getiri hesaplama
        potansiyel_getiri = round((katsayi - 1) * 100 * getiri_carpani * buyukluk_carpani, 2)
        
        return potansiyel_getiri
    
    def _hesapla_yatirim_suresi(self, arsa_data):
        """
        Tavsiye edilen minimum yatırım süresini hesaplar.
        
        Args:
            arsa_data (dict): Arsa verileri
            
        Returns:
            int: Tavsiye edilen minimum yatırım süresi (yıl)
        """
        potansiyel_getiri = arsa_data['potansiyel_getiri']
        
        if potansiyel_getiri > 8:
            return 3
        elif potansiyel_getiri > 6:
            return 4
        elif potansiyel_getiri > 4:
            return 5
        else:
            return 7
    
    def _degerlendir_yatirim(self, arsa_data):
        """
        Yatırım değerlendirmesi yapar.
        
        Args:
            arsa_data (dict): Arsa verileri
            
        Returns:
            dict: Yatırım değerlendirmesi
        """
        potansiyel_getiri = arsa_data['potansiyel_getiri']
        bolge_karsilastirma = arsa_data['bolge_karsilastirma']
        
        if potansiyel_getiri > 8:
            derece = "yüksek"
            oneri = "Bu arsa yüksek getiri potansiyeli sunmaktadır."
        elif potansiyel_getiri > 5:
            derece = "orta"
            oneri = "Bu arsa orta seviyede getiri potansiyeli sunmaktadır."
        else:
            derece = "düşük"
            oneri = "Bu arsa düşük getiri potansiyeli sunmaktadır."
        
        if bolge_karsilastirma < -10:
            fiyat_degerlendirme = "Arsa fiyatı bölge ortalamasının oldukça altındadır, bu bir fırsat olabilir."
        elif bolge_karsilastirma < 0:
            fiyat_degerlendirme = "Arsa fiyatı bölge ortalamasının altındadır, bu avantajlı bir durum olabilir."
        elif bolge_karsilastirma > 10:
            fiyat_degerlendirme = "Arsa fiyatı bölge ortalamasının oldukça üzerindedir, bu risk oluşturabilir."
        elif bolge_karsilastirma > 0:
            fiyat_degerlendirme = "Arsa fiyatı bölge ortalamasının üzerindedir, dikkatli değerlendirme yapılmalıdır."
        else:
            fiyat_degerlendirme = "Arsa fiyatı bölge ortalamasına yakındır."
        
        return {
            "derece": derece,
            "oneri": oneri,
            "fiyat_degerlendirme": fiyat_degerlendirme,
            "yatirim_suresi_aciklama": f"Bu arsa için tavsiye edilen minimum yatırım süresi {arsa_data['yatirim_suresi']} yıldır."
        }
    
    def _hesapla_uygunluk_puani(self, arsa_data):
        """
        Arsa uygunluk puanını hesaplar (0-100 arası).
        
        Args:
            arsa_data (dict): Arsa verileri
            
        Returns:
            float: Uygunluk puanı (0-100)
        """
        puan = 0
        
        # İmar durumu katkısı
        imar_durumu = arsa_data.get('imar_durumu', '').lower()
        puan += self.imar_uygunluk_katsayilari.get(imar_durumu, 0.5) * 30 # İmar durumu %30 etkili (Örnek ağırlık)
        
        # Metrekare katkısı (Örnek: Belirli aralıklarda daha yüksek puan)
        metrekare = arsa_data.get('metrekare', 0)
        if 500 <= metrekare <= 5000:
            puan += 25 # Metrekare %25 etkili (Örnek ağırlık)
        elif metrekare > 5000:
             puan += 20
        elif metrekare < 500 and metrekare > 0:
             puan += 15

        # Bölge karşılaştırması katkısı (Örnek: Bölge ortalamasına yakın veya altında olması pozitif)
        bolge_karsilastirma = arsa_data.get('bolge_karsilastirma', 0)
        if bolge_karsilastirma <= 0:
            puan += 20 # Bölge karşılaştırması %20 etkili (Örnek ağırlık)
        elif bolge_karsilastirma > 0 and bolge_karsilastirma <= 10:
            puan += 10
        
        # Altyapı katkısı (Örnek: Her altyapı için sabit puan)
        altyapi = arsa_data.get('altyapi', {})
        if isinstance(altyapi, str):
             try:
                 altyapi = json.loads(altyapi)
             except json.JSONDecodeError:
                 altyapi = {}

        if isinstance(altyapi, list):
            for item in altyapi:
                puan += self.altyapi_uygunluk_puanlari.get(item.lower(), 0) * 10 # Altyapı %10 etkili (Örnek ağırlık)
        
        # Puanı 0-100 arasına ölçeklendirme (Basit bir ölçeklendirme, daha karmaşık olabilir)
        # Maksimum olası puanı tahmin et (Örnek ağırlıklara göre)
        max_puan = (1.0 * 30) + 25 + 20 + (0.1 * 5 * 10) # En iyi imar, ideal metrekare, en iyi bölge, tüm altyapılar
        olcekli_puan = (puan / max_puan) * 100 if max_puan > 0 else 0

        # Puanı 0-100 arasına sabitleme
        return round(max(0, min(100, olcekli_puan)), 2)


    def ozetle(self, arsa_data):
        """
        Arsa analiz sonuçlarını özetler ve metin oluşturur.
        
        Args:
            arsa_data (dict): Analiz edilmiş arsa verileri
            
        Returns:
            dict: Özet metinler
        """
        # Konum bilgisi
        konum = f"{arsa_data['konum']['mahalle']}, {arsa_data['konum']['ilce']}, {arsa_data['konum']['il']}"
        
        # Temel bilgiler özeti
        temel_ozet = (
            f"{konum} konumunda bulunan {arsa_data['metrekare']} m² büyüklüğündeki {arsa_data['imar_durumu']} "
            f"imarlı arsa, {arsa_data['fiyat']:,.2f} TL fiyatla satılmaktadır. "
            f"Metrekare fiyatı {arsa_data['metrekare_fiyat']:,.2f} TL/m² olup, "
            f"bölge ortalaması olan {arsa_data['bolge_fiyat']:,.2f} TL/m² ile karşılaştırıldığında "
        )
        
        if arsa_data['bolge_karsilastirma'] < 0:
            temel_ozet += f"bölge ortalamasından %{abs(arsa_data['bolge_karsilastirma']):.1f} daha ucuzdur."
        else:
            temel_ozet += f"bölge ortalamasından %{arsa_data['bolge_karsilastirma']:.1f} daha pahalıdır."
        
        # Yatırım analizi özeti
        yatirim_ozet = (
            f"Yapılan analizlere göre, bu arsanın yıllık %{arsa_data['potansiyel_getiri']} potansiyel getiri "
            f"sunması beklenmektedir. {arsa_data['yatirim_degerlendirmesi']['oneri']} "
            f"{arsa_data['yatirim_degerlendirmesi']['fiyat_degerlendirme']} "
            f"{arsa_data['yatirim_degerlendirmesi']['yatirim_suresi_aciklama']}"
        )

        # Uygunluk puanı özeti (YENİ EKLENEN)
        uygunluk_ozet = f"Arsanın uygunluk puanı: {arsa_data['uygunluk_puani']}/100. Bu puan, arsanın imar durumu, büyüklüğü, konumu ve altyapı gibi faktörlere göre genel uygunluğunu göstermektedir."
        
        # Tavsiyeler
        if arsa_data['potansiyel_getiri'] > 7:
            tavsiyeler = (
                "Bu arsa yüksek getiri potansiyeli sunmaktadır ve yatırım için öncelikli olarak değerlendirilebilir. "
                "Bölgedeki gelişim planları ve altyapı çalışmaları takip edilmelidir. "
                "Kısa-orta vadede değer artışı beklenmektedir."
            )
        elif arsa_data['potansiyel_getiri'] > 5:
            tavsiyeler = (
                "Bu arsa orta seviyede getiri potansiyeli sunmaktadır. "
                "Orta-uzun vadeli bir yatırım olarak değerlendirilebilir. "
                "Bölgedeki gelişmelere bağlı olarak getiri oranı değişebilir."
            )
        else:
            tavsiyeler = (
                "Bu arsa düşük getiri potansiyeli sunmaktadır. "
                "Uzun vadeli bir yatırım olarak değerlendirilmelidir. "
                "Alternatif yatırım fırsatları da araştırılmalıdır."
            )
        
        return {
            "temel_ozet": temel_ozet,
            "yatirim_ozet": yatirim_ozet,
            "uygunluk_ozet": uygunluk_ozet, # Uygunluk özeti eklendi
            "tavsiyeler": tavsiyeler
        }
