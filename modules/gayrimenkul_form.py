# -*- coding: utf-8 -*-
"""Gayrimenkul formu (spec §3.1, §5.1): türe göre doğrulama, form ↔ kayıt dönüşümü.

Commit etmez; çağıran (blueprints/analysis_bp.py) sahipleri ve ilanı aynı transaction'da kaydeder.
"""
import json
from decimal import Decimal

from werkzeug.datastructures import MultiDict

from models.crm_models import Contact
from modules.gayrimenkul_sabitleri import (ALT_TURLER, ISINMA, KIMDEN, OZELLIKLER, TAPU_DURUMLARI,
                                          TURLER)
from modules.ilan_hesap import tutar_ayristir
from modules.ilan_servis import gorunur_kontaklar

ARSA_TURLERI = ('arsa', 'tarla')
YAPI_TURLERI = ('konut', 'isyeri', 'bina')

ARSA_ALANLARI = ('ada', 'parsel', 'pafta', 'imar_durumu', 'taks', 'kaks')
YAPI_ALANLARI = ('brut_m2', 'net_m2', 'oda_sayisi', 'banyo_sayisi', 'bulundugu_kat', 'toplam_kat', 'bina_yasi',
                 'isinma', 'esyali', 'site_icinde', 'balkon', 'aidat')
ORTAK_METIN = {'baslik': 200, 'il': 50, 'ilce': 50, 'mahalle': 100, 'koordinatlar': 100}
ORTAK_BOOL = ('krediye_uygun', 'takasli')
YAPI_BOOL = ('esyali', 'site_icinde', 'balkon')
TAMSAYI = ('banyo_sayisi', 'toplam_kat', 'bina_yasi')
ONDALIK = ('metrekare', 'taks', 'kaks', 'brut_m2', 'net_m2', 'aidat')
SWOT_ANAHTARLARI = ('strengths', 'weaknesses', 'opportunities', 'threats')

ETIKETLER = {
    'il': 'İl', 'ilce': 'İlçe', 'mahalle': 'Mahalle', 'ada': 'Ada', 'parsel': 'Parsel', 'metrekare': 'Metrekare',
    'taks': 'TAKS', 'kaks': 'KAKS', 'brut_m2': 'Brüt m²', 'net_m2': 'Net m²', 'oda_sayisi': 'Oda sayısı',
    'banyo_sayisi': 'Banyo sayısı', 'toplam_kat': 'Toplam kat', 'bina_yasi': 'Bina yaşı', 'aidat': 'Aidat',
}
# Sayısal üst sınırlar (sütun hassasiyeti)
SINIRLAR = {'metrekare': (0, 99999999.99), 'brut_m2': (0, 99999999.99), 'net_m2': (0, 99999999.99),
            'aidat': (0, 99999999.99), 'taks': (0, 1), 'kaks': (0, 10),
            'banyo_sayisi': (0, 100), 'toplam_kat': (0, 300), 'bina_yasi': (0, 500)}


def _metin(form, alan, uzunluk=None):
    deger = (form.get(alan) or '').strip()
    if not deger:
        return None
    return deger[:uzunluk] if uzunluk else deger


def _sayi(form, alan, hatalar, zorunlu=False):
    ham = (form.get(alan) or '').strip()
    etiket = ETIKETLER.get(alan, alan)
    if not ham:
        if zorunlu:
            hatalar.append(f"{etiket} alanı zorunludur.")
        return None
    deger = tutar_ayristir(ham)
    if deger is None:
        hatalar.append(f"{etiket} geçerli bir sayı olmalıdır.")
        return None
    alt, ust = SINIRLAR.get(alan, (0, None))
    if deger < alt or (ust is not None and deger > ust):
        hatalar.append(f"{etiket} {alt} ile {ust} arasında olmalıdır." if ust is not None
                       else f"{etiket} negatif olamaz.")
        return None
    if zorunlu and alan in ('metrekare', 'brut_m2') and deger <= 0:
        hatalar.append(f"{etiket} sıfırdan büyük olmalıdır.")
        return None
    if alan in TAMSAYI:
        if deger != int(deger):
            hatalar.append(f"{etiket} tam sayı olmalıdır.")
            return None
        return int(deger)
    return Decimal(str(deger))


def _secim(deger, secenekler):
    return deger if deger in secenekler else None


def _swot(form, hatalar):
    swot = {}
    for anahtar in SWOT_ANAHTARLARI:
        ham = form.get(anahtar) or '[]'
        try:
            liste = json.loads(ham)
        except (TypeError, ValueError):
            liste = None
        if not isinstance(liste, list):
            hatalar.append("SWOT verisi okunamadı.")
            liste = []
        swot[anahtar] = [str(m).strip() for m in liste if str(m).strip()]
    return swot


