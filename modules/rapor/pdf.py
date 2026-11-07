# -*- coding: utf-8 -*-
"""PDF raporu (ReportLab)."""
import os
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle, CondPageBreak)

from . import common
from .assets import FONT_DIRS
from .model import tr_number

FONT, FONT_B = 'Helvetica', 'Helvetica-Bold'


def _register_fonts():
    global FONT, FONT_B
    for d in FONT_DIRS:
        reg, bold = os.path.join(d, 'DejaVuSans.ttf'), os.path.join(d, 'DejaVuSans-Bold.ttf')
        if os.path.exists(reg) and os.path.exists(bold):
            if 'DejaVuSans' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('DejaVuSans', reg))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold))
                pdfmetrics.registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold',
                                              italic='DejaVuSans', boldItalic='DejaVuSans-Bold')
            FONT, FONT_B = 'DejaVuSans', 'DejaVuSans-Bold'
            return


def _p(text):
    return escape(str(text)).replace('\n', '<br/>')


class _Styles:
    def __init__(self, m):
        pri, acc = colors.HexColor(m.brand.primary), colors.HexColor(m.brand.accent)
        self.primary, self.accent = pri, acc
        self.light = colors.HexColor('#F3F5F8')
        self.line = colors.HexColor('#DDE2E8')
        self.muted = colors.HexColor('#6B7280')
        base = dict(fontName=FONT, fontSize=9.5, leading=13.5, textColor=colors.HexColor('#2B2F36'))
        self.body = ParagraphStyle('body', **base, spaceAfter=4)
        self.small = ParagraphStyle('small', **{**base, 'fontSize': 8, 'leading': 10.5, 'textColor': self.muted})
        self.h1 = ParagraphStyle('h1', fontName=FONT_B, fontSize=20, leading=24, textColor=pri, spaceAfter=2)
        self.sub = ParagraphStyle('sub', fontName=FONT, fontSize=11.5, leading=15, textColor=self.muted, spaceAfter=10)
        self.h2 = ParagraphStyle('h2', fontName=FONT_B, fontSize=12.5, leading=16, textColor=pri, spaceBefore=12, spaceAfter=6)
        self.kpi_label = ParagraphStyle('kl', fontName=FONT, fontSize=8, leading=10, textColor=self.muted)
        self.kpi_value = ParagraphStyle('kv', fontName=FONT_B, fontSize=13, leading=16, textColor=pri)
        self.kpi_note = ParagraphStyle('kn', fontName=FONT, fontSize=7.5, leading=9.5, textColor=self.muted)
        self.cell = ParagraphStyle('cell', **{**base, 'fontSize': 9, 'leading': 12})
        self.cell_b = ParagraphStyle('cellb', **{**base, 'fontName': FONT_B, 'fontSize': 9, 'leading': 12})
        self.cell_r = ParagraphStyle('cellr', **{**base, 'fontSize': 9, 'leading': 12, 'alignment': TA_RIGHT})
        self.center = ParagraphStyle('center', **{**base, 'alignment': TA_CENTER, 'fontSize': 8, 'leading': 10})


def _image(path, width, max_height=None):
    with PILImage.open(path) as im:
        w, h = im.size
    height = width * h / w
    if max_height and height > max_height:
        width, height = max_height * w / h, max_height
    return Image(path, width=width, height=height)


def _kv_table(rows, st, width, label_ratio=0.42):
    data = [[Paragraph(_p(k), st.cell_b), Paragraph(_p(v), st.cell)] for k, v in rows]
    t = Table(data, colWidths=[width * label_ratio, width * (1 - label_ratio)], hAlign='LEFT')
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, st.light]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, st.line),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def _kpi_row(m, st, width):
    cells = []
    for label, value, note in common.kpis(m):
        cells.append([Paragraph(_p(label.upper()), st.kpi_label), Paragraph(_p(value), st.kpi_value),
                      Paragraph(_p(note), st.kpi_note)])
    t = Table([cells], colWidths=[width / 4] * 4)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), st.light),
        ('LINEBEFORE', (1, 0), (-1, -1), 2, colors.white),
        ('LINEABOVE', (0, 0), (-1, 0), 2.5, st.accent),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
    ]))
    return t


def _section(title, st):
    return Paragraph(_p(title), st.h2)


