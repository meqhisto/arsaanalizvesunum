"""CSRF koruması: tarayıcıdan gelen form ve JSON istekleri token ister; JWT kullanan /api muaftır."""
import re

import pytest
from flask import g, request_started

from models import db
from models.user_models import User
from tests.conftest import giris

UYARI = 'Sayfayı yenileyip'


def _csrf_onbellegini_temizle(sender, **kwargs):
    # Flask-WTF token'ı g'de önbellekler; test istemcisi g'yi istekler arasında paylaştığı için
    # önceki isteğin (başka oturumun) token'ı kalmasın.
    g.pop('csrf_token', None)
    g.pop('csrf_valid', None)


@pytest.fixture
def csrf_app(app):
    app.config['WTF_CSRF_ENABLED'] = True
    request_started.connect(_csrf_onbellegini_temizle, app)
    yield app
    request_started.disconnect(_csrf_onbellegini_temizle, app)
    app.config['WTF_CSRF_ENABLED'] = False


@pytest.fixture
def csrf_istemci(csrf_app, kullanicilar):
    return giris(csrf_app.test_client(), kullanicilar['sa'])


def kullanici(kullanicilar):
    db.session.expire_all()
    return db.session.get(User, kullanicilar['sa'])


def meta_token(yanit):
    m = re.search(r'<meta name="csrf-token" content="([^"]+)"', yanit.get_data(as_text=True))
    return m.group(1) if m else ''


FORM = {'ad': 'X', 'soyad': 'Y', 'timezone': 'UTC'}


def test_tokensiz_form_reddedilir(csrf_istemci, kullanicilar):
    r = csrf_istemci.post('/profile', data=FORM, headers={'Referer': 'http://localhost/profile'})
    assert r.status_code == 302 and r.headers['Location'].endswith('/profile')
    assert kullanici(kullanicilar).ad != 'X'
    with csrf_istemci.session_transaction() as s:
        assert any(UYARI in mesaj for _, mesaj in s.get('_flashes', []))


def test_tokenli_form_kabul_edilir(csrf_istemci, kullanicilar):
    token = meta_token(csrf_istemci.get('/profile'))
    assert token
    csrf_istemci.post('/profile', data=dict(FORM, csrf_token=token))
    assert kullanici(kullanicilar).ad == 'X'


def test_tokensiz_json_400_doner(csrf_istemci):
    r = csrf_istemci.post('/crm/api/import/validate', json={'column_mapping': {}})
    assert r.status_code == 400 and UYARI in r.get_json()['error']


def test_json_hata_yaniti_sayfalarin_okudugu_tum_anahtarlari_tasir(csrf_istemci):
    """Sayfalardaki betikler hata metnini farklı anahtarlardan okur (hata, message, error); hepsi dolu olmalı."""
    veri = csrf_istemci.post('/crm/api/import/validate', json={'column_mapping': {}}).get_json()
    assert UYARI in veri['hata'] and UYARI in veri['message'] and UYARI in veri['error']
    assert veri['success'] is False and veri['ok'] is False


def test_baslikla_json_kabul_edilir(csrf_istemci):
    token = meta_token(csrf_istemci.get('/profile'))
    r = csrf_istemci.post('/crm/api/import/validate', json={'column_mapping': {}}, headers={'X-CSRFToken': token})
    assert UYARI not in r.get_data(as_text=True)


def test_jwt_api_muaf(csrf_istemci):
    r = csrf_istemci.post('/api/v1/auth/login', json={'email': 'yok@x.co', 'password': 'x'})
    assert UYARI not in r.get_data(as_text=True)
    assert r.status_code != 400 or 'CSRF' not in r.get_data(as_text=True)


def test_giris_sayfasinda_token_var(csrf_app):
    assert meta_token(csrf_app.test_client().get('/auth/login'))


def test_yabanci_referer_ana_sayfaya_doner(csrf_istemci):
    r = csrf_istemci.post('/profile', data=FORM, headers={'Referer': 'http://kotu.example/x'})
    assert r.status_code == 302 and 'kotu.example' not in r.headers['Location']
