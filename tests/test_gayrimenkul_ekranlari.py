"""Gayrimenkul listesi, detayı ve menü (spec §5.3, §5.4)."""
from models import db
from models.arsa_models import AnalizMedya, ArsaAnaliz
from models.crm_models import Contact
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanGayrimenkul
from conftest import giris


def istemci(app, user_id):
    return giris(app.test_client(), user_id)


def arsa(user_id, mahalle='Kepez', **kw):
    v = dict(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle=mahalle, ada='213', parsel='2',
             metrekare=800, imar_durumu='Konut', kaks=1.5, fiyat=0, tur='arsa')
    v.update(kw)
    g = ArsaAnaliz(**v)
    db.session.add(g)
    db.session.commit()
    return g


def daire(user_id, mahalle='Barbaros', **kw):
    v = dict(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle=mahalle, metrekare=120, brut_m2=120,
             net_m2=105, oda_sayisi='3+1', bulundugu_kat='4', isinma='Kombi (doğalgaz)', fiyat=0, tur='konut',
             alt_tur='daire')
    v.update(kw)
    g = ArsaAnaliz(**v)
    db.session.add(g)
    db.session.commit()
    return g


def ilan(g, kod='ILN-2026-0007', durum='pazarlamada', teklif_tipi='satilik', fiyat=1_250_000, **kw):
    i = Ilan(kod=kod, user_id=g.user_id, sorumlu_user_id=g.user_id, teklif_tipi=teklif_tipi, durum=durum,
             fiyat=fiyat, **kw)
    i.baglar.append(IlanGayrimenkul(gayrimenkul=g, ana_kayit=True, sira=1))
    db.session.add(i)
    db.session.commit()
    return i


def html(r):
    assert r.status_code == 200, r.status_code
    return r.get_data(as_text=True)


# ---------------------------------------------------------------- özet

def test_ozet_konut_ve_arsa(db_session, kullanicilar):
    assert daire(kullanicilar['d1']).ozet == '3+1 · 120 m² · 4. kat'
    assert arsa(kullanicilar['d1']).ozet == '800 m² · Konut imarlı · KAKS 1,5'
    assert arsa(kullanicilar['d1'], metrekare=12000, imar_durumu=None, kaks=None, tur='tarla').ozet == '12.000 m²'


# ---------------------------------------------------------------- liste

def test_liste_tur_filtresi(app, kullanicilar):
    a = arsa(kullanicilar['d1'], baslik='Yatırımlık arsa')
    d = daire(kullanicilar['d1'], baslik='Deniz manzaralı daire')
    c = istemci(app, kullanicilar['d1'])

    hepsi = html(c.get('/analysis/list'))
    assert 'Yatırımlık arsa' in hepsi and 'Deniz manzaralı daire' in hepsi
    assert '3+1 · 120 m² · 4. kat' in hepsi
    assert '800 m² · Konut imarlı · KAKS 1,5' in hepsi
    assert f'/analysis/{a.id}"' in hepsi and f'/analysis/{d.id}"' in hepsi

    konut = html(c.get('/analysis/list?tur=konut'))
    assert 'Deniz manzaralı daire' in konut
    assert 'Yatırımlık arsa' not in konut


def test_liste_aktif_ilan_filtresi(app, kullanicilar):
    a = arsa(kullanicilar['d1'], baslik='İlandaki arsa')
    arsa(kullanicilar['d1'], baslik='Boştaki arsa', mahalle='Kepez2')
    ilan(a)
    c = istemci(app, kullanicilar['d1'])

    var = html(c.get('/analysis/list?aktif_ilan=var'))
    assert 'İlandaki arsa' in var and 'Boştaki arsa' not in var
    assert 'Satılık' in var and '1.250.000 TL' in var and '₺' not in var

    yok = html(c.get('/analysis/list?aktif_ilan=yok'))
    assert 'Boştaki arsa' in yok and 'İlandaki arsa' not in yok


