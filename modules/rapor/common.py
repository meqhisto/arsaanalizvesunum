# -*- coding: utf-8 -*-
"""Üç formatın ortak kullandığı içerik parçaları (tablolar, göstergeler)."""
from .model import SWOT_KEYS, SWOT_TITLES, sayi, tr_currency, tr_number

FIYAT_BASLIK = 'Fiyat ve Emsal Analizi'


def _fark_kpi(m):
    if m.fark is None:
        return ('Bölgeye göre', '-', 'Bölge ortalaması yok')
    if abs(m.fark) < 0.05:
        deger = 'Aynı seviyede'
    else:
        yon = 'altında' if m.fark < 0 else 'üstünde'
        deger = f"%{tr_number(abs(m.fark), 1)} {yon}"
    return ('Bölgeye göre', deger, f"Bölge ort. {m.deger_metni(m.bolge)}")


def _alan_kpi(m):
    if m.cok_parsel:
        return ('Toplam alan', f"{sayi(m.metrekare)} m²", f"{len(m.parseller)} {m.parsel_birimi}")
    return ('Alan', f"{sayi(m.metrekare)} m²", m.tur_etiketi)


def kpis(m):
    """Kapaktaki 4 temel gösterge: (başlık, değer, alt not)."""
    satir = dict(m.fiyat_satirlari)
    if m.teklif_tipi == 'kat_karsiligi':
        eksik = m.extras.get('kaks_eksik')
        if m.insaat_hakki is None:
            insaat = ('İnşaat hakkı', 'Hesaplanamadı', 'KAKS bilgisi yok')
            sahibe = ('Sahibe düşen', 'Hesaplanamadı', 'KAKS bilgisi yok')
        else:
            not_ = eksik or ('Elle girildi' if m.extras.get('insaat_elle') else 'KAKS × alan')
            insaat = ('İnşaat hakkı', f"{sayi(m.insaat_hakki)} m²", not_)
            sahibe = ('Sahibe düşen', f"{sayi(m.sahibe_dusen_m2)} m²" if m.sahibe_dusen_m2 is not None else '-',
                      eksik or 'Tahmini inşaat alanı')
        return [
            ('Arsa sahibi payı', satir.get('Arsa sahibi payı', '-'), 'Talep edilen pay'),
            ('Toplam arsa alanı', satir.get('Toplam arsa alanı', '-'), f"{len(m.parseller)} {m.parsel_birimi}"),
            insaat,
            sahibe,
        ]
    if m.teklif_tipi in ('satilik', 'kiralik'):
        kira = m.teklif_tipi == 'kiralik'
        son = (('Uygunluk puanı', f"{tr_number(m.puan, 0)} / 100", m.puan_etiketi) if m.puan_detay
               else _alan_kpi(m))
        return [
            ('Aylık kira' if kira else 'İstenen fiyat', tr_currency(m.tutar) if m.tutar is not None else '-',
             f"{sayi(m.metrekare)} m²"),
            ('m² kira' if kira else 'm² fiyatı', satir.get('m² kira' if kira else 'm² fiyatı', '-'),
             'Aylık, TL / m²' if kira else 'TL / m²'),
            _fark_kpi(m),
            son,
        ]
    # Tanıtım
    kpi = [('Tür', m.tur_etiketi, m.teklif_etiketi + ' raporu'), _alan_kpi(m), ('Konum', m.ilce or '-', m.il or '')]
    if m.puan_detay:
        kpi.append(('Uygunluk puanı', f"{tr_number(m.puan, 0)} / 100", m.puan_etiketi))
    elif m.arsa_mi:
        kpi.append(('İmar', m.imar_durumu, f"KAKS {tr_number(m.kaks, 2)}"))
    else:
        bilgi = dict(m.tur_bilgileri)
        kpi.append(('Oda / kat', bilgi.get('Oda sayısı', '-'), f"Kat {bilgi.get('Bulunduğu kat', '-')}"))
    return kpi


def location_rows(m):
    """Konum (ve tek parselli arsada parsel) bilgileri: [(etiket, değer), ...]"""
    rows = [('İl / İlçe', f"{m.il} / {m.ilce}"), ('Mahalle', m.mahalle or '-')]
    if m.arsa_mi and not m.cok_parsel:
        rows += [('Ada / Parsel', f"{m.ada} / {m.parsel}"), ('Pafta', m.pafta),
                 ('Yüzölçümü', f"{tr_number(m.metrekare, 2)} m²"), ('İmar durumu', m.imar_durumu)]
    elif m.cok_parsel:
        rows.append(('Toplam alan', f"{sayi(m.metrekare)} m² ({len(m.parseller)} {m.parsel_birimi})"))
    if m.koordinat:
        rows.append(('Koordinat', f"{m.koordinat[0]:.5f}, {m.koordinat[1]:.5f}".replace('.', ',')))
    return rows


