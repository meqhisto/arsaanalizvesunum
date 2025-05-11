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
import logging
import os

# Logger ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Model kayıt yolu
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_models')
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
DEFAULT_MODEL_PATH = os.path.join(MODEL_SAVE_PATH, 'xgboost_model.joblib')
# filepath: c:\Users\ustad\Desktop\arsaanalizvesunum\modules\fiyat_tahmini.py
DATABASE_URL = "mssql+pyodbc://altan:Yxrkt2bb7q8.@46.221.49.106/arsa_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"  # Replace with your actual database URL
engine = create_engine(DATABASE_URL)
class ModelBase(ABC):
    @abstractmethod
    def train(self, X, y):
        pass


class XGBoostModel(ModelBase):
    def __init__(self):
        self.model = None

    def train(self, X, y):
        self.model = XGBRegressor(objective='reg:squarederror', n_estimators=1000)
        self.model.fit(X, y)

    def predict(self, X):
        if self.model is None:
            raise RuntimeError("Model has not been trained yet. Call train() first.")
        return self.model.predict(X)
    
    def save(self, filepath):
        """Modeli kaydet"""
        if self.model is not None:
            joblib.dump(self.model, filepath)
            logger.info(f"Model başarıyla kaydedildi: {filepath}")
            return True
        logger.error("Kaydedilecek eğitilmiş model yok!")
        return False
    
    def load(self, filepath):
        """Kaydedilmiş modeli yükle"""
        try:
            if os.path.exists(filepath):
                self.model = joblib.load(filepath)
                logger.info(f"Model başarıyla yüklendi: {filepath}")
                return True
            logger.warning(f"Model dosyası bulunamadı: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}", exc_info=True)
            return False


class FeatureEngineering:
    def process(self, df):
        # Eksik değerleri işle
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna('')
            else:
                df[col] = df[col].fillna(0)
                
        # Kategorik değişkenleri one-hot encoding yap
        if 'imar_durumu' in df.columns:
            df = pd.get_dummies(df, columns=['imar_durumu'])
        
        # İl ve ilçe için dummy değişkenler oluştur (eğer bunlar kategorik ise)
        if 'il' in df.columns:
            df = pd.get_dummies(df, columns=['il'], prefix='il')
        if 'ilce' in df.columns:
            df = pd.get_dummies(df, columns=['ilce'], prefix='ilce')
            
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
        
        try:
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
        except Exception as e:
            logger.error(f"Bölge istatistikleri hesaplanırken hata oluştu: {e}", exc_info=True)
        
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
        
        try:
            results = self.db.execute(text(query), params).fetchall()
            return [dict(row._mapping) for row in results]
        except Exception as e:
            logger.error(f"Benzer arsalar bulunurken hata oluştu: {e}", exc_info=True)
            return []

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


def validate_arsa_data(arsa_data: Dict) -> Dict:
    """Arsa verilerinin geçerliliğini doğrula ve düzelt"""
    MAX_FIYAT = 5_000_000_000  # 1 milyar TL - gerçekçi üst sınır
    MIN_FIYAT = 1000  # 1000 TL - gerçekçi alt sınır
    MAX_METREKARE = 1_000_000  # 1 milyon m² - gerçekçi üst sınır
    
    # Derin kopya oluştur, orijinal veriyi değiştirmemek için
    validated_data = arsa_data.copy()
    
    # Fiyat kontrolü
    if 'fiyat' in validated_data and validated_data['fiyat'] is not None:
        if validated_data['fiyat'] > MAX_FIYAT:
            logger.warning(f"Gerçekçi olmayan yüksek fiyat tespit edildi: {validated_data['fiyat']}. "
                          f"Üst sınır olan {MAX_FIYAT} değerine ayarlanıyor.")
            validated_data['fiyat'] = MAX_FIYAT
        elif validated_data['fiyat'] < MIN_FIYAT:
            logger.warning(f"Gerçekçi olmayan düşük fiyat tespit edildi: {validated_data['fiyat']}. "
                          f"Alt sınır olan {MIN_FIYAT} değerine ayarlanıyor.")
            validated_data['fiyat'] = MIN_FIYAT
    
    # Metrekare kontrolü
    if 'metrekare' in validated_data and validated_data['metrekare'] is not None:
        if validated_data['metrekare'] > MAX_METREKARE:
            logger.warning(f"Gerçekçi olmayan metrekare tespit edildi: {validated_data['metrekare']}. "
                          f"Üst sınır olan {MAX_METREKARE} değerine ayarlanıyor.")
            validated_data['metrekare'] = MAX_METREKARE
        elif validated_data['metrekare'] <= 0:
            logger.warning(f"Geçersiz metrekare tespit edildi: {validated_data['metrekare']}. "
                          f"Varsayılan değer 100 m² olarak ayarlanıyor.")
            validated_data['metrekare'] = 100
    
    return validated_data


