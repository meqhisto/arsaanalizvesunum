# -*- coding: utf-8 -*-
"""İş takip modülü için açılışta çalışan, tekrar çalıştırılabilir kurulum adımları.

Uygulama tabloları `db.create_all()` ile kuruyor; create_all mevcut tabloya sütun eklemediği
için crm_tasks'a eklenen sütunlar burada `IF NOT EXISTS` ile eklenir. Ayrıca hazır iş
şablonları (yoksa) oluşturulur.
"""
import logging

from sqlalchemy import text

from models import db
from models.is_takip_models import IsSablonu, IsSablonAdimi

log = logging.getLogger(__name__)

# (adım başlığı, önceki adımdan gün, sorumlu rol, gerekli belge türü)
HAZIR_SABLONLAR = [
    {
        'ad': 'Arsa satışı (aracılık)', 'is_turu': 'Arsa satışı',
        'aciklama': 'Yetki sözleşmesinden tapu devrine ve komisyon tahsilatına kadar arsa satış süreci.',
        'adimlar': [
            ('Yetki / aracılık sözleşmesi imzası', 0, 'danisman', 'Sözleşme'),
            ('Tapu kaydı ve takyidat sorgusu', 2, 'danisman', 'Tapu'),
            ('İmar durumu belgesinin alınması', 5, 'danisman', 'İmar durumu'),
            ('Arsa analizi ve değerleme raporu', 2, 'danisman', None),
            ('İlan ve pazarlama', 3, 'danisman', None),
            ('Alıcı görüşmeleri ve teklif', 30, 'danisman', None),
            ('Kapora / ön satış sözleşmesi', 5, 'broker', 'Sözleşme'),
            ('Tapu randevusu ve harç ödemesi', 7, 'danisman', 'Fatura / Makbuz'),
            ('Tapu devri', 3, 'danisman', 'Tapu'),
            ('Komisyon tahsilatı', 2, 'broker', 'Fatura / Makbuz'),
        ],
    },
    {
        'ad': 'Arsa alımı – ön inceleme', 'is_turu': 'Arsa alımı',
        'aciklama': 'Alıcı adına arsanın hukuki, imar ve değer açısından incelenip satın alınması.',
        'adimlar': [
            ('Tapu ve takyidat sorgusu', 0, 'danisman', 'Tapu'),
            ('İmar durumu sorgusu', 3, 'danisman', 'İmar durumu'),
            ('Yerinde inceleme ve fotoğraf', 3, 'danisman', 'Fotoğraf'),
            ('Değerleme / arsa analizi', 3, 'danisman', None),
            ('Teklif ve pazarlık', 7, 'broker', None),
            ('Satış sözleşmesi', 5, 'broker', 'Sözleşme'),
            ('Tapu devri', 7, 'danisman', 'Tapu'),
        ],
    },
    {
        'ad': 'İmar / ruhsat başvurusu', 'is_turu': 'İmar / Ruhsat',
        'aciklama': 'Aplikasyondan yapı ruhsatının alınmasına kadar belediye süreci.',
        'adimlar': [
            ('Aplikasyon krokisi', 0, 'danisman', 'Proje'),
            ('İmar durumu belgesi', 7, 'danisman', 'İmar durumu'),
            ('Zemin etüdü', 14, 'danisman', 'Proje'),
            ('Mimari ve statik projeler', 30, 'danisman', 'Proje'),
            ('Ruhsat başvurusu', 7, 'danisman', None),
            ('Harç ödemeleri', 7, 'danisman', 'Fatura / Makbuz'),
            ('Yapı ruhsatının alınması', 21, 'broker', 'Ruhsat'),
        ],
    },
    {
        'ad': 'Kat karşılığı proje', 'is_turu': 'Kat karşılığı',
        'aciklama': 'Arsa sahipleri ile müteahhit arasında kat karşılığı inşaat sürecinin takibi.',
        'adimlar': [
            ('Arsa sahipleriyle ön görüşme', 0, 'broker', None),
            ('Analiz ve fizibilite', 7, 'danisman', None),
            ('Müteahhit seçimi', 21, 'broker', None),
            ('Kat karşılığı sözleşmesi (noter)', 14, 'broker', 'Sözleşme'),
            ('Proje ve ruhsat', 60, 'danisman', 'Ruhsat'),
            ('İnşaat takibi', 365, 'danisman', 'Fotoğraf'),
            ('İskan', 30, 'danisman', None),
            ('Bağımsız bölüm teslimi', 15, 'broker', 'Tapu'),
        ],
    },
]


def _crm_tasks_sutunlarini_ekle():
    if db.engine.dialect.name != 'postgresql':
        log.warning("İş takip: crm_tasks sütunları sadece PostgreSQL'de otomatik eklenir; "
                    "diğer veritabanlarında is_id ve sira sütunlarını elle ekleyin.")
        return
    with db.engine.begin() as conn:
        conn.execute(text("ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS is_id INTEGER "
                          "REFERENCES isler(id) ON DELETE CASCADE"))
        conn.execute(text("ALTER TABLE crm_tasks ADD COLUMN IF NOT EXISTS sira INTEGER"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_crm_tasks_is_id ON crm_tasks (is_id)"))


def _hazir_sablonlari_ekle():
    if IsSablonu.query.filter(IsSablonu.office_id.is_(None)).count():
        return
    for tanim in HAZIR_SABLONLAR:
        sablon = IsSablonu(ad=tanim['ad'], is_turu=tanim['is_turu'], aciklama=tanim['aciklama'])
        for sira, (baslik, gun, rol, belge) in enumerate(tanim['adimlar'], start=1):
            sablon.adimlar.append(IsSablonAdimi(sira=sira, baslik=baslik, varsayilan_sure_gun=gun,
                                                sorumlu_rol=rol, gerekli_belge_turu=belge))
        db.session.add(sablon)
    db.session.commit()
    log.info("İş takip: hazır iş şablonları oluşturuldu.")


def kur():
    try:
        _crm_tasks_sutunlarini_ekle()
        _hazir_sablonlari_ekle()
    except Exception:
        db.session.rollback()
        log.exception("İş takip kurulumu sırasında hata")
        raise
