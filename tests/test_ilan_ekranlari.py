"""İlan ekranları: liste, form, detay, durum, silme (spec §5.2–5.4)."""
from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact, Deal
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanGayrimenkul
from models.user_models import Portfolio, portfolio_ilanlar
from conftest import giris


def istemci(app, user_id):
    return giris(app.test_client(), user_id)


def html(r):
    assert r.status_code == 200, r.status_code
    return r.get_data(as_text=True)


def arsa(user_id, parsel='2', metrekare=800, kaks=1.5, **kw):
    v = dict(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='213', parsel=parsel,
             metrekare=metrekare, kaks=kaks, imar_durumu='Konut', fiyat=0, tur='arsa')
    v.update(kw)
    g = ArsaAnaliz(**v)
    db.session.add(g)
    db.session.commit()
    return g


def daire(user_id, **kw):
    v = dict(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle='Barbaros', metrekare=120, brut_m2=120,
             oda_sayisi='3+1', bulundugu_kat='4', fiyat=0, tur='konut', alt_tur='daire')
    v.update(kw)
    g = ArsaAnaliz(**v)
    db.session.add(g)
    db.session.commit()
    return g


def ilan(gler, kod='ILN-2026-0001', durum='pazarlamada', teklif_tipi='satilik', user_id=None, **kw):
    user_id = user_id or gler[0].user_id
    i = Ilan(kod=kod, baslik=kw.pop('baslik', kod), user_id=user_id, sorumlu_user_id=kw.pop('sorumlu', user_id),
             teklif_tipi=teklif_tipi, durum=durum, **kw)
    for sira, g in enumerate(gler, start=1):
        i.baglar.append(IlanGayrimenkul(gayrimenkul=g, ana_kayit=(sira == 1), sira=sira))
    db.session.add(i)
    db.session.commit()
    return i


def form(gler, emsaller=(), **kw):
    v = {'baslik': '', 'aciklama': '', 'teklif_tipi': 'satilik', 'durum': 'pazarlamada',
         'gayrimenkul_id[]': [str(g.id) for g in gler], 'parsel_fiyati[]': ['' for _ in gler],
         'ana_gayrimenkul_id': str(gler[0].id)}
    anahtarlar = ('konum', 'm2', 'fiyat', 'pay', 'link', 'not')
    for a in anahtarlar:
        v[f'emsal_{a}[]'] = [str(e.get(a, '')) for e in emsaller]
    v.update(kw)
    return v


def flashlar(c):
    with c.session_transaction() as s:
        return ' '.join(m for _, m in s.get('_flashes', []))


# ---------------------------------------------------------------- uçtan uca

def test_kat_karsiligi_ilani_uctan_uca(app, kullanicilar):
    br = kullanicilar['broker']
    hasan = Contact(user_id=br, first_name='Hasan', last_name='Yılmaz', phone='05551112233')
    db.session.add(hasan)
    db.session.commit()
    gler = [arsa(br, parsel=str(p), metrekare=m2) for p, m2 in ((2, 800), (3, 750), (4, 900), (5, 750))]
    for g in gler:
        db.session.add(GayrimenkulSahibi(gayrimenkul_id=g.id, contact_id=hasan.id, hisse='1/2'))
    db.session.commit()
    c = istemci(app, br)

    r = c.get(f'/ilanlar/sahip/{hasan.id}/gayrimenkuller')
    assert r.status_code == 200
    liste = r.get_json()
    assert [x['id'] for x in liste] == [g.id for g in gler]
    assert set(liste[0]) == {'id', 'baslik', 'ozet', 'm2', 'kaks', 'aktif_ilan_kodu'}
    assert liste[0]['m2'] == 800 and liste[0]['kaks'] == 1.5 and liste[0]['aktif_ilan_kodu'] is None

    # form sahip ön seçimiyle açılır, sahibin gayrimenkulleri listelenir
    sayfa = html(c.get(f'/ilanlar/yeni?sahip={hasan.id}'))
    assert 'Hasan Yılmaz' in sayfa and gler[3].baslik_metni in sayfa

    r = c.post('/ilanlar/yeni', data=form(
        gler, emsaller=[{'konum': 'Kepez A', 'pay': '40'}, {'konum': 'Kepez B', 'pay': '50'}],
        teklif_tipi='kat_karsiligi', sahip_payi_yuzde='50', ek_nakit='2.000.000', teslim_suresi_ay='24',
        teminat_turu='Banka teminat mektubu', tevhid_durumu='yapilacak', ana_gayrimenkul_id=str(gler[2].id)))
    i = Ilan.query.one()
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/ilanlar/{i.id}')
    assert i.kod.startswith('ILN-') and float(i.ek_nakit) == 2_000_000 and i.teslim_suresi_ay == 24
    assert i.ana_gayrimenkul.id == gler[2].id and len(i.emsaller) == 2

    sayfa = html(c.get(f'/ilanlar/{i.id}'))
    for metin in ('ILN-', '4 parsel', '3.200', '4.800', '2.400', '%45', 'Talep bölge ortalamasının üstünde',
                  'Banka teminat mektubu', '2.000.000 TL', 'Yapılacak', 'Hasan Yılmaz', 'Kepez A'):
        assert metin in sayfa, metin
    assert '₺' not in sayfa


