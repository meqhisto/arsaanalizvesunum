# -*- coding: utf-8 -*-
"""İlan, ilan–gayrimenkul bağı, ilan emsalleri ve gayrimenkul sahipliği modelleri."""
from datetime import datetime

from . import db


class GayrimenkulSahibi(db.Model):
    __tablename__ = 'gayrimenkul_sahipleri'
    id = db.Column(db.Integer, primary_key=True)
    gayrimenkul_id = db.Column(db.Integer, db.ForeignKey('arsa_analizleri.id', ondelete='CASCADE'),
                               nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    hisse = db.Column(db.String(20))
    irtibat = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('gayrimenkul_id', 'contact_id', name='uq_gayrimenkul_sahibi'),)

    gayrimenkul = db.relationship('ArsaAnaliz', back_populates='sahiplikler')
    contact = db.relationship('Contact', backref=db.backref('sahiplikler', lazy=True, passive_deletes=True))


class Ilan(db.Model):
    __tablename__ = 'ilanlar'
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(20), unique=True, nullable=False)
    baslik = db.Column(db.String(200))
    aciklama = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sorumlu_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id', ondelete='SET NULL'), nullable=True)
    teklif_tipi = db.Column(db.String(20), nullable=False, default='satilik')
    durum = db.Column(db.String(20), nullable=False, default='hazirlaniyor')
    # Satılık
    fiyat = db.Column(db.Numeric(15, 2))
    # Kiralık
    kira = db.Column(db.Numeric(12, 2))
    depozito = db.Column(db.Numeric(12, 2))
    # Kat karşılığı
    sahip_payi_yuzde = db.Column(db.Numeric(5, 2))
    ek_nakit = db.Column(db.Numeric(15, 2))
    teslim_suresi_ay = db.Column(db.Integer)
    teminat_turu = db.Column(db.String(40))
    teminat_tutari = db.Column(db.Numeric(15, 2))
    tevhid_durumu = db.Column(db.String(20))
    insaat_alani_elle = db.Column(db.Numeric(12, 2))
    daire_tercihi_notu = db.Column(db.Text)
    # Emsal yoksa elle girilen bölge değerleri
    bolge_m2_fiyat_elle = db.Column(db.Numeric(15, 2))
    bolge_pay_yuzde_elle = db.Column(db.Numeric(5, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    baglar = db.relationship('IlanGayrimenkul', back_populates='ilan', order_by='IlanGayrimenkul.sira',
                             cascade='all, delete-orphan', passive_deletes=True)
    emsaller = db.relationship('IlanEmsal', back_populates='ilan', order_by='IlanEmsal.id',
                               cascade='all, delete-orphan', passive_deletes=True)
    user = db.relationship('User', foreign_keys=[user_id],
                           backref=db.backref('olusturdugu_ilanlar', lazy='dynamic'))
    sorumlu = db.relationship('User', foreign_keys=[sorumlu_user_id],
                              backref=db.backref('sorumlu_ilanlar', lazy='dynamic'))
    office = db.relationship('Office', backref=db.backref('ilanlar', lazy='dynamic'))

    @property
    def gayrimenkuller(self):
        return [b.gayrimenkul for b in self.baglar]

    @property
    def ana_gayrimenkul(self):
        for b in self.baglar:
            if b.ana_kayit:
                return b.gayrimenkul
        return self.baglar[0].gayrimenkul if self.baglar else None

    def __repr__(self):
        return f'<Ilan {self.kod}>'


class IlanGayrimenkul(db.Model):
    __tablename__ = 'ilan_gayrimenkulleri'
    ilan_id = db.Column(db.Integer, db.ForeignKey('ilanlar.id', ondelete='CASCADE'), primary_key=True)
    gayrimenkul_id = db.Column(db.Integer, db.ForeignKey('arsa_analizleri.id', ondelete='CASCADE'),
                               primary_key=True, index=True)
    ana_kayit = db.Column(db.Boolean, default=False, nullable=False)
    parsel_fiyati = db.Column(db.Numeric(15, 2))
    sira = db.Column(db.Integer, default=1, nullable=False)

    ilan = db.relationship('Ilan', back_populates='baglar')
    gayrimenkul = db.relationship('ArsaAnaliz', back_populates='ilan_baglari')


class IlanEmsal(db.Model):
    __tablename__ = 'ilan_emsalleri'
    id = db.Column(db.Integer, primary_key=True)
    ilan_id = db.Column(db.Integer, db.ForeignKey('ilanlar.id', ondelete='CASCADE'), nullable=False, index=True)
    konum = db.Column(db.String(200))
    m2 = db.Column(db.Numeric(10, 2))
    fiyat = db.Column(db.Numeric(15, 2))
    pay_yuzde = db.Column(db.Numeric(5, 2))
    link = db.Column(db.String(500))
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ilan = db.relationship('Ilan', back_populates='emsaller')
