# -*- coding: utf-8 -*-
"""PowerPoint sunumu (python-pptx), 16:9. Şablon dosyası kullanılmaz; tasarım koddan gelir."""
from PIL import Image as PILImage
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from . import common
from .model import tr_number

FONT = 'Calibri'
SW, SH = Inches(13.333), Inches(7.5)
TEXT = RGBColor(0x2B, 0x2F, 0x36)
MUTED = RGBColor(0x6B, 0x72, 0x80)
LIGHT = RGBColor(0xF3, 0xF5, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MARGIN = Inches(0.6)


def _rgb(hex_color):
    h = hex_color.lstrip('#')
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Deck:
    def __init__(self, m, assets):
        self.m, self.assets = m, assets
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = SW, SH
        self.blank = self.prs.slide_layouts[6]
        self.pri, self.acc = _rgb(m.brand.primary), _rgb(m.brand.accent)
        self.n = 0

    # ------------------------------------------------------------ yardımcılar
    def text(self, slide, x, y, w, h, text, size=14, bold=False, color=TEXT, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, wrap=True):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = wrap
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.05)
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if isinstance(line, tuple):
                line, lsize, lbold, lcolor = line
            else:
                lsize, lbold, lcolor = size, bold, color
            r = p.add_run()
            r.text = str(line)
            r.font.name, r.font.size, r.font.bold = FONT, Pt(lsize), lbold
            r.font.color.rgb = lcolor
        return tb

    def rect(self, slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE):
        s = slide.shapes.add_shape(shape, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = color
        s.line.fill.background()
        s.shadow.inherit = False
        return s

    def picture(self, slide, path, x, y, max_w, max_h, center=True):
        with PILImage.open(path) as im:
            iw, ih = im.size
        scale = min(max_w / iw, max_h / ih)
        w, h = int(iw * scale), int(ih * scale)
        if center:
            x, y = x + (max_w - w) // 2, y + (max_h - h) // 2
        return slide.shapes.add_picture(path, x, y, w, h)

    def slide(self, title, subtitle=None):
        """Başlık şeritli içerik slaytı."""
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        self.rect(s, 0, 0, SW, Inches(0.12), self.pri)
        self.text(s, MARGIN, Inches(0.35), SW - 2 * MARGIN, Inches(0.7), title, 26, True, self.pri)
        if subtitle:
            self.text(s, MARGIN, Inches(0.98), SW - 2 * MARGIN, Inches(0.4), subtitle, 13, color=MUTED)
        self.rect(s, MARGIN, Inches(1.42), Inches(0.9), Inches(0.05), self.acc)
        foot = self.m.satir(self.m.brand.name, self.m.konum, self.m.ada_parsel)
        self.text(s, MARGIN, SH - Inches(0.45), Inches(10), Inches(0.3), foot, 9, color=MUTED)
        self.text(s, SW - MARGIN - Inches(1), SH - Inches(0.45), Inches(1), Inches(0.3), str(self.n), 9,
                  color=MUTED, align=PP_ALIGN.RIGHT)
        if self.m.brand.logo_path:
            self.picture(s, self.m.brand.logo_path, SW - MARGIN - Inches(0.7), Inches(0.3), Inches(0.7), Inches(0.7))
        return s

    def kv_table(self, slide, rows, x, y, w, label_ratio=0.42, size=13, row_h=Inches(0.42)):
        shape = slide.shapes.add_table(len(rows), 2, x, y, w, row_h * len(rows))
        t = shape.table
        t.first_row = False
        t.horz_banding = False
        t.columns[0].width = int(w * label_ratio)
        t.columns[1].width = w - int(w * label_ratio)
        for i, (k, v) in enumerate(rows):
            t.rows[i].height = row_h
            for j, val in enumerate((k, v)):
                c = t.cell(i, j)
                c.fill.solid()
                c.fill.fore_color.rgb = LIGHT if i % 2 else WHITE
                c.vertical_anchor = MSO_ANCHOR.MIDDLE
                c.margin_left = Inches(0.1)
                tf = c.text_frame
                tf.paragraphs[0].text = ''
                r = tf.paragraphs[0].add_run()
                r.text = str(val)
                r.font.name, r.font.size, r.font.bold = FONT, Pt(size), j == 0
                r.font.color.rgb = TEXT
        return t

    # ------------------------------------------------------------ slaytlar
    def cover(self):
        m = self.m
        s = self.prs.slides.add_slide(self.blank)
        self.n += 1
        half = int(SW * 0.55)
        self.rect(s, 0, 0, half, SH, self.pri)
        if self.assets.get('harita'):
            self.picture(s, self.assets['harita'], half, 0, SW - half, SH)
            # Haritayı sağ yarıya kırparak doldur
            pic = s.shapes[-1]
            pic.left, pic.top, pic.width, pic.height = half, 0, SW - half, SH
            with PILImage.open(self.assets['harita']) as im:
                iw, ih = im.size
            target = (SW - half) / SH
            if iw / ih > target:
                crop = (1 - target * ih / iw) / 2
                pic.crop_left = pic.crop_right = crop
            else:
                crop = (1 - iw / ih / target) / 2
                pic.crop_top = pic.crop_bottom = crop
        else:
            self.rect(s, half, 0, SW - half, SH, LIGHT)
        self.rect(s, half - Inches(0.08), 0, Inches(0.08), SH, self.acc)
        x = Inches(0.8)
        if m.brand.logo_path:
            self.picture(s, m.brand.logo_path, x, Inches(0.7), Inches(1.1), Inches(1.1), center=False)
        self.text(s, x, Inches(1.95), half - Inches(1.4), Inches(0.4), m.brand.name.upper(), 13, True, self.acc)
        self.text(s, x, Inches(2.5), half - Inches(1.4), Inches(1.6), m.baslik, 36, True, WHITE)
        self.text(s, x, Inches(4.25), half - Inches(1.4), Inches(1.0),
                  [(m.konum, 18, False, WHITE), (m.satir(m.ada_parsel, f"{tr_number(m.metrekare)} m²"), 15, False, RGBColor(0xC9, 0xD3, 0xDF))])
        a = m.advisor
        self.text(s, x, SH - Inches(1.5), half - Inches(1.4), Inches(1.0),
                  [(a.ad_soyad, 14, True, WHITE),
                   (' · '.join(v for v in (a.unvan, a.telefon) if v and v != '-'), 12, False, RGBColor(0xC9, 0xD3, 0xDF)),
                   (m.tarih.strftime('%d.%m.%Y'), 12, False, RGBColor(0xC9, 0xD3, 0xDF))])

    def summary(self):
        m = self.m
        s = self.slide('Özet', 'Temel göstergeler ve değerlendirme')
        y, h = Inches(1.75), Inches(1.45)
        gap = Inches(0.25)
        w = (SW - 2 * MARGIN - 3 * gap) / 4
        for i, (label, value, note) in enumerate(common.kpis(m)):
            x = MARGIN + int(i * (w + gap))
            self.rect(s, x, y, int(w), h, LIGHT)
            self.rect(s, x, y, int(w), Inches(0.06), self.acc)
            self.text(s, x + Inches(0.2), y + Inches(0.18), int(w) - Inches(0.3), h - Inches(0.25),
                      [(label.upper(), 11, False, MUTED), (value, 24, True, self.pri), (note, 11, False, MUTED)])
        self.text(s, MARGIN, Inches(3.55), SW - 2 * MARGIN, Inches(3.2),
                  [(m.temel_ozet, 16, False, TEXT), ('', 8, False, TEXT), (m.yatirim_ozet, 16, False, TEXT)])

    def location(self):
        m = self.m
        s = self.slide('Konum ve arsa bilgileri', m.konum)
        top = Inches(1.75)
        if self.assets.get('harita'):
            self.picture(s, self.assets['harita'], MARGIN, top, Inches(6.9), Inches(5.1), center=False)
            self.kv_table(s, common.parcel_rows(m), Inches(7.8), top, SW - Inches(7.8) - MARGIN, size=12, row_h=Inches(0.5))
        else:
            self.kv_table(s, common.parcel_rows(m), MARGIN, top, Inches(7), size=13, row_h=Inches(0.5))

    def zoning(self):
        m = self.m
        s = self.slide('İmar ve yapılaşma', f"{m.imar_durumu} imar  ·  TAKS / KAKS {m.taks_kaks}")
        top = Inches(1.8)
        cards = [('Taban alanı', f"{tr_number(m.taban_alani)} m²"), ('Toplam inşaat alanı', f"{tr_number(m.insaat_alani)} m²"),
                 ('Teorik kat sayısı', tr_number(m.kat_sayisi, 1)),
                 ('İnşaat m² başı arsa maliyeti', f"{tr_number(m.fiyat / m.insaat_alani)} TL" if m.insaat_alani else '-')]
        w = (SW - 2 * MARGIN - Inches(0.75)) / 4
        for i, (label, value) in enumerate(cards):
            x = MARGIN + int(i * (w + Inches(0.25)))
            self.rect(s, x, top, int(w), Inches(1.3), LIGHT)
            self.text(s, x + Inches(0.2), top + Inches(0.2), int(w) - Inches(0.3), Inches(1.0),
                      [(label, 12, False, MUTED), (value, 24, True, self.pri)])
        self.text(s, MARGIN, Inches(3.5), Inches(6), Inches(0.4), 'Altyapı durumu', 16, True, self.pri)
        w2 = (SW - 2 * MARGIN - Inches(0.6)) / 5
        for i, (label, var) in enumerate(m.altyapi):
            x = MARGIN + int(i * (w2 + Inches(0.15)))
            color = RGBColor(0xE6, 0xF4, 0xEA) if var else RGBColor(0xFC, 0xE8, 0xE6)
            fg = RGBColor(0x1E, 0x7B, 0x3A) if var else RGBColor(0xB3, 0x26, 0x1E)
            self.rect(s, x, Inches(4.05), int(w2), Inches(1.1), color, MSO_SHAPE.ROUNDED_RECTANGLE)
            self.text(s, x, Inches(4.05), int(w2), Inches(1.1),
                      [('✓' if var else '✗', 26, True, fg), (label, 14, True, fg)], align=PP_ALIGN.CENTER,
                      anchor=MSO_ANCHOR.MIDDLE)
        eksik = [l for l, v in m.altyapi if not v]
        note = ('Tüm temel altyapı kalemleri mevcut.' if not eksik else
                f"Eksik kalemler ({', '.join(eksik).lower()}) için bağlantı planı ve maliyeti belediyeden teyit edilmelidir.")
        self.text(s, MARGIN, Inches(5.45), SW - 2 * MARGIN, Inches(0.8), note, 14, color=MUTED)

    def price(self):
        m = self.m
        if not self.assets.get('fiyat_grafik'):
            return
        yon = 'altında' if (m.bolge_fark or 0) < 0 else 'üzerinde'
        s = self.slide('Bölge fiyatı karşılaştırması',
                       f"Arsa, bölge ortalamasının %{tr_number(abs(m.bolge_fark or 0), 1)} {yon}")
        self.picture(s, self.assets['fiyat_grafik'], MARGIN, Inches(1.8), SW - 2 * MARGIN, Inches(3.3))
        self.text(s, MARGIN, Inches(5.3), SW - 2 * MARGIN, Inches(1.5), m.temel_ozet, 15)

    def projection(self):
        m = self.m
        s = self.slide('Değer projeksiyonu (5 yıl)',
                       f"Beklenen senaryo: yıllık %{tr_number(m.yillik_artis, 1)} "
                       f"({'danışman girdisi' if m.artis_kaynagi == 'kullanıcı' else 'model tahmini'})")
        data = CategoryChartData()
        data.categories = ['Bugün'] + [f"{i}. yıl" for i in range(1, len(m.senaryolar[0].degerler))]
        for sc in m.senaryolar:
            data.add_series(f"{sc.ad} (%{tr_number(sc.oran, 0)})", [round(v / 1e6, 2) for v in sc.degerler])
        gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, MARGIN, Inches(1.65), Inches(7.6), Inches(5.2), data)
        ch = gf.chart
        ch.has_legend = True
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(12)
        ch.font.name = FONT
        ch.value_axis.has_major_gridlines = True
        ch.value_axis.major_gridlines.format.line.color.rgb = RGBColor(0xE3, 0xE7, 0xEC)
        ch.value_axis.tick_labels.font.size = Pt(11)
        ch.value_axis.tick_labels.number_format = '0" Mn TL"'
        ch.value_axis.tick_labels.number_format_is_linked = False
        ch.category_axis.tick_labels.font.size = Pt(11)
        palette = [RGBColor(0x9A, 0xA8, 0xB8), self.pri, self.acc]
        for series, color in zip(ch.series, palette):
            series.format.line.color.rgb = color
            series.format.line.width = Pt(3)
            series.smooth = False
            series.marker.format.fill.solid()
            series.marker.format.fill.fore_color.rgb = color
            series.marker.format.line.color.rgb = color
        # Sağda senaryo özetleri
        x, w = Inches(8.5), SW - Inches(8.5) - MARGIN
        y = Inches(1.8)
        for sc, color in zip(m.senaryolar, palette):
            self.rect(s, x, y, Inches(0.08), Inches(1.4), color)
            self.text(s, x + Inches(0.25), y, w - Inches(0.25), Inches(1.4),
                      [(f"{sc.ad} · yıllık %{tr_number(sc.oran, 1)}", 13, True, TEXT),
                       (f"5. yıl: {tr_number(sc.degerler[-1])} TL", 18, True, color if sc.ad != 'Temkinli' else TEXT),
                       (f"Toplam artış %{tr_number((sc.degerler[-1] / sc.degerler[0] - 1) * 100 if sc.degerler[0] else 0, 0)}", 12, False, MUTED)])
            y += Inches(1.65)

    def score(self):
        m = self.m
        if not self.assets.get('puan_grafik'):
            return
        s = self.slide('Uygunluk puanı', 'İmar, büyüklük, fiyat ve altyapı bileşenlerine göre')
        self.rect(s, MARGIN, Inches(1.8), Inches(3.2), Inches(3.2), LIGHT, MSO_SHAPE.OVAL)
        self.text(s, MARGIN, Inches(1.8), Inches(3.2), Inches(3.2),
                  [(tr_number(m.puan, 0), 66, True, self.pri), ('/ 100', 16, False, MUTED), (m.puan_etiketi, 16, True, self.acc)],
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        self.picture(s, self.assets['puan_grafik'], Inches(4.3), Inches(1.7), SW - Inches(4.3) - MARGIN, Inches(4.2))
        self.text(s, MARGIN, Inches(6.05), SW - 2 * MARGIN, Inches(0.8),
                  'Puan; imar durumu (30), büyüklük (15), bölge fiyatına göre konum (35) ve altyapı (20) bileşenlerinin toplamıdır.',
                  12, color=MUTED)

    def swot(self):
        m = self.m
        s = self.slide('SWOT analizi')
        fills = ['E6F4EA', 'FCE8E6', 'E8F0FE', 'FEF3E2']
        heads = ['1E7B3A', 'B3261E', '1A56B8', 'A15C07']
        gap = Inches(0.2)
        w = (SW - 2 * MARGIN - gap) / 2
        h = (SH - Inches(1.75) - Inches(0.7) - gap) / 2
        for i, (title, items) in enumerate(common.swot_blocks(m)):
            x = MARGIN + int((i % 2) * (w + gap))
            y = Inches(1.75) + int((i // 2) * (h + gap))
            self.rect(s, x, y, int(w), int(h), _rgb(fills[i]))
            lines = [(title, 18, True, _rgb(heads[i]))]
            lines += [(f"• {it}", 14, False, TEXT) for it in items[:6]] or [('Belirtilmemiş', 14, False, MUTED)]
            self.text(s, x + Inches(0.25), y + Inches(0.15), int(w) - Inches(0.4), int(h) - Inches(0.25), lines)

    def photos(self):
        photos = self.assets.get('fotograflar') or []
        if not photos:
            return
        s = self.slide('Fotoğraflar')
        shown = photos[:6]
        cols = 3 if len(shown) > 4 else 2 if len(shown) > 1 else 1
        rows = (len(shown) + cols - 1) // cols
        gap = Inches(0.2)
        w = (SW - 2 * MARGIN - (cols - 1) * gap) / cols
        h = (SH - Inches(1.75) - Inches(0.7) - (rows - 1) * gap) / rows
        for i, p in enumerate(shown):
            self.picture(s, p, MARGIN + int((i % cols) * (w + gap)), Inches(1.75) + int((i // cols) * (h + gap)), int(w), int(h))

    def closing(self):
        m = self.m
        s = self.slide('Tavsiyeler ve iletişim')
        lines = [(f"• {t}", 15, False, TEXT) for t in m.tavsiyeler]
        if m.notlar:
            lines += [('', 6, False, TEXT), ('Danışman notu', 14, True, self.pri), (m.notlar, 14, False, TEXT)]
        self.text(s, MARGIN, Inches(1.75), Inches(7.4), Inches(4.2), lines)
        x = Inches(8.4)
        w = SW - x - MARGIN
        self.rect(s, x, Inches(1.75), w, Inches(4.25), LIGHT)
        a = m.advisor
        contact = [(a.ad_soyad, 18, True, self.pri)]
        contact += [(v, 13, False, TEXT) for v in (a.unvan, a.firma, a.telefon, a.email) if v and v != '-']
        self.text(s, x + Inches(0.3), Inches(1.95), w - Inches(0.5), Inches(2.0), contact)
        qx = x + Inches(0.3)
        for key, label in (('qr_detay', 'Analiz sayfası'), ('qr_harita', 'Haritada aç')):
            if self.assets.get(key):
                s.shapes.add_picture(self.assets[key], qx, Inches(4.15), Inches(1.4), Inches(1.4))
                self.text(s, qx - Inches(0.2), Inches(5.55), Inches(1.8), Inches(0.3), label, 10, color=MUTED, align=PP_ALIGN.CENTER)
                qx += Inches(1.9)
        self.text(s, MARGIN, Inches(6.15), SW - 2 * MARGIN, Inches(0.7), common.DISCLAIMER, 9.5, color=MUTED)


def render_pptx(m, assets, path):
    d = Deck(m, assets)
    d.cover()
    d.summary()
    d.location()
    d.zoning()
    d.price()
    d.projection()
    d.score()
    d.swot()
    d.photos()
    d.closing()
    d.prs.core_properties.title = f"{m.baslik} - {m.konum}"
    d.prs.core_properties.author = m.brand.name
    d.prs.save(path)
    return path
