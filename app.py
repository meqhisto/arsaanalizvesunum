from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import sqlite3
from functools import wraps
import json  # Bu satırı ekleyin
from docx import Document
from docx.shared import Inches
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pptx import Presentation
from pptx.util import Inches, Pt
import os
from pathlib import Path
from modules.analiz import ArsaAnalizci  # Import ekleyelim
from modules.document_generator import DocumentGenerator
from decimal import Decimal



app = Flask(__name__)
app.config['SECRET_KEY'] = 'sizin_gizli_anahtariniz'

# Jinja2 template engine'ine datetime modülünü ekle
app.jinja_env.globals.update(datetime=datetime)

# MySQL Veritabanı Ayarları (localhost:3306, kullanıcı=root, şifre boş)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/arsa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

BASE_DIR = Path(__file__).resolve().parent
PRESENTATIONS_DIR = BASE_DIR / 'static' / 'presentations'
if not PRESENTATIONS_DIR.exists():
    PRESENTATIONS_DIR.mkdir(parents=True)

# --- Kullanıcı Modeli ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ArsaAnaliz(db.Model):
    __tablename__ = 'arsa_analizleri'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    il = db.Column(db.String(50), nullable=False)
    ilce = db.Column(db.String(50), nullable=False)
    mahalle = db.Column(db.String(100), nullable=False)
    ada = db.Column(db.String(20))
    parsel = db.Column(db.String(20))
    koordinatlar = db.Column(db.String(100))
    pafta = db.Column(db.String(50))
    metrekare = db.Column(db.Numeric(10,2), nullable=False)
    imar_durumu = db.Column(db.String(50))
    taks = db.Column(db.Numeric(4,2))
    kaks = db.Column(db.Numeric(4,2))
    fiyat = db.Column(db.Numeric(15,2), nullable=False)
    bolge_fiyat = db.Column(db.Numeric(15,2))
    altyapi = db.Column(db.JSON)
    swot_analizi = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BolgeDagilimi(db.Model):
    __tablename__ = 'bolge_dagilimi'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Kullanıcı ID'si eklendi
    il = db.Column(db.String(50), nullable=False)
    analiz_sayisi = db.Column(db.Integer, default=0)
    toplam_deger = db.Column(db.Numeric(15,2), default=0)
    son_guncelleme = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişki tanımlama
    user = db.relationship('User', backref=db.backref('bolge_dagilimlari', lazy=True))

class YatirimPerformansi(db.Model):
    __tablename__ = 'yatirim_performansi'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Kullanıcı ID'si eklendi
    ay = db.Column(db.String(20), nullable=False)
    yil = db.Column(db.Integer, nullable=False)
    toplam_deger = db.Column(db.Numeric(15,2), default=0)
    analiz_sayisi = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişki tanımlama
    user = db.relationship('User', backref=db.backref('yatirim_performanslari', lazy=True))

class DashboardStats(db.Model):
    __tablename__ = 'dashboard_stats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Kullanıcı ID'si eklendi
    toplam_analiz = db.Column(db.Integer, default=0)
    aktif_projeler = db.Column(db.Integer, default=0)
    toplam_deger = db.Column(db.Numeric(15, 2), default=0.00)
    ortalama_roi = db.Column(db.Numeric(5, 2), default=0.00)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişki tanımlama
    user = db.relationship('User', backref=db.backref('dashboard_stats', lazy=True))

    def __repr__(self):
        return f"<DashboardStats(toplam_analiz={self.toplam_analiz}, aktif_projeler={self.aktif_projeler}, toplam_deger={self.toplam_deger}, ortalama_roi={self.ortalama_roi})>"

