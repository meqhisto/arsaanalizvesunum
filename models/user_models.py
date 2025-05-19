# models/user_models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
import secrets # forgot password için
from . import db # Aynı paketteki __init__.py'den db'yi al
from .office_models import Office
from flask_login import UserMixin




class User(UserMixin, db.Model):
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
    role = db.Column(db.String(32), default='')  # veya sana uygun default bir değer
    profil_foto = db.Column(db.String(200))  # Path to profile photo
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)
    son_giris = db.Column(db.DateTime)
    failed_attempts = db.Column(db.Integer, default=0)
    reset_token = db.Column(db.String(255))
    reset_token_expires = db.Column(db.DateTime)
    timezone = db.Column(
        db.String(50), default="Europe/Istanbul"
    )  # Kullanıcının zaman dilimi
    role = db.Column(db.String(20), default='danisman', nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True)
    
    # Tek bir manager ilişkisi tanımlayalım
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Manager ilişkisini açıkça tanımlayalım
    manager = db.relationship(
        'User',
        remote_side=[id],
        foreign_keys=[manager_id],
        backref=db.backref(
            'subordinates',
            lazy='dynamic',
            cascade='all, delete-orphan'
        )
    )
    
    # reports_to_user_id'yi kaldır çünkü artık manager_id kullanıyoruz
    # reports_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Office ilişkisi
    office = db.relationship('Office', backref=db.backref('members', lazy='dynamic'))

    def set_password(self, password):
        try:
            # print(f"Setting password for user {self.email}")  # Debug log
            self.password_hash = generate_password_hash(password, method="sha256")
            # print("Password hash generated successfully")  # Debug log
        except Exception as e:
            # print(f"Error setting password: {str(e)}")  # Debug log
            raise

    def check_password(self, password):
        try:
            # print(f"Checking password for user {self.email}")  # Debug log
            # print(f"Stored hash: {self.password_hash}")  # Debug log
            result = check_password_hash(self.password_hash, password)
            # print(f"Password check result: {result}")  # Debug log
            return result
        except Exception as e:
            # print(f"Error checking password: {str(e)}")  # Debug log
            # import traceback
            # print("Full traceback:")  # Debug log
            # print(traceback.format_exc())  # Debug log
            return False

    def localize_datetime(self, utc_dt, format="%d.%m.%Y %H:%M"):
        """Verilen UTC datetime nesnesini kullanıcının zaman dilimine çevirir ve formatlar."""
        if not utc_dt:
            return ""
        try:
            user_tz_str = (
                self.timezone if self.timezone in pytz.all_timezones else "UTC"
            )
            user_tz = pytz.timezone(user_tz_str)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc

        if utc_dt.tzinfo is None: # Eğer naive ise localize et
            aware_utc_dt = pytz.utc.localize(utc_dt)
        else: # Zaten aware ise direkt kullan
            aware_utc_dt = utc_dt.astimezone(pytz.utc)

        local_dt = aware_utc_dt.astimezone(user_tz)
        return local_dt.strftime(format)

    @property
    def is_active(self):
        return self.is_active_flag

# class Portfolio(db.Model):
#     __tablename__ = "portfolios"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     title = db.Column(db.String(200), nullable=False)
#     description = db.Column(db.Text)
#     visibility = db.Column(db.String(20), default="public")
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(
#         db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
#     )

#     user = db.relationship("User", backref=db.backref("portfolios_owned", lazy=True)) # backref adı değişti
#     # ArsaAnaliz ile ilişki için 'arsa_models.py' dosyasına bakılacak
#     # analizler ilişkisi 'portfolio_arsalar' üzerinden 'ArsaAnaliz'e bağlanacak
#     # Bu ilişki ArsaAnaliz modelinde veya burada tanımlanabilir. Şimdilik burada bırakalım.
#     # Ancak ArsaAnaliz modelinin import edilmesi gerekecek.
#     # from .arsa_models import ArsaAnaliz # Bu circular import yaratabilir, dikkat!
#     # En iyisi bu ilişkiyi ArsaAnaliz modelinden sonra portfolio_arsalar tablosunu tanımlarken
#     # ve Portfolio.analizler ilişkisini orada yapmak veya ArsaAnaliz'in olduğu dosyada yapmak.
#     # Şimdilik ArsaAnaliz'e olan doğrudan ilişkiyi yoruma alalım, portfolio_arsalar tablosu yeterli.

portfolio_arsalar = db.Table( # Bu tablo tanımı burada veya arsa_models.py'de olabilir
    "portfolio_arsalar",     # Önemli olan bir yerde tanımlı olması
    db.Column("portfolio_id", db.Integer, db.ForeignKey("portfolios.id"), primary_key=True),
    db.Column("arsa_id", db.Integer, db.ForeignKey("arsa_analizleri.id"), primary_key=True),
    db.Column("added_at", db.DateTime, default=datetime.utcnow)
)

class Portfolio(db.Model):
    __tablename__ = "portfolios"
    # ----- BU SATIR ÇOK ÖNEMLİ -----
    id = db.Column(db.Integer, primary_key=True) # BİRİNCİL ANAHTAR
    # ---------------------------------
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    visibility = db.Column(db.String(20), default="public")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("portfolios_owned", lazy=True))
    analizler = db.relationship(
        "ArsaAnaliz", # String olarak model adı
        secondary=portfolio_arsalar, # İlişki tablosu
        lazy="dynamic",
        # backref Portfolio'ya ArsaAnaliz'den nasıl erişileceğini tanımlar
        backref=db.backref("portfolios_containing", lazy=True)
    )