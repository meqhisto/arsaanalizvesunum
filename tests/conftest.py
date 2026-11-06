import os

import pytest

from flask import g, request_started
from sqlalchemy.engine import make_url

TEST_VERITABANI_ADI = 'arsa_ilan_test'

if not os.environ.get('TEST_VERITABANI') or 'supabase' in os.environ.get('DATABASE_URL', ''):
    pytest.exit("Testler yalnız yerel test veritabanında çalışır")
try:
    _vt_adi = make_url(os.environ.get('DATABASE_URL', '')).database
except Exception:
    _vt_adi = None
if _vt_adi != TEST_VERITABANI_ADI:
    # drop_all() başka bir veritabanına asla dokunmamalı
    pytest.exit(f"Testler yalnız '{TEST_VERITABANI_ADI}' veritabanında çalışır (DATABASE_URL: {_vt_adi!r})")

from app import create_app  # noqa: E402
from models import db  # noqa: E402
from models.office_models import Office  # noqa: E402
from models.user_models import User  # noqa: E402


def _login_onbellegini_temizle(sender, **kwargs):
    g.pop('_login_user', None)


@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update(WTF_CSRF_ENABLED=False, TESTING=True)
    # Test istemcisi açık app context'i (dolayısıyla g'yi) yeniden kullanır; flask_login'in g'de
    # önbelleklediği kullanıcı önceki istekten/testten kalmasın diye her istek başında temizlenir.
    request_started.connect(_login_onbellegini_temizle, app)
    with app.app_context():
        db.drop_all()
        db.create_all()
        from modules.ilan_kurulum import kur as ilan_kur
        ilan_kur()
        yield app
        db.session.remove()


def _tablolari_bosalt():
    """Tüm tabloları (kurulum_isaretleri dahil) boşaltır ve oturumun kimlik haritasını temizler."""
    db.session.rollback()
    tablolar = ', '.join(f'"{t.name}"' for t in db.metadata.sorted_tables)
    db.session.execute(db.text(f'TRUNCATE {tablolar} RESTART IDENTITY CASCADE'))
    db.session.commit()
    db.session.expunge_all()


@pytest.fixture
def db_session(app):
    # Öncesinde de boşalt: app fixture'ındaki ilan_kur() geçiş işaretini yazmış olabilir
    _tablolari_bosalt()
    yield db.session
    _tablolari_bosalt()


@pytest.fixture
def kullanicilar(db_session):
    ofis = Office(name='Test Ofis')
    db.session.add(ofis)
    db.session.flush()

    def yarat(email, role, office_id=None, manager_id=None):
        u = User(email=email, role=role, office_id=office_id, manager_id=manager_id, ad=email.split('@')[0])
        u.set_password('Test1234!')
        db.session.add(u)
        db.session.flush()
        return u

    broker = yarat('broker@test.com', 'broker', ofis.id)
    d1 = yarat('d1@test.com', 'danisman', ofis.id, broker.id)
    d2 = yarat('d2@test.com', 'danisman', ofis.id)
    dx = yarat('dx@test.com', 'danisman')
    sa = yarat('sa@test.com', 'superadmin')
    db.session.commit()
    return {'ofis': ofis.id, 'broker': broker.id, 'd1': d1.id, 'd2': d2.id, 'dx': dx.id, 'sa': sa.id}


def giris(client, user_id):
    """client'a kullanıcıyı oturum açmış yazar. Her kullanıcı için AYRI app.test_client() verin
    (aynı app context'te g paylaşımı yüzünden ikinci kullanıcı ilkinin kimliğini almasın)."""
    with client.session_transaction() as s:
        s['_user_id'] = str(user_id)
        s['_fresh'] = True
    return client
