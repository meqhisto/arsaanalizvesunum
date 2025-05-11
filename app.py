# -*- coding: utf-8 -*-
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_file,
    send_from_directory,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import tempfile
import traceback
from sqlalchemy import text,cast,Date 

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
from concurrent_log_handler import (
    ConcurrentRotatingFileHandler,
)  # Import concurrent handler
from modules.fiyat_tahmini import FiyatTahminModeli  # <<< YENİ EKLEME
import secrets
import pyodbc
import pytz
from itertools import zip_longest
from markupsafe import Markup, escape# Markup'ı import edin (bu zaten doğruydu)
from decimal import Decimal

import sys

# from modules import create_app

app = Flask(__name__)
application = app  # Flask uygulamasını application olarak ayarlayın

app.template_folder = "templates"


# Jinja2 template engine'ine datetime modülünü ekle
app.jinja_env.globals.update(datetime=datetime)
app.jinja_env.globals.update(zip=zip)


def nl2br_filter(value):
    if value is None:
        return ''
    # Önce escape et, sonra \n'leri <br> ile değiştir ve Markup olarak işaretle
    escaped_value = escape(value) # Şimdi escape fonksiyonu tanınacaktır
    return Markup(escaped_value.replace('\n', '<br>\n'))

app.jinja_env.filters['nl2br'] = nl2br_filter



# mssql
# conn_str = (
#        r'DRIVER={SQL Server};'
#        r'SERVER=46.221.49.106;'
#        r'DATABASE=arsa_db;'
#        r'UID=altan;'
#        r'PWD=Yxrkt2bb7q8.;'
#    )
# try:
#    conn = pyodbc.connect(conn_str)
#    cursor = conn.cursor()
#    cursor.execute("SELECT @@version;")
#    row = cursor.fetchone()
#    print(f"Bağlantı Başarılı: {row[0]}")
# except pyodbc.Error as ex:
#    sqlstate = ex.args[0]
#    print(f"Bağlantı Hatası: {sqlstate}")
#    sys.exit()

# --- CONFIGURATION FIRST ---
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mssql+pyodbc://altan:Yxrkt2bb7q8.@46.221.49.106/arsa_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "sizin_gizli_anahtariniz")

# Medya yükleme ayarları
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
BASE_DIR = Path(__file__).resolve().parent
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

PRESENTATIONS_DIR = BASE_DIR / "static" / "presentations"
if not PRESENTATIONS_DIR.exists():
    PRESENTATIONS_DIR.mkdir(parents=True)
# --- END CONFIGURATION ---

# Jinja2 template engine'ine datetime modülünü ekle
app.jinja_env.globals.update(datetime=datetime)


db = SQLAlchemy(app)
db.init_app(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# Log ayarları
# Use ConcurrentRotatingFileHandler for thread-safe logging
handler = ConcurrentRotatingFileHandler("app.log", maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# --- Kullanıcı Modeli ---
class User(db.Model):
    __tablename__ = "users"
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
    timezone = db.Column(
        db.String(50), default="Europe/Istanbul"
    )  # Kullanıcının zaman dilimi

    def set_password(self, password):
        try:
            print(f"Setting password for user {self.email}")  # Debug log
            self.password_hash = generate_password_hash(password, method="sha256")
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

    def localize_datetime(self, utc_dt, format="%d.%m.%Y %H:%M"):
        """Verilen UTC datetime nesnesini kullanıcının zaman dilimine çevirir ve formatlar."""
        if not utc_dt:
            return ""
        try:
            # Kullanıcının zaman dilimini al, yoksa veya geçersizse UTC kullan
            user_tz_str = (
                self.timezone if self.timezone in pytz.all_timezones else "UTC"
            )
            user_tz = pytz.timezone(user_tz_str)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc  # Hata durumunda UTC'ye dön

        # Gelen datetime'ı timezone-aware UTC yap
        aware_utc_dt = pytz.utc.localize(utc_dt)
        # Kullanıcının zaman dilimine çevir
        local_dt = aware_utc_dt.astimezone(user_tz)
        return local_dt.strftime(format)


class ArsaAnaliz(db.Model):
    __tablename__ = "arsa_analizleri"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    il = db.Column(db.String(50), nullable=False)
    ilce = db.Column(db.String(50), nullable=False)
    mahalle = db.Column(db.String(100), nullable=False)
    ada = db.Column(db.String(20))
    parsel = db.Column(db.String(20))
    koordinatlar = db.Column(db.String(100))
    pafta = db.Column(db.String(50))
    metrekare = db.Column(db.Numeric(10, 2), nullable=False)
    imar_durumu = db.Column(db.String(50))
    taks = db.Column(db.Numeric(4, 2))
    kaks = db.Column(db.Numeric(4, 2))
    fiyat = db.Column(db.Numeric(15, 2), nullable=False)
    bolge_fiyat = db.Column(db.Numeric(15, 2))
    altyapi = db.Column(db.JSON)
    swot_analizi = db.Column(db.JSON)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.Index("ix_user_il", "user_id", "il"),
        db.Index("ix_created_at", "created_at"),
    )

    # User ilişkisini ekle
    user = db.relationship("User", backref=db.backref("analizler", lazy=True))


class BolgeDagilimi(db.Model):
    __tablename__ = "bolge_dagilimi"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # Kullanıcı ID'si eklendi
    il = db.Column(db.String(50), nullable=False)
    analiz_sayisi = db.Column(db.Integer, default=0)
    toplam_deger = db.Column(db.Numeric(15, 2), default=0)
    son_guncelleme = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # İlişki tanımlama
    user = db.relationship("User", backref=db.backref("bolge_dagilimlari", lazy=True))


class YatirimPerformansi(db.Model):
    __tablename__ = "yatirim_performansi"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # Kullanıcı ID'si eklendi
    ay = db.Column(db.String(20), nullable=False)
    yil = db.Column(db.Integer, nullable=False)
    toplam_deger = db.Column(db.Numeric(15, 2), default=0)
    analiz_sayisi = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişki tanımlama
    user = db.relationship(
        "User", backref=db.backref("yatirim_performanslari", lazy=True)
    )


class DashboardStats(db.Model):
    __tablename__ = "dashboard_stats"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    toplam_arsa_sayisi = db.Column(db.Integer, default=0)
    ortalama_fiyat = db.Column(db.Float, default=0)
    en_yuksek_fiyat = db.Column(db.Float, default=0)
    en_dusuk_fiyat = db.Column(db.Float, default=0)
    toplam_deger = db.Column(db.Numeric(15, 2), default=0)
    son_guncelleme = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("dashboard_stats", lazy=True))

    def __repr__(self):
        return f"<DashboardStats(toplam_arsa_sayisi={self.toplam_arsa_sayisi}, ortalama_fiyat={self.ortalama_fiyat}, en_yuksek_fiyat={self.en_yuksek_fiyat}, en_dusuk_fiyat={self.en_dusuk_fiyat})>"


# Medya modeli
class AnalizMedya(db.Model):
    __tablename__ = "analiz_medya"
    id = db.Column(db.Integer, primary_key=True)
    analiz_id = db.Column(
        db.Integer, db.ForeignKey("arsa_analizleri.id"), nullable=False
    )
    filename = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'image' veya 'video'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    analiz = db.relationship("ArsaAnaliz", backref=db.backref("medyalar", lazy=True))


# Portfolio modeli (User ve ArsaAnaliz modellerinden sonra ekleyin)
class Portfolio(db.Model):
    __tablename__ = "portfolios"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    visibility = db.Column(db.String(20), default="public")  # 'public' veya 'private'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # İlişkiler
    user = db.relationship("User", backref=db.backref("portfolios", lazy=True))
    analizler = db.relationship(
        "ArsaAnaliz",
        secondary="portfolio_arsalar",
        lazy="dynamic",
        backref=db.backref("portfolios", lazy=True),
    )


# Portfolio-Arsa ilişki tablosu
portfolio_arsalar = db.Table(
    "portfolio_arsalar",
    db.Column(
        "portfolio_id", db.Integer, db.ForeignKey("portfolios.id"), primary_key=True
    ),
    db.Column(
        "arsa_id", db.Integer, db.ForeignKey("arsa_analizleri.id"), primary_key=True
    ),
    db.Column("added_at", db.DateTime, default=datetime.now),
)


# Arsa sınıfı
class Arsa:
    def __init__(self, form_data):
        self.form_data = form_data

        # Convert numeric values with safety checks
        try:
            # Get raw values
            raw_metrekare = form_data.get("metrekare", "0")
            raw_fiyat = form_data.get("fiyat", "0")
            raw_bolge_fiyat = form_data.get("bolge_fiyat", "0")
            raw_taks = form_data.get("taks", "0.3")
            raw_kaks = form_data.get("kaks", "1.5")

            # Clean and convert
            self.metrekare = float(str(raw_metrekare).replace(",", "").strip())
            self.fiyat = float(str(raw_fiyat).replace(",", "").strip())
            self.bolge_fiyat = float(str(raw_bolge_fiyat).replace(",", "").strip())
            self.taks = float(str(raw_taks).replace(",", "").strip())
            self.kaks = float(str(raw_kaks).replace(",", "").strip())

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
            self.metrekare_fiyat = (
                self.fiyat / self.metrekare if self.metrekare > 0 else 0
            )
        except ZeroDivisionError:
            print("Zero division error in metrekare_fiyat calculation")
            self.metrekare_fiyat = 0

        try:
            if self.bolge_fiyat > 0:
                self.bolge_karsilastirma = (
                    (self.metrekare_fiyat - self.bolge_fiyat) / self.bolge_fiyat
                ) * 100
            else:
                self.bolge_karsilastirma = 0
        except ZeroDivisionError:
            print("Zero division error in bolge_karsilastirma calculation")
            self.bolge_karsilastirma = 0

        self.konum = {
            "il": (
                self.form_data.get("il", [""])[0]
                if isinstance(self.form_data.get("il"), list)
                else self.form_data.get("il", "")
            ),
            "ilce": (
                self.form_data.get("ilce", [""])[0]
                if isinstance(self.form_data.get("ilce"), list)
                else self.form_data.get("ilce", "")
            ),
            "mahalle": (
                self.form_data.get("mahalle", [""])[0]
                if isinstance(self.form_data.get("mahalle"), list)
                else self.form_data.get("mahalle", "")
            ),
        }

        self.parsel = {
            "ada": (
                self.form_data.get("ada", [""])[0]
                if isinstance(self.form_data.get("ada"), list)
                else self.form_data.get("ada", "")
            ),
            "parsel": (
                self.form_data.get("parsel", [""])[0]
                if isinstance(self.form_data.get("parsel"), list)
                else self.form_data.get("parsel", "")
            ),
        }

        imar_durumu = (
            self.form_data.get("imar_durumu", [""])[0]
            if isinstance(self.form_data.get("imar_durumu"), list)
            else self.form_data.get("imar_durumu", "")
        )
        self.imar_durumu = imar_durumu.capitalize() if imar_durumu else ""

        # Yeni eklenen alanlar
        self.koordinatlar = self.form_data.get("koordinatlar")
        self.pafta = self.form_data.get("pafta")
        self.imar_tipi = self.imar_durumu  # İmar tipini imar durumundan al

        # Hesaplamalar
        self.potansiyel_getiri = self._hesapla_potansiyel_getiri()
        self.yatirim_suresi = self._hesapla_yatirim_suresi()

        # Altyapı bilgileri
        altyapi_list = (
            self.form_data.get("altyapi[]", [])
            if isinstance(self.form_data.get("altyapi[]"), list)
            else [self.form_data.get("altyapi[]", [])]
        )
        self.altyapi = {
            "yol": "yol" in altyapi_list,
            "elektrik": "elektrik" in altyapi_list,
            "su": "su" in altyapi_list,
            "dogalgaz": "dogalgaz" in altyapi_list,
            "kanalizasyon": "kanalizasyon" in altyapi_list,
        }

        # Ulaşım bilgileri
        self.ulasim = {"toplu_tasima_mesafe": "500m"}

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
            "strengths": parse_swot_data(self.form_data.get("strengths", [])),
            "weaknesses": parse_swot_data(self.form_data.get("weaknesses", [])),
            "opportunities": parse_swot_data(self.form_data.get("opportunities", [])),
            "threats": parse_swot_data(self.form_data.get("threats", [])),
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
            "yil_1": self.fiyat * 1.15,
            "yil_3": self.fiyat * 1.45,
            "yil_5": self.fiyat * 1.85,
        }

    def _yatirim_onerileri(self):
        return [
            "Kısa vadede yatırım için uygun",
            "Bölgedeki gelişim projeleri değer artışını destekliyor",
            "İmar durumu avantajlı konumda",
        ]

    def _insaat_hesapla(self):
        taban_alani = self.metrekare * self.taks
        toplam_insaat_alani = self.metrekare * self.kaks
        teorik_kat_sayisi = self.kaks / self.taks if self.taks else 0

        return {
            "taban_alani": taban_alani,
            "toplam_insaat_alani": toplam_insaat_alani,
            "teorik_kat_sayisi": teorik_kat_sayisi,
            "tam_kat_sayisi": int(teorik_kat_sayisi),
        }

