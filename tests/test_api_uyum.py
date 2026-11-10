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


def test_api_silme_ilanlari_temizler(app, kullanicilar):
    """API DELETE web silme yolunu kullanır: tek gayrimenkullü ilan silinir, çoklu ilandan yalnız bağ çıkar."""
    br = kullanicilar['broker']
    tek = ArsaAnaliz(user_id=br, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='1', parsel='1',
                     metrekare=500, fiyat=1000000, tur='arsa')
    a1 = ArsaAnaliz(user_id=br, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='2', parsel='1',
                    metrekare=500, fiyat=1000000, tur='arsa')
    a2 = ArsaAnaliz(user_id=br, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='2', parsel='2',
                    metrekare=500, fiyat=1000000, tur='arsa')
    db.session.add_all([tek, a1, a2])
    db.session.flush()
    i_tek = Ilan(kod='ILN-2026-0001', baslik='Tek', user_id=br, sorumlu_user_id=br,
                 teklif_tipi='satilik', durum='pazarlamada', fiyat=1000000)
    i_tek.baglar.append(IlanGayrimenkul(gayrimenkul=tek, ana_kayit=True, sira=1))
    i_cift = Ilan(kod='ILN-2026-0002', baslik='Çift', user_id=br, sorumlu_user_id=br,
                  teklif_tipi='satilik', durum='pazarlamada', fiyat=2000000)
    i_cift.baglar.append(IlanGayrimenkul(gayrimenkul=a1, ana_kayit=True, sira=1))
    i_cift.baglar.append(IlanGayrimenkul(gayrimenkul=a2, ana_kayit=False, sira=2))
    db.session.add_all([i_tek, i_cift])
    db.session.commit()
    tek_id, a1_id, a2_id, i_tek_id, i_cift_id = tek.id, a1.id, a2.id, i_tek.id, i_cift.id

    H = {'Authorization': f'Bearer {_token(app, "broker@test.com")}'}
    assert app.test_client().delete(f'/api/v1/analysis/{tek_id}', headers=H).status_code == 200
    assert app.test_client().delete(f'/api/v1/analysis/{a1_id}', headers=H).status_code == 200
    db.session.expire_all()
    assert db.session.get(Ilan, i_tek_id) is None
    cift = db.session.get(Ilan, i_cift_id)
    assert cift is not None and [b.gayrimenkul_id for b in cift.baglar] == [a2_id]
    assert ArsaAnaliz.query.filter(ArsaAnaliz.id.in_([tek_id, a1_id])).count() == 0


def test_api_v1_modullerinin_hepsi_ice_aktarilir():
    import importlib
    import pkgutil

    import blueprints.api.v1 as v1
    for m in pkgutil.iter_modules(v1.__path__):
        importlib.import_module(f'blueprints.api.v1.{m.name}')