def test_satilik_ilan_emsal_karsilastirma(app, kullanicilar):
    d = daire(kullanicilar['d1'])
    c = istemci(app, kullanicilar['d1'])
    r = c.post('/ilanlar/yeni', data=form([d], fiyat='1.950.000', emsaller=[
        {'konum': 'Barbaros 1', 'm2': '100', 'fiyat': '2.000.000'},
        {'konum': 'Barbaros 2', 'm2': '300', 'fiyat': '4.500.000', 'link': 'https://ornek.com/1'},
        {'konum': 'Fiyatsız emsal', 'link': 'javascript:alert(1)'}]))
    assert r.status_code == 302
    i = Ilan.query.one()
    sayfa = html(c.get(f'/ilanlar/{i.id}'))
    assert '16.250' in sayfa and 'Piyasa seviyesinde' in sayfa and '1.950.000 TL' in sayfa
    assert 'https://ornek.com/1' in sayfa and '2 emsalden' in sayfa
    assert 'Fiyatsız emsal' in sayfa and 'href="javascript' not in sayfa


def test_kiralik_ilan(app, kullanicilar):
    d = daire(kullanicilar['d1'])
    c = istemci(app, kullanicilar['d1'])
    r = c.post('/ilanlar/yeni', data=form([d], teklif_tipi='kiralik', kira='30.000', depozito='60.000',
                                         fiyat='999'))
    assert r.status_code == 302
    i = Ilan.query.one()
    assert float(i.kira) == 30_000 and i.fiyat is None
    sayfa = html(c.get(f'/ilanlar/{i.id}'))
    assert '30.000 TL' in sayfa and '60.000 TL' in sayfa and '₺' not in sayfa


def test_hata_formu_yeniden_gosterir(app, kullanicilar):
    d = daire(kullanicilar['d1'])
    c = istemci(app, kullanicilar['d1'])
    sayfa = html(c.post('/ilanlar/yeni', data=form([d], baslik='Hatalı ilan', emsaller=[{'konum': 'E1'}])))
    assert 'Satılık ilanda fiyat zorunludur.' in sayfa
    assert 'Hatalı ilan' in sayfa and 'E1' in sayfa and d.baslik_metni in sayfa
    assert Ilan.query.count() == 0


def test_yeni_gayrimenkul_on_secimi(app, kullanicilar):
    d = daire(kullanicilar['d1'], baslik='Seçili daire')
    baskasi = daire(kullanicilar['dx'], baslik='Görünmeyen daire')
    sayfa = html(istemci(app, kullanicilar['d1']).get(
        f'/ilanlar/yeni?gayrimenkul={d.id}&gayrimenkul={baskasi.id}'))
    assert 'Seçili daire' in sayfa and 'Görünmeyen daire' not in sayfa
    assert f'name="gayrimenkul_id[]" value="{d.id}" checked' in sayfa


