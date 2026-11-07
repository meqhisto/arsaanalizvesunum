"""CRM bağlantıları ve portföyler (spec §3.6, §5.3 CRM müşteri detayı, §5.5)."""
from models import db
from models.crm_models import Contact, Deal
from models.ilan_models import GayrimenkulSahibi
from models.user_models import Portfolio
from conftest import giris
from test_ilan_ekranlari import arsa, daire, flashlar, html, ilan


def istemci(app, user_id):
    return giris(app.test_client(), user_id)


def kisi(user_id, ad='Hasan', soyad='Yılmaz'):
    c = Contact(user_id=user_id, first_name=ad, last_name=soyad, phone='05551112233')
    db.session.add(c)
    db.session.commit()
    return c


def portfoy(user_id, baslik='Kepez Portföyü', **kw):
    p = Portfolio(user_id=user_id, title=baslik, visibility=kw.pop('visibility', 'private'), **kw)
    db.session.add(p)
    db.session.commit()
    return p


# ---------------------------------------------------------------- kontak detayı

def test_kontak_detayinda_gayrimenkulleri(app, kullanicilar):
    br = kullanicilar['broker']
    hasan = kisi(br)
    gler = [arsa(br, parsel=str(p)) for p in (2, 3, 4, 5)]
    for g in gler:
        db.session.add(GayrimenkulSahibi(gayrimenkul_id=g.id, contact_id=hasan.id, hisse='1/2'))
    db.session.commit()
    i = ilan([gler[0]], kod='ILN-2026-0007', fiyat=1_000_000)

    s = html(istemci(app, br).get(f'/crm/contact/{hasan.id}'))
    assert 'Gayrimenkulleri' in s
    for p in (2, 3, 4, 5):
        assert f'Parsel {p}' in s
    assert s.count('1/2') >= 4
    assert 'ILN-2026-0007' in s and f'/ilanlar/{i.id}' in s
    assert 'Seçilenlerle yeni ilan' in s
    assert f'sahip={hasan.id}' in s
    for g in gler:
        assert f'name="gayrimenkul" value="{g.id}"' in s


def test_kontak_detayi_gorunmeyen_gayrimenkulu_listelemez(app, kullanicilar):
    k = kullanicilar
    # d1'in müşterisi, görünmez bir kişinin (dx) gayrimenkulünün sahibi
    c = kisi(k['d1'])
    gizli = arsa(k['dx'], parsel='99')
    gorunur = arsa(k['d1'], parsel='7')
    db.session.add_all([GayrimenkulSahibi(gayrimenkul_id=gizli.id, contact_id=c.id, hisse='1/3'),
                        GayrimenkulSahibi(gayrimenkul_id=gorunur.id, contact_id=c.id, hisse='Tam')])
    db.session.commit()
    s = html(istemci(app, k['d1']).get(f'/crm/contact/{c.id}'))
    assert 'Parsel 7' in s and 'Parsel 99' not in s
    assert f'name="gayrimenkul" value="{gorunur.id}"' in s
    assert f'name="gayrimenkul" value="{gizli.id}"' not in s


# ---------------------------------------------------------------- fırsat ↔ ilan

def test_firsata_ilan_baglanir(app, kullanicilar):
    br = kullanicilar['broker']
    c = kisi(br)
    i = ilan([daire(br)], kod='ILN-2026-0011', baslik='Barbaros 3+1')
    istem = istemci(app, br)
    s = html(istem.get('/crm/deal/new'))
    assert 'ILN-2026-0011 · Barbaros 3+1' in s

    r = istem.post('/crm/deal/new', data={'title': 'Barbaros alıcısı', 'contact_id': str(c.id),
                                          'value': '0', 'stage': 'İlk İletişim', 'ilan_id': str(i.id)})
    assert r.status_code == 302
    d = Deal.query.one()
    assert d.ilan_id == i.id

    detay = html(istem.get(f'/crm/deal/{d.id}'))
    assert 'ILN-2026-0011' in detay and f'/ilanlar/{i.id}' in detay

    ilan_s = html(istem.get(f'/ilanlar/{i.id}'))
    assert 'Barbaros alıcısı' in ilan_s and f'/crm/deal/{d.id}' in ilan_s

    # Düzenlemede ilan kaldırılabilir
    r = istem.post(f'/crm/deal/{d.id}/edit', data={'title': 'Barbaros alıcısı', 'contact_id': str(c.id),
                                                   'value': '0', 'stage': 'İlk İletişim', 'ilan_id': ''})
    assert r.status_code == 302
    db.session.expire_all()
    assert db.session.get(Deal, d.id).ilan_id is None


