# blueprints/main_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import pytz # User.localize_datetime için
from decimal import Decimal # Sayısal işlemler için
from sqlalchemy import text, cast, Date # index route'undaki sorgu için

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats
# CRM Modelleri (index sayfasında CRM özeti için gerekli)
from models.crm_models import Contact, Deal, Interaction, Task


main_bp = Blueprint('main', __name__, template_folder='../templates')
# template_folder='../templates' ayarı, şablonların ana 'templates' klasöründe olduğunu varsayar.
# Örneğin, render_template('index.html') templates/index.html dosyasını arar.
# Eğer templates/main/index.html gibi bir yapınız varsa, template_folder='../templates/main' yapın.

@main_bp.route('/')
def home(): # Eski home() fonksiyonu
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return redirect(url_for('auth.login')) # auth Blueprint'indeki login'e yönlendir

@main_bp.route('/index')
@login_required # Flask-Login'den gelen decorator
def index():
    # Bu fonksiyonun içeriği eski app.py'deki index() ile aynı olacak.
    # current_user Flask-Login tarafından sağlanır.
    # User, ArsaAnaliz, DashboardStats, BolgeDagilimi, Contact, Deal, Interaction, Task modelleri
    # yukarıda import edildi.
    
    user_id = current_user.id # Artık session['user_id'] yerine current_user.id kullanabiliriz
    
    # --- Mevcut Arsa Analiz Verileri ve İstatistikler ---
    arsa_bolge_dagilimi = db.session.query(
        ArsaAnaliz.il,
        db.func.count(ArsaAnaliz.id).label('analiz_sayisi')
    ).filter(
        ArsaAnaliz.user_id == user_id
    ).group_by(
        ArsaAnaliz.il
    ).order_by(
        db.func.count(ArsaAnaliz.id).desc()
    ).all()

    grafik_bolge_labels = [b.il for b in arsa_bolge_dagilimi]
    grafik_bolge_data_sayi = [b.analiz_sayisi for b in arsa_bolge_dagilimi]
    
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats: # Eğer kullanıcı için istatistik yoksa oluştur
        stats = DashboardStats(
            user_id=user_id, 
            toplam_arsa_sayisi=0, 
            ortalama_fiyat=0.0, 
            en_yuksek_fiyat=0.0, 
            en_dusuk_fiyat=9999999999.0, # Sonsuz yerine çok büyük bir sayı kullanıyoruz
            toplam_deger=Decimal('0.00')
        )
        db.session.add(stats)
        # db.session.commit() # Commit'i toplu yapmak daha iyi olabilir, ama burada da yapılabilir.

    son_arsa_analizleri = (
        ArsaAnaliz.query.filter_by(user_id=user_id)
        .order_by(ArsaAnaliz.created_at.desc())
        .limit(5)
        .all()
    )

    son_aktiviteler_listesi = []
    for analiz in son_arsa_analizleri:
        son_aktiviteler_listesi.append(
            {
                "tarih": analiz.created_at,
                "mesaj": f"{analiz.il}, {analiz.ilce} bölgesinde yeni arsa analizi oluşturuldu.",
                "url": url_for('analysis.analiz_detay', analiz_id=analiz.id), # 'analysis' blueprint'i
                "tip": "analiz" 
            }
        )
    
    bolge_dagilimlari = BolgeDagilimi.query.filter_by(user_id=user_id).all()
    chart_bolge_labels_deger = [b.il for b in bolge_dagilimlari]
    chart_bolge_data_deger = [float(b.toplam_deger) if b.toplam_deger else 0.0 for b in bolge_dagilimlari]
    zipped = list(zip(chart_bolge_labels_deger, chart_bolge_data_deger))

    son_alti_ay_analiz = []
    aylik_analiz_sayilari_arsa = []
    current_date = datetime.utcnow()
    for i in range(6):
        month_offset = current_date.month - 1 - i
        target_year = current_date.year + (month_offset // 12)
        target_month = (month_offset % 12) + 1
        ay_analiz_sayisi = ArsaAnaliz.query.filter(
            ArsaAnaliz.user_id == user_id,
            db.extract("year", ArsaAnaliz.created_at) == target_year,
            db.extract("month", ArsaAnaliz.created_at) == target_month,
        ).count()
        ay_isimleri = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
        son_alti_ay_analiz.insert(0, f"{ay_isimleri[target_month]} {str(target_year)[-2:]}")
        aylik_analiz_sayilari_arsa.insert(0, ay_analiz_sayisi)

    toplam_arsa_degeri = (
        db.session.query(db.func.sum(ArsaAnaliz.fiyat))
        .filter_by(user_id=user_id)
        .scalar() or Decimal(0)
    )
    toplam_arsa_sayisi = ArsaAnaliz.query.filter_by(user_id=user_id).count()

    # --- YENİ: CRM Özet Verileri ---
    today_utc_date = datetime.utcnow().date()
    one_week_later_utc_date = today_utc_date + timedelta(days=7)
    
    yaklasan_gorevler = Task.query.filter(
        Task.assigned_to_user_id == user_id, # veya Task.user_id == user_id (görevi oluşturan)
        Task.status.notin_(['Tamamlandı', 'İptal Edildi']),
        Task.due_date != None,
        cast(Task.due_date, Date) >= today_utc_date,
        cast(Task.due_date, Date) <= one_week_later_utc_date
    ).order_by(Task.due_date.asc()).limit(5).all()

    son_kisiler = Contact.query.filter_by(user_id=user_id).order_by(Contact.created_at.desc()).limit(5).all()
    
    acik_firsatlar = Deal.query.filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi'])
    ).order_by(Deal.created_at.desc()).limit(5).all()
    
    toplam_acik_firsat_sayisi = Deal.query.filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi'])
    ).count()
    
    toplam_acik_firsat_degeri_try = db.session.query(db.func.sum(Deal.value)).filter(
        Deal.user_id == user_id,
        Deal.stage.notin_(['Kazanıldı', 'Kaybedildi']),
        Deal.currency == 'TRY'
    ).scalar() or Decimal(0)
    
    son_etkilesimler = Interaction.query.filter_by(user_id=user_id).order_by(Interaction.interaction_date.desc()).limit(5).all()

    # İstatistikler güncellenmediyse, varsayılan değerleri (0 veya boş) kullan
    # Bu, stats nesnesi None ise veya alanları None ise bir sorun yaratabilir.
    # Yukarıda stats None ise oluşturduk, şimdi alanlarının None olup olmadığını kontrol edebiliriz.
    # Ancak DashboardStats modelinde default değerler olduğu için bu genellikle sorun olmaz.

    return render_template(
        "index.html",
        # current_user şablona zaten Flask-Login tarafından veya context_processor ile ekleniyor
        stats=stats, # DashboardStats objesi
        analizler=son_arsa_analizleri,
        son_aktiviteler=son_aktiviteler_listesi,
        son_alti_ay=son_alti_ay_analiz,
        aylik_analiz_sayilari=aylik_analiz_sayilari_arsa,
        bolge_labels=chart_bolge_labels_deger, # Değer bazlı dağılım için
        bolge_data=chart_bolge_data_deger,     # Değer bazlı dağılım için
        # Grafik için sayı bazlı dağılım da gönderilebilir (opsiyonel)
        # grafik_bolge_labels_sayi=grafik_bolge_labels,
        # grafik_bolge_data_sayi=grafik_bolge_data_sayi,
        toplam_deger=toplam_arsa_degeri, # Arsa için toplam değer
        toplam_portfoy=toplam_arsa_sayisi, # Arsa için toplam sayı
        zipped=zipped, # BolgeDagilimi'nden gelen il ve toplam değer çiftleri
        
        # CRM Özet Verileri
        yaklasan_gorevler=yaklasan_gorevler,
        son_kisiler=son_kisiler,
        acik_firsatlar=acik_firsatlar,
        toplam_acik_firsat_sayisi=toplam_acik_firsat_sayisi,
        toplam_acik_firsat_degeri_try=toplam_acik_firsat_degeri_try,
        son_etkilesimler=son_etkilesimler
    )

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # current_user Flask-Login tarafından sağlanır.
    # user = User.query.get(current_user.id) # Buna gerek yok, current_user zaten User objesi
    user = current_user
    timezones_list = pytz.all_timezones # pytz.all_timezones bir liste döndürür

    if request.method == 'POST':
        try:
            user.ad = request.form.get('ad')
            user.soyad = request.form.get('soyad')
            user.telefon = request.form.get('telefon')
            user.firma = request.form.get('firma')
            user.unvan = request.form.get('unvan')
            user.adres = request.form.get('adres')
            selected_timezone = request.form.get('timezone')
            if selected_timezone in timezones_list:
                user.timezone = selected_timezone
            else:
                user.timezone = "UTC" 

            if 'profil_foto' in request.files:
                file = request.files['profil_foto']
                # app.config['UPLOAD_FOLDER'] ve allowed_file'a erişim lazım.
                # Bunları current_app üzerinden alabiliriz.
                from flask import current_app # Fonksiyon içinde import
                
                def allowed_file(filename): # Bu fonksiyonu da buraya taşıyabilir veya global bir yardımcı modüle alabiliriz
                    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"} # Ana app'den alınabilir
                    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

                if file and allowed_file(file.filename):
                    from werkzeug.utils import secure_filename # Fonksiyon içinde import
                    filename = secure_filename(file.filename)
                    user_upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles", str(user.id))
                    os.makedirs(user_upload_dir, exist_ok=True)
                    filepath = os.path.join(user_upload_dir, filename)
                    file.save(filepath)
                    relative_path = os.path.join("profiles", str(user.id), filename).replace(os.sep, '/') # OS bağımsız yol
                    user.profil_foto = relative_path
            
            db.session.commit()
            flash('Profil başarıyla güncellendi!', 'success')
            return redirect(url_for('main.profile'))

        except Exception as e:
            db.session.rollback()
            import logging
            logging.getLogger(__name__).error(f"Profile update error: {str(e)}", exc_info=True)
            flash('Profil güncellenirken bir hata oluştu!', 'danger')
            
    return render_template('profile.html', user=user, timezones=timezones_list)