def _swot_table(m, st, width):
    fills = ['#E6F4EA', '#FCE8E6', '#E8F0FE', '#FEF3E2']
    heads = ['#1E7B3A', '#B3261E', '#1A56B8', '#A15C07']
    blocks = common.swot_blocks(m)
    cells = []
    for i, (title, items) in enumerate(blocks):
        hs = ParagraphStyle(f'sw{i}', fontName=FONT_B, fontSize=10, leading=13, textColor=colors.HexColor(heads[i]), spaceAfter=3)
        body = [Paragraph(_p(title), hs)]
        body += [Paragraph('• ' + _p(it), st.cell) for it in items] or [Paragraph('Belirtilmemiş', st.small)]
        cells.append(body)
    t = Table([[cells[0], cells[1]], [cells[2], cells[3]]], colWidths=[width / 2] * 2)
    style = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 7),
             ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 8),
             ('LINEAFTER', (0, 0), (0, -1), 3, colors.white), ('LINEBELOW', (0, 0), (-1, 0), 3, colors.white)]
    for i, (r, c) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
        style.append(('BACKGROUND', (c, r), (c, r), colors.HexColor(fills[i])))
    t.setStyle(TableStyle(style))
    return t


def _altyapi_table(m, st, width):
    cells = []
    for label, var in m.altyapi:
        color = '#1E7B3A' if var else '#B3261E'
        mark = '✓' if var else '✗'
        cells.append(Paragraph(f'<font color="{color}"><b>{mark}</b></font> {_p(label)}', st.cell))
    t = Table([cells], colWidths=[width / len(cells)] * len(cells))
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), st.light), ('LINEBEFORE', (1, 0), (-1, -1), 2, colors.white),
                           ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8)]))
    return t


def _grid_table(rows, st, width, ratios, right_cols=()):
    """Başlık satırlı tablo; right_cols sütunları sağa yaslı."""
    head_r = ParagraphStyle('hr', parent=st.cell_b, alignment=TA_RIGHT)

    def style(r, j):
        sag = j in right_cols
        if r == 0:
            return head_r if sag else st.cell_b
        return st.cell_r if sag else st.cell
    data = [[Paragraph(_p(c), style(r, j)) for j, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[width * x for x in ratios], repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), st.light), ('LINEBELOW', (0, 0), (-1, -1), 0.4, st.line),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def _side_by_side(left, right, W):
    t = Table([[left, right]], colWidths=[W * 0.51, W * 0.49])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    return t


def _contact_block(m, assets, st, width):
    left = [Paragraph(_p('İletişim'), st.h2), _kv_table(common.advisor_rows(m), st, width * 0.62, 0.3)]
    qrs = []
    for key, label in common.QR_LABELS:
        if assets.get(key):
            qrs.append([Image(assets[key], width=2.6 * cm, height=2.6 * cm), Paragraph(_p(label), st.center)])
    right = Table([[q for q in qrs]], colWidths=[3.2 * cm] * len(qrs)) if qrs else Spacer(1, 1)
    if qrs:
        right.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'BOTTOM')]))
    t = Table([[left, right]], colWidths=[width * 0.66, width * 0.34])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    return t


