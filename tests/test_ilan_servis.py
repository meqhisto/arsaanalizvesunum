import pytest

from models import db
from models.arsa_models import ArsaAnaliz
from models.crm_models import Contact, Deal
from models.ilan_models import GayrimenkulSahibi, Ilan, IlanEmsal, IlanGayrimenkul
from models.user_models import Portfolio, User, portfolio_ilanlar
from modules.ilan_servis import (IlanHatasi, cakisan_ilan, gayrimenkul_or_404, gayrimenkul_silinirken,
                                 gorunur_gayrimenkuller, gorunur_ilanlar, gorunur_kontaklar,
                                 gorunur_kullanici_idleri, ilan_kaydet, ilan_or_404, ilan_ozeti,
                                 sahipleri_kaydet, yeni_ilan_kodu)


def kul(uid):
    return db.session.get(User, uid)


def gayrimenkul(user_id, ada='213', parsel='2', metrekare=800, kaks=None, fiyat=1_000_000, mahalle='Kepez'):
    g = ArsaAnaliz(user_id=user_id, il='Çanakkale', ilce='Merkez', mahalle=mahalle, ada=ada, parsel=parsel,
                   metrekare=metrekare, kaks=kaks, fiyat=fiyat, tur='arsa')
    db.session.add(g)
    db.session.commit()
    return g


def ilan_olustur(user_id=None, kod='ILN-2026-0001', durum='hazirlaniyor', gayrimenkuller=(), teklif_tipi='satilik'):
    if user_id is None:
        user_id = db.session.query(User.id).order_by(User.id).first()[0]
    i = Ilan(kod=kod, user_id=user_id, sorumlu_user_id=user_id, teklif_tipi=teklif_tipi, durum=durum,
             fiyat=1_000_000)
    for sira, g in enumerate(gayrimenkuller, start=1):
        i.baglar.append(IlanGayrimenkul(gayrimenkul=g, ana_kayit=(sira == 1), sira=sira))
    db.session.add(i)
    db.session.commit()
    return i


def kontak(user_id, ad='Ali'):
    c = Contact(user_id=user_id, first_name=ad, last_name='Yılmaz')
    db.session.add(c)
    db.session.commit()
    return c


def veri(gayrimenkuller, **kw):
    v = {'baslik': 'Test ilan', 'teklif_tipi': 'satilik', 'durum': 'hazirlaniyor', 'fiyat': 1_000_000,
         'gayrimenkuller': [{'id': g.id, 'parsel_fiyati': None} for g in gayrimenkuller],
         'ana_gayrimenkul_id': None, 'emsaller': []}
    v.update(kw)
    return v


def test_gorunurluk(db_session, kullanicilar):
    k = kullanicilar
    g_d1 = gayrimenkul(k['d1'])
    g_br = gayrimenkul(k['broker'], parsel='3')
    i_d1 = ilan_olustur(k['d1'], 'ILN-2026-0001', gayrimenkuller=[g_d1])
    i_br = ilan_olustur(k['broker'], 'ILN-2026-0002', gayrimenkuller=[g_br])
    c_d1 = kontak(k['d1'])

    assert gorunur_kullanici_idleri(kul(k['sa'])) is None
    assert set(gorunur_kullanici_idleri(kul(k['broker']))) == {k['broker'], k['d1'], k['d2']}
    assert gorunur_kullanici_idleri(kul(k['d1'])) == [k['d1']]

    broker = kul(k['broker'])
    assert {g.id for g in gorunur_gayrimenkuller(broker)} == {g_d1.id, g_br.id}
    assert {i.id for i in gorunur_ilanlar(broker)} == {i_d1.id, i_br.id}
    assert [c.id for c in gorunur_kontaklar(broker)] == [c_d1.id]
    assert gayrimenkul_or_404(g_d1.id, broker).id == g_d1.id
    assert ilan_or_404(i_d1.id, broker).id == i_d1.id

    d1 = kul(k['d1'])
    assert [g.id for g in gorunur_gayrimenkuller(d1)] == [g_d1.id]
    assert [i.id for i in gorunur_ilanlar(d1)] == [i_d1.id]
    from werkzeug.exceptions import NotFound
    with pytest.raises(NotFound):
        gayrimenkul_or_404(g_br.id, d1)
    with pytest.raises(NotFound):
        ilan_or_404(i_br.id, d1)

    dx = kul(k['dx'])
    assert gorunur_gayrimenkuller(dx).count() == 0 and gorunur_ilanlar(dx).count() == 0
    assert gorunur_kontaklar(dx).count() == 0

    sa = kul(k['sa'])
    assert gorunur_gayrimenkuller(sa).count() == 2 and gorunur_ilanlar(sa).count() == 2
    assert gorunur_kontaklar(sa).count() == 1