def test_liste_arama_ve_konum_filtresi(app, kullanicilar):
    arsa(kullanicilar['d1'], baslik='Kepez arsası', ada='999')
    daire(kullanicilar['d1'], baslik='Lapseki dairesi', ilce='Lapseki')
    c = istemci(app, kullanicilar['d1'])

    sonuc = html(c.get('/analysis/list?q=999'))
    assert 'Kepez arsası' in sonuc and 'Lapseki dairesi' not in sonuc

    sonuc = html(c.get('/analysis/list?ilce=Lapseki'))
    assert 'Lapseki dairesi' in sonuc and 'Kepez arsası' not in sonuc

    sonuc = html(c.get('/analysis/list?q=lapseki'))
    assert 'Lapseki dairesi' in sonuc and 'Kepez arsası' not in sonuc


def test_broker_ekibin_kayitlarini_listeler_danisman_digerini_goremez(app, kullanicilar):
    arsa(kullanicilar['d1'], baslik='D1 kaydı')
    arsa(kullanicilar['d2'], baslik='D2 kaydı')
    arsa(kullanicilar['dx'], baslik='DX kaydı')

    broker = html(istemci(app, kullanicilar['broker']).get('/analysis/list'))
    assert 'D1 kaydı' in broker and 'D2 kaydı' in broker and 'DX kaydı' not in broker

    d1 = html(istemci(app, kullanicilar['d1']).get('/analysis/list'))
    assert 'D1 kaydı' in d1 and 'D2 kaydı' not in d1 and 'DX kaydı' not in d1


# ---------------------------------------------------------------- detay

def test_detay_konut_alanlari_ve_ilanlar(app, kullanicilar):
    d = daire(kullanicilar['d1'], ozellikler={'ic': ['Asansör'], 'altyapi': ['dogalgaz']},
              swot_analizi='{"strengths": ["Deniz manzarası"]}')
    i = ilan(d, durum='anlasildi')
    kisi = Contact(user_id=kullanicilar['d1'], first_name='Ayşe', last_name='Kaya', phone='5551112233')
    db.session.add(kisi)
    db.session.flush()
    db.session.add(GayrimenkulSahibi(gayrimenkul_id=d.id, contact_id=kisi.id, hisse='1/2', irtibat=True))
    db.session.commit()

    sayfa = html(istemci(app, kullanicilar['d1']).get(f'/analysis/{d.id}'))
    assert '3+1' in sayfa
    assert 'Kombi (doğalgaz)' in sayfa
    assert 'Asansör' in sayfa and 'Doğalgaz' in sayfa
    assert 'Deniz manzarası' in sayfa
    assert 'ILN-2026-0007' in sayfa and f'/ilanlar/{i.id}' in sayfa
    assert 'Anlaşıldı' in sayfa
    assert f'/ilanlar/yeni?gayrimenkul={d.id}' in sayfa
    assert 'Ayşe Kaya' in sayfa and '1/2' in sayfa and f'/crm/contact/{kisi.id}' in sayfa
    assert 'Birim Maliyet' not in sayfa
    assert 'Güncel Değer' not in sayfa and 'Değer Artışı' not in sayfa
    # Yalnız dolu alanlar: arsa alanları konutta görünmez
    assert 'KAKS' not in sayfa and 'Ada' not in sayfa


def test_detay_baskasina_404(app, kullanicilar):
    g = arsa(kullanicilar['d1'])
    assert istemci(app, kullanicilar['d2']).get(f'/analysis/{g.id}').status_code == 404
    assert istemci(app, kullanicilar['dx']).get(f'/analysis/{g.id}').status_code == 404
    assert istemci(app, kullanicilar['broker']).get(f'/analysis/{g.id}').status_code == 200
    assert istemci(app, kullanicilar['sa']).get(f'/analysis/{g.id}').status_code == 200


