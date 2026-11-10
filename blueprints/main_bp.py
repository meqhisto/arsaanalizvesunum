# blueprints/main_bp.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, 
    session, send_from_directory, current_app
)
from flask_login import login_required, current_user
# from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import pytz # User.localize_datetime için
from decimal import Decimal # Sayısal işlemler için
from sqlalchemy import text, cast, Date # index route'undaki sorgu için
from models.office_models import Office # Office modelini import et

# Modelleri ve db nesnesini models paketinden import et
from models import db
from models.user_models import User
from models.arsa_models import ArsaAnaliz, BolgeDagilimi, DashboardStats
# CRM Modelleri (index sayfasında CRM özeti için gerekli)
from models.crm_models import Contact, Deal, Interaction, Task
from .auth_decorators import broker_required # BU IMPORT SATIRI EKSİK OLABİLİR VEYA YANLIŞ YERDE OLABİLİR


main_bp = Blueprint('main', __name__, template_folder='../templates')
# template_folder='../templates' ayarı, şablonların ana 'templates' klasöründe olduğunu varsayar.
# Örneğin, render_template('index.html') templates/index.html dosyasını arar.
# Eğer templates/main/index.html gibi bir yapınız varsa, template_folder='../templates/main' yapın.

@main_bp.route('/')
def home(): # Eski home() fonksiyonu
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return redirect(url_for('auth.login')) # auth Blueprint'indeki login'e yönlendir

@main_bp.route('/broker/dashboard')
@login_required
@broker_required
def broker_dashboard():
    """Broker Dashboard - Ofis yönetimi ve ekip performansı"""

    # Broker'ın ofis bilgilerini al
    office = current_user.office if current_user.office_id else None

    # Temel istatistikler
    stats = {
        'office_consultants': 0,
        'monthly_analyses': 0,
        'active_customers': 0,
        'pending_tasks': 0
    }

    if office:
        # Ofis danışmanlarını say
        stats['office_consultants'] = User.query.filter_by(office_id=office.id, role='danisman').count()

        # Bu ay yapılan analizler
        from datetime import datetime
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stats['monthly_analyses'] = ArsaAnaliz.query.filter(
            ArsaAnaliz.office_id == office.id,
            ArsaAnaliz.created_at >= start_of_month
        ).count()

        # Aktif müşteriler
        stats['active_customers'] = Contact.query.filter_by(office_id=office.id).count()

    # Ekip üyeleri
    team_members = []
    if office:
        team_members = User.query.filter(
            User.office_id == office.id,
            User.id != current_user.id
        ).limit(5).all()

    return render_template('dashboard_base.html',
                         page_title="Broker Dashboard",
                         page_subtitle="Ofis yönetimi ve ekip performansı",
                         office=office,
                         stats=stats,
                         team_members=team_members,
                         show_broker_content=True)

@main_bp.route('/broker/team')
@login_required
@broker_required
def broker_team():
    """Broker Ekip Yönetimi"""
    office = current_user.office if current_user.office_id else None

    team_members = []
    if office:
        team_members = User.query.filter(
            User.office_id == office.id,
            User.id != current_user.id
        ).all()

    return render_template('dashboard_base.html',
                         page_title="Ekip Yönetimi",
                         page_subtitle="Ofis çalışanlarını yönetin",
                         office=office,
                         team_members=team_members,
                         show_team_content=True)

@main_bp.route('/broker/permissions')
@login_required
@broker_required
def broker_permissions():
    """Broker Yetki Yönetimi"""
    office = current_user.office if current_user.office_id else None

    team_members = []
    if office:
        team_members = User.query.filter(
            User.office_id == office.id,
            User.id != current_user.id
        ).all()

    return render_template('dashboard_base.html',
                         page_title="Yetki Yönetimi",
                         page_subtitle="Ekip üyelerinin yetkilerini yönetin",
                         office=office,
                         team_members=team_members,
                         show_permissions_content=True)

@main_bp.route('/broker/reports')
@login_required
@broker_required
def broker_reports():
    """Broker Performans Raporları"""
    office = current_user.office if current_user.office_id else None

    return render_template('dashboard_base.html',
                         page_title="Performans Raporları",
                         page_subtitle="Ofis ve ekip performans analizi",
                         office=office,
                         show_reports_content=True)

