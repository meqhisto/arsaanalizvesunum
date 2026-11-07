"""Eski ArsaAnaliz.fiyat alanının aktif satılık ilanla eşitlenmesi ve portföy kartları (final inceleme #3)."""
from decimal import Decimal

from models import db
from models.arsa_models import ArsaAnaliz, DashboardStats
from models.ilan_models import Ilan
from test_ilan_ekranlari import arsa, form, html, ilan, istemci


def _stats(user_id, sayi=1, toplam=0):
    s = DashboardStats(user_id=user_id, toplam_arsa_sayisi=sayi, toplam_deger=Decimal(toplam),
                       ortalama_fiyat=0.0, en_yuksek_fiyat=0.0, en_dusuk_fiyat=0.0)
    db.session.add(s)
    db.session.commit()
    return s


def _fiyat(g):
    db.session.expire_all()
    return float(db.session.get(ArsaAnaliz, g.id).fiyat or 0)


def _toplam(user_id):
    db.session.expire_all()
    return float(DashboardStats.query.filter_by(user_id=user_id).one().toplam_deger)


def test_ilan_formu_aktif_satilik_tek_gayrimenkulde_fiyati_esitler(app, kullanicilar):
    d1 = kullanicilar['d1']
    g = arsa(d1)
    _stats(d1)
    c = istemci(app, d1)
    r = c.post('/ilanlar/yeni', data=form([g], fiyat='2.500.000'))
    assert r.status_code == 302
    assert _fiyat(g) == 2_500_000 and _toplam(d1) == 2_500_000
    i = Ilan.query.one()
    # Düzenlemede fiyat değişince fark istatistiğe yansır
    r = c.post(f'/ilanlar/{i.id}/duzenle', data=form([g], fiyat='3.000.000'))
    assert r.status_code == 302
    assert _fiyat(g) == 3_000_000 and _toplam(d1) == 3_000_000
    stats = DashboardStats.query.filter_by(user_id=d1).one()
    assert stats.en_yuksek_fiyat == 3_000_000


def test_aktif_olmayan_kiralik_veya_cok_gayrimenkullu_ilan_fiyati_degistirmez(app, kullanicilar):
    d1 = kullanicilar['d1']
    g1, g2, g3, g4 = (arsa(d1, parsel=str(n)) for n in range(1, 5))
    c = istemci(app, d1)
    assert c.post('/ilanlar/yeni', data=form([g1], fiyat='1.000.000', durum='hazirlaniyor')).status_code == 302
    assert c.post('/ilanlar/yeni', data=form([g2], teklif_tipi='kiralik', kira='10.000')).status_code == 302
    assert c.post('/ilanlar/yeni', data=form([g3, g4], fiyat='5.000.000')).status_code == 302
    assert [_fiyat(g) for g in (g1, g2, g3, g4)] == [0, 0, 0, 0]


def test_durum_aktif_olunca_fiyat_esitlenir(app, kullanicilar):
    d1 = kullanicilar['d1']
    g = arsa(d1)
    _stats(d1)
    i = ilan([g], durum='hazirlaniyor', fiyat=1_750_000)
    r = istemci(app, d1).post(f'/ilanlar/{i.id}/durum', data={'durum': 'opsiyonlu'})
    assert r.status_code == 302
    assert _fiyat(g) == 1_750_000 and _toplam(d1) == 1_750_000


def test_hemen_ilana_cikar_istatistigi_bir_kez_sayar(app, kullanicilar):
    from test_gayrimenkul_form import arsa_formu, olustur
    d1 = kullanicilar['d1']
    c = istemci(app, d1)
    r = olustur(c, arsa_formu(ilana_cikar='1', ilan_teklif_tipi='satilik', ilan_fiyat='4.250.000'))
    assert r.status_code == 302
    stats = DashboardStats.query.filter_by(user_id=d1).one()
    assert float(stats.toplam_deger) == 4_250_000 and stats.toplam_arsa_sayisi == 1
    assert stats.en_yuksek_fiyat == 4_250_000 and stats.en_dusuk_fiyat == 4_250_000


def test_portfoy_kartlari_aktif_ilan_fiyatini_gosterir(app, kullanicilar):
    d1 = kullanicilar['d1']
    g = arsa(d1, fiyat=0, mahalle='Kepez')
    ilan([g], durum='pazarlamada', fiyat=6_400_000)
    kira = arsa(d1, parsel='9', fiyat=123_456, mahalle='Esenler')
    ilan([kira], kod='ILN-2026-0002', durum='pazarlamada', teklif_tipi='kiralik', kira=15_000)
    arsa(d1, parsel='10', fiyat=999_999, mahalle='Barbaros')  # aktif ilanı yok
    sayfa = html(istemci(app, d1).get('/portfolio/portfolios'))
    assert '6.400.000 TL' in sayfa
    assert '15.000 TL/ay' in sayfa and '123.456 TL' not in sayfa
    assert '999.999 TL' not in sayfa and 'Aktif ilan yok' in sayfa
    assert '₺' not in sayfa
