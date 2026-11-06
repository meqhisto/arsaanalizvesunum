# -*- coding: utf-8 -*-
"""Rapor modeli: PDF, Word ve PowerPoint çıktılarının ortak kullandığı veriyi hazırlar.

Çiziciler (pdf.py, word.py, pptx_.py) hesap yapmaz; her şey burada bir kez hesaplanır.
"""
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from modules.analiz import ArsaAnalizci

SWOT_KEYS = ('strengths', 'weaknesses', 'opportunities', 'threats')
SWOT_TITLES = {'strengths': 'Güçlü Yönler', 'weaknesses': 'Zayıf Yönler',
               'opportunities': 'Fırsatlar', 'threats': 'Tehditler'}
ALTYAPI_ETIKETLERI = (('yol', 'Yol'), ('elektrik', 'Elektrik'), ('su', 'Su'),
                      ('dogalgaz', 'Doğalgaz'), ('kanalizasyon', 'Kanalizasyon'))
PROJEKSIYON_YIL = 5
IMAGE_EXTS = ('.jpg', '.jpeg', '.png')


# ---------------------------------------------------------------- biçimlendirme
def tr_number(value, decimals=0):
    """1234567.5 -> '1.234.567,50' (Türkçe binlik/ondalık ayırıcı)."""
    try:
        text = f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return '-'
    return text.replace(',', 'X').replace('.', ',').replace('X', '.')


def tr_currency(value, decimals=0):
    return f"{tr_number(value, decimals)} TL"


def tr_short_currency(value):
    """Grafik etiketleri için kısa para: 7.350.000 -> '7,35 Mn TL'."""
    v = float(value or 0)
    if abs(v) >= 1e9:
        return f"{tr_number(v / 1e9, 2)} Mr TL"
    if abs(v) >= 1e6:
        return f"{tr_number(v / 1e6, 2)} Mn TL"
    if abs(v) >= 1e3:
        return f"{tr_number(v / 1e3, 0)} B TL"
    return tr_currency(v)


def to_local_time(dt, tz_name='Europe/Istanbul'):
    if not isinstance(dt, datetime):
        return dt
    try:
        import pytz
        tz = pytz.timezone(tz_name or 'Europe/Istanbul')
        aware = dt if dt.tzinfo else pytz.utc.localize(dt)
        return aware.astimezone(tz).replace(tzinfo=None)
    except Exception:
        return dt


def ascii_slug(text):
    table = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')
    return re.sub(r'[^A-Za-z0-9]+', '_', (text or '').translate(table)).strip('_') or 'rapor'


# ---------------------------------------------------------------- veri çözme
def _parse_json(value, default):
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
    if isinstance(data, dict):
        data = [k for k, v in data.items() if v]
    if not isinstance(data, list):
        return []
    return [str(i).strip().lower() for i in data if str(i).strip()]


def parse_swot(value):
    data = _parse_json(value, {})
    if not isinstance(data, dict):
        data = {}
    out = {}
    for key in SWOT_KEYS:
        items = data.get(key) or []
        if isinstance(items, str):
            items = [items]
        out[key] = [str(i).strip() for i in items if str(i).strip()]
    return out


def parse_coordinates(text):
    """'40.1012, 26.4085' veya '40,1012 26,4085' -> (40.1012, 26.4085). Geçersizse None."""
    if not text:
        return None
    nums = re.findall(r'-?\d+(?:[.,]\d+)?', str(text))
    if len(nums) < 2:
        return None
    try:
        lat, lon = (float(n.replace(',', '.')) for n in nums[:2])
    except ValueError:
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def _clean(value):
    if value is None:
        return '-'
    text = str(value).strip()
    return text if text and text.lower() != 'none' else '-'


# ---------------------------------------------------------------- model
@dataclass
class Brand:
    name: str
    web: str = ''
    logo_path: Optional[str] = None
    primary: str = '#1B3A5C'   # koyu lacivert
    accent: str = '#E08A1E'    # turuncu vurgu


