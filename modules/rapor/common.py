# -*- coding: utf-8 -*-
"""Üç formatın ortak kullandığı içerik parçaları (tablolar, göstergeler)."""
from .model import tr_currency, tr_number, SWOT_TITLES, SWOT_KEYS


def kpis(m):
    """Kapaktaki 4 temel gösterge: (başlık, değer, alt not)."""
    if m.bolge_fark is None:
        fark = ('Bölgeye göre', '-', 'Bölge fiyatı girilmedi')
    else:
        yon = 'ucuz' if m.bolge_fark < 0 else 'pahalı'
        fark = ('Bölgeye göre', f"%{tr_number(abs(m.bolge_fark), 1)} {yon}",
                f"Bölge ort. {tr_number(m.bolge_m2_fiyat)} TL/m²")
    return [
        ('Toplam fiyat', tr_currency(m.fiyat), f"{tr_number(m.metrekare)} m²"),
        ('m² fiyatı', f"{tr_number(m.m2_fiyat)} TL",
         f"İnşaat m² başı {tr_number(m.fiyat / m.insaat_alani)} TL" if m.insaat_alani else 'TL / m²'),
        fark,
        ('Uygunluk puanı', f"{tr_number(m.puan, 0)} / 100", m.puan_etiketi),
    ]


def parcel_rows(m):
    """Arsa bilgileri: [(etiket, değer), ...]"""
    rows = [
        ('İl / İlçe', f"{m.il} / {m.ilce}"),
        ('Mahalle', m.mahalle or '-'),
        ('Ada / Parsel', f"{m.ada} / {m.parsel}"),
        ('Pafta', m.pafta),
        ('Yüzölçümü', f"{tr_number(m.metrekare, 2)} m²"),
        ('İmar durumu', m.imar_durumu),
        ('Toplam fiyat', tr_currency(m.fiyat)),
        ('m² fiyatı', tr_currency(m.m2_fiyat)),
    ]
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


def scenario_rows(m):
    """Başlık + senaryo satırları: [['Senaryo', 'Yıllık artış', '1. yıl', '3. yıl', '5. yıl', 'Toplam artış']]"""
    head = ['Senaryo', 'Yıllık artış', '1. yıl', '3. yıl', '5. yıl', '5 yılda artış']
    rows = [head]
    for sc in m.senaryolar:
        d = sc.degerler
        rows.append([sc.ad, f"%{tr_number(sc.oran, 1)}", tr_currency(d[1]), tr_currency(d[3]), tr_currency(d[5]),
                     f"%{tr_number((d[5] / d[0] - 1) * 100 if d[0] else 0, 0)}"])
    return rows


def swot_blocks(m):
    return [(SWOT_TITLES[k], m.swot.get(k) or []) for k in SWOT_KEYS]


def advisor_rows(m):
    a = m.advisor
    rows = [('Danışman', a.ad_soyad), ('Ünvan', a.unvan), ('Firma', a.firma),
            ('Telefon', a.telefon), ('E-posta', a.email)]
    if a.adres != '-':
        rows.append(('Adres', a.adres))
    return [(k, v) for k, v in rows if v and v != '-']


DISCLAIMER = ("Bu rapor bilgilendirme amaçlıdır ve lisanslı bir değerleme raporu yerine geçmez. Projeksiyonlar "
              "varsayımlara dayanır; gerçekleşen değerler piyasa koşullarına göre farklılık gösterebilir. "
              "Tapu, imar ve şerh bilgileri resmi kurumlardan teyit edilmelidir.")