# Arsa sınıfı
class Arsa:
    def __init__(self, form_data):
        self.form_data = form_data

        # Convert numeric values with safety checks
        try:
            # Get raw values
            raw_metrekare = form_data.get('metrekare', '0')
            raw_fiyat = form_data.get('fiyat', '0')
            raw_bolge_fiyat = form_data.get('bolge_fiyat', '0')
            raw_taks = form_data.get('taks', '0.3')
            raw_kaks = form_data.get('kaks', '1.5')

            # Clean and convert
            self.metrekare = float(str(raw_metrekare).replace(',', '').strip())
            self.fiyat = float(str(raw_fiyat).replace(',', '').strip())
            self.bolge_fiyat = float(str(raw_bolge_fiyat).replace(',', '').strip())
            self.taks = float(str(raw_taks).replace(',', '').strip())
            self.kaks = float(str(raw_kaks).replace(',', '').strip())

        except (ValueError, TypeError) as e:
            print(f"Numeric conversion error: {e}")
            # Set default values
            self.metrekare = 0.0
            self.fiyat = 0.0
            self.bolge_fiyat = 0.0
            self.taks = 0.3
            self.kaks = 1.5

        # Calculate derived values with safety checks
        try:
            self.metrekare_fiyat = self.fiyat / self.metrekare if self.metrekare > 0 else 0
        except ZeroDivisionError:
            print("Zero division error in metrekare_fiyat calculation")
            self.metrekare_fiyat = 0

        try:
            if self.bolge_fiyat > 0:
                self.bolge_karsilastirma = ((self.metrekare_fiyat - self.bolge_fiyat) / self.bolge_fiyat) * 100
            else:
                self.bolge_karsilastirma = 0
        except ZeroDivisionError:
            print("Zero division error in bolge_karsilastirma calculation")
            self.bolge_karsilastirma = 0

        self.konum = {
            'il': self.form_data.get('il', [''])[0] if isinstance(self.form_data.get('il'), list) else self.form_data.get('il', ''),
            'ilce': self.form_data.get('ilce', [''])[0] if isinstance(self.form_data.get('ilce'), list) else self.form_data.get('ilce', ''),
            'mahalle': self.form_data.get('mahalle', [''])[0] if isinstance(self.form_data.get('mahalle'), list) else self.form_data.get('mahalle', '')
        }
        
        self.parsel = {
            'ada': self.form_data.get('ada', [''])[0] if isinstance(self.form_data.get('ada'), list) else self.form_data.get('ada', ''),
            'parsel': self.form_data.get('parsel', [''])[0] if isinstance(self.form_data.get('parsel'), list) else self.form_data.get('parsel', '')
        }
        
        imar_durumu = self.form_data.get('imar_durumu', [''])[0] if isinstance(self.form_data.get('imar_durumu'), list) else self.form_data.get('imar_durumu', '')
        self.imar_durumu = imar_durumu.capitalize() if imar_durumu else ''

        # Yeni eklenen alanlar
        self.koordinatlar = self.form_data.get('koordinatlar')
        self.pafta = self.form_data.get('pafta')
        self.imar_tipi = self.imar_durumu  # İmar tipini imar durumundan al

        # Hesaplamalar
        self.potansiyel_getiri = self._hesapla_potansiyel_getiri()
        self.yatirim_suresi = self._hesapla_yatirim_suresi()

        # Altyapı bilgileri
        altyapi_list = self.form_data.get('altyapi[]', []) if isinstance(self.form_data.get('altyapi[]'), list) else [self.form_data.get('altyapi[]', [])]
        self.altyapi = {
            'yol': 'yol' in altyapi_list,
            'elektrik': 'elektrik' in altyapi_list,
            'su': 'su' in altyapi_list,
            'dogalgaz': 'dogalgaz' in altyapi_list,
            'kanalizasyon': 'kanalizasyon' in altyapi_list
        }

        # Ulaşım bilgileri
        self.ulasim = {'toplu_tasima_mesafe': '500m'}

        # Risk analizi
        self.risk_puani = self._hesapla_risk_puani()
        self.risk_aciklamasi = self._risk_aciklamasi()

        # SWOT Analizi
        def parse_swot_data(data):
            if isinstance(data, list):
                return data
            elif isinstance(data, str):
                try:
                    return json.loads(data) if data else []
                except json.JSONDecodeError:
                    return [data] if data else []
            return []

        self.swot = {
            'strengths': parse_swot_data(self.form_data.get('strengths', [])),
            'weaknesses': parse_swot_data(self.form_data.get('weaknesses', [])),
            'opportunities': parse_swot_data(self.form_data.get('opportunities', [])),
            'threats': parse_swot_data(self.form_data.get('threats', []))
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

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Lütfen önce giriş yapın', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        try:
            print("\n=== Login Debug Info ===")
            print(f"Login attempt for email: {email}")
            
            user = User.query.filter_by(email=email).first()
            print(f"User found: {user is not None}")
            
            if user:
                print(f"User ID: {user.id}")
                print(f"Stored hash: {user.password_hash}")
                is_valid = user.check_password(password)
                print(f"Password verification result: {is_valid}")
                
                if is_valid:
                    session['user_id'] = user.id
                    session['email'] = user.email
                    flash('Başarıyla giriş yaptınız!', 'success')
                    return redirect(url_for('index'))
            
            flash('Geçersiz e-posta veya şifre!', 'danger')
            return redirect(url_for('login'))
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('Giriş işlemi sırasında bir hata oluştu!', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

# Çıkış yapma route'u
@app.route('/logout')
def logout():
    session.clear()
    flash('Başarıyla çıkış yaptınız', 'info')
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))  # Kullanıcı giriş yaptıysa index.html'e yönlendir
    return redirect(url_for('login'))  # Kullanıcı giriş yapmadıysa login.html'e yönlendir

