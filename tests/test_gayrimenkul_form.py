import pytest

from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact
from models.ilan_models import Ilan
from conftest import giris


def istemci(app, user_id):
    return giris(app.test_client(), user_id)


def temel(tur, **alanlar):
    v = {'tur': tur, 'il': 'Çanakkale', 'ilce': 'Merkez', 'mahalle': 'Kepez'}
    v.update(alanlar)
    return v


def arsa_formu(**kw):
    return temel('arsa', ada='213', parsel='2', metrekare='800', imar_durumu='Konut', **kw)


def olustur(client, veri):
    return client.post('/analysis/create', data=veri)


def kontak(user_id, ad='Ali', telefon='5551112233'):
    c = Contact(user_id=user_id, first_name=ad, last_name='Yılmaz', phone=telefon)
    db.session.add(c)
    db.session.commit()
    return c.id


@pytest.mark.parametrize('tur,alanlar,metrekare', [
    ('arsa', {'ada': '213', 'parsel': '2', 'metrekare': '800', 'imar_durumu': 'Konut', 'kaks': '1,5'}, 800),
    ('tarla', {'ada': '101', 'parsel': '7', 'metrekare': '12.000'}, 12000),
    ('konut', {'alt_tur': 'daire', 'brut_m2': '120', 'net_m2': '105', 'oda_sayisi': '3+1', 'bulundugu_kat': '4',
               'bina_yasi': '5', 'isinma': 'Kombi (doğalgaz)'}, 120),
    ('isyeri', {'alt_tur': 'dukkan', 'brut_m2': '85'}, 85),
    ('bina', {'brut_m2': '640', 'toplam_kat': '5'}, 640),
])
def test_her_tur_olusturulur(app, kullanicilar, tur, alanlar, metrekare):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, temel(tur, **alanlar))
    assert r.status_code == 302, r.get_data(as_text=True)[:2000]
    g = ArsaAnaliz.query.one()
    assert r.headers['Location'].endswith(f'/analysis/{g.id}')
    assert g.tur == tur
    assert float(g.metrekare) == metrekare
    assert g.user_id == kullanicilar['d1']
    assert g.office_id == kullanicilar['ofis']
    if tur == 'arsa':
        assert float(g.kaks) == 1.5
    if tur == 'konut':
        assert g.alt_tur == 'daire' and g.oda_sayisi == '3+1' and g.bina_yasi == 5
        assert float(g.net_m2) == 105 and g.isinma == 'Kombi (doğalgaz)'
        assert g.ada is None and g.kaks is None


def test_konutta_ada_parsel_zorunlu_degil_arsada_zorunlu(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, temel('arsa', parsel='2', metrekare='800'))
    assert r.status_code == 200
    assert 'Ada alanı zorunludur' in r.get_data(as_text=True)
    assert ArsaAnaliz.query.count() == 0

    r = olustur(c, temel('konut', alt_tur='daire', brut_m2='120', oda_sayisi='2+1'))
    assert r.status_code == 302
    assert ArsaAnaliz.query.count() == 1


def test_konutta_oda_sayisi_zorunlu_ve_tur_gecerli_olmali(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, temel('konut', brut_m2='120'))
    assert r.status_code == 200
    assert 'Oda sayısı alanı zorunludur' in r.get_data(as_text=True)
    r = olustur(c, temel('uzay', brut_m2='120'))
    assert r.status_code == 200
    assert 'Gayrimenkul türü' in r.get_data(as_text=True)
    r = olustur(c, arsa_formu(taks='1,5'))
    assert r.status_code == 200
    assert 'TAKS' in r.get_data(as_text=True)
    assert ArsaAnaliz.query.count() == 0


