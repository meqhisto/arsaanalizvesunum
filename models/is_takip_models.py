# -*- coding: utf-8 -*-
"""İş takip modülü modelleri.

Bir İş (Is) ofisin yürüttüğü bir süreçtir (arsa satışı, imar başvurusu vb.).
İşin adımları mevcut CRM görevleridir (crm_tasks.is_id ile bağlanır), böylece
görev atama / hatırlatma / performans ekranları iş adımları için de çalışır.
"""
from datetime import datetime, date

from models import db

IS_DURUMLARI = ['Açık', 'Devam ediyor', 'Beklemede', 'Tamamlandı', 'İptal']
IS_ACIK_DURUMLAR = ['Açık', 'Devam ediyor', 'Beklemede']
IS_ONCELIKLERI = ['Düşük', 'Normal', 'Yüksek', 'Acil']
IS_TURLERI = ['Arsa satışı', 'Arsa alımı', 'İmar / Ruhsat', 'Kat karşılığı', 'Diğer']
BELGE_TURLERI = ['Tapu', 'İmar durumu', 'Ruhsat', 'Sözleşme', 'Vekaletname', 'Fatura / Makbuz',
                 'Proje', 'Fotoğraf', 'Diğer']
MASRAF_KALEMLERI = ['Tapu harcı', 'Döner sermaye', 'Belediye harcı', 'Komisyon', 'Ekspertiz', 'Noter',
                    'Proje / Mühendislik', 'Diğer']
ODEME_DURUMLARI = ['Ödendi', 'Bekliyor']

# Görev tablosundaki "tamamlandı" durumu (CRM ile aynı değer)
GOREV_TAMAMLANDI = 'Tamamlandı'
GOREV_IPTAL = 'İptal Edildi'


class IsSablonu(db.Model):
    __tablename__ = 'is_sablonlari'
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(120), nullable=False)
    is_turu = db.Column(db.String(50), nullable=False, default='Diğer')
    aciklama = db.Column(db.Text)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True)  # NULL = herkese açık
    aktif = db.Column(db.Boolean, default=True, nullable=False)
    olusturan_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    adimlar = db.relationship('IsSablonAdimi', backref='sablon', order_by='IsSablonAdimi.sira',
                              cascade='all, delete-orphan', lazy='select')


class IsSablonAdimi(db.Model):
    __tablename__ = 'is_sablon_adimlari'
    id = db.Column(db.Integer, primary_key=True)
    sablon_id = db.Column(db.Integer, db.ForeignKey('is_sablonlari.id', ondelete='CASCADE'), nullable=False)
    sira = db.Column(db.Integer, nullable=False, default=1)
    baslik = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    varsayilan_sure_gun = db.Column(db.Integer, default=0, nullable=False)  # önceki adımdan kaç gün sonra
    sorumlu_rol = db.Column(db.String(20))  # broker / danisman (öneri)
    gerekli_belge_turu = db.Column(db.String(50))