def zoning_rows(m):
    return [
        ('TAKS / KAKS', m.taks_kaks),
        ('Taban alanı', f"{tr_number(m.taban_alani)} m²"),
        ('Toplam inşaat alanı', f"{tr_number(m.insaat_alani)} m²"),
        ('Teorik kat sayısı', tr_number(m.kat_sayisi, 1)),
    ]


def show_zoning(m):
    """İmar/yapılaşma tablosu yalnız tek parselli arsa/tarlada."""
    return m.arsa_mi and not m.cok_parsel


def parcel_table(m):
    """Çok parselde başlık + satırlar."""
    head = ['#', 'Ada', 'Parsel', 'm²', 'İmar', 'KAKS']
    rows = [head]
    for n, p in enumerate(m.parseller, start=1):
        rows.append([str(n), p['ada'], p['parsel'], sayi(p['m2']), p['imar'],
                     sayi(p['kaks']) if p['kaks'] is not None else '-'])
    return rows


def parcel_summary(m):
    text = f"Toplam {sayi(m.toplam_m2)} m²"
    if m.insaat_hakki is not None:
        text += f" · İnşaat hakkı ({'elle' if m.extras.get('insaat_elle') else 'tahmini'}) {sayi(m.insaat_hakki)} m²"
        if m.extras.get('kaks_eksik'):
            text += f" ({m.extras['kaks_eksik']})"
    elif m.extras.get('kaks_hic_yok'):
        text += " · İnşaat hakkı hesaplanamadı (KAKS bilgisi yok)"
    return text


def parcel_section_title(m):
    return 'Parseller' if m.parsel_birimi == 'parsel' else 'Gayrimenkuller'


def emsal_table(m):
    """Emsal tablosu: başlık + satırlar; emsal yoksa []."""
    if not m.emsaller:
        return []
    kat = m.teklif_tipi == 'kat_karsiligi'
    if kat:  # Kat karşılığında m² fiyatı anlamsız: sütun yok
        return [['Konum', 'm²', 'Pay']] + [[e['konum'], e['m2'], e['deger']] for e in m.emsaller]
    head = ['Konum', 'm²', 'Kira' if m.teklif_tipi == 'kiralik' else 'Fiyat', 'm² fiyatı']
    return [head] + [[e['konum'], e['m2'], e['deger'], e['m2_fiyat']] for e in m.emsaller]


def emsal_ratios(m):
    return (0.5, 0.2, 0.3) if m.teklif_tipi == 'kat_karsiligi' else (0.4, 0.15, 0.25, 0.2)


PARCEL_RATIOS = (0.06, 0.14, 0.14, 0.18, 0.34, 0.14)
PARCEL_RIGHT = (3, 5)
EMSAL_RIGHT = (1, 2, 3)


def bolge_rows(m):
    """Bölge ortalaması, kaynağı, fark ve konumlandırma."""
    if m.bolge is None:
        return [('Bölge ortalaması', 'Emsal ya da elle girilmiş bölge değeri yok')]
    kaynak = f"{m.emsal_sayisi} emsalden" if m.bolge_kaynak == 'emsal' else 'Elle girildi'
    rows = [('Bu ilan', m.deger_metni(m.istenen)), ('Bölge ortalaması', m.deger_metni(m.bolge)),
            ('Kaynak', kaynak)]
    if m.fark is not None:
        yon = 'altında' if m.fark < 0 else 'üzerinde'
        rows.append(('Fark', f"%{tr_number(abs(m.fark), 1)} {yon}" if abs(m.fark) >= 0.05 else 'Aynı seviyede'))
    if m.konum_etiketi:
        rows.append(('Konumlandırma', m.konum_etiketi))
    return rows


def swot_blocks(m):
    return [(SWOT_TITLES[k], m.swot.get(k) or []) for k in SWOT_KEYS]


def has_swot(m):
    return any(m.swot.get(k) for k in SWOT_KEYS)


def advisor_rows(m):
    a = m.advisor
    rows = [('Danışman', a.ad_soyad), ('Ünvan', a.unvan), ('Firma', a.firma),
            ('Telefon', a.telefon), ('E-posta', a.email)]
    if a.adres != '-':
        rows.append(('Adres', a.adres))
    return [(k, v) for k, v in rows if v and v != '-']


QR_LABELS = (('qr_detay', 'Detay sayfası'), ('qr_harita', 'Haritada aç'))

DISCLAIMER = ("Bu rapor bilgilendirme amaçlıdır ve lisanslı bir değerleme raporu yerine geçmez. Bölge "
              "karşılaştırmaları ilana girilen emsallere dayanır; gerçekleşen değerler piyasa koşullarına göre "
              "farklılık gösterebilir. Tapu, imar ve şerh bilgileri resmi kurumlardan teyit edilmelidir.")
