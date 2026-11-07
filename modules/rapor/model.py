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
from modules.gayrimenkul_sabitleri import ALTYAPI_ETIKETLERI

SWOT_KEYS = ('strengths', 'weaknesses', 'opportunities', 'threats')
SWOT_TITLES = {'strengths': 'Güçlü Yönler', 'weaknesses': 'Zayıf Yönler',
               'opportunities': 'Fırsatlar', 'threats': 'Tehditler'}
ARSA_TURLERI = ('arsa', 'tarla')
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
class ReportModel:
    analiz_id: int                 # ana gayrimenkulün id'si
    baslik: str
    kod: str                       # ilan kodu; tanıtım raporunda ''
    teklif_tipi: Optional[str]     # satilik / kiralik / kat_karsiligi; tanıtım raporunda None
    teklif_etiketi: str
    tur: str                       # arsa, tarla, konut, isyeri, bina
    tur_etiketi: str               # alt tür varsa onun etiketi
    konum: str
    il: str
    ilce: str
    mahalle: str
    ada: str
    parsel: str
    pafta: str
    koordinat: Optional[tuple]
    metrekare: float               # toplam alan (çok parselde parsellerin toplamı)
    parseller: List[dict]          # [{baslik, ada, parsel, m2, imar, kaks}]
    tur_bilgileri: List[tuple]     # [(etiket, metin)] — yalnız dolu türe özel alanlar
    ozellik_gruplari: List[tuple]  # [(başlık, [etiket, ...])]
    # Arsa / tarla (ana gayrimenkul)
    imar_durumu: str
    taks: float
    kaks: float
    taban_alani: float
    insaat_alani: float
    kat_sayisi: float
    altyapi: List[tuple]           # [(etiket, var_mi)]
    puan: float                    # yalnız tek parselli arsa/tarla; diğerlerinde 0
    puan_detay: List[dict]
    # Fiyat ve emsal analizi (tanıtım raporunda boş)
    fiyat_satirlari: List[tuple]   # [(etiket, metin)]
    tutar: Optional[float]         # satılıkta fiyat, kiralıkta aylık kira
    istenen: Optional[float]       # m² fiyatı / m² kira / sahip payı %
    emsaller: List[dict]           # [{konum, m2, deger, m2_fiyat}] — biçimlenmiş metinler
    bolge: Optional[float]
    bolge_kaynak: str              # 'emsal' / 'elle' / 'yok'
    emsal_sayisi: int
    fark: Optional[float]          # % (negatif = bölgenin altında)
    konum_etiketi: Optional[str]
    toplam_m2: float
    insaat_hakki: Optional[float]
    sahibe_dusen_m2: Optional[float]
    fiyat_ozet: str
    swot: dict
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
    def arsa_mi(self):
        return self.tur in ARSA_TURLERI

    @property
    def cok_parsel(self):
        return len(self.parseller) > 1

    @property
    def tanitim(self):
        return self.teklif_tipi is None

    @property
    def parsel_birimi(self):
        """Çok kayıtlı ilanda birim: hepsi arsa/tarla ise 'parsel', değilse 'gayrimenkul'."""
        return 'parsel' if self.extras.get('hepsi_arsa') else 'gayrimenkul'

    @property
    def ada_parsel(self):
        """'Ada 1245 / Parsel 18'; çok parselde '4 parsel'; bilgi yoksa boş."""
        if self.cok_parsel:
            return f"{len(self.parseller)} {self.parsel_birimi}"
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

    @property
    def birim(self):
        """Karşılaştırılan değerin birimi: 'TL/m²' ya da '%'."""
        return '%' if self.teklif_tipi == 'kat_karsiligi' else 'TL/m²'

    def deger_metni(self, deger):
        """İstenen / bölge değeri: '12.500 TL/m²' ya da '%45'."""
        if deger is None:
            return '-'
        if self.teklif_tipi == 'kat_karsiligi':
            return f"%{sayi(deger)}"
        return f"{tr_currency(deger)}/m²"

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


def tr_lower(text):
    return (text or '').replace('İ', 'i').replace('I', 'ı').lower()


def sayi(deger, ondalik=2):
    """Gereksiz ondalık sıfırları atılmış Türkçe sayı: 2400 -> '2.400', 1.5 -> '1,5'."""
    from modules.ilan_hesap import sayi_metni
    return sayi_metni(deger, ondalik) or '-'


