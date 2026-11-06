# -*- coding: utf-8 -*-
"""Word (.docx) raporu (python-docx). PDF ile aynı içerik ve sıra."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import common
from .model import tr_number

FONT = 'Calibri'
TEXT = RGBColor(0x2B, 0x2F, 0x36)
MUTED = RGBColor(0x6B, 0x72, 0x80)


def _rgb(hex_color):
    h = hex_color.lstrip('#')
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _shade(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color.lstrip('#'))
    tcPr.append(shd)


def _borders(table, color='DDE2E8', inside=True):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        visible = edge in ('bottom', 'insideH') and inside
        el.set(qn('w:val'), 'single' if visible else 'nil')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:color'), color)
        borders.append(el)
    tblPr.append(borders)


def _run(p, text, size=10, bold=False, color=TEXT, italic=False):
    r = p.add_run(str(text))
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return r


def _para(container, text='', size=10, bold=False, color=TEXT, align=None, space_after=4, italic=False):
    p = container.add_paragraph()
    if text:
        _run(p, text, size, bold, color, italic)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    if align:
        p.alignment = align
    return p


def _cell_text(cell, text, size=9.5, bold=False, color=TEXT, align=None):
    cell.text = ''
    p = cell.paragraphs[0]
    _run(p, text, size, bold, color)
    p.paragraph_format.space_after = Pt(1)
    if align:
        p.alignment = align
    return p


def _heading(doc, text, m):
    p = _para(doc, text, 13, True, _rgb(m.brand.primary), space_after=5)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.keep_with_next = True
    return p


def _no_split(table):
    """Tablo satırlarının sayfa sonunda bölünmesini engelle."""
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        el = OxmlElement('w:cantSplit')
        trPr.append(el)


def _drop_leading_paragraph(cell):
    """Hücreye tablo eklenince başta kalan boş paragrafı kaldır."""
    first = cell.paragraphs[0] if cell.paragraphs else None
    if first is not None and not first.text and len(cell._tc.xpath('./w:tbl')):
        cell._tc.remove(first._p)


def _kv_table(doc_or_cell, rows, width_cm, label_ratio=0.42):
    t = doc_or_cell.add_table(rows=len(rows), cols=2)
    _no_split(t)
    _borders(t)
    for i, (k, v) in enumerate(rows):
        a, b = t.rows[i].cells
        a.width, b.width = Cm(width_cm * label_ratio), Cm(width_cm * (1 - label_ratio))
        _cell_text(a, k, bold=True)
        _cell_text(b, v)
        if i % 2:
            _shade(a, 'F3F5F8')
            _shade(b, 'F3F5F8')
    return t


def _picture(doc, path, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    p.add_run().add_picture(path, width=Cm(width_cm))
    return p


def render_word(m, assets, path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.8)
    sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.6)
    W = 21 - 3.6
    pri = _rgb(m.brand.primary)

    style = doc.styles['Normal']
    style.font.name = FONT
    style.font.size = Pt(10)

    # Üst bilgi / alt bilgi
    hp = sec.header.paragraphs[0]
    if m.brand.logo_path:
        hp.add_run().add_picture(m.brand.logo_path, height=Cm(0.9))
        hp.add_run('  ')
    _run(hp, m.brand.name, 11, True, pri)
    _run(hp, "     " + m.satir(m.konum, m.ada_parsel, ayirici=" · "), 8.5, False, MUTED)
    fp = sec.footer.paragraphs[0]
    _run(fp, f"{m.brand.name}{' · ' + m.brand.web if m.brand.web else ''} · Rapor tarihi {m.tarih.strftime('%d.%m.%Y')}", 8, color=MUTED)

    # Başlık
    _para(doc, m.baslik, 20, True, pri, space_after=2)
    _para(doc, m.satir(m.konum, m.ada_parsel, m.tarih.strftime('%d.%m.%Y'), ayirici=' · '), 11, color=MUTED, space_after=10)

    # Göstergeler
    k = doc.add_table(rows=1, cols=4)
    k.alignment = WD_TABLE_ALIGNMENT.CENTER
    _borders(k, inside=False)
    for cell, (label, value, note) in zip(k.rows[0].cells, common.kpis(m)):
        cell.width = Cm(W / 4)
        _shade(cell, 'F3F5F8')
        _cell_text(cell, label.upper(), 7.5, color=MUTED)
        p = cell.add_paragraph(); _run(p, value, 13, True, pri); p.paragraph_format.space_after = Pt(0)
        p = cell.add_paragraph(); _run(p, note, 7.5, color=MUTED); p.paragraph_format.space_after = Pt(3)

    _heading(doc, 'Değerlendirme özeti', m)
    _para(doc, m.temel_ozet)
    _para(doc, m.yatirim_ozet)

    if assets.get('harita'):
        _heading(doc, 'Konum', m)
        _picture(doc, assets['harita'], W * 0.95)

    _heading(doc, 'Arsa ve imar bilgileri', m)
    outer = doc.add_table(rows=1, cols=2)
    lc, rc = outer.rows[0].cells
    lc.width, rc.width = Cm(W * 0.52), Cm(W * 0.48)
    _kv_table(lc, common.parcel_rows(m), W * 0.5)
    _kv_table(rc, common.zoning_rows(m), W * 0.46)
    _drop_leading_paragraph(lc)
    _drop_leading_paragraph(rc)
    p = _para(doc, '', space_after=2); p.paragraph_format.space_before = Pt(6)
    _run(p, 'Altyapı: ', 10, True)
    for label, var in m.altyapi:
        _run(p, '✓ ' if var else '✗ ', 10, True, RGBColor(0x1E, 0x7B, 0x3A) if var else RGBColor(0xB3, 0x26, 0x1E))
        _run(p, f"{label}    ", 10)

    if assets.get('fiyat_grafik'):
        _heading(doc, 'Bölge fiyatı karşılaştırması', m)
        _picture(doc, assets['fiyat_grafik'], W * 0.8)

    _heading(doc, 'Değer projeksiyonu (5 yıl)', m)
    kaynak = 'danışmanın girdiği' if m.artis_kaynagi == 'kullanıcı' else 'modelin tahmin ettiği'
    _para(doc, f"Beklenen senaryo {kaynak} yıllık %{tr_number(m.yillik_artis, 1)} artışa dayanır; temkinli ve "
               f"iyimser senaryolar ±5 puan farkla hesaplanmıştır.", 8.5, color=MUTED)
    _picture(doc, assets['projeksiyon_grafik'], W * 0.85)
    rows = common.scenario_rows(m)
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    _borders(t)
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = t.cell(r, c)
            _cell_text(cell, val, 9, bold=(r == 0 or c == 0),
                       align=WD_ALIGN_PARAGRAPH.RIGHT if c >= 2 and r > 0 else None)
            if r == 0:
                _shade(cell, 'F3F5F8')
            elif r == 2:
                _shade(cell, 'FFF6EA')

    if assets.get('puan_grafik'):
        _heading(doc, f"Uygunluk puanı: {tr_number(m.puan, 0)} / 100 ({m.puan_etiketi})", m)
        _picture(doc, assets['puan_grafik'], W * 0.85)

    _heading(doc, 'SWOT analizi', m)
    fills = ['E6F4EA', 'FCE8E6', 'E8F0FE', 'FEF3E2']
    heads = ['1E7B3A', 'B3261E', '1A56B8', 'A15C07']
    sw = doc.add_table(rows=2, cols=2)
    _borders(sw, inside=False)
    _no_split(sw)
    for i, (title, items) in enumerate(common.swot_blocks(m)):
        cell = sw.cell(i // 2, i % 2)
        cell.width = Cm(W / 2)
        _shade(cell, fills[i])
        _cell_text(cell, title, 10.5, True, _rgb(heads[i]))
        for it in items or ['Belirtilmemiş']:
            p = cell.add_paragraph(); _run(p, f"• {it}" if items else it, 9.5, color=TEXT if items else MUTED)
            p.paragraph_format.space_after = Pt(1)

    _heading(doc, 'Tavsiyeler', m)
    for t_ in m.tavsiyeler:
        _para(doc, f"• {t_}", space_after=2)
    if m.notlar:
        _para(doc, 'Danışman notu', 10, True, space_after=1).paragraph_format.space_before = Pt(6)
        _para(doc, m.notlar)

    photos = assets.get('fotograflar') or []
    if photos:
        _heading(doc, 'Fotoğraflar', m)
        pt = doc.add_table(rows=(len(photos) + 1) // 2, cols=2)
        for i, ph in enumerate(photos):
            cell = pt.cell(i // 2, i % 2)
            cell.paragraphs[0].add_run().add_picture(ph, width=Cm(W / 2 - 0.3))

    _heading(doc, 'İletişim', m)
    ct = doc.add_table(rows=1, cols=2)
    lc, rc = ct.rows[0].cells
    lc.width, rc.width = Cm(W * 0.62), Cm(W * 0.38)
    _kv_table(lc, common.advisor_rows(m), W * 0.58, 0.3)
    _drop_leading_paragraph(lc)
    rp = rc.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    labels = []
    for key, label in (('qr_detay', 'Analiz sayfası'), ('qr_harita', 'Haritada aç')):
        if assets.get(key):
            rp.add_run().add_picture(assets[key], width=Cm(2.6))
            rp.add_run('   ')
            labels.append(label)
    if labels:
        _para(rc, '          '.join(labels), 8, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)

    _para(doc, '', space_after=6)
    _para(doc, common.DISCLAIMER, 7.5, color=MUTED, italic=True)

    doc.core_properties.title = f"{m.baslik} - {m.konum}"
    doc.core_properties.author = m.brand.name
    doc.save(path)
    return path