class Contact(db.Model):
    __tablename__ = "crm_contacts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"), nullable=True)

    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    role = db.Column(db.String(100))  # Pozisyonu
    status = db.Column(db.String(50), default="Lead")  # Lead, Müşteri, Eski Müşteri, Partner vb.
    source = db.Column(db.String(100)) # Müşteri kaynağı (Web, Referans vb.)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_contacts", lazy="dynamic"))
    # company ilişkisi aşağıda Company modelinde tanımlanacak (backref)
    interactions = db.relationship("Interaction", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    deals = db.relationship("Deal", backref="contact", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", foreign_keys="[Task.contact_id]", backref="contact_tasks", lazy="dynamic", cascade="all, delete-orphan") # foreign_keys belirtildi

    # Kullanıcı bazında e-posta benzersizliği için bir index (isteğe bağlı ama önerilir)
    __table_args__ = (db.UniqueConstraint('user_id', 'email', name='uq_user_contact_email'),)

    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"

class Company(db.Model):
    __tablename__ = "crm_companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100)) # Sektör
    website = db.Column(db.String(200))
    address = db.Column(db.Text)
    phone = db.Column(db.String(30))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_companies", lazy="dynamic"))
    contacts = db.relationship("Contact", backref="company", lazy="dynamic")
    deals = db.relationship("Deal", backref="company", lazy="dynamic", cascade="all, delete-orphan")

    # Kullanıcı bazında şirket ismi benzersizliği
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_user_company_name'),)

    def __repr__(self):
        return f"<Company {self.name}>"

class Interaction(db.Model):
    __tablename__ = "crm_interactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=False)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True) # İsteğe bağlı olarak bir anlaşmayla ilişkilendirilebilir

    type = db.Column(db.String(50), nullable=False) # Telefon, E-posta, Toplantı, Not vb.
    interaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_interactions", lazy="dynamic"))
    # contact ilişkisi Contact modelinde tanımlı
    # deal ilişkisi Deal modelinde tanımlanacak

    def __repr__(self):
        return f"<Interaction {self.type} on {self.interaction_date.strftime('%Y-%m-%d')}>"

class Deal(db.Model):
    __tablename__ = "crm_deals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=False) # Birincil kontak
    company_id = db.Column(db.Integer, db.ForeignKey("crm_companies.id"), nullable=True) # İlişkili şirket

    title = db.Column(db.String(200), nullable=False)
    value = db.Column(db.Numeric(15, 2), default=0.00)
    currency = db.Column(db.String(10), default="TRY")
    stage = db.Column(db.String(50), default="Potansiyel") # Potansiyel, Teklif, Müzakere, Kazanıldı, Kaybedildi
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date, nullable=True)
    probability = db.Column(db.Integer, default=0) # Kazanma olasılığı % (0-100)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    user = db.relationship("User", backref=db.backref("crm_deals", lazy="dynamic"))
    # contact ve company ilişkileri ilgili modellerde backref ile tanımlı
    interactions = db.relationship("Interaction", backref="deal", lazy="dynamic", cascade="all, delete-orphan")
    tasks = db.relationship("Task", foreign_keys="[Task.deal_id]", backref="deal_tasks", lazy="dynamic", cascade="all, delete-orphan") # foreign_keys belirtildi

    def __repr__(self):
        return f"<Deal {self.title}>"

class Task(db.Model):
    __tablename__ = "crm_tasks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) # Görevi oluşturan/atanan ana kullanıcı
    contact_id = db.Column(db.Integer, db.ForeignKey("crm_contacts.id"), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey("crm_deals.id"), nullable=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) # Görevin atandığı kullanıcı (kendisi veya başkası olabilir)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="Beklemede") # Beklemede, Devam Ediyor, Tamamlandı, İptal
    priority = db.Column(db.String(50), default="Normal") # Düşük, Normal, Yüksek
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    owner_user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("owned_crm_tasks", lazy="dynamic"))
    assigned_user = db.relationship("User", foreign_keys=[assigned_to_user_id], backref=db.backref("assigned_crm_tasks", lazy="dynamic"))
    # contact_tasks ve deal_tasks ilişkileri ilgili modellerde backref ile tanımlı

    def __repr__(self):
        return f"<Task {self.title}>"

