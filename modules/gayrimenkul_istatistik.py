# -*- coding: utf-8 -*-
"""Panel (DashboardStats) ve bölge (BolgeDagilimi) istatistiklerinin artımlı güncellenmesi.

Gayrimenkul formu (blueprints/analysis_bp.py) ve ilan servisi (modules/ilan_servis.py) ortak kullanır.
Fonksiyonlar commit etmez.
"""
from datetime import datetime
from decimal import Decimal

from models import db
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats


def istatistiklere_ekle(gayrimenkul):
    """Panel ve bölge istatistiklerine yeni kaydı ekler (commit etmez)."""
    user_id = gayrimenkul.user_id
    fiyat = Decimal(str(gayrimenkul.fiyat or 0))
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = DashboardStats()
        stats.user_id = user_id
        db.session.add(stats)
    stats.toplam_arsa_sayisi = (stats.toplam_arsa_sayisi or 0) + 1
    stats.toplam_deger = (stats.toplam_deger or Decimal(0)) + fiyat
    fiyat_f = float(fiyat)
    if stats.toplam_arsa_sayisi == 1:
        stats.ortalama_fiyat = stats.en_yuksek_fiyat = stats.en_dusuk_fiyat = fiyat_f
    else:
        stats.ortalama_fiyat = (((stats.ortalama_fiyat or 0.0) * (stats.toplam_arsa_sayisi - 1)) + fiyat_f) \
            / stats.toplam_arsa_sayisi
        stats.en_yuksek_fiyat = max((stats.en_yuksek_fiyat or 0.0), fiyat_f)
        stats.en_dusuk_fiyat = min(stats.en_dusuk_fiyat if stats.en_dusuk_fiyat is not None else fiyat_f, fiyat_f)
    stats.son_guncelleme = datetime.utcnow()

    bolge = BolgeDagilimi.query.filter_by(user_id=user_id, il=gayrimenkul.il).first()
    if not bolge:
        bolge = BolgeDagilimi()
        bolge.user_id = user_id
        bolge.il = gayrimenkul.il
        bolge.analiz_sayisi = 0
        bolge.toplam_deger = Decimal('0.00')
        db.session.add(bolge)
    bolge.analiz_sayisi = (bolge.analiz_sayisi or 0) + 1
    bolge.toplam_deger = (bolge.toplam_deger or Decimal(0)) + fiyat
    bolge.son_guncelleme = datetime.utcnow()


def istatistik_fiyat_degisti(gayrimenkul, eski_fiyat):
    """Kayıtlı gayrimenkulün fiyatı değişince panel/bölge istatistiklerini düzeltir (commit etmez)."""
    fark = Decimal(str(gayrimenkul.fiyat or 0)) - Decimal(str(eski_fiyat or 0))
    if not fark:
        return
    user_id = gayrimenkul.user_id
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if stats:
        db.session.flush()
        sayi, en_yuksek, en_dusuk = (db.session.query(db.func.count(ArsaAnaliz.id), db.func.max(ArsaAnaliz.fiyat),
                                                       db.func.min(ArsaAnaliz.fiyat))
                                     .filter(ArsaAnaliz.user_id == user_id).one())
        stats.toplam_deger = (stats.toplam_deger or Decimal(0)) + fark
        if sayi:
            stats.ortalama_fiyat = float(stats.toplam_deger) / sayi
            stats.en_yuksek_fiyat = float(en_yuksek or 0)
            stats.en_dusuk_fiyat = float(en_dusuk or 0)
        stats.son_guncelleme = datetime.utcnow()
    bolge = BolgeDagilimi.query.filter_by(user_id=user_id, il=gayrimenkul.il).first()
    if bolge:
        bolge.toplam_deger = (bolge.toplam_deger or Decimal(0)) + fark
        bolge.son_guncelleme = datetime.utcnow()