def _f(deger):
    return float(deger) if deger is not None else None


def _tur_etiketi(g):
    from modules.gayrimenkul_sabitleri import ALT_TURLER, TURLER, etiket
    tur = g.tur or 'arsa'
    if g.alt_tur:
        return etiket(ALT_TURLER.get(tur, []), g.alt_tur)
    return etiket(TURLER, tur)


# detay_bilgileri satırlarından rapora ayrıca girenler (konum, arsa/imar tablosu)
_GENEL_ETIKETLER = {'Tür', 'Alt tür', 'Konum', 'Koordinatlar', 'Ada', 'Parsel', 'Pafta', 'Yüzölçümü',
                    'İmar durumu', 'TAKS', 'KAKS'}


def _parsel(g):
    return {'baslik': g.baslik_metni, 'ada': g.ada or '-', 'parsel': g.parsel or '-',
            'm2': float(g.metrekare or 0), 'imar': (g.imar_durumu or '').strip() or '-',
            'kaks': _f(g.kaks)}


def _emsal_satirlari(ilan):
    kat = ilan.teklif_tipi == 'kat_karsiligi'
    satirlar = []
    for e in ilan.emsaller:
        m2, fiyat, pay = _f(e.m2), _f(e.fiyat), _f(e.pay_yuzde)
        if kat:
            deger = f"%{sayi(pay)}" if pay is not None else '-'
            m2_fiyat = '-'
        else:
            deger = tr_currency(fiyat) if fiyat is not None else '-'
            m2_fiyat = f"{tr_currency(fiyat / m2)}/m²" if fiyat is not None and m2 else '-'
        satirlar.append({'konum': (e.konum or '').strip() or '-', 'm2': f"{sayi(m2)} m²" if m2 else '-',
                         'deger': deger, 'm2_fiyat': m2_fiyat})
    return satirlar


def _fiyat_satirlari(ilan, oz):
    from modules.gayrimenkul_sabitleri import TEVHID, etiket
    tip = ilan.teklif_tipi
    satirlar = []
    if tip == 'satilik':
        satirlar.append(('İstenen fiyat', tr_currency(ilan.fiyat) if ilan.fiyat is not None else '-'))
        if oz['istenen'] is not None:
            satirlar.append(('m² fiyatı', f"{tr_currency(oz['istenen'])}/m²"))
    elif tip == 'kiralik':
        satirlar.append(('Aylık kira', tr_currency(ilan.kira) if ilan.kira is not None else '-'))
        if ilan.depozito is not None:
            satirlar.append(('Depozito', tr_currency(ilan.depozito)))
        if oz['istenen'] is not None:
            satirlar.append(('m² kira', f"{tr_currency(oz['istenen'])}/m²"))
    else:
        pay = ilan.sahip_payi_yuzde
        satirlar.append(('Arsa sahibi payı', f"%{sayi(pay)}" if pay is not None else '-'))
        if ilan.ek_nakit is not None:
            satirlar.append(('Ek nakit', tr_currency(ilan.ek_nakit)))
        if ilan.teslim_suresi_ay is not None:
            satirlar.append(('Teslim süresi', f"{sayi(ilan.teslim_suresi_ay)} ay"))
        teminat = ' · '.join(p for p in ((ilan.teminat_turu or '').strip(),
                                          tr_currency(ilan.teminat_tutari) if ilan.teminat_tutari is not None else '')
                             if p)
        if teminat:
            satirlar.append(('Teminat', teminat))
        if ilan.tevhid_durumu:
            satirlar.append(('Tevhid', etiket(TEVHID, ilan.tevhid_durumu)))
        if oz['toplam_m2']:
            satirlar.append(('Toplam arsa alanı', f"{sayi(oz['toplam_m2'])} m²"))
        elle = ilan.insaat_alani_elle is not None
        if oz['insaat_hakki'] is not None:
            satirlar.append((f"İnşaat hakkı ({'elle' if elle else 'tahmini'})", f"{sayi(oz['insaat_hakki'])} m²"))
        if oz['sahibe_dusen_m2'] is not None:
            satirlar.append(('Arsa sahibine düşen (tahmini)', f"{sayi(oz['sahibe_dusen_m2'])} m²"))
    return satirlar


