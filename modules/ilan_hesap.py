"""İlan hesapları: saf fonksiyonlar, ORM bilmez."""


def tutar_ayristir(metin):
    """'4.250.000' / '1.250,50' / '1250.5' -> float; çözülemezse None."""
    if metin is None:
        return None
    s = str(metin).strip().replace(' ', '')
    if not s:
        return None
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    elif '.' in s:
        gruplar = s.split('.')
        haneler = len(''.join(gruplar).lstrip('-+'))
        binlik = len(gruplar[-1]) == 3 and gruplar[0].lstrip('-+') != '0' and (len(gruplar) > 2 or haneler > 3)
        if binlik:
            s = s.replace('.', '')
    try:
        return float(s)
    except ValueError:
        return None


def toplam_m2(parseller):
    return sum(p.get('m2') or 0 for p in parseller)


def insaat_hakki(parseller, elle):
    if elle is not None:
        return elle, []
    eksik = [i for i, p in enumerate(parseller) if not p.get('kaks')]
    toplam = sum((p['m2'] or 0) * p['kaks'] for p in parseller if p.get('kaks'))
    if len(eksik) == len(parseller):
        return None, eksik
    return toplam, eksik


def sahibe_dusen_m2(insaat, pay_yuzde):
    if insaat is None or pay_yuzde is None:
        return None
    return insaat * pay_yuzde / 100


def bolge_ortalamasi(teklif_tipi, emsaller, elle_m2, elle_pay):
    if teklif_tipi == 'kat_karsiligi':
        paylar = [e['pay_yuzde'] for e in emsaller if e.get('pay_yuzde') is not None]
        if paylar:
            return sum(paylar) / len(paylar), 'emsal'
        elle = elle_pay
    else:
        gecerli = [e for e in emsaller if e.get('m2') and e.get('fiyat') is not None]
        m2 = sum(e['m2'] for e in gecerli)
        if m2:
            return sum(e['fiyat'] for e in gecerli) / m2, 'emsal'
        elle = elle_m2
    if elle is not None:
        return elle, 'elle'
    return None, 'yok'


def istenen_deger(teklif_tipi, fiyat, kira, pay_yuzde, toplam_m2):
    if teklif_tipi == 'kat_karsiligi':
        return pay_yuzde
    tutar = kira if teklif_tipi == 'kiralik' else fiyat
    if tutar is None or not toplam_m2:
        return None
    return tutar / toplam_m2


def fark_yuzde(istenen, bolge):
    if istenen is None or not bolge:
        return None
    return (istenen - bolge) / bolge * 100


def konumlandirma(teklif_tipi, fark):
    if fark is None:
        return None
    if fark < -5:
        return 'Müteahhit için cazip' if teklif_tipi == 'kat_karsiligi' else 'Bölgeye göre uygun'
    if fark <= 5:
        return 'Piyasa seviyesinde'
    return 'Talep bölge ortalamasının üstünde' if teklif_tipi == 'kat_karsiligi' else 'Bölgenin üstünde'


def sayi_metni(deger, ondalik=2):
    """Türkçe sayı yazımı (rapor tr_number + gereksiz ondalık sıfırlar atılır): 12000 -> '12.000', 1.5 -> '1,5'; gereksiz sıfırlar atılır. None -> ''."""
    if deger is None or deger == '':
        return ''
    from modules.rapor.model import tr_number
    try:
        float(deger)
    except (TypeError, ValueError):
        return str(deger)
    metin = tr_number(deger, ondalik)
    if ',' in metin:
        metin = metin.rstrip('0').rstrip(',')
    return metin