def formdan_gayrimenkul(form, gayrimenkul):
    """Formu doğrular ve alanları gayrimenkule yazar. Hata listesi döndürür (boşsa geçerli).

    Tür dışı alanlar None yapılır; kaldırılan yatırımcı alanları ve fiyat yazılmaz.
    """
    hatalar = []
    tur = form.get('tur')
    if tur not in {k for k, _ in TURLER}:
        return ["Gayrimenkul türü seçilmelidir."]

    for alan in ('il', 'ilce', 'mahalle'):
        if not (form.get(alan) or '').strip():
            hatalar.append(f"{ETIKETLER[alan]} alanı zorunludur.")

    degerler = {alan: _metin(form, alan, uzunluk) for alan, uzunluk in ORTAK_METIN.items()}
    degerler['notlar'] = _metin(form, 'notlar')
    degerler['tapu_durumu'] = _secim(form.get('tapu_durumu'), TAPU_DURUMLARI)
    degerler['kimden'] = _secim(form.get('kimden'), KIMDEN)
    for alan in ORTAK_BOOL:
        degerler[alan] = bool(form.get(alan))
    for alan in ARSA_ALANLARI + YAPI_ALANLARI:
        degerler[alan] = None

    alt_turler = {k for k, _ in ALT_TURLER.get(tur, [])}
    degerler['alt_tur'] = _secim(form.get('alt_tur'), alt_turler)
    if form.get('alt_tur') and degerler['alt_tur'] is None and alt_turler:
        hatalar.append("Alt tür geçersiz.")

    if tur in ARSA_TURLERI:
        for alan in ('ada', 'parsel'):
            if not (form.get(alan) or '').strip():
                hatalar.append(f"{ETIKETLER[alan]} alanı zorunludur.")
        degerler['ada'] = _metin(form, 'ada', 20)
        degerler['parsel'] = _metin(form, 'parsel', 20)
        degerler['pafta'] = _metin(form, 'pafta', 50)
        degerler['imar_durumu'] = _metin(form, 'imar_durumu', 50)
        degerler['metrekare'] = _sayi(form, 'metrekare', hatalar, zorunlu=True)
        degerler['taks'] = _sayi(form, 'taks', hatalar)
        degerler['kaks'] = _sayi(form, 'kaks', hatalar)
    else:
        degerler['brut_m2'] = _sayi(form, 'brut_m2', hatalar, zorunlu=True)
        degerler['metrekare'] = degerler['brut_m2']
        for alan in ('net_m2', 'aidat') + TAMSAYI:
            degerler[alan] = _sayi(form, alan, hatalar)
        degerler['oda_sayisi'] = _metin(form, 'oda_sayisi', 10)
        if tur == 'konut' and not degerler['oda_sayisi']:
            hatalar.append(f"{ETIKETLER['oda_sayisi']} alanı zorunludur.")
        degerler['bulundugu_kat'] = _metin(form, 'bulundugu_kat', 10)
        degerler['isinma'] = _secim(form.get('isinma'), ISINMA)
        for alan in YAPI_BOOL:
            degerler[alan] = bool(form.get(alan))

    ozellikler = {}
    for baslik, secenekler in OZELLIKLER.items():
        secilen = set(form.getlist(f'oz_{baslik}'))
        ozellikler[baslik] = [s for s in secenekler if s in secilen]
    swot = _swot(form, hatalar)

    if hatalar:
        return hatalar

    gayrimenkul.tur = tur
    for alan, deger in degerler.items():
        setattr(gayrimenkul, alan, deger)
    gayrimenkul.ozellikler = ozellikler
    # Eski ekranlar ve raporlar altyapıyı ayrı sütundan okur
    gayrimenkul.altyapi = json.dumps(ozellikler['altyapi'])
    gayrimenkul.swot_analizi = json.dumps(swot, ensure_ascii=False)
    return []


def sahipler_formdan(form):
    """sahip_contact_id[] / sahip_hisse[] paralel listeleri ve sahip_irtibat → sahipleri_kaydet girdisi."""
    idler = form.getlist('sahip_contact_id[]') or form.getlist('sahip_contact_id')
    hisseler = form.getlist('sahip_hisse[]') or form.getlist('sahip_hisse')
    irtibat = (form.get('sahip_irtibat') or '').strip()
    sahipler = []
    for i, cid in enumerate(idler):
        cid = (cid or '').strip()
        if not cid:
            continue
        sahipler.append({'contact_id': cid, 'hisse': hisseler[i] if i < len(hisseler) else None,
                         'irtibat': cid == irtibat})
    return sahipler