# --- CRM Modelleri Sonu ---
# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Lütfen önce giriş yapın", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Sunucu hatası: {str(e)}", exc_info=True)
    return "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.", 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            remember = "remember" in request.form

            print(f"Login attempt - Email: {email}")  # Debug log

            if not email or not password:
                print("Email or password is missing")  # Debug log
                flash("E-posta ve şifre alanları zorunludur!", "danger")
                return redirect(url_for("login"))

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
                    flash("Şifre doğrulama hatası!", "danger")
                    return redirect(url_for("login"))

                if is_valid:
                    session["user_id"] = user.id
                    session["email"] = user.email

                    user.failed_attempts = 0
                    user.son_giris = datetime.utcnow()

                    if remember:
                        session.permanent = True
                        app.permanent_session_lifetime = timedelta(days=30)

                    db.session.commit()
                    print("Login successful")  # Debug log
                    flash("Başarıyla giriş yaptınız!", "success")
                    return redirect(url_for("index"))
                else:
                    user.failed_attempts = (user.failed_attempts or 0) + 1
                    user.son_giris = datetime.utcnow()
                    db.session.commit()

                    if user.failed_attempts >= 5:
                        flash(
                            "Çok fazla başarısız giriş denemesi. Lütfen 5 dakika bekleyin.",
                            "danger",
                        )
                    else:
                        flash("Geçersiz e-posta veya şifre!", "danger")
            else:
                print("User not found")  # Debug log
                flash("Geçersiz e-posta veya şifre!", "danger")

            return redirect(url_for("login"))

        except Exception as e:
            print(f"Login error details: {str(e)}")  # Debug log
            import traceback

            print("Full traceback:")  # Debug log
            print(traceback.format_exc())  # Debug log
            flash("Giriş işlemi sırasında bir hata oluştu!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


# Şifremi unuttum sayfası
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
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

            flash(
                "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.", "success"
            )
        else:
            flash("Bu e-posta adresi ile kayıtlı bir hesap bulunamadı.", "danger")

        return redirect(url_for("login"))

    return render_template("forgot_password.html")


# Şifre sıfırlama sayfası
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expires < datetime.utcnow():
        flash("Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Şifreler eşleşmiyor!", "danger")
            return redirect(url_for("reset_password", token=token))

        if len(password) < 6:
            flash("Şifre en az 6 karakter olmalıdır!", "danger")
            return redirect(url_for("reset_password", token=token))

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        flash(
            "Şifreniz başarıyla güncellendi. Lütfen yeni şifrenizle giriş yapın.",
            "success",
        )
        return redirect(url_for("login"))

    return render_template("reset_password.html", token=token)


# Çıkış yapma route'u
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız", "info")
    return redirect(url_for("login"))


@app.route("/favicon.ico")
def favicon():
    favicon_path = os.path.join(app.root_path, "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    else:
        # If favicon.ico does not exist, return a 204 No Content response.
        # This tells the browser there's no icon, and it shouldn't request it again (for a while).
        return "", 204


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(
            url_for("index")
        )  # Kullanıcı giriş yaptıysa index.html'e yönlendir
    return redirect(
        url_for("login")
    )  # Kullanıcı giriş yapmadıysa login.html'e yönlendir
@app.route("/crm/contacts")
@login_required
def crm_contacts_list():
    user_id = session["user_id"]
    # Kullanıcının kendi kişilerini, soyadına ve adına göre sıralı alalım
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    return render_template("crm/contacts_list.html", contacts=contacts, title="Kişiler")


# ...

@app.route("/crm/contact/<int:contact_id>")
@login_required
def crm_contact_detail(contact_id):
    user_id = session["user_id"]
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    interactions = contact.interactions.order_by(Interaction.interaction_date.desc()).all()
    
    tasks = contact.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()
    
    return render_template(
        "crm/contact_detail.html",
        contact=contact,
        title=f"{contact.first_name} {contact.last_name}",
        interactions=interactions,
        tasks=tasks
    )
    
# app.py - crm_contact_new
@app.route("/crm/contact/new", methods=["GET", "POST"])
@login_required
def crm_contact_new():
    user_id = session["user_id"] # user_id'yi başta alalım
    # Mevcut şirketleri al (forma göndermek için)
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        # ... (mevcut POST işleme kodu) ...
        company_id_str = request.form.get("company_id")
        # ...

        # Temel Doğrulama
        if not first_name or not last_name:
            flash("Ad ve Soyad alanları zorunludur.", "danger")
            return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)

        # E-posta benzersizlik kontrolü
        if email:
            existing_contact = Contact.query.filter_by(user_id=user_id, email=email).first()
            if existing_contact:
                flash(f"'{email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", "warning")
                return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)
        try:
            new_contact = Contact(
                # ... (diğer alanlar) ...
                company_id=int(company_id_str) if company_id_str else None, # Güncellendi
                # ...
            )
            db.session.add(new_contact)
            db.session.commit()
            flash(f"'{new_contact.first_name} {new_contact.last_name}' adlı kişi başarıyla eklendi.", "success")
            return redirect(url_for("crm_contacts_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Kişi eklenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Contact New Error: {e}")
            # Hata durumunda formu ve şirket listesini tekrar gönder
            return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", contact=request.form, companies=companies)


    # GET isteği için formu ve şirket listesini gönder
    return render_template("crm/contact_form.html", title="Yeni Kişi Ekle", companies=companies)


@app.route("/crm/contact/<int:contact_id>/edit", methods=["GET", "POST"])
@login_required
def crm_contact_edit(contact_id):
    user_id = session["user_id"]
    contact_to_edit = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        # Formdan gelen verileri al
        contact_to_edit.first_name = request.form.get("first_name")
        contact_to_edit.last_name = request.form.get("last_name")
        new_email = request.form.get("email")  # <<< BU SATIRI EKLEYİN/KONTROL EDİN
        contact_to_edit.phone = request.form.get("phone")
        contact_to_edit.company_id = int(request.form.get("company_id")) if request.form.get("company_id") else None
        contact_to_edit.role = request.form.get("role")
        contact_to_edit.status = request.form.get("status")
        contact_to_edit.source = request.form.get("source")
        contact_to_edit.notes = request.form.get("notes")

        # Temel Doğrulama
        if not contact_to_edit.first_name or not contact_to_edit.last_name:
            flash("Ad ve Soyad alanları zorunludur.", "danger")
            return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

        # E-posta benzersizlik kontrolü (kullanıcı bazında, mevcut kişi hariç)
        # new_email artık burada tanımlı olmalı
        if new_email and new_email != contact_to_edit.email: # E-posta değiştiyse kontrol et
            existing_contact = Contact.query.filter(
                Contact.user_id == user_id,
                Contact.email == new_email,
                Contact.id != contact_id # Kendisi hariç
            ).first()
            if existing_contact:
                flash(f"'{new_email}' e-posta adresi ile kayıtlı başka bir kişi zaten mevcut.", "warning")
                return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)
        
        contact_to_edit.email = new_email if new_email else None

        try:
            db.session.commit()
            flash(f"'{contact_to_edit.first_name} {contact_to_edit.last_name}' adlı kişi başarıyla güncellendi.", "success")
            return redirect(url_for("crm_contact_detail", contact_id=contact_to_edit.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Kişi güncellenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Contact Edit Error: {e}")
            return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

    return render_template("crm/contact_form.html", title=f"Kişi Düzenle: {contact_to_edit.first_name} {contact_to_edit.last_name}", contact=contact_to_edit, companies=companies, edit_mode=True)

# ... (mevcut importlar) ...
# Interaction modelini import ettiğinizden emin olun

# --- Etkileşim (Interaction) Fonksiyonları ---

@app.route("/crm/contact/<int:contact_id>/interaction/new", methods=["POST"])
@login_required
def crm_interaction_new(contact_id):
    user_id = session["user_id"]
    contact = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()

    interaction_type = request.form.get("interaction_type")
    interaction_date_str = request.form.get("interaction_date") # Formdan YYYY-MM-DDTHH:MM formatında gelecek
    summary = request.form.get("summary")
    # deal_id = request.form.get("deal_id") # Eğer bir fırsata da bağlanacaksa

    if not interaction_type or not interaction_date_str or not summary:
        flash("Etkileşim türü, tarihi ve özeti zorunludur.", "danger")
        return redirect(url_for("crm_contact_detail", contact_id=contact.id))

    try:
        # Tarih ve saat string'ini datetime nesnesine çevir
        interaction_datetime = datetime.strptime(interaction_date_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Geçersiz tarih formatı. Lütfen doğru bir tarih ve saat girin.", "danger")
        return redirect(url_for("crm_contact_detail", contact_id=contact.id))

    try:
        new_interaction = Interaction(
            user_id=user_id,
            contact_id=contact.id,
            # deal_id=int(deal_id) if deal_id else None,
            type=interaction_type,
            interaction_date=interaction_datetime, # datetime nesnesini kullan
            summary=summary
        )
        db.session.add(new_interaction)
        db.session.commit()
        flash("Yeni etkileşim başarıyla eklendi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Etkileşim eklenirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Interaction New Error: {e}")

    return redirect(url_for("crm_contact_detail", contact_id=contact.id))

# Basit bir etkileşim silme fonksiyonu (isteğe bağlı)
@app.route("/crm/interaction/<int:interaction_id>/delete", methods=["POST"])
@login_required
def crm_interaction_delete(interaction_id):
    user_id = session["user_id"]
    interaction_to_delete = Interaction.query.filter_by(id=interaction_id, user_id=user_id).first_or_404()
    
    contact_id_redirect = interaction_to_delete.contact_id # Yönlendirme için sakla
    # deal_id_redirect = interaction_to_delete.deal_id # Eğer fırsatlara da bağlıysa

    try:
        db.session.delete(interaction_to_delete)
        db.session.commit()
        flash("Etkileşim başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Etkileşim silinirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Interaction Delete Error: {e}")
    
    # if deal_id_redirect:
    #     return redirect(url_for('crm_deal_detail', deal_id=deal_id_redirect))
    if contact_id_redirect:
        return redirect(url_for('crm_contact_detail', contact_id=contact_id_redirect))
    return redirect(url_for('crm_contacts_list')) # Varsayılan yönlendirme

# --- Etkileşim (Interaction) Fonksiyonları Sonu ---



@app.route(
    "/change-password", methods=["POST"], endpoint="change_password"
)  # endpoint adını belirtiyoruz
@login_required  # Kullanıcının giriş yapmış olması gerekebilir
def change_password_route():  # Fonksiyon adı farklı olabilir ama endpoint önemlidir
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        # Mevcut kullanıcıyı al (örneğin session'dan ID ile)
        user_id = session.get("user_id")
        user = User.query.get(user_id)  # User modelinize göre ayarlayın

        if not user or not check_password_hash(
            user.password_hash, current_password
        ):  # password_hash, modelinizdeki hash'lenmiş şifre alanı olmalı
            flash("Mevcut şifreniz yanlış!", "danger")
            return redirect(url_for("profile"))  # Profil sayfasına geri yönlendir

        if new_password != confirm_password:
            flash("Yeni şifreler eşleşmiyor!", "danger")
            return redirect(url_for("profile"))

        # Yeni şifreyi hash'le ve veritabanında güncelle
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()  # Veritabanı işlemini kaydet

        flash("Şifreniz başarıyla güncellendi.", "success")
        return redirect(url_for("profile"))

    # POST dışındaki istekler için (genelde buraya gelinmemeli)
    return redirect(url_for("profile"))


@app.route("/index")
@login_required
def index():
    user_id = session["user_id"]
    current_user = User.query.get(user_id)

    # --- Mevcut Arsa Analiz Verileri ve İstatistikler ---
    # Bölge dağılımı için verileri hazırla (Arsa Analizleri için)
    arsa_bolge_dagilimi = db.session.query(
        ArsaAnaliz.il,
        db.func.count(ArsaAnaliz.id).label('analiz_sayisi')
    ).filter(
        ArsaAnaliz.user_id == user_id
    ).group_by(
        ArsaAnaliz.il
    ).order_by(
        db.func.count(ArsaAnaliz.id).desc()
    ).all()

    # Grafik için etiketler ve veriler (Arsa Analizleri için)
    # Bu değişken isimleri index.html'deki grafiklerle eşleşmeli
    # Eğer index.html'de "bolge_labels" ve "bolge_data" farklı bir amaçla kullanılıyorsa,
    # aşağıdaki değişken isimlerini (örn: arsa_bolge_labels) değiştirip template'i de güncellemeniz gerekir.
    grafik_bolge_labels = [b.il for b in arsa_bolge_dagilimi]
    grafik_bolge_data_sayi = [b.analiz_sayisi for b in arsa_bolge_dagilimi]


    # Kullanıcının genel dashboard istatistiklerini getir
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = DashboardStats(user_id=user_id)
        db.session.add(stats)
        # db.session.commit() # Commit'i sonda tek seferde yapalım

    # Son Arsa Analizleri (limit 5)
    son_arsa_analizleri = (
        ArsaAnaliz.query.filter_by(user_id=user_id)
        .order_by(ArsaAnaliz.created_at.desc())
        .limit(5)
        .all()
    )

    # Son Aktiviteler (şimdilik sadece arsa analizleri için)
    son_aktiviteler_listesi = []
    for analiz in son_arsa_analizleri:
        son_aktiviteler_listesi.append(
            {
                "tarih": analiz.created_at,
                "mesaj": f"{analiz.il}, {analiz.ilce} bölgesinde yeni arsa analizi oluşturuldu.",
                "url": url_for('analiz_detay', analiz_id=analiz.id), # Link için
                "tip": "analiz" 
            }
        )
    # CRM aktivitelerini de buraya ekleyip tarihe göre sıralayabilirsiniz (ileri seviye)

    # BolgeDagilimi verileri (Bu sizin orijinal kodunuzdan, toplam değer için)
    bolge_dagilimlari_deger = BolgeDagilimi.query.filter_by(user_id=user_id).all()
    # Eğer `zipped` bu veriyi kullanıyorsa:
    # zipped_bolge_deger_labels = [b.il for b in bolge_dagilimlari_deger]
    # zipped_bolge_deger_data = [float(b.toplam_deger) for b in bolge_dagilimlari_deger]
    # zipped = list(zip(zipped_bolge_deger_labels, zipped_bolge_deger_data))
    # VEYA sizin orijinal `zipped` mantığınız neyse onu koruyun.
    # Şimdilik index.html'de `zipped` kullanılıp kullanılmadığını bilmediğim için bu kısmı yoruma alıyorum.
    # Eğer kullanılıyorsa, yukarıdaki arsa_bolge_dagilimi'nden gelen `grafik_bolge_labels` ve `grafik_bolge_data_sayi`
    # ile mi, yoksa BolgeDagilimi modelinden gelen toplam değerlerle mi oluşturulacağına karar verin.
    # Orijinal kodunuzda hem `bolge_dagilimi` hem de `bolge_dagilimlari` vardı, bu biraz kafa karıştırıcı.
    # `index.html`'deki `regionDistributionChart` hangi `bolge_labels` ve `bolge_data`'yı kullandığınıza bağlı.
    # Varsayılan olarak analiz sayısını kullanan grafiği baz alıyorum.
    # Eğer toplam değeri kullanan bir grafik varsa, o zaman BolgeDagilimi modeli kullanılmalı.
    # Mevcut `index.html`'inizde `regionDistributionChart`'ın `bolge_data`'sı analiz sayısı mı, toplam değer mi?
    # Orijinal kodunuzda `bolge_data = [float(b.toplam_deger) for b in bolge_dagilimlari]` vardı,
    # ve `bolge_labels = [b.il for b in bolge_dagilimlari]` vardı. Bu, BolgeDagilimi modelini kullanıyor.
    # Ancak aynı zamanda `bolge_dagilimi` sorgusuyla da benzer etiketler ve veriler çekiyorsunuz.
    # Hangi grafiğin hangi veriyi kullandığını netleştirmek önemli.
    # Ben şimdilik `index.html`'deki `regionDistributionChart`'ın `BolgeDagilimi` modelini kullandığını varsayarak
    # o değişkenleri koruyorum, ancak `bolge_labels` ve `bolge_data` isim çakışması olabilir.
    
    # Orjinal kodunuzdaki `bolge_dagilimlari` ve ondan türetilen `bolge_labels`, `bolge_data`, `zipped`:
    bolge_dagilimlari = BolgeDagilimi.query.filter_by(user_id=user_id).all()
    chart_bolge_labels_deger = [b.il for b in bolge_dagilimlari] # İsim çakışmasını önlemek için değiştirdim
    chart_bolge_data_deger = [float(b.toplam_deger) for b in bolge_dagilimlari] # İsim çakışmasını önlemek için
    zipped = list(zip(chart_bolge_labels_deger, chart_bolge_data_deger)) # `zipped`'in bu veriyi kullandığını varsayıyorum


    # Son 6 ayın Arsa Analiz sayılarını hesapla
    son_alti_ay_analiz = []
    aylik_analiz_sayilari_arsa = []
    current_date = datetime.utcnow() # UTCnow kullanmak daha tutarlı olabilir
    for i in range(6):
        # Ay ve yılı doğru hesapla
        month_offset = current_date.month - 1 - i # -1 mevcut ayı 0. offset yapar
        target_year = current_date.year + (month_offset // 12)
        target_month = (month_offset % 12) + 1

        ay_analiz_sayisi = ArsaAnaliz.query.filter(
            ArsaAnaliz.user_id == user_id,
            db.extract("year", ArsaAnaliz.created_at) == target_year,
            db.extract("month", ArsaAnaliz.created_at) == target_month,
        ).count()

        ay_isimleri = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
        son_alti_ay_analiz.insert(0, f"{ay_isimleri[target_month]} {str(target_year)[-2:]}") # Örn: May 23
        aylik_analiz_sayilari_arsa.insert(0, ay_analiz_sayisi)


    # Arsa Analizleri için Ek İstatistikler
    toplam_arsa_degeri = (
        db.session.query(db.func.sum(ArsaAnaliz.fiyat))
        .filter_by(user_id=user_id)
        .scalar() or Decimal(0) # Decimal ile başlatmak daha iyi
    )
    toplam_arsa_sayisi = ArsaAnaliz.query.filter_by(user_id=user_id).count()


    # --- YENİ: CRM Özet Verileri ---
    # 1. Yaklaşan Görevler (Önümüzdeki 7 gün içinde bitiş tarihi olan ve tamamlanmamış/iptal edilmemiş)
    today_utc_date = datetime.utcnow().date() # Sadece tarih kısmını al
    one_week_later_utc_date = today_utc_date + timedelta(days=7)
    yaklasan_gorevler = Task.query.filter(
        Task.assigned_to_user_id == user_id,
        Task.status.notin_(['Tamamlandı', 'İptal Edildi']),
        Task.due_date != None,
        # SQL Server için datetime sütununu date'e cast et
        cast(Task.due_date, Date) >= today_utc_date,
        cast(Task.due_date, Date) <= one_week_later_utc_date
    ).order_by(Task.due_date.asc()).limit(5).all()

    # 2. Son Eklenen Kişiler (Son 5)
    son_kisiler = Contact.query.filter_by(user_id=user_id).order_by(Contact.created_at.desc()).limit(5).all()

    # 3. Açık Fırsatlar (Kazanıldı veya Kaybedildi olmayanlar - Son eklenen 5)
    acik_firsatlar = Deal.query.filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi'])
    ).order_by(Deal.created_at.desc()).limit(5).all()
    
    # 4. Toplam Açık Fırsat Sayısı ve Değeri
    toplam_acik_firsat_sayisi = Deal.query.filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi'])
    ).count()
    
    toplam_acik_firsat_degeri_try = db.session.query(db.func.sum(Deal.value)).filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi']),
        Deal.currency == 'TRY'
    ).scalar() or Decimal(0)
    # Diğer para birimleri için de benzer sorgularla toplam değerler hesaplanabilir.

    # 5. Son Etkileşimler (kullanıcının oluşturduğu - Son 5)
    son_etkilesimler = Interaction.query.filter_by(user_id=user_id).order_by(Interaction.interaction_date.desc()).limit(5).all()


    # DashboardStats modelini CRM verileriyle de güncelleyebiliriz (isteğe bağlı)
    # if stats:
    #     stats.toplam_kisi_sayisi = Contact.query.filter_by(user_id=user_id).count() # Örnek
    #     stats.acik_firsat_sayisi = toplam_acik_firsat_sayisi # Örnek
    # db.session.commit() # Tüm değişiklikler için tek commit

    return render_template(
        "index.html",
        current_user=current_user,
        stats=stats, # Genel dashboard istatistikleri (Arsa + CRM olabilir)
        
        # Arsa Analizleri Bölümü için Veriler
        analizler=son_arsa_analizleri, # Son arsa analizleri (template'de `analizler` olarak kullanılıyor)
        son_aktiviteler=son_aktiviteler_listesi, # Arsa analiz aktiviteleri (template'de `son_aktiviteler`)
        
        # `index.html`'deki "Analiz İstatistikleri (Son 6 Ay)" grafiği için:
        son_alti_ay=son_alti_ay_analiz, # Template'de `son_alti_ay`
        aylik_analiz_sayilari=aylik_analiz_sayilari_arsa, # Template'de `aylik_analiz_sayilari`
        
        # `index.html`'deki "Analizlerin Bölge Dağılımı" grafiği için:
        # Eğer bu grafik BolgeDagilimi modelindeki toplam_deger'i kullanıyorsa:
        bolge_labels=chart_bolge_labels_deger, # Template'de `bolge_labels`
        bolge_data=chart_bolge_data_deger,   # Template'de `bolge_data`
        # Yok eğer analiz sayısını kullanıyorsa:
        # bolge_labels=grafik_bolge_labels,
        # bolge_data=grafik_bolge_data_sayi,
        
        # Arsa Analizleri için Ek İstatistikler (Kartlarda gösterilen)
        toplam_deger=toplam_arsa_degeri, # Template'de `toplam_deger` (Arsa için)
        toplam_portfoy=toplam_arsa_sayisi, # Template'de `toplam_portfoy` (Arsa için)
        
        # `zipped` değişkeni (eğer hala kullanılıyorsa ve yukarıdaki chart_bolge... verilerini kullanıyorsa)
        zipped=zipped, 
        
        # YENİ CRM ÖZET VERİLERİ
        yaklasan_gorevler=yaklasan_gorevler,
        son_kisiler=son_kisiler,
        acik_firsatlar=acik_firsatlar,
        toplam_acik_firsat_sayisi=toplam_acik_firsat_sayisi,
        toplam_acik_firsat_degeri_try=toplam_acik_firsat_degeri_try,
        son_etkilesimler=son_etkilesimler
    )
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            # Şifre doğrulama kontrolü
            password = request.form.get("password")
            password_confirm = request.form.get("password_confirm")

            if password != password_confirm:
                flash("Şifreler eşleşmiyor!", "danger")
                return redirect(url_for("register"))

            if len(password) < 6:
                flash("Şifre en az 6 karakter olmalıdır!", "danger")
                return redirect(url_for("register"))

            # E-posta kontrolü
            if User.query.filter_by(email=request.form.get("email")).first():
                flash("Bu e-posta adresi zaten kayıtlı!", "danger")
                return redirect(url_for("register"))

            # Yeni kullanıcı oluştur
            user = User(
                email=request.form.get("email"),
                ad=request.form.get("ad"),
                soyad=request.form.get("soyad"),
                telefon=request.form.get("telefon"),
                firma=request.form.get("firma"),
                unvan=request.form.get("unvan"),
                adres=request.form.get("adres"),
                is_active=True,
            )

            # Şifreyi ayarla
            user.set_password(password)

            # Veritabanına kaydet
            db.session.add(user)
            db.session.commit()

            flash("Kayıt başarılı! Lütfen giriş yapın.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            db.session.rollback()
            flash(f"Kayıt sırasında bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"Registration error: {str(e)}")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/submit", methods=["POST"])
@login_required
def submit():
    try:
        user_id = session["user_id"]
        form_data = request.form.to_dict(flat=True)

        # Altyapı verilerini özel olarak al
        altyapi_list = request.form.getlist("altyapi[]")
        form_data["altyapi[]"] = altyapi_list  # form_data'ya ekle

        print("Raw form data:", form_data)
        print("Altyapı verileri:", altyapi_list)

        # Convert numeric values before object creation
        try:
            # Clean and convert numeric values
            metrekare = float(
                str(form_data.get("metrekare", "0")).replace(",", "").strip()
            )
            fiyat = float(str(form_data.get("fiyat", "0")).replace(",", "").strip())
            bolge_fiyat = float(
                str(form_data.get("bolge_fiyat", "0")).replace(",", "").strip()
            )
            taks = float(str(form_data.get("taks", "0.3")).replace(",", "").strip())
            kaks = float(str(form_data.get("kaks", "1.5")).replace(",", "").strip())

            # Değerleri sınırla
            if metrekare > 9999999.99:
                metrekare = 9999999.99
                flash(
                    "Metrekare değeri çok büyük, maksimum değer ile sınırlandı.",
                    "warning",
                )

            if fiyat > 9999999999999.99:
                fiyat = 9999999999999.99
                flash(
                    "Fiyat değeri çok büyük, maksimum değer ile sınırlandı.", "warning"
                )

            if bolge_fiyat > 9999999999999.99:
                bolge_fiyat = 9999999999999.99
                flash(
                    "Bölge fiyat değeri çok büyük, maksimum değer ile sınırlandı.",
                    "warning",
                )

            # Update form data with converted values
            form_data.update(
                {
                    "metrekare": metrekare,
                    "fiyat": fiyat,
                    "bolge_fiyat": bolge_fiyat,
                    "taks": taks,
                    "kaks": kaks,
                }
            )

        except (ValueError, TypeError) as e:
            print(f"Numeric conversion error: {e}")
            return (
                jsonify({"error": "Lütfen sayısal değerleri doğru formatta giriniz."}),
                400,
            )

        # Process SWOT data
        swot_data = {}
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            try:
                value = form_data.get(key, "[]")
                swot_data[key] = json.loads(value) if value else []
            except json.JSONDecodeError:
                print(f"JSON decode error for {key}: {value}")
                swot_data[key] = []

        # Create new ArsaAnaliz object
        yeni_analiz = ArsaAnaliz(
            user_id=user_id,
            il=form_data.get("il", ""),
            ilce=form_data.get("ilce", ""),
            mahalle=form_data.get("mahalle", ""),
            ada=form_data.get("ada", ""),
            parsel=form_data.get("parsel", ""),
            koordinatlar=form_data.get("koordinatlar", ""),
            pafta=form_data.get("pafta", ""),
            metrekare=Decimal(str(metrekare)),
            imar_durumu=form_data.get("imar_durumu", ""),
            taks=Decimal(str(taks)),
            kaks=Decimal(str(kaks)),
            fiyat=Decimal(str(fiyat)),
            bolge_fiyat=Decimal(str(bolge_fiyat)),
            altyapi=json.dumps(altyapi_list),
            swot_analizi=json.dumps(swot_data),
        )

        # Veritabanına kaydet
        db.session.add(yeni_analiz)

        # Bölge istatistiklerini güncelle
        bolge = BolgeDagilimi.query.filter_by(
            user_id=user_id, il=form_data.get("il")
        ).first()

        fiyat_decimal = Decimal(str(fiyat))

        if bolge:
            bolge.analiz_sayisi += 1
            bolge.toplam_deger += fiyat_decimal
        else:
            yeni_bolge = BolgeDagilimi(
                user_id=user_id,
                il=form_data.get("il"),
                analiz_sayisi=1,
                toplam_deger=fiyat_decimal,
            )
            db.session.add(yeni_bolge)

        # Dashboard istatistiklerini güncelle
        stats = DashboardStats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = DashboardStats(user_id=user_id)
            db.session.add(stats)

        stats.toplam_arsa_sayisi += 1
        stats.ortalama_fiyat = (
            stats.ortalama_fiyat * (stats.toplam_arsa_sayisi - 1) + fiyat
        ) / stats.toplam_arsa_sayisi
        stats.en_yuksek_fiyat = max(stats.en_yuksek_fiyat, fiyat)
        stats.en_dusuk_fiyat = min(stats.en_dusuk_fiyat, fiyat)
        stats.toplam_deger += fiyat_decimal
        # Ortalama ROI float kalabilir, Numeric ise Decimal'e çevirin
        try:
            stats.ortalama_roi = Decimal(str(form_data.get("potansiyel_getiri", 0)))
        except Exception:
            stats.ortalama_roi = Decimal("0")

        # Değişiklikleri kaydet
        db.session.commit()

        # --- DEĞİŞİKLİK BAŞLANGICI ---
        # ID'nin atanmasını garantilemek için flush yap
        db.session.flush()
        # Yeni oluşturulan analizin ID'sini al
        analiz_id_yeni = yeni_analiz.id
        print(f"DEBUG: Yeni analiz ID'si: {analiz_id_yeni}")  # Debug için

        # Yeni ID'yi form_data'ya ekle (session'a kaydetmeden önce)
        form_data["id"] = analiz_id_yeni
        # --- DEĞİŞİKLİK SONU ---

        # ArsaAnalizci ile analiz yap
        analizci = ArsaAnalizci()
        analiz_sonuclari = analizci.analiz_et(
            {
                "metrekare": form_data.get("metrekare", 0),
                "fiyat": form_data.get("fiyat", 0),
                "bolge_fiyat": form_data.get("bolge_fiyat", 0),
                "taks": form_data.get("taks", 0.3),
                "kaks": form_data.get("kaks", 1.5),
                "imar_durumu": form_data.get("imar_durumu", ""),
                "altyapi": form_data.get("altyapi[]", []),
                "konum": {
                    "il": form_data.get("il", ""),
                    "ilce": form_data.get("ilce", ""),
                    "mahalle": form_data.get("mahalle", ""),
                },
            }
        )

        # Özet analizi al
        ozet = analizci.ozetle(analiz_sonuclari)

        # Session'a kaydet (artık 'id' içeriyor)
        session["arsa_data"] = form_data
        session["analiz_sonuclari"] = analiz_sonuclari
        session["analiz_ozeti"] = ozet
        print(
            f"DEBUG: Session'a kaydedilen arsa_data: {session['arsa_data']}"
        )  # Debug için

        # Arsa nesnesini oluştur (artık ID'yi de içerebilir)
        arsa = Arsa(form_data)

        # UUID oluştur (dosya adı için)
        file_id = str(uuid.uuid4())

        # Kullanıcı bilgilerini al
        user = User.query.get(session["user_id"])

        # Sonuç sayfasına yönlendir
        return render_template(
            "sonuc.html",
            arsa=arsa,
            analiz=analiz_sonuclari,
            ozet=ozet,
            file_id=file_id,
            user=user,
        )  # Kullanıcı bilgilerini ekle

    except Exception as e:
        # Hata durumunda rollback yap
        db.session.rollback()
        print(f"Submit error: {str(e)}")
        import traceback

        traceback.print_exc()  # Hatanın tam izini yazdır
        return jsonify({"error": str(e)}), 500


# app.py içinde /generate fonksiyonu


@app.route("/generate/<format>/<file_id>")
@login_required
def generate(format, file_id):
    try:
        arsa_data = session.get("arsa_data")
        analiz_ozeti = session.get("analiz_ozeti")

        if not arsa_data or not analiz_ozeti:
            flash("Analiz verisi bulunamadı veya oturum süresi doldu.", "warning")
            return redirect(url_for("index"))

        # Analize ait kullanıcı bilgilerini veritabanından al
        analiz = ArsaAnaliz.query.get(arsa_data["id"])
        user = User.query.get(analiz.user_id)
        profile_info = {
            "ad": user.ad,
            "soyad": user.soyad,
            "email": user.email,
            "telefon": user.telefon,
            "firma": user.firma,
            "unvan": user.unvan,
            "adres": user.adres,
            "profil_foto": user.profil_foto,
            "created_at": analiz.created_at,
        }

        print(
            f"DEBUG [Generate]: Kullanılacak arsa_data: {arsa_data}", flush=True
        )  # Flush eklendi
        print(
            f"DEBUG [Generate]: Kullanılacak analiz_ozeti: {analiz_ozeti}", flush=True
        )  # Flush eklendi

        # URL parametrelerinden rapor ayarlarını al
        theme = request.args.get("theme", "classic")  # Varsayılan tema
        color_scheme = request.args.get(
            "color_scheme", "blue"
        )  # Varsayılan renk şeması

        raw_sections_str = request.args.get("sections")
        passed_sections_list = None  # Başlangıçta None
        if raw_sections_str is not None:  # Eğer 'sections' parametresi URL'de varsa
            # Virgülle ayrılmış string'i listeye çevir, boş elemanları ve baştaki/sondaki boşlukları temizle
            passed_sections_list = [
                s.strip() for s in raw_sections_str.split(",") if s.strip()
            ]

        doc_generator_settings = {
            "theme": theme,
            "color_scheme": color_scheme,
        }
        # Sadece URL'den geçerli bir sections listesi geldiyse settings'e ekle
        if (
            passed_sections_list is not None
        ):  # Eğer sections parametresi vardıysa (boş liste bile olsa)
            doc_generator_settings["sections"] = passed_sections_list

        # Ayarları DocumentGenerator'a gönder
        doc_generator = DocumentGenerator(
            arsa_data,
            analiz_ozeti,
            file_id,
            PRESENTATIONS_DIR,
            profile_info=profile_info,
            settings=doc_generator_settings,
        )

        filename = None  # Başlangıç değeri
        download_name = None  # Başlangıç değeri

        if format == "word":
            print(
                "DEBUG [Generate]: doc_generator.create_word() çağrılacak...",
                flush=True,
            )
            filename = doc_generator.create_word()
            if filename and os.path.exists(filename):
                print(f"DEBUG [Generate]: Word dosyası bulundu: {filename}", flush=True)
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=f"arsa_analiz_{file_id}.docx",
                )
            else:
                print(
                    f"HATA [Generate]: Word dosyası oluşturulamadı veya bulunamadı: {filename}",
                    flush=True,
                )
                flash("Word dosyası oluşturulamadı.", "danger")
                return redirect(url_for("analiz_detay", analiz_id=file_id))

        elif format == "pdf":
            # --- YENİ LOG ---
            print(
                "DEBUG [Generate]: doc_generator.create_pdf() çağrılacak...", flush=True
            )
            filename = doc_generator.create_pdf()
            download_name = f"gayrimenkul_analiz_{file_id}.pdf"
            # --- YENİ LOG ---
            print(
                f"DEBUG [Generate]: create_pdf() tamamlandı. Dosya: {filename}",
                flush=True,
            )
        else:
            print(f"UYARI [Generate]: Geçersiz format istendi: {format}", flush=True)
            return jsonify({"error": "Geçersiz format"}), 400

        # --- YENİ LOG ---
        if filename and os.path.exists(filename):
            print(
                f"DEBUG [Generate]: send_file çağrılacak. Dosya: {filename}", flush=True
            )
            return send_file(filename, as_attachment=True, download_name=download_name)
        else:
            print(
                f"HATA [Generate]: Oluşturulan dosya bulunamadı veya geçersiz! Dosya: {filename}",
                flush=True,
            )
            flash("Rapor dosyası oluşturulamadı veya bulunamadı.", "danger")
            return redirect(request.referrer or url_for("index"))

    except Exception as e:
        print(f"HATA [Generate]: {str(e)}", flush=True)
        import traceback

        traceback.print_exc()
        flash("Rapor oluşturulurken bir hata oluştu.", "danger")
        return redirect(url_for("analiz_detay", analiz_id=file_id))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.query.get(session["user_id"])
    timezone = pytz.all_timezones

    if request.method == "POST":
        try:
            user.ad = request.form.get("ad")
            user.soyad = request.form.get("soyad")
            user.telefon = request.form.get("telefon")
            user.firma = request.form.get("firma")
            user.unvan = request.form.get("unvan")
            user.adres = request.form.get("adres")
            # Zaman dilimini al ve kontrol et
            selected_timezone = request.form.get("timezone")
            if selected_timezone in pytz.all_timezones:
                user.timezone = selected_timezone
            else:
                user.timezone = "UTC"  # Geçersizse veya yoksa varsayılana dön

            # Handle profile photo upload
            if "profil_foto" in request.files:
                file = request.files["profil_foto"]
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Kullanıcıya özel bir alt klasör oluştur (isteğe bağlı ama önerilir)
                    user_upload_dir = os.path.join(
                        app.config["UPLOAD_FOLDER"], "profiles", str(user.id)
                    )
                    os.makedirs(user_upload_dir, exist_ok=True)
                    filepath = os.path.join(user_upload_dir, filename)
                    file.save(filepath)
                    # Veritabanına göreceli yolu kaydet
                    relative_path = "/".join(["profiles", str(user.id), filename])
                    user.profil_foto = relative_path

            db.session.commit()
            flash("Profil başarıyla güncellendi!", "success")
            return redirect(url_for("profile"))

        except Exception as e:
            db.session.rollback()
            flash("Profil güncellenirken bir hata oluştu!", "danger")
            print(f"Profile update error: {str(e)}")

    return render_template(
        "profile.html", user=user, timezones=timezone
    )  # Değişken adını 'timezones' olarak düzelt


@app.route("/analiz/<int:analiz_id>")
@login_required
def analiz_detay(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        # Kullanıcı bilgilerini getir
        user = User.query.get(analiz.user_id)

        # print(f"DEBUG: Session user_id: {session.get('user_id')}, Analiz user_id: {analiz.user_id}")  # Debug log
        if analiz.user_id != session["user_id"]:
            # print("DEBUG: Permission denied for analiz_detay")  # Debug log
            flash("Bu analizi görüntüleme yetkiniz yok.", "danger")
            return redirect(url_for("analizler"))

        # JSON verilerini dönüştür
        altyapi = (
            json.loads(analiz.altyapi)
            if isinstance(analiz.altyapi, str)
            else analiz.altyapi
        )
        swot_analizi = (
            json.loads(analiz.swot_analizi)
            if isinstance(analiz.swot_analizi, str)
            else analiz.swot_analizi
        )

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
        analiz_sonuclari = analizci.analiz_et(
            {
                "metrekare": metrekare,
                "fiyat": fiyat,
                "bolge_fiyat": bolge_fiyat,
                "taks": taks,
                "kaks": kaks,
                "imar_durumu": analiz.imar_durumu,
                "altyapi": altyapi,
                "konum": {
                    "il": analiz.il,
                    "ilce": analiz.ilce,
                    "mahalle": analiz.mahalle,
                },
            }
        )
        ozet = analizci.ozetle(analiz_sonuclari)

        # --- PDF/Word için session'a analiz verisi yükle ---
        # Bu kısım önemli: Analiz detay sayfasından rapor oluşturulacaksa,
        # session'daki verinin güncel analiz verisi olduğundan emin olmalıyız.
        session["arsa_data"] = {
            "id": analiz.id,  # <<< ÖNEMLİ: Analiz ID'sini ekle
            "il": analiz.il,
            "ilce": analiz.ilce,
            "mahalle": analiz.mahalle,
            "ada": analiz.ada,
            "parsel": analiz.parsel,
            "koordinatlar": analiz.koordinatlar,
            "pafta": analiz.pafta,
            "metrekare": float(metrekare),
            "imar_durumu": analiz.imar_durumu,
            "taks": float(taks),
            "kaks": float(kaks),
            "fiyat": float(fiyat),
            "bolge_fiyat": float(bolge_fiyat),
            "altyapi[]": altyapi,  # Anahtar adını DocumentGenerator'ın beklediği gibi yapalım
            # SWOT alanları
            "strengths": swot_analizi.get("strengths", []),
            "weaknesses": swot_analizi.get("weaknesses", []),
            "opportunities": swot_analizi.get("opportunities", []),
            "threats": swot_analizi.get("threats", []),
        }
        session["analiz_ozeti"] = ozet
        print(
            f"DEBUG [Analiz Detay]: Session'a kaydedilen arsa_data: {session['arsa_data']}"
        )  # Debug için

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
                "altyapi": altyapi,  # Model altyapıyı kullanıyorsa
            }

            # Tahmini yap
            tahmin_sonucu = tahmin_modeli.tahmin_yap(prediction_input_data)
            print(f"DEBUG [Analiz Detay]: Fiyat tahmini sonucu: {tahmin_sonucu}")

        except Exception as e:
            app.logger.error(f"Fiyat tahmini sırasında hata oluştu: {e}", exc_info=True)
            flash("Fiyat tahmini yapılırken bir sorun oluştu.", "warning")
        # --- YENİ: Fiyat Tahmini Entegrasyonu Sonu ---

        # Medya dosyalarını getir
        medyalar = (
            AnalizMedya.query.filter_by(analiz_id=analiz_id)
            .order_by(AnalizMedya.uploaded_at)
            .all()
        )

        # UUID oluştur (dosya adı için, detay sayfasında da gerekebilir)
        file_id = str(uuid.uuid4())

        return render_template(
            "analiz_detay.html",
            analiz=analiz,
            altyapi=altyapi,
            swot=swot_analizi,
            sonuc=analiz_sonuclari,
            ozet=ozet,
            user=user,  # Kullanıcı bilgilerini template'e gönder
            medyalar=medyalar,  # Medya dosyalarını template'e gönder
            file_id=file_id,  # Rapor oluşturma linkleri için file_id gönder
            tahmin=tahmin_sonucu,
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
            print(f"analiz.id: {analiz_id}")  # analiz_id'yi yazdır
            # Diğer analiz detaylarını yazdırmaya çalış (hata alabilir)
            # print(f"analiz.il: {getattr(analiz, 'il', None)}")
            # ...
        except Exception as inner_e:
            print(f"Ek veri yazılırken hata: {inner_e}")
        print("--- Çözüm Önerisi ---")
        print(
            "Lütfen analiz kaydındaki tüm sayısal alanların (metrekare, fiyat, bolge_fiyat, taks, kaks) boş veya None olmadığından emin olun."
        )
        print(
            "Veritabanında eksik veya hatalı veri varsa düzeltin. Gerekirse analiz kaydını silip tekrar oluşturun."
        )
        flash(
            "Analiz görüntülenirken bir hata oluştu. Detaylar için sunucu loglarını kontrol edin.",
            "danger",
        )
        flash("Analiz görüntülenirken bir hata oluştu.", "danger")
        return redirect(url_for("analizler"))


@app.route("/analizler")
@login_required
def analizler():
    user_id = session["user_id"]

    # Tüm illeri al (filtreleme için)
    iller = (
        db.session.query(ArsaAnaliz.il)
        .filter_by(user_id=user_id)
        .distinct()
        .order_by(ArsaAnaliz.il)
        .all()
    )
    iller = [il[0] for il in iller]

    # Analizleri al
    analizler = (
        ArsaAnaliz.query.filter_by(user_id=user_id)
        .order_by(ArsaAnaliz.created_at.desc())
        .all()
    )

    # Ay/yıl gruplandırması
    grouped_analizler = {}
    for analiz in analizler:
        ay_isimleri = {
            1: "Ocak",
            2: "Şubat",
            3: "Mart",
            4: "Nisan",
            5: "Mayıs",
            6: "Haziran",
            7: "Temmuz",
            8: "Ağustos",
            9: "Eylül",
            10: "Ekim",
            11: "Kasım",
            12: "Aralık",
        }
        key = f"{ay_isimleri[analiz.created_at.month]} {analiz.created_at.year}"
        if key not in grouped_analizler:
            grouped_analizler[key] = []
        grouped_analizler[key].append(analiz)

    return render_template(
        "analizler.html",
        grouped_analizler=grouped_analizler,
        total_count=len(analizler),
        iller=iller,
    )


@app.route("/analiz/sil/<int:analiz_id>", methods=["POST"])
@login_required
def analiz_sil(analiz_id):
    try:
        # Analizi bul
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)

        # Kullanıcının yetkisi var mı kontrol et
        if analiz.user_id != session["user_id"]:
            flash("Bu analizi silme yetkiniz yok.", "danger")
            return redirect(url_for("analizler"))

        # İstatistikleri güncelle (Decimal kullanarak)
        stats = DashboardStats.query.filter_by(user_id=session["user_id"]).first()
        if stats:
            stats.toplam_arsa_sayisi = max(
                0, stats.toplam_arsa_sayisi - 1
            )  # Negatife düşmesini engelle
            stats.toplam_deger = max(
                Decimal("0.00"), stats.toplam_deger - (analiz.fiyat or Decimal("0.00"))
            )

        # Bölge istatistiklerini güncelle (Decimal kullanarak)
        bolge = BolgeDagilimi.query.filter_by(
            user_id=session["user_id"], il=analiz.il
        ).first()
        if bolge:
            bolge.analiz_sayisi = max(0, bolge.analiz_sayisi - 1)
            bolge.toplam_deger = max(
                Decimal("0.00"), bolge.toplam_deger - (analiz.fiyat or Decimal("0.00"))
            )

            # Eğer bölgede başka analiz kalmadıysa bölgeyi sil
            if bolge.analiz_sayisi <= 0:
                db.session.delete(bolge)

        # İlişkili medya dosyalarını sil
        medyalar = AnalizMedya.query.filter_by(analiz_id=analiz_id).all()
        for medya in medyalar:
            try:
                # Dosya yolunu oluştur (medya.filename analiz_id/dosyaadi şeklinde olmalı)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], medya.filename)
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
        analiz_folder = os.path.join(app.config["UPLOAD_FOLDER"], str(analiz_id))
        try:
            if os.path.exists(analiz_folder) and not os.listdir(analiz_folder):
                os.rmdir(analiz_folder)
                print(f"DEBUG: Boş analiz klasörü silindi: {analiz_folder}")
        except Exception as e:
            print(f"Analiz klasörü silinirken hata ({analiz_folder}): {e}")

        # Analizi sil
        db.session.delete(analiz)
        db.session.commit()

        flash("Analiz ve ilişkili medyalar başarıyla silindi.", "success")
        return redirect(url_for("analizler"))

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting analysis: {str(e)}")
        flash("Analiz silinirken bir hata oluştu.", "danger")
        return redirect(url_for("analizler"))


@app.route("/analiz/<int:analiz_id>/medya_yukle", methods=["POST"])
@login_required
def medya_yukle(analiz_id):
    # Önce analizin kullanıcıya ait olup olmadığını kontrol et
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != session["user_id"]:
        flash("Bu analize medya yükleme yetkiniz yok.", "danger")
        return redirect(url_for("analizler"))

    if "medya" not in request.files:
        flash("Dosya seçilmedi.", "warning")
        return redirect(url_for("analiz_detay", analiz_id=analiz_id))
    file = request.files["medya"]
    if file.filename == "":
        flash("Dosya seçilmedi.", "warning")
        return redirect(url_for("analiz_detay", analiz_id=analiz_id))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit(".", 1)[1].lower()
        medya_type = "image" if ext in {"jpg", "jpeg", "png", "gif"} else "video"

        # Analize özel klasör oluştur
        analiz_folder = os.path.join(app.config["UPLOAD_FOLDER"], str(analiz_id))
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
            medya = AnalizMedya(
                analiz_id=analiz_id, filename=db_filename, type=medya_type
            )
            db.session.add(medya)
            db.session.commit()
            flash("Medya başarıyla yüklendi.", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Medya kaydetme hatası: {e}")
            flash("Medya yüklenirken bir hata oluştu.", "danger")

    else:
        flash("Geçersiz dosya türü.", "danger")
    return redirect(url_for("analiz_detay", analiz_id=analiz_id))


@app.route("/analiz/<int:analiz_id>/medya_sil/<int:medya_id>", methods=["POST"])
@login_required
def medya_sil(analiz_id, medya_id):
    medya = AnalizMedya.query.get_or_404(medya_id)
    # Analizin kullanıcıya ait olup olmadığını ve medyanın bu analize ait olup olmadığını kontrol et
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != session["user_id"] or medya.analiz_id != analiz_id:
        flash("Yetkisiz işlem.", "danger")
        return redirect(url_for("analiz_detay", analiz_id=analiz_id))

    try:
        # Dosyayı sil (medya.filename 'analiz_id/dosyaadi' formatında)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], medya.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"DEBUG: Silinen medya: {filepath}")
        else:
            print(f"DEBUG: Silinecek medya bulunamadı: {filepath}")

        db.session.delete(medya)
        db.session.commit()
        flash("Medya silindi.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Medya silme hatası: {e}")
        flash("Medya silinirken bir hata oluştu.", "danger")

    return redirect(url_for("analiz_detay", analiz_id=analiz_id))


@app.route("/portfolios")
@login_required
def portfolios():
    # Join ile User bilgilerini de getir
    analizler = (
        ArsaAnaliz.query.join(User)
        .add_columns(User.ad, User.soyad)
        .filter(User.is_active == True)
        .order_by(ArsaAnaliz.created_at.desc())
        .all()
    )

    return render_template("portfolios.html", analizler=analizler)


@app.route("/portfolio/create", methods=["GET", "POST"])
@login_required
def portfolio_create():
    if request.method == "POST":
        try:
            # Yeni portföy oluştur
            portfolio = Portfolio(
                user_id=session["user_id"],
                title=request.form.get("title"),
                description=request.form.get("description"),
                visibility=request.form.get("visibility", "public"),
            )

            # Veritabanına kaydet
            db.session.add(portfolio)
            db.session.commit()

            flash("Portföy başarıyla oluşturuldu.", "success")
            return redirect(url_for("portfolios"))

        except Exception as e:
            db.session.rollback()
            flash("Portföy oluşturulurken bir hata oluştu.", "danger")
            print(f"Portfolio creation error: {str(e)}")

    # GET isteği için form sayfasını göster
    return render_template("portfolio_create.html")


@app.route("/portfolio/<int:id>")
@login_required
def portfolio_detail(id):
    portfolio = Portfolio.query.get_or_404(id)

    # Portföy private ise ve kullanıcının kendi portföyü değilse erişimi engelle
    if portfolio.visibility == "private" and portfolio.user_id != session["user_id"]:
        flash("Bu portföye erişim yetkiniz yok.", "danger")
        return redirect(url_for("portfolios"))

    return render_template("portfolio_detail.html", portfolio=portfolio)

# app.py

# ... diğer route'lar ...



DEAL_STAGES = ["Potansiyel", "Görüşme Planlandı", "Teklif Sunuldu", "Müzakere", "Kazanıldı", "Kaybedildi", "Beklemede"]

@app.route("/crm/deals")
@login_required
def crm_deals_list():
    user_id = session["user_id"]
    # Tüm fırsatları veya belirli bir filtreye göre alabiliriz
    deals_query = Deal.query.filter_by(user_id=user_id)
    
    # Kanban görünümü için aşamalara göre gruplandırma
    deals_by_stage = {}
    for stage in DEAL_STAGES:
        deals_by_stage[stage] = deals_query.filter_by(stage=stage).order_by(Deal.expected_close_date.asc()).all()
    
    # Henüz bir aşamaya atanmamış veya DEALS_STAGES dışında bir aşamada olanlar (opsiyonel)
    # other_deals = deals_query.filter(Deal.stage.notin_(DEAL_STAGES)).order_by(Deal.created_at.desc()).all()
    # if other_deals:
    #     deals_by_stage["Diğer"] = other_deals

    return render_template("crm/deals_list.html", deals_by_stage=deals_by_stage, stages=DEAL_STAGES, title="Fırsatlar")

@app.route("/crm/deal/new", methods=["GET", "POST"])
@login_required
def crm_deal_new():
    user_id = session["user_id"]
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        title = request.form.get("title")
        contact_id_str = request.form.get("contact_id")
        company_id_str = request.form.get("company_id")
        value_str = request.form.get("value", "0").replace(",", "") # Virgülü temizle
        currency = request.form.get("currency", "TRY")
        stage = request.form.get("stage", DEAL_STAGES[0]) # Varsayılan ilk aşama
        expected_close_date_str = request.form.get("expected_close_date")
        notes = request.form.get("notes")

        if not title or not contact_id_str:
            flash("Fırsat başlığı ve birincil kontak zorunludur.", "danger")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)

        try:
            value = Decimal(value_str) if value_str else Decimal("0.00")
        except:
            flash("Geçersiz değer formatı. Lütfen sayısal bir değer girin (örn: 1500.50).", "danger")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)
        
        expected_close_date = None
        if expected_close_date_str:
            try:
                expected_close_date = datetime.strptime(expected_close_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Geçersiz beklenen kapanış tarihi formatı. Lütfen YYYY-AA-GG formatında girin.", "danger")
                return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)

        try:
            new_deal = Deal(
                user_id=user_id,
                title=title,
                contact_id=int(contact_id_str),
                company_id=int(company_id_str) if company_id_str else None,
                value=value,
                currency=currency,
                stage=stage,
                expected_close_date=expected_close_date,
                notes=notes
            )
            db.session.add(new_deal)
            db.session.commit()
            flash(f"'{new_deal.title}' adlı fırsat başarıyla eklendi.", "success")
            return redirect(url_for("crm_deals_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Fırsat eklenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Deal New Error: {e}")
            return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES, deal=request.form)

    return render_template("crm/deal_form.html", title="Yeni Fırsat Ekle", contacts=contacts, companies=companies, stages=DEAL_STAGES)

