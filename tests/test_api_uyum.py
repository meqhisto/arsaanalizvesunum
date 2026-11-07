"""REST API geriye dönük uyum: eski analiz alanları korunur, gayrimenkul/ilan alanları salt-okunur eklenir (spec §7)."""
from models import db
from models.arsa_models import ArsaAnaliz
from models.ilan_models import Ilan, IlanGayrimenkul


def _token(app, email):
    r = app.test_client().post('/api/v1/auth/login', json={'email': email, 'password': 'Test1234!'})
    assert r.status_code == 200, r.get_data(as_text=True)[:200]
    js = r.get_json()
    return (js.get('data') or {}).get('access_token') or js.get('access_token')


def test_api_analiz_listesi_eski_alanlar_ve_yeni_alanlar(app, kullanicilar):
    br = kullanicilar['broker']
    arsa = ArsaAnaliz(user_id=br, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='213', parsel='2',
                      metrekare=800, fiyat=4000000, imar_durumu='Konut', tur='arsa')
    dukkan = ArsaAnaliz(user_id=br, il='Çanakkale', ilce='Merkez', mahalle='Cevatpaşa', metrekare=60,
                        fiyat=0, tur='isyeri', alt_tur='dukkan', baslik='Çarşı dükkânı')
    db.session.add_all([arsa, dukkan])
    db.session.flush()
    ilan = Ilan(kod='ILN-2026-0001', baslik='Kepez arsa', user_id=br, sorumlu_user_id=br,
                teklif_tipi='satilik', durum='pazarlamada', fiyat=4000000)
    ilan.baglar.append(IlanGayrimenkul(gayrimenkul=arsa, ana_kayit=True, sira=1))
    db.session.add(ilan)
    db.session.commit()
    arsa_id, dukkan_id = arsa.id, dukkan.id

    H = {'Authorization': f'Bearer {_token(app, "broker@test.com")}'}
    r = app.test_client().get('/api/v1/analysis', headers=H)
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    js = r.get_json()
    kayitlar = {k['id']: k for k in js['data']['data']}
    a = kayitlar[arsa_id]
    # Eski alanlar
    for alan in ('il', 'ilce', 'mahalle', 'ada', 'parsel', 'metrekare', 'fiyat', 'imar_durumu', 'created_at'):
        assert alan in a
    assert a['il'] == 'Çanakkale' and a['metrekare'] == 800.0 and a['fiyat'] == 4000000.0
    # Yeni salt-okunur alanlar
    assert a['tur'] == 'arsa'
    assert a['aktif_ilan']['kod'] == 'ILN-2026-0001'
    assert a['aktif_ilan']['teklif_tipi'] == 'satilik' and a['aktif_ilan']['durum'] == 'pazarlamada'
    assert a['aktif_ilan']['fiyat'] == 4000000.0
    d = kayitlar[dukkan_id]
    assert d['tur'] == 'isyeri' and d['alt_tur'] == 'dukkan' and d['baslik'] == 'Çarşı dükkânı'
    assert d['aktif_ilan'] is None and d['fiyat'] == 0.0

    # Detay da aynı alanları verir
    r = app.test_client().get(f'/api/v1/analysis/{arsa_id}', headers=H)
    assert r.status_code == 200
    det = r.get_json()['data']
    assert det['fiyat'] == 4000000.0 and det['tur'] == 'arsa' and det['aktif_ilan']['kod'] == 'ILN-2026-0001'

    # Yeni alanlar API ile güncellenemez (GUNCELLENEBILIR listesi değişmedi)
    r = app.test_client().put(f'/api/v1/analysis/{arsa_id}', headers=H, json={'tur': 'konut'})
    assert r.status_code == 400
    r = app.test_client().put(f'/api/v1/analysis/{arsa_id}', headers=H, json={'notlar': 'güncel'})
    assert r.status_code == 200
    up = r.get_json()['data']
    assert up['tur'] == 'arsa' and up['aktif_ilan']['kod'] == 'ILN-2026-0001'
