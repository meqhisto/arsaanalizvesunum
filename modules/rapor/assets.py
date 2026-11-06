# -*- coding: utf-8 -*-
"""Rapor görselleri: grafikler, konum haritası ve QR kod (PNG).

Grafikler Pillow ile çizilir; böylece PDF, Word ve PowerPoint aynı görseli kullanır
ve ek bir grafik kütüphanesine gerek kalmaz.
"""
import io
import logging
import math
import os

import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont

from .model import tr_number, tr_short_currency

log = logging.getLogger(__name__)

FONT_DIRS = ['/usr/share/fonts/truetype/dejavu', '/usr/share/fonts/dejavu', '/usr/share/fonts/TTF']
SCALE = 2  # Yüksek çözünürlük için 2x çiz
GRID = '#E3E7EC'
TEXT = '#2B2F36'
MUTED = '#6B7280'


def _font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    for d in FONT_DIRS:
        path = os.path.join(d, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size * SCALE)
    return ImageFont.load_default()


def _hex(color):
    color = color.lstrip('#')
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _blend(color, alpha):
    """Rengi beyazla karıştırarak açık ton üretir."""
    r, g, b = _hex(color)
    return (int(r + (255 - r) * (1 - alpha)), int(g + (255 - g) * (1 - alpha)), int(b + (255 - b) * (1 - alpha)))


def _canvas(w, h):
    img = Image.new('RGB', (w * SCALE, h * SCALE), 'white')
    return img, ImageDraw.Draw(img)


def _nice_step(span, ticks=4):
    """Eksen için yuvarlak adım: 1, 2, 2.5, 5 x 10^n."""
    raw = span / ticks if span > 0 else 1
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _save(img, path):
    img.save(path, 'PNG', optimize=True)
    return path


def price_comparison_chart(model, path, width=760, height=200):
    """Arsanın m² fiyatı ile bölge ortalamasını yatay çubuklarla karşılaştırır."""
    if model.bolge_m2_fiyat <= 0:
        return None
    img, d = _canvas(width, height)
    s = SCALE
    rows = [('Bu arsa', model.m2_fiyat, model.brand.accent), ('Bölge ortalaması', model.bolge_m2_fiyat, model.brand.primary)]
    step = _nice_step(max(v for _, v, _ in rows) * 1.25)
    maxv = step * 4
    left, right, top = 170, width - 40, 24
    bar_h, gap = 50, 30
    f_label, f_val, f_small = _font(15, True), _font(14, True), _font(12)
    for i in range(5):
        x = left + (right - left) * i / 4
        d.line([(x * s, (top - 8) * s), (x * s, (top + 2 * bar_h + gap + 8) * s)], fill=GRID, width=s)
        d.text((x * s, (top + 2 * bar_h + gap + 14) * s), f"{tr_number(maxv * i / 4)} TL", font=f_small, fill=MUTED, anchor='mt')
    for i, (label, value, color) in enumerate(rows):
        y = top + i * (bar_h + gap)
        d.text(((left - 14) * s, (y + bar_h / 2) * s), label, font=f_label, fill=TEXT, anchor='rm')
        x2 = left + (right - left) * value / maxv
        d.rounded_rectangle([left * s, y * s, x2 * s, (y + bar_h) * s], radius=6 * s, fill=_hex(color))
        d.text(((x2 + 8) * s, (y + bar_h / 2) * s), f"{tr_number(value)} TL/m²", font=f_val, fill=TEXT, anchor='lm')
    return _save(img, path)


