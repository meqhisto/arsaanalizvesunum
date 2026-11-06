# blueprints/analysis_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory, make_response
)
from flask_login import login_required, current_user
from datetime import datetime
import uuid # Rapor ID'leri için
import tempfile # Kullanılmıyorsa kaldırılabilir
import traceback
import json
from decimal import Decimal # Sayısal dönüşümler için
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename # Dosya yükleme için
import os
import logging # logging için
from typing import Any # For type hinting

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats, AnalizMedya

# Özel modüllerinizi import edin
# Bu import yolları, projenizin klasör yapısına göre ayarlanmalıdır.
# Eğer blueprints klasörü, modules klasörü ile aynı seviyedeyse:
from modules.analiz import ArsaAnalizci
from modules.fiyat_tahmini import FiyatTahminModeli # FiyatTahminModeli'ne engine geçilecek

# Flask uygulamasının yapılandırmasına erişmek için current_app
from flask import current_app

analysis_bp = Blueprint('analysis', __name__, template_folder='../templates/analysis')# template_folder='../templates' ana şablon klasörünü kullanır.
# Eğer analiz şablonları templates/analysis/ altındaysa, template_folder='../templates/analysis' yapın.

# --- YARDIMCI FONKSİYONLAR (app.py'den taşınabilir veya burada tanımlanabilir) ---
def allowed_file(filename):
    # ALLOWED_EXTENSIONS'ı current_app.config'den almak daha iyi olur
    # veya burada sabit olarak tanımlanabilir.
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- ROTALAR ---

@analysis_bp.route('/new', methods=['GET'])
@login_required
def new_analysis():
    """Yeni gayrimenkul formu"""
    return _gayrimenkul_formu(None, MultiDict({'tur': request.args.get('tur', 'arsa')}))


def _gayrimenkul_formu(gayrimenkul, veri, hatalar=None):
    """Oluştur/düzenle ortak şablonu; veri MultiDict (POST'ta girilen değerler, GET'te kayıttan)."""
    from modules.gayrimenkul_form import sahip_satirlari
    from modules import gayrimenkul_sabitleri as sabit
    baslik = 'Gayrimenkulü düzenle' if gayrimenkul else 'Yeni gayrimenkul'
    return render_template('gayrimenkul/form.html', gayrimenkul=gayrimenkul, v=veri, hatalar=hatalar or [],
                           sahipler=sahip_satirlari(veri, current_user, gayrimenkul), sabit=sabit, title=baslik)


def _medyalari_kaydet(gayrimenkul, dosyalar):
    """Formla gelen fotoğraf/videoları gayrimenkulün klasörüne kaydeder (commit etmez)."""
    sayi = 0
    for dosya in dosyalar:
        if not dosya or not dosya.filename or not allowed_file(dosya.filename):
            continue
        ad = secure_filename(dosya.filename)
        if not ad or '.' not in ad:
            continue
        uzanti = ad.rsplit('.', 1)[1].lower()
        ad = f"{uuid.uuid4().hex[:8]}_{ad}"  # aynı adlı yüklemeler birbirini ezmesin
        klasor = os.path.join(current_app.config['UPLOAD_FOLDER'], str(gayrimenkul.id))
        os.makedirs(klasor, exist_ok=True)
        dosya.save(os.path.join(klasor, ad))
        medya = AnalizMedya()
        medya.analiz_id = gayrimenkul.id
        medya.filename = f"{gayrimenkul.id}/{ad}"
        medya.type = 'image' if uzanti in {'jpg', 'jpeg', 'png', 'gif'} else 'video'
        db.session.add(medya)
        sayi += 1
    return sayi


def _sahipler_ve_ilan(gayrimenkul, form):
    """Sahipleri senkronlar; 'hemen ilana çıkar' işaretliyse tek gayrimenkullü ilan açar (commit etmez)."""
    from modules.gayrimenkul_form import ilan_verisi, sahipler_formdan
    from modules.ilan_servis import ilan_kaydet, sahipleri_kaydet
    sahipleri_kaydet(gayrimenkul, current_user, sahipler_formdan(form))
    if form.get('ilana_cikar') == '1':
        return ilan_kaydet(None, current_user, ilan_verisi(form, gayrimenkul))
    return None


def _medya_sonrasi(gayrimenkul):
    try:
        if _medyalari_kaydet(gayrimenkul, request.files.getlist('medya[]')):
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Medya kaydetme hatası (ID: {gayrimenkul.id}): {e}", exc_info=True)
        flash('Gayrimenkul kaydedildi ancak bazı fotoğraflar yüklenemedi.', 'warning')


@analysis_bp.route('/list', methods=['GET'])
@login_required
def list_analyses():
    """Kullanıcının analizlerini listele ve filtrele"""
    user_id = current_user.id  # Giriş yapmış kullanıcının ID'si

    # Base query
    query = ArsaAnaliz.query.filter_by(user_id=user_id)

    # Search filter
    search = request.args.get('search', '').strip()
    if search:
        search_filter = db.or_(
            ArsaAnaliz.il.ilike(f'%{search}%'),
            ArsaAnaliz.ilce.ilike(f'%{search}%'),
            ArsaAnaliz.mahalle.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)

    # Location filter
    il_filter = request.args.get('il', '').strip()
    if il_filter:
        query = query.filter(ArsaAnaliz.il == il_filter)

    # Date filter
    date_filter = request.args.get('date_filter', '').strip()
    if date_filter:
        from datetime import datetime, timedelta
        today = datetime.now().date()

        if date_filter == 'today':
            # SQL Server compatible date filtering
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            query = query.filter(ArsaAnaliz.created_at.between(start_of_day, end_of_day))
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            start_of_week = datetime.combine(week_ago, datetime.min.time())
            query = query.filter(ArsaAnaliz.created_at >= start_of_week)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            start_of_month = datetime.combine(month_ago, datetime.min.time())
            query = query.filter(ArsaAnaliz.created_at >= start_of_month)

    # Execute query with ordering
    analyses = query.order_by(ArsaAnaliz.created_at.desc()).all()

    return render_template('analysis_list.html', analyses=analyses, title="Analizlerim")

