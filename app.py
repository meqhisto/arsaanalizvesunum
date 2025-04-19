from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# Arsa sınıfı
class Arsa:
    def __init__(self, form_data):
        self.konum = {
            'il': form_data.get('il'),
            'ilce': form_data.get('ilce'),
            'mahalle': form_data.get('mahalle')
        }
        self.parsel = {
            'ada': form_data.get('ada'),
            'parsel': form_data.get('parsel')
        }
        self.metrekare = float(form_data.get('metrekare', 0))
        imar_durumu = form_data.get('imar_durumu', '')
        self.imar_durumu = imar_durumu.capitalize() if imar_durumu else ''
        self.fiyat = float(form_data.get('fiyat', 0))
        self.taks = float(form_data.get('taks', 0.3))
        self.kaks = float(form_data.get('kaks', 1.5))
        
        # Yeni eklenen alanlar
        self.koordinatlar = form_data.get('koordinatlar')
        self.pafta = form_data.get('pafta')
        self.imar_tipi = self.imar_durumu  # İmar tipini imar durumundan al
        
        # Hesaplamalar
        self.metrekare_fiyat = self.fiyat / self.metrekare if self.metrekare else 0
        self.bolge_fiyat = float(form_data.get('bolge_fiyat', 0))
        self.bolge_karsilastirma = ((self.metrekare_fiyat - self.bolge_fiyat) / self.bolge_fiyat) * 100
        self.potansiyel_getiri = self._hesapla_potansiyel_getiri()
        self.yatirim_suresi = self._hesapla_yatirim_suresi()
        
        # Altyapı bilgileri
        self.altyapi = {
            'yol': 'yol' in form_data.getlist('altyapi[]'),
            'elektrik': 'elektrik' in form_data.getlist('altyapi[]'),
            'su': 'su' in form_data.getlist('altyapi[]'),
            'dogalgaz': 'dogalgaz' in form_data.getlist('altyapi[]'),
            'kanalizasyon': 'kanalizasyon' in form_data.getlist('altyapi[]')
        }
        
        # Ulaşım bilgileri
        self.ulasim = {
            'toplu_tasima_mesafe': '500m'
        }
        
        # Risk analizi
        self.risk_puani = self._hesapla_risk_puani()
        self.risk_aciklamasi = self._risk_aciklamasi()
        
        # SWOT Analizi
        def parse_swot_data(data):
            try:
                return json.loads(data) if data else []
            except json.JSONDecodeError:
                return []

        self.swot = {
            'strengths': parse_swot_data(form_data.get('strengths')),
            'weaknesses': parse_swot_data(form_data.get('weaknesses')),
            'opportunities': parse_swot_data(form_data.get('opportunities')),
            'threats': parse_swot_data(form_data.get('threats'))
        }

        # Debug için SWOT verilerini yazdır
        print("SWOT Verileri:", self.swot)
        
        # Projeksiyon hesaplamaları
        self.projeksiyon = self._hesapla_projeksiyon()
        
        # Yatırım önerileri
        self.yatirim_onerileri = self._yatirim_onerileri()
        
        # İnşaat hesaplamaları
        self.insaat_hesaplama = self._insaat_hesapla()

    def _hesapla_potansiyel_getiri(self):
        # Basit bir getiri hesaplama örneği
        return 8.5

    def _hesapla_yatirim_suresi(self):
        # Basit bir yatırım süresi hesaplama örneği
        return 3

    def _hesapla_risk_puani(self):
        # Risk puanı hesaplama örneği
        return 2

    def _risk_aciklamasi(self):
        return "Düşük riskli yatırım alanı"

    def _hesapla_projeksiyon(self):
        return {
            'yil_1': self.fiyat * 1.15,
            'yil_3': self.fiyat * 1.45,
            'yil_5': self.fiyat * 1.85
        }

    def _yatirim_onerileri(self):
        return [
            "Kısa vadede yatırım için uygun",
            "Bölgedeki gelişim projeleri değer artışını destekliyor",
            "İmar durumu avantajlı konumda"
        ]

    def _insaat_hesapla(self):
        taban_alani = self.metrekare * self.taks
        toplam_insaat_alani = self.metrekare * self.kaks
        teorik_kat_sayisi = self.kaks / self.taks if self.taks else 0
        
        return {
            'taban_alani': taban_alani,
            'toplam_insaat_alani': toplam_insaat_alani,
            'teorik_kat_sayisi': teorik_kat_sayisi,
            'tam_kat_sayisi': int(teorik_kat_sayisi)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        arsa = Arsa(request.form)
        file_id = str(uuid.uuid4())
        # Burada verileri geçici olarak saklayabilirsiniz
        return render_template('sonuc.html', arsa=arsa, file_id=file_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate/<format>/<file_id>')
def generate(format, file_id):
    # Sunum oluşturma fonksiyonları buraya gelecek
    return jsonify({'status': 'not implemented yet'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