def projection_chart(model, path, width=760, height=330):
    """Senaryolara göre yıllara yayılmış toplam değer projeksiyonu."""
    img, d = _canvas(width, height)
    s = SCALE
    left, right, top, bottom = 110, width - 40, 56, height - 46
    all_vals = [v for sc in model.senaryolar for v in sc.degerler]
    lo, hi = min(all_vals) * 0.95, max(all_vals) * 1.03
    years = len(model.senaryolar[0].degerler) - 1
    f_small, f_lbl = _font(12), _font(13, True)

    def xy(i, v):
        return (left + (right - left) * i / years) * s, (bottom - (bottom - top) * (v - lo) / (hi - lo or 1)) * s

    for k in range(5):
        v = lo + (hi - lo) * k / 4
        y = xy(0, v)[1]
        d.line([(left * s, y), (right * s, y)], fill=GRID, width=s)
        d.text(((left - 10) * s, y), tr_short_currency(v), font=f_small, fill=MUTED, anchor='rm')
    for i in range(years + 1):
        x = xy(i, lo)[0]
        d.text((x, (bottom + 14) * s), 'Bugün' if i == 0 else f"{i}. yıl", font=f_small, fill=MUTED, anchor='mt')

    colors = [_blend(model.brand.primary, 0.45), _hex(model.brand.primary), _hex(model.brand.accent)]
    for sc, color in zip(model.senaryolar, colors):
        pts = [xy(i, v) for i, v in enumerate(sc.degerler)]
        d.line(pts, fill=color, width=4 * s if sc.ad == 'Beklenen' else 3 * s, joint='curve')
        for p in pts:
            r = 4 * s
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)
    # Lejant
    x = left
    for sc, color in zip(model.senaryolar, colors):
        d.rounded_rectangle([x * s, 14 * s, (x + 22) * s, 26 * s], radius=3 * s, fill=color)
        label = f"{sc.ad} (yıllık %{tr_number(sc.oran, 0)})"
        d.text(((x + 30) * s, 20 * s), label, font=f_lbl, fill=TEXT, anchor='lm')
        x += 30 + d.textlength(label, font=f_lbl) / s + 28
    return _save(img, path)


def score_chart(model, path, width=760, height=240):
    """Uygunluk puanı bileşenleri: her bileşen için alınan / en yüksek puan."""
    if not model.puan_detay:
        return None
    img, d = _canvas(width, height)
    s = SCALE
    left, right, top = 150, width - 150, 16
    row_h = (height - 2 * top) / len(model.puan_detay)
    f_lbl, f_val, f_note = _font(14, True), _font(13, True), _font(11)
    for i, comp in enumerate(model.puan_detay):
        y = top + i * row_h
        bh = row_h * 0.42
        cy = y + row_h * 0.32
        d.text(((left - 12) * s, cy * s), comp['baslik'], font=f_lbl, fill=TEXT, anchor='rm')
        d.rounded_rectangle([left * s, (cy - bh / 2) * s, right * s, (cy + bh / 2) * s], radius=5 * s, fill=_blend(model.brand.primary, 0.12))
        ratio = comp['puan'] / comp['max'] if comp['max'] else 0
        if ratio > 0:
            x2 = left + (right - left) * ratio
            d.rounded_rectangle([left * s, (cy - bh / 2) * s, max(x2, left + 10) * s, (cy + bh / 2) * s], radius=5 * s,
                                fill=_hex(model.brand.primary))
        d.text(((right + 12) * s, cy * s), f"{tr_number(comp['puan'], 1).rstrip('0').rstrip(',')} / {comp['max']}", font=f_val, fill=TEXT, anchor='lm')
        d.text((left * s, (cy + bh / 2 + 4) * s), comp.get('aciklama', ''), font=f_note, fill=MUTED, anchor='lt')
    return _save(img, path)


# ---------------------------------------------------------------- harita
TILE = 256
TILE_URL = os.environ.get('REPORT_TILE_URL', 'https://tile.openstreetmap.org/{z}/{x}/{y}.png')
USER_AGENT = 'ArsaAnalizRapor/1.0 (+https://github.com/meqhisto/arsaanalizvesunum)'


