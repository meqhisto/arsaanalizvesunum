# modules/fiyat_tahmini.py
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib
from sklearn.metrics import mean_squared_error, r2_score
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine # Engine'i buradan import edin
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from scipy import stats # Bu import kullanılıyor mu kontrol edin, eğer kullanılmıyorsa kaldırılabilir.
from typing import Dict, List, Optional, Tuple # Tuple eklendi
import logging
import os

# Logger ayarları
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Logger'ı app.py'deki ana logger ile entegre etmek daha iyi olabilir veya burada bırakılabilir.
# Şimdilik burada bırakıyorum, ama app.py'deki logger'ı kullanmak daha merkezi bir loglama sağlar.
logger = logging.getLogger(__name__)
if not logger.handlers: # Eğer daha önce handler eklenmediyse (örn: app.py'den)
    handler = logging.StreamHandler() # Konsola log bas
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# Model kayıt yolu
MODEL_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_models')
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
DEFAULT_MODEL_PATH = os.path.join(MODEL_SAVE_PATH, 'xgboost_model.joblib')

# Veritabanı URL'si burada tanımlanmış ama FiyatTahminModeli'ne engine olarak verilecek.
# Bu global engine'i FiyatTahminModeli içinde kullanmak yerine, instance'a enjekte etmek daha iyi.
# DATABASE_URL = "mssql+pyodbc://altan:Yxrkt2bb7q8.@46.221.49.106/arsa_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
# engine = create_engine(DATABASE_URL) # Bu global engine'i burada oluşturmak yerine, FiyatTahminModeli'ne dışarıdan verin.

class ModelBase(ABC):
    @abstractmethod
    def train(self, X, y):
        pass
    # predict, save, load metodları da abstract olabilir veya temel implementasyonları olabilir.

class XGBoostModel(ModelBase):
    def __init__(self, n_estimators=100, random_state=42, **kwargs): # Parametreler eklendi
        self.model = XGBRegressor(
            objective='reg:squarederror',
            n_estimators=n_estimators,
            random_state=random_state,
            **kwargs
        )
        self._is_trained = False # Modelin eğitilip eğitilmediğini takip et

    def train(self, X, y):
        if X.empty or y.empty:
            logger.error("Eğitim verisi (X veya y) boş. Model eğitilemiyor.")
            self._is_trained = False
            return
        try:
            self.model.fit(X, y)
            self._is_trained = True
            logger.info("XGBoost modeli başarıyla eğitildi.")
        except Exception as e:
            logger.error(f"XGBoost model eğitimi sırasında hata: {e}", exc_info=True)
            self._is_trained = False


    def predict(self, X):
        if not self._is_trained:
            logger.error("Model eğitilmemiş. Önce train() metodunu çağırın veya modeli yükleyin.")
            return None # Veya hata fırlat
        if X.empty:
            logger.warning("Tahmin için boş DataFrame gönderildi.")
            return np.array([]) # Boş numpy array döndür
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.error(f"XGBoost model tahmini sırasında hata: {e}", exc_info=True)
            return None
    
    def save(self, filepath: str) -> bool:
        if not self._is_trained:
            logger.error("Kaydedilecek eğitilmiş model yok!")
            return False
        try:
            joblib.dump(self.model, filepath)
            logger.info(f"Model başarıyla kaydedildi: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Model kaydetme hatası: {e}", exc_info=True)
            return False
    
    def load(self, filepath: str) -> bool:
        try:
            if os.path.exists(filepath):
                self.model = joblib.load(filepath)
                self._is_trained = True # Model yüklendiği için eğitilmiş kabul edilir
                logger.info(f"Model başarıyla yüklendi: {filepath}")
                return True
            logger.warning(f"Model dosyası bulunamadı: {filepath}")
            self._is_trained = False
            return False
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}", exc_info=True)
            self._is_trained = False
            return False