def ilan_verisi(form, gayrimenkul):
    """'Hemen ilana çıkar' alanlarından ilan_kaydet verisi (tek gayrimenkullü, pazarlamada)."""
    return {
        'baslik': '',
        'aciklama': None,
        'teklif_tipi': form.get('ilan_teklif_tipi'),
        'durum': 'pazarlamada',
        'fiyat': form.get('ilan_fiyat'),
        'kira': form.get('ilan_kira'),
        'depozito': form.get('ilan_depozito'),
        'sahip_payi_yuzde': form.get('ilan_sahip_payi_yuzde'),
        'gayrimenkuller': [{'id': gayrimenkul.id}],
        'ana_gayrimenkul_id': gayrimenkul.id,
        'emsaller': [],
    }


# ---------------------------------------------------------------- formu yeniden doldurma

def _yazi(deger):
    if deger is None:
        return ''
    if isinstance(deger, bool):
        return '1' if deger else ''
    if isinstance(deger, Decimal):
        return format(deger.normalize(), 'f').replace('.', ',')
    if isinstance(deger, float):
        return _yazi(Decimal(str(deger)))
    return str(deger)


def _json(deger, varsayilan):
    if isinstance(deger, str):
        try:
            deger = json.loads(deger)
        except ValueError:
            return varsayilan
    return deger if deger is not None else varsayilan


def form_verisi(gayrimenkul):
    """Kayıttan, formun POST'ta göndereceği biçimde bir MultiDict üretir (düzenleme formu için)."""
    v = MultiDict()
    for alan in (('tur', 'alt_tur', 'notlar', 'tapu_durumu', 'kimden', 'metrekare') + tuple(ORTAK_METIN)
                 + ORTAK_BOOL + ARSA_ALANLARI + YAPI_ALANLARI):
        v[alan] = _yazi(getattr(gayrimenkul, alan))
    v['tur'] = gayrimenkul.tur or 'arsa'
    ozellikler = _json(gayrimenkul.ozellikler, {})
    if not isinstance(ozellikler, dict):
        ozellikler = {}
    for baslik in OZELLIKLER:
        v.setlist(f'oz_{baslik}', list(ozellikler.get(baslik) or []))
    if not ozellikler.get('altyapi') and gayrimenkul.altyapi:
        from modules.rapor.model import parse_altyapi
        v.setlist('oz_altyapi', parse_altyapi(gayrimenkul.altyapi))
    from modules.rapor.model import parse_swot
    swot = parse_swot(gayrimenkul.swot_analizi)
    for anahtar in SWOT_ANAHTARLARI:
        v[anahtar] = json.dumps(swot.get(anahtar, []), ensure_ascii=False)
    sahiplikler = list(gayrimenkul.sahiplikler)
    v.setlist('sahip_contact_id[]', [str(s.contact_id) for s in sahiplikler])
    v.setlist('sahip_hisse[]', [s.hisse or '' for s in sahiplikler])
    irtibat = next((s.contact_id for s in sahiplikler if s.irtibat), None)
    if irtibat is not None:
        v['sahip_irtibat'] = str(irtibat)
    return v


def kontak_json(c):
    return {'id': c.id, 'ad': f"{c.first_name} {c.last_name}".strip(), 'telefon': c.phone or ''}


def sahip_satirlari(veri, user, gayrimenkul=None):
    """Formdaki sahip seçimlerini ad/telefonla şablona hazırlar.

    Görünür kontaklar ve (düzenlemede) gayrimenkulün mevcut sahipleri gösterilir; mevcut sahip
    düzenleyene görünmüyorsa satır 'salt_okunur' işaretlenir (kaydederken korunur).
    """
    sahipler = sahipler_formdan(veri)
    idler = set()
    for s in sahipler:
        try:
            idler.add(int(s['contact_id']))
        except ValueError:
            continue
    gorunur = {c.id: c for c in gorunur_kontaklar(user).filter(Contact.id.in_(idler))} if idler else {}
    mevcut = {}
    if gayrimenkul is not None and gayrimenkul.id is not None:
        mevcut = {sh.contact_id: sh.contact for sh in gayrimenkul.sahiplikler}
    satirlar = []
    for s in sahipler:
        try:
            cid = int(s['contact_id'])
        except ValueError:
            continue
        c = gorunur.get(cid) or mevcut.get(cid)
        if c is None:
            continue
        satir = kontak_json(c)
        satir.update(hisse=s['hisse'] or '', irtibat=s['irtibat'], salt_okunur=cid not in gorunur)
        satirlar.append(satir)
    return satirlar
