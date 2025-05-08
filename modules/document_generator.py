# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage # Image'ı RLImage olarak import et
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import json
import sys
from datetime import datetime
import shutil
import glob
from PIL import Image # Pillow'u import et
import traceback
import sys
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import sqlalchemy
from pptx.enum.text import PP_ALIGN # PowerPoint metin hizalaması için import
import qrcode  # En üstte import ekleyin

class DocumentGenerator:
    def __init__(self, arsa_data, analiz_ozeti, file_id, output_dir, profile_info=None, settings=None):
        # --- YENİ LOG (EN BAŞA) ---
        print("DEBUG [DocGen Init]: __init__ metodu başladı.", flush=True)
        self.arsa_data = arsa_data
        self.analiz_ozeti = analiz_ozeti
        self.file_id = file_id
        self.output_dir = output_dir

        self.analiz_id = arsa_data.get('id')
        print(f"DEBUG [DocGen Init]: Analiz ID: {self.analiz_id}, File ID: {self.file_id}", flush=True) # Flush eklendi
        self.sunum_klasoru = os.path.join(output_dir, file_id)
        print(f"DEBUG [DocGen Init]: Sunum Klasörü: {self.sunum_klasoru}", flush=True) # Flush eklendi

        if not os.path.exists(self.sunum_klasoru):
            try:
                os.makedirs(self.sunum_klasoru)
                print(f"DEBUG [DocGen Init]: Sunum klasörü oluşturuldu: {self.sunum_klasoru}", flush=True) # Flush eklendi
            except Exception as e:
                print(f"HATA [DocGen Init]: Sunum klasörü oluşturulamadı: {e}", flush=True) # Flush eklendi
        # --- YENİ LOG ---
        print("DEBUG [DocGen Init]: __init__ metodu tamamlandı.", flush=True)
        self.profile_info = profile_info or {}
        
        # Establish default settings
        _default_settings = {
            'theme': 'classic',
            'color_scheme': 'blue',
            'sections': ['profile', 'property', 'infrastructure', 'swot', 'photos', 'qr_code']
        }
        
        # Start with defaults
        self.settings = _default_settings.copy()
        
        if settings: # If settings are provided from app.py
            # Override theme and color_scheme if present
            if 'theme' in settings:
                self.settings['theme'] = settings['theme']
            if 'color_scheme' in settings:
                self.settings['color_scheme'] = settings['color_scheme']
            
            # Handle 'sections' specifically:
            # If 'sections' is provided in settings AND it's a non-empty list, use it.
            # Otherwise (if 'sections' not in settings, or is an empty list), keep the default 'sections'.
            if 'sections' in settings and isinstance(settings['sections'], list) and settings['sections']:
                self.settings['sections'] = settings['sections']

        self.colors = self._get_color_scheme()
        self.logo_path = "/static/logo.png"

    def _get_color_scheme(self):
        """Seçilen renk şemasına göre renkleri döndürür"""
        schemes = {
            'blue': {
                'primary': RGBColor(26, 35, 126),  # Koyu Mavi
                'secondary': RGBColor(63, 81, 181), # Orta Mavi
                'accent': RGBColor(33, 150, 243),   # Açık Mavi
                'background': '#E3F2FD'             # En Açık Mavi (HexColor için # eklendi)
            },
            'green': {
                'primary': RGBColor(27, 94, 32),    # Koyu Yeşil
                'secondary': RGBColor(56, 142, 60),  # Orta Yeşil
                'accent': RGBColor(76, 175, 80),     # Açık Yeşil
                'background': '#E8F5E9'              # En Açık Yeşil (HexColor için # eklendi)
            },
            'purple': {
                'primary': RGBColor(74, 20, 140),    # Koyu Mor
                'secondary': RGBColor(123, 31, 162), # Orta Mor
                'accent': RGBColor(156, 39, 176),    # Açık Mor
                'background': '#F3E5F5'              # En Açık Mor (HexColor için # eklendi)
            }
        }
        return schemes.get(self.settings['color_scheme'], schemes['blue'])

    def _should_include_section(self, section):
        """Belirli bir bölümün rapora dahil edilip edilmeyeceğini kontrol eder"""
        return section in self.settings['sections']

    def _format_currency(self, value):
        """Para birimini formatlayan yardımcı metod"""
        try:
            # Gelen değerin float olduğundan emin ol
            float_value = float(value)
            return f"{float_value:,.2f} TL".replace(',', 'X').replace('.', ',').replace('X', '.') # Türkçe format
        except (TypeError, ValueError):
            return "0,00 TL"

    def _format_area(self, value):
        """Alan birimini formatlayan yardımcı metod"""
        try:
             # Gelen değerin float olduğundan emin ol
            float_value = float(value)
            return f"{float_value:,.2f} m²".replace(',', 'X').replace('.', ',').replace('X', '.') # Türkçe format
        except (TypeError, ValueError):
            return "0,00 m²"

    def _get_arsa_bilgileri(self):
        """Arsa bilgilerini hazırlayan yardımcı metod"""
        try:
            fiyat = float(self.arsa_data.get('fiyat', 0))
            metrekare = float(self.arsa_data.get('metrekare', 1))
            metrekare_fiyati = fiyat / metrekare if metrekare > 0 else 0
        except (TypeError, ValueError):
            fiyat = 0
            metrekare = 1
            metrekare_fiyati = 0

        return [
            ['İl/İlçe', f"{self.arsa_data.get('il', '')}/{self.arsa_data.get('ilce', '')}"],
            ['Mahalle', self.arsa_data.get('mahalle', '')],
            ['Ada/Parsel', f"{self.arsa_data.get('ada', '')}/{self.arsa_data.get('parsel', '')}"],
            ['Alan', self._format_area(metrekare)],
            ['İmar Durumu', self.arsa_data.get('imar_durumu', '')],
            ['TAKS/KAKS', f"{self.arsa_data.get('taks', '')}/{self.arsa_data.get('kaks', '')}"],
            ['Toplam Fiyat', self._format_currency(fiyat)],
            ['m² Fiyatı', self._format_currency(metrekare_fiyati)],
        ]

    def _get_altyapi_durumu(self):
        """Altyapı durumunu hazırlayan yardımcı metod"""
        # Anahtar adını 'altyapi[]' olarak düzeltelim (app.py'den gelenle eşleşsin)
        altyapi_list = self.arsa_data.get('altyapi[]', [])

        # Eğer altyapi[] bir string ise (tek bir değer seçilmişse)
        # onu bir listeye dönüştür (Bu durum artık olmamalı ama garanti olsun)
        if isinstance(altyapi_list, str):
            altyapi_list = [altyapi_list]
        # Eğer None ise boş liste yap
        elif altyapi_list is None:
            altyapi_list = []

        return [
            ['Yol', '✓' if 'yol' in altyapi_list else '✗'],
            ['Elektrik', '✓' if 'elektrik' in altyapi_list else '✗'],
            ['Su', '✓' if 'su' in altyapi_list else '✗'],
            ['Doğalgaz', '✓' if 'dogalgaz' in altyapi_list else '✗'],
            ['Kanalizasyon', '✓' if 'kanalizasyon' in altyapi_list else '✗']
        ]

    def _get_swot_analizi(self):
        """SWOT analizini hazırlayan yardımcı metod"""
        swot_data = {
            'Güçlü Yönler': self.arsa_data.get('strengths', []),
            'Zayıf Yönler': self.arsa_data.get('weaknesses', []),
            'Fırsatlar': self.arsa_data.get('opportunities', []),
            'Tehditler': self.arsa_data.get('threats', [])
        }

        # Gelen verinin zaten liste olması beklenir (app.py'de parse ediliyor)
        # Ama yine de kontrol edelim
        for key, value in swot_data.items():
            if isinstance(value, str):
                try:
                    # JSON string ise parse et
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, list):
                        swot_data[key] = parsed_value
                    else:
                        # JSON ama liste değilse, tek elemanlı listeye çevir
                        swot_data[key] = [str(parsed_value)]
                except json.JSONDecodeError:
                    # JSON değilse ve boş değilse, tek elemanlı listeye çevir
                    swot_data[key] = [value] if value else []
            elif not isinstance(value, list):
                 # Liste veya string değilse (örn. None), boş listeye çevir
                 swot_data[key] = []

        return swot_data

    def _set_cell_background(self, cell, color):
        """Tablo hücresinin arka plan rengini ayarlar"""
        try:
            shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
            cell._tc.get_or_add_tcPr().append(shading_elm)
        except Exception as e:
            print(f"Hücre arkaplanı ayarlanamadı: {e}")


    def _get_uploaded_images(self):
        # --- YENİ LOG ---
        print("DEBUG [DocGen GetImages]: _get_uploaded_images metodu başladı.", flush=True)
        if not self.analiz_id:
            print("UYARI [DocGen GetImages]: Analiz ID bulunamadı. Resimler aranamıyor.", flush=True) # Flush
            return []

        analiz_id_str = str(self.analiz_id)
        print(f"DEBUG [DocGen GetImages]: Analiz ID (str): {analiz_id_str}", flush=True) # Flush
        uploads_dir = os.path.join(self.output_dir.parent, 'uploads', analiz_id_str)
        print(f"DEBUG [DocGen GetImages]: Orijinal resimlerin aranacağı klasör: {uploads_dir}", flush=True) # Flush
        print(f"DEBUG [DocGen GetImages]: Bu klasör var mı? {os.path.exists(uploads_dir)}", flush=True) # Flush

        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
        original_images = []
        if os.path.exists(uploads_dir):
            for ext in image_extensions:
                search_pattern = os.path.join(uploads_dir, ext)
                print(f"DEBUG [DocGen GetImages]: Aranıyor: {search_pattern}", flush=True) # Flush
                found = glob.glob(search_pattern)
                if found:
                     print(f"DEBUG [DocGen GetImages]: Bulunanlar ({ext}): {found}", flush=True) # Flush
                     original_images.extend(found)
        else:
            print(f"UYARI [DocGen GetImages]: Yükleme klasörü bulunamadı: {uploads_dir}", flush=True) # Flush

        original_images = sorted(list(set(original_images)))
        print(f"DEBUG [DocGen GetImages]: Bulunan toplam orijinal resim sayısı (unique): {len(original_images)}", flush=True) # Flush
        print(f"DEBUG [DocGen GetImages]: Bulunan orijinal resimler (unique, sıralı): {original_images}", flush=True) # Flush

        copied_images = []
        print(f"DEBUG [DocGen GetImages]: Kopyalama hedef klasörü: {self.sunum_klasoru}", flush=True) # Flush
        for img_path in original_images:
            dest_path = os.path.join(self.sunum_klasoru, os.path.basename(img_path))
            print(f"DEBUG [DocGen GetImages]: Kopyalama deneniyor: {img_path} -> {dest_path}", flush=True) # Flush
            try:
                shutil.copy(img_path, dest_path)
                print(f"DEBUG [DocGen GetImages]: Kopyalama BAŞARILI.", flush=True) # Flush
                copied_images.append(dest_path)
            except Exception as e:
                print(f"HATA [DocGen GetImages]: Resim kopyalanamadı!", flush=True) # Flush
                print(f"HATA [DocGen GetImages]: Kaynak: {img_path}", flush=True) # Flush
                print(f"HATA [DocGen GetImages]: Hedef: {dest_path}", flush=True) # Flush
                print(f"HATA [DocGen GetImages]: Hata Mesajı: {e}", flush=True) # Flush
                traceback.print_exc(file=sys.stdout) # Konsola yazdır
                sys.stdout.flush() # Zorla
                p1.add_run("Resim yüklenemedi.") # Hata mesajı ekle


        print(f"DEBUG [DocGen GetImages]: Kopyalanan resim sayısı: {len(copied_images)}", flush=True) # Flush
        print(f"DEBUG [DocGen GetImages]: Fonksiyondan dönen (kopyalanmış) resim yolları: {copied_images}", flush=True) # Flush
        # --- YENİ LOG ---
        print("DEBUG [DocGen GetImages]: _get_uploaded_images metodu tamamlandı.", flush=True)
        return copied_images

    def _get_profile_table_data(self):
        """Profil bilgilerini tabloya hazırlar"""
        p = self.profile_info or {}
        created_at = p.get('created_at')
        date_str = created_at.strftime('%d.%m.%Y %H:%M') if created_at else '-'
        
        return [
            ['Ad Soyad', f"{p.get('ad','') or ''} {p.get('soyad','') or ''}"],
            ['Ünvan', p.get('unvan', '-')],
            ['Firma', p.get('firma', '-')],
            ['E-posta', p.get('email', '-')],
            ['Telefon', p.get('telefon', '-')],
            ['Adres', p.get('adres', '-')],
            ['Analiz Tarihi', date_str]
        ]

    def _get_profile_photo_path(self):
        """Profil fotoğrafı varsa tam yolunu döndürür"""
        pf = self.profile_info.get('profil_foto')
        if pf:
            # pf ör: 'profiles/1/xxx.jpg'
            uploads_dir = os.path.join(self.output_dir.parent, 'uploads')
            full_path = os.path.join(uploads_dir, pf)
            if os.path.exists(full_path):
                return full_path
        return None

    def _add_footer_word(self, doc, text):
        """Tüm Word sayfalarına footer ekler"""
        for section in doc.sections:
            footer = section.footer
            p = footer.paragraphs[0]
            p.text = text
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.size = Pt(9)
            run.font.name = 'Arial'
            run.font.color.rgb = RGBColor(120, 120, 120)

    def _add_footer_pdf(self, canvas, doc):
        """PDF için footer fonksiyonu"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#888888'))
        canvas.drawString(2*cm, 1*cm, "Arsa Analiz Sistemi - www.invecoproje.com")
        canvas.drawRightString(A4[0]-2*cm, 1*cm, f"Sayfa {doc.page}")
        canvas.restoreState()

    def _swot_table_data(self):
        """SWOT'u tabloya uygun şekilde hazırlar"""
        swot = self._get_swot_analizi()
        return [
            [swot.get('Güçlü Yönler', []), swot.get('Zayıf Yönler', [])],
            [swot.get('Fırsatlar', []), swot.get('Tehditler', [])]
        ]

    def _get_insaat_hesaplama(self):
        """İnşaat alanı hesaplama verilerini tabloya hazırlar"""
        # ArsaAnalizci kullanılmadığı için, arsa_data'dan değerleri çek
        hesap = self.arsa_data.get('insaat_hesaplama')
        # Eğer insaat_hesaplama yoksa, manuel hesapla
        if not hesap:
            try:
                metrekare = float(self.arsa_data.get('metrekare', 0))
                taks = float(self.arsa_data.get('taks', 0.3))
                kaks = float(self.arsa_data.get('kaks', 1.5))
                taban_alani = metrekare * taks
                toplam_insaat_alani = metrekare * kaks
                teorik_kat_sayisi = kaks / taks if taks else 0
                tam_kat_sayisi = int(teorik_kat_sayisi)
                hesap = {
                    'taban_alani': taban_alani,
                    'toplam_insaat_alani': toplam_insaat_alani,
                    'teorik_kat_sayisi': teorik_kat_sayisi,
                    'tam_kat_sayisi': tam_kat_sayisi
                }
            except Exception:
                hesap = {
                    'taban_alani': 0,
                    'toplam_insaat_alani': 0,
                    'teorik_kat_sayisi': 0,
                    'tam_kat_sayisi': 0
                }
        return [
            ['Taban Alanı (m²)', f"{hesap['taban_alani']:.2f}"],
            ['Toplam İnşaat Alanı (m²)', f"{hesap['toplam_insaat_alani']:.2f}"],
            ['Teorik Kat Sayısı', f"{hesap['teorik_kat_sayisi']:.2f}"],
            ['Tam Kat Sayısı', f"{hesap['tam_kat_sayisi']}"]
        ]

    def _create_qr_code(self):
        """Analiz detayları için QR kod oluşturur"""
        try:
            # QR kodun içeriği - analiz detay sayfasının URL'i
            qr_data = f"http://192.168.2.14:5000/analiz/{self.arsa_data.get('id')}"
            
            # QR kod ayarları
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            # QR kod görüntüsü oluştur
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # QR kodu kaydet
            qr_path = os.path.join(self.sunum_klasoru, 'qr_code.png')
            qr_image.save(qr_path)
            
            return qr_path
        except Exception as e:
            print(f"QR kod oluşturma hatası: {e}")
            return None

    def create_word(self):
        try:
            print("DEBUG [Create Word]: Word belgesi oluşturma başladı.")
            doc = Document()

            # Sayfa yapılandırması (A4 Yatay)
            sections = doc.sections
            for section in sections:
                section.orientation = 1 # WD_ORIENT.LANDSCAPE (enum yerine direkt değer)
                section.page_width = Cm(29.7)
                section.page_height = Cm(21.0)
                section.left_margin = Cm(1.27) # 0.5 inch
                section.right_margin = Cm(1.27)
                section.top_margin = Cm(1.27)
                section.bottom_margin = Cm(1.27)

            # Kapak Sayfası
            section = doc.sections[0]
            # Logo ekle (varsa)
            if self.logo_path and os.path.exists(self.logo_path):
                p_logo = doc.add_paragraph()
                p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_logo = p_logo.add_run()
                run_logo.add_picture(self.logo_path, width=Inches(2.2))
                p_logo.space_after = Pt(10)
            title = doc.add_heading('', 0)
            title_run = title.add_run('ARSA ANALİZ RAPORU')
            title_run.font.name = 'Arial'
            title_run.font.size = Pt(40)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Alt başlık
            subtitle = doc.add_paragraph() # Heading yerine paragraph kullanalım
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
            subtitle_run = subtitle.add_run(f"{self.arsa_data.get('il', '')}, {self.arsa_data.get('ilce', '')}")
            subtitle_run.font.name = 'Arial'
            subtitle_run.font.size = Pt(28)
            subtitle_run.font.color.rgb = self.colors['secondary']
            subtitle.space_before = Pt(12)
            subtitle.space_after = Pt(30)


            # Tarih
            date_paragraph = doc.add_paragraph()
            date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            date_run = date_paragraph.add_run(datetime.now().strftime('%d.%m.%Y'))
            date_run.font.name = 'Arial'
            date_run.font.size = Pt(14)
            date_run.font.color.rgb = RGBColor(96, 125, 139) # Gri Mavi

            doc.add_page_break()

            # PROFİL SAYFASI (Kapaktan sonra)
            if self._should_include_section('profile'):
                self._add_profile_section_word(doc) # Metod adını _word ile değiştirelim

            # İçindekiler Sayfası
            toc_heading = doc.add_heading('İçindekiler', level=1)
            toc_heading.runs[0].font.name = 'Arial'
            toc_heading.runs[0].font.size = Pt(24)
            sections_list = [
                'Arsa Bilgileri',
                'Altyapı Durumu',
                'SWOT Analizi',
                'Analiz Özeti',
                'Arsa Fotoğrafları'
            ]

            for i, section_name in enumerate(sections_list, 1):
                p = doc.add_paragraph(style='List Number') # Numaralı liste stili
                p.paragraph_format.left_indent = Inches(0.5)
                run = p.add_run(f"{section_name}")
                run.font.name = 'Arial'
                run.font.size = Pt(14)

            doc.add_page_break()

            # Arsa Bilgileri Sayfası
            if self._should_include_section('property'):
                self._add_property_section_word(doc) # Metod adını _word ile değiştirelim

            # Altyapı Durumu - Daha okunaklı tablo
            if self._should_include_section('infrastructure'):
                self._add_infrastructure_section_word(doc) # Metod adını _word ile değiştirelim

            # İnşaat Alanı Hesaplama Tablosu
            heading = doc.add_heading('İnşaat Alanı Hesaplaması', 1)
            heading.runs[0].font.name = 'Arial'
            heading.runs[0].font.size = Pt(20)
            heading.runs[0].font.color.rgb = self.colors['accent']
            data = self._get_insaat_hesaplama()
            table = doc.add_table(rows=len(data), cols=2)
            table.style = 'Table Grid'
            table.autofit = False
            table.allow_autofit = False
            for i, (label, value) in enumerate(data):
                cell1 = table.cell(i, 0)
                cell2 = table.cell(i, 1)
                p1 = cell1.paragraphs[0]
                run1 = p1.add_run(label)
                run1.font.bold = True
                run1.font.name = 'Arial'
                p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
                self._set_cell_background(cell1, "E3F2FD")
                p2 = cell2.paragraphs[0]
                run2 = p2.add_run(value)
                run2.font.name = 'Arial'
                p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
                self._set_cell_background(cell2, "FFFFFF")
                cell1.vertical_alignment = 1
                cell2.vertical_alignment = 1
            doc.add_paragraph()
            doc.add_page_break()

            # SWOT Analizi - 2x2 tablo
            if self._should_include_section('swot'):
                self._add_swot_section_word(doc) # Metod adını _word ile değiştirelim

            # Analiz Özeti - Başlıklar ve paragraflar
            ozet_heading = doc.add_heading('Analiz Özeti', 1)
            ozet_heading.runs[0].font.name = 'Arial'
            ozet_heading.runs[0].font.size = Pt(20)

            ozet_sections = {
                'Temel Değerlendirme': self.analiz_ozeti.get('temel_ozet', 'Değerlendirme bulunamadı.'),
                'Yatırım Değerlendirmesi': self.analiz_ozeti.get('yatirim_ozet', 'Değerlendirme bulunamadı.'),
                'Uygunluk Puanı': self.analiz_ozeti.get('uygunluk_ozet', 'Uygunluk puanı bulunamadı.'), # Uygunluk puanı özeti eklendi
                'Öneriler ve Tavsiyeler': self.analiz_ozeti.get('tavsiyeler', 'Tavsiye bulunamadı.')
            }

            for title, text in ozet_sections.items():
                sub_heading = doc.add_heading(title, level=2)
                run = sub_heading.runs[0]
                run.font.name = 'Arial'
                run.font.size = Pt(16)
                sub_heading.paragraph_format.space_before = Pt(12)
                sub_heading.paragraph_format.space_after = Pt(6)

                p = doc.add_paragraph(text)
                p.runs[0].font.name = 'Arial'
                p.paragraph_format.space_after = Pt(10) # Paragraflar arasına boşluk ekle

            doc.add_page_break()

            # Arsa Fotoğrafları
            if self._should_include_section('photos'):
                self._add_photos_section(doc)

            # QR Kod Sayfası
            qr_path = self._create_qr_code()
            if qr_path and os.path.exists(qr_path):
                 doc.add_page_break()
                 qr_heading = doc.add_heading('Analiz Detayları QR Kod', 1)
                 qr_heading.runs[0].font.name = 'Arial'
                 qr_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
                 
                 p_qr = doc.add_paragraph()
                 p_qr.alignment = WD_ALIGN_PARAGRAPH.CENTER
                 run_qr = p_qr.add_run()
                 # QR kod resmini ekle, boyutunu ayarla
                 run_qr.add_picture(qr_path, width=Inches(3.0)) # Boyutu ayarla
                 p_qr.space_before = Pt(20) # QR kodun üstüne boşluk ekle


            # Footer ekle
            self._add_footer_word(doc, "Arsa Analiz Sistemi - Rapor")

            # Dosya adını oluştur
            il = self.arsa_data.get('il', 'Bilinmiyor')
            ilce = self.arsa_data.get('ilce', 'Bilinmiyor')
            dosya_adi = f"arsa_analiz_{il}_{ilce}_{self.file_id}.docx"
            filepath = os.path.join(self.sunum_klasoru, dosya_adi)

            # Belgeyi kaydet
            doc.save(filepath)
            print(f"DEBUG [Create Word]: Word belgesi kaydedildi: {filepath}")
            return filepath

        except Exception as e:
            print(f"HATA [Create Word]: Word belgesi oluşturulurken hata oluştu: {e}")
            traceback.print_exc(file=sys.stdout) # Konsola yazdır
            sys.stdout.flush() # Zorla
            return None

    def _add_profile_section_word(self, doc):
        """Word belgesine profil bilgilerini ekler"""
        doc.add_heading("Analist Bilgileri", level=1)

        # Profil fotoğrafı ekle (varsa)
        profile_photo_path = self._get_profile_photo_path()
        if profile_photo_path and os.path.exists(profile_photo_path):
            try:
                p_photo = doc.add_paragraph()
                p_photo.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run_photo = p_photo.add_run()
                run_photo.add_picture(profile_photo_path, width=Inches(1.5)) # Boyutu ayarla
                p_photo.space_after = Pt(12)
                print(f"DEBUG [Add Profile Word]: Profil fotoğrafı eklendi: {profile_photo_path}")
            except Exception as e:
                print(f"HATA [Add Profile Word]: Profil fotoğrafı eklenemedi: {e}")
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()

        data = self._get_profile_table_data()
        table = doc.add_table(rows=len(data), cols=2)
        table.style = 'Table Grid' # Veya istediğiniz başka bir stil
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Sütun genişliklerini ayarla (isteğe bağlı)
        table.columns[0].width = Inches(2.5)
        table.columns[1].width = Inches(4.5)

        for i, (label, value) in enumerate(data):
            cell1 = table.cell(i, 0)
            cell2 = table.cell(i, 1)
            p1 = cell1.paragraphs[0]
            run1 = p1.add_run(label)
            run1.font.bold = True
            run1.font.name = 'Arial'
            p2 = cell2.paragraphs[0]
            run2 = p2.add_run(str(value)) # Değeri stringe çevir
            run2.font.name = 'Arial'

        doc.add_paragraph() # Tablodan sonra boşluk
        doc.add_page_break()

    def _add_property_section_word(self, doc):
        """Word belgesine arsa bilgilerini ekler"""
        doc.add_heading("Arsa Bilgileri", level=1)
        data = self._get_arsa_bilgileri()
        table = doc.add_table(rows=len(data), cols=2)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Sütun genişliklerini ayarla
        table.columns[0].width = Inches(2.5)
        table.columns[1].width = Inches(4.5)

        for i, (label, value) in enumerate(data):
            cell1 = table.cell(i, 0)
            cell2 = table.cell(i, 1)
            
            p1 = cell1.paragraphs[0]
            run1 = p1.add_run(label)
            run1.font.bold = True
            run1.font.name = 'Arial'
            self._set_cell_background(cell1, "E3F2FD") # Arkaplan rengi
            
            p2 = cell2.paragraphs[0]
            run2 = p2.add_run(str(value)) # Değeri stringe çevir
            run2.font.name = 'Arial'
            self._set_cell_background(cell2, "FFFFFF") # Arkaplan rengi

        doc.add_paragraph() # Tablodan sonra boşluk
        doc.add_page_break()

    def _add_infrastructure_section_word(self, doc):
        """Word belgesine altyapı durumunu ekler"""
        doc.add_heading("Altyapı Durumu", level=1)
        data = self._get_altyapi_durumu()
        table = doc.add_table(rows=len(data), cols=2)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Sütun genişliklerini ayarla
        table.columns[0].width = Inches(3.5)
        table.columns[1].width = Inches(3.5)

        for i, (label, status) in enumerate(data):
            cell1 = table.cell(i, 0)
            cell2 = table.cell(i, 1)

            p1 = cell1.paragraphs[0]
            run1 = p1.add_run(label)
            run1.font.bold = True
            run1.font.name = 'Arial'
            self._set_cell_background(cell1, "E3F2FD") # Arkaplan rengi

            p2 = cell2.paragraphs[0]
            run2 = p2.add_run(status)
            run2.font.name = 'Arial'
            # Duruma göre metin rengini ayarla
            if status == '✓':
                run2.font.color.rgb = RGBColor(0, 128, 0) # Yeşil
            else:
                run2.font.color.rgb = RGBColor(255, 0, 0) # Kırmızı
            self._set_cell_background(cell2, "FFFFFF") # Arkaplan rengi

        doc.add_paragraph() # Tablodan sonra boşluk
        doc.add_page_break()

    def _add_swot_section_word(self, doc):
        """Word belgesine SWOT analizini ekler"""
        doc.add_heading("SWOT Analizi", level=1)
        swot_data = self._get_swot_analizi()

        # SWOT başlıkları ve renkleri (Word'de renkler farklı uygulanabilir)
        swot_titles = {
            'Güçlü Yönler': RGBColor(0, 128, 0), # Yeşil
            'Zayıf Yönler': RGBColor(255, 0, 0), # Kırmızı
            'Fırsatlar': RGBColor(0, 0, 255),   # Mavi
            'Tehditler': RGBColor(255, 165, 0)    # Turuncu
        }

        # 2x2 tablo oluştur
        table = doc.add_table(rows=2, cols=2)
        table.style = 'Table Grid' # Veya istediğiniz başka bir stil
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Hücrelere başlıkları ve içerikleri yerleştir
        cells_data = [
            (swot_titles['Güçlü Yönler'], "Güçlü Yönler", swot_data.get('Güçlü Yönler', [])),
            (swot_titles['Zayıf Yönler'], "Zayıf Yönler", swot_data.get('Zayıf Yönler', [])),
            (swot_titles['Fırsatlar'], "Fırsatlar", swot_data.get('Fırsatlar', [])),
            (swot_titles['Tehditler'], "Tehditler", swot_data.get('Tehditler', []))
        ]

        for i, (color, title, items) in enumerate(cells_data):
            row = i // 2
            col = i % 2
            cell = table.cell(row, col)
            
            # Başlık paragrafı
            p_title = cell.paragraphs[0] # Mevcut paragrafı kullan
            run_title = p_title.add_run(title)
            run_title.font.bold = True
            run_title.font.name = 'Arial'
            run_title.font.size = Pt(14)
            run_title.font.color.rgb = color
            
            # İçerik maddeleri
            for item_text in items:
                p_item = cell.add_paragraph(f"- {item_text}")
                p_item.runs[0].font.name = 'Arial'
                p_item.runs[0].font.size = Pt(10)
        doc.add_page_break()


    def create_pdf(self):
        try:
            print("DEBUG [Create PDF]: PDF belgesi oluşturma başladı.")
            # --- FONT KAYITLARI BAŞLANGICI ---
            # Projenizin ana dizinini bulun (app.py'nin olduğu yer)
            project_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fonts_dir = os.path.join(project_base_dir, 'static', 'fonts') # Fontların olduğu varsayılan klasör

            # Fontları ReportLab'a kaydet
            # Bu dosya yollarının doğru olduğundan emin olun!
            pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(fonts_dir, 'DejaVuSans.ttf')))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')))
            # --- FONT KAYITLARI SONU ---

            # Fontları kaydet (Türkçe karakter desteği için)

            # Stil şablonunu al
            styles = getSampleStyleSheet()
            # Normal stilin kopyasını oluştur ve fontu ayarla
            styleN = styles['Normal']
            styleN.fontName = 'DejaVuSans'
            styleN.fontSize = 10
            styleN.leading = 14 # Satır aralığı
            styleN.alignment = TA_LEFT

            # Başlık stilleri
            styleHeading1 = styles['Heading1']
            styleHeading1.fontName = 'DejaVuSans-Bold'
            styleHeading1.fontSize = 24
            styleHeading1.leading = 28
            styleHeading1.spaceAfter = 14

            styleHeading2 = styles['Heading2']
            styleHeading2.fontName = 'DejaVuSans-Bold'
            styleHeading2.fontSize = 16
            styleHeading2.leading = 20
            styleHeading2.spaceBefore = 12
            styleHeading2.spaceAfter = 6


            # Belge oluşturma ayarları
            il = self.arsa_data.get('il', 'Bilinmiyor')
            ilce = self.arsa_data.get('ilce', 'Bilinmiyor')
            dosya_adi = f"arsa_analiz_{il}_{ilce}_{self.file_id}.pdf"
            filepath = os.path.join(self.sunum_klasoru, dosya_adi)

            doc = SimpleDocTemplate(
                filepath,
                pagesize=landscape(A4),
                rightMargin=1.27*cm, leftMargin=1.27*cm,
                topMargin=1.27*cm, bottomMargin=1.27*cm,
                title=f"Gayrimenkul Analiz Raporu - {il}, {ilce}"
            )

            elements = []

            # Kapak Sayfası
            # Logo ekle (varsa)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # modules'ten app.py'nin olduğu yere
            logo_full_path = os.path.join(base_dir, self.logo_path.lstrip('/'))
            print(f"DEBUG [Create PDF]: Logo yolu deneniyor: {logo_full_path}")
            if os.path.exists(logo_full_path):
                 try:
                     img = RLImage(logo_full_path, width=2.2*inch, height=2.2*inch)
                     img.hAlign = 'CENTER'
                     elements.append(img)
                     elements.append(Spacer(1, 0.2*inch))
                     print("DEBUG [Create PDF]: Logo eklendi.")
                 except Exception as img_e:
                     print(f"HATA [Create PDF]: Logo eklenemedi: {img_e}")


            # Başlık
            title_text = f"GAYRİMENKUL ANALİZ RAPORU\n{il}, {ilce}"
            title_style = ParagraphStyle(
                name='TitleStyle',
                parent=styles['Heading1'],
                fontName='DejaVuSans-Bold',
                fontSize=36,
                leading=40,
                alignment=TA_CENTER,
                spaceAfter=20,
            )
            elements.append(Paragraph(title_text, title_style))

            # Tarih
            date_style = ParagraphStyle(
                name='DateStyle',
                parent=styles['Normal'],
                fontName='DejaVuSans',
                fontSize=12,
                alignment=TA_CENTER,
                textColor = colors.HexColor('#607D8B') # Gri Mavi
            )
            elements.append(Paragraph(datetime.now().strftime('%d.%m.%Y'), date_style))

            elements.append(PageBreak())

            # PROFİL SAYFASI
            if self._should_include_section('profile'):
                 elements.extend(self._add_profile_section_pdf(styles))
                 elements.append(PageBreak())


            # İçindekiler (Manuel olarak ekleyelim şimdilik)
            elements.append(Paragraph("İçindekiler", styleHeading1))
            toc_items = [
                'Gayrimenkul Bilgileri',
                'Altyapı Durumu',
                'SWOT Analizi',
                'Analiz Özeti',
                'Gayrimenkul Fotoğrafları'
            ]
            for i, item in enumerate(toc_items, 1):
                 elements.append(Paragraph(f"{i}. {item}", styleN))
            elements.append(PageBreak())


            # Arsa Bilgileri
            if self._should_include_section('property'):
                 elements.extend(self._add_property_section_pdf(styles))
                 elements.append(PageBreak())

            # Altyapı Durumu
            if self._should_include_section('infrastructure'):
                 elements.extend(self._add_infrastructure_section_pdf(styles))
                 elements.append(PageBreak())

            # İnşaat Alanı Hesaplama
            elements.append(Paragraph("İnşaat Alanı Hesaplaması", styleHeading1))
            insaat_data = self._get_insaat_hesaplama()
            insaat_table_data = [['Özellik', 'Değer']]
            for label, value in insaat_data:
                 insaat_table_data.append([label, value])

            insaat_table = Table(insaat_table_data, colWidths=[5*cm, 5*cm])
            insaat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors['background'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(insaat_table)
            elements.append(PageBreak())


            # SWOT Analizi
            if self._should_include_section('swot'):
                 elements.extend(self._add_swot_section_pdf(styles))
                 elements.append(PageBreak())

            # Analiz Özeti
            elements.append(Paragraph("Analiz Özeti", styleHeading1))

            ozet_sections_pdf = {
                'Temel Değerlendirme': self.analiz_ozeti.get('temel_ozet', 'Değerlendirme bulunamadı.'),
                'Yatırım Değerlendirmesi': self.analiz_ozeti.get('yatirim_ozet', 'Değerlendirme bulunamadı.'),
                'Uygunluk Puanı': self.analiz_ozeti.get('uygunluk_ozet', 'Uygunluk puanı bulunamadı.'), # Uygunluk puanı özeti eklendi
                'Öneriler ve Tavsiyeler': self.analiz_ozeti.get('tavsiyeler', 'Tavsiye bulunamadı.')
            }

            for title, text in ozet_sections_pdf.items():
                 elements.append(Paragraph(title, styleHeading2))
                 elements.append(Paragraph(text, styleN))
                 elements.append(Spacer(1, 0.2*inch)) # Paragraflar arasına boşluk

            elements.append(PageBreak())

            # Arsa Fotoğrafları
            if self._should_include_section('photos'):
                 elements.extend(self._add_photos_section_pdf(styles))
                 elements.append(PageBreak())

            # QR Kod Sayfası
            qr_path = self._create_qr_code()
            if qr_path and os.path.exists(qr_path):
                 elements.append(PageBreak())
                 qr_heading_style = ParagraphStyle(
                     name='QRHeadingStyle',
                     parent=styles['Heading1'],
                     fontName='DejaVuSans-Bold',
                     fontSize=24,
                     leading=28,
                     alignment=TA_CENTER,
                     spaceAfter=14,
                 )
                 elements.append(Paragraph("Analiz Detayları QR Kod", qr_heading_style))

                 try:
                     qr_img = RLImage(qr_path, width=3.0*inch, height=3.0*inch) # Boyutu ayarla
                     qr_img.hAlign = 'CENTER'
                     elements.append(qr_img)
                     elements.append(Spacer(1, 0.2*inch)) # QR kodun altına boşluk
                 except Exception as qr_img_e:
                     print(f"HATA [Create PDF]: QR kod resmi eklenemedi: {qr_img_e}")


            # Belgeyi oluştur
            doc.build(elements, onFirstPage=self._add_footer_pdf, onLaterPages=self._add_footer_pdf)
            print(f"DEBUG [Create PDF]: PDF belgesi kaydedildi: {filepath}")
            return filepath

        except Exception as e:
            print(f"HATA [Create PDF]: PDF belgesi oluşturulurken hata oluştu: {e}")
            traceback.print_exc(file=sys.stdout) # Konsola yazdır
            sys.stdout.flush() # Zorla
            return None

    def _add_profile_section_pdf(self, styles):
        """PDF belgesine profil bilgilerini ekler"""
        elements = []
        styleHeading1 = styles['Heading1']
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans' # Fontu ayarla

        elements.append(Paragraph("Analist Bilgileri", styleHeading1))

        # Profil fotoğrafı ekle (varsa)
        profile_photo_path = self._get_profile_photo_path()
        if profile_photo_path and os.path.exists(profile_photo_path):
            try:
                img = RLImage(profile_photo_path, width=1.5*inch, height=1.5*inch) # Boyutu ayarla
                img.hAlign = 'CENTER'
                elements.append(img)
                elements.append(Spacer(1, 0.2*inch))
                print(f"DEBUG [Add Profile PDF]: Profil fotoğrafı eklendi: {profile_photo_path}")
            except Exception as e:
                print(f"HATA [Add Profile PDF]: Profil fotoğrafı eklenemedi: {e}")
                traceback.print_exc(file=sys.stdout) # Konsola yazdır
                sys.stdout.flush() # Zorla


        data = self._get_profile_table_data()
        table_data = [['Özellik', 'Değer']] # Başlık satırı
        for label, value in data:
            table_data.append([label, value])

        table = Table(table_data, colWidths=[4*cm, 8*cm]) # Sütun genişliklerini ayarla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors['background'])), # Başlık satırı arkaplan
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')), # Başlık satırı yazı rengi
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'), # Başlık fontu
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'), # İçerik fontu
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white), # İçerik satırları arkaplan
            ('GRID', (0, 0), (-1, -1), 1, colors.black), # Tablo çizgileri
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch)) # Tablodan sonra boşluk
        return elements

    def _add_property_section_pdf(self, styles):
        """PDF belgesine arsa bilgilerini ekler"""
        elements = []
        styleHeading1 = styles['Heading1']
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans' # Fontu ayarla

        elements.append(Paragraph("Arsa Bilgileri", styleHeading1))

        data = self._get_arsa_bilgileri()
        table_data = [['Özellik', 'Değer']] # Başlık satırı
        for label, value in data:
            table_data.append([label, value])

        table = Table(table_data, colWidths=[4*cm, 8*cm]) # Sütun genişliklerini ayarla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors['background'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        return elements

    def _add_infrastructure_section_pdf(self, styles):
        """PDF belgesine altyapı durumunu ekler"""
        elements = []
        styleHeading1 = styles['Heading1']
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans' # Fontu ayarla

        elements.append(Paragraph("Altyapı Durumu", styleHeading1))

        data = self._get_altyapi_durumu()
        table_data = [['Altyapı', 'Durum']] # Başlık satırı
        for label, status in data:
            table_data.append([label, status])

        table = Table(table_data, colWidths=[6*cm, 6*cm]) # Sütun genişliklerini ayarla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors['background'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Duruma göre hücre rengi (PDF'te hücre arkaplanı renklemek daha karmaşık, şimdilik sadece yazı rengi)
            ('TEXTCOLOR', (1, 1), (1, -1), colors.green), # ✓ için yeşil
            ('TEXTCOLOR', (1, 1), (1, -1), colors.red), # ✗ için kırmızı (Bu şekilde olmaz, her satır için ayrı stil gerekir)
            # Alternatif olarak, her hücre için ayrı stil tanımlanabilir veya sadece metin rengi değiştirilebilir.
            # Şimdilik sadece metin rengini değiştirelim.
        ]))

        # Her hücrenin metin rengini duruma göre ayarla
        for i in range(1, len(table_data)):
             status = table_data[i][1]
             if status == '✓':
                 table.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), colors.green)]))
             else:
                 table.setStyle(TableStyle([('TEXTCOLOR', (1, i), (1, i), colors.red)]))


        elements.append(table)
        elements.append(Spacer(1, 0.5*inch))
        return elements

    def _add_swot_section_pdf(self, styles):
        """PDF belgesine SWOT analizini ekler"""
        elements = []
        styleHeading1 = styles['Heading1']
        styleHeading2 = styles['Heading2']
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans' # Fontu ayarla
        styleHeading2.fontName = 'DejaVuSans-Bold' # Başlık fontu

        elements.append(Paragraph("SWOT Analizi", styleHeading1))

        swot_data = self._get_swot_analizi()

        # SWOT başlıkları ve renkleri
        swot_titles = {
            'Güçlü Yönler': colors.green,
            'Zayıf Yönler': colors.red,
            'Fırsatlar': colors.blue,
            'Tehditler': colors.orange
        }

        for title, color in swot_titles.items():
            elements.append(Paragraph(title, ParagraphStyle(
                name=f'{title.replace(" ", "")}Style',
                parent=styleHeading2,
                textColor=color
            )))
            items = swot_data.get(title, [])
            if items:
                for item in items:
                    elements.append(Paragraph(f"- {item}", styleN))
            else:
                elements.append(Paragraph("Veri bulunamadı.", styleN))
            elements.append(Spacer(1, 0.2*inch)) # Maddeler arası boşluk

        elements.append(Spacer(1, 0.5*inch)) # Bölüm sonu boşluk
        return elements

    def _add_photos_section_pdf(self, styles):
        """PDF belgesine yüklenen fotoğrafları ekler"""
        print("DEBUG [Add Photos PDF]: _add_photos_section_pdf metodu başladı.")
        elements = []
        styleHeading1 = styles['Heading1']
        styleN = styles['Normal']
        styleN.fontName = 'DejaVuSans' # Fontu ayarla

        elements.append(Paragraph("Arsa Fotoğrafları", styleHeading1))

        images = self._get_uploaded_images()
        print(f"DEBUG [Add Photos PDF]: Eklenecek resim sayısı: {len(images)}") # Flush

        if not images:
            elements.append(Paragraph("Yüklü fotoğraf bulunamadı.", styleN))
            print("DEBUG [Add Photos PDF]: Yüklü fotoğraf bulunamadı mesajı eklendi.") # Flush
            return elements

        # Resimleri 2 sütunlu bir tabloya yerleştirme
        table_data = []
        row = []
        for i in range(0, len(images), 2):
            row_elements = []
            # İlk sütun
            img_path1 = images[i]
            try:
                # Resim boyutunu ayarla (örn: 8 cm genişlik)
                img1 = RLImage(img_path1, width=8*cm, height=8*cm, kind='proportional')
                img1.hAlign = 'CENTER'
                row_elements.append(img1)
                print(f"DEBUG [Add Photos PDF]: Resim 1 eklendi: {img_path1}") # Flush
            except Exception as e:
                print(f"HATA [Add Photos PDF]: Resim 1 eklenemedi: {img_path1} - {e}") # Flush
                traceback.print_exc(file=sys.stdout) # Konsola yazdır
                sys.stdout.flush() # Zorla
                row_elements.append(Paragraph("Resim yüklenemedi.", styleN)) # Hata mesajı ekle

            # İkinci sütun (varsa)
            if i + 1 < len(images):
                img_path2 = images[i+1]
                try:
                    img2 = RLImage(img_path2, width=8*cm, height=8*cm, kind='proportional')
                    img2.hAlign = 'CENTER'
                    row_elements.append(img2)
                    print(f"DEBUG [Add Photos PDF]: Resim 2 eklendi: {img_path2}") # Flush
                except Exception as e:
                    print(f"HATA [Add Photos PDF]: Resim 2 eklenemedi: {img_path2} - {e}") # Flush
                    traceback.print_exc(file=sys.stdout) # Konsola yazdır
                    sys.stdout.flush() # Zorla
                    row_elements.append(Paragraph("Resim yüklenemedi.", styleN)) # Hata mesajı ekle
            else:
                 # Tek resim varsa ikinci hücre boş kalır
                 row_elements.append(Spacer(1,1)) # Boşluk ekle

            table_data.append(row_elements)


        if table_data:
            table = Table(table_data, colWidths=[9*cm, 9*cm]) # Sütun genişliklerini ayarla
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white), # Arkaplanı beyaz yap
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.5*inch)) # Tablodan sonra boşluk

        print("DEBUG [Add Photos PDF]: _add_photos_section_pdf metodu tamamlandı.") # Flush
        return elements

    def create_pptx(self):
        try:
            print("DEBUG [Create PPTX]: PowerPoint sunumu oluşturma başladı.")
            # Mevcut sunum şablonunu yükle
            template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'sunum', 'ppt_template.pptx')
            print(f"DEBUG [Create PPTX]: Şablon yolu: {template_path}")
            if not os.path.exists(template_path):
                print(f"HATA [Create PPTX]: Şablon dosyası bulunamadı: {template_path}")
                return None

            prs = Presentation(template_path)

            # İlk slayt (Başlık Slaytı)
            title_slide_layout = prs.slide_layouts[0] # Genellikle ilk layout başlık slaytıdır
            slide = prs.slides.add_slide(title_slide_layout)

            # Başlık ve Alt Başlık Placeholder'larını bul ve doldur
            title_placeholder = slide.shapes.title
            subtitle_placeholder = slide.placeholders[1] # Genellikle alt başlık placeholder'ı 1 indexindedir

            title_placeholder.text = "ARSA ANALİZ RAPORU"
            subtitle_placeholder.text = f"{self.arsa_data.get('il', '')}, {self.arsa_data.get('ilce', '')}\n{datetime.now().strftime('%d.%m.%Y')}"

            # Logo ekle (varsa) - Şablonda logo placeholder'ı varsa onu kullanabiliriz
            # veya manuel olarak ekleyebiliriz. Manuel ekleyelim şimdilik.
            # Logo yolunu app.py'nin bulunduğu dizine göre ayarla
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # modules'ten app.py'nin olduğu yere
            logo_full_path = os.path.join(base_dir, self.logo_path.lstrip('/'))
            print(f"DEBUG [Create PPTX]: Logo yolu deneniyor: {logo_full_path}")
            if os.path.exists(logo_full_path):
                 try:
                     left = top = Inches(0.5) # Slaytın sol üst köşesine yakın
                     pic = slide.shapes.add_picture(logo_full_path, left, top, width=Inches(1.5)) # Boyutu ayarla
                     print("DEBUG [Create PPTX]: Logo eklendi.")
                 except Exception as e:
                     print(f"HATA [Create PPTX]: Logo eklenemedi: {e}")
                     traceback.print_exc(file=sys.stdout) # Konsola yazdır
                     sys.stdout.flush() # Zorla


            # PROFİL SLAYTI
            if self._should_include_section('profile'):
                 self._add_profile_slide_pptx(prs)

            # ARSA BİLGİLERİ SLAYTI
            if self._should_include_section('property'):
                 self._add_property_slide_pptx(prs)

            # ALTYAPI DURUMU SLAYTI
            if self._should_include_section('infrastructure'):
                 self._add_infrastructure_slide_pptx(prs)

            # İNŞAAT ALANI HESAPLAMA SLAYTI
            self._add_insaat_hesaplama_slide_pptx(prs)

            # SWOT ANALİZİ SLAYTI
            if self._should_include_section('swot'):
                 self._add_swot_slide_pptx(prs)

            # ANALİZ ÖZETİ SLAYTI
            self._add_analiz_ozeti_slide_pptx(prs)

            # ARSA FOTOĞRAFLARI SLAYTI
            if self._should_include_section('photos'):
                 self._add_photos_slide_pptx(prs)

            # QR KOD SLAYTI
            qr_path = self._create_qr_code()
            if qr_path and os.path.exists(qr_path):
                 self._add_qr_code_slide_pptx(prs, qr_path)


            # Dosya adını oluştur
            il = self.arsa_data.get('il', 'Bilinmiyor')
            ilce = self.arsa_data.get('ilce', 'Bilinmiyor')
            dosya_adi = f"arsa_analiz_{il}_{ilce}_{self.file_id}.pptx"
            filepath = os.path.join(self.sunum_klasoru, dosya_adi)

            # Sunumu kaydet
            prs.save(filepath)
            print(f"DEBUG [Create PPTX]: PowerPoint sunumu kaydedildi: {filepath}")
            return filepath

        except Exception as e:
            print(f"HATA [Create PPTX]: PowerPoint sunumu oluşturulurken hata oluştu: {e}")
            traceback.print_exc(file=sys.stdout) # Konsola yazdır
            sys.stdout.flush() # Zorla
            return None

    def _add_profile_slide_pptx(self, prs):
        """PowerPoint sunumuna profil bilgilerini içeren slayt ekler"""
        # Boş bir slayt layout'u seçin (veya şablonda uygun bir layout varsa onu kullanın)
        blank_slide_layout = prs.slide_layouts[5] # Genellikle 5 boş layouttur
        slide = prs.slides.add_slide(blank_slide_layout)

        # Başlık ekle
        title_shape = slide.shapes.title
        title_shape.text = "Analist Bilgileri"

        # Tablo ekle
        data = self._get_profile_table_data()
        rows = len(data) + 1 # Başlık satırı için +1
        cols = 2
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(8), Inches(4) # Tablo konumu ve boyutu (örnek)
        shape = slide.shapes.add_table(rows, cols, x, y, cx, cy)
        table = shape.table

        # Başlık satırını doldur
        cell = table.cell(0, 0)
        cell.text = "Özellik"
        cell = table.cell(0, 1)
        cell.text = "Değer"

        # Veri satırlarını doldur
        for i, (label, value) in enumerate(data):
            cell = table.cell(i + 1, 0)
            cell.text = label
            cell = table.cell(i + 1, 1)
            cell.text = value

        # Tablo stilini ayarla (isteğe bağlı)
        # table.first_row = True # İlk satırı başlık olarak biçimlendir
        # table.banded_rows = True # Şeritli satırlar

        # Profil fotoğrafı ekle (varsa)
        profile_photo_path = self._get_profile_photo_path()
        if profile_photo_path and os.path.exists(profile_photo_path):
            try:
                img_x, img_y, img_cx, img_cy = Inches(9.5), Inches(1.5), Inches(1.5), Inches(1.5) # Resim konumu ve boyutu (örnek)
                slide.shapes.add_picture(profile_photo_path, img_x, img_y, width=img_cx, height=img_cy)
                print(f"DEBUG [Add Profile PPTX]: Profil fotoğrafı eklendi: {profile_photo_path}")
            except Exception as e:
                print(f"HATA [Add Profile PPTX]: Profil fotoğrafı eklenemedi: {e}")
                traceback.print_exc(file=sys.stdout) # Konsola yazdır
                sys.stdout.flush() # Zorla


    def _add_property_slide_pptx(self, prs):
        """PowerPoint sunumuna arsa bilgilerini içeren slayt ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "Arsa Bilgileri"

        data = self._get_arsa_bilgileri()
        rows = len(data) + 1
        cols = 2
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(8), Inches(4)
        shape = slide.shapes.add_table(rows, cols, x, y, cx, cy)
        table = shape.table

        cell = table.cell(0, 0)
        cell.text = "Özellik"
        cell = table.cell(0, 1)
        cell.text = "Değer"

        for i, (label, value) in enumerate(data):
            cell = table.cell(i + 1, 0)
            cell.text = label
            cell = table.cell(i + 1, 1)
            cell.text = value

    def _add_infrastructure_slide_pptx(self, prs):
        """PowerPoint sunumuna altyapı durumunu içeren slayt ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "Altyapı Durumu"

        data = self._get_altyapi_durumu()
        rows = len(data) + 1
        cols = 2
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(6), Inches(3)
        shape = slide.shapes.add_table(rows, cols, x, y, cx, cy)
        table = shape.table

        cell = table.cell(0, 0)
        cell.text = "Altyapı"
        cell = table.cell(0, 1)
        cell.text = "Durum"

        for i, (label, status) in enumerate(data):
            cell = table.cell(i + 1, 0)
            cell.text = label
            cell = table.cell(i + 1, 1)
            cell.text = status
            # Duruma göre metin rengini ayarla (PowerPoint'te hücre arkaplanı renklemek daha karmaşık)
            if status == '✓':
                 cell.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 128, 0) # Yeşil
            else:
                 cell.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 0, 0) # Kırmızı


    def _add_insaat_hesaplama_slide_pptx(self, prs):
        """PowerPoint sunumuna inşaat alanı hesaplamasını içeren slayt ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "İnşaat Alanı Hesaplaması"

        data = self._get_insaat_hesaplama()
        rows = len(data) + 1
        cols = 2
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(6), Inches(3)
        shape = slide.shapes.add_table(rows, cols, x, y, cx, cy)
        table = shape.table

        cell = table.cell(0, 0)
        cell.text = "Özellik"
        cell = table.cell(0, 1)
        cell.text = "Değer"

        for i, (label, value) in enumerate(data):
            cell = table.cell(i + 1, 0)
            cell.text = label
            cell = table.cell(i + 1, 1)
            cell.text = value

    def _add_swot_slide_pptx(self, prs):
        """PowerPoint sunumuna SWOT analizini içeren slayt ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "SWOT Analizi"

        swot_data = self._get_swot_analizi()

        # SWOT başlıkları ve renkleri
        swot_titles = {
            'Güçlü Yönler': RGBColor(0, 128, 0), # Yeşil
            'Zayıf Yönler': RGBColor(255, 0, 0), # Kırmızı
            'Fırsatlar': RGBColor(0, 0, 255),   # Mavi
            'Tehditler': RGBColor(255, 165, 0)    # Turuncu
        }

        # Metin kutuları ekleyerek SWOT'u gösterelim
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(4), Inches(2.5) # Konum ve boyut (örnek)
        col_offset = Inches(4.5)
        row_offset = Inches(3)

        for i, (title, color) in enumerate(swot_titles.items()):
            row = i // 2
            col = i % 2
            left = x + col * col_offset
            top = y + row * row_offset
            width = cx
            height = cy

            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame

            # Başlık paragrafı
            p = tf.add_paragraph()
            p.text = title
            p.font.bold = True
            p.font.color.rgb = color
            p.font.size = Pt(14)

            # İçerik maddeleri
            items = swot_data.get(title, [])
            if items:
                for item in items:
                    p = tf.add_paragraph()
                    p.text = f"- {item}"
                    p.font.size = Pt(10)
                    p.level = 1 # Girinti için seviye ayarı
            else:
                 p = tf.add_paragraph()
                 p.text = "Veri bulunamadı."
                 p.font.size = Pt(10)


    def _add_analiz_ozeti_slide_pptx(self, prs):
        """PowerPoint sunumuna analiz özetini içeren slayt ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "Analiz Özeti"

        ozet_sections_pptx = {
            'Temel Değerlendirme': self.analiz_ozeti.get('temel_ozet', 'Değerlendirme bulunamadı.'),
            'Yatırım Değerlendirmesi': self.analiz_ozeti.get('yatirim_ozet', 'Değerlendirme bulunamadı.'),
            'Uygunluk Puanı': self.analiz_ozeti.get('uygunluk_ozet', 'Uygunluk puanı bulunamadı.'), # Uygunluk puanı özeti eklendi
            'Öneriler ve Tavsiyeler': self.analiz_ozeti.get('tavsiyeler', 'Tavsiye bulunamadı.')
        }

        y_offset = Inches(1.5)
        for title, text in ozet_sections_pptx.items():
            # Başlık ekle
            txBox_title = slide.shapes.add_textbox(Inches(1), y_offset, Inches(8), Inches(0.5))
            tf_title = txBox_title.text_frame
            p_title = tf_title.add_paragraph()
            p_title.text = title
            p_title.font.bold = True
            p_title.font.size = Pt(16)
            p_title.space_after = Pt(6)

            y_offset += Inches(0.5) # Başlık yüksekliği kadar aşağı in

            # İçerik ekle
            txBox_content = slide.shapes.add_textbox(Inches(1), y_offset, Inches(8), Inches(1.5)) # İçerik için daha fazla yükseklik
            tf_content = txBox_content.text_frame
            p_content = tf_content.add_paragraph()
            p_content.text = text
            p_content.font.size = Pt(10)

            y_offset += Inches(1.5) + Inches(0.2) # İçerik yüksekliği + boşluk kadar aşağı in


    def _add_photos_slide_pptx(self, prs):
        """PowerPoint sunumuna yüklenen fotoğrafları içeren slayt ekler"""
        print("DEBUG [Add Photos PPTX]: _add_photos_slide_pptx metodu başladı.")
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "Arsa Fotoğrafları"

        images = self._get_uploaded_images()
        print(f"DEBUG [Add Photos PPTX]: Eklenecek resim sayısı: {len(images)}") # Flush

        if not images:
            txBox = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(1))
            tf = txBox.text_frame
            p = tf.add_paragraph()
            p.text = "Yüklü fotoğraf bulunamadı."
            p.font.size = Pt(12)
            print("DEBUG [Add Photos PPTX]: Yüklü fotoğraf bulunamadı mesajı eklendi.") # Flush
            return

        # Resimleri slayta yerleştirme (basit ızgara düzeni)
        x, y, cx, cy = Inches(1), Inches(1.5), Inches(4), Inches(3) # Konum ve boyut (örnek)
        col_offset = Inches(4.5)
        row_offset = Inches(3.5)

        for i in range(0, len(images), 2):
            row = i // 2
            col = i % 2
            left = x + col * col_offset
            top = y + row * row_offset
            width = cx
            height = cy

            try:
                slide.shapes.add_picture(images[i], left, top, width=width, height=height) # images[i] kullanılmalı
                print(f"DEBUG [Add Photos PPTX]: Resim eklendi: {images[i]}") # Flush
            except Exception as e:
                print(f"HATA [Add Photos PPTX]: Resim eklenemedi: {images[i]} - {e}") # Flush
                traceback.print_exc(file=sys.stdout) # Konsola yazdır
                sys.stdout.flush() # Zorla
                # Hata durumunda metin kutusu ekleyebiliriz
                txBox = slide.shapes.add_textbox(left, top, width, height)
                tf = txBox.text_frame
                p = tf.add_paragraph()
                p.text = "Resim yüklenemedi."
                if p.runs: p.runs[0].font.size = Pt(10) # Check if run exists
                p.alignment = PP_ALIGN.CENTER # WD_ALIGN_PARAGRAPH yerine PP_ALIGN kullanılmalı


        print("DEBUG [Add Photos PPTX]: _add_photos_slide_pptx metodu tamamlandı.") # Flush

    def _add_qr_code_slide_pptx(self, prs, qr_path):
        """PowerPoint sunumuna QR kod slaytı ekler"""
        blank_slide_layout = prs.slide_layouts[5]
        slide = prs.slides.add_slide(blank_slide_layout)

        title_shape = slide.shapes.title
        title_shape.text = "Analiz Detayları QR Kod"

        # QR kod resmini slaytın ortasına ekle
        try:
            img = slide.shapes.add_picture(qr_path, Inches(4), Inches(2), width=Inches(3), height=Inches(3)) # Konum ve boyut (örnek)
            print(f"DEBUG [Add QR PPTX]: QR kod resmi eklendi: {qr_path}")
        except Exception as e:
            print(f"HATA [Add QR PPTX]: QR kod resmi eklenemedi: {e}")
            traceback.print_exc(file=sys.stdout) # Konsola yazdır
            sys.stdout.flush() # Zorla
            txBox = slide.shapes.add_textbox(Inches(4), Inches(2), Inches(3), Inches(3))
            tf = txBox.text_frame
            p = tf.add_paragraph()
            p.text = "QR Kod yüklenemedi."
            p.font.size = Pt(10)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER