from datetime import datetime

from models import db
from models.arsa_models import ArsaAnaliz
from models.ilan_models import Ilan
from models.user_models import Portfolio
from modules.ilan_kurulum import kur


def eski_analiz(user_id, il='Çanakkale', ilce='Merkez', mahalle='Kepez', ada='101', parsel='5',
                metrekare=1000, fiyat=3_000_000, bolge_fiyat=None, altyapi=None):
    """Eski stilde (yalnız eski sütunlar dolu; tur/ozellikler NULL) gayrimenkul kaydı."""
    a = ArsaAnaliz(user_id=user_id, il=il, ilce=ilce, mahalle=mahalle, ada=ada, parsel=parsel,
                   metrekare=metrekare, fiyat=fiyat, bolge_fiyat=bolge_fiyat, altyapi=altyapi)
    db.session.add(a)
    db.session.flush()
    # ORM varsayılanlarını (tur='arsa') atlayıp eski kayıt durumunu taklit et
    db.session.execute(db.text("UPDATE arsa_analizleri SET tur = NULL, ozellikler = NULL WHERE id = :id"),
                       {'id': a.id})
    db.session.commit()
    return a


def portfoy(user_id, analizler):
    p = Portfolio(user_id=user_id, title='Test portföy')
    db.session.add(p)
    for a in analizler:
        p.analizler.append(a)
    db.session.commit()
    return p


def test_gecis_ilan_olusturur_ve_iki_kez_calisir(db_session, kullanicilar):
    a = eski_analiz(kullanicilar['broker'], metrekare=2450, fiyat=7_350_000, bolge_fiyat=3200,
                    altyapi=['yol', 'su'])
    kur(); kur()
    ilanlar = Ilan.query.all()
    assert len(ilanlar) == 1
    i = ilanlar[0]
    assert (i.teklif_tipi, i.durum, float(i.fiyat), float(i.bolge_m2_fiyat_elle)) == ('satilik', 'pazarlamada', 7_350_000, 3200)
    assert i.kod.startswith(f"ILN-{datetime.utcnow().year}-") and i.user_id == a.user_id and i.sorumlu_user_id == a.user_id
    assert i.ana_gayrimenkul.id == a.id
    db.session.refresh(a)
    assert a.tur == 'arsa' and a.ozellikler['altyapi'] == ['yol', 'su'] and a.altyapi == ['yol', 'su']


def test_gecis_toplam_bolge_fiyatini_m2ye_cevirir(db_session, kullanicilar):
    eski_analiz(kullanicilar['broker'], metrekare=10094.82, fiyat=35_000_000, bolge_fiyat=70_000_000)
    kur()
    assert round(float(Ilan.query.one().bolge_m2_fiyat_elle)) == 6934


def test_gecis_portfoy_baglarini_kopyalar(db_session, kullanicilar):
    a = eski_analiz(kullanicilar['broker']); p = portfoy(kullanicilar['broker'], [a])
    kur(); kur()
    assert [i.ana_gayrimenkul.id for i in p.ilanlar] == [a.id]


def test_ilani_olan_gayrimenkule_yeni_ilan_acilmaz(db_session, kullanicilar):
    eski_analiz(kullanicilar['broker']); kur()
    Ilan.query.one().durum = 'geri_cekildi'; db.session.commit()
    kur()
    assert Ilan.query.count() == 1


def test_kur_eski_semaya_eksik_sutunlari_ekler(db_session, kullanicilar):
    # create_all yeni sütunlarla kurduğu için eski şemayı sütunları düşürerek taklit et
    from sqlalchemy import inspect
    from modules.ilan_kurulum import ARSA_SUTUNLARI
    for ad, _ in ARSA_SUTUNLARI:
        db.session.execute(db.text(f"ALTER TABLE arsa_analizleri DROP COLUMN {ad}"))
    db.session.execute(db.text("ALTER TABLE crm_deals DROP COLUMN ilan_id"))
    db.session.execute(db.text(
        "INSERT INTO arsa_analizleri (user_id, il, ilce, mahalle, ada, parsel, metrekare, fiyat, altyapi) "
        "VALUES (:u, 'Çanakkale', 'Merkez', 'Kepez', '1', '2', 500, 1000000, '[\"yol\"]')"),
        {'u': kullanicilar['broker']})
    db.session.commit()
    kur(); kur()
    db.session.remove()
    ins = inspect(db.engine)
    arsa = {c['name'] for c in ins.get_columns('arsa_analizleri')}
    assert {ad for ad, _ in ARSA_SUTUNLARI} <= arsa
    assert 'ilan_id' in {c['name'] for c in ins.get_columns('crm_deals')}
    assert 'ix_crm_deals_ilan_id' in {i['name'] for i in ins.get_indexes('crm_deals')}
    a = ArsaAnaliz.query.one()
    assert a.tur == 'arsa' and a.ozellikler == {'altyapi': ['yol']}
    assert Ilan.query.one().ana_gayrimenkul.id == a.id


def test_gecis_bir_kez_calisir_sonradan_ilansiz_gayrimenkule_ilan_acmaz(db_session, kullanicilar):
    eski_analiz(kullanicilar['broker']); kur()
    yeni = ArsaAnaliz(user_id=kullanicilar['broker'], il='Çanakkale', ilce='Merkez', mahalle='Esenler',
                      ada='7', parsel='8', metrekare=600, fiyat=900_000)
    db.session.add(yeni); db.session.commit()
    kur()
    db.session.refresh(yeni)
    assert yeni.ilan_baglari == [] and Ilan.query.count() == 1


def test_portfoyden_cikarilan_ilan_geri_eklenmez(db_session, kullanicilar):
    a = eski_analiz(kullanicilar['broker']); p = portfoy(kullanicilar['broker'], [a])
    kur()
    p.ilanlar.remove(Ilan.query.one()); db.session.commit()
    kur()
    assert p.ilanlar.count() == 0
