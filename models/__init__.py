# models/__init__.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db_models(app):
    """Veritabanını uygulamaya bağlar ve tabloları oluşturur."""
    db.init_app(app)

    # Modelleri burada import etmek, create_all çağrılmadan önce
    # SQLAlchemy'nin tüm model tanımlarını bilmesini sağlar.
    from . import user_models
    from . import arsa_models
    from . import crm_models
    # Bu importlar, user_models.py, arsa_models.py, crm_models.py dosyalarının
    # içindeki tüm model sınıflarını yükler.

    with app.app_context():
        print("Veritabanı tabloları oluşturuluyor...")
        db.create_all()
        print("Veritabanı tabloları (models/__init__.py üzerinden) başarıyla oluşturuldu!")