@app.route('/index')
@login_required
def index():
    user_id = session['user_id']
    
    # Kullanıcının kendi istatistiklerini getir
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = DashboardStats(user_id=user_id)
        db.session.add(stats)
        db.session.commit()

    # Kullanıcının kendi bölge dağılımlarını getir
    bolge_dagilimlari = BolgeDagilimi.query.filter_by(user_id=user_id).all()
    
    # Kullanıcının kendi yatırım performansını getir
    yatirim_performanslari = YatirimPerformansi.query.filter_by(user_id=user_id)\
        .order_by(YatirimPerformansi.yil, YatirimPerformansi.ay).all()

    # Bölge dağılımı için labels ve data
    bolge_labels = [b.il for b in bolge_dagilimlari]
    bolge_data = [b.analiz_sayisi for b in bolge_dagilimlari]

    # Yatırım performansı için labels ve data
    perf_labels = [f"{yp.ay} {yp.yil}" for yp in yatirim_performanslari]
    perf_data = [float(yp.toplam_deger) for yp in yatirim_performanslari]

    return render_template(
        'index.html',
        stats=stats,
        bolge_dagilimlari=bolge_dagilimlari,
        yatirim_performanslari=yatirim_performanslari,
        bolge_labels=bolge_labels,
        bolge_data=bolge_data,
        perf_labels=perf_labels,
        perf_data=perf_data
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            if User.query.filter_by(email=email).first():
                flash('Bu e-posta zaten kayıtlı.', 'danger')
                return redirect(url_for('register'))
            
            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Kayıt başarılı. Lütfen giriş yapın.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {str(e)}")
            db.session.rollback()
            flash('Kayıt sırasında bir hata oluştu!', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    try:
        user_id = session['user_id']
        form_data = request.form.to_dict(flat=True)
        print("Raw form data:", form_data)

        # Convert numeric values before object creation
        try:
            # Clean and convert numeric values
            metrekare = float(str(form_data.get('metrekare', '0')).replace(',', '').strip())
            fiyat = float(str(form_data.get('fiyat', '0')).replace(',', '').strip())
            bolge_fiyat = float(str(form_data.get('bolge_fiyat', '0')).replace(',', '').strip())
            taks = float(str(form_data.get('taks', '0.3')).replace(',', '').strip())
            kaks = float(str(form_data.get('kaks', '1.5')).replace(',', '').strip())

            # Update form data with converted values
            form_data.update({
                'metrekare': metrekare,
                'fiyat': fiyat,
                'bolge_fiyat': bolge_fiyat,
                'taks': taks,
                'kaks': kaks
            })

        except (ValueError, TypeError) as e:
            print(f"Numeric conversion error: {e}")
            return jsonify({'error': 'Lütfen sayısal değerleri doğru formatta giriniz.'}), 400

        # Create Arsa object with converted values
        arsa = Arsa(form_data)

        # Process SWOT data
        swot_data = {}
        for key in ['strengths', 'weaknesses', 'opportunities', 'threats']:
            try:
                value = form_data.get(key, '[]')
                swot_data[key] = json.loads(value) if value else []
            except json.JSONDecodeError:
                print(f"JSON decode error for {key}: {value}")
                swot_data[key] = []

        # Create new ArsaAnaliz object
        yeni_analiz = ArsaAnaliz(
            user_id=user_id,
            il=form_data.get('il', ''),
            ilce=form_data.get('ilce', ''),
            mahalle=form_data.get('mahalle', ''),
            ada=form_data.get('ada', ''),
            parsel=form_data.get('parsel', ''),
            koordinatlar=form_data.get('koordinatlar', ''),
            pafta=form_data.get('pafta', ''),
            metrekare=Decimal(str(metrekare)),
            imar_durumu=form_data.get('imar_durumu', ''),
            taks=Decimal(str(taks)),
            kaks=Decimal(str(kaks)),
            fiyat=Decimal(str(fiyat)),
            bolge_fiyat=Decimal(str(bolge_fiyat)),
            altyapi=json.dumps(request.form.getlist('altyapi[]')),
            swot_analizi=json.dumps(swot_data)
        )

        # Veritabanına kaydet
        db.session.add(yeni_analiz)
        
        # Bölge istatistiklerini güncelle
        bolge = BolgeDagilimi.query.filter_by(
            user_id=user_id,
            il=form_data.get('il')
        ).first()
        
        fiyat_decimal = Decimal(str(form_data.get('fiyat', 0)))
        
        if bolge:
            bolge.analiz_sayisi += 1
            bolge.toplam_deger += fiyat_decimal
        else:
            yeni_bolge = BolgeDagilimi(
                user_id=user_id,
                il=form_data.get('il'),
                analiz_sayisi=1,
                toplam_deger=fiyat_decimal
            )
            db.session.add(yeni_bolge)

        # Dashboard istatistiklerini güncelle
        stats = DashboardStats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = DashboardStats(user_id=user_id)
            db.session.add(stats)
        
        stats.toplam_analiz += 1
        stats.toplam_deger += fiyat_decimal
        # Ortalama ROI float kalabilir, Numeric ise Decimal'e çevirin
        try:
            stats.ortalama_roi = Decimal(str(form_data.get('potansiyel_getiri', 0)))
        except Exception:
            stats.ortalama_roi = Decimal('0')

        # Değişiklikleri kaydet
        db.session.commit()

        # ArsaAnalizci ile analiz yap
        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et({
            'metrekare': form_data.get('metrekare', 0),
            'fiyat': form_data.get('fiyat', 0),
            'bolge_fiyat': form_data.get('bolge_fiyat', 0),
            'taks': form_data.get('taks', 0.3),
            'kaks': form_data.get('kaks', 1.5),
            'imar_durumu': form_data.get('imar_durumu', ''),
            'altyapi': form_data.get('altyapi[]', []),
            'konum': {
                'il': form_data.get('il', ''),
                'ilce': form_data.get('ilce', ''),
                'mahalle': form_data.get('mahalle', '')
            }
        })
        
        # Özet analizi al
        ozet = analizci.ozetle(analiz_sonuclari)
        
        # Session'a kaydet
        session['arsa_data'] = form_data
        session['analiz_sonuclari'] = analiz_sonuclari
        session['analiz_ozeti'] = ozet
        
        # Arsa nesnesini oluştur
        arsa = Arsa(form_data)
        
        # UUID oluştur
        file_id = str(uuid.uuid4())
        
        # Sonuç sayfasına yönlendir
        return render_template('sonuc.html',
                            arsa=arsa,
                            analiz=analiz_sonuclari,
                            ozet=ozet,
                            file_id=file_id)

    except Exception as e:
        # Hata durumunda rollback yap
        db.session.rollback()
        print(f"Submit error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate/<format>/<file_id>')
def generate(format, file_id):
    try:
        arsa_data = session.get('arsa_data')
        analiz_ozeti = session.get('analiz_ozeti')
        
        if not arsa_data or not analiz_ozeti:
            return jsonify({'error': 'Analiz verisi bulunamadı'}), 400

        doc_generator = DocumentGenerator(
            arsa_data,
            analiz_ozeti,
            file_id,
            PRESENTATIONS_DIR
        )

        if format == 'word':
            filename = doc_generator.create_word()
        elif format == 'pdf':
            filename = doc_generator.create_pdf()
        else:
            return jsonify({'error': 'Geçersiz format'}), 400

        return send_file(
            filename,
            as_attachment=True,
            download_name=f'arsa_analiz_{file_id}.{format}'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)