def _kaynak_metni(oz):
    return f"{oz['emsal_sayisi']} emsal" if oz['bolge_kaynak'] == 'emsal' else 'elle girildi'


def _fiyat_ozeti(ilan, oz, konum, tanim):
    tip = ilan.teklif_tipi
    fark = oz['fark']
    if tip == 'kat_karsiligi':
        n = len(ilan.gayrimenkuller)
        metin = (f"{n} parsel, toplam {sayi(oz['toplam_m2'])} m² arsa için arsa sahibi "
                 f"%{sayi(ilan.sahip_payi_yuzde)} pay talep ediyor")
        if oz['sahibe_dusen_m2'] is not None:
            metin += f"; tahmini {sayi(oz['sahibe_dusen_m2'])} m² inşaat alanına karşılık gelir."
        else:
            metin += "; KAKS bilgisi eksik olduğundan inşaat alanı hesaplanamadı."
        if oz['bolge'] is not None:
            metin += f" Bölge emsallerinde ortalama pay %{sayi(oz['bolge'])} ({_kaynak_metni(oz)})"
            if fark is not None and abs(fark) >= 0.05:
                yon = 'altında' if fark < 0 else 'üzerinde'
                metin += f"; talep bu ortalamanın %{tr_number(abs(fark), 1)} {yon} — {oz['konum']}."
            else:
                metin += f"; talep bu ortalamayla aynı seviyede — {oz['konum'] or 'Piyasa seviyesinde'}."
        return metin

    kira = tip == 'kiralik'
    tutar = ilan.kira if kira else ilan.fiyat
    metin = (f"{konum} konumundaki {tanim} için istenen {'aylık kira' if kira else 'fiyat'} "
             f"{tr_currency(tutar) if tutar is not None else '-'}")
    if oz['istenen'] is not None:
        metin += f", m² {tr_currency(oz['istenen'])}"
    metin += '.'
    if oz['bolge'] is not None:
        metin += f" Bölge ortalaması {tr_currency(oz['bolge'])}/m² ({_kaynak_metni(oz)})"
        if fark is not None and abs(fark) >= 0.05:
            yon = 'altında' if fark < 0 else 'üzerinde'
            metin += f"; ilan bu ortalamanın %{tr_number(abs(fark), 1)} {yon} — {oz['konum']}."
        elif fark is not None:
            metin += f"; ilan bu ortalamayla aynı seviyede — {oz['konum']}."
        else:
            metin += '.'
    else:
        metin += " Emsal ya da bölge ortalaması girilmediği için karşılaştırma yapılmamıştır."
    return metin


def _tavsiyeler(ilan, oz, arsa_mi, altyapi_list):
    tavsiyeler = []
    fark = oz['fark'] if ilan is not None else None
    if ilan is not None and ilan.teklif_tipi == 'kat_karsiligi':
        if fark is not None and fark > 5:
            tavsiyeler.append('Talep edilen pay bölge emsallerinin üzerinde; müteahhit tekliflerinde pazarlık '
                              'beklenmeli.')
        elif fark is not None and fark < -5:
            tavsiyeler.append('Talep edilen pay bölge emsallerinin altında; müteahhitler için cazip bir teklif.')
        if ilan.tevhid_durumu == 'yapilacak':
            tavsiyeler.append('Parsellerin tevhidi (birleştirilmesi) için belediye ve tapu süreci planlanmalı.')
    elif fark is not None:
        ne = 'Kira' if ilan.teklif_tipi == 'kiralik' else 'Fiyat'
        if fark <= -10:
            tavsiyeler.append(f'{ne} bölge ortalamasının belirgin şekilde altında; hızlı karar avantaj sağlayabilir.')
        elif fark < 0:
            tavsiyeler.append(f'{ne} bölge ortalamasının altında; pazarlık payı sınırlı olabilir.')
        elif fark > 10:
            tavsiyeler.append(f'{ne} bölge ortalamasının belirgin şekilde üzerinde; pazarlık veya emsal araştırması '
                              'önerilir.')
        else:
            tavsiyeler.append(f'{ne} bölge ortalamasına yakın; emsal işlemlerle teyit edilmesi önerilir.')
    if arsa_mi:
        eksik = [etiket for kod, etiket in ALTYAPI_ETIKETLERI if kod not in altyapi_list]
        if eksik:
            tavsiyeler.append(f"Eksik altyapı ({', '.join(eksik).lower()}) için belediyeden bağlantı planı ve "
                              "maliyeti sorulmalı.")
    tavsiyeler.append('Tapu kaydı, imar durumu ve olası şerhler resmi kurumlardan güncel olarak teyit edilmelidir.')
    return tavsiyeler