class Is(db.Model):
    __tablename__ = 'isler'
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(20), unique=True, nullable=False, index=True)
    baslik = db.Column(db.String(200), nullable=False)
    is_turu = db.Column(db.String(50), nullable=False, default='Diğer')
    durum = db.Column(db.String(30), nullable=False, default='Açık', index=True)
    oncelik = db.Column(db.String(20), nullable=False, default='Normal')
    aciklama = db.Column(db.Text)

    sorumlu_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    olusturan_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=True, index=True)

    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id', ondelete='SET NULL'), nullable=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('crm_deals.id', ondelete='SET NULL'), nullable=True)
    analiz_id = db.Column(db.Integer, db.ForeignKey('arsa_analizleri.id', ondelete='SET NULL'), nullable=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id', ondelete='SET NULL'), nullable=True)
    sablon_id = db.Column(db.Integer, db.ForeignKey('is_sablonlari.id', ondelete='SET NULL'), nullable=True)

    baslangic_tarihi = db.Column(db.Date, default=date.today)
    hedef_bitis_tarihi = db.Column(db.Date)
    tamamlanma_tarihi = db.Column(db.DateTime)
    butce = db.Column(db.Numeric(15, 2))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sorumlu = db.relationship('User', foreign_keys=[sorumlu_user_id])
    olusturan = db.relationship('User', foreign_keys=[olusturan_user_id])
    office = db.relationship('Office')
    contact = db.relationship('Contact', backref=db.backref('isler', lazy='dynamic'))
    deal = db.relationship('Deal', backref=db.backref('isler', lazy='dynamic'))
    analiz = db.relationship('ArsaAnaliz', backref=db.backref('isler', lazy='dynamic'))
    portfolio = db.relationship('Portfolio', backref=db.backref('isler', lazy='dynamic'))
    sablon = db.relationship('IsSablonu')

    adimlar = db.relationship('Task', backref='is_kaydi', lazy='dynamic',
                              order_by='Task.sira', foreign_keys='Task.is_id')
    belgeler = db.relationship('IsBelgesi', backref='is_kaydi', lazy='dynamic',
                               cascade='all, delete-orphan', order_by='IsBelgesi.created_at.desc()')
    masraflar = db.relationship('IsMasrafi', backref='is_kaydi', lazy='dynamic',
                                cascade='all, delete-orphan', order_by='IsMasrafi.tarih.desc()')
    aktiviteler = db.relationship('IsAktivitesi', backref='is_kaydi', lazy='dynamic',
                                  cascade='all, delete-orphan', order_by='IsAktivitesi.created_at.desc()')

    # --- Hesaplanan bilgiler ---
    def adim_ozeti(self, tum_adimlar=None):
        """tum_adimlar verilirse (liste sayfasında toplu yüklenmiş) ayrıca sorgu atılmaz."""
        kaynak = self.adimlar if tum_adimlar is None else tum_adimlar
        adimlar = [a for a in kaynak if a.status != GOREV_IPTAL]
        tamam = sum(1 for a in adimlar if a.status == GOREV_TAMAMLANDI)
        toplam = len(adimlar)
        now = datetime.utcnow()
        acik = [a for a in adimlar if a.status != GOREV_TAMAMLANDI]
        geciken = [a for a in acik if a.due_date and a.due_date < now]
        siradaki = min((a for a in acik if a.due_date), key=lambda a: a.due_date, default=None)
        return {
            'toplam': toplam, 'tamam': tamam,
            'yuzde': int(round(100 * tamam / toplam)) if toplam else 0,
            'geciken': len(geciken), 'siradaki': siradaki,
        }

    def masraf_ozeti(self):
        kalemler = self.masraflar.all()
        toplam = sum(float(m.tutar or 0) for m in kalemler)
        return {
            'toplam': toplam,
            'odenen': sum(float(m.tutar or 0) for m in kalemler if m.odeme_durumu == 'Ödendi'),
            'bekleyen': sum(float(m.tutar or 0) for m in kalemler if m.odeme_durumu != 'Ödendi'),
            'musteriye': sum(float(m.tutar or 0) for m in kalemler if m.musteriye_yansit),
            'adet': len(kalemler),
        }

    @property
    def acik_mi(self):
        return self.durum in IS_ACIK_DURUMLAR

    @staticmethod
    def yeni_kod():
        yil = datetime.utcnow().year
        onek = f"IS-{yil}-"
        son = db.session.query(Is.kod).filter(Is.kod.like(f"{onek}%")).order_by(Is.kod.desc()).first()
        sira = int(son[0].rsplit('-', 1)[1]) + 1 if son else 1
        return f"{onek}{sira:04d}"


class IsBelgesi(db.Model):
    __tablename__ = 'is_belgeleri'
    id = db.Column(db.Integer, primary_key=True)
    is_id = db.Column(db.Integer, db.ForeignKey('isler.id', ondelete='CASCADE'), nullable=False, index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('crm_tasks.id', ondelete='SET NULL'), nullable=True)
    belge_turu = db.Column(db.String(50), nullable=False, default='Diğer')
    dosya_adi = db.Column(db.String(255), nullable=False)   # kullanıcının yüklediği özgün ad
    dosya_yolu = db.Column(db.String(500), nullable=False)  # uploads kökünden göreli, rastgele ad
    boyut = db.Column(db.Integer, default=0)
    mime_type = db.Column(db.String(100))
    aciklama = db.Column(db.String(500))
    yukleyen_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    yukleyen = db.relationship('User')
    adim = db.relationship('Task')


class IsMasrafi(db.Model):
    __tablename__ = 'is_masraflari'
    id = db.Column(db.Integer, primary_key=True)
    is_id = db.Column(db.Integer, db.ForeignKey('isler.id', ondelete='CASCADE'), nullable=False, index=True)
    kalem = db.Column(db.String(50), nullable=False, default='Diğer')
    tutar = db.Column(db.Numeric(15, 2), nullable=False)
    para_birimi = db.Column(db.String(10), nullable=False, default='TRY')
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    odeme_durumu = db.Column(db.String(20), nullable=False, default='Bekliyor')
    musteriye_yansit = db.Column(db.Boolean, nullable=False, default=False)
    belge_id = db.Column(db.Integer, db.ForeignKey('is_belgeleri.id', ondelete='SET NULL'), nullable=True)
    aciklama = db.Column(db.String(500))
    ekleyen_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ekleyen = db.relationship('User')
    belge = db.relationship('IsBelgesi')


class IsAktivitesi(db.Model):
    __tablename__ = 'is_aktiviteleri'
    id = db.Column(db.Integer, primary_key=True)
    is_id = db.Column(db.Integer, db.ForeignKey('isler.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    eylem = db.Column(db.String(40), nullable=False)
    detay = db.Column(db.Text)  # okunabilir açıklama
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')


class Bildirim(db.Model):
    __tablename__ = 'bildirimler'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    is_id = db.Column(db.Integer, db.ForeignKey('isler.id', ondelete='CASCADE'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('crm_tasks.id', ondelete='CASCADE'), nullable=True)
    tur = db.Column(db.String(20), nullable=False)  # yaklasan, geciken, atandi, tamamlandi
    mesaj = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(300))
    okundu = db.Column(db.Boolean, nullable=False, default=False, index=True)
    gun = db.Column(db.Date, nullable=False, default=date.today)  # aynı uyarıyı günde bir kez üretmek için
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'task_id', 'tur', 'gun', name='uq_bildirim_gunluk'),)