def test_firsata_gorunmeyen_ilan_baglanamaz(app, kullanicilar):
    k = kullanicilar
    c = kisi(k['d1'])
    yabanci = ilan([daire(k['dx'])], kod='ILN-2026-0021')
    istem = istemci(app, k['d1'])
    assert 'ILN-2026-0021' not in html(istem.get('/crm/deal/new'))
    veri = {'title': 'Sızma', 'contact_id': str(c.id), 'value': '0', 'stage': 'İlk İletişim'}
    for deger in (str(yabanci.id), '999999', 'abc'):
        r = istem.post('/crm/deal/new', data=dict(veri, ilan_id=deger))
        assert r.status_code == 400
        assert 'Seçilen ilan bulunamadı.' in r.get_data(as_text=True)
    assert Deal.query.count() == 0

    # Düzenlemede de reddedilir
    d = Deal(user_id=k['d1'], contact_id=c.id, title='Mevcut')
    db.session.add(d)
    db.session.commit()
    r = istem.post(f'/crm/deal/{d.id}/edit', data=dict(veri, title='Mevcut', ilan_id=str(yabanci.id)))
    assert r.status_code == 400
    assert 'Seçilen ilan bulunamadı.' in r.get_data(as_text=True)
    db.session.expire_all()
    assert db.session.get(Deal, d.id).ilan_id is None


def test_ilan_detayinda_yalniz_kendi_firsati_linkli(app, kullanicilar):
    k = kullanicilar
    i = ilan([daire(k['d1'])], fiyat=1, sorumlu=k['d1'])
    deals = {}
    for uid, baslik in ((k['broker'], 'BR fırsatı'), (k['d1'], 'D1 fırsatı')):
        c = kisi(uid, soyad=baslik)
        d = Deal(user_id=uid, contact_id=c.id, title=baslik, ilan_id=i.id)
        db.session.add(d)
        db.session.commit()
        deals[uid] = d.id
    s = html(istemci(app, k['broker']).get(f'/ilanlar/{i.id}'))
    assert 'D1 fırsatı' in s and 'BR fırsatı' in s
    assert f'/crm/deal/{deals[k["broker"]]}"' in s
    assert f'/crm/deal/{deals[k["d1"]]}"' not in s


# ---------------------------------------------------------------- portföy

def test_portfoye_ilan_eklenir_ve_toplam(app, kullanicilar):
    br = kullanicilar['broker']
    p = portfoy(br)
    satilik = ilan([arsa(br, parsel='2')], kod='ILN-2026-0031', fiyat=4_250_000)
    kiralik = ilan([daire(br)], kod='ILN-2026-0032', teklif_tipi='kiralik', kira=30_000)
    kat = ilan([arsa(br, parsel='3')], kod='ILN-2026-0033', teklif_tipi='kat_karsiligi', sahip_payi_yuzde=50)
    istem = istemci(app, br)
    for x in (satilik, kiralik, kat):
        r = istem.post(f'/portfolio/{p.id}/add', data={'ilan_id': str(x.id)})
        assert r.status_code == 302
    db.session.expire_all()
    assert {x.id for x in db.session.get(Portfolio, p.id).ilanlar} == {satilik.id, kiralik.id, kat.id}

    s = html(istem.get(f'/portfolio/{p.id}'))
    assert '4.250.000' in s and '30.000' in s
    assert 'Maliyet' not in s and '₺' not in s
    for kod in ('ILN-2026-0031', 'ILN-2026-0032', 'ILN-2026-0033'):
        assert kod in s

    from blueprints.portfolio_bp import _portfolio_totals
    t = _portfolio_totals([satilik, kiralik, kat])
    assert t == {'adet': 3, 'toplam_fiyat': 4_250_000, 'aylik_kira': 30_000, 'kat_karsiligi_adet': 1}

    # Aynı ilan ikinci kez eklenmez; çıkarma ilan id'siyle
    istem.post(f'/portfolio/{p.id}/add', data={'ilan_id': str(satilik.id)})
    r = istem.post(f'/portfolio/{p.id}/remove/{satilik.id}')
    assert r.status_code == 302
    db.session.expire_all()
    assert {x.id for x in db.session.get(Portfolio, p.id).ilanlar} == {kiralik.id, kat.id}


