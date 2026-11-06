# -*- coding: utf-8 -*-
"""Rapor (PDF / Word / PPTX) üretimi için ortak veri hazırlama.

Tüm rapor rotaları DocumentGenerator'a gönderilecek veriyi buradan alır; böylece
her format aynı arsa verisini, aynı analiz özetini ve gerçek kullanıcı bilgisini kullanır.
"""
import json
from datetime import datetime

from modules.analiz import ArsaAnalizci

SWOT_KEYS = ('strengths', 'weaknesses', 'opportunities', 'threats')


def tr_number(value, decimals=0):
    """Sayıyı Türkçe biçimde yazar: 1234567.5 -> '1.234.567,50'."""
    try:
        text = f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return '-'
    return text.replace(',', 'X').replace('.', ',').replace('X', '.')


def tr_currency(value, decimals=0):
    return f"{tr_number(value, decimals)} TL"


def _parse_json(value, default):
    """Veritabanındaki JSON alanı hem string hem de çözülmüş nesne olarak gelebilir."""
    if value is None or value == '':
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def parse_altyapi(value):
    data = _parse_json(value, [])
    if isinstance(data, dict):  # {'yol': True, ...} biçimi
        data = [k for k, v in data.items() if v]
    if not isinstance(data, list):
        return []
    return [str(item).strip().lower() for item in data if str(item).strip()]


def parse_swot(value):
    data = _parse_json(value, {})
    if not isinstance(data, dict):
        data = {}
    result = {}
    for key in SWOT_KEYS:
        items = data.get(key) or []
        if isinstance(items, str):
            items = [items]
        result[key] = [str(i).strip() for i in items if str(i).strip()]
    return result


def _clean(value):
    """None / boş değerleri rapora '-' olarak yansıt."""
    if value is None:
        return '-'
    text = str(value).strip()
    return text if text and text.lower() != 'none' else '-'


def to_local_time(dt, tz_name='Europe/Istanbul'):
    """Veritabanındaki UTC zamanı kullanıcının saat dilimine çevirir."""
    if not isinstance(dt, datetime):
        return dt
    try:
        import pytz
        tz = pytz.timezone(tz_name or 'Europe/Istanbul')
        aware = dt if dt.tzinfo else pytz.utc.localize(dt)
        return aware.astimezone(tz).replace(tzinfo=None)
    except Exception:
        return dt


def build_profile_info(user, created_at=None):
    full_name = ' '.join(p for p in [(user.ad or '').strip(), (user.soyad or '').strip()] if p)
    return {
        'ad': user.ad or '', 'soyad': user.soyad or '',
        'ad_soyad': full_name or user.email,
        'unvan': _clean(user.unvan), 'firma': _clean(user.firma),
        'email': _clean(user.email), 'telefon': _clean(user.telefon), 'adres': _clean(user.adres),
        'profil_foto': user.profil_foto,
        'created_at': to_local_time(created_at, getattr(user, 'timezone', None)),
    }