@analysis_bp.route('/export/excel', methods=['GET'])
@login_required
def export_excel():
    """Analizleri Excel formatında dışa aktar"""
    try:
        import pandas as pd
        from io import BytesIO
        from flask import make_response
        from datetime import datetime

        user_id = current_user.id  # Giriş yapmış kullanıcının ID'si

        # Apply same filters as list view
        query = ArsaAnaliz.query.filter_by(user_id=user_id)

        # Search filter
        search = request.args.get('search', '').strip()
        if search:
            search_filter = db.or_(
                ArsaAnaliz.il.ilike(f'%{search}%'),
                ArsaAnaliz.ilce.ilike(f'%{search}%'),
                ArsaAnaliz.mahalle.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # Location filter
        il_filter = request.args.get('il', '').strip()
        if il_filter:
            query = query.filter(ArsaAnaliz.il == il_filter)

        # Date filter
        date_filter = request.args.get('date_filter', '').strip()
        if date_filter:
            from datetime import datetime, timedelta
            today = datetime.now().date()

            if date_filter == 'today':
                start_of_day = datetime.combine(today, datetime.min.time())
                end_of_day = datetime.combine(today, datetime.max.time())
                query = query.filter(ArsaAnaliz.created_at.between(start_of_day, end_of_day))
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                start_of_week = datetime.combine(week_ago, datetime.min.time())
                query = query.filter(ArsaAnaliz.created_at >= start_of_week)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                start_of_month = datetime.combine(month_ago, datetime.min.time())
                query = query.filter(ArsaAnaliz.created_at >= start_of_month)

        analyses = query.order_by(ArsaAnaliz.created_at.desc()).all()

        # Prepare data for Excel
        data = []
        for analysis in analyses:
            data.append({
                'ID': analysis.id,
                'İl': analysis.il,
                'İlçe': analysis.ilce,
                'Mahalle': analysis.mahalle or '',
                'Ada': analysis.ada or '',
                'Parsel': analysis.parsel or '',
                'Koordinatlar': analysis.koordinatlar or '',
                'Metrekare': float(analysis.metrekare or 0),
                'İmar Durumu': analysis.imar_durumu or '',
                'TAKS': float(analysis.taks or 0),
                'KAKS': float(analysis.kaks or 0),
                'Fiyat (TL)': float(analysis.fiyat or 0),
                'Bölge Fiyatı (TL)': float(analysis.bolge_fiyat or 0),
                'Birim Fiyat (TL/m²)': float(analysis.fiyat / analysis.metrekare) if analysis.metrekare and analysis.fiyat else 0,
                'Oluşturma Tarihi': analysis.created_at.strftime('%d.%m.%Y %H:%M'),
                'Notlar': analysis.notlar or ''
            })

        # Create DataFrame
        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Analizler', index=False)

            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Analizler']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename=analizler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        return response

    except ImportError:
        flash('Excel dışa aktarma için pandas kütüphanesi gerekli. Lütfen sistem yöneticisine başvurun.', 'error')
        return redirect(url_for('analysis.list_analyses'))
    except Exception as e:
        current_app.logger.error(f"Excel export error: {str(e)}", exc_info=True)
        flash('Excel dosyası oluşturulurken bir hata oluştu.', 'error')
        return redirect(url_for('analysis.list_analyses'))

@analysis_bp.route('/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    """Analizleri PDF formatında dışa aktar"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO
        from flask import make_response
        from datetime import datetime

        user_id = current_user.id  # Giriş yapmış kullanıcının ID'si

        # Apply same filters as list view
        query = ArsaAnaliz.query.filter_by(user_id=user_id)

        # Search filter
        search = request.args.get('search', '').strip()
        if search:
            search_filter = db.or_(
                ArsaAnaliz.il.ilike(f'%{search}%'),
                ArsaAnaliz.ilce.ilike(f'%{search}%'),
                ArsaAnaliz.mahalle.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # Location filter
        il_filter = request.args.get('il', '').strip()
        if il_filter:
            query = query.filter(ArsaAnaliz.il == il_filter)

        # Date filter
        date_filter = request.args.get('date_filter', '').strip()
        if date_filter:
            from datetime import datetime, timedelta
            today = datetime.now().date()

            if date_filter == 'today':
                start_of_day = datetime.combine(today, datetime.min.time())
                end_of_day = datetime.combine(today, datetime.max.time())
                query = query.filter(ArsaAnaliz.created_at.between(start_of_day, end_of_day))
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                start_of_week = datetime.combine(week_ago, datetime.min.time())
                query = query.filter(ArsaAnaliz.created_at >= start_of_week)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                start_of_month = datetime.combine(month_ago, datetime.min.time())
                query = query.filter(ArsaAnaliz.created_at >= start_of_month)

        analyses = query.order_by(ArsaAnaliz.created_at.desc()).all()

        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

        # Container for the 'Flowable' objects
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

        # Add title
        title = Paragraph("Arsa Analiz Raporu", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Add summary info
        summary_data = [
            ['Toplam Analiz:', str(len(analyses))],
            ['Rapor Tarihi:', datetime.now().strftime('%d.%m.%Y %H:%M')],
            ['Toplam Değer:', f"₺{sum(float(a.fiyat or 0) for a in analyses):,.0f}"],
            ['Toplam Alan:', f"{sum(float(a.metrekare or 0) for a in analyses):,.0f} m²"]
        ]

        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 20))

        # Prepare table data
        data = [['ID', 'Lokasyon', 'Alan (m²)', 'Fiyat (₺)', 'İmar Durumu', 'Tarih']]

        for analysis in analyses:
            data.append([
                str(analysis.id),
                f"{analysis.il}, {analysis.ilce}",
                f"{float(analysis.metrekare or 0):,.0f}",
                f"₺{float(analysis.fiyat or 0):,.0f}",
                analysis.imar_durumu or '-',
                analysis.created_at.strftime('%d.%m.%Y')
            ])

        # Create table
        table = Table(data, colWidths=[0.5*inch, 2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)

        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()

        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=analizler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

        return response

    except ImportError:
        flash('PDF dışa aktarma için reportlab kütüphanesi gerekli. Lütfen sistem yöneticisine başvurun.', 'error')
        return redirect(url_for('analysis.list_analyses'))
    except Exception as e:
        current_app.logger.error(f"PDF export error: {str(e)}", exc_info=True)
        flash('PDF dosyası oluşturulurken bir hata oluştu.', 'error')
        return redirect(url_for('analysis.list_analyses'))

@analysis_bp.route('/<int:analysis_id>', methods=['GET'])
@login_required
def view_analysis(analysis_id):
    """Analiz detayını görüntüle"""
    user_id = current_user.id  # Giriş yapmış kullanıcının ID'si

    try:
        analysis = ArsaAnaliz.query.filter_by(id=analysis_id, user_id=user_id).first_or_404()

        # Parse JSON fields
        altyapi_parsed = []
        if analysis.altyapi:
            try:
                altyapi_data = json.loads(analysis.altyapi)
                if isinstance(altyapi_data, list):
                    altyapi_parsed = altyapi_data
                elif isinstance(altyapi_data, dict):
                    altyapi_parsed = [key for key, value in altyapi_data.items() if value]
            except json.JSONDecodeError:
                current_app.logger.warning(f"Invalid altyapi JSON for analysis {analysis_id}")

        swot_parsed = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        if analysis.swot_analizi:
            try:
                swot_data = json.loads(analysis.swot_analizi)
                if isinstance(swot_data, dict):
                    swot_parsed.update(swot_data)
            except json.JSONDecodeError:
                current_app.logger.warning(f"Invalid SWOT JSON for analysis {analysis_id}")

        # Calculate additional metrics
        calculations = {}
        try:
            metrekare = float(analysis.metrekare) if analysis.metrekare else 0
            fiyat = float(analysis.fiyat) if analysis.fiyat else 0
            bolge_fiyat = float(analysis.bolge_fiyat) if analysis.bolge_fiyat else 0
            taks = float(analysis.taks) if analysis.taks else 0
            kaks = float(analysis.kaks) if analysis.kaks else 0

            if metrekare and fiyat:
                calculations['unit_price'] = fiyat / metrekare
            if metrekare and bolge_fiyat:
                calculations['unit_market_price'] = bolge_fiyat / metrekare
            if fiyat and bolge_fiyat:
                calculations['price_difference'] = bolge_fiyat - fiyat
                calculations['price_difference_percent'] = (calculations['price_difference'] / fiyat) * 100
            if taks and metrekare:
                calculations['buildable_area'] = taks * metrekare
            if kaks and metrekare:
                calculations['total_construction_area'] = kaks * metrekare
        except (ValueError, TypeError, ZeroDivisionError) as e:
            current_app.logger.warning(f"Calculation error for analysis {analysis_id}: {str(e)}")
            calculations = {}

        # Get related analyses in same location
        related_analyses = ArsaAnaliz.query.filter(
            ArsaAnaliz.user_id == user_id,
            ArsaAnaliz.id != analysis_id,
            db.or_(
                db.and_(ArsaAnaliz.il == analysis.il, ArsaAnaliz.ilce == analysis.ilce),
                ArsaAnaliz.il == analysis.il
            )
        ).order_by(ArsaAnaliz.created_at.desc()).limit(5).all()

        # Get analysis media files
        media_files = AnalizMedya.query.filter_by(analiz_id=analysis_id).order_by(AnalizMedya.uploaded_at.desc()).all()

        return render_template('analysis_detail.html',
                             analysis=analysis,
                             altyapi=altyapi_parsed,
                             swot=swot_parsed,
                             calculations=calculations,
                             related_analyses=related_analyses,
                             media_files=media_files,
                             title=f"Analiz Detayı - {analysis.il} {analysis.ilce}")

    except Exception as e:
        current_app.logger.error(f"Analysis detail error: {str(e)}", exc_info=True)
        flash('Analiz detayları yüklenirken bir hata oluştu.', 'error')
        return redirect(url_for('analysis.list_analyses'))

@analysis_bp.route('/<int:analysis_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_analysis(analysis_id):
    """Gayrimenkulü düzenle (sahibi, ekibinin broker'ı, superadmin)"""
    from modules.gayrimenkul_form import form_verisi, formdan_gayrimenkul
    from modules.ilan_servis import IlanHatasi, gayrimenkul_or_404
    gayrimenkul = gayrimenkul_or_404(analysis_id, current_user)
    if request.method == 'GET':
        return _gayrimenkul_formu(gayrimenkul, form_verisi(gayrimenkul))

    hatalar = formdan_gayrimenkul(request.form, gayrimenkul)
    if not hatalar:
        try:
            eski_fiyat = gayrimenkul.fiyat
            ilan = _sahipler_ve_ilan(gayrimenkul, request.form)
            if ilan is not None and ilan.teklif_tipi == 'satilik' and ilan.fiyat is not None:
                gayrimenkul.fiyat = ilan.fiyat
                _istatistik_fiyat_degisti(gayrimenkul, eski_fiyat)
            db.session.commit()
        except IlanHatasi as e:
            hatalar = [str(e)]
    if hatalar:
        db.session.rollback()
        return _gayrimenkul_formu(gayrimenkul, request.form, hatalar)
    _medya_sonrasi(gayrimenkul)
    flash('Gayrimenkul güncellendi.', 'success')
    return redirect(url_for('analysis.view_analysis', analysis_id=gayrimenkul.id))


def _analizi_sil(analiz):
    """Analizi bağlı kayıtları ve dosyalarıyla siler, panel istatistiklerini günceller (commit etmez)."""
    from models.user_models import portfolio_arsalar
    stats = DashboardStats.query.filter_by(user_id=analiz.user_id).first()
    if stats:
        stats.toplam_arsa_sayisi = max(0, (stats.toplam_arsa_sayisi or 0) - 1)
        stats.toplam_deger = max(Decimal("0.00"), (stats.toplam_deger or Decimal(0)) - (analiz.fiyat or Decimal(0)))
        if stats.toplam_arsa_sayisi == 0:
            stats.ortalama_fiyat = stats.en_yuksek_fiyat = stats.en_dusuk_fiyat = 0.0
    bolge = BolgeDagilimi.query.filter_by(user_id=analiz.user_id, il=analiz.il).first()
    if bolge:
        bolge.analiz_sayisi = max(0, (bolge.analiz_sayisi or 0) - 1)
        bolge.toplam_deger = max(Decimal("0.00"), (bolge.toplam_deger or Decimal(0)) - (analiz.fiyat or Decimal(0)))
        if bolge.analiz_sayisi == 0:
            db.session.delete(bolge)
    # Fotoğraflar: veritabanında 'analiz_id/dosya' biçiminde, UPLOAD_FOLDER altında
    upload = current_app.config['UPLOAD_FOLDER']
    for medya in AnalizMedya.query.filter_by(analiz_id=analiz.id).all():
        yol = os.path.join(upload, medya.filename or '')
        try:
            if medya.filename and os.path.isfile(yol):
                os.remove(yol)
        except OSError:
            current_app.logger.warning(f"Medya dosyası silinemedi: {yol}")
        db.session.delete(medya)
    klasor = os.path.join(upload, str(analiz.id))
    try:
        if os.path.isdir(klasor) and not os.listdir(klasor):
            os.rmdir(klasor)
    except OSError:
        pass
    # Portföy bağlantıları (iş takip kayıtlarındaki bağlantı veritabanında SET NULL olur)
    db.session.execute(portfolio_arsalar.delete().where(portfolio_arsalar.c.arsa_id == analiz.id))
    # İlanlar: tek gayrimenkullü ilan silinir, çok gayrimenkulden yalnız bağ çıkar
    from modules.ilan_servis import gayrimenkul_silinirken
    gayrimenkul_silinirken(analiz)
    db.session.delete(analiz)


@analysis_bp.route('/<int:analysis_id>/delete', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """Analizi sil (JSON)"""
    analysis = ArsaAnaliz.query.filter_by(id=analysis_id, user_id=current_user.id).first()
    if not analysis:
        return jsonify({'success': False, 'message': 'Analiz bulunamadı.'}), 404
    try:
        il, ilce = analysis.il, analysis.ilce
        _analizi_sil(analysis)
        db.session.commit()
        flash(f'{il} {ilce} analizi başarıyla silindi.', 'success')
        return jsonify({'success': True, 'message': 'Analiz başarıyla silindi.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analysis delete error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Analiz silinirken bir hata oluştu.'}), 500

KOPYALANAN_ALANLAR = (
    'il', 'ilce', 'ada', 'parsel', 'koordinatlar', 'pafta', 'metrekare', 'imar_durumu', 'taks', 'kaks', 'fiyat',
    'bolge_fiyat', 'altyapi', 'swot_analizi', 'tur', 'alt_tur', 'baslik', 'brut_m2', 'net_m2', 'oda_sayisi',
    'banyo_sayisi', 'bulundugu_kat', 'toplam_kat', 'bina_yasi', 'isinma', 'esyali', 'site_icinde', 'balkon',
    'aidat', 'tapu_durumu', 'krediye_uygun', 'takasli', 'kimden',
)


@analysis_bp.route('/<int:analysis_id>/duplicate', methods=['POST'])
@login_required
def duplicate_analysis(analysis_id):
    """Gayrimenkulü kopyala (sahipler ve ilan bağları kopyalanmaz)"""
    import copy
    from modules.ilan_servis import gayrimenkul_or_404
    original = gayrimenkul_or_404(analysis_id, current_user)
    try:
        kopya = ArsaAnaliz(user_id=current_user.id, office_id=current_user.office_id,
                           created_at=datetime.utcnow())
        for alan in KOPYALANAN_ALANLAR:
            setattr(kopya, alan, getattr(original, alan))
        kopya.ozellikler = copy.deepcopy(original.ozellikler)
        kopya.mahalle = f"{original.mahalle} (Kopya)" if original.mahalle else "Kopya"
        not_ = f"[Bu kayıt {original.il} {original.ilce} kaydından kopyalanmıştır]"
        kopya.notlar = f"{original.notlar}\n\n{not_}" if original.notlar else not_
        db.session.add(kopya)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Gayrimenkul başarıyla kopyalandı.',
            'new_id': kopya.id,
            'redirect_url': url_for('analysis.view_analysis', analysis_id=kopya.id)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analysis duplicate error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Gayrimenkul kopyalanırken bir hata oluştu.'}), 500


@analysis_bp.route('/<int:analysis_id>/share', methods=['GET'])
@login_required
def share_analysis(analysis_id):
    """Analiz paylaşım bilgilerini getir"""
    user_id = current_user.id  # Giriş yapmış kullanıcının ID'si
    analysis = ArsaAnaliz.query.filter_by(id=analysis_id, user_id=user_id).first_or_404()

    try:
        share_data = {
            'title': f'Arsa Analizi - {analysis.il} {analysis.ilce}',
            'description': f'{analysis.metrekare} m² arsa analizi. Fiyat: ₺{analysis.fiyat:,.0f}' if analysis.metrekare and analysis.fiyat else f'{analysis.il} {analysis.ilce} arsa analizi',
            'url': request.url_root.rstrip('/') + url_for('analysis.view_analysis', analysis_id=analysis_id),
            'image': None  # Gelecekte analiz görseli eklenebilir
        }

        return jsonify({'success': True, 'data': share_data})

    except Exception as e:
        current_app.logger.error(f"Analysis share error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Paylaşım bilgileri alınırken bir hata oluştu.'}), 500

def _build_report(analiz, fmt, settings=None):
    """Analiz için istenen formatta (pdf / word / pptx) rapor üretir ve indirilebilir yanıt döndürür."""
    import tempfile, shutil
    from modules.rapor import MIMETYPES, EXTENSIONS, ascii_slug, build_report_model, generate_report
    detail_url = request.url_root.rstrip('/') + url_for('analysis.view_analysis', analysis_id=analiz.id)
    model = build_report_model(analiz, current_user, detail_url=detail_url,
                               upload_folder=current_app.config.get('UPLOAD_FOLDER'))
    output_dir = tempfile.mkdtemp(prefix='rapor_')
    try:
        path = generate_report(model, fmt, output_dir)
        with open(path, 'rb') as f:
            data = f.read()
    finally:
        shutil.rmtree(output_dir, ignore_errors=True)
    filename = (f"arsa_analiz_{ascii_slug(analiz.il)}_{ascii_slug(analiz.ilce)}_{analiz.id}_"
                f"{datetime.now().strftime('%Y%m%d')}.{EXTENSIONS[fmt]}")
    response = make_response(data)
    response.headers['Content-Type'] = MIMETYPES[fmt]
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _report_or_redirect(analiz, fmt, settings=None):
    try:
        return _build_report(analiz, fmt, settings)
    except Exception as e:
        current_app.logger.error(f"Rapor oluşturma hatası ({fmt}, ID: {analiz.id}): {e}", exc_info=True)
        flash('Rapor oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('analysis.view_analysis', analysis_id=analiz.id))


@analysis_bp.route('/<int:analysis_id>/report/word', methods=['GET'])
@login_required
def generate_word_report(analysis_id):
    """Word raporu indir."""
    analysis = ArsaAnaliz.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    return _report_or_redirect(analysis, 'word')


@analysis_bp.route('/<int:analysis_id>/report/pdf', methods=['GET'])
@login_required
def generate_pdf_report(analysis_id):
    """PDF raporu indir."""
    analysis = ArsaAnaliz.query.filter_by(id=analysis_id, user_id=current_user.id).first_or_404()
    return _report_or_redirect(analysis, 'pdf')


def _istatistiklere_ekle(gayrimenkul):
    """Panel ve bölge istatistiklerine yeni kaydı ekler (commit etmez)."""
    user_id = gayrimenkul.user_id
    fiyat = Decimal(str(gayrimenkul.fiyat or 0))
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = DashboardStats()
        stats.user_id = user_id
        db.session.add(stats)
    stats.toplam_arsa_sayisi = (stats.toplam_arsa_sayisi or 0) + 1
    stats.toplam_deger = (stats.toplam_deger or Decimal(0)) + fiyat
    fiyat_f = float(fiyat)
    if stats.toplam_arsa_sayisi == 1:
        stats.ortalama_fiyat = stats.en_yuksek_fiyat = stats.en_dusuk_fiyat = fiyat_f
    else:
        stats.ortalama_fiyat = (((stats.ortalama_fiyat or 0.0) * (stats.toplam_arsa_sayisi - 1)) + fiyat_f) \
            / stats.toplam_arsa_sayisi
        stats.en_yuksek_fiyat = max((stats.en_yuksek_fiyat or 0.0), fiyat_f)
        stats.en_dusuk_fiyat = min(stats.en_dusuk_fiyat if stats.en_dusuk_fiyat is not None else fiyat_f, fiyat_f)
    stats.son_guncelleme = datetime.utcnow()

    bolge = BolgeDagilimi.query.filter_by(user_id=user_id, il=gayrimenkul.il).first()
    if not bolge:
        bolge = BolgeDagilimi()
        bolge.user_id = user_id
        bolge.il = gayrimenkul.il
        bolge.analiz_sayisi = 0
        bolge.toplam_deger = Decimal('0.00')
        db.session.add(bolge)
    bolge.analiz_sayisi = (bolge.analiz_sayisi or 0) + 1
    bolge.toplam_deger = (bolge.toplam_deger or Decimal(0)) + fiyat
    bolge.son_guncelleme = datetime.utcnow()


def _istatistik_fiyat_degisti(gayrimenkul, eski_fiyat):
    """Kayıtlı gayrimenkulün fiyatı değişince panel/bölge istatistiklerini düzeltir (commit etmez)."""
    fark = Decimal(str(gayrimenkul.fiyat or 0)) - Decimal(str(eski_fiyat or 0))
    if not fark:
        return
    user_id = gayrimenkul.user_id
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if stats:
        db.session.flush()
        sayi, en_yuksek, en_dusuk = (db.session.query(db.func.count(ArsaAnaliz.id), db.func.max(ArsaAnaliz.fiyat),
                                                       db.func.min(ArsaAnaliz.fiyat))
                                     .filter(ArsaAnaliz.user_id == user_id).one())
        stats.toplam_deger = (stats.toplam_deger or Decimal(0)) + fark
        if sayi:
            stats.ortalama_fiyat = float(stats.toplam_deger) / sayi
            stats.en_yuksek_fiyat = float(en_yuksek or 0)
            stats.en_dusuk_fiyat = float(en_dusuk or 0)
        stats.son_guncelleme = datetime.utcnow()
    bolge = BolgeDagilimi.query.filter_by(user_id=user_id, il=gayrimenkul.il).first()
    if bolge:
        bolge.toplam_deger = (bolge.toplam_deger or Decimal(0)) + fark
        bolge.son_guncelleme = datetime.utcnow()


@analysis_bp.route('/create', methods=['POST'])
@login_required
def create_analysis():
    """Yeni gayrimenkul; sahipler ve isteğe bağlı ilan aynı transaction'da kaydedilir."""
    from modules.gayrimenkul_form import formdan_gayrimenkul
    from modules.ilan_servis import IlanHatasi
    gayrimenkul = ArsaAnaliz(user_id=current_user.id, office_id=current_user.office_id, fiyat=Decimal('0'))
    hatalar = formdan_gayrimenkul(request.form, gayrimenkul)
    if hatalar:
        return _gayrimenkul_formu(None, request.form, hatalar)
    try:
        db.session.add(gayrimenkul)
        db.session.flush()
        ilan = _sahipler_ve_ilan(gayrimenkul, request.form)
        # Panel istatistikleri fiyat alanına bakar: satış ilanı açıldıysa onun fiyatı, değilse 0
        if ilan is not None and ilan.teklif_tipi == 'satilik' and ilan.fiyat is not None:
            gayrimenkul.fiyat = ilan.fiyat
        _istatistiklere_ekle(gayrimenkul)
        db.session.commit()
    except IlanHatasi as e:
        db.session.rollback()
        return _gayrimenkul_formu(None, request.form, [str(e)])
    _medya_sonrasi(gayrimenkul)
    flash('Gayrimenkul kaydedildi.' + (' İlan da oluşturuldu.' if ilan is not None else ''), 'success')
    return redirect(url_for('analysis.view_analysis', analysis_id=gayrimenkul.id))


@analysis_bp.route('/kontak-ara', methods=['GET'])
@login_required
def kontak_ara():
    """Mal sahibi seçimi için görünür CRM kişilerinde ad/soyad/telefon araması (en çok 20)."""
    from models.crm_models import Contact
    from modules.gayrimenkul_form import kontak_json
    from modules.ilan_servis import gorunur_kontaklar
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    desen = f"%{q}%"
    kontaklar = (gorunur_kontaklar(current_user)
                 .filter(db.or_(Contact.first_name.ilike(desen), Contact.last_name.ilike(desen),
                                Contact.phone.ilike(desen),
                                (Contact.first_name + ' ' + Contact.last_name).ilike(desen)))
                 .order_by(Contact.first_name, Contact.last_name).limit(20).all())
    return jsonify([kontak_json(c) for c in kontaklar])


@analysis_bp.route('/kontak-ekle', methods=['POST'])
@login_required
def kontak_ekle():
    """Formdan anında mal sahibi kişisi oluşturur."""
    from models.crm_models import Contact
    from modules.gayrimenkul_form import kontak_json
    veri = request.get_json(silent=True) or {}
    ad = str(veri.get('ad') or '').strip()
    if not ad:
        return jsonify({'hata': 'Ad zorunludur.'}), 400
    soyad = str(veri.get('soyad') or '').strip()
    telefon = str(veri.get('telefon') or '').strip()
    kontak = Contact(user_id=current_user.id, office_id=current_user.office_id, first_name=ad[:100],
                     last_name=soyad[:100] or '-', phone=telefon[:30] or None, status='Mal sahibi',
                     source='Portföy')
    db.session.add(kontak)
    db.session.commit()
    return jsonify(kontak_json(kontak))


@analysis_bp.route('/<int:analiz_id>')
@login_required
def analiz_detay(analiz_id):
    try:
        analiz = ArsaAnaliz.query.get_or_404(analiz_id)
        analiz_sahibi_user = User.query.get(analiz.user_id)

        if not analiz_sahibi_user:
            flash("Analize ait kullanıcı bulunamadı.", "danger")
            return redirect(url_for('analysis.analizler'))

        read_only_mode = (current_user.id != analiz.user_id)
        
        altyapi_parsed = []
        if analiz.altyapi:
            try:
                altyapi_data = json.loads(analiz.altyapi)
                if isinstance(altyapi_data, list):
                    altyapi_parsed = altyapi_data
                elif isinstance(altyapi_data, dict): # Eski format {yol:true, su:false} ise listeye çevir
                    altyapi_parsed = [key for key, value in altyapi_data.items() if value]
                else:
                    current_app.logger.warning(f"Analiz ID {analiz_id} altyapı verisi beklenmedik format: {analiz.altyapi}")
            except json.JSONDecodeError:
                current_app.logger.error(f"Analiz ID {analiz_id} altyapı JSON parse hatası.")
        
        swot_analizi_parsed = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        if analiz.swot_analizi:
            try:
                swot_data = json.loads(analiz.swot_analizi)
                if isinstance(swot_data, dict):
                    swot_analizi_parsed = {k: (v if isinstance(v, list) else [v] if v else []) for k, v in swot_data.items()}
                else: # Eğer direkt liste ise (eski bir format olabilir)
                    current_app.logger.warning(f"Analiz ID {analiz_id} SWOT verisi beklenmedik format: {analiz.swot_analizi}")
            except json.JSONDecodeError:
                current_app.logger.error(f"Analiz ID {analiz_id} SWOT JSON parse hatası.")

        # ArsaAnalizci ve FiyatTahminModeli kullanımı
        analizci = ArsaAnalizci() # Strateji default SwotAnalizi olacak
        # ArsaAnalizci'nin beklediği veri formatını kontrol et
        # Genellikle bir dict bekler: {'metrekare': ..., 'fiyat': ..., 'imar_durumu': ...}
        arsa_data_for_analizci = {
            "metrekare": float(analiz.metrekare or 0),
            "fiyat": float(analiz.fiyat or 0),
            "bolge_fiyat": float(analiz.bolge_fiyat or 0),
            "taks": float(analiz.taks or 0.3), # Varsayılan değerler
            "kaks": float(analiz.kaks or 1.5), # Varsayılan değerler
            "imar_durumu": analiz.imar_durumu or "",
            "altyapi": altyapi_parsed, # Parse edilmiş liste
            "konum": {"il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle}
        }
        analiz_sonuclari_data = analizci.analiz_et(arsa_data_for_analizci.copy()) # Kopyasını gönder
        ozet = analizci.ozetle(analiz_sonuclari_data.copy())

        tahmin_sonucu = None
        try:
            # db.engine'e create_app içinde erişim sağlanmalı veya FiyatTahminModeli'ne app context'i verilmeli.
            # Şimdilik db.engine'in erişilebilir olduğunu varsayıyorum.
            tahmin_modeli = FiyatTahminModeli(db.engine)
            prediction_input_data = {
                "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
                "metrekare": float(analiz.metrekare or 0),
                "imar_durumu": analiz.imar_durumu or "",
                "taks": float(analiz.taks or 0.3),
                "kaks": float(analiz.kaks or 1.5),
                "bolge_fiyat": float(analiz.bolge_fiyat or 0)
            }
            tahmin_sonucu = tahmin_modeli.tahmin_yap(prediction_input_data)
        except Exception as e_tahmin:
            current_app.logger.error(f"Fiyat tahmini hatası (ID: {analiz_id}): {e_tahmin}", exc_info=False)

        medyalar = AnalizMedya.query.filter_by(analiz_id=analiz_id).order_by(AnalizMedya.uploaded_at.asc()).all()
        
        # Rapor için session verilerini ayarla (sadece sahibi ise)
        if not read_only_mode:
            session_arsa_data = {
                "id": analiz.id, "il": analiz.il, "ilce": analiz.ilce, "mahalle": analiz.mahalle,
                "ada": analiz.ada, "parsel": analiz.parsel, "koordinatlar": analiz.koordinatlar,
                "pafta": analiz.pafta, "metrekare": float(analiz.metrekare or 0), "imar_durumu": analiz.imar_durumu or "",
                "taks": float(analiz.taks or 0.3), "kaks": float(analiz.kaks or 1.5), 
                "fiyat": float(analiz.fiyat or 0), "bolge_fiyat": float(analiz.bolge_fiyat or 0),
                "altyapi[]": altyapi_parsed, # Bu anahtarın DocumentGenerator tarafından doğru okunması lazım
                "strengths": swot_analizi_parsed.get("strengths", []), 
                "weaknesses": swot_analizi_parsed.get("weaknesses", []),
                "opportunities": swot_analizi_parsed.get("opportunities", []), 
                "threats": swot_analizi_parsed.get("threats", []),
                # İnşaat hesaplama verisi DocumentGenerator'a gönderilecek arsa_data'ya eklenebilir
                "insaat_hesaplama": analiz_sonuclari_data.get("insaat_hesaplama", {}) # ArsaAnalizci'den gelen veri
            }
            session["arsa_data"] = session_arsa_data # DocumentGenerator için
            session["analiz_ozeti"] = ozet
        elif "arsa_data" in session: # Başkasının analizine bakarken kendi session'ımızı temizleyelim
            session.pop("arsa_data", None)
            session.pop("analiz_ozeti", None)

        return render_template(
            "analiz_detay.html", # templates/analiz_detay.html (veya templates/analysis/analiz_detay.html)
            analiz=analiz,
            altyapi=altyapi_parsed, # Şablona parse edilmiş altyapı listesini gönder
            swot=swot_analizi_parsed,
            sonuc=analiz_sonuclari_data, # ArsaAnalizci'den gelen tüm sonuçlar
            ozet=ozet,
            user=analiz_sahibi_user,
            medyalar=medyalar,
            file_id=str(analiz.id), # Rapor linkleri için
            tahmin=tahmin_sonucu,
            read_only_mode=read_only_mode
        )
    except Exception as e:
        current_app.logger.error(f"Analiz Detay Sayfası Hatası (ID: {analiz_id}): {str(e)}", exc_info=True)
        flash("Analiz görüntülenirken beklenmedik bir hata oluştu.", "danger")
        return redirect(url_for('analysis.analizler'))


@analysis_bp.route('/list') # Eski /analizler
@login_required
def analizler():
    user_id = current_user.id
    iller = (
        db.session.query(ArsaAnaliz.il)
        .filter_by(user_id=user_id)
        .distinct()
        .order_by(ArsaAnaliz.il)
        .all()
    )
    iller_list = [il[0] for il in iller] # Tuple listesinden string listesine

    all_analizler = (
        ArsaAnaliz.query.filter_by(user_id=user_id)
        .order_by(ArsaAnaliz.created_at.desc())
        .all()
    )

    grouped_analizler = {}
    ay_isimleri_tr = {1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"}
    for analiz_item in all_analizler:
        key = f"{ay_isimleri_tr[analiz_item.created_at.month]} {analiz_item.created_at.year}"
        if key not in grouped_analizler:
            grouped_analizler[key] = []
        grouped_analizler[key].append(analiz_item)

    return render_template(
        "analizler.html", # templates/analizler.html
        grouped_analizler=grouped_analizler,
        total_count=len(all_analizler),
        iller=iller_list
    )

@analysis_bp.route('/delete/<int:analiz_id>', methods=['POST']) # Eski /analiz/sil/...
@login_required
def analiz_sil(analiz_id):
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != current_user.id:
        flash("Bu analizi silme yetkiniz yok.", "danger")
        return redirect(url_for('analysis.analizler'))
    try:
        _analizi_sil(analiz)
        db.session.commit()
        flash("Analiz ve ilişkili medyalar başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analiz silme hatası: {str(e)}", exc_info=True)
        flash("Analiz silinirken bir hata oluştu.", "danger")
    return redirect(url_for('analysis.analizler'))


@analysis_bp.route('/<int:analiz_id>/media_upload', methods=['POST']) # Eski /analiz/.../medya_yukle
@login_required
def medya_yukle(analiz_id):
    analiz = ArsaAnaliz.query.get_or_404(analiz_id)
    if analiz.user_id != current_user.id:
        flash("Bu analize medya yükleme yetkiniz yok.", "danger")
        return redirect(url_for('analysis.analizler'))

    if 'medya' not in request.files:
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))
    
    file = request.files['medya']
    if file.filename == '':
        flash('Dosya seçilmedi.', 'warning')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))

    if file and file.filename and allowed_file(file.filename): # allowed_file bu BP içinde tanımlı
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        medya_type = 'image' if ext in {'jpg', 'jpeg', 'png', 'gif'} else 'video'
        
        # Analize özel klasör oluştur
        analiz_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(analiz_id))
        os.makedirs(analiz_upload_folder, exist_ok=True)
        
        # Benzersiz dosya adı oluşturma (aynı isimde dosya yüklenirse üzerine yazmasın diye)
        # unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}" 
        # Veya basitçe mevcut dosya adını kullanıp üzerine yazsın:
        unique_filename = filename
        filepath = os.path.join(analiz_upload_folder, unique_filename)
        
        try:
            file.save(filepath)
            # Veritabanına göreceli yolu kaydet (örn: "123/resim.jpg")
            db_filename = os.path.join(str(analiz_id), unique_filename).replace(os.sep, '/')
            medya_kaydi = AnalizMedya()
            medya_kaydi.analiz_id = analiz_id
            medya_kaydi.filename = db_filename
            medya_kaydi.type = medya_type
            db.session.add(medya_kaydi)
            db.session.commit()
            flash('Medya başarıyla yüklendi.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Medya kaydetme hatası: {e}", exc_info=True)
            flash('Medya yüklenirken bir hata oluştu.', 'danger')
    else:
        flash('Geçersiz dosya türü.', 'danger')
    return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))


@analysis_bp.route('/<int:analiz_id>/media_delete/<int:medya_id>', methods=['POST']) # Eski /analiz/.../medya_sil/...
@login_required
def medya_sil(analiz_id, medya_id):
    medya = AnalizMedya.query.get_or_404(medya_id)
    analiz = ArsaAnaliz.query.get_or_404(analiz_id) # Medyanın analizini de alalım
    
    if analiz.user_id != current_user.id or medya.analiz_id != analiz_id:
        flash('Yetkisiz işlem.', 'danger')
        return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))

    try:
        # medya.filename 'analiz_id/dosyaadi' formatında
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], medya.filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(medya)
        db.session.commit()
        flash('Medya başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Medya silme hatası: {e}", exc_info=True)
        flash('Medya silinirken bir hata oluştu.', 'danger')
    return redirect(url_for('analysis.analiz_detay', analiz_id=analiz_id))


# Rapor Oluşturma Rotası (Word, PDF)
# Eski /generate/<format>/<file_id>
@analysis_bp.route('/report/generate/<string:format_type>/<int:analiz_id_param>')
@login_required
def generate_report(format_type, analiz_id_param):
    """Eski rapor rotası: /report/generate/<word|pdf>/<id> (tema/renk ayarlarıyla)."""
    analiz = ArsaAnaliz.query.filter_by(id=analiz_id_param, user_id=current_user.id).first_or_404()
    fmt = {'word': 'word', 'docx': 'word', 'pdf': 'pdf', 'pptx': 'pptx'}.get(format_type)
    if not fmt:
        flash("Geçersiz rapor formatı.", "danger")
        return redirect(url_for('analysis.view_analysis', analysis_id=analiz.id))
    settings = {"theme": request.args.get("theme", "classic"),
                "color_scheme": request.args.get("color_scheme", "blue")}
    return _report_or_redirect(analiz, fmt, settings)


# Sunum Oluşturma Rotası (PPTX)
# Eski /generate/pptx/<int:analiz_id>
@analysis_bp.route('/report/generate_pptx/<int:analiz_id>', methods=['POST']) # POST olmalı, formdan veri alacak
@login_required
def generate_pptx(analiz_id):
    """PowerPoint sunumu indir."""
    analiz = ArsaAnaliz.query.filter_by(id=analiz_id, user_id=current_user.id).first_or_404()
    settings = {"color_scheme": request.form.get("color_scheme", "blue")}
    try:
        return _build_report(analiz, 'pptx', settings)
    except Exception as e:
        current_app.logger.error(f"PPTX oluşturma hatası (ID: {analiz_id}): {e}", exc_info=True)
        return jsonify({"error": "Sunum oluşturulurken bir hata oluştu."}), 500