@main_bp.route('/my_office', methods=['GET', 'POST'])
@login_required
@broker_required
def my_office():
    broker = current_user
    office = Office.query.get(broker.office_id) if broker.office_id else None
    
    if not office:
        if broker.firma:
            # First check if office exists with this name
            existing_office = Office.query.filter_by(name=broker.firma).first()
            if not existing_office:
                # Create new office with required fields
                office = Office()
                office.name = broker.firma
                office.created_at = datetime.utcnow()
                office.updated_at = datetime.utcnow()
                db.session.add(office)
                broker.office = office
                db.session.commit()
                flash(f"'{office.name}' adında yeni bir ofis sizin için oluşturuldu.", "info")
            else:
                broker.office = existing_office
                db.session.commit()
                office = existing_office
        else:
            flash("Bir ofise atanmamışsınız. Lütfen sistem yöneticisi ile iletişime geçin.", "warning")
            return redirect(url_for('main.index'))

    team_members = User.query.filter(User.office_id == office.id, User.id != broker.id).all()

    if request.method == 'POST': # Yeni danışman/çalışan ekleme
        # Get form data first
        form_data = {
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'ad': request.form.get('ad'),
            'soyad': request.form.get('soyad'),
            'role': request.form.get('role', 'danisman')
        }
        # Broker yalnızca kendi ekibine danışman/çalışan ekleyebilir (rol formdan serbestçe alınmaz)
        if form_data['role'] not in ('danisman', 'calisan'):
            flash('Geçersiz rol seçimi.', 'danger')
            return render_template('my_office.html',
                                office=office,
                                team_members=team_members,
                                form_data=form_data), 400

        # Validate required fields
        if not all([form_data['email'], form_data['password'], 
                   form_data['ad'], form_data['soyad']]):
            flash('E-posta, şifre, ad ve soyad zorunludur!', 'danger')
            return render_template('my_office.html', 
                                office=office, 
                                team_members=team_members,
                                form_data=form_data)

        # Check if email is unique
        if User.query.filter_by(email=form_data['email']).first():
            flash('Bu e-posta adresi zaten kullanımda!', 'danger')
            return render_template('my_office.html', 
                                office=office, 
                                team_members=team_members,
                                form_data=form_data)

        # Create new user
        new_member = User()
        new_member.email = form_data['email']
        new_member.ad = form_data['ad']
        new_member.soyad = form_data['soyad']
        new_member.role = form_data['role']
        new_member.office_id = office.id
        new_member.manager_id = broker.id
        new_member.firma = office.name
        new_member.set_password(form_data['password'])
        
        try:
            db.session.add(new_member)
            db.session.commit()
            flash(f"Ekip üyesi '{form_data['ad']} {form_data['soyad']}' eklendi.", 'success')
            return redirect(url_for('main.my_office'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding new member: {str(e)}")
            flash('Ekip üyesi eklenirken bir hata oluştu!', 'danger')
            return render_template('my_office.html', 
                                office=office, 
                                team_members=team_members,
                                form_data=form_data)
            
    return render_template('my_office.html', office=office, team_members=team_members)

@main_bp.route('/index')
@login_required
def index():
    # Bu fonksiyonun içeriği eski app.py'deki index() ile aynı olacak.
    # current_user Flask-Login tarafından sağlanır.
    # User, ArsaAnaliz, DashboardStats, BolgeDagilimi, Contact, Deal, Interaction, Task modelleri
    # yukarıda import edildi.

    user_id = current_user.id  # Giriş yapmış kullanıcının ID'si
    
    # --- Mevcut Arsa Analiz Verileri ve İstatistikler ---
    # Toplam değer ve sayı tek sorguda (uzak veritabanında her sorgu ~50 ms)
    toplam_arsa_degeri, toplam_arsa_sayisi = db.session.query(
        db.func.coalesce(db.func.sum(ArsaAnaliz.fiyat), 0), db.func.count(ArsaAnaliz.id)
    ).filter(ArsaAnaliz.user_id == user_id).one()
    toplam_arsa_degeri = Decimal(toplam_arsa_degeri or 0)
    
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if not stats: # Eğer kullanıcı için istatistik yoksa oluştur
        stats = DashboardStats()
        stats.user_id = user_id
        stats.toplam_arsa_sayisi = toplam_arsa_sayisi
        stats.ortalama_fiyat = float(toplam_arsa_degeri/toplam_arsa_sayisi) if toplam_arsa_sayisi > 0 else 0
        stats.en_yuksek_fiyat = db.session.query(db.func.max(ArsaAnaliz.fiyat)).filter_by(user_id=user_id).scalar() or 0
        stats.en_dusuk_fiyat = db.session.query(db.func.min(ArsaAnaliz.fiyat)).filter_by(user_id=user_id).scalar() or 0
        stats.toplam_deger = toplam_arsa_degeri
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
                "mesaj": f"{analiz.il}, {analiz.ilce} bölgesinde yeni gayrimenkul kaydı oluşturuldu.",
                "url": url_for('analysis.view_analysis', analysis_id=analiz.id), # 'analysis' blueprint'i
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
    # Son 6 ayın kayıt sayıları tek sorguda
    ilk_ay_offset = current_date.month - 1 - 5
    ilk_ay = datetime(current_date.year + (ilk_ay_offset // 12), (ilk_ay_offset % 12) + 1, 1)
    yil_ifadesi = db.extract("year", ArsaAnaliz.created_at)
    ay_ifadesi = db.extract("month", ArsaAnaliz.created_at)
    aylik_sayim = {
        (int(yil), int(ay)): sayi
        for yil, ay, sayi in db.session.query(yil_ifadesi, ay_ifadesi, db.func.count(ArsaAnaliz.id))
        .filter(ArsaAnaliz.user_id == user_id, ArsaAnaliz.created_at >= ilk_ay)
        .group_by(yil_ifadesi, ay_ifadesi)
    }
    for i in range(6):
        month_offset = current_date.month - 1 - i
        target_year = current_date.year + (month_offset // 12)
        target_month = (month_offset % 12) + 1
        ay_analiz_sayisi = aylik_sayim.get((target_year, target_month), 0)
        ay_isimleri = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
        son_alti_ay_analiz.insert(0, f"{ay_isimleri[target_month]} {str(target_year)[-2:]}")
        aylik_analiz_sayilari_arsa.insert(0, ay_analiz_sayisi)

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
    toplam_contact_sayisi = Contact.query.filter_by(user_id=user_id).count()
    
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
        "new_index.html",
        # current_user şablona zaten Flask-Login tarafından veya context_processor ile ekleniyor
        stats=stats, # DashboardStats objesi
        recent_analyses=son_arsa_analizleri,
        recent_contacts=son_aktiviteler_listesi,
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
        toplam_contact_sayisi=toplam_contact_sayisi,
        acik_firsatlar=acik_firsatlar,
        toplam_acik_firsat_sayisi=toplam_acik_firsat_sayisi,
        toplam_acik_firsat_degeri_try=toplam_acik_firsat_degeri_try,
        son_etkilesimler=son_etkilesimler
    )

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Giriş yapmış kullanıcının profili
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

            foto = request.files.get('profil_foto')
            foto_reddedildi = False
            if foto and foto.filename:
                from flask import current_app
                from utils.yukleme import resim_kaydet
                # HEIC/webp JPEG'e çevrilir, büyük fotoğraflar 800 px'e küçültülür
                kaydedilen = resim_kaydet(foto, os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles", str(user.id)),
                                          en_buyuk_kenar=800)
                if kaydedilen:
                    user.profil_foto = f"profiles/{user.id}/{kaydedilen}"
                else:
                    foto_reddedildi = True

            db.session.commit()
            flash('Profil başarıyla güncellendi!', 'success')
            if foto_reddedildi:
                flash('Profil fotoğrafı yüklenemedi: desteklenen türler jpg, png, gif, webp ve HEIC.', 'warning')
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
    
    if not new_password or len(new_password) < 6: # Şifre uzunluk kontrolü
        flash('Yeni şifre en az 6 karakter olmalıdır!', 'danger')
        return redirect(url_for('main.profile'))

    user.set_password(new_password)
    db.session.commit()

    flash('Şifreniz başarıyla güncellendi.', 'success')
    return redirect(url_for('main.profile'))

# blueprints/main_bp.py
@main_bp.route('/analysis-form') # Varsayılan olarak sadece GET
@login_required
def analysis_form():
    """Eski adres: yeni gayrimenkul formuna yönlendirir."""
    return redirect(url_for('analysis.new_analysis'))

@main_bp.route('/login')
def login_redirect():
    """Redirect /login to /auth/login for backward compatibility"""
    return redirect(url_for('auth.login'))

@main_bp.route('/logout')
def logout_redirect():
    """Redirect /logout to /auth/logout for backward compatibility"""
    return redirect(url_for('auth.logout'))

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