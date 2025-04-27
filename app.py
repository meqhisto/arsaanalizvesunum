# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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
import sys
from modules.document_generator import DocumentGenerator
from decimal import Decimal
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler
from modules.fiyat_tahmini import FiyatTahminModeli # <<< YENİ EKLEME
import secrets



import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sizin_gizli_anahtariniz'
application = app  # Flask uygulamasını application olarak ayarlayın

# Jinja2 template engine'ine datetime modülünü ekle
app.jinja_env.globals.update(datetime=datetime)

# MySQL Veritabanı Ayarları
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:altan@localhost:3306/arsa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800

db = SQLAlchemy(app)

BASE_DIR = Path(__file__).resolve().parent
PRESENTATIONS_DIR = BASE_DIR / 'static' / 'presentations'
if not PRESENTATIONS_DIR.exists():
    PRESENTATIONS_DIR.mkdir(parents=True)

# Medya yükleme ayarları
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Log ayarları
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# --- Kullanıcı Modeli ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)

    # New profile fields
    ad = db.Column(db.String(50))
    soyad = db.Column(db.String(50))
    telefon = db.Column(db.String(20))
    firma = db.Column(db.String(100))
    unvan = db.Column(db.String(100))
    adres = db.Column(db.Text)
    profil_foto = db.Column(db.String(200))  # Path to profile photo
    is_active = db.Column(db.Boolean, default=True)
    son_giris = db.Column(db.DateTime)
    failed_attempts = db.Column(db.Integer, default=0)
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)

    def set_password(self, password):
        try:
            print(f"Setting password for user {self.email}")  # Debug log
            self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            print("Password hash generated successfully")  # Debug log
        except Exception as e:
            print(f"Error setting password: {str(e)}")  # Debug log
            raise

    def check_password(self, password):
        try:
            print(f"Checking password for user {self.email}")  # Debug log
            print(f"Stored hash: {self.password_hash}")  # Debug log
            result = check_password_hash(self.password_hash, password)
            print(f"Password check result: {result}")  # Debug log
            return result
        except Exception as e:
            print(f"Error checking password: {str(e)}")  # Debug log
            import traceback
            print("Full traceback:")  # Debug log
            print(traceback.format_exc())  # Debug log
            return False

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
    __table_args__ = (
        db.Index('ix_user_il', 'user_id', 'il'),
        db.Index('ix_created_at', 'created_at'),
    )

    # User ilişkisini ekle
    user = db.relationship('User', backref=db.backref('analizler', lazy=True))

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

