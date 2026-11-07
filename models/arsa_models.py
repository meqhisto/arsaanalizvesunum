# models/arsa_models.py
from datetime import datetime
from decimal import Decimal # Numeric için
from sqlalchemy import Index # Index için
from . import db
from .user_models import User # User ilişkisi için
from .office_models import Office # Office modelini import et


# Portfolio ve portfolio_arsalar tablosunu import edelim ki ilişki kurabilelim
from .user_models import Portfolio, portfolio_arsalar

class ArsaAnaliz(db.Model):
    __tablename__ = "arsa_analizleri"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey("offices.id"), nullable=True) # Hangi ofise ait (bireysel ise NULL)
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
    deger_artis_orani = db.Column(db.Numeric(5, 2))  # Yıllık beklenen değer artışı (%)
    # Gayrimenkul türü ve tür bazlı alanlar (spec §3.1); mevcut tabloya ilan_kurulum ekler
    tur = db.Column(db.String(20), default='arsa', server_default='arsa')
    alt_tur = db.Column(db.String(30))
    baslik = db.Column(db.String(200))
    brut_m2 = db.Column(db.Numeric(10, 2))
    net_m2 = db.Column(db.Numeric(10, 2))
    oda_sayisi = db.Column(db.String(10))
    banyo_sayisi = db.Column(db.Integer)
    bulundugu_kat = db.Column(db.String(10))
    toplam_kat = db.Column(db.Integer)
    bina_yasi = db.Column(db.Integer)
    isinma = db.Column(db.String(30))
    esyali = db.Column(db.Boolean)
    site_icinde = db.Column(db.Boolean)
    balkon = db.Column(db.Boolean)
    aidat = db.Column(db.Numeric(10, 2))
    tapu_durumu = db.Column(db.String(30))
    krediye_uygun = db.Column(db.Boolean)
    takasli = db.Column(db.Boolean)
    kimden = db.Column(db.String(20))
    ozellikler = db.Column(db.JSON(none_as_null=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_user_il", "user_id", "il"),
        Index("ix_created_at", "created_at"),
    )

    sahiplikler = db.relationship("GayrimenkulSahibi", back_populates="gayrimenkul",
                                  cascade="all, delete-orphan", passive_deletes=True)
    ilan_baglari = db.relationship("IlanGayrimenkul", back_populates="gayrimenkul",
                                   cascade="all, delete-orphan", passive_deletes=True)

    @property
    def baslik_metni(self):
        """Başlık; boşsa tür/alt tür etiketi ve konumdan üretilir."""
        if self.baslik:
            return self.baslik
        from modules.gayrimenkul_sabitleri import ALT_TURLER, TURLER, etiket
        tur = self.tur or 'arsa'
        tur_etiketi = etiket(ALT_TURLER.get(tur, []), self.alt_tur) if self.alt_tur else etiket(TURLER, tur)
        metin = f"{tur_etiketi} · {self.mahalle}, {self.ilce}"
        if tur in ('arsa', 'tarla') and (self.ada or self.parsel):
            metin += f" · Ada {self.ada or '-'} / Parsel {self.parsel or '-'}"
        return metin

    @property
    def ozet(self):
        """Liste kartı için kısa özet: konutta '3+1 · 120 m² · 4. kat', arsada '800 m² · Konut imarlı · KAKS 1,5'."""
        from modules.ilan_hesap import sayi_metni
        parcalar = []
        if (self.tur or 'arsa') in ('arsa', 'tarla'):
            if self.metrekare is not None:
                parcalar.append(f"{sayi_metni(self.metrekare)} m²")
            imar = (self.imar_durumu or '').strip()
            if imar:
                sade = imar == 'İmarsız' or imar.endswith('imarlı') or imar.endswith('İmarlı')
                parcalar.append(imar if sade else f"{imar} imarlı")
            if self.kaks is not None:
                parcalar.append(f"KAKS {sayi_metni(self.kaks)}")
        else:
            if self.oda_sayisi:
                parcalar.append(self.oda_sayisi)
            m2 = self.brut_m2 if self.brut_m2 is not None else self.metrekare
            if m2 is not None:
                parcalar.append(f"{sayi_metni(m2)} m²")
            kat = (self.bulundugu_kat or '').strip()
            if kat:
                parcalar.append(f"{kat}. kat" if kat.lstrip('-').isdigit() else kat)
            elif self.toplam_kat:
                parcalar.append(f"{self.toplam_kat} katlı")
        return ' · '.join(parcalar)

    @property
    def aktif_ilan(self):
        from modules.gayrimenkul_sabitleri import AKTIF_DURUMLAR
        for bag in self.ilan_baglari:
            if bag.ilan is not None and bag.ilan.durum in AKTIF_DURUMLAR:
                return bag.ilan
        return None

    user = db.relationship("User", backref=db.backref("analizler_olusturdugu", lazy="dynamic")) # backref adı değişti
    office = db.relationship("Office", backref=db.backref("analizler_ofisin", lazy="dynamic")) # Yeni ilişki    # Portfolio ile çoktan çoğa ilişki (portfolio_arsalar üzerinden)
    # Bu ilişki zaten Portfolio modelinde tanımlanmış olabilir,
    # Eğer öyleyse burada tekrar tanımlamaya gerek yok.
    # Eğer Portfolio modelinde `analizler = db.relationship("ArsaAnaliz", secondary=portfolio_arsalar, ...)`
    # şeklinde tanımlandıysa, burada `portfolios = db.relationship("Portfolio", secondary=portfolio_arsalar, back_populates="analizler")`
    # şeklinde tanımlanabilir. user_models.py'de `Portfolio` modeline ekleyelim:
    # `analizler = db.relationship("ArsaAnaliz", secondary=portfolio_arsalar, lazy="dynamic", backref=db.backref("portfolios_containing", lazy=True))`

class BolgeDagilimi(db.Model):
    __tablename__ = "bolge_dagilimi"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    il = db.Column(db.String(50), nullable=True)
    analiz_sayisi = db.Column(db.Integer, default=0)
    toplam_deger = db.Column(db.Numeric(15, 2), default=Decimal("0.00")) # Decimal ile başlat
    son_guncelleme = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("bolge_dagilimlari", lazy="dynamic"))

