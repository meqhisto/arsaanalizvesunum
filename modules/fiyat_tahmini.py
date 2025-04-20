# Makine Öğrenmesi ile Fiyat Tahmini
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import joblib

class FiyatTahminModeli:
    def __init__(self):
        self.model = XGBRegressor(objective='reg:squarederror', n_estimators=1000)
        
    def veri_hazirla(self, dosya_yolu):
        df = pd.read_csv(dosya_yolu)
        # Özellik mühendisliği
        df = pd.get_dummies(df, columns=['imar_tipi', 'bolge'])
        X = df.drop('fiyat', axis=1)
        y = df['fiyat']
        return train_test_split(X, y, test_size=0.2)
    
    def egit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        
    def tahmin_raporu(self, X_test):
        return self.model.predict(X_test)
    
    def model_kaydet(self, dosya_adi):
        joblib.dump(self.model, dosya_adi)

# Kullanım Örneği
model = FiyatTahminModeli()
X_train, X_test, y_train, y_test = model.veri_hazirla('arsa_verileri.csv')
model.egit(X_train, y_train)
tahminler = model.tahmin_raporu(X_test)
model.model_kaydet('akilli_fiyat_modeli.pkl')