# Medya modeli
class AnalizMedya(db.Model):
    __tablename__ = 'analiz_medya'
    id = db.Column(db.Integer, primary_key=True)
    analiz_id = db.Column(db.Integer, db.ForeignKey('arsa_analizleri.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'image' veya 'video'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    analiz = db.relationship('ArsaAnaliz', backref=db.backref('medyalar', lazy=True))

# Portfolio modeli (User ve ArsaAnaliz modellerinden sonra ekleyin)
class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    visibility = db.Column(db.String(20), default='public')  # 'public' veya 'private'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = db.relationship('User', backref=db.backref('portfolios', lazy=True))
    analizler = db.relationship('ArsaAnaliz', secondary='portfolio_arsalar', lazy='dynamic',
                              backref=db.backref('portfolios', lazy=True))

# Portfolio-Arsa ilişki tablosu
portfolio_arsalar = db.Table('portfolio_arsalar',
    db.Column('portfolio_id', db.Integer, db.ForeignKey('portfolios.id'), primary_key=True),
    db.Column('arsa_id', db.Integer, db.ForeignKey('arsa_analizleri.id'), primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

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
        # print("SWOT Verileri:", self.swot) # İsteğe bağlı olarak açılabilir

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

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Sunucu hatası: {str(e)}", exc_info=True)
    return "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            remember = 'remember' in request.form

            print(f"Login attempt - Email: {email}")  # Debug log

            if not email or not password:
                print("Email or password is missing")  # Debug log
                flash('E-posta ve şifre alanları zorunludur!', 'danger')
                return redirect(url_for('login'))

            user = User.query.filter_by(email=email).first()
            print(f"User found: {user is not None}")  # Debug log

            if user:
                print(f"User ID: {user.id}, Email: {user.email}")  # Debug log
                print(f"Password hash: {user.password_hash}")  # Debug log
                
                try:
                    is_valid = user.check_password(password)
                    print(f"Password check result: {is_valid}")  # Debug log
                except Exception as e:
                    print(f"Password check error: {str(e)}")  # Debug log
                    flash('Şifre doğrulama hatası!', 'danger')
                    return redirect(url_for('login'))

                if is_valid:
                    session['user_id'] = user.id
                    session['email'] = user.email
                    
                    user.failed_attempts = 0
                    user.son_giris = datetime.utcnow()
                    
                    if remember:
                        session.permanent = True
                        app.permanent_session_lifetime = timedelta(days=30)
                    
                    db.session.commit()
                    print("Login successful")  # Debug log
                    flash('Başarıyla giriş yaptınız!', 'success')
                    return redirect(url_for('index'))
                else:
                    user.failed_attempts = (user.failed_attempts or 0) + 1
                    user.son_giris = datetime.utcnow()
                    db.session.commit()
                    
                    if user.failed_attempts >= 5:
                        flash('Çok fazla başarısız giriş denemesi. Lütfen 5 dakika bekleyin.', 'danger')
                    else:
                        flash('Geçersiz e-posta veya şifre!', 'danger')
            else:
                print("User not found")  # Debug log
                flash('Geçersiz e-posta veya şifre!', 'danger')

            return redirect(url_for('login'))

        except Exception as e:
            print(f"Login error details: {str(e)}")  # Debug log
            import traceback
            print("Full traceback:")  # Debug log
            print(traceback.format_exc())  # Debug log
            flash('Giriş işlemi sırasında bir hata oluştu!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Şifremi unuttum sayfası
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Şifre sıfırlama token'ı oluştur
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            # E-posta gönderme işlemi burada yapılacak
            # Şimdilik sadece token'ı log'a yazalım
            print(f"Password reset token for {email}: {token}")
            
            flash('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.', 'success')
        else:
            flash('Bu e-posta adresi ile kayıtlı bir hesap bulunamadı.', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

# Şifre sıfırlama sayfası
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expires < datetime.utcnow():
        flash('Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır!', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        
        flash('Şifreniz başarıyla güncellendi. Lütfen yeni şifrenizle giriş yapın.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

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


@app.route('/change-password', methods=['POST'], endpoint='change_password') # endpoint adını belirtiyoruz
@login_required # Kullanıcının giriş yapmış olması gerekebilir
def change_password_route(): # Fonksiyon adı farklı olabilir ama endpoint önemlidir
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Mevcut kullanıcıyı al (örneğin session'dan ID ile)
        user_id = session.get('user_id')
        user = User.query.get(user_id) # User modelinize göre ayarlayın

        if not user or not check_password_hash(user.password_hash, current_password): # password_hash, modelinizdeki hash'lenmiş şifre alanı olmalı
            flash('Mevcut şifreniz yanlış!', 'danger')
            return redirect(url_for('profile')) # Profil sayfasına geri yönlendir

        if new_password != confirm_password:
            flash('Yeni şifreler eşleşmiyor!', 'danger')
            return redirect(url_for('profile'))

        # Yeni şifreyi hash'le ve veritabanında güncelle
        user.password_hash = generate_password_hash(new_password)
        db.session.commit() # Veritabanı işlemini kaydet

        flash('Şifreniz başarıyla güncellendi.', 'success')
        return redirect(url_for('profile'))

    # POST dışındaki istekler için (genelde buraya gelinmemeli)
    return redirect(url_for('profile'))

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
    bolge_data = [float(b.toplam_deger) for b in bolge_dagilimlari]

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
        try:
            # Şifre doğrulama kontrolü
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')
            
            if password != password_confirm:
                flash('Şifreler eşleşmiyor!', 'danger')
                return redirect(url_for('register'))
            
            if len(password) < 6:
                flash('Şifre en az 6 karakter olmalıdır!', 'danger')
                return redirect(url_for('register'))

            # E-posta kontrolü
            if User.query.filter_by(email=request.form.get('email')).first():
                flash('Bu e-posta adresi zaten kayıtlı!', 'danger')
                return redirect(url_for('register'))

            # Yeni kullanıcı oluştur
            user = User(
                email=request.form.get('email'),
                ad=request.form.get('ad'),
                soyad=request.form.get('soyad'),
                telefon=request.form.get('telefon'),
                firma=request.form.get('firma'),
                unvan=request.form.get('unvan'),
                adres=request.form.get('adres'),
                is_active=True
            )
            
            # Şifreyi ayarla
            user.set_password(password)

            # Veritabanına kaydet
            db.session.add(user)
            db.session.commit()

            flash('Kayıt başarılı! Lütfen giriş yapın.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Kayıt sırasında bir hata oluştu: {str(e)}', 'danger')
            app.logger.error(f'Registration error: {str(e)}')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    try:
        user_id = session['user_id']
        form_data = request.form.to_dict(flat=True)

        # Altyapı verilerini özel olarak al
        altyapi_list = request.form.getlist('altyapi[]')
        form_data['altyapi[]'] = altyapi_list  # form_data'ya ekle

        print("Raw form data:", form_data)
        print("Altyapı verileri:", altyapi_list)

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
        # arsa = Arsa(form_data) # Bu satır veritabanı kaydından sonra olmalı

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
            altyapi=json.dumps(altyapi_list),  # altyapi_list'i direkt kullan
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

        # --- DEĞİŞİKLİK BAŞLANGICI ---
        # ID'nin atanmasını garantilemek için flush yap
        db.session.flush()
        # Yeni oluşturulan analizin ID'sini al
        analiz_id_yeni = yeni_analiz.id
        print(f"DEBUG: Yeni analiz ID'si: {analiz_id_yeni}") # Debug için

        # Yeni ID'yi form_data'ya ekle (session'a kaydetmeden önce)
        form_data['id'] = analiz_id_yeni
        # --- DEĞİŞİKLİK SONU ---

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

        # Session'a kaydet (artık 'id' içeriyor)
        session['arsa_data'] = form_data
        session['analiz_sonuclari'] = analiz_sonuclari
        session['analiz_ozeti'] = ozet
        print(f"DEBUG: Session'a kaydedilen arsa_data: {session['arsa_data']}") # Debug için

        # Arsa nesnesini oluştur (artık ID'yi de içerebilir)
        arsa = Arsa(form_data)

        # UUID oluştur (dosya adı için)
        file_id = str(uuid.uuid4())

        # Kullanıcı bilgilerini al
        user = User.query.get(session['user_id'])

        # Sonuç sayfasına yönlendir
        return render_template('sonuc.html',
                            arsa=arsa,
                            analiz=analiz_sonuclari,
                            ozet=ozet,
                            file_id=file_id,
                            user=user)  # Kullanıcı bilgilerini ekle

    except Exception as e:
        # Hata durumunda rollback yap
        db.session.rollback()
        print(f"Submit error: {str(e)}")
        import traceback
        traceback.print_exc() # Hatanın tam izini yazdır
        return jsonify({'error': str(e)}), 500

# app.py içinde /generate fonksiyonu

@app.route('/generate/<format>/<file_id>')
@login_required
def generate(format, file_id):
    try:
        arsa_data = session.get('arsa_data')
        analiz_ozeti = session.get('analiz_ozeti')
        
        if not arsa_data or not analiz_ozeti:
            flash('Analiz verisi bulunamadı veya oturum süresi doldu.', 'warning')
            return redirect(url_for('index'))

        # Analize ait kullanıcı bilgilerini veritabanından al
        analiz = ArsaAnaliz.query.get(arsa_data['id'])
        user = User.query.get(analiz.user_id)
        profile_info = {
            'ad': user.ad,
            'soyad': user.soyad,
            'email': user.email,
            'telefon': user.telefon,
            'firma': user.firma,
            'unvan': user.unvan,
            'adres': user.adres,
            'profil_foto': user.profil_foto,
            'created_at': analiz.created_at
        }

        print(f"DEBUG [Generate]: Kullanılacak arsa_data: {arsa_data}", flush=True) # Flush eklendi
        print(f"DEBUG [Generate]: Kullanılacak analiz_ozeti: {analiz_ozeti}", flush=True) # Flush eklendi

        # URL parametrelerinden rapor ayarlarını al
        theme = request.args.get('theme', 'classic')
        color_scheme = request.args.get('color_scheme', 'blue')
        sections = request.args.get('sections', '').split(',')

        # Ayarları DocumentGenerator'a gönder
        doc_generator = DocumentGenerator(
            arsa_data,
            analiz_ozeti,
            file_id,
            PRESENTATIONS_DIR,
            profile_info=profile_info,
            settings={
                'theme': theme,
                'color_scheme': color_scheme,
                'sections': sections
            }
        )

        filename = None # Başlangıç değeri
        download_name = None # Başlangıç değeri

        if format == 'word':
            print("DEBUG [Generate]: doc_generator.create_word() çağrılacak...", flush=True)
            filename = doc_generator.create_word()
            if filename and os.path.exists(filename):
                print(f"DEBUG [Generate]: Word dosyası bulundu: {filename}", flush=True)
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=f'arsa_analiz_{file_id}.docx'
                )
            else:
                print(f"HATA [Generate]: Word dosyası oluşturulamadı veya bulunamadı: {filename}", flush=True)
                flash('Word dosyası oluşturulamadı.', 'danger')
                return redirect(url_for('analiz_detay', analiz_id=file_id))

        elif format == 'pdf':
             # --- YENİ LOG ---
            print("DEBUG [Generate]: doc_generator.create_pdf() çağrılacak...", flush=True)
            filename = doc_generator.create_pdf()
            download_name = f'arsa_analiz_{file_id}.pdf'
             # --- YENİ LOG ---
            print(f"DEBUG [Generate]: create_pdf() tamamlandı. Dosya: {filename}", flush=True)
        else:
            print(f"UYARI [Generate]: Geçersiz format istendi: {format}", flush=True)
            return jsonify({'error': 'Geçersiz format'}), 400

        # --- YENİ LOG ---
        if filename and os.path.exists(filename):
             print(f"DEBUG [Generate]: send_file çağrılacak. Dosya: {filename}", flush=True)
             return send_file(
                filename,
                as_attachment=True,
                download_name=download_name
             )
        else:
             print(f"HATA [Generate]: Oluşturulan dosya bulunamadı veya geçersiz! Dosya: {filename}", flush=True)
             flash('Rapor dosyası oluşturulamadı veya bulunamadı.', 'danger')
             return redirect(request.referrer or url_for('index'))


    except Exception as e:
        print(f"HATA [Generate]: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        flash('Rapor oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('analiz_detay', analiz_id=file_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        try:
            user.ad = request.form.get('ad')
            user.soyad = request.form.get('soyad')
            user.telefon = request.form.get('telefon')
            user.firma = request.form.get('firma')
            user.unvan = request.form.get('unvan')
            user.adres = request.form.get('adres')

            # Handle profile photo upload
            if 'profil_foto' in request.files:
                file = request.files['profil_foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Kullanıcıya özel bir alt klasör oluştur (isteğe bağlı ama önerilir)
                    user_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', str(user.id))
                    os.makedirs(user_upload_dir, exist_ok=True)
                    filepath = os.path.join(user_upload_dir, filename)
                    file.save(filepath)
                    # Veritabanına göreceli yolu kaydet
                    relative_path = '/'.join(['profiles', str(user.id), filename])
                    user.profil_foto = relative_path

            db.session.commit()
            flash('Profil başarıyla güncellendi!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            flash('Profil güncellenirken bir hata oluştu!', 'danger')
            print(f"Profile update error: {str(e)}")

    return render_template('profile.html', user=user)

@app.route('/analiz/<int:analiz_id>')
@login_required
def analiz_detay(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        # Kullanıcı bilgilerini getir
        user = User.query.get(analiz.user_id)

        # print(f"DEBUG: Session user_id: {session.get('user_id')}, Analiz user_id: {analiz.user_id}")  # Debug log
        if analiz.user_id != session['user_id']:
            # print("DEBUG: Permission denied for analiz_detay")  # Debug log
            flash('Bu analizi görüntüleme yetkiniz yok.', 'danger')
            return redirect(url_for('analizler'))

        # JSON verilerini dönüştür
        altyapi = json.loads(analiz.altyapi) if isinstance(analiz.altyapi, str) else analiz.altyapi
        swot_analizi = json.loads(analiz.swot_analizi) if isinstance(analiz.swot_analizi, str) else analiz.swot_analizi

        # Tüm sayısal değerleri güvenli şekilde float'a çevir
        def safe_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return 0.0

        metrekare = safe_float(analiz.metrekare)
        fiyat = safe_float(analiz.fiyat)
        bolge_fiyat = safe_float(analiz.bolge_fiyat)
        taks = safe_float(analiz.taks)
        kaks = safe_float(analiz.kaks)

        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et({
            'metrekare': metrekare,
            'fiyat': fiyat,
            'bolge_fiyat': bolge_fiyat,
            'taks': taks,
            'kaks': kaks,
            'imar_durumu': analiz.imar_durumu,
            'altyapi': altyapi,
            'konum': {
                'il': analiz.il,
                'ilce': analiz.ilce,
                'mahalle': analiz.mahalle
            }
        })
        ozet = analizci.ozetle(analiz_sonuclari)

        # --- PDF/Word için session'a analiz verisi yükle ---
        # Bu kısım önemli: Analiz detay sayfasından rapor oluşturulacaksa,
        # session'daki verinin güncel analiz verisi olduğundan emin olmalıyız.
        session['arsa_data'] = {
            'id': analiz.id, # <<< ÖNEMLİ: Analiz ID'sini ekle
            'il': analiz.il,
            'ilce': analiz.ilce,
            'mahalle': analiz.mahalle,
            'ada': analiz.ada,
            'parsel': analiz.parsel,
            'koordinatlar': analiz.koordinatlar,
            'pafta': analiz.pafta,
            'metrekare': float(metrekare),
            'imar_durumu': analiz.imar_durumu,
            'taks': float(taks),
            'kaks': float(kaks),
            'fiyat': float(fiyat),
            'bolge_fiyat': float(bolge_fiyat),
            'altyapi[]': altyapi, # Anahtar adını DocumentGenerator'ın beklediği gibi yapalım
            # SWOT alanları
            'strengths': swot_analizi.get('strengths', []),
            'weaknesses': swot_analizi.get('weaknesses', []),
            'opportunities': swot_analizi.get('opportunities', []),
            'threats': swot_analizi.get('threats', [])
        }
        session['analiz_ozeti'] = ozet
        print(f"DEBUG [Analiz Detay]: Session'a kaydedilen arsa_data: {session['arsa_data']}") # Debug için
        
        tahmin_sonucu = None
        try:
            # Fiyat tahmin modelini başlat
            tahmin_modeli = FiyatTahminModeli(db.session)

            # Tahmin için gerekli veriyi hazırla
            prediction_input_data = {
                "il": analiz.il,
                "ilce": analiz.ilce,
                "mahalle": analiz.mahalle,
                "metrekare": metrekare,
                "imar_durumu": analiz.imar_durumu,
                # Modelin eğitildiği diğer özellikler varsa buraya ekleyin
                # Örneğin:
                 "taks": taks,
                 "kaks": kaks,
                 "bolge_fiyat": bolge_fiyat,
                 "altyapi": altyapi, # Model altyapıyı kullanıyorsa
            }

            # Tahmini yap
            tahmin_sonucu = tahmin_modeli.tahmin_yap(prediction_input_data)
            print(f"DEBUG [Analiz Detay]: Fiyat tahmini sonucu: {tahmin_sonucu}")

        except Exception as e:
            app.logger.error(f"Fiyat tahmini sırasında hata oluştu: {e}", exc_info=True)
            flash('Fiyat tahmini yapılırken bir sorun oluştu.', 'warning')
        # --- YENİ: Fiyat Tahmini Entegrasyonu Sonu ---
        
        # Medya dosyalarını getir
        medyalar = AnalizMedya.query.filter_by(analiz_id=analiz_id).order_by(AnalizMedya.uploaded_at).all()

        # UUID oluştur (dosya adı için, detay sayfasında da gerekebilir)
        file_id = str(uuid.uuid4())

        return render_template(
            'analiz_detay.html',
            analiz=analiz,
            altyapi=altyapi,
            swot=swot_analizi,
            sonuc=analiz_sonuclari,
            ozet=ozet,
            user=user,  # Kullanıcı bilgilerini template'e gönder
            medyalar=medyalar, # Medya dosyalarını template'e gönder
            file_id=file_id, # Rapor oluşturma linkleri için file_id gönder
            tahmin=tahmin_sonucu 
        )

    except Exception as e:
        import traceback
        print("=== HATA DETAYLARI (analiz_detay) ===")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {e}")
        print("Traceback:")
        traceback.print_exc()
        print("--- Analiz edilen veri ---")
        try:
            print(f"analiz.id: {analiz_id}") # analiz_id'yi yazdır
            # Diğer analiz detaylarını yazdırmaya çalış (hata alabilir)
            # print(f"analiz.il: {getattr(analiz, 'il', None)}")
            # ...
        except Exception as inner_e:
            print(f"Ek veri yazılırken hata: {inner_e}")
        print("--- Çözüm Önerisi ---")
        print("Lütfen analiz kaydındaki tüm sayısal alanların (metrekare, fiyat, bolge_fiyat, taks, kaks) boş veya None olmadığından emin olun.")
        print("Veritabanında eksik veya hatalı veri varsa düzeltin. Gerekirse analiz kaydını silip tekrar oluşturun.")
        flash('Analiz görüntülenirken bir hata oluştu. Detaylar için sunucu loglarını kontrol edin.', 'danger')
        flash('Analiz görüntülenirken bir hata oluştu.', 'danger')
        return redirect(url_for('analizler'))

@app.route('/analizler')
@login_required
def analizler():
    user_id = session['user_id']

    # Tüm illeri al (filtreleme için)
    iller = db.session.query(ArsaAnaliz.il)\
        .filter_by(user_id=user_id)\
        .distinct()\
        .order_by(ArsaAnaliz.il)\
        .all()
    iller = [il[0] for il in iller]

    # Analizleri al
    analizler = ArsaAnaliz.query.filter_by(user_id=user_id)\
        .order_by(ArsaAnaliz.created_at.desc()).all()

    # Ay/yıl gruplandırması
    grouped_analizler = {}
    for analiz in analizler:
        ay_isimleri = {
            1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
            5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
            9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
        }
        key = f"{ay_isimleri[analiz.created_at.month]} {analiz.created_at.year}"
        if key not in grouped_analizler:
            grouped_analizler[key] = []
        grouped_analizler[key].append(analiz)

    return render_template('analizler.html',
                         grouped_analizler=grouped_analizler,
                         total_count=len(analizler),
                         iller=iller)

@app.route('/analiz/sil/<int:analiz_id>', methods=['POST'])
@login_required
def analiz_sil(analiz_id):
    try:
        # Analizi bul
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)

        # Kullanıcının yetkisi var mı kontrol et
        if analiz.user_id != session['user_id']:
            flash('Bu analizi silme yetkiniz yok.', 'danger')
            return redirect(url_for('analizler'))

        # İstatistikleri güncelle (Decimal kullanarak)
        stats = DashboardStats.query.filter_by(user_id=session['user_id']).first()
        if stats:
            stats.toplam_analiz = max(0, stats.toplam_analiz - 1) # Negatife düşmesini engelle
            stats.toplam_deger = max(Decimal('0.00'), stats.toplam_deger - (analiz.fiyat or Decimal('0.00')))

        # Bölge istatistiklerini güncelle (Decimal kullanarak)
        bolge = BolgeDagilimi.query.filter_by(
            user_id=session['user_id'],
            il=analiz.il
        ).first()
        if bolge:
            bolge.analiz_sayisi = max(0, bolge.analiz_sayisi - 1)
            bolge.toplam_deger = max(Decimal('0.00'), bolge.toplam_deger - (analiz.fiyat or Decimal('0.00')))

            # Eğer bölgede başka analiz kalmadıysa bölgeyi sil
            if bolge.analiz_sayisi <= 0:
                db.session.delete(bolge)

        # İlişkili medya dosyalarını sil
        medyalar = AnalizMedya.query.filter_by(analiz_id=analiz_id).all()
        for medya in medyalar:
            try:
                # Dosya yolunu oluştur (medya.filename analiz_id/dosyaadi şeklinde olmalı)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], medya.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"DEBUG: Silinen medya dosyası: {filepath}")
                else:
                    print(f"DEBUG: Silinecek medya dosyası bulunamadı: {filepath}")
                db.session.delete(medya)
            except Exception as e:
                print(f"Medya dosyası silinirken hata ({medya.filename}): {e}")
                # Hata olsa bile devam et, veritabanı kaydını silmeye çalış

        # Analizle ilişkili upload klasörünü sil (içi boşsa)
        analiz_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(analiz_id))
        try:
            if os.path.exists(analiz_folder) and not os.listdir(analiz_folder):
                os.rmdir(analiz_folder)
                print(f"DEBUG: Boş analiz klasörü silindi: {analiz_folder}")
        except Exception as e:
            print(f"Analiz klasörü silinirken hata ({analiz_folder}): {e}")


        # Analizi sil
        db.session.delete(analiz)
        db.session.commit()

        flash('Analiz ve ilişkili medyalar başarıyla silindi.', 'success')
        return redirect(url_for('analizler'))

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting analysis: {str(e)}")
        flash('Analiz silinirken bir hata oluştu.', 'danger')
        return redirect(url_for('analizler'))

@app.route('/analiz/<int:analiz_id>/medya_yukle', methods=['POST'])
@login_required
def medya_yukle(analiz_id):
    # Önce analizin kullanıcıya ait olup olmadığını kontrol et
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != session['user_id']:
        flash('Bu analize medya yükleme yetkiniz yok.', 'danger')
        return redirect(url_for('analizler'))

    if 'medya' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analiz_detay', analiz_id=analiz_id))
    file = request.files['medya']
    if file.filename == '':
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analiz_detay', analiz_id=analiz_id))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        medya_type = 'image' if ext in {'jpg', 'jpeg', 'png', 'gif'} else 'video'

        # Analize özel klasör oluştur
        analiz_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(analiz_id))
        os.makedirs(analiz_folder, exist_ok=True)
        filepath = os.path.join(analiz_folder, filename)

        # Dosya boyutunu kontrol et
        # file.seek(0, os.SEEK_END)
        # file_length = file.tell()
        # file.seek(0) # Dosya işaretçisini başa al
        # if file_length > app.config['MAX_CONTENT_LENGTH']:
        #     flash(f'Dosya boyutu çok büyük (Maksimum {app.config["MAX_CONTENT_LENGTH"] / 1024 / 1024:.1f} MB).', 'danger')
        #     return redirect(url_for('analiz_detay', analiz_id=analiz_id))

        try:
            file.save(filepath)
            # Veritabanına kaydet (dosya adını analiz ID'si ile birlikte kaydet)
            db_filename = f"{analiz_id}/{filename}"
            medya = AnalizMedya(analiz_id=analiz_id, filename=db_filename, type=medya_type)
            db.session.add(medya)
            db.session.commit()
            flash('Medya başarıyla yüklendi.', 'success')
        except Exception as e:
             db.session.rollback()
             print(f"Medya kaydetme hatası: {e}")
             flash('Medya yüklenirken bir hata oluştu.', 'danger')

    else:
        flash('Geçersiz dosya türü.', 'danger')
    return redirect(url_for('analiz_detay', analiz_id=analiz_id))

@app.route('/analiz/<int:analiz_id>/medya_sil/<int:medya_id>', methods=['POST'])
@login_required
def medya_sil(analiz_id, medya_id):
    medya = AnalizMedya.query.get_or_404(medya_id)
    # Analizin kullanıcıya ait olup olmadığını ve medyanın bu analize ait olup olmadığını kontrol et
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != session['user_id'] or medya.analiz_id != analiz_id:
        flash('Yetkisiz işlem.', 'danger')
        return redirect(url_for('analiz_detay', analiz_id=analiz_id))

    try:
        # Dosyayı sil (medya.filename 'analiz_id/dosyaadi' formatında)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], medya.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"DEBUG: Silinen medya: {filepath}")
        else:
             print(f"DEBUG: Silinecek medya bulunamadı: {filepath}")

        db.session.delete(medya)
        db.session.commit()
        flash('Medya silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Medya silme hatası: {e}")
        flash('Medya silinirken bir hata oluştu.', 'danger')

    return redirect(url_for('analiz_detay', analiz_id=analiz_id))

@app.route('/portfolios')
@login_required
def portfolios():
    # Join ile User bilgilerini de getir
    analizler = ArsaAnaliz.query.join(User)\
        .add_columns(User.ad, User.soyad)\
        .filter(User.is_active == True)\
        .order_by(ArsaAnaliz.created_at.desc()).all()
    
    return render_template('portfolios.html', analizler=analizler)

@app.route('/portfolio/create', methods=['GET', 'POST'])
@login_required
def portfolio_create():
    if request.method == 'POST':
        try:
            # Yeni portföy oluştur
            portfolio = Portfolio(
                user_id=session['user_id'],
                title=request.form.get('title'),
                description=request.form.get('description'),
                visibility=request.form.get('visibility', 'public')
            )
            
            # Veritabanına kaydet
            db.session.add(portfolio)
            db.session.commit()
            
            flash('Portföy başarıyla oluşturuldu.', 'success')
            return redirect(url_for('portfolios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Portföy oluşturulurken bir hata oluştu.', 'danger')
            print(f"Portfolio creation error: {str(e)}")
    
    # GET isteği için form sayfasını göster
    return render_template('portfolio_create.html')

@app.route('/portfolio/<int:id>')
@login_required
def portfolio_detail(id):
    portfolio = Portfolio.query.get_or_404(id)
    
    # Portföy private ise ve kullanıcının kendi portföyü değilse erişimi engelle
    if portfolio.visibility == 'private' and portfolio.user_id != session['user_id']:
        flash('Bu portföye erişim yetkiniz yok.', 'danger')
        return redirect(url_for('portfolios'))
    
    return render_template('portfolio_detail.html', portfolio=portfolio)

# Veritabanı tablolarını oluştur
def init_db():
    with app.app_context():
        try:
            # Önce tüm tabloları sil
            db.drop_all()
            # Bağlantıyı yeniden başlat
            db.session.close()
            db.session.remove()
            # Sonra yeniden oluştur
            db.create_all()
            print("Veritabanı tabloları başarıyla oluşturuldu!")
        except Exception as e:
            print(f"Veritabanı oluşturma hatası: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    try:
        # Veritabanını başlat
        init_db()
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Uygulama başlatma hatası: {str(e)}")
