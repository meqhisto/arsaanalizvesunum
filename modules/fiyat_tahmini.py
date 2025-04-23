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
from typing import Dict, Optional  # Import Optional

# Logger ayarları
logger = logging.getLogger(__name__)  # Get a logger


class ModelBase(ABC):
    @abstractmethod
    def train(self, X, y):
        pass


class XGBoostModel(ModelBase):
    def train(self, X, y):
        self.model = XGBRegressor(objective='reg:squarederror', n_estimators=1000)
        self.model.fit(X, y)


class FeatureEngineering:
    def process(self, df):
        # Feature engineering logic
        df = pd.get_dummies(df, columns=['imar_tipi', 'bolge'])
        return df


class BolgeselVeriAnalizi:
    def __init__(self, db_session: Session):
        self.db = db_session

    def bolge_istatistikleri(self, il: str, ilce: str, mahalle: Optional[str] = None) -> Dict:
        """Bölgesel fiyat istatistiklerini hesaplar"""
        query = """
            SELECT 
                AVG(fiyat/metrekare) as ort_birim_fiyat,
                STDDEV(fiyat/metrekare) as std_birim_fiyat,
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
            SELECT *
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND ABS(metrekare - :metrekare) / :metrekare <= 0.3
            AND imar_durumu = :imar_durumu
            AND created_at >= :son_tarih
            ORDER BY created_at DESC
            LIMIT 10
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
        self.model = self._create_model('xgboost')
        self.feature_engineering = FeatureEngineering()

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
        df = pd.read_sql(text(query), self.db.bind, params=params)
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
        model_tahmini = self._model_tahmini_yap(arsa_data)
        print(f"DEBUG: Raw model_tahmini: {model_tahmini}")  # Debug log ekle

        # Değişkenleri başlat
        bolge_tahmini = 0.0
        benzer_tahmini = 0.0
        bolge_agirligi = 0.0
        benzer_agirligi = 0.0
        model_agirligi = 0.0
        nihai_tahmin = 0.0
        std_hata = 0.0
        guven_araligi = (0.0, 0.0)

        # Ağırlıklı ortalama ile nihai tahmin
        if bolge_stats and bolge_stats["analiz_sayisi"] > 0:
            # Bölgesel tahmin (None kontrolü yap)
            if bolge_stats.get("ort_birim_fiyat") is not None and arsa_data.get("metrekare") is not None:
                bolge_tahmini = bolge_stats["ort_birim_fiyat"] * arsa_data["metrekare"]
            else:
                print("WARN: bolge_tahmini calculation skipped due to None value.")
                bolge_tahmini = 0.0  # Varsayılan değer ata

            bolge_agirligi = min(0.6, bolge_stats["analiz_sayisi"] / 100)
            # Benzer arsalar ağırlığı
            benzer_agirligi = min(0.3, len(benzer_arsalar) * 0.05)
            # Model ağırlığı
            model_agirligi = max(0.0, 1.0 - (bolge_agirligi + benzer_agirligi))

            # Benzer arsalardan tahmin
            gecerli_fiyatlar = [float(a["fiyat"]) for a in benzer_arsalar if a.get("fiyat") is not None]
            if gecerli_fiyatlar:
                benzer_tahmini = sum(gecerli_fiyatlar) / len(gecerli_fiyatlar)
            else:
                benzer_tahmini = bolge_tahmini  # Geri dönüş için bölge tahmini kullan
                benzer_agirligi = 0.0

            # Nihai tahmin hesaplama
            if model_tahmini is not None:
                try:
                    model_tahmini_float = float(model_tahmini)
                    nihai_tahmin = (
                        bolge_tahmini * bolge_agirligi +
                        benzer_tahmini * benzer_agirligi +
                        model_tahmini_float * model_agirligi
                    )
                    # Toplam ağırlığı kontrol et
                    total_weight = bolge_agirligi + benzer_agirligi + model_agirligi
                    if total_weight > 0:
                        nihai_tahmin /= total_weight
                except (TypeError, ValueError):
                    print("ERROR: model_tahmini could not be converted to float. Excluding from final estimate.")
                    model_tahmini = None
                    model_agirligi = 0.0
                    total_weight = bolge_agirligi + benzer_agirligi
                    if total_weight > 0:
                        nihai_tahmin = (
                            bolge_tahmini * bolge_agirligi +
                            benzer_tahmini * benzer_agirligi
                        ) / total_weight
                    else:
                        nihai_tahmin = 0.0
            else:
                # model_tahmini yoksa, sadece bölge ve benzer arsalar kullan
                total_weight = bolge_agirligi + benzer_agirligi
                if total_weight > 0:
                    nihai_tahmin = (
                        bolge_tahmini * bolge_agirligi +
                        benzer_tahmini * benzer_agirligi
                    ) / total_weight
                else:
                    nihai_tahmin = 0.0

            # Güven aralığı hesaplama
            std_birim_fiyat = bolge_stats.get("std_birim_fiyat")
            if std_birim_fiyat is not None and arsa_data.get("metrekare") is not None:
                std_hata = max(0.0, std_birim_fiyat * arsa_data["metrekare"])
                scale_val = std_hata if std_hata > 1e-9 else 1.0
                guven_araligi = stats.norm.interval(0.95, loc=nihai_tahmin, scale=scale_val)
            else:
                guven_araligi = (nihai_tahmin * 0.8, nihai_tahmin * 1.2)

        elif model_tahmini is not None:
            # Sadece model tahmini varsa
            try:
                nihai_tahmin = float(model_tahmini)
                guven_araligi = (nihai_tahmin * 0.8, nihai_tahmin * 1.2)
                model_agirligi = 1.0
            except (TypeError, ValueError):
                print("ERROR: model_tahmini could not be converted to float. No estimate possible.")
                nihai_tahmin = 0.0
                guven_araligi = (0.0, 0.0)
        else:
            print("ERROR: No estimation data available.")
            nihai_tahmin = 0.0
            guven_araligi = (0.0, 0.0)

        return {
            "tahmin_fiyat": nihai_tahmin,
            "min_fiyat": max(0, guven_araligi[0]),
            "max_fiyat": guven_araligi[1],
            "bolge_istatistikleri": bolge_stats,
            "benzer_arsalar": benzer_arsalar,
            "model_tahmini": model_tahmini,
            "agirliklar": {
                "bolge": bolge_agirligi if bolge_stats else 0,
                "benzer": benzer_agirligi if benzer_arsalar else 0,
                "model": model_agirligi
            }
        }

    def bolge_trend_analizi(self, il: str, ilce: str, ay_sayisi: int = 12) -> Dict:
        """
        Bölgedeki fiyat trendlerini analiz eder
        """
        query = """
            SELECT 
                DATE_TRUNC('month', created_at) as ay,
                AVG(fiyat/metrekare) as ort_birim_fiyat,
                COUNT(*) as islem_sayisi
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND created_at >= :baslangic_tarih
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY ay
        """
        baslangic = datetime.now() - timedelta(days=30 * ay_sayisi)
        results = self.db.execute(text(query), {
            "il": il,
            "ilce": ilce,
            "baslangic_tarih": baslangic
        }).fetchall()
        if results:
            aylar = [r.ay for r in results]
            fiyatlar = [float(r.ort_birim_fiyat or 0.0) for r in results]
            islem_sayilari = [int(r.islem_sayisi) for r in results]
            # Trend analizi
            z = np.polyfit(range(len(fiyatlar)), fiyatlar, 1)
            trend = z[0]  # Eğim
            # Yıllık değişim oranı
            yillik_degisim = 0
            if len(fiyatlar) > 1:
                yillik_degisim = (fiyatlar[-1] - fiyatlar[0]) / fiyatlar[0] * 100
            else:
                yillik_degisim = 0
            return {
                "aylar": aylar,
                "fiyatlar": fiyatlar,
                "islem_sayilari": islem_sayilari,
                "trend": trend,
                "trend_yonu": "artış" if trend > 0 else "düşüş",
                "yillik_degisim": (fiyatlar[-1] - fiyatlar[0]) / fiyatlar[0] * 100 if len(fiyatlar) > 1 else 0
            }
        return None

    def _model_tahmini_yap(self, arsa_data: Dict) -> float:
        """
        Makine öğrenmesi modeli ile tahmin yapar
        """
        try:
            input_df = pd.DataFrame([arsa_data])
            input_df = self.feature_engineering.process(input_df)
            prediction = self.model.model.predict(input_df)[0]
            return float(prediction)  # Kesinlikle float dön
        except Exception as e:
            print(f"Model tahmini sırasında hata oluştu: {e}")
            return 0.0  # Varsayılan bir değer döndür