def render_pdf(m, assets, path):
    _register_fonts()
    st = _Styles(m)
    margin = 1.6 * cm
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=2.2 * cm,
                          bottomMargin=1.8 * cm, title=f"{m.baslik} - {m.konum}", author=m.brand.name,
                          subject=m.ada_parsel or m.konum)
    W = doc.width

    def on_page(canvas, d):
        canvas.saveState()
        pw, ph = A4
        canvas.setFillColor(st.primary)
        canvas.rect(0, ph - 1.25 * cm, pw, 1.25 * cm, stroke=0, fill=1)
        canvas.setFillColor(st.accent)
        canvas.rect(0, ph - 1.25 * cm - 1.2 * mm, pw, 1.2 * mm, stroke=0, fill=1)
        x = margin
        if m.brand.logo_path:
            canvas.drawImage(m.brand.logo_path, x, ph - 1.12 * cm, width=1.0 * cm, height=1.0 * cm,
                             preserveAspectRatio=True, mask='auto')
            x += 1.3 * cm
        canvas.setFillColor(colors.white)
        canvas.setFont(FONT_B, 11)
        canvas.drawString(x, ph - 0.78 * cm, m.brand.name)
        canvas.setFont(FONT, 8.5)
        canvas.drawRightString(pw - margin, ph - 0.78 * cm, m.satir(m.kod, m.konum, m.ada_parsel))
        canvas.setFillColor(st.muted)
        canvas.setFont(FONT, 7.5)
        foot = f"{m.brand.name}{'  ·  ' + m.brand.web if m.brand.web else ''}  ·  Rapor tarihi {m.tarih.strftime('%d.%m.%Y')}"
        canvas.drawString(margin, 1.0 * cm, foot)
        canvas.drawRightString(pw - margin, 1.0 * cm, f"Sayfa {d.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id='p', frames=[Frame(margin, doc.bottomMargin, W, doc.height, id='f')],
                                       onPage=on_page)])
    E = []

    # --- Başlık ve özet
    E.append(Paragraph(_p(m.baslik), st.h1))
    E.append(Paragraph(_p(m.satir(m.kod, m.konum, m.ada_parsel, m.tarih.strftime('%d.%m.%Y'))), st.sub))
    E.append(_kpi_row(m, st, W))
    E.append(_section('Değerlendirme özeti', st))
    E.append(Paragraph(_p(m.fiyat_ozet), st.body))

    # --- Konum ve gayrimenkul bilgileri
    if assets.get('harita'):
        E.append(KeepTogether([_section('Konum', st), _image(assets['harita'], W, 7.2 * cm)]))
    if common.show_zoning(m):
        blok = [_section('Arsa ve imar bilgileri', st),
                _side_by_side(_kv_table(common.location_rows(m), st, W * 0.49),
                              _kv_table(common.zoning_rows(m), st, W * 0.49), W)]
    else:
        blok = [_section('Konum bilgileri', st), _kv_table(common.location_rows(m), st, W * 0.6, 0.35)]
    if m.arsa_mi:
        blok += [Spacer(1, 6), Paragraph(_p('Altyapı'), st.cell_b), Spacer(1, 3), _altyapi_table(m, st, W)]
    E.append(KeepTogether(blok))
    if m.cok_parsel:
        E.append(KeepTogether([
            _section(common.parcel_section_title(m), st),
            _grid_table(common.parcel_table(m), st, W, common.PARCEL_RATIOS, right_cols=common.PARCEL_RIGHT),
            Spacer(1, 4), Paragraph(_p(common.parcel_summary(m)), st.cell_b)]))
    if m.tur_bilgileri:
        E.append(KeepTogether([_section(f"{m.tur_etiketi} bilgileri", st),
                               _kv_table(m.tur_bilgileri, st, W * 0.7, 0.4)]))
    if m.ozellik_gruplari:
        oz = [_section('Özellikler', st)]
        oz += [Paragraph(f"<b>{_p(baslik)}:</b> {_p(', '.join(liste))}", st.body) for baslik, liste in m.ozellik_gruplari]
        E.append(KeepTogether(oz))

    # --- Fiyat ve emsal analizi
    if not m.tanitim:
        E.append(CondPageBreak(6 * cm))
        E.append(_section(common.FIYAT_BASLIK, st))
        E.append(_side_by_side(_kv_table(m.fiyat_satirlari, st, W * 0.49),
                               _kv_table(common.bolge_rows(m), st, W * 0.49, 0.4), W))
        emsal = common.emsal_table(m)
        if emsal:
            E.append(KeepTogether([Spacer(1, 8), Paragraph(_p('Emsaller'), st.cell_b), Spacer(1, 3),
                                   _grid_table(emsal, st, W, common.emsal_ratios(m), right_cols=common.EMSAL_RIGHT)]))
        if assets.get('price_chart'):
            E.append(KeepTogether([Spacer(1, 8), _image(assets['price_chart'], W * 0.8)]))
    if assets.get('puan_grafik'):
        E.append(KeepTogether([
            _section(f"Uygunluk puanı: {tr_number(m.puan, 0)} / 100 ({m.puan_etiketi})", st),
            _image(assets['puan_grafik'], W * 0.85)]))

    # --- SWOT ve tavsiyeler
    if common.has_swot(m):
        E.append(CondPageBreak(7 * cm))
        E.append(KeepTogether([_section('SWOT analizi', st), _swot_table(m, st, W)]))
    tav = [_section('Tavsiyeler', st)] + [Paragraph('• ' + _p(t), st.body) for t in m.tavsiyeler]
    if m.notlar:
        tav += [Paragraph(_p(m.extras.get('not_basligi', 'Not')), st.cell_b), Paragraph(_p(m.notlar), st.body)]
    E.append(KeepTogether(tav))

    # --- Fotoğraflar
    photos = assets.get('fotograflar') or []
    if photos:
        E.append(_section('Fotoğraflar', st))
        cw = (W - 0.4 * cm) / 2
        rows = []
        for i in range(0, len(photos), 2):
            pair = [Image(p, width=cw, height=cw * 2 / 3) for p in photos[i:i + 2]]
            rows.append(pair + [''] * (2 - len(pair)))
        t = Table(rows, colWidths=[cw + 0.2 * cm] * 2)
        t.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
        E.append(t)

    # --- İletişim
    E.append(CondPageBreak(6 * cm))
    E.append(_contact_block(m, assets, st, W))
    E.append(Spacer(1, 10))
    E.append(Paragraph(_p(common.DISCLAIMER), st.small))
    doc.build(E)
    return path