# app.py

# ... (diğer importlar ve route'lar) ...

@app.route("/crm/tasks")
@login_required
def crm_tasks_list():
    user_id = session["user_id"]
    tasks_query = Task.query.filter_by(user_id=user_id)
    
    filter_status = request.args.get('status')
    if filter_status and filter_status in TASK_STATUSES:
        tasks_query = tasks_query.filter_by(status=filter_status)
    
    tasks = tasks_query.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"), # NULL olanlar sona (1 > 0)
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()
    
    return render_template("crm/tasks_list.html", tasks=tasks, title="Görevler", statuses=TASK_STATUSES, current_status=filter_status)
# --- Görev (Task) CRUD Fonksiyonları ---

TASK_STATUSES = ["Beklemede", "Devam Ediyor", "Tamamlandı", "İptal Edildi", "Ertelendi"]
TASK_PRIORITIES = ["Düşük", "Normal", "Yüksek", "Acil"]






@app.route("/crm/task/new", methods=["GET", "POST"])
@app.route("/crm/contact/<int:contact_id>/task/new", methods=["GET", "POST"])
@app.route("/crm/deal/<int:deal_id>/task/new", methods=["GET", "POST"])
@login_required
def crm_task_new(contact_id=None, deal_id=None): # contact_id ve deal_id opsiyonel
    user_id = session["user_id"]
    # Form için ilgili kontakları, fırsatları ve kullanıcıları (atanacak kişi için) al
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name).all()
    deals = Deal.query.filter_by(user_id=user_id).order_by(Deal.title).all()
    # users_for_assignment = User.query.filter_by(is_active=True).order_by(User.ad).all() # Eğer başkasına atama olacaksa

    # URL'den gelen contact_id veya deal_id varsa, formda seçili gelsin
    preselected_contact = Contact.query.get(contact_id) if contact_id else None
    preselected_deal = Deal.query.get(deal_id) if deal_id else None

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        due_date_str = request.form.get("due_date")
        status = request.form.get("status", TASK_STATUSES[0])
        priority = request.form.get("priority", TASK_PRIORITIES[1])
        
        # Formdan gelen contact_id ve deal_id'yi al (URL'den geleni değil, formdakini)
        posted_contact_id_str = request.form.get("contact_id")
        posted_deal_id_str = request.form.get("deal_id")
        # assigned_to_user_id_str = request.form.get("assigned_to_user_id")

        if not title:
            flash("Görev başlığı zorunludur.", "danger")
            return render_template("crm/task_form.html", title="Yeni Görev Ekle", 
                                   contacts=contacts, deals=deals, # users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES,
                                   preselected_contact=preselected_contact, preselected_deal=preselected_deal,
                                   task=request.form)
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M") # datetime-local için
            except ValueError:
                flash("Geçersiz bitiş tarihi formatı.", "danger")
                return render_template("crm/task_form.html", title="Yeni Görev Ekle", 
                                   contacts=contacts, deals=deals, # users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES,
                                   preselected_contact=preselected_contact, preselected_deal=preselected_deal,
                                   task=request.form)
        try:
            new_task = Task(
                user_id=user_id, # Oluşturan kullanıcı
                title=title,
                description=description,
                due_date=due_date,
                status=status,
                priority=priority,
                contact_id=int(posted_contact_id_str) if posted_contact_id_str else None,
                deal_id=int(posted_deal_id_str) if posted_deal_id_str else None,
                assigned_to_user_id=user_id # Şimdilik oluşturan kişiye ata
                # assigned_to_user_id=int(assigned_to_user_id_str) if assigned_to_user_id_str else user_id 
            )
            db.session.add(new_task)
            db.session.commit()
            flash(f"'{new_task.title}' adlı görev başarıyla eklendi.", "success")
            
            if new_task.deal_id:
                return redirect(url_for("crm_deal_detail", deal_id=new_task.deal_id))
            elif new_task.contact_id:
                return redirect(url_for("crm_contact_detail", contact_id=new_task.contact_id))
            return redirect(url_for("crm_tasks_list"))

        except Exception as e:
            db.session.rollback()
            flash(f"Görev eklenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Task New Error: {e}")
            return render_template("crm/task_form.html", title="Yeni Görev Ekle", 
                                   contacts=contacts, deals=deals, # users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES,
                                   preselected_contact=preselected_contact, preselected_deal=preselected_deal,
                                   task=request.form)

    return render_template("crm/task_form.html", title="Yeni Görev Ekle",
                           contacts=contacts, deals=deals, # users_for_assignment=users_for_assignment,
                           statuses=TASK_STATUSES, priorities=TASK_PRIORITIES,
                           preselected_contact=preselected_contact, preselected_deal=preselected_deal)