class FeatureEngineering:
    def __init__(self, training_columns: Optional[List[str]] = None):
        self.training_columns = training_columns # Eğitim sırasında kullanılan sütunlar

    def process(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        processed_df = df.copy()

        # Eksik değerleri işle
        for col in processed_df.columns:
            if processed_df[col].dtype == 'object':
                processed_df[col] = processed_df[col].fillna(processed_df[col].mode()[0] if not processed_df[col].mode().empty else '') # En sık kullanılanla veya boş string ile doldur
            elif pd.api.types.is_numeric_dtype(processed_df[col]):
                processed_df[col] = processed_df[col].fillna(processed_df[col].median() if not processed_df[col].isnull().all() else 0) # Medyanla veya 0 ile doldur
            else: # Diğer tipler (örn: datetime)
                 processed_df[col] = processed_df[col].fillna(0) # Veya uygun bir değer


        # Kategorik değişkenleri one-hot encoding yap
        categorical_cols = ['imar_durumu', 'il', 'ilce', 'mahalle'] # Mahalle de eklendi
        for col in categorical_cols:
            if col in processed_df.columns:
                processed_df = pd.get_dummies(processed_df, columns=[col], prefix=col, dummy_na=False) # dummy_na=False NaN için ayrı sütun oluşturmaz
        
        if is_training:
            self.training_columns = processed_df.columns.tolist()
        elif self.training_columns is not None:
            # Tahmin zamanında, eğitimdeki sütunlarla eşleştir
            # Eksik sütunları 0 ile ekle
            for col in self.training_columns:
                if col not in processed_df.columns:
                    processed_df[col] = 0
            # Eğitimde olmayan fazla sütunları kaldır
            processed_df = processed_df[self.training_columns].copy() # .copy() ile SettingWithCopyWarning önlenir
            # Sütun sıralamasını eğitimdekiyle aynı yap
            processed_df = processed_df.reindex(columns=self.training_columns, fill_value=0)


        return processed_df

class BolgeselVeriAnalizi:
    def __init__(self, engine: Engine): # SQLAlchemy engine alacak
        self.engine = engine

    def _execute_query(self, query_str: str, params: Dict) -> List[Dict]:
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query_str), params)
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows] # _mapping ile dict'e çevir
        except Exception as e:
            logger.error(f"Sorgu çalıştırılırken hata: {e}\nSorgu: {query_str}\nParametreler: {params}", exc_info=True)
            return []

    def bolge_istatistikleri(self, il: str, ilce: str, mahalle: Optional[str] = None) -> Optional[Dict]:
        query_str = """
            SELECT 
                AVG(CAST(fiyat AS FLOAT) / CASE WHEN metrekare = 0 THEN NULL ELSE CAST(metrekare AS FLOAT) END) as ort_birim_fiyat,
                STDEV(CAST(fiyat AS FLOAT) / CASE WHEN metrekare = 0 THEN NULL ELSE CAST(metrekare AS FLOAT) END) as std_birim_fiyat,
                MIN(CAST(fiyat AS FLOAT) / CASE WHEN metrekare = 0 THEN NULL ELSE CAST(metrekare AS FLOAT) END) as min_birim_fiyat,
                MAX(CAST(fiyat AS FLOAT) / CASE WHEN metrekare = 0 THEN NULL ELSE CAST(metrekare AS FLOAT) END) as max_birim_fiyat,
                COUNT(*) as analiz_sayisi,
                AVG(CAST(metrekare AS FLOAT)) as ort_metrekare,
                AVG(CAST(fiyat AS FLOAT)) as ort_fiyat
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND created_at >= :son_tarih
            AND metrekare > 0 AND fiyat > 0 /* Geçerli veriler için */
        """
        params = {
            "il": il,
            "ilce": ilce,
            "son_tarih": datetime.now() - timedelta(days=365*2) # Son 2 yıllık veriler
        }
        if mahalle:
            query_str += " AND mahalle = :mahalle"
            params["mahalle"] = mahalle
        
        results = self._execute_query(query_str, params)
        if results and results[0]:
            result_data = results[0]
            return {
                "ort_birim_fiyat": float(result_data.get("ort_birim_fiyat") or 0),
                "std_birim_fiyat": float(result_data.get("std_birim_fiyat") or 0),
                "min_birim_fiyat": float(result_data.get("min_birim_fiyat") or 0),
                "max_birim_fiyat": float(result_data.get("max_birim_fiyat") or 0),
                "analiz_sayisi": int(result_data.get("analiz_sayisi") or 0),
                "ort_metrekare": float(result_data.get("ort_metrekare") or 0),
                "ort_fiyat": float(result_data.get("ort_fiyat") or 0),
                "guven_skoru": self._hesapla_guven_skoru(int(result_data.get("analiz_sayisi") or 0))
            }
        return None

    def benzer_arsalar(self, arsa_data: Dict) -> List[Dict]:
        # Metrekare ve imar durumu None ise boş liste dön
        if arsa_data.get("metrekare") is None or arsa_data.get("imar_durumu") is None:
            logger.warning("Benzer arsa araması için metrekare veya imar durumu eksik.")
            return []

        query_str = """
            SELECT TOP 5 id, mahalle, metrekare, imar_durumu, fiyat, created_at
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND metrekare > 0 AND fiyat > 0
            AND ABS(CAST(metrekare AS FLOAT) - :metrekare) / :metrekare <= 0.35 /* %35 tolerans */
            AND imar_durumu = :imar_durumu
            AND created_at >= :son_tarih
            ORDER BY ABS(CAST(metrekare AS FLOAT) - :metrekare) ASC, created_at DESC /* En yakın metrekare ve en yeni */
        """
        params = {
            "il": arsa_data["il"],
            "ilce": arsa_data["ilce"],
            "metrekare": float(arsa_data["metrekare"]), # Float'a çevir
            "imar_durumu": arsa_data["imar_durumu"],
            "son_tarih": datetime.now() - timedelta(days=365*2) # Son 2 yıl
        }
        if arsa_data.get("mahalle"): # Mahalle varsa onu da ekle (daha iyi benzerlik için)
            query_str = query_str.replace("ORDER BY", "AND mahalle = :mahalle ORDER BY")
            params["mahalle"] = arsa_data["mahalle"]
            
        return self._execute_query(query_str, params)

    def _hesapla_guven_skoru(self, analiz_sayisi: int) -> float:
        # ... (mevcut kodunuz) ...
        if analiz_sayisi == 0: return 0
        elif analiz_sayisi < 3: return 20 # Eşik değerleri güncellendi
        elif analiz_sayisi < 7: return 45
        elif analiz_sayisi < 15: return 65
        else: return min(95, 65 + (analiz_sayisi - 15) * 1.0) # Daha hızlı artış