def _puan(g, fark, teklif_tipi, altyapi_list):
    """Tek parselli arsa/tarla için mevcut ArsaAnalizci uygunluk puanı."""
    karsilastir = fark is not None and teklif_tipi in ('satilik', 'kiralik')
    detay = ArsaAnalizci().uygunluk_detay({
        'metrekare': float(g.metrekare or 0), 'imar_durumu': g.imar_durumu or '', 'altyapi': altyapi_list,
        'bolge_karsilastirma': fark if karsilastir else None, 'bolge_fiyat_girildi': karsilastir,
    })
    for d in detay:
        if d['kod'] == 'fiyat' and not karsilastir:
            d['aciklama'] = ('Kat karşılığında fiyat bileşeni nötr kabul edildi' if teklif_tipi == 'kat_karsiligi'
                             else 'Bölge karşılaştırması olmadığı için nötr kabul edildi')
    puan = round(max(0, min(100, sum(d['puan'] for d in detay))), 1)
    return puan, detay


def build_report_model(ilan_or_none, gayrimenkul, user, detail_url='', upload_folder=None, base_dir=None):
    """İlan (ya da ilan yoksa yalnız gayrimenkul -> tanıtım raporu) için rapor modeli.

    Mal sahibi bilgisi modele hiç alınmaz.
    """
    from modules.gayrimenkul_form import detay_bilgileri, ozellik_gruplari
    from modules.gayrimenkul_sabitleri import TEKLIF_TIPLERI, etiket
    base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    upload_folder = upload_folder or os.path.join(base_dir, 'static', 'uploads')

    ilan = ilan_or_none
    g = gayrimenkul
    gler = ilan.gayrimenkuller if ilan is not None else [g]
    if g not in gler:
        gler = [g] + list(gler)
    tur = g.tur or 'arsa'
    arsa_mi = tur in ARSA_TURLERI
    tek = len(gler) == 1
    tur_etiketi = _tur_etiketi(g)

    taks = float(g.taks) if g.taks is not None else 0.3
    kaks = float(g.kaks) if g.kaks is not None else 1.5
    altyapi_list = parse_altyapi(g.altyapi)
    konum = ', '.join(p for p in [g.mahalle, g.ilce, g.il] if p)
    imar = (g.imar_durumu or '').strip()

    if ilan is not None:
        from modules.ilan_servis import ilan_ozeti
        oz = ilan_ozeti(ilan)
    else:
        oz = {'toplam_m2': sum(float(x.metrekare or 0) for x in gler), 'insaat_hakki': None,
              'sahibe_dusen_m2': None, 'istenen': None, 'bolge': None, 'bolge_kaynak': 'yok',
              'emsal_sayisi': 0, 'fark': None, 'konum': None}
    metrekare = float(oz['toplam_m2'] or 0)

    tip = ilan.teklif_tipi if ilan is not None else None
    if tip == 'satilik':
        baslik = f"Satılık {tur_etiketi} Sunum Raporu"
    elif tip == 'kiralik':
        baslik = f"Kiralık {tur_etiketi} Sunum Raporu"
    elif tip == 'kat_karsiligi':
        baslik = 'Kat Karşılığı Teklif Raporu'
    else:
        baslik = f"{tur_etiketi} Tanıtım Raporu"

    # Türe özel bilgiler ve özellikler (tek kayıtta)
    tur_bilgileri, gruplar = [], []
    if tek:
        tur_bilgileri = [(k, v) for k, v in detay_bilgileri(g) if k not in _GENEL_ETIKETLER]
        gruplar = [(b, liste) for b, liste in ozellik_gruplari(g) if not (arsa_mi and b == 'Altyapı')]

    if tek:
        tanim = f"{g.ozet} {tr_lower(tur_etiketi)}".strip() if g.ozet else tr_lower(tur_etiketi)
        tanim = tanim.replace(' · ', ', ')
    else:
        birim = 'parsel' if all((x.tur or 'arsa') in ARSA_TURLERI for x in gler) else 'gayrimenkul'
        tanim = f"{len(gler)} {birim}, toplam {sayi(metrekare)} m²"

    if ilan is not None:
        fiyat_satirlari = _fiyat_satirlari(ilan, oz)
        emsaller = _emsal_satirlari(ilan)
        fiyat_ozet = _fiyat_ozeti(ilan, oz, konum, tanim)
        tutar = _f(ilan.kira if tip == 'kiralik' else ilan.fiyat) if tip != 'kat_karsiligi' else None
    else:
        fiyat_satirlari, emsaller, tutar = [], [], None
        fiyat_ozet = f"{konum} konumundaki {tanim} için hazırlanan tanıtım raporudur."

    puan, puan_detay = (_puan(g, oz['fark'], tip, altyapi_list) if arsa_mi and tek else (0, []))

    tarih = to_local_time(datetime.utcnow(), getattr(user, 'timezone', None))
    coord = parse_coordinates(g.koordinatlar)
    maps_url = f"https://www.google.com/maps?q={coord[0]},{coord[1]}" if coord else ''

    fotograflar = []
    for x in gler:
        fotograflar.extend(p for p in _photos_for(x, upload_folder) if p not in fotograflar)
    photo = None
    if user.profil_foto:
        cand = os.path.join(upload_folder, user.profil_foto)
        photo = cand if os.path.exists(cand) else None
    advisor = Advisor(
        ad_soyad=' '.join(p for p in [(user.ad or '').strip(), (user.soyad or '').strip()] if p) or user.email,
        unvan=_clean(user.unvan), firma=_clean(user.firma), email=_clean(user.email),
        telefon=_clean(user.telefon), adres=_clean(user.adres), photo_path=photo,
    )
    # İlanda yalnız ilan açıklaması (alıcıya yönelik metin); tanıtımda gayrimenkul notu
    notlar = ((ilan.aciklama if ilan is not None else g.notlar) or '').strip()

    return ReportModel(
        analiz_id=g.id, baslik=baslik, kod=ilan.kod if ilan is not None else '',
        teklif_tipi=tip, teklif_etiketi=etiket(TEKLIF_TIPLERI, tip) if tip else 'Tanıtım',
        tur=tur, tur_etiketi=tur_etiketi,
        konum=konum, il=g.il or '', ilce=g.ilce or '', mahalle=g.mahalle or '',
        ada=g.ada or '-', parsel=g.parsel or '-', pafta=g.pafta or '-',
        koordinat=coord, metrekare=metrekare,
        parseller=[_parsel(x) for x in gler], tur_bilgileri=tur_bilgileri, ozellik_gruplari=gruplar,
        imar_durumu=imar or '-', taks=taks, kaks=kaks,
        taban_alani=float(g.metrekare or 0) * taks, insaat_alani=float(g.metrekare or 0) * kaks,
        kat_sayisi=(kaks / taks) if taks else 0,
        altyapi=[(etiket_, kod in altyapi_list) for kod, etiket_ in ALTYAPI_ETIKETLERI],
        puan=puan, puan_detay=puan_detay,
        fiyat_satirlari=fiyat_satirlari, tutar=tutar, istenen=oz['istenen'], emsaller=emsaller,
        bolge=oz['bolge'], bolge_kaynak=oz['bolge_kaynak'], emsal_sayisi=oz['emsal_sayisi'],
        fark=oz['fark'], konum_etiketi=oz['konum'],
        toplam_m2=metrekare, insaat_hakki=oz['insaat_hakki'], sahibe_dusen_m2=oz['sahibe_dusen_m2'],
        fiyat_ozet=fiyat_ozet,
        swot=parse_swot(g.swot_analizi),
        tavsiyeler=_tavsiyeler(ilan, oz, arsa_mi, altyapi_list),
        notlar=notlar,
        fotograflar=fotograflar[:8],
        tarih=tarih, detail_url=detail_url, maps_url=maps_url,
        advisor=advisor, brand=_brand_for(user, base_dir),
        extras={'taks_varsayilan': g.taks is None or g.kaks is None,
                'hepsi_arsa': all((x.tur or 'arsa') in ARSA_TURLERI for x in gler),
                'insaat_elle': ilan is not None and ilan.insaat_alani_elle is not None,
                'not_basligi': 'Açıklama' if ilan is not None else 'Danışman notu'},
    )