def build_analysis_summary(arsa):
    """ArsaAnalizci ile hesap yapar, Türkçe biçimli özet metinleri ve sayısal metrikleri döndürür."""
    metrekare = float(arsa['metrekare'] or 0)
    fiyat = float(arsa['fiyat'] or 0)
    bolge_fiyat = float(arsa['bolge_fiyat'] or 0)
    if metrekare <= 0 or fiyat <= 0:
        return {
            'temel_ozet': 'Alan veya fiyat bilgisi eksik olduğu için değerlendirme yapılamadı.',
            'yatirim_ozet': '-', 'uygunluk_ozet': '-', 'tavsiyeler': arsa.get('notlar') or '-',
        }, {}

    analizci = ArsaAnalizci()
    metrics = analizci.analiz_et({
        'metrekare': metrekare, 'fiyat': fiyat,
        # Bölge fiyatı girilmemişse arsanın kendi m² fiyatı baz alınır (sıfıra bölmeyi önler)
        'bolge_fiyat': bolge_fiyat if bolge_fiyat > 0 else fiyat / metrekare,
        'imar_durumu': arsa.get('imar_durumu') or '',
        'altyapi': arsa.get('altyapi[]', []),
        'konum': {'il': arsa.get('il'), 'ilce': arsa.get('ilce'), 'mahalle': arsa.get('mahalle')},
    })

    m2_fiyat = metrics['metrekare_fiyat']
    fark = metrics['bolge_karsilastirma']
    konum = ', '.join(p for p in [arsa.get('mahalle'), arsa.get('ilce'), arsa.get('il')] if p)
    temel = (f"{konum} konumundaki {tr_number(metrekare)} m² büyüklüğündeki "
             f"{(arsa.get('imar_durumu') or '').lower() or 'belirtilmemiş'} imarlı arsanın fiyatı "
             f"{tr_currency(fiyat)}, metrekare fiyatı {tr_currency(m2_fiyat)}'dir.")
    if bolge_fiyat > 0:
        yon = 'altındadır' if fark < 0 else 'üzerindedir'
        temel += (f" Bölge ortalaması olan {tr_currency(bolge_fiyat)}/m² ile karşılaştırıldığında "
                  f"%{tr_number(abs(fark), 1)} {yon}." if abs(fark) >= 0.05 else
                  f" Fiyat, bölge ortalaması olan {tr_currency(bolge_fiyat)}/m² ile aynı seviyededir.")
    else:
        temel += " Bölge ortalama fiyatı girilmediği için karşılaştırma yapılamadı."

    deg = metrics['yatirim_degerlendirmesi']
    yatirim = (f"Tahmini yıllık değer artış potansiyeli %{tr_number(metrics['potansiyel_getiri'], 1)}. "
               f"{deg['oneri']} {deg['fiyat_degerlendirme'] if bolge_fiyat > 0 else ''} "
               f"{deg['yatirim_suresi_aciklama']}").replace('  ', ' ').strip()
    uygunluk = (f"Uygunluk puanı: {tr_number(metrics['uygunluk_puani'], 0)}/100. Puan; imar durumu, arsa büyüklüğü, "
                f"bölge fiyatına göre konum ve altyapı durumu dikkate alınarak hesaplanmıştır.")
    tavsiye = analizci.ozetle({**metrics, 'konum': {'il': '', 'ilce': '', 'mahalle': ''}})['tavsiyeler']
    if arsa.get('notlar'):
        tavsiye = f"{arsa['notlar'].strip()}\n{tavsiye}"
    return {'temel_ozet': temel, 'yatirim_ozet': yatirim, 'uygunluk_ozet': uygunluk, 'tavsiyeler': tavsiye}, metrics


def build_report_inputs(analiz, user, detail_url=None):
    """DocumentGenerator(arsa_data, analiz_ozeti, ..., profile_info=...) için girdileri hazırlar."""
    swot = parse_swot(analiz.swot_analizi)
    arsa = {
        'id': analiz.id,
        'il': analiz.il or '', 'ilce': analiz.ilce or '', 'mahalle': analiz.mahalle or '',
        'ada': analiz.ada or '-', 'parsel': analiz.parsel or '-', 'pafta': analiz.pafta or '-',
        'koordinatlar': analiz.koordinatlar or '',
        'metrekare': float(analiz.metrekare or 0), 'fiyat': float(analiz.fiyat or 0),
        'bolge_fiyat': float(analiz.bolge_fiyat or 0),
        'taks': float(analiz.taks) if analiz.taks is not None else 0.3,
        'kaks': float(analiz.kaks) if analiz.kaks is not None else 1.5,
        'imar_durumu': analiz.imar_durumu or '',
        'notlar': analiz.notlar or '',
        'altyapi[]': parse_altyapi(analiz.altyapi),
        'swot': swot,
        'created_at': analiz.created_at,
        'detail_url': detail_url,
        **swot,
    }
    ozet, metrics = build_analysis_summary(arsa)
    arsa['metrics'] = metrics
    profile = build_profile_info(user, created_at=analiz.created_at or datetime.utcnow())
    return arsa, ozet, profile