def test_kod_cakismasinda_yeniden_dener(app, kullanicilar, monkeypatch):
    from modules import ilan_servis
    d1 = daire(kullanicilar['d1'])
    d2 = daire(kullanicilar['d1'], mahalle='Esenler')
    mevcut = ilan([d1], kod='ILN-2026-0005', durum='hazirlaniyor', fiyat=1)
    gercek = ilan_servis.yeni_ilan_kodu
    cagri = []

    def sahte(yil=None):
        cagri.append(1)
        return mevcut.kod if len(cagri) == 1 else gercek(yil)
    monkeypatch.setattr(ilan_servis, 'yeni_ilan_kodu', sahte)
    r = istemci(app, kullanicilar['d1']).post('/ilanlar/yeni', data=form([d2], fiyat='1.000.000'))
    assert r.status_code == 302 and len(cagri) == 2
    assert Ilan.query.count() == 2


# ---------------------------------------------------------------- durum

def test_durum_degisikligi_cakisma(app, kullanicilar):
    g1 = arsa(kullanicilar['d1'])
    a = ilan([g1], kod='ILN-2026-0001', durum='pazarlamada', fiyat=1)
    b = ilan([g1], kod='ILN-2026-0002', durum='hazirlaniyor', fiyat=1)
    c = istemci(app, kullanicilar['d1'])
    r = c.post(f'/ilanlar/{b.id}/durum', data={'durum': 'pazarlamada'})
    assert r.status_code == 302
    assert a.kod in flashlar(c)
    db.session.expire_all()
    assert db.session.get(Ilan, b.id).durum == 'hazirlaniyor'

    c.post(f'/ilanlar/{b.id}/durum', data={'durum': 'geri_cekildi'})
    db.session.expire_all()
    assert db.session.get(Ilan, b.id).durum == 'geri_cekildi'


# ---------------------------------------------------------------- uyarılar

def test_kakssiz_parsel_uyarisi(app, kullanicilar):
    g1 = arsa(kullanicilar['d1'], baslik='Kepez parsel A')
    g2 = arsa(kullanicilar['d1'], parsel='3', kaks=None, baslik='Kepez parsel B')
    i = ilan([g1, g2], teklif_tipi='kat_karsiligi', sahip_payi_yuzde=40)
    sayfa = html(istemci(app, kullanicilar['d1']).get(f'/ilanlar/{i.id}'))
    assert 'KAKS bilgisi olmayan parseller hesaba katılmadı' in sayfa and 'Kepez parsel B' in sayfa


def test_emsal_yoksa_elle_bolge_fiyati(app, kullanicilar):
    d = daire(kullanicilar['d1'])
    c = istemci(app, kullanicilar['d1'])
    c.post('/ilanlar/yeni', data=form([d], fiyat='2.000.000', bolge_m2_fiyat_elle='18.000'))
    i = Ilan.query.one()
    assert float(i.bolge_m2_fiyat_elle) == 18_000
    sayfa = html(c.get(f'/ilanlar/{i.id}'))
    assert '18.000' in sayfa and 'elle girildi' in sayfa


# ---------------------------------------------------------------- liste

def test_liste_filtreleri(app, kullanicilar):
    k = kullanicilar
    g1, g2, g3 = arsa(k['d1']), daire(k['d1']), daire(k['d1'], mahalle='Esenler')
    g4 = arsa(k['d1'], parsel='9')
    ilan([g1, g4], kod='ILN-2026-0001', baslik='Kat ilanı', teklif_tipi='kat_karsiligi', sahip_payi_yuzde=50)
    ilan([g2], kod='ILN-2026-0002', baslik='Kiralık ilan', teklif_tipi='kiralik', kira=30_000)
    ilan([g3], kod='ILN-2026-0003', baslik='Satılık ilan', fiyat=4_250_000, durum='geri_cekildi',
         sorumlu=k['broker'])
    c = istemci(app, k['broker'])

    hepsi = html(c.get('/ilanlar/'))
    assert 'Kat ilanı' in hepsi and 'Kiralık ilan' in hepsi and 'Satılık ilan' in hepsi
    assert 'Kat karşılığı · 2 parsel · 1.600 m² · %50' in hepsi
    assert 'Satılık · Daire · 3+1 · 4.250.000 TL' in hepsi and '₺' not in hepsi

    kiralik = html(c.get('/ilanlar/?teklif_tipi=kiralik'))
    assert 'Kiralık ilan' in kiralik and 'Kat ilanı' not in kiralik and 'Satılık ilan' not in kiralik

    geri = html(c.get('/ilanlar/?durum=geri_cekildi'))
    assert 'Satılık ilan' in geri and 'Kiralık ilan' not in geri

    konut = html(c.get('/ilanlar/?tur=konut'))
    assert 'Kiralık ilan' in konut and 'Satılık ilan' in konut and 'Kat ilanı' not in konut

    aralik = html(c.get('/ilanlar/?fiyat_min=20.000&fiyat_max=100.000'))
    assert 'Kiralık ilan' in aralik and 'Satılık ilan' not in aralik and 'Kat ilanı' not in aralik

    sorumlu = html(c.get(f'/ilanlar/?sorumlu={k["broker"]}'))
    assert 'Satılık ilan' in sorumlu and 'Kiralık ilan' not in sorumlu


