# -*- coding: utf-8 -*-
"""Gayrimenkul/ilan yapısı için açılışta çalışan, tekrar çalıştırılabilir kurulum ve geçiş (spec §7).

1. arsa_analizleri'ne yeni sütunlar ve crm_deals.ilan_id `IF NOT EXISTS` ile eklenir
   (yeni tablolar `db.create_all()` ile kurulur). Her açılışta çalışır.

2-5. veri geçişi yalnız BİR KEZ çalışır: `kurulum_isaretleri`'nde 'ilan_gecisi_v1' satırı yoksa
   çalıştırılır ve satır aynı işlemde eklenir. (Sonradan ilansız gayrimenkul olabilir, portföyden
   ilan çıkarılabilir; geçiş bunları geri almamalı.)
2. tur boş kayıtlar 'arsa' yapılır.
3. altyapi, ozellikler.altyapi'ya kopyalanır (altyapi sütunu silinmez).
4. Hiç ilanı olmayan her gayrimenkul için tek gayrimenkullü satılık/pazarlamada ilan açılır.
5. portfolio_arsalar bağları portfolio_ilanlar'a kopyalanır.

6. (PostgreSQL, her açılışta) YENI_TABLOLAR'da RLS açılır; Supabase'in `anon` / `authenticated`
   rolleri varsa bu tablolardaki yetkileri kaldırılır. Zaten tamamsa hiçbir ALTER/REVOKE çalışmaz.

Hepsi tek veritabanı işleminde (oturum bağlantısı) çalışır: ya tamamı uygulanır ya hiçbiri.
"""
import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Text, cast, inspect, or_, text

from models import db
from models.arsa_models import ArsaAnaliz
from models.ilan_models import Ilan, IlanGayrimenkul, KurulumIsareti
from modules.ilan_servis import yeni_ilan_kodu
from modules.rapor.model import parse_altyapi

log = logging.getLogger(__name__)

GECIS_ISARETI = 'ilan_gecisi_v1'

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


# Bu dalda eklenen tablolar: Supabase PostgREST public şemayı dışa açtığı için RLS açık, anon/authenticated yetkisiz
YENI_TABLOLAR = ('kurulum_isaretleri', 'gayrimenkul_sahipleri', 'ilanlar', 'ilan_gayrimenkulleri',
                 'ilan_emsalleri', 'portfolio_ilanlar')
REST_ROLLERI = ('anon', 'authenticated')


def _rls_ac():
    """Yeni tablolarda RLS'yi açar, REST rollerinin yetkilerini kaldırır (yalnız gerekiyorsa)."""
    if db.engine.dialect.name != 'postgresql':
        return
    kapali = db.session.execute(text(
        "SELECT c.relname FROM pg_class c WHERE c.relkind = 'r' AND c.relnamespace = 'public'::regnamespace "
        "AND c.relname = ANY(:t) AND NOT c.relrowsecurity ORDER BY c.relname"),
        {'t': list(YENI_TABLOLAR)}).scalars().all()
    roller = db.session.execute(text("SELECT rolname FROM pg_roles WHERE rolname = ANY(:r) ORDER BY rolname"),
                                {'r': list(REST_ROLLERI)}).scalars().all()
    yetkili = []
    if roller:
        yetkili = db.session.execute(text(
            "SELECT DISTINCT table_name FROM information_schema.role_table_grants "
            "WHERE table_schema = 'public' AND table_name = ANY(:t) AND grantee = ANY(:r) ORDER BY table_name"),
            {'t': list(YENI_TABLOLAR), 'r': list(roller)}).scalars().all()
    if not kapali and not yetkili:
        return
    db.session.execute(text("SET LOCAL lock_timeout = '10s'"))
    for t in kapali:
        db.session.execute(text(f'ALTER TABLE public."{t}" ENABLE ROW LEVEL SECURITY'))
    rol_listesi = ', '.join(f'"{r}"' for r in roller)
    for t in yetkili:
        db.session.execute(text(f'REVOKE ALL ON TABLE public."{t}" FROM {rol_listesi}'))
    log.info("İlan kurulumu: RLS açıldı %s, yetki kaldırıldı %s", list(kapali), list(yetkili))


def _sema_tamam_mi():
    """Hedef sütunlar ve indeks zaten var mı? (Varsa ALTER hiç çalıştırılmaz: kilit beklemesi olmasın.)"""
    ins = inspect(db.session.connection())
    arsa = {c['name'] for c in ins.get_columns('arsa_analizleri')}
    if not {ad for ad, _ in ARSA_SUTUNLARI} <= arsa:
        return False
    if 'ilan_id' not in {c['name'] for c in ins.get_columns('crm_deals')}:
        return False
    return 'ix_crm_deals_ilan_id' in {i['name'] for i in ins.get_indexes('crm_deals')}


def _sutunlari_ekle():
    if db.engine.dialect.name != 'postgresql':
        log.warning("İlan kurulumu: yeni sütunlar sadece PostgreSQL'de otomatik eklenir; "
                    "diğer veritabanlarında arsa_analizleri ve crm_deals.ilan_id sütunlarını elle ekleyin.")
        return
    if _sema_tamam_mi():
        return
    # Üretimde açılış bir tablo kilidini sonsuza dek beklemesin
    db.session.execute(text("SET LOCAL lock_timeout = '10s'"))
    for ad, tip in ARSA_SUTUNLARI:
        db.session.execute(text(f"ALTER TABLE arsa_analizleri ADD COLUMN IF NOT EXISTS {ad} {tip}"))
    db.session.execute(text("ALTER TABLE crm_deals ADD COLUMN IF NOT EXISTS ilan_id INTEGER "
                            "REFERENCES ilanlar(id) ON DELETE SET NULL"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_deals_ilan_id ON crm_deals (ilan_id)"))


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
        ilan = Ilan(kod=yeni_ilan_kodu(yil), baslik=a.baslik_metni[:200], teklif_tipi='satilik', durum='pazarlamada',
                    fiyat=a.fiyat, bolge_m2_fiyat_elle=donustur(a), office_id=a.office_id,
                    user_id=a.user_id, sorumlu_user_id=a.user_id)
        ilan.baglar.append(IlanGayrimenkul(gayrimenkul=a, ana_kayit=True, sira=1))
        db.session.add(ilan)
        db.session.flush()  # sonraki yeni_ilan_kodu bu kodu görsün
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
        if db.session.get(KurulumIsareti, GECIS_ISARETI) is None:
            db.session.execute(text("UPDATE arsa_analizleri SET tur = 'arsa' WHERE tur IS NULL"))
            _ozellikleri_doldur()
            _ilanlari_olustur()
            _portfoyleri_kopyala()
            db.session.add(KurulumIsareti(ad=GECIS_ISARETI))
            log.info("İlan kurulumu: veri geçişi tamamlandı (%s).", GECIS_ISARETI)
        _rls_ac()
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("İlan kurulumu sırasında hata")
        raise