def _deg2px(lat, lon, z):
    n = 2 ** z * TILE
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def location_map(model, path, width=760, height=380, zoom=15):
    """Koordinat varsa OpenStreetMap karolarından konum haritası çizer. Başarısızsa None."""
    if not model.koordinat:
        return None
    lat, lon = model.koordinat
    cx, cy = _deg2px(lat, lon, zoom)
    x0, y0 = cx - width / 2, cy - height / 2
    tx0, ty0 = int(x0 // TILE), int(y0 // TILE)
    tx1, ty1 = int((x0 + width) // TILE), int((y0 + height) // TILE)
    canvas = Image.new('RGB', ((tx1 - tx0 + 1) * TILE, (ty1 - ty0 + 1) * TILE), '#EEF0F2')
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    try:
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                r = session.get(TILE_URL.format(z=zoom, x=tx % (2 ** zoom), y=ty), timeout=5)
                r.raise_for_status()
                canvas.paste(Image.open(io.BytesIO(r.content)).convert('RGB'), ((tx - tx0) * TILE, (ty - ty0) * TILE))
    except Exception as e:
        log.warning("Harita karoları alınamadı: %s", e)
        return None
    ox, oy = int(x0 - tx0 * TILE), int(y0 - ty0 * TILE)
    img = canvas.crop((ox, oy, ox + width, oy + height)).resize((width * SCALE, height * SCALE), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    s = SCALE
    px, py = width / 2 * s, height / 2 * s
    accent = _hex(model.brand.accent)
    # İşaretçi: halka + iğne
    d.ellipse([px - 22 * s, py - 22 * s, px + 22 * s, py + 22 * s], outline=accent, width=4 * s)
    d.polygon([(px, py), (px - 11 * s, py - 26 * s), (px + 11 * s, py - 26 * s)], fill=accent)
    d.ellipse([px - 14 * s, py - 44 * s, px + 14 * s, py - 16 * s], fill=accent, outline='white', width=3 * s)
    # Atıf (OSM lisans gereği)
    f = _font(10)
    text = '© OpenStreetMap katkıcıları'
    tw = d.textlength(text, font=f)
    d.rectangle([img.width - tw - 12 * s, img.height - 20 * s, img.width, img.height], fill=(255, 255, 255))
    d.text((img.width - 6 * s, img.height - 10 * s), text, font=f, fill=MUTED, anchor='rm')
    img.save(path, 'JPEG', quality=82, optimize=True)  # Harita fotoğraf gibi; JPEG çok daha küçük
    return path


def qr_code(data, path):
    if not data:
        return None
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    qr.make_image(fill_color='black', back_color='white').save(path)
    return path


def photo_thumb(src, path, width=900, height=600):
    """Fotoğrafı kırparak sabit oranlı küçük görsele çevirir (rapor ızgarası için)."""
    try:
        with Image.open(src) as im:
            im = im.convert('RGB')
            ratio = width / height
            w, h = im.size
            if w / h > ratio:
                nw = int(h * ratio)
                im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
            else:
                nh = int(w / ratio)
                im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
            im.resize((width, height), Image.LANCZOS).save(path, 'JPEG', quality=85)
        return path
    except Exception as e:
        log.warning("Fotoğraf işlenemedi (%s): %s", src, e)
        return None


def small_logo(src, path, size=400):
    """Logoyu rapora gömmek için küçültür (orijinal dosyalar çok büyük olabiliyor)."""
    try:
        with Image.open(src) as im:
            im = im.convert('RGBA')
            im.thumbnail((size, size), Image.LANCZOS)
            im.save(path, 'PNG', optimize=True)
        return path
    except Exception as e:
        log.warning("Logo işlenemedi (%s): %s", src, e)
        return None


def build_assets(model, out_dir):
    """Tüm görselleri üretir; üretilemeyenler için None döner."""
    os.makedirs(out_dir, exist_ok=True)
    j = lambda n: os.path.join(out_dir, n)  # noqa: E731
    if model.brand.logo_path:
        model.brand.logo_path = small_logo(model.brand.logo_path, j('logo.png'))
    assets = {
        'fiyat_grafik': price_comparison_chart(model, j('fiyat.png')),
        'projeksiyon_grafik': projection_chart(model, j('projeksiyon.png')),
        'puan_grafik': score_chart(model, j('puan.png')),
        'harita': location_map(model, j('harita.jpg')),
        'qr_detay': qr_code(model.detail_url, j('qr_detay.png')),
        'qr_harita': qr_code(model.maps_url, j('qr_harita.png')),
        'fotograflar': [p for p in (photo_thumb(src, j(f'foto_{i}.jpg')) for i, src in enumerate(model.fotograflar)) if p],
    }
    return assets