def test_eski_detay_ucu_yok(app):
    adlar = {r.endpoint for r in app.url_map.iter_rules()}
    assert 'analysis.analiz_detay' not in adlar and 'analysis.list_analyses' not in adlar
    assert 'analysis.view_analysis' in adlar and 'analysis.analizler' in adlar


# ---------------------------------------------------------------- silme ve medya yetkisi

def test_broker_ekibin_kaydini_silebilir_baskasi_silemez(app, kullanicilar):
    g = arsa(kullanicilar['d1'])
    g_id = g.id
    assert istemci(app, kullanicilar['d2']).post(f'/analysis/{g_id}/delete').status_code == 404
    assert istemci(app, kullanicilar['d2']).post(f'/analysis/delete/{g_id}').status_code == 404
    assert db.session.get(ArsaAnaliz, g_id) is not None

    r = istemci(app, kullanicilar['broker']).post(f'/analysis/{g_id}/delete')
    assert r.status_code == 200 and r.get_json()['success'] is True
    db.session.expire_all()
    assert db.session.get(ArsaAnaliz, g_id) is None


def test_analiz_sil_formu_listeye_doner(app, kullanicilar):
    g = arsa(kullanicilar['d1'])
    g_id = g.id
    r = istemci(app, kullanicilar['broker']).post(f'/analysis/delete/{g_id}')
    assert r.status_code == 302 and r.headers['Location'].endswith('/analysis/list')
    db.session.expire_all()
    assert db.session.get(ArsaAnaliz, g_id) is None


def test_medya_yetkisi(app, kullanicilar, tmp_path):
    import io
    app.config['UPLOAD_FOLDER'] = str(tmp_path)
    g = arsa(kullanicilar['d1'])
    veri = lambda: {'medya': (io.BytesIO(b'\x89PNG'), 'foto.png')}  # noqa: E731

    r = istemci(app, kullanicilar['d2']).post(f'/analysis/{g.id}/media_upload', data=veri(),
                                              content_type='multipart/form-data')
    assert r.status_code == 404
    r = istemci(app, kullanicilar['broker']).post(f'/analysis/{g.id}/media_upload', data=veri(),
                                                  content_type='multipart/form-data')
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/analysis/{g.id}')
    medya = AnalizMedya.query.filter_by(analiz_id=g.id).one()

    assert istemci(app, kullanicilar['d2']).post(
        f'/analysis/{g.id}/media_delete/{medya.id}').status_code == 404
    r = istemci(app, kullanicilar['d1']).post(f'/analysis/{g.id}/media_delete/{medya.id}')
    assert r.status_code == 302
    assert AnalizMedya.query.count() == 0


# ---------------------------------------------------------------- menü

def test_menude_gayrimenkuller_ve_ilanlar(app, kullanicilar):
    sayfa = html(istemci(app, kullanicilar['d1']).get('/index'))
    assert 'Gayrimenkuller' in sayfa
    assert 'Analizlerim' not in sayfa
    assert 'İlanlar' in sayfa and '/ilanlar/' in sayfa


def test_detay_para_tr_currency_ve_gorunmeyen_ilan_linksiz(app, kullanicilar):
    d = daire(kullanicilar['d1'], aidat=1500)
    gorunur = ilan(d, kod='ILN-2026-0001', durum='anlasildi')
    baskasi = Ilan(kod='ILN-2026-0002', user_id=kullanicilar['dx'], sorumlu_user_id=kullanicilar['dx'],
                   teklif_tipi='kiralik', durum='geri_cekildi', kira=15000)
    baskasi.baglar.append(IlanGayrimenkul(gayrimenkul=d, ana_kayit=True, sira=1))
    db.session.add(baskasi)
    db.session.commit()

    sayfa = html(istemci(app, kullanicilar['d1']).get(f'/analysis/{d.id}'))
    assert '1.500 TL' in sayfa and '₺' not in sayfa
    assert f'/ilanlar/{gorunur.id}"' in sayfa
    assert 'ILN-2026-0002' in sayfa and f'/ilanlar/{baskasi.id}"' not in sayfa