def test_tur_degisince_tur_disi_alanlar_temizlenir(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    assert olustur(c, arsa_formu(kaks='1,5', taks='0,3')).status_code == 302
    g = ArsaAnaliz.query.one()
    r = c.post(f'/analysis/{g.id}/edit', data=temel('konut', alt_tur='daire', brut_m2='110', oda_sayisi='2+1',
                                                   ada='213', kaks='1,5'))
    assert r.status_code == 302, r.get_data(as_text=True)[:2000]
    db.session.expire_all()
    g = db.session.get(ArsaAnaliz, g.id)
    assert g.tur == 'konut'
    assert g.ada is None and g.parsel is None and g.kaks is None and g.taks is None
    assert float(g.metrekare) == 110

    r = c.post(f'/analysis/{g.id}/edit', data=arsa_formu(oda_sayisi='3+1', aidat='500'))
    assert r.status_code == 302
    db.session.expire_all()
    g = db.session.get(ArsaAnaliz, g.id)
    assert g.tur == 'arsa' and g.oda_sayisi is None and g.aidat is None and g.brut_m2 is None
    assert float(g.metrekare) == 800


def test_duzenleme_formu_mevcut_degerleri_gosterir(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    olustur(c, temel('konut', alt_tur='villa', brut_m2='250', oda_sayisi='5+2', oz_ic=['Şömine']))
    g = ArsaAnaliz.query.one()
    r = c.get(f'/analysis/{g.id}/edit')
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'value="5+2"' in html
    assert 'value="Şömine" checked' in html


def test_ozellikler_listede_olmayani_almaz(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, arsa_formu(oz_ic=['Asansör', 'Uydurma'], oz_altyapi=['yol', 'su']))
    assert r.status_code == 302
    g = ArsaAnaliz.query.one()
    assert g.ozellikler['ic'] == ['Asansör']
    assert g.ozellikler['altyapi'] == ['yol', 'su']


def test_swot_hidden_alanlardan_okunur(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, arsa_formu(strengths='["Denize yakın"]', threats='["Sel riski"]'))
    assert r.status_code == 302
    from modules.rapor.model import parse_swot
    swot = parse_swot(ArsaAnaliz.query.one().swot_analizi)
    assert swot['strengths'] == ['Denize yakın'] and swot['threats'] == ['Sel riski']


def test_hisseli_sahipler_ve_yeni_kontak(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = c.post('/analysis/kontak-ekle', json={'ad': 'Ayşe', 'soyad': '', 'telefon': '5550001122'})
    assert r.status_code == 200
    yeni_id = r.get_json()['id']
    yeni = db.session.get(Contact, yeni_id)
    assert yeni.user_id == kullanicilar['d1'] and yeni.last_name == '-' and yeni.status == 'Mal sahibi'
    assert yeni.source == 'Portföy' and yeni.office_id == kullanicilar['ofis']
    eski_id = kontak(kullanicilar['d1'], 'Mehmet')

    r = olustur(c, arsa_formu(**{'sahip_contact_id[]': [str(eski_id), str(yeni_id)],
                                 'sahip_hisse[]': ['1/2', '1/2'], 'sahip_irtibat': str(yeni_id)}))
    assert r.status_code == 302, r.get_data(as_text=True)[:2000]
    g = ArsaAnaliz.query.one()
    sahipler = {s.contact_id: s for s in g.sahiplikler}
    assert set(sahipler) == {eski_id, yeni_id}
    assert sahipler[eski_id].hisse == '1/2' and sahipler[yeni_id].hisse == '1/2'
    assert sahipler[yeni_id].irtibat and not sahipler[eski_id].irtibat


def test_kontak_ekle_ad_bos_ise_400(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = c.post('/analysis/kontak-ekle', json={'ad': '  ', 'telefon': '555'})
    assert r.status_code == 400
    assert Contact.query.count() == 0


def test_baskasinin_kontagi_sahip_secilemez(app, kullanicilar):
    d2_kontak = kontak(kullanicilar['d2'], 'Zeynep')
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, arsa_formu(**{'sahip_contact_id[]': [str(d2_kontak)], 'sahip_hisse[]': ['']}))
    assert r.status_code == 200
    assert 'Seçilen müşteri bulunamadı.' in r.get_data(as_text=True)
    assert ArsaAnaliz.query.count() == 0


def test_hemen_ilana_cikar(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, arsa_formu(ilana_cikar='1', ilan_teklif_tipi='satilik', ilan_fiyat='4.250.000'))
    assert r.status_code == 302, r.get_data(as_text=True)[:2000]
    g = ArsaAnaliz.query.one()
    ilan = Ilan.query.one()
    assert float(ilan.fiyat) == 4250000
    assert ilan.durum == 'pazarlamada' and ilan.teklif_tipi == 'satilik'
    assert ilan.gayrimenkuller == [g]
    assert float(g.fiyat) == 4250000


def test_hemen_ilana_cikar_hatasinda_hicbir_sey_kaydedilmez(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    r = olustur(c, arsa_formu(ilana_cikar='1', ilan_teklif_tipi='satilik', ilan_fiyat=''))
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'Satılık ilanda fiyat zorunludur.' in html
    assert 'value="213"' in html  # girilen değerler korunur
    assert ArsaAnaliz.query.count() == 0 and Ilan.query.count() == 0


def test_ilana_cikarilmazsa_ilan_olusmaz_fiyat_sifir(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    assert olustur(c, arsa_formu(ilan_fiyat='4.250.000')).status_code == 302
    assert Ilan.query.count() == 0
    assert float(ArsaAnaliz.query.one().fiyat) == 0


def test_kontak_ara_yalniz_gorunurleri_dondurur(app, kullanicilar):
    kontak(kullanicilar['d1'], 'Ahmet')
    kontak(kullanicilar['d2'], 'Ahmetcan')
    r = istemci(app, kullanicilar['d1']).get('/analysis/kontak-ara?q=ahmet')
    adlar = [k['ad'] for k in r.get_json()]
    assert adlar == ['Ahmet Yılmaz']
    assert set(r.get_json()[0]) == {'id', 'ad', 'telefon'}
    r = istemci(app, kullanicilar['broker']).get('/analysis/kontak-ara?q=ahmet')
    assert sorted(k['ad'] for k in r.get_json()) == ['Ahmet Yılmaz', 'Ahmetcan Yılmaz']
    r = istemci(app, kullanicilar['d1']).get('/analysis/kontak-ara?q=5551112')
    assert len(r.get_json()) == 1


def test_baskasinin_gayrimenkulu_duzenlenemez(app, kullanicilar):
    c1 = istemci(app, kullanicilar['d1'])
    olustur(c1, arsa_formu())
    g = ArsaAnaliz.query.one()
    c2 = istemci(app, kullanicilar['d2'])
    assert c2.get(f'/analysis/{g.id}/edit').status_code == 404
    assert c2.post(f'/analysis/{g.id}/edit', data=arsa_formu(mahalle='Değişti')).status_code == 404
    # Ekibinin broker'ı düzenleyebilir
    cb = istemci(app, kullanicilar['broker'])
    assert cb.get(f'/analysis/{g.id}/edit').status_code == 200
    r = cb.post(f'/analysis/{g.id}/edit', data=arsa_formu(mahalle='Güzelyalı'))
    assert r.status_code == 302
    db.session.expire_all()
    g = db.session.get(ArsaAnaliz, g.id)
    assert g.mahalle == 'Güzelyalı' and g.user_id == kullanicilar['d1']


def test_kopyalama_yeni_alanlari_alir_sahip_ve_ilan_almaz(app, kullanicilar):
    c = istemci(app, kullanicilar['d1'])
    k = kontak(kullanicilar['d1'])
    olustur(c, temel('konut', alt_tur='daire', brut_m2='120', oda_sayisi='3+1', oz_ic=['Asansör'],
                     ilana_cikar='1', ilan_teklif_tipi='satilik', ilan_fiyat='1.000.000',
                     **{'sahip_contact_id[]': [str(k)], 'sahip_hisse[]': ['']}))
    g = ArsaAnaliz.query.one()
    r = c.post(f'/analysis/{g.id}/duplicate')
    assert r.status_code == 200 and r.get_json()['success']
    kopya = db.session.get(ArsaAnaliz, r.get_json()['new_id'])
    assert kopya.tur == 'konut' and kopya.oda_sayisi == '3+1' and kopya.ozellikler['ic'] == ['Asansör']
    assert kopya.sahiplikler == [] and kopya.ilan_baglari == []
    assert istemci(app, kullanicilar['d2']).post(f'/analysis/{g.id}/duplicate').status_code == 404


def test_yatirimci_alanlari_formda_yok(app, kullanicilar):
    html = istemci(app, kullanicilar['d1']).get('/analysis/new').get_data(as_text=True)
    assert 'Gayrimenkul türü' in html
    for metin in ('Alım Tarihi', 'Maliyet', 'Elde Tutma'):
        assert metin not in html
    from modules.gayrimenkul_sabitleri import OZELLIK_BASLIKLARI
    for baslik in OZELLIK_BASLIKLARI.values():
        assert baslik in html


def test_eski_form_adresi_yeni_forma_yonlenir(app, kullanicilar):
    r = istemci(app, kullanicilar['d1']).get('/analysis-form')
    assert r.status_code == 302 and r.headers['Location'].endswith('/analysis/new')