class FiyatTahminModeli:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.bolgesel_analiz = BolgeselVeriAnalizi(db_session)
        self.version = '1.1'  # Versiyon numarasını güncelledik
        self.model_wrapper = self._create_model('xgboost')
        self.feature_engineering = FeatureEngineering()
        
        # Önce kaydedilmiş modeli yüklemeyi dene
        model_loaded = self.model_wrapper.load(DEFAULT_MODEL_PATH)
        
        # Eğer model yüklenemezse, eğitmeyi dene
        if not model_loaded:
            try:
                X_train, X_test, y_train, y_test = self.veri_hazirla()
                if not X_train.empty and len(X_train) > 10 and not y_train.empty:
                    self.model_wrapper.train(X_train, y_train)
                    logger.info("Model başarıyla eğitildi.")
                    
                    # Eğitilen modeli kaydet
                    self.model_wrapper.save(DEFAULT_MODEL_PATH)
                else:
                    logger.warning("Modeli eğitmek için yeterli veri bulunamadı (minimum 10 örnek gerekli).")
            except Exception as e:
                logger.error(f"Model eğitme sırasında hata oluştu: {e}", exc_info=True)

    def _create_model(self, model_type):
        if model_type == 'xgboost':
            return XGBoostModel()
        # Diğer model tipleri eklenebilir...
        return None

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
        
        # Fiyat validasyonu için WHERE şartı ekle
        if not filtre or "WHERE" not in query:
            query += " WHERE fiyat <= 1000000000 AND fiyat > 1000"  # Gerçekçi fiyat aralığı
        else:
            query += " AND fiyat <= 1000000000 AND fiyat > 1000"
        
        try:
            with engine.connect() as conn:
                df = pd.read_sql(query, con=conn, params=params)           
            # Eksik değerleri ve problematik verileri kontrol et
            if df.empty:
                logger.warning("Veri setimizdeki filtrelere uygun hiç veri bulunamadı.")
                return pd.DataFrame(), pd.DataFrame(), pd.Series(), pd.Series()
                
            # Özellik mühendisliği
            df = self.feature_engineering.process(df)
            
            # 'fiyat' sütununun varlığını kontrol et
            if 'fiyat' not in df.columns:
                logger.error("Veri setinde 'fiyat' sütunu bulunamadı!")
                return pd.DataFrame(), pd.DataFrame(), pd.Series(), pd.Series()
                
            X = df.drop('fiyat', axis=1)
            y = df['fiyat']
            
            return train_test_split(X, y, test_size=0.2, random_state=42)
            
        except Exception as e:
            logger.error(f"Veri hazırlanırken hata oluştu: {e}", exc_info=True)
            return pd.DataFrame(), pd.DataFrame(), pd.Series(), pd.Series()

    def egit(self, X_train, y_train):
        """Modeli eğit"""
        if X_train.empty or y_train.empty:
            logger.error("Eğitim verisi boş, model eğitilemedi!")
            return False
            
        try:
            self.model_wrapper.train(X_train, y_train)
            self.model_wrapper.save(DEFAULT_MODEL_PATH)
            return True
        except Exception as e:
            logger.error(f"Model eğitimi sırasında hata: {e}", exc_info=True)
            return False

    def tahmin_raporu(self, X_test):
        """Test veri seti üzerinde tahmin yap"""
        if self.model_wrapper.model is None:
            logger.error("Eğitilmiş model yok, tahmin yapılamıyor!")
            return None
            
        try:
            return self.model_wrapper.predict(X_test)
        except Exception as e:
            logger.error(f"Tahmin sırasında hata: {e}", exc_info=True)
            return None

    def model_degerlendir(self, X_test, y_test):
        """Model performansını değerlendir"""
        if X_test.empty or y_test.empty:
            logger.warning("Değerlendirme için veri yok!")
            return None, None
            
        if self.model_wrapper.model is None:
            logger.error("Eğitilmiş model yok, değerlendirme yapılamıyor!")
            return None, None
            
        try:
            y_pred = self.model_wrapper.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            return mse, r2
        except Exception as e:
            logger.error(f"Model değerlendirme sırasında hata: {e}", exc_info=True)
            return None, None

    def tahmin_yap(self, arsa_data: Dict) -> Dict:
        """
        Arsa için fiyat tahmini yapar
        """
        # Veri doğrulama
        validated_data = validate_arsa_data(arsa_data)
        
        # Bölgesel istatistikleri al
        bolge_stats = self.bolgesel_analiz.bolge_istatistikleri(
            validated_data["il"], 
            validated_data["ilce"],
            validated_data.get("mahalle")
        )
        
        # Benzer arsaları bul
        benzer_arsalar = self.bolgesel_analiz.benzer_arsalar(validated_data)
        
        # Model tahmini yap
        model_tahmini_val = self._model_tahmini_yap(validated_data)
        logger.info(f"Model tahmini: {model_tahmini_val}")

        # Değişkenleri başlat
        agirliklar = {"bolge": 0.0, "benzer": 0.0, "model": 0.0}
        tahminler = {"bolge": None, "benzer": None, "model": model_tahmini_val}

        # Bölgesel tahmin
        if bolge_stats and bolge_stats.get("analiz_sayisi", 0) > 0:
            ort_birim_fiyat = bolge_stats.get("ort_birim_fiyat")
            metrekare = validated_data.get("metrekare")
            if ort_birim_fiyat is not None and metrekare is not None:
                tahminler["bolge"] = ort_birim_fiyat * metrekare
                agirliklar["bolge"] = min(0.6, bolge_stats["analiz_sayisi"] / 100.0)
            else:
                logger.warning("Bölgesel tahmin için ort_birim_fiyat veya metrekare eksik.")

        # Benzer arsalardan tahmin
        if benzer_arsalar:
            gecerli_fiyatlar = [float(a["fiyat"]) for a in benzer_arsalar if a.get("fiyat") is not None]
            if gecerli_fiyatlar:
                tahminler["benzer"] = sum(gecerli_fiyatlar) / len(gecerli_fiyatlar)
                agirliklar["benzer"] = min(0.3, len(benzer_arsalar) * 0.05)
            elif tahminler["bolge"] is not None:
                tahminler["benzer"] = tahminler["bolge"]
            else:
                logger.warning("Benzer arsalar için fiyat verisi yok ve bölgesel tahmin de yok.")

        # Model tahmini ağırlığı
        if tahminler["model"] is not None:
            kalan_agirlik = 1.0 - (agirliklar["bolge"] + agirliklar["benzer"])
            agirliklar["model"] = max(0.0, kalan_agirlik) if kalan_agirlik > 0 else 0.1

        # Ağırlıkları normalize et
        toplam_agirlik_hesaplanan = sum(agirliklar[k] for k, v in tahminler.items() if v is not None and agirliklar[k] > 0)
        
        # Nihai tahmin hesapla
        nihai_tahmin = 0.0
        if toplam_agirlik_hesaplanan > 1e-6:
            for source in ["bolge", "benzer", "model"]:
                if tahminler[source] is not None and agirliklar[source] > 0:
                    normalized_weight = agirliklar[source] / toplam_agirlik_hesaplanan
                    nihai_tahmin += tahminler[source] * normalized_weight
                    agirliklar[source] = normalized_weight 
                else:
                    agirliklar[source] = 0.0
        elif tahminler["model"] is not None:
            nihai_tahmin = tahminler["model"]
            agirliklar["model"] = 1.0
        elif tahminler["bolge"] is not None:
            nihai_tahmin = tahminler["bolge"]
            agirliklar["bolge"] = 1.0
        elif tahminler["benzer"] is not None:
            nihai_tahmin = tahminler["benzer"]
            agirliklar["benzer"] = 1.0
        else:
            logger.error("Hiçbir kaynaktan geçerli tahmin üretilemedi.")
            nihai_tahmin = 0.0

        # Güven aralığı hesapla
        min_fiyat_tahmini = 0.0
        max_fiyat_tahmini = 0.0
        
        if bolge_stats and bolge_stats.get("std_birim_fiyat") is not None and validated_data.get("metrekare") is not None:
            std_birim_fiyat = bolge_stats.get("std_birim_fiyat")
            std_hata = max(0.0, std_birim_fiyat * validated_data["metrekare"])
            scale_val = std_hata if std_hata > 1e-9 else (nihai_tahmin * 0.1 if nihai_tahmin > 0 else 1.0)
            
            try:
                guven_araligi_tuple = stats.norm.interval(0.95, loc=nihai_tahmin, scale=scale_val)
                min_fiyat_tahmini = max(0, guven_araligi_tuple[0])
                max_fiyat_tahmini = guven_araligi_tuple[1]
            except Exception as e:
                logger.error(f"Güven aralığı hesaplanırken hata: {e}", exc_info=True)
                min_fiyat_tahmini = nihai_tahmin * 0.8
                max_fiyat_tahmini = nihai_tahmin * 1.2
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
        
        try:
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
                    
                    fiyatlar_np = np.array(fiyatlar)
                    
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
        except Exception as e:
            logger.error(f"Trend analizi sırasında hata: {e}", exc_info=True)
            
        return None

    def _model_tahmini_yap(self, arsa_data: Dict) -> Optional[float]:
        """
        Makine öğrenmesi modeli ile tahmin yapar
        """
        try:
            if self.model_wrapper.model is None:
                # Modeli yüklemeyi dene
                model_loaded = self.model_wrapper.load(DEFAULT_MODEL_PATH)
                if not model_loaded:
                    logger.error("XGBoost modeli eğitilmemiş veya yüklenememiş.")
                    return None

            # Tahmin için DataFrame hazırla
            input_df = pd.DataFrame([arsa_data])
            
            # Özellik mühendisliği
            try:
                input_df = self.feature_engineering.process(input_df)
            except Exception as fe:
                logger.error(f"Özellik mühendisliği sırasında hata: {fe}", exc_info=True)
                return None

            # Modelin tahmin yapması için gerekli tüm sütunların var olduğundan emin ol
            # Eğitim verisinden gelen sütun listesini bir dosyada saklayabiliriz
            # Burada basitleştirilmiş bir kontrol ekleyelim
            required_features = ['metrekare']  # En azından metrekare olmalı
            missing_features = [f for f in required_features if f not in input_df.columns]
            
            if missing_features:
                logger.error(f"Tahmin verisinde gerekli sütunlar eksik: {missing_features}")
                return None

            # Tahmin yap
            prediction = self.model_wrapper.predict(input_df)
            
            if prediction is not None and len(prediction) > 0:
                # Makul değer kontrolü
                pred_val = float(prediction[0])
                if pred_val < 0:
                    logger.warning(f"Negatif tahmin değeri: {pred_val}, 0 olarak düzeltiliyor.")
                    pred_val = 0.0
                elif pred_val > 1_000_000_000:  # 1 milyar TL üst sınırı
                    logger.warning(f"Aşırı yüksek tahmin değeri: {pred_val}, 1 milyar TL ile sınırlandırılıyor.")
                    pred_val = 1_000_000_000
                    
                return pred_val
            else:
                logger.error("Model tahmini boş veya None döndü.")
                return None
                
        except RuntimeError as r_err:
            logger.error(f"Model tahmini sırasında çalışma zamanı hatası: {r_err}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Model tahmini sırasında hata oluştu: {e}", exc_info=True)
            return None