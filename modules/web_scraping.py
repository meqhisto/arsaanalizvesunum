"""
Arsa Yatırım Danışmanlığı - Web Scraping Modülü
Bu modül, parselsorgu.tkgm.gov.tr ve sahibinden.com gibi sitelerden veri çekmek için kullanılır.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
from urllib.parse import quote

class ParselSorgu:
    """
    parselsorgu.tkgm.gov.tr sitesinden parsel bilgilerini çekmek için kullanılan sınıf
    """
    
    def __init__(self):
        """
        ParselSorgu sınıfını başlatır.
        """
        self.base_url = "https://parselsorgu.tkgm.gov.tr"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session.headers.update(self.headers)
    
    def _get_csrf_token(self):
        """
        CSRF token'ı almak için ana sayfayı ziyaret eder.
        
        Returns:
            str: CSRF token
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('input', {'name': '_csrf'}).get('value')
            
            return csrf_token
        except Exception as e:
            print(f"CSRF token alınırken hata oluştu: {e}")
            return None
    
    def sorgula(self, il, ilce, mahalle, ada, parsel):
        """
        Belirtilen parsel bilgileriyle sorgu yapar.
        
        Args:
            il (str): İl adı
            ilce (str): İlçe adı
            mahalle (str): Mahalle adı
            ada (str): Ada numarası
            parsel (str): Parsel numarası
            
        Returns:
            dict: Parsel bilgileri veya hata durumunda None
        """
        try:
            # CSRF token al
            csrf_token = self._get_csrf_token()
            if not csrf_token:
                return {"error": "CSRF token alınamadı"}
            
            # İl, ilçe ve mahalle kodlarını al
            il_kod = self._get_il_kod(il)
            if not il_kod:
                return {"error": f"'{il}' ili bulunamadı"}
            
            ilce_kod = self._get_ilce_kod(il_kod, ilce)
            if not ilce_kod:
                return {"error": f"'{ilce}' ilçesi bulunamadı"}
            
            mahalle_kod = self._get_mahalle_kod(il_kod, ilce_kod, mahalle)
            if not mahalle_kod:
                return {"error": f"'{mahalle}' mahallesi bulunamadı"}
            
            # Sorgu yap
            sorgu_url = f"{self.base_url}/parsel-sorgu"
            sorgu_data = {
                "_csrf": csrf_token,
                "il": il_kod,
                "ilce": ilce_kod,
                "mahalle": mahalle_kod,
                "ada": ada,
                "parsel": parsel
            }
            
            # İnsan davranışını taklit etmek için kısa bir bekleme
            time.sleep(random.uniform(1, 2))
            
            response = self.session.post(sorgu_url, data=sorgu_data, timeout=15)
            response.raise_for_status()
            
            # Yanıtı işle
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Hata kontrolü
            error_msg = soup.find('div', {'class': 'alert-danger'})
            if error_msg:
                return {"error": error_msg.text.strip()}
            
            # Parsel bilgilerini çıkar
            parsel_bilgileri = {}
            
            # Alan bilgisini bul
            alan_div = soup.find('div', text=re.compile('Alan'))
            if alan_div and alan_div.find_next('div'):
                alan_text = alan_div.find_next('div').text.strip()
                # Metrekare değerini çıkar
                alan_match = re.search(r'([\d,.]+)\s*m²', alan_text)
                if alan_match:
                    alan = alan_match.group(1).replace('.', '').replace(',', '.')
                    parsel_bilgileri['alan'] = float(alan)
            
            # Diğer bilgileri de ekle
            for label_div in soup.find_all('div', {'class': 'col-sm-4'}):
                label = label_div.text.strip()
                if label and label_div.find_next('div'):
                    value = label_div.find_next('div').text.strip()
                    key = label.lower().replace(' ', '_')
                    parsel_bilgileri[key] = value
            
            return parsel_bilgileri
        
        except Exception as e:
            print(f"Parsel sorgulanırken hata oluştu: {e}")
            return {"error": f"Parsel sorgulanırken hata oluştu: {e}"}
    
    def _get_il_kod(self, il_adi):
        """
        İl adına göre il kodunu alır.
        
        Args:
            il_adi (str): İl adı
            
        Returns:
            str: İl kodu veya bulunamazsa None
        """
        try:
            url = f"{self.base_url}/api/il"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            iller = response.json()
            for il in iller:
                if il['text'].lower() == il_adi.lower():
                    return il['id']
            
            return None
        except Exception as e:
            print(f"İl kodu alınırken hata oluştu: {e}")
            return None
    
    def _get_ilce_kod(self, il_kod, ilce_adi):
        """
        İlçe adına göre ilçe kodunu alır.
        
        Args:
            il_kod (str): İl kodu
            ilce_adi (str): İlçe adı
            
        Returns:
            str: İlçe kodu veya bulunamazsa None
        """
        try:
            url = f"{self.base_url}/api/ilce?ilId={il_kod}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            ilceler = response.json()
            for ilce in ilceler:
                if ilce['text'].lower() == ilce_adi.lower():
                    return ilce['id']
            
            return None
        except Exception as e:
            print(f"İlçe kodu alınırken hata oluştu: {e}")
            return None
    
    def _get_mahalle_kod(self, il_kod, ilce_kod, mahalle_adi):
        """
        Mahalle adına göre mahalle kodunu alır.
        
        Args:
            il_kod (str): İl kodu
            ilce_kod (str): İlçe kodu
            mahalle_adi (str): Mahalle adı
            
        Returns:
            str: Mahalle kodu veya bulunamazsa None
        """
        try:
            url = f"{self.base_url}/api/mahalle?ilId={il_kod}&ilceId={ilce_kod}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            mahalleler = response.json()
            for mahalle in mahalleler:
                if mahalle['text'].lower() == mahalle_adi.lower():
                    return mahalle['id']
            
            return None
        except Exception as e:
            print(f"Mahalle kodu alınırken hata oluştu: {e}")
            return None


