"""Sunucu hataları superadmin kullanıcılara zil bildirimi olarak düşer; aynı hata günde bir kez."""
import pytest

from models import db
from models.is_takip_models import Bildirim
from models.user_models import User
from modules.hata_bildirimi import bildir


def _kullanici(email, role, aktif=True):
    u = User(email=email, role=role, ad=email.split('@')[0])
    u.set_password('Test1234!')
    u._is_active = aktif
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def superadmin(db_session):
    return _kullanici('sa@test.com', 'superadmin')


@pytest.fixture
def danisman(db_session):
    return _kullanici('d@test.com', 'danisman')


def test_hata_superadmine_bildirilir(db_session, superadmin):
    assert bildir('POST', '/x', ValueError('a')) == 1
    b = Bildirim.query.filter_by(user_id=superadmin.id, tur='hata').one()
    assert b.mesaj == 'Sunucu hatası: POST /x (ValueError)'
    assert b.okundu is False


def test_ayni_hata_gunde_bir_kez(db_session, superadmin):
    for _ in range(100):
        bildir('POST', '/x', ValueError('a'))
    assert Bildirim.query.filter_by(tur='hata').count() == 1


def test_farkli_yol_ayri_bildirim(db_session, superadmin):
    bildir('POST', '/x', ValueError('a'))
    bildir('GET', '/y', ValueError('a'))
    assert Bildirim.query.filter_by(tur='hata').count() == 2


def test_danismana_bildirilmez(db_session, superadmin, danisman):
    bildir('POST', '/x', ValueError('a'))
    assert Bildirim.query.filter_by(user_id=danisman.id).count() == 0


def test_pasif_superadmine_bildirilmez(db_session):
    pasif = _kullanici('eski@test.com', 'superadmin', aktif=False)
    assert bildir('POST', '/x', ValueError('a')) == 0
    assert Bildirim.query.filter_by(user_id=pasif.id).count() == 0


def test_bozuk_oturumda_da_calisir(db_session, superadmin):
    """Hata çoğu zaman yarım kalmış bir veritabanı işleminin ortasında oluşur."""
    db.session.add(Bildirim(user_id=None, tur='x', mesaj='geçersiz'))  # commit edilirse NOT NULL ihlali
    with pytest.raises(Exception):
        db.session.flush()
    assert bildir('POST', '/x', ValueError('a')) == 1


def test_uzun_yol_kirpilir(db_session, superadmin):
    assert bildir('GET', '/' + 'a' * 900, ValueError('a')) == 1
    assert len(Bildirim.query.filter_by(tur='hata').one().mesaj) <= 500


def test_500_karsilayici_bildirim_uretir(app, db_session, superadmin, monkeypatch):
    def patla(*a, **kw):
        raise RuntimeError('patladı')

    giris_ucu = next(r.endpoint for r in app.url_map.iter_rules() if r.rule == '/auth/login')
    monkeypatch.setitem(app.view_functions, giris_ucu, patla)
    monkeypatch.setitem(app.config, 'PROPAGATE_EXCEPTIONS', False)
    r = app.test_client().get('/auth/login')
    assert r.status_code == 500
    assert Bildirim.query.filter_by(tur='hata').one().mesaj == 'Sunucu hatası: GET /auth/login (RuntimeError)'