def test_sorumlu_uzerinden_ilan_gorunur(db_session, kullanicilar):
    k = kullanicilar
    g = gayrimenkul(k['dx'])
    i = ilan_olustur(k['dx'], gayrimenkuller=[g])
    i.sorumlu_user_id = k['d1']; db.session.commit()
    assert [x.id for x in gorunur_ilanlar(kul(k['d1']))] == [i.id]


def test_pasif_kullanici_broker_ekibinde_degil(db_session, kullanicilar):
    k = kullanicilar
    kul(k['d2']).is_active = False; db.session.commit()
    assert set(gorunur_kullanici_idleri(kul(k['broker']))) == {k['broker'], k['d1']}


def test_yeni_ilan_kodu_yil_icinde_artar(db_session, kullanicilar):
    assert yeni_ilan_kodu(2026) == 'ILN-2026-0001'
    ilan_olustur(kullanicilar['broker'], kod='ILN-2026-0007')
    assert yeni_ilan_kodu(2026) == 'ILN-2026-0008' and yeni_ilan_kodu(2027) == 'ILN-2027-0001'


def test_cakisma_aktif_ilan(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g1 = gayrimenkul(br.id)
    ilk = ilan_kaydet(None, br, veri([g1], durum='pazarlamada'))
    db.session.commit()
    assert cakisan_ilan(g1.id, None).id == ilk.id
    assert cakisan_ilan(g1.id, ilk.id) is None

    with pytest.raises(IlanHatasi) as e:
        ilan_kaydet(None, br, veri([g1], durum='pazarlamada'))
    assert ilk.kod in str(e.value) and g1.baslik_metni in str(e.value)
    db.session.rollback()

    ikinci = ilan_kaydet(None, br, veri([g1], durum='hazirlaniyor'))
    db.session.commit()
    with pytest.raises(IlanHatasi):
        ilan_kaydet(ikinci, br, veri([g1], durum='opsiyonlu'))
    db.session.rollback()

    ilan_kaydet(ilk, br, veri([g1], durum='geri_cekildi')); db.session.commit()
    ilan_kaydet(ikinci, br, veri([g1], durum='pazarlamada')); db.session.commit()
    assert ikinci.durum == 'pazarlamada'
    # aynı ilanın kendisiyle çakışması yok: tekrar kaydedilebilir
    ilan_kaydet(ikinci, br, veri([g1], durum='pazarlamada')); db.session.commit()


def test_kat_karsiligi_dort_parsel(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    gler = [gayrimenkul(br.id, ada='213', parsel=str(p), metrekare=m2, kaks=1.5)
            for p, m2 in ((2, 800), (3, 750), (4, 900), (5, 750))]
    ilan = ilan_kaydet(None, br, veri(gler, teklif_tipi='kat_karsiligi', fiyat=None, sahip_payi_yuzde=50,
                                      ana_gayrimenkul_id=gler[2].id,
                                      emsaller=[{'konum': 'A', 'pay_yuzde': 40},
                                                {'konum': '', 'm2': None, 'fiyat': None, 'pay_yuzde': None,
                                                 'link': '', 'notlar': ''},
                                                {'konum': 'B', 'pay_yuzde': 50}]))
    db.session.commit()
    assert [b.gayrimenkul_id for b in ilan.baglar] == [g.id for g in gler]
    assert [b.sira for b in ilan.baglar] == [1, 2, 3, 4]
    assert ilan.ana_gayrimenkul.id == gler[2].id and sum(b.ana_kayit for b in ilan.baglar) == 1
    assert len(ilan.emsaller) == 2
    assert ilan.office_id == gler[2].office_id

    oz = ilan_ozeti(ilan)
    assert {k: oz[k] for k in ('toplam_m2', 'insaat_hakki', 'sahibe_dusen_m2', 'bolge', 'bolge_kaynak')} == \
        {'toplam_m2': 3200, 'insaat_hakki': 4800, 'sahibe_dusen_m2': 2400, 'bolge': 45, 'bolge_kaynak': 'emsal'}
    assert round(oz['fark'], 1) == 11.1
    assert oz['konum'] == 'Talep bölge ortalamasının üstünde'
    assert oz['istenen'] == 50 and oz['kakssiz_parseller'] == []
    assert oz['emsal_sayisi'] == 2


def test_ozet_kakssiz_parselleri_listeler(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g1 = gayrimenkul(br.id, parsel='2', metrekare=1000, kaks=2)
    g2 = gayrimenkul(br.id, parsel='3', metrekare=500)
    ilan = ilan_kaydet(None, br, veri([g1, g2], fiyat=3_000_000, bolge_m2_fiyat_elle=2500)); db.session.commit()
    oz = ilan_ozeti(ilan)
    assert oz['toplam_m2'] == 1500 and oz['insaat_hakki'] == 2000
    assert oz['kakssiz_parseller'] == [g2.baslik_metni]
    assert oz['istenen'] == 2000 and (oz['bolge'], oz['bolge_kaynak']) == (2500, 'elle')
    assert oz['emsal_sayisi'] == 0
    assert oz['konum'] == 'Bölgeye göre uygun'


def test_emsaller_bastan_yazilir(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    ilan = ilan_kaydet(None, br, veri([g], emsaller=[{'konum': 'A', 'm2': 100, 'fiyat': 200000}]))
    db.session.commit()
    ilan_kaydet(ilan, br, veri([g], emsaller=[{'konum': 'B', 'm2': 100, 'fiyat': 300000}]))
    db.session.commit()
    assert [e.konum for e in IlanEmsal.query.all()] == ['B']


def test_gayrimenkul_listesi_guncellenir(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g1, g2, g3 = (gayrimenkul(br.id, parsel=str(p)) for p in (1, 2, 3))
    ilan = ilan_kaydet(None, br, veri([g1, g2])); db.session.commit()
    ilan_kaydet(ilan, br, veri([g3, g2], ana_gayrimenkul_id=g2.id)); db.session.commit()
    db.session.expire_all()
    assert [(b.gayrimenkul_id, b.sira, b.ana_kayit) for b in ilan.baglar] == [(g3.id, 1, False), (g2.id, 2, True)]


def test_teklif_tipine_ait_olmayan_alanlar_temizlenir(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    ilan = ilan_kaydet(None, br, veri([g], fiyat=1_500_000, kira=5000)); db.session.commit()
    assert float(ilan.fiyat) == 1_500_000 and ilan.kira is None
    ilan_kaydet(ilan, br, veri([g], teklif_tipi='kiralik', fiyat=1_500_000, kira=12_000, depozito=24_000,
                               sahip_payi_yuzde=40))
    db.session.commit()
    assert ilan.fiyat is None and float(ilan.kira) == 12_000 and float(ilan.depozito) == 24_000
    assert ilan.sahip_payi_yuzde is None


def test_zorunlu_alanlar(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([g], fiyat=None))
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([g], teklif_tipi='kat_karsiligi', sahip_payi_yuzde=120))
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([g], teklif_tipi='kiralik', kira=None))
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([g], teklif_tipi='takas'))
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([g], durum='bilinmiyor'))
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, br, veri([]))
    db.session.rollback()
    assert Ilan.query.count() == 0


def test_gorunmeyen_gayrimenkul_ilana_eklenemez(db_session, kullanicilar):
    g_br = gayrimenkul(kullanicilar['broker'])
    with pytest.raises(IlanHatasi):
        ilan_kaydet(None, kul(kullanicilar['d1']), veri([g_br]))


def test_sorumlu_gorunur_olmali(db_session, kullanicilar):
    k = kullanicilar
    d1 = kul(k['d1'])
    g = gayrimenkul(d1.id)
    ilan = ilan_kaydet(None, d1, veri([g], sorumlu_user_id=None)); db.session.commit()
    assert ilan.sorumlu_user_id == d1.id and ilan.user_id == d1.id
    with pytest.raises(IlanHatasi):
        ilan_kaydet(ilan, d1, veri([g], sorumlu_user_id=k['broker']))
    db.session.rollback()
    br = kul(k['broker'])
    ilan_kaydet(ilan, br, veri([g], sorumlu_user_id=k['d2'])); db.session.commit()
    assert ilan.sorumlu_user_id == k['d2'] and ilan.user_id == d1.id


def test_sahipleri_kaydet_hisseli(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    c1, c2 = kontak(br.id, 'Ali'), kontak(br.id, 'Veli')
    sahipleri_kaydet(g, br, [{'contact_id': c1.id, 'hisse': '1/2', 'irtibat': True},
                             {'contact_id': c2.id, 'hisse': '1/2', 'irtibat': False}])
    db.session.commit()
    s = {x.contact_id: (x.hisse, x.irtibat) for x in GayrimenkulSahibi.query.all()}
    assert s == {c1.id: ('1/2', True), c2.id: ('1/2', False)}

    sahipleri_kaydet(g, br, [{'contact_id': c2.id, 'hisse': 'Tam', 'irtibat': True}])
    db.session.commit()
    s = [(x.contact_id, x.hisse, x.irtibat) for x in GayrimenkulSahibi.query.all()]
    assert s == [(c2.id, 'Tam', True)]


def test_baskasinin_kontagi_sahip_secilemez_servis(db_session, kullanicilar):
    d1 = kul(kullanicilar['d1'])
    g = gayrimenkul(d1.id)
    c = kontak(kullanicilar['d2'])
    with pytest.raises(IlanHatasi, match='Seçilen müşteri bulunamadı.'):
        sahipleri_kaydet(g, d1, [{'contact_id': c.id, 'hisse': '1/1', 'irtibat': True}])
    db.session.rollback()
    assert GayrimenkulSahibi.query.count() == 0


def test_kontak_silinince_sahiplik_silinir_gayrimenkul_kalir(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    c = kontak(br.id)
    sahipleri_kaydet(g, br, [{'contact_id': c.id, 'hisse': '1/1', 'irtibat': True}]); db.session.commit()
    c.sahiplikler  # ilişkiyi yükle: ORM tarafı da silmeli (null yapmamalı)
    db.session.delete(c); db.session.commit()
    assert GayrimenkulSahibi.query.count() == 0
    assert db.session.get(ArsaAnaliz, g.id) is not None


def _deal(user_id, ilan):
    c = kontak(user_id, 'Alıcı')
    d = Deal(user_id=user_id, contact_id=c.id, title='Satış', ilan_id=ilan.id)
    db.session.add(d); db.session.commit()
    return d


def test_tek_gayrimenkullu_ilan_gayrimenkulle_silinir(db_session, kullanicilar):
    from blueprints.analysis_bp import _analizi_sil
    br = kul(kullanicilar['broker'])
    g = gayrimenkul(br.id)
    ilan = ilan_kaydet(None, br, veri([g], emsaller=[{'konum': 'A', 'm2': 100, 'fiyat': 1000}]))
    db.session.commit()
    p = Portfolio(user_id=br.id, title='P'); p.ilanlar.append(ilan); db.session.add(p); db.session.commit()
    d = _deal(br.id, ilan)
    ilan_id, deal_id = ilan.id, d.id

    _analizi_sil(g); db.session.commit()
    db.session.expire_all()
    assert db.session.get(Ilan, ilan_id) is None and IlanEmsal.query.count() == 0
    assert db.session.execute(db.select(portfolio_ilanlar)).all() == []
    assert db.session.get(Deal, deal_id).ilan_id is None
    assert db.session.get(Portfolio, p.id) is not None


def test_dort_parselli_ilan_kalan_uc_ile_yeni_ana_kayit(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    gler = [gayrimenkul(br.id, parsel=str(p)) for p in (2, 3, 4, 5)]
    ilan = ilan_kaydet(None, br, veri(gler)); db.session.commit()
    assert ilan.ana_gayrimenkul.id == gler[0].id
    ilan_id = ilan.id

    gayrimenkul_silinirken(gler[0])
    db.session.delete(gler[0]); db.session.commit()
    db.session.expire_all()
    ilan = db.session.get(Ilan, ilan_id)
    assert [b.gayrimenkul_id for b in ilan.baglar] == [g.id for g in gler[1:]]
    assert [b.ana_kayit for b in ilan.baglar] == [True, False, False]
    assert ilan.ana_gayrimenkul.id == gler[1].id


def test_sorumlu_ilani_kaydedebilir_ama_yeni_gayrimenkul_ve_sorumlu_kisitli(db_session, kullanicilar):
    k = kullanicilar
    br, d1 = kul(k['broker']), kul(k['d1'])
    g_br = gayrimenkul(br.id, parsel='2')
    g_br2 = gayrimenkul(br.id, parsel='3')
    ilan = ilan_kaydet(None, br, veri([g_br], sorumlu_user_id=d1.id)); db.session.commit()
    assert ilan_or_404(ilan.id, d1).id == ilan.id

    # d1 yalnız sorumlu: durumunu değiştirerek kaydedebilir (mevcut gayrimenkul, değişmeyen sorumlu)
    ilan_kaydet(ilan, d1, veri([g_br], durum='pazarlamada', sorumlu_user_id=d1.id)); db.session.commit()
    assert ilan.durum == 'pazarlamada' and ilan.sorumlu_user_id == d1.id

    # bağlı olmayan broker gayrimenkulü eklenemez
    with pytest.raises(IlanHatasi):
        ilan_kaydet(ilan, d1, veri([g_br, g_br2], sorumlu_user_id=d1.id))
    db.session.rollback()

    # sorumlu görünmeyen bir kullanıcıya değiştirilemez
    with pytest.raises(IlanHatasi):
        ilan_kaydet(ilan, d1, veri([g_br], sorumlu_user_id=k['d2']))
    db.session.rollback()


def test_degismeyen_gorunmez_sorumlu_korunur(db_session, kullanicilar):
    k = kullanicilar
    d1 = kul(k['d1'])
    g = gayrimenkul(d1.id)
    ilan = ilan_kaydet(None, d1, veri([g])); db.session.commit()
    ilan.sorumlu_user_id = k['dx']; db.session.commit()  # ör. superadmin atadı; dx d1'e görünmez
    ilan_kaydet(ilan, d1, veri([g], durum='opsiyonlu', sorumlu_user_id=k['dx'])); db.session.commit()
    assert ilan.durum == 'opsiyonlu' and ilan.sorumlu_user_id == k['dx']


def test_ana_kayit_tasininca_office_guncellenir(db_session, kullanicilar):
    br = kul(kullanicilar['broker'])
    g1 = gayrimenkul(br.id, parsel='1'); g2 = gayrimenkul(br.id, parsel='2')
    g2.office_id = kullanicilar['ofis']; db.session.commit()
    ilan = ilan_kaydet(None, br, veri([g1, g2])); db.session.commit()
    assert ilan.office_id is None
    ilan_id = ilan.id
    gayrimenkul_silinirken(g1); db.session.delete(g1); db.session.commit()
    db.session.expire_all()
    assert db.session.get(Ilan, ilan_id).office_id == kullanicilar['ofis']