@dataclass
class Advisor:
    ad_soyad: str
    unvan: str
    firma: str
    email: str
    telefon: str
    adres: str
    photo_path: Optional[str] = None


@dataclass
class Scenario:
    ad: str
    oran: float
    degerler: List[float]  # yıl 0..N toplam değer


@dataclass
class ReportModel:
    analiz_id: int
    baslik: str
    konum: str
    il: str
    ilce: str
    mahalle: str
    ada: str
    parsel: str
    pafta: str
    koordinat: Optional[tuple]
    metrekare: float
    imar_durumu: str
    taks: float
    kaks: float
    fiyat: float
    m2_fiyat: float
    bolge_m2_fiyat: float          # 0 ise girilmemiş
    bolge_fark: Optional[float]    # % (negatif = bölgeden ucuz)
    taban_alani: float
    insaat_alani: float
    kat_sayisi: float
    altyapi: List[tuple]           # [(etiket, var_mi)]
    swot: dict
    puan: float
    puan_detay: List[dict]
    yillik_artis: float            # baz senaryo oranı (%)
    artis_kaynagi: str             # 'kullanıcı' / 'model'
    senaryolar: List[Scenario]
    temel_ozet: str
    yatirim_ozet: str
    tavsiyeler: List[str]
    notlar: str
    fotograflar: List[str]
    tarih: datetime
    detail_url: str
    maps_url: str
    advisor: Advisor
    brand: Brand
    extras: dict = field(default_factory=dict)

    @property
    def ada_parsel(self):
        """'Ada 1245 / Parsel 18'; bilgi yoksa boş."""
        if self.ada == '-' and self.parsel == '-':
            return ''
        return f"Ada {self.ada} / Parsel {self.parsel}"

    def satir(self, *parcalar, ayirici='  ·  '):
        """Boş parçaları atlayarak birleştirir."""
        return ayirici.join(p for p in parcalar if p)

    @property
    def taks_kaks(self):
        text = f"{tr_number(self.taks, 2)} / {tr_number(self.kaks, 2)}"
        return text + (' (varsayılan)' if self.extras.get('taks_varsayilan') else '')

    @property
    def altyapi_sayisi(self):
        return sum(1 for _, var in self.altyapi if var)

    @property
    def puan_etiketi(self):
        if self.puan >= 80:
            return 'Çok uygun'
        if self.puan >= 65:
            return 'Uygun'
        if self.puan >= 50:
            return 'Orta'
        return 'Dikkatli değerlendirilmeli'


def _brand_for(user, base_dir):
    """Marka bilgisi: ortam değişkeni > kullanıcının firması > platform adı."""
    logo = os.environ.get('REPORT_LOGO_PATH') or os.path.join(base_dir, 'static', 'logo.png')
    if logo and not os.path.isabs(logo):
        logo = os.path.join(base_dir, logo)
    firma = (user.firma or '').strip()
    return Brand(
        name=os.environ.get('REPORT_BRAND_NAME') or firma or 'Arsa Analiz Platformu',
        web=os.environ.get('REPORT_BRAND_WEB', ''),
        logo_path=logo if logo and os.path.exists(logo) else None,
        primary=os.environ.get('REPORT_PRIMARY_COLOR', '#1B3A5C'),
        accent=os.environ.get('REPORT_ACCENT_COLOR', '#E08A1E'),
    )


def _photos_for(analiz, upload_folder):
    paths = []
    try:
        from models.arsa_models import AnalizMedya
        kayitlar = AnalizMedya.query.filter_by(analiz_id=analiz.id).order_by(AnalizMedya.uploaded_at).all()
        for k in kayitlar:
            p = os.path.join(upload_folder, k.filename)
            if p.lower().endswith(IMAGE_EXTS) and os.path.exists(p):
                paths.append(p)
    except Exception:
        pass
    if not paths:  # Eski kayıtlar: klasördeki resimler
        folder = os.path.join(upload_folder, str(analiz.id))
        if os.path.isdir(folder):
            paths = sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTS))
    return paths[:8]