# ---------------------------------------------------------------- yetki

def test_ilan_yetki(app, kullanicilar):
    k = kullanicilar
    g = daire(k['d1'])
    i = ilan([g], fiyat=1_000_000, baslik='D1 ilanı')
    assert istemci(app, k['d2']).get(f'/ilanlar/{i.id}').status_code == 404
    assert istemci(app, k['d2']).get(f'/ilanlar/{i.id}/duzenle').status_code == 404
    assert 'D1 ilanı' not in html(istemci(app, k['d2']).get('/ilanlar/'))
    assert 'D1 ilanı' in html(istemci(app, k['broker']).get(f'/ilanlar/{i.id}'))

    d1 = istemci(app, k['d1'])
    sayfa = html(d1.get(f'/ilanlar/{i.id}/duzenle'))
    assert 'D1 ilanı' in sayfa and '1.000.000' in sayfa
    r = d1.post(f'/ilanlar/{i.id}/duzenle', data=form([g], baslik='Yeni başlık', fiyat='1.100.000'))
    assert r.status_code == 302
    db.session.expire_all()
    i = db.session.get(Ilan, i.id)
    assert i.baslik == 'Yeni başlık' and float(i.fiyat) == 1_100_000 and i.kod == 'ILN-2026-0001'

    # sahip_gayrimenkulleri: görünmeyen kontak 404
    kisi = Contact(user_id=k['d1'], first_name='Ali', last_name='Veli')
    db.session.add(kisi)
    db.session.commit()
    assert istemci(app, k['d2']).get(f'/ilanlar/sahip/{kisi.id}/gayrimenkuller').status_code == 404


def test_yalniz_sorumlu_silemez(app, kullanicilar):
    k = kullanicilar
    g = daire(k['broker'])
    i = ilan([g], fiyat=1, sorumlu=k['d1'])
    assert istemci(app, k['d1']).post(f'/ilanlar/{i.id}/sil').status_code == 403
    assert Ilan.query.count() == 1
    assert istemci(app, k['broker']).post(f'/ilanlar/{i.id}/sil').status_code == 302
    assert Ilan.query.count() == 0


def test_ilan_silinince_gayrimenkul_kalir(app, kullanicilar):
    k = kullanicilar
    g = daire(k['d1'])
    i = ilan([g], fiyat=1)
    p = Portfolio(user_id=k['d1'], title='Portföy')
    kisi = Contact(user_id=k['d1'], first_name='Alıcı', last_name='Kişi')
    db.session.add(kisi)
    db.session.flush()
    deal = Deal(user_id=k['d1'], contact_id=kisi.id, title='Fırsat', ilan_id=i.id)
    db.session.add_all([p, deal])
    db.session.commit()
    db.session.execute(portfolio_ilanlar.insert().values(portfolio_id=p.id, ilan_id=i.id))
    db.session.commit()
    ilan_id, g_id, deal_id = i.id, g.id, deal.id

    c = istemci(app, k['d1'])
    r = c.post(f'/ilanlar/{ilan_id}/sil')
    assert r.status_code == 302 and r.headers['Location'].endswith('/ilanlar/')
    db.session.expire_all()
    assert db.session.get(Ilan, ilan_id) is None
    assert db.session.get(ArsaAnaliz, g_id) is not None
    assert db.session.get(Deal, deal_id).ilan_id is None
    assert db.session.execute(portfolio_ilanlar.select()).fetchall() == []