class SahibindenScraper:
    """
    sahibinden.com sitesinden arsa fiyat bilgilerini çekmek için kullanılan sınıf
    """
    
    def __init__(self):
        """
        SahibindenScraper sınıfını başlatır.
        """
        self.base_url = "https://www.sahibinden.com"
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session.headers.update(self.headers)
    
    def _get_search_url(self, il, ilce, mahalle, kategori="arsa"):
        """
        Arama URL'sini oluşturur.
        
        Args:
            il (str): İl adı
            ilce (str): İlçe adı
            mahalle (str): Mahalle adı
            kategori (str): Kategori (arsa, konut, vb.)
            
        Returns:
            str: Arama URL'si
        """
        # URL'de kullanılacak şekilde kodla
        il_encoded = quote(il.lower())
        ilce_encoded = quote(ilce.lower())
        mahalle_encoded = quote(mahalle.lower())
        
        # Kategori kontrolü
        if kategori.lower() == "arsa":
            kategori_path = "arsa"
        else:
            kategori_path = kategori.lower()
        
        # Arama URL'sini oluştur
        search_url = f"{self.base_url}/{kategori_path}/{il_encoded}/{ilce_encoded}/{mahalle_encoded}"
        
        return search_url
    
    def get_arsa_fiyatlari(self, il, ilce, mahalle, imar_durumu=None):
        """
        Belirtilen bölgedeki arsa fiyatlarını çeker.
        
        Args:
            il (str): İl adı
            ilce (str): İlçe adı
            mahalle (str): Mahalle adı
            imar_durumu (str, optional): İmar durumu filtresi
            
        Returns:
            dict: Arsa fiyat bilgileri
        """
        try:
            # Arama URL'sini oluştur
            search_url = self._get_search_url(il, ilce, mahalle, "arsa")
            
            # İnsan davranışını taklit etmek için kısa bir bekleme
            time.sleep(random.uniform(2, 4))
            
            # Sayfayı çek
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            
            # Yanıtı işle
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # İlan listesini bul
            ilan_listesi = soup.find('tbody', {'class': 'searchResultsRowClass'})
            if not ilan_listesi:
                return {"error": "İlan listesi bulunamadı"}
            
            # İlanları topla
            ilanlar = []
            for ilan in ilan_listesi.find_all('tr'):
                try:
                    # Fiyat bilgisini al
                    fiyat_div = ilan.find('td', {'class': 'searchResultsPriceValue'})
                    if not fiyat_div:
                        continue
                    
                    fiyat_text = fiyat_div.text.strip()
                    # TL değerini çıkar
                    fiyat_match = re.search(r'([\d,.]+)\s*TL', fiyat_text)
                    if not fiyat_match:
                        continue
                    
                    fiyat = fiyat_match.group(1).replace('.', '').replace(',', '.')
                    
                    # Metrekare bilgisini al
                    detay_div = ilan.find('td', {'class': 'searchResultsAttributeValue'})
                    if not detay_div:
                        continue
                    
                    metrekare_text = detay_div.text.strip()
                    # Metrekare değerini çıkar
                    metrekare_match = re.search(r'([\d,.]+)\s*m²', metrekare_text)
                    if not metrekare_match:
                        continue
                    
                    metrekare = metrekare_match.group(1).replace('.', '').replace(',', '.')
                    
                    # İmar durumu bilgisini al (varsa)
                    imar_durumu_actual = None
                    detay_divs = ilan.find_all('td', {'class': 'searchResultsAttributeValue'})
                    for div in detay_divs:
                        if "İmar Durumu" in div.text:
                            imar_durumu_actual = div.find_next('td').text.strip()
                            break
                    
                    # İmar durumu filtresi varsa kontrol et
                    if imar_durumu and imar_durumu_actual and imar_durumu.lower() != imar_durumu_actual.lower():
                        continue
                    
                    # İlan bilgilerini ekle
                    ilan_bilgisi = {
                        "fiyat": float(fiyat),
                        "metrekare": float(metrekare),
                        "metrekare_fiyat": float(fiyat) / float(metrekare),
                        "imar_durumu": imar_durumu_actual
                    }
                    
                    ilanlar.append(ilan_bilgisi)
                
                except Exception as e:
                    print(f"İlan işlenirken hata oluştu: {e}")
                    continue
            
            # Sonuçları hesapla
            if not ilanlar:
                return {"error": "Uygun ilan bulunamadı"}
            
            toplam_fiyat = sum(ilan["metrekare_fiyat"] for ilan in ilanlar)
            ortalama_fiyat = toplam_fiyat / len(ilanlar)
            
            min_fiyat = min(ilan["metrekare_fiyat"] for ilan in ilanlar)
            max_fiyat = max(ilan["metrekare_fiyat"] for ilan in ilanlar)
            
            return {
                "ortalama_metrekare_fiyat": ortalama_fiyat,
                "min_metrekare_fiyat": min_fiyat,
                "max_metrekare_fiyat": max_fiyat,
                "ilan_sayisi": len(ilanlar),
                "ilanlar": ilanlar
            }
        
        except Exception as e:
            print(f"Arsa fiyatları çekilirken hata oluştu: {e}")
            return {"error": f"Arsa fiyatları çekilirken hata oluştu: {e}"}


