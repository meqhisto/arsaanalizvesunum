"""Tarayıcı testleri için başlangıç verisi (yalnız SQLite test kopyasında çalışır)."""
import contextlib
import io
import logging
import os
import sys

if not os.environ.get('DATABASE_URL', '').startswith('sqlite:'):
    sys.exit('tohum.py yalnız SQLite test veritabanında çalışır')

sys.path.insert(0, '/app')
logging.disable(logging.CRITICAL)
with contextlib.redirect_stdout(io.StringIO()):
    from app import create_app
    app = create_app()

from models import db  # noqa: E402
from models.arsa_models import ArsaAnaliz  # noqa: E402
from models.crm_models import Contact  # noqa: E402
from models.is_takip_models import Is  # noqa: E402
from models.office_models import Office  # noqa: E402
from models.user_models import User  # noqa: E402

with app.app_context():
    db.create_all()
    if not User.query.first():
        ofis = Office(name='Test Ofis')
        db.session.add(ofis)
        db.session.flush()
        k = User(email='t@t.co', ad='Test', soyad='Kullanici', role='superadmin', office_id=ofis.id)
        k.set_password('Abc12345!')
        db.session.add(k)
        db.session.flush()
        db.session.add_all([
            ArsaAnaliz(user_id=k.id, il='Çanakkale', ilce='Merkez', mahalle='Kepez', metrekare=500, fiyat=1000000),
            Is(kod='IS-1', baslik='Test işi', sorumlu_user_id=k.id, olusturan_user_id=k.id, office_id=ofis.id),
            Contact(user_id=k.id, first_name='Mevcut', last_name='Musteri'),
        ])
        db.session.commit()
print('tohum tamam')
