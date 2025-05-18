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
    from . import office_models
    # Bu importlar, user_models.py, arsa_models.py, crm_models.py dosyalarının
    # içindeki tüm model sınıflarını yükler.
    


    from .user_models import User
    with app.app_context():
        print("Veritabanı tabloları oluşturuluyor...")
        db.create_all()
        print("Veritabanı tabloları (models/__init__.py üzerinden) başarıyla oluşturuldu!")
        
    from .user_models import User, Portfolio # portfolio_arsalar'ı da ekleyebilirsiniz
    from .arsa_models import ArsaAnaliz, BolgeDagilimi, YatirimPerformansi, DashboardStats, AnalizMedya
    from .crm_models import Contact, Company, Interaction, Deal, Task, CrmTeam, crm_team_members
    from .office_models import Office # YENİ EKLEDİK