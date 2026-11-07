from modules.ilan_hesap import (bolge_ortalamasi, fark_yuzde, insaat_hakki, istenen_deger,
                                konumlandirma, sahibe_dusen_m2, toplam_m2, tutar_ayristir,
                                sayi_metni)


def test_tutar_ayristir_turkce():
    assert tutar_ayristir("4.250.000") == 4250000
    assert tutar_ayristir("1.250,50") == 1250.5
    assert tutar_ayristir("1250.5") == 1250.5
    assert tutar_ayristir("") is None and tutar_ayristir(None) is None and tutar_ayristir("abc") is None


def test_tutar_ayristir_sonlu_ve_duz_sayi():
    for metin in ("nan", "NaN", "inf", "-inf", "Infinity", "1e3", "1E3", "1_000", "+-5", "--5", "1.2.3,4,5"):
        assert tutar_ayristir(metin) is None, metin
    assert tutar_ayristir("-1.250,5") == -1250.5 and tutar_ayristir("+50") is None
    assert tutar_ayristir("-12") == -12 and tutar_ayristir("0,5") == 0.5 and tutar_ayristir(".5") == 0.5


def test_insaat_hakki_toplar():
    p = [{'m2': 1000, 'kaks': 1.5}, {'m2': 800, 'kaks': 2.0}]
    assert toplam_m2(p) == 1800
    assert insaat_hakki(p, None) == (3100, [])


def test_insaat_hakki_kakssiz_parseli_atlar():
    p = [{'m2': 1000, 'kaks': 1.5}, {'m2': 800, 'kaks': None}]
    assert insaat_hakki(p, None) == (1500, [1])
    assert insaat_hakki([{'m2': 800, 'kaks': None}], None) == (None, [0])


def test_insaat_hakki_elle_degeri_kullanir():
    assert insaat_hakki([{'m2': 1000, 'kaks': 1.5}], 4000) == (4000, [])


def test_sahibe_dusen_m2():
    assert sahibe_dusen_m2(3100, 50) == 1550
    assert sahibe_dusen_m2(None, 50) is None and sahibe_dusen_m2(3100, None) is None


def test_bolge_ortalamasi_m2_agirlikli():
    e = [{'m2': 100, 'fiyat': 2_000_000, 'pay_yuzde': None}, {'m2': 300, 'fiyat': 4_500_000, 'pay_yuzde': None}]
    assert bolge_ortalamasi('satilik', e, 99, None) == (16250, 'emsal')
    assert bolge_ortalamasi('satilik', [], 18000, None) == (18000, 'elle')
    assert bolge_ortalamasi('satilik', [], None, None) == (None, 'yok')


def test_bolge_ortalamasi_kat_karsiligi_pay():
    e = [{'m2': None, 'fiyat': None, 'pay_yuzde': 40}, {'m2': None, 'fiyat': None, 'pay_yuzde': 50}]
    assert bolge_ortalamasi('kat_karsiligi', e, None, 30) == (45, 'emsal')


def test_eksik_emsal_satiri_ortalamaya_girmez():
    e = [{'m2': 100, 'fiyat': 2_000_000, 'pay_yuzde': None}, {'m2': None, 'fiyat': 3_000_000, 'pay_yuzde': None}]
    assert bolge_ortalamasi('satilik', e, None, None) == (20000, 'emsal')


def test_fark_ve_konumlandirma():
    assert round(fark_yuzde(19980, 18500), 1) == 8.0
    assert fark_yuzde(100, None) is None and fark_yuzde(100, 0) is None
    assert konumlandirma('satilik', -6) == 'Bölgeye göre uygun'
    assert konumlandirma('satilik', 5) == 'Piyasa seviyesinde'
    assert konumlandirma('satilik', 5.1) == 'Bölgenin üstünde'
    assert konumlandirma('kat_karsiligi', 11.1) == 'Talep bölge ortalamasının üstünde'
    assert konumlandirma('kat_karsiligi', -6) == 'Müteahhit için cazip'
    assert konumlandirma('kat_karsiligi', 0) == 'Piyasa seviyesinde'
    assert konumlandirma('satilik', None) is None


def test_istenen_deger():
    assert istenen_deger('satilik', 4_000_000, None, None, 200) == 20000
    assert istenen_deger('kiralik', None, 30_000, None, 150) == 200
    assert istenen_deger('kat_karsiligi', None, None, 50, 3200) == 50
    assert istenen_deger('satilik', 4_000_000, None, None, 0) is None


def test_sayi_metni_turkce():
    assert sayi_metni(12000) == "12.000"
    assert sayi_metni(1.5) == "1,5"
    assert sayi_metni("800.00") == "800"
    assert sayi_metni(1250000.25) == "1.250.000,25"
    assert sayi_metni(None) == ""