class InsaatAlaniHesaplayici:
    """
    TAKS ve KAKS değerlerine göre inşaat alanı hesaplayan sınıf
    """
    
    def __init__(self):
        """
        InsaatAlaniHesaplayici sınıfını başlatır.
        """
        pass
    
    def hesapla(self, arsa_alani, taks, kaks):
        """
        TAKS ve KAKS değerlerine göre inşaat alanı hesaplar.
        
        Args:
            arsa_alani (float): Arsa alanı (m²)
            taks (float): Taban Alanı Katsayısı (0-1 arası)
            kaks (float): Kat Alanı Katsayısı
            
        Returns:
            dict: Hesaplama sonuçları
        """
        try:
            # Değerleri kontrol et
            if arsa_alani <= 0:
                return {"error": "Arsa alanı pozitif bir değer olmalıdır"}
            
            if taks < 0 or taks > 1:
                return {"error": "TAKS değeri 0-1 arasında olmalıdır"}
            
            if kaks < 0:
                return {"error": "KAKS değeri pozitif bir değer olmalıdır"}
            
            # Taban alanı hesapla
            taban_alani = arsa_alani * taks
            
            # Toplam inşaat alanı hesapla
            toplam_insaat_alani = arsa_alani * kaks
            
            # Kat sayısı hesapla (teorik)
            if taban_alani > 0:
                teorik_kat_sayisi = toplam_insaat_alani / taban_alani
                # Tam kat sayısı ve kalan alan
                tam_kat_sayisi = int(teorik_kat_sayisi)
                kalan_alan = (teorik_kat_sayisi - tam_kat_sayisi) * taban_alani
            else:
                teorik_kat_sayisi = 0
                tam_kat_sayisi = 0
                kalan_alan = 0
            
            return {
                "arsa_alani": arsa_alani,
                "taks": taks,
                "kaks": kaks,
                "taban_alani": taban_alani,
                "toplam_insaat_alani": toplam_insaat_alani,
                "teorik_kat_sayisi": teorik_kat_sayisi,
                "tam_kat_sayisi": tam_kat_sayisi,
                "kalan_alan": kalan_alan
            }
        
        except Exception as e:
            print(f"İnşaat alanı hesaplanırken hata oluştu: {e}")
            return {"error": f"İnşaat alanı hesaplanırken hata oluştu: {e}"}
