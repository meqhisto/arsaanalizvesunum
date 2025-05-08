# Makine Öğrenmesi ile Fiyat Tahmini
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib
from sklearn.metrics import mean_squared_error, r2_score
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from typing import Dict, List, Optional
import logging  # Import logging

# Logger ayarları
# Configure logger for basic output if not configured by the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelBase(ABC):
    @abstractmethod
    def train(self, X, y):
        pass


class XGBoostModel(ModelBase):
    def __init__(self): # __init__ ekleyelim
        self.model = None # Modeli başlangıçta None olarak ayarlayalım

    def train(self, X, y):
        self.model = XGBRegressor(objective='reg:squarederror', n_estimators=1000)
        self.model.fit(X, y)

    def predict(self, X): # Kendi predict metodunu ekleyelim
        if self.model is None:
            raise RuntimeError("Model has not been trained yet. Call train() first.")
        return self.model.predict(X)


class FeatureEngineering:
    def process(self, df):
        df = pd.get_dummies(df, columns=['imar_durumu'])
        return df


class BolgeselVeriAnalizi:
    def __init__(self, db_session: Session):
        self.db = db_session

    def bolge_istatistikleri(self, il: str, ilce: str, mahalle: Optional[str] = None) -> Dict:
        """Bölgesel fiyat istatistiklerini hesaplar"""
        query = """
            SELECT 
                AVG(fiyat/metrekare) as ort_birim_fiyat,
                STDEV(fiyat/metrekare) as std_birim_fiyat,
                MIN(fiyat/metrekare) as min_birim_fiyat,
                MAX(fiyat/metrekare) as max_birim_fiyat,
                COUNT(*) as analiz_sayisi,
                AVG(metrekare) as ort_metrekare,
                AVG(fiyat) as ort_fiyat
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND created_at >= :son_tarih
        """
        params = {
            "il": il,
            "ilce": ilce,
            "son_tarih": datetime.now() - timedelta(days=365)  # Son 1 yıllık veriler
        }
        if mahalle:
            query += " AND mahalle = :mahalle"
            params["mahalle"] = mahalle
        result = self.db.execute(text(query), params).fetchone()
        if result:
            return {
                "ort_birim_fiyat": float(result.ort_birim_fiyat or 0),
                "std_birim_fiyat": float(result.std_birim_fiyat or 0),
                "min_birim_fiyat": float(result.min_birim_fiyat or 0),
                "max_birim_fiyat": float(result.max_birim_fiyat or 0),
                "analiz_sayisi": int(result.analiz_sayisi or 0),
                "ort_metrekare": float(result.ort_metrekare or 0),
                "ort_fiyat": float(result.ort_fiyat or 0),
                "guven_skoru": self._hesapla_guven_skoru(result.analiz_sayisi)
            }
        return None

    def benzer_arsalar(self, arsa_data: Dict) -> List[Dict]:
        """Benzer özellikteki arsaları bulur"""
        query = """
            SELECT TOP 10 *
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND ABS(metrekare - :metrekare) / :metrekare <= 0.3
            AND imar_durumu = :imar_durumu
            AND created_at >= :son_tarih
            ORDER BY created_at DESC
        """
        params = {
            "il": arsa_data["il"],
            "ilce": arsa_data["ilce"],
            "metrekare": arsa_data["metrekare"],
            "imar_durumu": arsa_data["imar_durumu"],
            "son_tarih": datetime.now() - timedelta(days=365)
        }
        results = self.db.execute(text(query), params).fetchall()
        return [dict(row._mapping) for row in results]

    def _hesapla_guven_skoru(self, analiz_sayisi: int) -> float:
        """Veri güvenilirlik skorunu hesaplar"""
        if analiz_sayisi == 0:
            return 0
        elif analiz_sayisi < 5:
            return 30
        elif analiz_sayisi < 10:
            return 50
        elif analiz_sayisi < 20:
            return 70
        else:
            return min(90, 70 + (analiz_sayisi - 20) * 0.5)

