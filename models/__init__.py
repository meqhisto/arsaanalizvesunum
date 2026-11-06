# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Model import'larını dışarı çıkaralım
from .user_models import User, Portfolio
from .arsa_models import ArsaAnaliz, BolgeDagilimi, YatirimPerformansi, DashboardStats, AnalizMedya
from .crm_models import Contact, Company, Interaction, Deal, Task, CrmTeam, crm_team_members
from .office_models import Office
from .permission_models import PermissionTemplate, UserPermission, OfficePermission, PermissionLog, PermissionManager
from .is_takip_models import IsSablonu, IsSablonAdimi, Is, IsBelgesi, IsMasrafi, IsAktivitesi, Bildirim

def _ensure_columns():
    """Sonradan eklenen sütunları mevcut tablolara ekler (create_all bunu yapmaz)."""
    from sqlalchemy import inspect, text
    eklenecek = {'arsa_analizleri': {'deger_artis_orani': 'NUMERIC(5,2) NULL'}}
    inspector = inspect(db.engine)
    for tablo, sutunlar in eklenecek.items():
        if not inspector.has_table(tablo):
            continue
        mevcut = {c['name'] for c in inspector.get_columns(tablo)}
        for ad, tip in sutunlar.items():
            if ad not in mevcut:
                try:
                    with db.engine.begin() as conn:
                        conn.execute(text(f'ALTER TABLE {tablo} ADD {ad} {tip}'))
                except Exception as e:  # Başka bir worker aynı anda eklemiş olabilir
                    print(f"Sütun eklenemedi ({tablo}.{ad}): {e}")


def init_db_models(app):
    """Veritabanını uygulamaya bağlar ve tabloları oluşturur."""
    db.init_app(app)

    # Modelleri burada import etmek, create_all çağrılmadan önce
    # SQLAlchemy'nin tüm model tanımlarını bilmesini sağlar.
    from . import user_models
    from . import arsa_models
    from . import crm_models
    from . import office_models
    from . import permission_models
    from . import is_takip_models
    # Bu importlar, user_models.py, arsa_models.py, crm_models.py dosyalarının
    # içindeki tüm model sınıflarını yükler.

    with app.app_context():
        print("Veritabanı tabloları oluşturuluyor...")
        db.create_all()
        _ensure_columns()
        print("Veritabanı tabloları (models/__init__.py üzerinden) başarıyla oluşturuldu!")
        from modules.is_takip_kurulum import kur as is_takip_kur
        is_takip_kur()