def test_portfoye_gorunmeyen_ilan_eklenemez(app, kullanicilar):
    k = kullanicilar
    p = portfoy(k['d1'])
    yabanci = ilan([daire(k['dx'])], kod='ILN-2026-0041')
    r = istemci(app, k['d1']).post(f'/portfolio/{p.id}/add', data={'ilan_id': str(yabanci.id)})
    assert r.status_code == 302
    db.session.expire_all()
    assert db.session.get(Portfolio, p.id).ilanlar.count() == 0
    # Başkasının portföyüne eklenemez
    r = istemci(app, k['d2']).post(f'/portfolio/{p.id}/add', data={'ilan_id': str(yabanci.id)})
    assert r.status_code == 404


def test_eski_analiz_id_ile_portfoye_ekleme(app, kullanicilar):
    br = kullanicilar['broker']
    p = portfoy(br)
    g = arsa(br, parsel='2')
    ilan([g], kod='ILN-2026-0051', durum='geri_cekildi')
    aktif = ilan([g], kod='ILN-2026-0052', durum='pazarlamada')
    g2 = arsa(br, parsel='3')
    eski = ilan([g2], kod='ILN-2026-0053', durum='hazirlaniyor')
    son = ilan([g2], kod='ILN-2026-0054', durum='anlasildi')
    ilansiz = arsa(br, parsel='4')
    istem = istemci(app, br)

    istem.post(f'/portfolio/{p.id}/add', data={'analiz_id': str(g.id)})
    istem.post(f'/portfolio/{p.id}/add', data={'analiz_id': str(g2.id)})
    db.session.expire_all()
    assert {x.id for x in db.session.get(Portfolio, p.id).ilanlar} == {aktif.id, son.id}
    assert eski.id not in {x.id for x in db.session.get(Portfolio, p.id).ilanlar}

    istem.post(f'/portfolio/{p.id}/add', data={'analiz_id': str(ilansiz.id)})
    assert 'ilanı yok' in flashlar(istem)
    db.session.expire_all()
    assert db.session.get(Portfolio, p.id).ilanlar.count() == 2


def test_ilan_detayinda_portfoye_ekle(app, kullanicilar):
    br = kullanicilar['broker']
    p = portfoy(br, baslik='Yatırımcı Seçkisi')
    i = ilan([daire(br)], kod='ILN-2026-0061', fiyat=2_000_000)
    istem = istemci(app, br)
    s = html(istem.get(f'/ilanlar/{i.id}'))
    assert 'Portföye ekle' in s and 'Yatırımcı Seçkisi' in s
    assert f'/portfolio/{p.id}/add' in s or 'portfolio_id' in s
    r = istem.post(f'/portfolio/{p.id}/add', data={'ilan_id': str(i.id), 'geri': 'ilan'})
    assert r.status_code == 302 and f'/ilanlar/{i.id}' in r.headers['Location']
    db.session.expire_all()
    assert [x.id for x in db.session.get(Portfolio, p.id).ilanlar] == [i.id]


def test_portfoy_olusturma_ilan_ile(app, kullanicilar):
    br = kullanicilar['broker']
    i = ilan([daire(br)], kod='ILN-2026-0071', fiyat=2_000_000)
    istem = istemci(app, br)
    s = html(istem.get('/portfolio/create'))
    assert 'ILN-2026-0071' in s
    r = istem.post('/portfolio/create', data={'title': 'Yeni', 'visibility': 'private', 'ilan_ids': [str(i.id)]})
    assert r.status_code == 302
    p = Portfolio.query.one()
    assert [x.id for x in p.ilanlar] == [i.id]
    assert p.analizler.count() == 0