class FiyatTahminModeli:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.bolgesel_analiz = BolgeselVeriAnalizi(db_session)
        self.version = '1.0'
        self.model_wrapper = self._create_model('xgboost') # Değişken adını değiştirelim karışmasın
        self.feature_engineering = FeatureEngineering()
        # Modeli burada eğitelim (her FiyatTahminModeli örneği için)
        try:
            X_train, X_test, y_train, y_test = self.veri_hazirla() # Test verilerini de alabilirsiniz
            if not X_train.empty and not y_train.empty:
                self.model_wrapper.train(X_train, y_train)
                logger.info("Model FiyatTahminModeli başlatılırken eğitildi.")
            else:
                logger.warning("Modeli eğitmek için yeterli veri bulunamadı. Model eğitilmedi.")
        except Exception as e:
            logger.error(f"Model FiyatTahminModeli başlatılırken eğitilemedi: {e}", exc_info=True)


    def _create_model(self, model_type):
        if model_type == 'xgboost':
            return XGBoostModel()
        # Add more model types...

    def veri_hazirla(self, filtre: dict = None):
        """
        SQLAlchemy ile veritabanından analiz verilerini çekip eğitim seti hazırlar.
        filtre: {'il': 'İstanbul', ...} gibi opsiyonel filtreler
        """
        query = "SELECT metrekare, fiyat, imar_durumu, il, ilce, mahalle, bolge_fiyat FROM arsa_analizleri"
        params = {}
        if filtre:
            conditions = []
            for k, v in filtre.items():
                conditions.append(f"{k} = :{k}")
                params[k] = v
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # SQLAlchemy session'ının bağlı olduğu engine'i kullan
        # self.db bir SQLAlchemy Session nesnesi ise, self.db.bind engine'i verir.
        engine = self.db.bind
        conn = engine.connect() # Engine'den bir bağlantı al
        try:
            # pd.read_sql_query yerine pd.read_sql ve açık bağlantı kullanmayı deneyelim
            df = pd.read_sql(text(query), conn, params=params)
        finally:
            conn.close() # Bağlantıyı her zaman kapat
        
        # Özellik mühendisliği
        df = self.feature_engineering.process(df)
        X = df.drop('fiyat', axis=1)
        y = df['fiyat']
        return train_test_split(X, y, test_size=0.2)

    def egit(self, X_train, y_train):
        self.model.train(X_train, y_train)

    def tahmin_raporu(self, X_test):
        return self.model.model.predict(X_test)

    def model_kaydet(self, dosya_adi):
        joblib.dump(self.model, dosya_adi)

    def model_degerlendir(self, X_test, y_test):
        y_pred = self.model.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        return mse, r2

    def tahmin_yap(self, arsa_data: Dict) -> Dict:
        """
        Arsa için fiyat tahmini yapar
        """
        # Bölgesel istatistikleri al
        bolge_stats = self.bolgesel_analiz.bolge_istatistikleri(
            arsa_data["il"], 
            arsa_data["ilce"],
            arsa_data.get("mahalle")
        )
        # Benzer arsaları bul
        benzer_arsalar = self.bolgesel_analiz.benzer_arsalar(arsa_data)
        # Model tahmini yap
        model_tahmini_val = self._model_tahmini_yap(arsa_data)
        logger.info(f"DEBUG: Raw model_tahmini_val: {model_tahmini_val}")

        # Değişkenleri başlat
        bolge_tahmini = 0.0
        benzer_tahmini = 0.0
        bolge_agirligi = 0.0
        benzer_agirligi = 0.0
        model_agirligi = 0.0
        nihai_tahmin = 0.0
        std_hata = 0.0
        min_fiyat_tahmini = 0.0
        max_fiyat_tahmini = 0.0

        agirliklar = {"bolge": 0.0, "benzer": 0.0, "model": 0.0}
        tahminler = {"bolge": None, "benzer": None, "model": model_tahmini_val}

        # Ağırlıklı ortalama ile nihai tahmin
        if bolge_stats and bolge_stats.get("analiz_sayisi", 0) > 0:
            ort_birim_fiyat = bolge_stats.get("ort_birim_fiyat")
            metrekare = arsa_data.get("metrekare")
            if ort_birim_fiyat is not None and metrekare is not None:
                tahminler["bolge"] = ort_birim_fiyat * metrekare
                agirliklar["bolge"] = min(0.6, bolge_stats["analiz_sayisi"] / 100.0)
            else:
                logger.warning("Bölgesel tahmin için ort_birim_fiyat veya metrekare eksik.")

        if benzer_arsalar:
            gecerli_fiyatlar = [float(a["fiyat"]) for a in benzer_arsalar if a.get("fiyat") is not None]
            if gecerli_fiyatlar:
                tahminler["benzer"] = sum(gecerli_fiyatlar) / len(gecerli_fiyatlar)
                agirliklar["benzer"] = min(0.3, len(benzer_arsalar) * 0.05)
            elif tahminler["bolge"] is not None:
                tahminler["benzer"] = tahminler["bolge"]
                # agirliklar["benzer"] = 0.0 # Gerçek benzer olmadığı için ağırlığı sıfırlayabiliriz
            else:
                logger.warning("Benzer arsalar için fiyat verisi yok ve bölgesel tahmin de yok.")

        if tahminler["model"] is not None:
            kalan_agirlik = 1.0 - (agirliklar["bolge"] + agirliklar["benzer"])
            agirliklar["model"] = max(0.0, kalan_agirlik) if kalan_agirlik > 0 else 0.1

        toplam_agirlik_hesaplanan = sum(agirliklar[k] for k, v in tahminler.items() if v is not None and agirliklar[k] > 0)
        
        weighted_sum = 0.0
        if toplam_agirlik_hesaplanan > 1e-6:
            for source in ["bolge", "benzer", "model"]:
                if tahminler[source] is not None and agirliklar[source] > 0:
                    normalized_weight = agirliklar[source] / toplam_agirlik_hesaplanan
                    weighted_sum += tahminler[source] * normalized_weight
                    agirliklar[source] = normalized_weight 
                else:
                    agirliklar[source] = 0.0
            nihai_tahmin = weighted_sum
        elif tahminler["model"] is not None:
            nihai_tahmin = tahminler["model"]
            agirliklar["model"] = 1.0
        elif tahminler["bolge"] is not None:
            nihai_tahmin = tahminler["bolge"]
            agirliklar["bolge"] = 1.0
        elif tahminler["benzer"] is not None: # Bu durum pek olası değil
            nihai_tahmin = tahminler["benzer"]
            agirliklar["benzer"] = 1.0
        else:
            logger.error("Hiçbir kaynaktan geçerli tahmin üretilemedi.")
            nihai_tahmin = 0.0

        if bolge_stats and bolge_stats.get("std_birim_fiyat") is not None and arsa_data.get("metrekare") is not None:
            std_birim_fiyat = bolge_stats.get("std_birim_fiyat")
            std_hata = max(0.0, std_birim_fiyat * arsa_data["metrekare"])
            scale_val = std_hata if std_hata > 1e-9 else (nihai_tahmin * 0.1 if nihai_tahmin > 0 else 1.0)
            guven_araligi_tuple = stats.norm.interval(0.95, loc=nihai_tahmin, scale=scale_val)
            min_fiyat_tahmini = max(0, guven_araligi_tuple[0])
            max_fiyat_tahmini = guven_araligi_tuple[1]
        else: 
            min_fiyat_tahmini = nihai_tahmin * 0.8
            max_fiyat_tahmini = nihai_tahmin * 1.2
            if nihai_tahmin == 0.0:
                 min_fiyat_tahmini = 0.0
                 max_fiyat_tahmini = 0.0

        return {
            "tahmin_fiyat": nihai_tahmin,
            "min_fiyat": min_fiyat_tahmini,
            "max_fiyat": max_fiyat_tahmini,
            "bolge_istatistikleri": bolge_stats,
            "benzer_arsalar": benzer_arsalar,
            "model_tahmini": tahminler["model"],
            "agirliklar": agirliklar
        }

    def bolge_trend_analizi(self, il: str, ilce: str, ay_sayisi: int = 12) -> Optional[Dict]:
        """
        Bölgedeki fiyat trendlerini analiz eder
        """
        query = """
            SELECT 
                EXTRACT(YEAR FROM created_at) as yil, 
                EXTRACT(MONTH FROM created_at) as ay_no,
                AVG(fiyat/metrekare) as ort_birim_fiyat,
                COUNT(*) as islem_sayisi
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND created_at >= :baslangic_tarih
            GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at)
            ORDER BY yil, ay_no
        """
        baslangic = datetime.now() - timedelta(days=30 * ay_sayisi)
        results = self.db.execute(text(query), {
            "il": il,
            "ilce": ilce,
            "baslangic_tarih": baslangic
        }).fetchall()

        if results:
            aylar = [datetime(int(r.yil), int(r.ay_no), 1) for r in results]
            fiyatlar = [float(r.ort_birim_fiyat or 0.0) for r in results]
            islem_sayilari = [int(r.islem_sayisi) for r in results]
            
            trend_egimi = 0.0
            yillik_degisim_orani = 0.0
            trend_yonu = "belirsiz"

            if len(fiyatlar) > 1:
                x_indices = np.arange(len(fiyatlar))
                # NaN veya sonsuz değerleri filtrele
                valid_mask = ~np.isnan(fiyatlar) & ~np.isinf(fiyatlar)
                
                fiyatlar_np = np.array(fiyatlar) # NumPy array'ine çevir
                
                if np.any(valid_mask) and len(fiyatlar_np[valid_mask]) > 1:
                    z = np.polyfit(x_indices[valid_mask], fiyatlar_np[valid_mask], 1)
                    trend_egimi = z[0]
                    trend_yonu = "artış" if trend_egimi > 1e-3 else ("düşüş" if trend_egimi < -1e-3 else "sabit")

                first_valid_price = next((p for p in fiyatlar if p is not None and p > 1e-6), None)
                last_valid_price = next((p for p in reversed(fiyatlar) if p is not None), None)

                if first_valid_price and last_valid_price:
                    yillik_degisim_orani = ((last_valid_price - first_valid_price) / first_valid_price) * 100
                
            elif len(fiyatlar) == 1:
                 trend_yonu = "veri yetersiz"

            return {
                "aylar": [ay.strftime("%Y-%m") for ay in aylar],
                "fiyatlar": fiyatlar,
                "islem_sayilari": islem_sayilari,
                "trend_egimi": trend_egimi,
                "trend_yonu": trend_yonu,
                "yillik_degisim_orani": yillik_degisim_orani
            }
        logger.info(f"{il}/{ilce} için bölge trend analizi sonucu bulunamadı.")
        return None

    def _model_tahmini_yap(self, arsa_data: Dict) -> Optional[float]:
        """
        Makine öğrenmesi modeli ile tahmin yapar
        """
        try:
            if self.model_wrapper.model is None: # Eğitilmiş modelin varlığını kontrol et
                logger.error("XGBoost modeli eğitilmemiş veya yüklenememiş.")
                # Burada ya modeli eğitmeyi deneyebilir ya da None dönebilirsiniz.
                # Şimdilik None dönelim:
                # Örnek: Acil eğitim (her tahmin için maliyetli olabilir)
                # logger.info("Model eğitilmemiş, şimdi eğitiliyor...")
                # X_train, _, y_train, _ = self.veri_hazirla() # Tüm veriyi eğitim için kullanabiliriz
                # if not X_train.empty:
                #    self.model_wrapper.train(X_train, y_train)
                #    logger.info("Model tahmin öncesinde eğitildi.")
                # else:
                #    logger.error("Modeli eğitmek için veri bulunamadı.")
                #    return None
                return None # Model eğitilmemişse None dön

            input_df = pd.DataFrame([arsa_data])
            # Tahmin için gelen veride modelin eğitildiği tüm sütunların olması gerekir.
            # Eksik sütunlar varsa, bunları ekleyin (genellikle 0 veya ortalama ile doldurulur)
            # Veya FeatureEngineering.process içinde bu işlem yapılmalı.
            # Şu anki FeatureEngineering sadece 'imar_durumu' için get_dummies yapıyor.
            # Eğer eğitim verisinde 'il_Ankara', 'ilce_Çankaya' gibi sütunlar varsa,
            # tahmin verisinde de bunlar olmalı.
            # Bu genellikle eğitim sırasında kullanılan sütun listesini kaydedip,
            # tahmin sırasında bu listeye göre DataFrame'i yeniden indeksleyerek yapılır.

            # Geçici çözüm: Eğer model eğitilirken oluşan dummy sütunlar tahmin input_df'sinde yoksa hata verir.
            # Bu durumu daha sağlam yönetmek için eğitimdeki sütunları bilmek gerekir.
            # Şimdilik, process metodunun gelen veriyi doğru hazırladığını varsayıyoruz.
            input_df = self.feature_engineering.process(input_df)

            prediction = self.model_wrapper.predict(input_df) # Artık XGBoostModel'in kendi predict'ini kullanıyoruz
            if prediction is not None and len(prediction) > 0:
                return float(prediction[0])
            else:
                logger.error("Model prediction was None or empty.")
                return None
        except RuntimeError as r_err: # Modelin eğitilmediği durum
            logger.error(f"Model tahmini sırasında çalışma zamanı hatası: {r_err}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Model tahmini sırasında hata oluştu: {e}", exc_info=True)
            return None