@main_bp.route('/change-password', methods=['POST'])
@login_required
def change_password(): # endpoint eski app.py'de 'change_password' idi, fonksiyon adı da aynı olabilir.
    # Bu fonksiyon sadece POST kabul ediyor ve profile.html içindeki formdan çağrılıyor.
    # current_user Flask-Login tarafından sağlanır.
    user = current_user

    current_password_form = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not user.check_password(current_password_form):
        flash('Mevcut şifreniz yanlış!', 'danger')
        return redirect(url_for('main.profile'))

    if new_password != confirm_password:
        flash('Yeni şifreler eşleşmiyor!', 'danger')
        return redirect(url_for('main.profile'))
    
    if len(new_password) < 6: # Şifre uzunluk kontrolü
        flash('Yeni şifre en az 6 karakter olmalıdır!', 'danger')
        return redirect(url_for('main.profile'))

    user.set_password(new_password)
    db.session.commit()

    flash('Şifreniz başarıyla güncellendi.', 'success')
    return redirect(url_for('main.profile'))

@main_bp.route('/analysis-form')
@login_required
def analysis_form():
    # Eğer formda önceden doldurulmuş veri (hata durumunda) varsa, onu al
    # Bu, ana app.py'deki submit_analysis içinde session'a kaydediliyordu.
    # Bu mantığı buraya veya formun POST edildiği yere taşımak gerekebilir.
    # Şimdilik sadece şablonu render edelim.
    form_data = session.pop('analysis_form_data', None)
    form_errors = session.pop('analysis_form_errors', None)
    return render_template('analysis_form.html', form_data=form_data, form_errors=form_errors)

@main_bp.route('/favicon.ico')
def favicon():
    # send_from_directory için current_app.root_path kullanılabilir.
    from flask import current_app # Fonksiyon içinde import
    favicon_path = os.path.join(current_app.root_path, 'static', 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_from_directory(
            os.path.join(current_app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    else:
        return '', 204

# Diğer genel rotalar (hakkımızda, iletişim vb.) buraya eklenebilir.