@app.route("/crm/task/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def crm_task_edit(task_id):
    user_id = session["user_id"]
    # Kullanıcının ya oluşturduğu ya da kendisine atanan görevi düzenlemesine izin ver
    task_to_edit = Task.query.filter(Task.id == task_id, (Task.user_id == user_id) | (Task.assigned_to_user_id == user_id)).first_or_404()
    
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name).all()
    deals = Deal.query.filter_by(user_id=user_id).order_by(Deal.title).all()
    # users_for_assignment = User.query.filter_by(is_active=True).order_by(User.ad).all()

    if request.method == "POST":
        task_to_edit.title = request.form.get("title")
        task_to_edit.description = request.form.get("description")
        due_date_str = request.form.get("due_date")
        task_to_edit.status = request.form.get("status")
        task_to_edit.priority = request.form.get("priority")
        task_to_edit.contact_id = int(request.form.get("contact_id")) if request.form.get("contact_id") else None
        task_to_edit.deal_id = int(request.form.get("deal_id")) if request.form.get("deal_id") else None
        # task_to_edit.assigned_to_user_id = int(request.form.get("assigned_to_user_id")) if request.form.get("assigned_to_user_id") else user_id

        if not task_to_edit.title:
            flash("Görev başlığı zorunludur.", "danger")
            return render_template("crm/task_form.html", title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit,
                                   contacts=contacts, deals=deals, #users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True)
        
        if due_date_str:
            try:
                task_to_edit.due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Geçersiz bitiş tarihi formatı.", "danger")
                return render_template("crm/task_form.html", title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit,
                                   contacts=contacts, deals=deals, #users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True)
        else:
            task_to_edit.due_date = None
        
        try:
            db.session.commit()
            flash(f"'{task_to_edit.title}' adlı görev başarıyla güncellendi.", "success")
            if task_to_edit.deal_id:
                return redirect(url_for("crm_deal_detail", deal_id=task_to_edit.deal_id))
            elif task_to_edit.contact_id:
                return redirect(url_for("crm_contact_detail", contact_id=task_to_edit.contact_id))
            return redirect(url_for("crm_tasks_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Görev güncellenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Task Edit Error: {e}")
            return render_template("crm/task_form.html", title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit,
                                   contacts=contacts, deals=deals, #users_for_assignment=users_for_assignment,
                                   statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True)

    return render_template("crm/task_form.html", title=f"Görevi Düzenle: {task_to_edit.title}", task=task_to_edit,
                           contacts=contacts, deals=deals, #users_for_assignment=users_for_assignment,
                           statuses=TASK_STATUSES, priorities=TASK_PRIORITIES, edit_mode=True)


@app.route("/crm/task/<int:task_id>/delete", methods=["POST"])
@login_required
def crm_task_delete(task_id):
    user_id = session["user_id"]
    task_to_delete = Task.query.filter(Task.id == task_id, (Task.user_id == user_id) | (Task.assigned_to_user_id == user_id)).first_or_404()
    
    # Yönlendirme için bilgileri sakla
    redirect_url = url_for('crm_tasks_list')
    if task_to_delete.deal_id:
        redirect_url = url_for('crm_deal_detail', deal_id=task_to_delete.deal_id)
    elif task_to_delete.contact_id:
        redirect_url = url_for('crm_contact_detail', contact_id=task_to_delete.contact_id)

    try:
        task_title = task_to_delete.title
        db.session.delete(task_to_delete)
        db.session.commit()
        flash(f"'{task_title}' adlı görev başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Görev silinirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Task Delete Error: {e}")

    return redirect(redirect_url)

# Bir görevin durumunu hızlıca güncellemek için (örn: Tamamlandı olarak işaretle)
@app.route("/crm/task/<int:task_id>/toggle_status", methods=["POST"])
@login_required
def crm_task_toggle_status(task_id):
    user_id = session["user_id"]
    task = Task.query.filter(Task.id == task_id, (Task.user_id == user_id) | (Task.assigned_to_user_id == user_id)).first_or_404()
    
    new_status_form = request.form.get("new_status") # Formdan yeni durum gelebilir

    if new_status_form and new_status_form in TASK_STATUSES:
        task.status = new_status_form
    elif task.status == "Tamamlandı":
        task.status = "Devam Ediyor" # Veya "Beklemede"
    else:
        task.status = "Tamamlandı"
    
    try:
        db.session.commit()
        flash(f"'{task.title}' görevinin durumu '{task.status}' olarak güncellendi.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Görev durumu güncellenirken hata: {str(e)}", "danger")
        app.logger.error(f"CRM Task Toggle Status Error: {e}")

    # AJAX isteği olup olmadığını kontrol et (daha sonra geliştirilebilir)
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('crm_tasks_list'))

# --- Görev (Task) CRUD Fonksiyonları Sonu ---

@app.route("/crm/deal/<int:deal_id>/update_stage", methods=["POST"])
@login_required
def crm_deal_update_stage(deal_id):
    user_id = session["user_id"]
    deal_to_update = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()

    data = request.get_json()
    new_stage = data.get("stage")
    # new_index = data.get("new_index") # İsteğe bağlı: Sıralamayı da kaydetmek isterseniz

    if not new_stage:
        return jsonify({"success": False, "message": "Yeni aşama bilgisi eksik."}), 400

    if new_stage not in DEAL_STAGES: # DEAL_STAGES listesini kontrol et
        return jsonify({"success": False, "message": f"Geçersiz aşama: {new_stage}"}), 400

    try:
        old_stage = deal_to_update.stage
        deal_to_update.stage = new_stage
        
        # Eğer aşama "Kazanıldı" veya "Kaybedildi" ise ve fiili kapanış tarihi yoksa, bugünün tarihini ata
        if new_stage in ["Kazanıldı", "Kaybedildi"] and not deal_to_update.actual_close_date:
            deal_to_update.actual_close_date = datetime.utcnow().date()

        # Eğer aşama "Kazanıldı" veya "Kaybedildi" durumundan çıkıyorsa, fiili kapanış tarihini temizle
        elif old_stage in ["Kazanıldı", "Kaybedildi"] and new_stage not in ["Kazanıldı", "Kaybedildi"]:
            deal_to_update.actual_close_date = None

        # İsteğe bağlı: Eğer sıralamayı da kaydediyorsanız, burada deal_to_update.order = new_index gibi bir şey yapabilirsiniz.
        # Bunun için Deal modelinize bir `order` (integer) alanı eklemeniz gerekir.

        db.session.commit()
        return jsonify({
            "success": True, 
            "message": "Fırsat aşaması güncellendi.", 
            "deal_id": deal_to_update.id,
            "deal_stage": deal_to_update.stage,
            "actual_close_date": deal_to_update.actual_close_date.strftime('%Y-%m-%d') if deal_to_update.actual_close_date else None
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"CRM Deal Update Stage Error: {e}")
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(e)}"}), 500


@app.route("/crm/deal/<int:deal_id>")
@login_required
def crm_deal_detail(deal_id):
    user_id = session["user_id"]
    deal = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    interactions = deal.interactions.order_by(Interaction.interaction_date.desc()).all()
    
    tasks = deal.tasks.order_by(
        text("CASE WHEN crm_tasks.due_date IS NULL THEN 1 ELSE 0 END"),
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()
    
    return render_template(
        "crm/deal_detail.html",
        deal=deal,
        title=deal.title,
        interactions=interactions,
        tasks=tasks
    )

@app.route("/crm/deal/<int:deal_id>/edit", methods=["GET", "POST"])
@login_required
def crm_deal_edit(deal_id):
    user_id = session["user_id"]
    deal_to_edit = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()
    contacts = Contact.query.filter_by(user_id=user_id).order_by(Contact.last_name, Contact.first_name).all()
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()

    if request.method == "POST":
        deal_to_edit.title = request.form.get("title")
        contact_id_str = request.form.get("contact_id")
        company_id_str = request.form.get("company_id")
        value_str = request.form.get("value", "0").replace(",", "")
        deal_to_edit.currency = request.form.get("currency", "TRY")
        deal_to_edit.stage = request.form.get("stage")
        expected_close_date_str = request.form.get("expected_close_date")
        actual_close_date_str = request.form.get("actual_close_date") # Kazanıldı/Kaybedildi durumunda
        deal_to_edit.notes = request.form.get("notes")

        if not deal_to_edit.title or not contact_id_str:
            flash("Fırsat başlığı ve birincil kontak zorunludur.", "danger")
            return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

        try:
            deal_to_edit.value = Decimal(value_str) if value_str else Decimal("0.00")
        except:
            flash("Geçersiz değer formatı.", "danger")
            return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

        deal_to_edit.contact_id = int(contact_id_str)
        deal_to_edit.company_id = int(company_id_str) if company_id_str else None
        
        if expected_close_date_str:
            try:
                deal_to_edit.expected_close_date = datetime.strptime(expected_close_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Geçersiz beklenen kapanış tarihi formatı.", "danger")
                return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)
        else:
            deal_to_edit.expected_close_date = None

        if deal_to_edit.stage in ["Kazanıldı", "Kaybedildi"] and actual_close_date_str:
            try:
                deal_to_edit.actual_close_date = datetime.strptime(actual_close_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Geçersiz fiili kapanış tarihi formatı.", "danger")
                return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)
        elif deal_to_edit.stage not in ["Kazanıldı", "Kaybedildi"]:
             deal_to_edit.actual_close_date = None # Eğer kazanıldı/kaybedildi değilse fiili tarihi temizle

        try:
            db.session.commit()
            flash(f"'{deal_to_edit.title}' adlı fırsat başarıyla güncellendi.", "success")
            return redirect(url_for("crm_deal_detail", deal_id=deal_to_edit.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Fırsat güncellenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Deal Edit Error: {e}")
            return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

    return render_template("crm/deal_form.html", title=f"Fırsat Düzenle: {deal_to_edit.title}", deal=deal_to_edit, contacts=contacts, companies=companies, stages=DEAL_STAGES, edit_mode=True)

@app.route("/crm/deal/<int:deal_id>/delete", methods=["POST"])
@login_required
def crm_deal_delete(deal_id):
    user_id = session["user_id"]
    deal_to_delete = Deal.query.filter_by(id=deal_id, user_id=user_id).first_or_404()

    # Deal modelindeki interactions ve tasks ilişkilerinde cascade delete kullandık,
    # bu yüzden bağlı etkileşimler ve görevler otomatik silinecektir.
    try:
        deal_title = deal_to_delete.title
        db.session.delete(deal_to_delete)
        db.session.commit()
        flash(f"'{deal_title}' adlı fırsat başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Fırsat silinirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Deal Delete Error: {e}")

    return redirect(url_for("crm_deals_list"))

# --- Fırsat (Deal) CRUD Fonksiyonları Sonu ---



@app.route("/crm/contact/<int:contact_id>/delete", methods=["POST"]) # Genellikle POST ile yapılır
@login_required
def crm_contact_delete(contact_id):
    user_id = session["user_id"]
    contact_to_delete = Contact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()

    try:
        # İlişkili kayıtların durumu (cascade silme modelde ayarlandıysa otomatik olur)
        # Eğer cascade ayarlanmadıysa, önce ilişkili Interaction, Deal, Task vb. silmeniz gerekebilir.
        # Modellerimizde cascade="all, delete-orphan" kullandığımız için bu otomatik olmalı.
        
        contact_name = f"{contact_to_delete.first_name} {contact_to_delete.last_name}"
        db.session.delete(contact_to_delete)
        db.session.commit()
        flash(f"'{contact_name}' adlı kişi başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Kişi silinirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Contact Delete Error: {e}")

    return redirect(url_for("crm_contacts_list"))



@app.route("/crm/companies")
@login_required
def crm_companies_list():
    user_id = session["user_id"]
    companies = Company.query.filter_by(user_id=user_id).order_by(Company.name).all()
    return render_template("crm/companies_list.html", companies=companies, title="Şirketler")

@app.route("/crm/company/new", methods=["GET", "POST"])
@login_required
def crm_company_new():
    if request.method == "POST":
        user_id = session["user_id"]
        name = request.form.get("name")
        industry = request.form.get("industry")
        website = request.form.get("website")
        address = request.form.get("address")
        phone = request.form.get("phone")
        notes = request.form.get("notes")

        if not name:
            flash("Şirket adı zorunludur.", "danger")
            return render_template("crm/company_form.html", title="Yeni Şirket Ekle", company=request.form)

        # Şirket adı benzersizlik kontrolü (kullanıcı bazında)
        existing_company = Company.query.filter_by(user_id=user_id, name=name).first()
        if existing_company:
            flash(f"'{name}' adlı şirket zaten mevcut.", "warning")
            return render_template("crm/company_form.html", title="Yeni Şirket Ekle", company=request.form)

        try:
            new_company = Company(
                user_id=user_id,
                name=name,
                industry=industry,
                website=website,
                address=address,
                phone=phone,
                notes=notes
            )
            db.session.add(new_company)
            db.session.commit()
            flash(f"'{new_company.name}' adlı şirket başarıyla eklendi.", "success")
            return redirect(url_for("crm_companies_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Şirket eklenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Company New Error: {e}")

    return render_template("crm/company_form.html", title="Yeni Şirket Ekle")

@app.route("/crm/company/<int:company_id>")
@login_required
def crm_company_detail(company_id):
    user_id = session["user_id"]
    company = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()
    company_contacts = company.contacts.order_by(Contact.last_name).all()
    company_deals = company.deals.order_by(Deal.created_at.desc()).all()
    return render_template(
        "crm/company_detail.html",
        company=company,
        title=company.name,
        company_contacts=company_contacts, 
        company_deals=company_deals
    )

@app.route("/crm/company/<int:company_id>/edit", methods=["GET", "POST"])
@login_required
def crm_company_edit(company_id):
    user_id = session["user_id"]
    company_to_edit = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()

    if request.method == "POST":
        new_name = request.form.get("name")
        company_to_edit.industry = request.form.get("industry")
        company_to_edit.website = request.form.get("website")
        company_to_edit.address = request.form.get("address")
        company_to_edit.phone = request.form.get("phone")
        company_to_edit.notes = request.form.get("notes")

        if not new_name:
            flash("Şirket adı zorunludur.", "danger")
            return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)

        # Şirket adı benzersizlik kontrolü (kullanıcı bazında, mevcut şirket hariç)
        if new_name != company_to_edit.name:
            existing_company = Company.query.filter(
                Company.user_id == user_id,
                Company.name == new_name,
                Company.id != company_id
            ).first()
            if existing_company:
                flash(f"'{new_name}' adlı başka bir şirket zaten mevcut.", "warning")
                return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)
        
        company_to_edit.name = new_name

        try:
            db.session.commit()
            flash(f"'{company_to_edit.name}' adlı şirket başarıyla güncellendi.", "success")
            return redirect(url_for("crm_company_detail", company_id=company_to_edit.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Şirket güncellenirken bir hata oluştu: {str(e)}", "danger")
            app.logger.error(f"CRM Company Edit Error: {e}")
            return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)

    return render_template("crm/company_form.html", title=f"Şirket Düzenle: {company_to_edit.name}", company=company_to_edit)

@app.route("/crm/company/<int:company_id>/delete", methods=["POST"])
@login_required
def crm_company_delete(company_id):
    user_id = session["user_id"]
    company_to_delete = Company.query.filter_by(id=company_id, user_id=user_id).first_or_404()

    # ÖNEMLİ: Bir şirket silinmeden önce, ona bağlı kişilerin (Contacts)
    # company_id alanlarının ne olacağına karar vermelisiniz.
    # Seçenekler:
    # 1. Bağlı kişilerin company_id'sini NULL yapmak:
    #    for contact in company_to_delete.contacts:
    #        contact.company_id = None
    #    db.session.commit() # Kişileri güncelledikten sonra commit
    # 2. Şirketle birlikte kişileri de silmek (Eğer Contact modelinde company ilişkisi cascade delete ise)
    #    Bu genellikle istenmez, kişiler farklı bir şirkete atanabilir.
    # 3. Silmeyi engellemek (Eğer şirkete bağlı kişiler varsa).
    #    if company_to_delete.contacts.first():
    #        flash(f"'{company_to_delete.name}' adlı şirkete bağlı kişiler bulunduğu için silinemez. Önce kişilerin şirket bağlantısını kaldırın.", "warning")
    #        return redirect(url_for("crm_companies_list"))

    # Şimdilik 1. seçeneği uygulayalım (bağlı kişilerin şirketini null yapalım)
    # Bu, Contact modelindeki company ilişkisinin `nullable=True` olmasını gerektirir (ki öyle tanımlamıştık).
    try:
        company_name = company_to_delete.name
        
        # Bağlı kişilerin company_id'lerini null yap
        updated_contacts_count = Contact.query.filter_by(company_id=company_id, user_id=user_id).update({"company_id": None})
        if updated_contacts_count > 0:
             app.logger.info(f"{updated_contacts_count} kişinin şirket bağlantısı '{company_name}' şirketinden kaldırıldı.")
        
        # Bağlı fırsatların company_id'lerini null yap (eğer Deal modelinde cascade delete yoksa)
        # Deal modelindeki company ilişkisinde cascade delete olmadığı için bunu manuel yapmalıyız.
        updated_deals_count = Deal.query.filter_by(company_id=company_id, user_id=user_id).update({"company_id": None})
        if updated_deals_count > 0:
            app.logger.info(f"{updated_deals_count} fırsatın şirket bağlantısı '{company_name}' şirketinden kaldırıldı.")

        db.session.delete(company_to_delete)
        db.session.commit()
        flash(f"'{company_name}' adlı şirket başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Şirket silinirken bir hata oluştu: {str(e)}", "danger")
        app.logger.error(f"CRM Company Delete Error: {e}")

    return redirect(url_for("crm_companies_list"))

# --- Şirket (Company) CRUD Fonksiyonları Sonu ---

@app.route("/analysis-form")
@login_required
def analysis_form():
    return render_template("analysis_form.html")


@app.route("/generate/pptx/<int:analiz_id>", methods=["POST"])
def generate_pptx(analiz_id):
    try:
        # Form verilerini kontrol et
        print("DEBUG: Gelen form verileri:", request.form)

        # Sections verisini al ve kontrol et
        sections_data = request.form.get("sections")
        color_scheme = request.form.get(
            "color_scheme", "blue"
        )  # Varsayılan değer 'blue'

        if not sections_data:
            sections = []
        else:
            try:
                sections = json.loads(sections_data)
                if not isinstance(sections, list):
                    sections = []
            except json.JSONDecodeError:
                sections = []

        print("DEBUG: Parsed sections:", sections)
        print("DEBUG: Color scheme:", color_scheme)

        # Analiz ve kullanıcı verilerini al
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        user = User.query.get(analiz.user_id)

        # JSON için veri yapısını oluştur
        temp_data = {
            "analiz": {
                "id": analiz.id,
                "il": analiz.il,
                "ilce": analiz.ilce,
                "mahalle": analiz.mahalle,
                "ada": analiz.ada,
                "parsel": analiz.parsel,
                "metrekare": float(analiz.metrekare),
                "imar_durumu": analiz.imar_durumu,
                "taks": float(analiz.taks),
                "kaks": float(analiz.kaks),
                "fiyat": float(analiz.fiyat) if analiz.fiyat else 0,
                "bolge_fiyat": (
                    float(analiz.fiyat)
                    if (
                        analiz.bolge_fiyat is None or analiz.bolge_fiyat == Decimal("0")
                    )
                    else float(analiz.bolge_fiyat)
                ),
                "altyapi": (
                    json.loads(analiz.altyapi)
                    if isinstance(analiz.altyapi, str)
                    else analiz.altyapi
                ),
                "swot": (
                    json.loads(analiz.swot_analizi)
                    if isinstance(analiz.swot_analizi, str)
                    else analiz.swot_analizi
                ),
                "created_at": analiz.created_at.strftime("%d.%m.%Y %H:%M"),
            },
            "user": {
                "ad": user.ad,
                "soyad": user.soyad,
                "email": user.email,
                "telefon": user.telefon,
                "firma": user.firma,
                "unvan": user.unvan,
                "adres": user.adres,
                "profil_foto": user.profil_foto,
            },
        }

        # DocumentGenerator'ı çağır
        file_id = str(uuid.uuid4())
        output_dir = os.path.join(app.config["UPLOAD_FOLDER"], "presentations", file_id)
        os.makedirs(output_dir, exist_ok=True)

        doc_gen = DocumentGenerator(
            temp_data["analiz"],
            analiz_ozeti=None,
            file_id=file_id,
            output_dir=output_dir,
            profile_info=temp_data["user"],
            settings={
                "sections": sections,
                "color_scheme": color_scheme,  # color_scheme ekle
            },
        )

        pptx_path = doc_gen.create_pptx()

        if pptx_path and os.path.exists(pptx_path):
            return send_file(
                pptx_path,
                as_attachment=True,
                download_name=f"analiz_sunum_{analiz_id}.pptx",
            )
        else:
            return jsonify({"error": "Sunum oluşturulamadı"}), 500

    except Exception as e:
        print(f"HATA [Generate PPTX]: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/submit_analysis", methods=["POST"])
@login_required
def submit_analysis():
    try:
        user_id = session["user_id"]
        form_data = request.form.to_dict(flat=True)
        altyapi_list = request.form.getlist("altyapi[]")
        form_data["altyapi[]"] = altyapi_list

        print("Raw form data:", form_data)
        print("Altyapı verileri:", altyapi_list)
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            print(f"SWOT {key}:", form_data.get(key, "Yok"))

        # --- Sunucu Tarafı Validasyon Başlangıcı ---
        errors = []
        required_fields = {
            "il": "İl",
            "ilce": "İlçe",
            "mahalle": "Mahalle",
            "ada": "Ada No",
            "parsel": "Parsel No",
            "metrekare": "Metrekare",
            "imar_durumu": "İmar Durumu",
            "maliyet": "Maliyet",
            "guncel_deger": "Güncel Değer",
            "tarih": "Alım Tarihi",
        }

        for field, label in required_fields.items():
            if not form_data.get(field):
                errors.append(f"{label} alanı zorunludur.")

        # Sayısal Alan Kontrolleri
        numeric_fields = {
            "metrekare": "Metrekare",
            "taks": "TAKS",
            "kaks": "KAKS",
            "maliyet": "Maliyet",
            "guncel_deger": "Güncel Değer",
            "deger_artis_orani": "Yıllık Değer Artış Oranı",
        }
        for field, label in numeric_fields.items():
            value_str = form_data.get(field, "").replace(",", "").strip()
            if value_str:  # Alan boş değilse kontrol et
                try:
                    value_float = float(value_str)
                    if value_float < 0:
                        errors.append(f"{label} değeri negatif olamaz.")
                    # Ekstra aralık kontrolleri eklenebilir (örn: TAKS 0-1 arası)
                    if field == "taks" and not (0 <= value_float <= 1):
                        errors.append(f"{label} değeri 0 ile 1 arasında olmalıdır.")
                    if field == "deger_artis_orani" and not (0 <= value_float <= 100):
                        errors.append(f"{label} değeri 0 ile 100 arasında olmalıdır.")
                except ValueError:
                    errors.append(f"{label} alanı geçerli bir sayı olmalıdır.")

        # Tarih Format Kontrolü
        tarih_str = form_data.get("tarih", "")
        if tarih_str:
            try:
                datetime.strptime(tarih_str, "%Y-%m-%d")
            except ValueError:
                errors.append(
                    "Alım Tarihi geçerli bir formatta (YYYY-MM-DD) olmalıdır."
                )

        # String Uzunluk Kontrolleri (Modele göre)
        length_checks = {
            "il": 50,
            "ilce": 50,
            "mahalle": 100,
            "ada": 20,
            "parsel": 20,
            "koordinatlar": 100,
            "pafta": 50,
            "imar_durumu": 50,
        }
        for field, max_len in length_checks.items():
            value = form_data.get(field, "")
            if len(value) > max_len:
                errors.append(
                    f"{required_fields.get(field, field).capitalize()} alanı {max_len} karakterden uzun olamaz."
                )

        # SWOT JSON Kontrolü
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            try:
                json.loads(form_data.get(key, "[]"))
            except json.JSONDecodeError:
                errors.append(f"SWOT {key.capitalize()} verisi geçersiz formatta.")

        if errors:
            for error in errors:
                flash(error, "danger")
            # Form verilerini session'da saklayarak kullanıcıya geri gönderebiliriz (isteğe bağlı iyileştirme)
            # session['form_data_temp'] = form_data
            return redirect(url_for("analysis_form"))
        # --- Sunucu Tarafı Validasyon Sonu ---

        # Convert numeric values (validasyon başarılıysa)
        try:
            metrekare = float(str(form_data.get("metrekare")).replace(",", "").strip())
            maliyet = float(str(form_data.get("maliyet")).replace(",", "").strip())
            guncel_deger = float(
                str(form_data.get("guncel_deger")).replace(",", "").strip()
            )
            taks = float(str(form_data.get("taks", "0.3")).replace(",", "").strip())
            kaks = float(str(form_data.get("kaks", "1.5")).replace(",", "").strip())

            print(
                f"Dönüştürülmüş değerler - metrekare: {metrekare}, maliyet: {maliyet}, güncel değer: {guncel_deger}"
            )

            # Değerleri sınırla (Bu kısım önceki adımlarda eklendi)
            if metrekare > 9999999.99:
                metrekare = 9999999.99
                flash(
                    "Metrekare değeri çok büyük, maksimum değer ile sınırlandı.",
                    "warning",
                )
            if maliyet > 9999999999999.99:
                maliyet = 9999999999999.99
                flash(
                    "Maliyet değeri çok büyük, maksimum değer ile sınırlandı.",
                    "warning",
                )
            if guncel_deger > 9999999999999.99:
                guncel_deger = 9999999999999.99
                flash(
                    "Güncel değer değeri çok büyük, maksimum değer ile sınırlandı.",
                    "warning",
                )

            form_data.update(
                {
                    "metrekare": metrekare,
                    "maliyet": maliyet,
                    "guncel_deger": guncel_deger,
                    "taks": taks,
                    "kaks": kaks,
                }
            )

        except (ValueError, TypeError) as e:
            # Bu blok normalde validasyon sonrası çalışmamalı ama güvenlik için kalabilir
            print(f"Numeric conversion error after validation: {e}")
            flash("Sayısal değerlerde beklenmedik bir hata oluştu.", "danger")
            return redirect(url_for("analysis_form"))

        # Process SWOT data (validasyon başarılıysa)
        swot_data = {}
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            swot_data[key] = json.loads(form_data.get(key, "[]"))

        # Create new ArsaAnaliz object
        yeni_analiz = ArsaAnaliz(
            user_id=user_id,
            il=form_data.get("il"),
            ilce=form_data.get("ilce"),
            mahalle=form_data.get("mahalle"),
            ada=form_data.get("ada"),
            parsel=form_data.get("parsel"),
            koordinatlar=form_data.get("koordinatlar"),
            pafta=form_data.get("pafta"),
            metrekare=Decimal(str(metrekare)),
            imar_durumu=form_data.get("imar_durumu"),
            taks=Decimal(str(taks)),
            kaks=Decimal(str(kaks)),
            fiyat=Decimal(str(maliyet)),  # 'fiyat' yerine 'maliyet' kullanılıyor
            bolge_fiyat=Decimal(
                str(guncel_deger)
            ),  # 'bolge_fiyat' yerine 'guncel_deger'
            altyapi=json.dumps(altyapi_list),
            swot_analizi=json.dumps(swot_data),
            notlar=form_data.get("notlar"),  # Notlar alanını ekle
        )

        # Veritabanına kaydet ve istatistikleri güncelle...
        db.session.add(yeni_analiz)
        # db.session.commit() # Commit işlemi diğer güncellemelerle birlikte sonda yapılacak

        # Bölge istatistiklerini güncelle
        bolge = BolgeDagilimi.query.filter_by(
            user_id=user_id, il=form_data.get("il")
        ).first()

        fiyat_decimal = Decimal(str(maliyet))

        if bolge:
            bolge.analiz_sayisi += 1
            bolge.toplam_deger += fiyat_decimal
        else:
            yeni_bolge = BolgeDagilimi(
                user_id=user_id,
                il=form_data.get("il"),
                analiz_sayisi=1,
                toplam_deger=fiyat_decimal,
            )
            db.session.add(yeni_bolge)

        # Dashboard istatistiklerini güncelle
        stats = DashboardStats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = DashboardStats(user_id=user_id)
            db.session.add(stats)

        stats.toplam_arsa_sayisi += 1
        # Ortalama fiyatı güvenli hesapla
        if stats.toplam_arsa_sayisi > 0:
            stats.ortalama_fiyat = (
                (stats.ortalama_fiyat * (stats.toplam_arsa_sayisi - 1)) + maliyet
            ) / stats.toplam_arsa_sayisi
        else:
            stats.ortalama_fiyat = maliyet  # İlk analiz ise doğrudan maliyeti ata
        stats.en_yuksek_fiyat = max(stats.en_yuksek_fiyat or 0, maliyet)
        stats.en_dusuk_fiyat = min(stats.en_dusuk_fiyat or float("inf"), maliyet)
        stats.toplam_deger += fiyat_decimal

        db.session.commit()

        flash("Arsa analizi başarıyla kaydedildi.", "success")
        return redirect(url_for("analizler"))

    except Exception as e:
        db.session.rollback()
        print(f"Submit analysis error: {str(e)}")
        import traceback

        traceback.print_exc()
        print("Hata durumunda form verileri:")
        # Hata durumunda form verilerini yazdırma
        form_data_error = request.form.to_dict(
            flat=False
        )  # Checkbox/multiselect için flat=False
        for key, value in form_data_error.items():
            print(f"  {key}: {value}")
        flash(
            f"Arsa analizi kaydedilirken beklenmedik bir hata oluştu: {str(e)}",
            "danger",
        )
        return redirect(url_for("analysis_form"))


# Diger route fonksiyonları


# Veritabanı tablolarını oluştur
def init_db():
    with app.app_context():
        try:
            # Önce tüm tabloları sil
            # db.drop_all()
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


if __name__ == "__main__":
    try:
        # Veritabanını başlat
        init_db()
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"Uygulama başlatma hatası: {str(e)}")
        app.logger.error(f"Uygulama başlatma hatası: {str(e)}", exc_info=True)
        # Uygulama başlatılamadı, gerekli önlemleri al
        # Örneğin, veritabanı bağlantısını kontrol et veya hata mesajını logla
        # Uygulama başlatılamadı, gerekli önlemleri al
