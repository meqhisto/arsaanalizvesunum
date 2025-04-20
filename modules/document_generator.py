from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class DocumentGenerator:
    def __init__(self, arsa_data, analiz_ozeti, file_id, output_dir):
        self.arsa_data = arsa_data
        self.analiz_ozeti = analiz_ozeti
        self.file_id = file_id
        self.output_dir = output_dir

    def create_word(self):
        """Word belgesi oluşturur"""
        doc = Document()
        
        # Başlık
        heading = doc.add_heading('Arsa Analiz Raporu', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Temel Bilgiler
        doc.add_heading('1. Arsa Bilgileri', level=1)
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Table Grid'
        
        # Tablo başlıkları
        header_cells = table.rows[0].cells
        header_cells[0].text = 'Özellik'
        header_cells[1].text = 'Değer'
        
        # Temel bilgileri ekle
        data = [
            ('İl', self.arsa_data['il']),
            ('İlçe', self.arsa_data['ilce']),
            ('Mahalle', self.arsa_data['mahalle']),
            ('Ada', self.arsa_data['ada']),
            ('Parsel', self.arsa_data['parsel']),
            ('Pafta', self.arsa_data.get('pafta', 'Belirtilmemiş')),
            ('Koordinatlar', self.arsa_data.get('koordinatlar', 'Belirtilmemiş')),
            ('Metrekare', f"{float(self.arsa_data['metrekare']):,.2f} m²"),
            ('İmar Durumu', self.arsa_data.get('imar_durumu', 'Belirtilmemiş')),
            ('TAKS', f"{float(self.arsa_data.get('taks', 0)):,.2f}"),
            ('KAKS', f"{float(self.arsa_data.get('kaks', 0)):,.2f}"),
            ('Fiyat', f"{float(self.arsa_data['fiyat']):,.2f} TL"),
            ('m² Fiyatı', f"{float(self.arsa_data['fiyat'])/float(self.arsa_data['metrekare']):,.2f} TL/m²"),
            ('Bölge m² Fiyatı', f"{float(self.arsa_data['bolge_fiyat']):,.2f} TL/m²")
        ]
        
        for item in data:
            row_cells = table.add_row().cells
            row_cells[0].text = item[0]
            row_cells[1].text = str(item[1])

        # Altyapı Bilgileri
        doc.add_heading('2. Altyapı Bilgileri', level=1)
        altyapi = self.arsa_data.get('altyapi[]', [])
        if isinstance(altyapi, str):
            altyapi = [altyapi]
        doc.add_paragraph('Mevcut Altyapı Özellikleri:')
        for ozellik in ['yol', 'elektrik', 'su', 'dogalgaz', 'kanalizasyon']:
            doc.add_paragraph(f"• {ozellik.capitalize()}: {'Mevcut' if ozellik in altyapi else 'Mevcut Değil'}", style='List Bullet')

        # SWOT Analizi
        doc.add_heading('3. SWOT Analizi', level=1)
        swot_table = doc.add_table(rows=1, cols=2)
        swot_table.style = 'Table Grid'
        
        # SWOT verilerini ekle
        swot_data = [
            ('Güçlü Yönler', self.arsa_data.get('strengths', [])),
            ('Zayıf Yönler', self.arsa_data.get('weaknesses', [])),
            ('Fırsatlar', self.arsa_data.get('opportunities', [])),
            ('Tehditler', self.arsa_data.get('threats', []))
        ]
        
        for title, items in swot_data:
            row_cells = swot_table.add_row().cells
            row_cells[0].text = title
            if isinstance(items, str):
                try:
                    items = eval(items)
                except:
                    items = [items]
            row_cells[1].text = '\n'.join([f"• {item}" for item in items]) if items else 'Belirtilmemiş'

        # Analiz Sonuçları
        doc.add_heading('4. Analiz Sonuçları', level=1)
        doc.add_paragraph('Temel Özet').bold = True
        doc.add_paragraph(self.analiz_ozeti['temel_ozet'])
        
        doc.add_paragraph('Yatırım Özeti').bold = True
        doc.add_paragraph(self.analiz_ozeti['yatirim_ozet'])
        
        doc.add_paragraph('Tavsiyeler').bold = True
        doc.add_paragraph(self.analiz_ozeti['tavsiyeler'])

        # Dosyayı kaydet
        filename = os.path.join(self.output_dir, f'arsa_analiz_{self.file_id}.docx')
        doc.save(filename)
        return filename

    def create_pdf(self):
        """PDF belgesi oluşturur"""
        # Türkçe karakter desteği için font tanımlama
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        
        filename = os.path.join(self.output_dir, f'arsa_analiz_{self.file_id}.pdf')
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Türkçe karakterler için özel stil
        styles.add(ParagraphStyle(
            name='TurkishStyle',
            fontName='DejaVuSans',
            fontSize=12,
            leading=14,
        ))
        
        story = []

        # Başlık
        title = Paragraph("Arsa Analiz Raporu", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))

        # 1. Arsa Bilgileri
        story.append(Paragraph("1. Arsa Bilgileri", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Arsa Bilgileri Tablosu
        data = [['Özellik', 'Değer']]
        table_data = [
            ('İl', self.arsa_data['il']),
            ('İlçe', self.arsa_data['ilce']),
            ('Mahalle', self.arsa_data['mahalle']),
            ('Ada', self.arsa_data['ada']),
            ('Parsel', self.arsa_data['parsel']),
            ('Pafta', self.arsa_data.get('pafta', 'Belirtilmemiş')),
            ('Koordinatlar', self.arsa_data.get('koordinatlar', 'Belirtilmemiş')),
            ('Metrekare', f"{float(self.arsa_data['metrekare']):,.2f} m²"),
            ('İmar Durumu', self.arsa_data.get('imar_durumu', 'Belirtilmemiş')),
            ('TAKS', f"{float(self.arsa_data.get('taks', 0)):,.2f}"),
            ('KAKS', f"{float(self.arsa_data.get('kaks', 0)):,.2f}"),
            ('Fiyat', f"{float(self.arsa_data['fiyat']):,.2f} TL"),
            ('m² Fiyatı', f"{float(self.arsa_data['fiyat'])/float(self.arsa_data['metrekare']):,.2f} TL/m²"),
            ('Bölge m² Fiyatı', f"{float(self.arsa_data['bolge_fiyat']):,.2f} TL/m²")
        ]
        data.extend(table_data)

        # Tablo stilini oluştur
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # 2. Altyapı Bilgileri
        story.append(Paragraph("2. Altyapı Bilgileri", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        altyapi = self.arsa_data.get('altyapi[]', [])
        if isinstance(altyapi, str):
            altyapi = [altyapi]
            
        for ozellik in ['yol', 'elektrik', 'su', 'dogalgaz', 'kanalizasyon']:
            durum = 'Mevcut' if ozellik in altyapi else 'Mevcut Değil'
            story.append(Paragraph(f"• {ozellik.capitalize()}: {durum}", styles['TurkishStyle']))
        story.append(Spacer(1, 20))

        # 3. SWOT Analizi
        story.append(Paragraph("3. SWOT Analizi", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        swot_data = [
            ('Güçlü Yönler', self.arsa_data.get('strengths', [])),
            ('Zayıf Yönler', self.arsa_data.get('weaknesses', [])),
            ('Fırsatlar', self.arsa_data.get('opportunities', [])),
            ('Tehditler', self.arsa_data.get('threats', []))
        ]
        
        for title, items in swot_data:
            story.append(Paragraph(title, styles['Heading2']))
            if isinstance(items, str):
                try:
                    items = eval(items)
                except:
                    items = [items]
            for item in items:
                story.append(Paragraph(f"• {item}", styles['TurkishStyle']))
            story.append(Spacer(1, 12))

        # 4. Analiz Sonuçları
        story.append(Paragraph("4. Analiz Sonuçları", styles['Heading1']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("Temel Özet:", styles['Heading2']))
        story.append(Paragraph(self.analiz_ozeti['temel_ozet'], styles['TurkishStyle']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("Yatırım Özeti:", styles['Heading2']))
        story.append(Paragraph(self.analiz_ozeti['yatirim_ozet'], styles['TurkishStyle']))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("Tavsiyeler:", styles['Heading2']))
        story.append(Paragraph(self.analiz_ozeti['tavsiyeler'], styles['TurkishStyle']))

        doc.build(story)
        return filename