class YatirimPerformansi(db.Model):
    __tablename__ = "yatirim_performansi"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ay = db.Column(db.String(20), nullable=False)
    yil = db.Column(db.Integer, nullable=False)
    toplam_deger = db.Column(db.Numeric(15, 2), default=Decimal("0.00"))
    analiz_sayisi = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("yatirim_performanslari", lazy="dynamic"))

class DashboardStats(db.Model):
    __tablename__ = "dashboard_stats"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    toplam_arsa_sayisi = db.Column(db.Integer, default=0)
    ortalama_fiyat = db.Column(db.Float, default=0.0)
    en_yuksek_fiyat = db.Column(db.Float, default=0.0)
    en_dusuk_fiyat = db.Column(db.Float, default=0.0) # Veya float('inf') ile başlat
    toplam_deger = db.Column(db.Numeric(15, 2), default=Decimal("0.00"))
    ortalama_roi = db.Column(db.Numeric(5,2), default=Decimal("0.00")) # Eğer kullanılıyorsa
    son_guncelleme = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("dashboard_stats_entries", lazy="dynamic", cascade="all, delete-orphan")) # backref adı ve cascade

    def __repr__(self):
        return f"<DashboardStats(toplam_arsa_sayisi={self.toplam_arsa_sayisi}, ortalama_fiyat={self.ortalama_fiyat})>"

class AnalizMedya(db.Model):
    __tablename__ = "analiz_medya"
    id = db.Column(db.Integer, primary_key=True)
    analiz_id = db.Column(db.Integer, db.ForeignKey("arsa_analizleri.id", ondelete="CASCADE"), nullable=False) # ondelete eklendi
    filename = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    analiz = db.relationship("ArsaAnaliz", backref=db.backref("medyalar", lazy="dynamic", cascade="all, delete-orphan")) # cascade eklendi
    
    # models/user_models.py
# ... (User sınıfından sonra)
# ArsaAnaliz modelini import et
from .arsa_models import ArsaAnaliz