def _scenarios(fiyat, baz_oran):
    oranlar = [('Temkinli', max(baz_oran - 5, 0)), ('Beklenen', baz_oran), ('İyimser', baz_oran + 5)]
    out = []
    for ad, oran in oranlar:
        out.append(Scenario(ad, oran, [fiyat * (1 + oran / 100) ** y for y in range(PROJEKSIYON_YIL + 1)]))
    return out


def build_report_model(analiz, user, detail_url='', upload_folder=None, base_dir=None):
    base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    upload_folder = upload_folder or os.path.join(base_dir, 'static', 'uploads')

    metrekare = float(analiz.metrekare or 0)
    fiyat = float(analiz.fiyat or 0)
    bolge = float(analiz.bolge_fiyat or 0)
    taks = float(analiz.taks) if analiz.taks is not None else 0.3
    kaks = float(analiz.kaks) if analiz.kaks is not None else 1.5
    altyapi_list = parse_altyapi(analiz.altyapi)
    m2_fiyat = fiyat / metrekare if metrekare else 0

    analizci = ArsaAnalizci()
    metrics = {}
    if metrekare > 0 and fiyat > 0:
        metrics = analizci.analiz_et({
            'metrekare': metrekare, 'fiyat': fiyat,
            'bolge_fiyat': bolge if bolge > 0 else m2_fiyat,
            'bolge_fiyat_girildi': bolge > 0,
            'imar_durumu': analiz.imar_durumu or '', 'altyapi': altyapi_list,
            'konum': {'il': analiz.il, 'ilce': analiz.ilce, 'mahalle': analiz.mahalle},
        })
    bolge_fark = metrics.get('bolge_karsilastirma') if bolge > 0 else None
    model_oran = float(metrics.get('potansiyel_getiri') or 0)
    kullanici_oran = getattr(analiz, 'deger_artis_orani', None)
    if kullanici_oran is not None:
        yillik, kaynak = float(kullanici_oran), 'kullanıcı'
    else:
        yillik, kaynak = model_oran, 'model'

    konum = ', '.join(p for p in [analiz.mahalle, analiz.ilce, analiz.il] if p)
    imar = (analiz.imar_durumu or '').strip()

    # Metinler
    temel = (f"{konum} konumundaki {tr_number(metrekare)} m² büyüklüğündeki "
             f"{imar.lower() + ' imarlı ' if imar else ''}arsanın fiyatı {tr_currency(fiyat)}, "
             f"metrekare fiyatı {tr_currency(m2_fiyat)}.")
    if bolge_fark is not None:
        if abs(bolge_fark) < 0.05:
            temel += f" Bu fiyat bölge ortalamasıyla ({tr_currency(bolge)}/m²) aynı seviyededir."
        else:
            yon = 'altında' if bolge_fark < 0 else 'üzerinde'
            temel += (f" Bölge ortalaması {tr_currency(bolge)}/m² olup arsa bu ortalamanın "
                      f"%{tr_number(abs(bolge_fark), 1)} {yon} fiyatlanmıştır.")
    else:
        temel += " Bölge ortalama fiyatı girilmediği için karşılaştırma yapılmamıştır."

    senaryolar = _scenarios(fiyat, yillik)
    beklenen_son = senaryolar[1].degerler[-1]
    yatirim = (f"Yıllık %{tr_number(yillik, 1)} değer artışı varsayımıyla ({'danışman girdisi' if kaynak == 'kullanıcı' else 'model tahmini'}) "
               f"arsanın {PROJEKSIYON_YIL} yıl sonraki tahmini değeri {tr_currency(beklenen_son)} olur. "
               f"Temkinli senaryoda {tr_currency(senaryolar[0].degerler[-1])}, iyimser senaryoda "
               f"{tr_currency(senaryolar[2].degerler[-1])} öngörülmektedir.")
    if metrics:
        yatirim += f" {metrics['yatirim_degerlendirmesi']['yatirim_suresi_aciklama']}"

    tavsiyeler = []
    if bolge_fark is not None:
        if bolge_fark <= -10:
            tavsiyeler.append('Fiyat bölge ortalamasının belirgin şekilde altında; hızlı karar avantaj sağlayabilir.')
        elif bolge_fark < 0:
            tavsiyeler.append('Fiyat bölge ortalamasının altında; pazarlık payı sınırlı olabilir.')
        elif bolge_fark > 10:
            tavsiyeler.append('Fiyat bölge ortalamasının belirgin şekilde üzerinde; pazarlık veya emsal araştırması önerilir.')
        else:
            tavsiyeler.append('Fiyat bölge ortalamasına yakın; emsal satışlarla teyit edilmesi önerilir.')
    eksik = [etiket for kod, etiket in ALTYAPI_ETIKETLERI if kod not in altyapi_list]
    if eksik:
        tavsiyeler.append(f"Eksik altyapı ({', '.join(eksik).lower()}) için belediyeden bağlantı planı ve maliyeti sorulmalı.")
    tavsiyeler.append('Tapu kaydı, imar durumu ve olası şerhler resmi kurumlardan güncel olarak teyit edilmelidir.')

    tarih = to_local_time(analiz.created_at or datetime.utcnow(), getattr(user, 'timezone', None))
    coord = parse_coordinates(analiz.koordinatlar)
    maps_url = f"https://www.google.com/maps?q={coord[0]},{coord[1]}" if coord else ''

    photo = None
    if user.profil_foto:
        cand = os.path.join(upload_folder, user.profil_foto)
        photo = cand if os.path.exists(cand) else None
    advisor = Advisor(
        ad_soyad=' '.join(p for p in [(user.ad or '').strip(), (user.soyad or '').strip()] if p) or user.email,
        unvan=_clean(user.unvan), firma=_clean(user.firma), email=_clean(user.email),
        telefon=_clean(user.telefon), adres=_clean(user.adres), photo_path=photo,
    )

    return ReportModel(
        analiz_id=analiz.id,
        baslik='Arsa Değerleme ve Yatırım Raporu',
        konum=konum, il=analiz.il or '', ilce=analiz.ilce or '', mahalle=analiz.mahalle or '',
        ada=analiz.ada or '-', parsel=analiz.parsel or '-', pafta=analiz.pafta or '-',
        koordinat=coord, metrekare=metrekare, imar_durumu=imar or '-', taks=taks, kaks=kaks,
        fiyat=fiyat, m2_fiyat=m2_fiyat, bolge_m2_fiyat=bolge, bolge_fark=bolge_fark,
        taban_alani=metrekare * taks, insaat_alani=metrekare * kaks,
        kat_sayisi=(kaks / taks) if taks else 0,
        altyapi=[(etiket, kod in altyapi_list) for kod, etiket in ALTYAPI_ETIKETLERI],
        swot=parse_swot(analiz.swot_analizi),
        puan=float(metrics.get('uygunluk_puani') or 0), puan_detay=metrics.get('uygunluk_detay') or [],
        yillik_artis=yillik, artis_kaynagi=kaynak, senaryolar=senaryolar,
        temel_ozet=temel, yatirim_ozet=yatirim, tavsiyeler=tavsiyeler,
        notlar=(analiz.notlar or '').strip(),
        fotograflar=_photos_for(analiz, upload_folder),
        tarih=tarih, detail_url=detail_url, maps_url=maps_url,
        advisor=advisor, brand=_brand_for(user, base_dir),
        extras={'taks_varsayilan': analiz.taks is None or analiz.kaks is None},
    )
