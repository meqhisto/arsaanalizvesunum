# -*- coding: utf-8 -*-
"""Gayrimenkul/ilan yapısı için açılışta çalışan, tekrar çalıştırılabilir kurulum ve geçiş (spec §7).

1. arsa_analizleri'ne yeni sütunlar ve crm_deals.ilan_id `IF NOT EXISTS` ile eklenir
   (yeni tablolar `db.create_all()` ile kurulur).
2. tur boş kayıtlar 'arsa' yapılır.
3. altyapi, ozellikler.altyapi'ya kopyalanır (altyapi sütunu silinmez).
4. Hiç ilanı olmayan her gayrimenkul için tek gayrimenkullü satılık/pazarlamada ilan açılır.
5. portfolio_arsalar bağları portfolio_ilanlar'a kopyalanır.

Hepsi tek veritabanı işleminde (oturum bağlantısı) çalışır: ya tamamı uygulanır ya hiçbiri.
"""
import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Text, cast, or_, text

from models import db
from models.arsa_models import ArsaAnaliz
from models.ilan_models import Ilan, IlanGayrimenkul
from modules.rapor.model import parse_altyapi

log = logging.getLogger(__name__)

ARSA_SUTUNLARI = [
    ('tur', "VARCHAR(20) DEFAULT 'arsa'"),
    ('alt_tur', 'VARCHAR(30)'),
    ('baslik', 'VARCHAR(200)'),
    ('brut_m2', 'NUMERIC(10,2)'),
    ('net_m2', 'NUMERIC(10,2)'),
    ('oda_sayisi', 'VARCHAR(10)'),
    ('banyo_sayisi', 'INTEGER'),
    ('bulundugu_kat', 'VARCHAR(10)'),
    ('toplam_kat', 'INTEGER'),
    ('bina_yasi', 'INTEGER'),
    ('isinma', 'VARCHAR(30)'),
    ('esyali', 'BOOLEAN'),
    ('site_icinde', 'BOOLEAN'),
    ('balkon', 'BOOLEAN'),
    ('aidat', 'NUMERIC(10,2)'),
    ('tapu_durumu', 'VARCHAR(30)'),
    ('krediye_uygun', 'BOOLEAN'),
    ('takasli', 'BOOLEAN'),
    ('kimden', 'VARCHAR(20)'),
    ('ozellikler', 'JSON'),
]


def _sutunlari_ekle():
    if db.engine.dialect.name != 'postgresql':
        log.warning("İlan kurulumu: yeni sütunlar sadece PostgreSQL'de otomatik eklenir; "
                    "diğer veritabanlarında arsa_analizleri ve crm_deals.ilan_id sütunlarını elle ekleyin.")
        return
    for ad, tip in ARSA_SUTUNLARI:
        db.session.execute(text(f"ALTER TABLE arsa_analizleri ADD COLUMN IF NOT EXISTS {ad} {tip}"))
    db.session.execute(text("ALTER TABLE crm_deals ADD COLUMN IF NOT EXISTS ilan_id INTEGER "
                            "REFERENCES ilanlar(id) ON DELETE SET NULL"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_deals_ilan_id ON crm_deals (ilan_id)"))


def _yeni_kod(yil):
    """ILN-YYYY-NNNN: o yılın en büyük sıra numarası + 1. (Task 3'te ilan_servis'e taşınacak.)"""
    onek = f"ILN-{yil}-"
    en_buyuk = 0
    for (kod,) in db.session.query(Ilan.kod).filter(Ilan.kod.like(f"{onek}%")):
        try:
            en_buyuk = max(en_buyuk, int(kod[len(onek):]))
        except ValueError:
            continue
    return f"{onek}{en_buyuk + 1:04d}"


def donustur(a):
    """Eski bolge_fiyat'ı m² fiyatına çevirir: m² fiyatının 10 katından büyükse toplam bedel sayılır."""
    if not a.bolge_fiyat:
        return None
    bolge = Decimal(a.bolge_fiyat)
    m2 = Decimal(a.metrekare or 0)
    if m2 <= 0:
        return bolge
    m2_fiyat = Decimal(a.fiyat or 0) / m2
    if bolge > 10 * m2_fiyat:
        return (bolge / m2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return bolge


def _ozellikleri_doldur():
    eksikler = ArsaAnaliz.query.filter(or_(ArsaAnaliz.ozellikler.is_(None),
                                           cast(ArsaAnaliz.ozellikler, Text) == 'null'))
    for a in eksikler:
        a.ozellikler = {'altyapi': parse_altyapi(a.altyapi)}


def _ilanlari_olustur():
    yil = datetime.utcnow().year
    ilansizlar = ArsaAnaliz.query.filter(~ArsaAnaliz.ilan_baglari.any()).order_by(ArsaAnaliz.id).all()
    for a in ilansizlar:
        ilan = Ilan(kod=_yeni_kod(yil), baslik=a.baslik_metni, teklif_tipi='satilik', durum='pazarlamada',
                    fiyat=a.fiyat, bolge_m2_fiyat_elle=donustur(a), office_id=a.office_id,
                    user_id=a.user_id, sorumlu_user_id=a.user_id)
        ilan.baglar.append(IlanGayrimenkul(gayrimenkul=a, ana_kayit=True, sira=1))
        db.session.add(ilan)
        db.session.flush()  # sonraki _yeni_kod bu kodu görsün
    if ilansizlar:
        log.info("İlan kurulumu: %d gayrimenkul için ilan oluşturuldu.", len(ilansizlar))


def _portfoyleri_kopyala():
    db.session.execute(text("""
        INSERT INTO portfolio_ilanlar (portfolio_id, ilan_id, added_at)
        SELECT pa.portfolio_id, ilk.ilan_id, COALESCE(pa.added_at, CURRENT_TIMESTAMP)
        FROM portfolio_arsalar pa
        JOIN (SELECT gayrimenkul_id, MIN(ilan_id) AS ilan_id
              FROM ilan_gayrimenkulleri GROUP BY gayrimenkul_id) ilk ON ilk.gayrimenkul_id = pa.arsa_id
        ON CONFLICT DO NOTHING
    """))


def kur():
    try:
        _sutunlari_ekle()
        db.session.execute(text("UPDATE arsa_analizleri SET tur = 'arsa' WHERE tur IS NULL"))
        _ozellikleri_doldur()
        _ilanlari_olustur()
        _portfoyleri_kopyala()
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("İlan kurulumu sırasında hata")
        raise