# validate_arsa_data fonksiyonu olduğu gibi kalabilir veya FiyatTahminModeli içine alınabilir.

class FiyatTahminModeli:
    def __init__(self, engine: Engine): # SQLAlchemy engine alacak
        self.engine = engine # engine'i sakla
        self.bolgesel_analiz = BolgeselVeriAnalizi(engine) # BolgeselVeriAnalizi'ne de engine'i ver
        self.version = '1.2' 
        self.model_wrapper = XGBoostModel(n_estimators=150, learning_rate=0.05, max_depth=5) # Model parametreleri
        self.feature_engineering = FeatureEngineering()
        
        self._initialize_model()

    def _initialize_model(self):
        """Modeli yükler veya eğitir."""
        model_loaded = self.model_wrapper.load(DEFAULT_MODEL_PATH)
        if not model_loaded:
            logger.info(f"{DEFAULT_MODEL_PATH} bulunamadı, model yeniden eğitilecek.")
            self.model_yeniden_egit() # Yeniden eğitim fonksiyonunu çağır

    def model_yeniden_egit(self, filtre: Optional[Dict] = None) -> bool:
        """Modeli veritabanından veri çekerek yeniden eğitir."""
        logger.info(f"Model yeniden eğitiliyor... Filtre: {filtre}")
        X_train, X_test, y_train, y_test, df_for_features = self.veri_hazirla(filtre)
        
        if X_train is None or X_train.empty or y_train is None or y_train.empty:
            logger.warning("Yeniden eğitim için yeterli veya geçerli veri bulunamadı.")
            return False
        
        if len(X_train) < 10: # Minimum örnek sayısı kontrolü
            logger.warning(f"Modeli eğitmek için yeterli veri bulunamadı (minimum 10 örnek gerekli, bulunan: {len(X_train)}).")
            return False

        # Eğitim verisi için özellik mühendisliğini uygula ve sütunları sakla
        X_train_processed = self.feature_engineering.process(X_train.copy(), is_training=True)
        if X_test is not None and not X_test.empty:
            X_test_processed = self.feature_engineering.process(X_test.copy())
        else:
            X_test_processed = pd.DataFrame() # Boş DataFrame

        if X_train_processed.empty:
            logger.error("Özellik mühendisliği sonrası eğitim verisi (X_train) boş.")
            return False

        logger.info(f"Eğitim için kullanılacak özellikler: {X_train_processed.columns.tolist()}")

        self.model_wrapper.train(X_train_processed, y_train)
        
        if X_test_processed is not None and not X_test_processed.empty and y_test is not None and not y_test.empty:
            try:
                # Test sütunlarını eğitim sütunlarıyla eşleştir
                for col in X_train_processed.columns:
                    if col not in X_test_processed.columns:
                        X_test_processed[col] = 0
                X_test_processed = X_test_processed[X_train_processed.columns]

                mse, r2 = self.model_degerlendir(X_test_processed, y_test)
                if mse is not None and r2 is not None:
                    logger.info(f"Model değerlendirme (yeniden eğitim sonrası) - MSE: {mse:.2f}, R2: {r2:.2f}")
            except Exception as e_eval:
                logger.error(f"Yeniden eğitim sonrası model değerlendirme hatası: {e_eval}")

        # Eğitilmiş modeli kaydet (eğer eğitildiyse)
        if self.model_wrapper._is_trained:
            # Eğitimde kullanılan sütunları da kaydet (veya bir config dosyasına)
            # Bu, tahmin zamanında aynı özellikleri kullanmak için önemli.
            # Örneğin: self.feature_engineering.training_columns ile erişilebilir.
            if self.feature_engineering.training_columns is not None:
                 # Bu sütunları bir yere kaydetmek iyi bir pratik olur. Şimdilik loglayalım.
                 logger.info(f"Model eğitilirken kullanılan sütunlar (kaydedilmeli): {self.feature_engineering.training_columns}")

            self.model_wrapper.save(DEFAULT_MODEL_PATH)
            return True
        return False


    def veri_hazirla(self, filtre: Optional[Dict] = None) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.Series], Optional[pd.Series], Optional[pd.DataFrame]]:
        """
        Veritabanından analiz verilerini çekip özellik mühendisliği olmadan ham X, y ve df döndürür.
        Özellik mühendisliği eğitim ve tahmin adımlarında ayrıca uygulanır.
        """
        query = "SELECT metrekare, fiyat, imar_durumu, il, ilce, mahalle, taks, kaks, bolge_fiyat FROM arsa_analizleri" # taks, kaks eklendi
        params = {}
        
        conditions = ["fiyat IS NOT NULL", "metrekare IS NOT NULL", "metrekare > 0", "fiyat > 1000", "fiyat < 2000000000"] # Temel filtreler

        if filtre:
            for k, v in filtre.items():
                if v is not None: # Sadece None olmayan filtreleri ekle
                    conditions.append(f"{k} = :{k}")
                    params[k] = v
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        try:
            # self.engine kullanarak sorguyu çalıştır
            df = pd.read_sql(query, con=self.engine, params=params)
            
            if df.empty:
                logger.warning("Veri seti (df) sorgu sonucu boş.")
                return None, None, None, None, None
            
            # Fiyatı olmayan veya geçersiz olan satırları çıkar (ekstra kontrol)
            df = df.dropna(subset=['fiyat'])
            df = df[pd.to_numeric(df['fiyat'], errors='coerce').notnull()]
            df['fiyat'] = df['fiyat'].astype(float)

            # Metrekaresi olmayan veya geçersiz olanları çıkar
            df = df.dropna(subset=['metrekare'])
            df = df[pd.to_numeric(df['metrekare'], errors='coerce').notnull()]
            df['metrekare'] = df['metrekare'].astype(float)
            df = df[df['metrekare'] > 0] # Metrekare 0'dan büyük olmalı

            if df.empty:
                logger.warning("Temizlik sonrası veri seti (df) boş.")
                return None, None, None, None, None

            # Hedef değişken (fiyat) ve özellikler (X)
            # Özellik mühendisliği bu aşamada DEĞİL, eğitim/tahmin sırasında yapılacak.
            if 'fiyat' not in df.columns:
                logger.error("Temizlenmiş veri setinde 'fiyat' sütunu bulunamadı!")
                return None, None, None, None, None
                
            X = df.drop('fiyat', axis=1)
            y = df['fiyat']
            
            # Eğitim ve test setlerine ayır
            if len(df) < 5: # Çok az veri varsa test seti oluşturma
                logger.warning(f"Veri sayısı ({len(df)}) test seti oluşturmak için yetersiz. Tüm veri eğitim için kullanılacak.")
                return X, None, y, None, df.copy() # X_test ve y_test None

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            return X_train, X_test, y_train, y_test, df.copy() # df'i de döndür (feature engineering için)
            
        except Exception as e:
            logger.error(f"Veri hazırlanırken hata oluştu: {e}", exc_info=True)
            return None, None, None, None, None

    # egit, tahmin_raporu, model_degerlendir metodları XGBoostModel'e taşındı veya orada kullanılacak.
    # Bu sınıfta bu metodlara doğrudan gerek kalmadı.

    def model_degerlendir(self, X_test: pd.DataFrame, y_test: pd.Series) -> Tuple[Optional[float], Optional[float]]:
        if self.model_wrapper.model is None or not self.model_wrapper._is_trained:
            logger.error("Eğitilmiş model yok, değerlendirme yapılamıyor!")
            return None, None
        if X_test.empty or y_test.empty:
            logger.warning("Değerlendirme için test verisi (X_test veya y_test) boş!")
            return None, None
            
        try:
            # Tahmin zamanı özellik mühendisliği (eğitimdeki sütunlara göre)
            X_test_processed = self.feature_engineering.process(X_test.copy(), is_training=False)
            
            # Eğer X_test_processed boş dönerse (örn: hiç sütun eşleşmezse)
            if X_test_processed.empty and not X_test.empty:
                logger.error("Özellik mühendisliği sonrası X_test_processed boş, ancak X_test dolu. Sütun uyumsuzluğu olabilir.")
                return None, None
            elif X_test_processed.empty and X_test.empty: # Zaten boşsa
                 return None, None


            y_pred = self.model_wrapper.predict(X_test_processed)
            if y_pred is None:
                logger.error("Model tahmini None döndü, değerlendirme yapılamıyor.")
                return None, None

            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            return mse, r2
        except Exception as e:
            logger.error(f"Model değerlendirme sırasında hata: {e}", exc_info=True)
            return None, None

    def tahmin_yap(self, arsa_data: Dict) -> Optional[Dict]:
        """ Arsa için fiyat tahmini yapar """
        if not isinstance(arsa_data, dict):
            logger.error("`arsa_data` bir sözlük olmalıdır.")
            return None

        # Temel zorunlu alanları kontrol et
        required_for_prediction = ['il', 'ilce', 'metrekare', 'imar_durumu']
        if not all(k in arsa_data and arsa_data[k] is not None for k in required_for_prediction):
            logger.error(f"Tahmin için gerekli alanlar eksik veya None: {required_for_prediction}")
            return { # Temel bir yapı dön, en azından bölgesel veri varsa onu gösterir
                "tahmin_fiyat": 0.0, "min_fiyat": 0.0, "max_fiyat": 0.0,
                "bolge_istatistikleri": None, "benzer_arsalar": [],
                "model_tahmini": None, "agirliklar": {}
            }

        # Veri doğrulama (validate_arsa_data fonksiyonunu kullanabilirsiniz)
        # validated_data = validate_arsa_data(arsa_data.copy()) # Eğer bu fonksiyon varsa
        validated_data = arsa_data.copy() # Şimdilik direkt kopyala

        model_tahmini_val = self._model_tahmini_yap(validated_data)
        logger.info(f"Model ham tahmini: {model_tahmini_val}")

        bolge_stats = self.bolgesel_analiz.bolge_istatistikleri(
            validated_data["il"], 
            validated_data["ilce"],
            validated_data.get("mahalle")
        )
        benzer_arsalar_list = self.bolgesel_analiz.benzer_arsalar(validated_data)

        # Ağırlıklandırma ve Nihai Tahmin (Bu kısım çok detaylı, basitleştirilebilir veya olduğu gibi kalabilir)
        # ... (Bir önceki mesajınızdaki ağırlıklandırma ve nihai tahmin mantığı buraya gelecek) ...
        # ÖNEMLİ: Bu kısım için bir önceki mesajınızdaki kodu kullanın, çünkü o daha detaylıydı.
        # Aşağıya o kısmı ekliyorum:

        agirliklar = {"bolge": 0.0, "benzer": 0.0, "model": 0.0}
        tahminler = {"bolge": None, "benzer": None, "model": model_tahmini_val}

        if bolge_stats and bolge_stats.get("analiz_sayisi", 0) > 0:
            ort_birim_fiyat = bolge_stats.get("ort_birim_fiyat")
            metrekare = float(validated_data.get("metrekare", 0)) # float'a çevir ve varsayılan ata
            if ort_birim_fiyat is not None and metrekare > 0:
                tahminler["bolge"] = ort_birim_fiyat * metrekare
                agirliklar["bolge"] = min(0.6, bolge_stats["analiz_sayisi"] / 50.0) # Eşiği düşürdüm
            else:
                logger.warning("Bölgesel tahmin için ort_birim_fiyat veya metrekare eksik/geçersiz.")

        if benzer_arsalar_list:
            gecerli_fiyatlar = [float(a["fiyat"]) for a in benzer_arsalar_list if a.get("fiyat") is not None]
            if gecerli_fiyatlar:
                tahminler["benzer"] = np.median(gecerli_fiyatlar) # Ortalama yerine medyan daha robust olabilir
                agirliklar["benzer"] = min(0.4, len(gecerli_fiyatlar) * 0.08) # Ağırlığı biraz artırdım
            elif tahminler["bolge"] is not None: # Benzer arsa yok ama bölge varsa, benzeri bölgeye eşitle
                tahminler["benzer"] = tahminler["bolge"]
                agirliklar["benzer"] = agirliklar["bolge"] * 0.5 # Bölgenin yarısı kadar ağırlık ver
            else:
                logger.warning("Benzer arsalar için fiyat verisi yok ve bölgesel tahmin de yok.")
        
        if tahminler["model"] is not None:
            # Model ağırlığı, diğerlerinin toplamı 1'i geçmiyorsa kalanını alır, geçerse küçük bir pay alır.
            kalan_agirlik = 1.0 - (agirliklar["bolge"] + agirliklar["benzer"])
            agirliklar["model"] = max(0.05, kalan_agirlik) if kalan_agirlik > 0 else 0.05
        
        # Ağırlıkları normalize et (toplamları 1 olacak şekilde)
        aktif_tahmin_kaynaklari = [k for k, v in tahminler.items() if v is not None and agirliklar[k] > 1e-6]
        toplam_aktif_agirlik = sum(agirliklar[k] for k in aktif_tahmin_kaynaklari)

        nihai_tahmin = 0.0
        if toplam_aktif_agirlik > 1e-6:
            for source in aktif_tahmin_kaynaklari:
                normalized_weight = agirliklar[source] / toplam_aktif_agirlik
                nihai_tahmin += tahminler[source] * normalized_weight
                agirliklar[source] = normalized_weight # Normalize edilmiş ağırlığı sakla
        elif tahminler["model"] is not None: nihai_tahmin = tahminler["model"]; agirliklar["model"] = 1.0
        elif tahminler["bolge"] is not None: nihai_tahmin = tahminler["bolge"]; agirliklar["bolge"] = 1.0
        elif tahminler["benzer"] is not None: nihai_tahmin = tahminler["benzer"]; agirliklar["benzer"] = 1.0
        else: logger.error("Hiçbir kaynaktan geçerli tahmin üretilemedi."); nihai_tahmin = 0.0


        # Güven aralığı
        min_fiyat_tahmini, max_fiyat_tahmini = 0.0, 0.0
        if nihai_tahmin > 0:
            std_sapma_yuzdesi = 0.20 # Varsayılan %20 sapma
            if bolge_stats and bolge_stats.get("std_birim_fiyat") and bolge_stats.get("ort_birim_fiyat") and bolge_stats["ort_birim_fiyat"] > 0:
                # Bölgesel standart sapmayı göreceli olarak kullan
                goreceli_std_sapma = bolge_stats["std_birim_fiyat"] / bolge_stats["ort_birim_fiyat"]
                # Güven skoru ile bu sapmayı ayarla (düşük güven daha geniş aralık)
                guven_faktoru = (100 - bolge_stats.get("guven_skoru", 50)) / 100  # 0 ile 0.5 arası
                std_sapma_yuzdesi = max(0.10, min(0.50, goreceli_std_sapma * (1 + guven_faktoru))) # %10 ile %50 arası sınırla

            sapma_miktari = nihai_tahmin * std_sapma_yuzdesi
            min_fiyat_tahmini = max(0, nihai_tahmin - sapma_miktari)
            max_fiyat_tahmini = nihai_tahmin + sapma_miktari
        
        if nihai_tahmin == 0.0: min_fiyat_tahmini = 0.0; max_fiyat_tahmini = 0.0

        return {
            "tahmin_fiyat": nihai_tahmin,
            "min_fiyat": min_fiyat_tahmini,
            "max_fiyat": max_fiyat_tahmini,
            "bolge_istatistikleri": bolge_stats,
            "benzer_arsalar": benzer_arsalar_list, # Değişken adı düzeltildi
            "model_tahmini": tahminler["model"],
            "agirliklar": agirliklar,
            "tahmin_kaynaklari": tahminler # Hangi tahminlerin kullanıldığını görmek için
        }

    def _model_tahmini_yap(self, arsa_data: Dict) -> Optional[float]:
        try:
            if not self.model_wrapper._is_trained: # _is_trained kontrolü
                logger.warning("Model eğitilmemiş veya yüklenememiş, tahmin yapılamıyor.")
                return None

            # Tahmin için DataFrame hazırla
            input_df_raw = pd.DataFrame([arsa_data])
            
            # Özellik mühendisliği (eğitimdeki sütunlara göre hizala)
            input_df_processed = self.feature_engineering.process(input_df_raw.copy(), is_training=False)

            if input_df_processed.empty:
                 logger.error("Özellik mühendisliği sonrası tahmin için input_df boş.")
                 return None
            
            # Modelin beklediği sütunların varlığını ve sırasını kontrol et
            if self.feature_engineering.training_columns:
                # Eksik sütunları 0 ile ekle
                for col in self.feature_engineering.training_columns:
                    if col not in input_df_processed.columns:
                        input_df_processed[col] = 0
                # Sütun sırasını ve seçimini eğitimdekiyle aynı yap
                try:
                    input_df_processed = input_df_processed[self.feature_engineering.training_columns]
                except KeyError as ke:
                    logger.error(f"Tahmin verisinde eğitimde kullanılan sütunlar eksik/farklı: {ke}. Mevcut sütunlar: {input_df_processed.columns.tolist()}")
                    return None
            else:
                logger.warning("Eğitim sütunları (training_columns) FeatureEngineering içinde tanımlanmamış. Bu, tahminlerin tutarsız olmasına neden olabilir.")
                # Sadece modelin `feature_names_in_` özelliğine güvenebiliriz (eğer model XGBoost ise)
                if hasattr(self.model_wrapper.model, 'feature_names_in_'):
                    model_features = self.model_wrapper.model.feature_names_in_
                    for col in model_features:
                         if col not in input_df_processed.columns:
                            input_df_processed[col] = 0
                    try:
                        input_df_processed = input_df_processed[model_features]
                    except KeyError as ke:
                        logger.error(f"Tahmin verisinde modelin beklediği sütunlar eksik/farklı: {ke}.")
                        return None
                else:
                    logger.error("Modelin beklediği özellik listesi (feature_names_in_) bulunamadı.")
                    return None


            prediction = self.model_wrapper.predict(input_df_processed)
            
            if prediction is not None and len(prediction) > 0:
                pred_val = float(prediction[0])
                # Makul değer kontrolü (validate_arsa_data benzeri)
                if pred_val < 1000: pred_val = 1000.0
                if pred_val > 2000000000: pred_val = 2000000000.0
                return pred_val
            else:
                logger.error("Model tahmini (predict) boş veya None döndü.")
                return None
        except Exception as e:
            logger.error(f"Model tahmini yaparken genel hata: {e}", exc_info=True)
            return None

    # bolge_trend_analizi metodu (içeriği bir önceki mesajınızdaki gibi kalabilir, sadece self.engine kullanmalı)
    def bolge_trend_analizi(self, il: str, ilce: str, ay_sayisi: int = 12) -> Optional[Dict]:
        query_str = """
            SELECT 
                EXTRACT(YEAR FROM created_at) as yil, 
                EXTRACT(MONTH FROM created_at) as ay_no,
                AVG(CAST(fiyat AS FLOAT)/CASE WHEN metrekare = 0 THEN NULL ELSE CAST(metrekare AS FLOAT) END) as ort_birim_fiyat,
                COUNT(*) as islem_sayisi
            FROM arsa_analizleri
            WHERE il = :il 
            AND ilce = :ilce
            AND created_at >= :baslangic_tarih
            AND metrekare > 0 AND fiyat > 0
            GROUP BY EXTRACT(YEAR FROM created_at), EXTRACT(MONTH FROM created_at)
            ORDER BY yil, ay_no
        """
        baslangic = datetime.now() - timedelta(days=30 * ay_sayisi)
        
        params = { "il": il, "ilce": ilce, "baslangic_tarih": baslangic }
        results = self._execute_query(query_str, params)

        if results:
            aylar_str = [f"{int(r['yil'])}-{int(r['ay_no']):02d}" for r in results]
            fiyatlar = [float(r.get('ort_birim_fiyat') or 0.0) for r in results] # get() ile None kontrolü
            islem_sayilari = [int(r.get('islem_sayisi',0)) for r in results] # get() ile None kontrolü
            
            # ... (trend hesaplama mantığınız olduğu gibi kalabilir) ...
            trend_egimi = 0.0; yillik_degisim_orani = 0.0; trend_yonu = "belirsiz"
            if len(fiyatlar) > 1:
                x_indices = np.arange(len(fiyatlar))
                valid_mask = ~np.isnan(fiyatlar) & ~np.isinf(fiyatlar) & (np.array(fiyatlar) > 1e-6)
                fiyatlar_np = np.array(fiyatlar)
                if np.sum(valid_mask) > 1: # En az iki geçerli nokta olmalı
                    z = np.polyfit(x_indices[valid_mask], fiyatlar_np[valid_mask], 1)
                    trend_egimi = z[0]
                    trend_yonu = "artış" if trend_egimi > 1e-3 else ("düşüş" if trend_egimi < -1e-3 else "sabit")
                first_valid_price = next((p for p in fiyatlar if p is not None and p > 1e-6), None)
                last_valid_price = next((p for p in reversed(fiyatlar) if p is not None and p > 1e-6), None)
                if first_valid_price and last_valid_price and first_valid_price > 1e-6:
                    yillik_degisim_orani = ((last_valid_price - first_valid_price) / first_valid_price) * 100
                elif len(fiyatlar) == 1 and fiyatlar[0] > 1e-6 : trend_yonu = "tek veri"
                else: trend_yonu = "veri yetersiz"
            elif len(fiyatlar) == 1 and fiyatlar[0] > 1e-6 : trend_yonu = "tek veri"
            else: trend_yonu = "veri yetersiz"

            return {
                "aylar": aylar_str, "fiyatlar": fiyatlar, "islem_sayilari": islem_sayilari,
                "trend_egimi": trend_egimi, "trend_yonu": trend_yonu,
                "yillik_degisim_orani": yillik_degisim_orani
            }
        return None

# validate_arsa_data fonksiyonu global kalabilir veya bir sınıfa taşınabilir.
def validate_arsa_data(arsa_data: Dict) -> Dict:
    # ... (mevcut kodunuz) ...
    # Bu fonksiyonu FiyatTahminModeli içinde de çağırabilirsiniz.
    # Önemli: Bu fonksiyonun arsa_data'nın kopyası üzerinde çalıştığından emin olun.
    processed_data = arsa_data.copy()
    # Fiyat, metrekare vb. kontrolleri ve düzeltmeleri burada yapın.
    # Örnek:
    if 'fiyat' in processed_data and isinstance(processed_data['fiyat'], (int, float)):
        if processed_data['fiyat'] < 1000: processed_data['fiyat'] = 1000.0
        if processed_data['fiyat'] > 2000000000: processed_data['fiyat'] = 2000000000.0
    if 'metrekare' in processed_data and isinstance(processed_data['metrekare'], (int, float)):
        if processed_data['metrekare'] <=0: processed_data['metrekare'] = 10.0 # Min 10m2
        if processed_data['metrekare'] > 1000000 : processed_data['metrekare'] = 1000000.0
    return processed_data