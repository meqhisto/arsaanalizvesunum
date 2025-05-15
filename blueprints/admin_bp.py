# blueprints/admin_bp.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.security import generate_password_hash

from models import db
from models.user_models import User
from models.office_models import Office
from .auth_decorators import superadmin_required
import os
from flask_login import login_required, current_user # <-- current_user'ı buradan import edin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../templates/admin')

# --- DASHBOARD ---
@admin_bp.route('/dashboard')
@login_required
@superadmin_required
def dashboard():
    # ... (mevcut dashboard kodu) ...
    total_users = User.query.count()
    total_offices = Office.query.count()
    total_brokers = User.query.filter_by(role='broker').count()
    total_consultants = User.query.filter_by(role='danisman').count()
    recent_offices = Office.query.order_by(Office.created_at.desc()).limit(5).all()
    recent_brokers = User.query.filter_by(role='broker').order_by(User.registered_on.desc()).limit(5).all()
    return render_template('admin_dashboard.html', total_users=total_users, total_offices=total_offices,
                           total_brokers=total_brokers, total_consultants=total_consultants,
                           recent_offices=recent_offices, recent_brokers=recent_brokers)

# --- OFİS YÖNETİMİ ---
@admin_bp.route('/offices')
@login_required
@superadmin_required
def list_offices():
    offices = Office.query.order_by(Office.name).all()
    return render_template('list_offices.html', offices=offices)

@admin_bp.route('/office/create', methods=['GET', 'POST']) # URL'i create_office'ten buna değiştirdim
@login_required
@superadmin_required
def create_office(): # Fonksiyon adı aynı kalabilir
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        logo_file = request.files.get('logo_path') # Logo yükleme
        is_active = 'is_active' in request.form
        is_valid = True

        if not name:
            flash('Ofis adı zorunludur!', 'danger')
            is_valid = False
        elif Office.query.filter_by(name=name).first():
            flash('Bu isimde bir ofis zaten mevcut!', 'warning')
            is_valid = False
        
        logo_filename = None
        if logo_file and logo_file.filename != '':
            if allowed_file(logo_file.filename): # allowed_file fonksiyonunu tanımlamanız/import etmeniz gerek
                from werkzeug.utils import secure_filename
                filename = secure_filename(logo_file.filename)
                # Ofise özel bir alt klasör veya benzersiz adlandırma
                logo_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'office_logos')
                os.makedirs(logo_upload_folder, exist_ok=True)
                logo_path = os.path.join(logo_upload_folder, filename)
                logo_file.save(logo_path)
                logo_filename = os.path.join('office_logos', filename).replace(os.sep, '/') # Veritabanına göreceli yol
            else:
                flash('Geçersiz logo dosyası türü.', 'warning')
                is_valid = False
        
        if not is_valid:
            return render_template('office_form.html', form_title="Yeni Ofis Oluştur", form_data=request.form, office=None)

        try:
            new_office = Office(name=name, address=address, phone=phone, logo_path=logo_filename, is_active=is_active)
            db.session.add(new_office)
            db.session.commit()
            flash(f"'{new_office.name}' adlı ofis başarıyla oluşturuldu.", "success")
            return redirect(url_for('admin.list_offices'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ofis oluşturulurken hata: {str(e)}", exc_info=True)
            flash(f"Ofis oluşturulurken bir hata oluştu: {str(e)}", "danger")
            return render_template('office_form.html', form_title="Yeni Ofis Oluştur", form_data=request.form, office=None)
    
    return render_template('office_form.html', form_title="Yeni Ofis Oluştur", form_data={}, office=None)


@admin_bp.route('/office/<int:office_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_office(office_id):
    office = Office.query.get_or_404(office_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        logo_file = request.files.get('logo_path')
        is_active = 'is_active' in request.form
        is_valid = True

        if not name:
            flash('Ofis adı zorunludur!', 'danger')
            is_valid = False
        elif name != office.name and Office.query.filter_by(name=name).first():
            flash('Bu isimde başka bir ofis zaten mevcut!', 'warning')
            is_valid = False

        logo_filename = office.logo_path # Mevcut logoyu koru
        if logo_file and logo_file.filename != '':
            if allowed_file(logo_file.filename):
                from werkzeug.utils import secure_filename
                filename = secure_filename(logo_file.filename)
                logo_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'office_logos')
                os.makedirs(logo_upload_folder, exist_ok=True)
                
                # Eski logoyu sil (opsiyonel)
                if office.logo_path:
                    old_logo_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], office.logo_path)
                    if os.path.exists(old_logo_full_path):
                        try: os.remove(old_logo_full_path)
                        except: pass
                
                logo_path = os.path.join(logo_upload_folder, filename)
                logo_file.save(logo_path)
                logo_filename = os.path.join('office_logos', filename).replace(os.sep, '/')
            else:
                flash('Geçersiz logo dosyası türü. Logo güncellenmedi.', 'warning')
                # is_valid = False # Sadece logoyu güncellemiyorsak formu göndermeye devam edebiliriz

        if not is_valid: # Sadece isim kontrolünden geçemediyse
             return render_template('office_form.html', form_title="Ofis Düzenle", form_data=request.form, office=office)

        try:
            office.name = name
            office.address = address
            office.phone = phone
            if logo_filename is not None or (logo_file and logo_file.filename == ''): # Eğer yeni logo seçilmediyse ve boş dosya da gönderilmediyse mevcutu koru, aksi halde güncelle (boş bile olsa)
                 if not (logo_file and logo_file.filename == '' and office.logo_path): # Eğer boş dosya gönderildiyse ve mevcut logo varsa, logoyu sil (None yap)
                     office.logo_path = logo_filename
                 elif (logo_file and logo_file.filename == ''):
                      office.logo_path = None


            office.is_active = is_active
            db.session.commit()
            flash(f"'{office.name}' adlı ofis başarıyla güncellendi.", "success")
            return redirect(url_for('admin.list_offices'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Ofis güncellenirken hata (ID: {office_id}): {str(e)}", exc_info=True)
            flash(f"Ofis güncellenirken bir hata oluştu: {str(e)}", "danger")
            return render_template('office_form.html', form_title="Ofis Düzenle", form_data=request.form, office=office)

    # GET isteği için formu ofis verileriyle doldur
    form_data = {
        'name': office.name, 'address': office.address, 'phone': office.phone,
        'is_active': office.is_active, 'current_logo_path': office.logo_path
    }
    return render_template('office_form.html', form_title="Ofis Düzenle", form_data=form_data, office=office)


@admin_bp.route('/office/<int:office_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_office(office_id):
    office = Office.query.get_or_404(office_id)
    try:
        # Ofise bağlı kullanıcıların office_id'lerini NULL yap
        User.query.filter_by(office_id=office.id).update({'office_id': None})
        
        # Ofis logosunu sil
        if office.logo_path:
            logo_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], office.logo_path)
            if os.path.exists(logo_full_path):
                try: os.remove(logo_full_path)
                except: pass

        db.session.delete(office)
        db.session.commit()
        flash(f"'{office.name}' adlı ofis ve bağlı kullanıcıların ofis atamaları başarıyla silindi/kaldırıldı.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Ofis silinirken hata (ID: {office_id}): {str(e)}", exc_info=True)
        flash(f"Ofis silinirken bir hata oluştu: {str(e)}", "danger")
    return redirect(url_for('admin.list_offices'))

# --- BROKER YÖNETİMİ (create_broker zaten vardı, onu güncelleyelim) ---
@admin_bp.route('/broker/create', methods=['GET', 'POST']) # URL'i create_broker'dan buna değiştirdim
@login_required
@superadmin_required
def create_broker(): # Fonksiyon adı aynı
    offices = Office.query.filter_by(is_active=True).order_by(Office.name).all()
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ad = request.form.get('ad', '').strip()
        soyad = request.form.get('soyad', '').strip()
        firma = request.form.get('firma', '').strip() # Bu User.firma alanı
        unvan = request.form.get('unvan', '').strip()
        office_id_str = request.form.get('office_id')
        is_active_broker = 'is_active' in request.form # Broker için aktiflik durumu
        is_valid = True
        error_messages = []

        if not all([email, password, ad, soyad, office_id_str]):
            error_messages.append('E-posta, şifre, ad, soyad ve ofis seçimi zorunludur!')
            is_valid = False
        if User.query.filter_by(email=email).first():
            error_messages.append('Bu e-posta adresi zaten kayıtlı!')
            is_valid = False
        if len(password) < 6:
            error_messages.append('Şifre en az 6 karakter olmalıdır!')
            is_valid = False
        
        selected_office_id = None
        if office_id_str:
            try:
                selected_office_id = int(office_id_str)
                if not Office.query.get(selected_office_id):
                    error_messages.append('Geçersiz ofis seçimi!')
                    is_valid = False
            except ValueError:
                error_messages.append('Geçersiz ofis ID formatı!')
                is_valid = False
        
        if not is_valid:
            for error_msg in error_messages:
                flash(error_msg, 'danger')
            form_data_to_repopulate = request.form.to_dict()
            return render_template('broker_form.html', form_title="Yeni Broker Oluştur", offices=offices, form_data=form_data_to_repopulate, user_data=None)

        try:
            new_broker = User(
                email=email, ad=ad, soyad=soyad, firma=firma, unvan=unvan,
                role='broker', office_id=selected_office_id, is_active=is_active_broker
            )
            new_broker.set_password(password)
            db.session.add(new_broker)
            db.session.commit()
            flash(f"Broker '{new_broker.ad} {new_broker.soyad}' başarıyla oluşturuldu.", "success")
            return redirect(url_for('admin.list_users')) # Kullanıcı listesine yönlendir
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Broker oluşturulurken hata: {str(e)}", exc_info=True)
            flash(f"Broker oluşturulurken bir hata oluştu: {str(e)}", "danger")
            form_data_to_repopulate = request.form.to_dict()
            return render_template('broker_form.html', form_title="Yeni Broker Oluştur", offices=offices, form_data=form_data_to_repopulate, user_data=None)
            
    return render_template('broker_form.html', form_title="Yeni Broker Oluştur", offices=offices, form_data={}, user_data=None)
@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_user(user_id):
    user_to_edit = User.query.get_or_404(user_id)
    offices = Office.query.order_by(Office.name).all()

    if request.method == 'POST':
        # Formdan verileri al
        user_to_edit.ad = request.form.get('ad', user_to_edit.ad).strip()
        user_to_edit.soyad = request.form.get('soyad', user_to_edit.soyad).strip()
        # E-posta genellikle değiştirilmez, ama isterseniz değiştirebilirsiniz (unique kontrolüyle)
        # new_email = request.form.get('email', user_to_edit.email).strip()
        user_to_edit.firma = request.form.get('firma', user_to_edit.firma).strip()
        user_to_edit.unvan = request.form.get('unvan', user_to_edit.unvan).strip()
        user_to_edit.role = request.form.get('role', user_to_edit.role)
        office_id_str = request.form.get('office_id')
        user_to_edit.is_active = 'is_active' in request.form
        
        new_password = request.form.get('password')
        is_valid = True
        error_messages = []

        if not all([user_to_edit.ad, user_to_edit.soyad, user_to_edit.role, office_id_str]):
            error_messages.append('Ad, soyad, rol ve ofis seçimi zorunludur!')
            is_valid = False
        
        if new_password and len(new_password) < 6:
            error_messages.append('Yeni şifre en az 6 karakter olmalıdır!')
            is_valid = False
        
        selected_office_id = None
        if office_id_str:
            try:
                selected_office_id = int(office_id_str)
                if not Office.query.get(selected_office_id):
                    error_messages.append('Geçersiz ofis seçimi!')
                    is_valid = False
                else:
                    user_to_edit.office_id = selected_office_id
            except ValueError:
                error_messages.append('Geçersiz ofis ID formatı!')
                is_valid = False
        else: # Eğer ofis seçimi boş gelirse (ve zorunluysa)
            error_messages.append('Ofis seçimi zorunludur!')
            is_valid = False
            
        if not is_valid:
            for error_msg in error_messages:
                flash(error_msg, 'danger')
            # Hata durumunda formu, mevcut verilerle tekrar render et
            return render_template('broker_form.html', form_title=f"Kullanıcı Düzenle: {user_to_edit.ad}", 
                                   offices=offices, user_data=user_to_edit, form_data=request.form.to_dict())
        try:
            if new_password:
                user_to_edit.set_password(new_password)
            
            db.session.commit()
            flash(f"Kullanıcı '{user_to_edit.ad} {user_to_edit.soyad}' başarıyla güncellendi.", "success")
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Kullanıcı güncellenirken hata (ID: {user_id}): {str(e)}", exc_info=True)
            flash(f"Kullanıcı güncellenirken bir hata oluştu: {str(e)}", "danger")
            return render_template('broker_form.html', form_title=f"Kullanıcı Düzenle: {user_to_edit.ad}", 
                                   offices=offices, user_data=user_to_edit, form_data=request.form.to_dict())

    # GET isteği için formu kullanıcı verileriyle doldur
    return render_template('broker_form.html', form_title=f"Kullanıcı Düzenle: {user_to_edit.ad} {user_to_edit.soyad}", 
                           offices=offices, user_data=user_to_edit, form_data=user_to_edit.__dict__)


@admin_bp.route('/user/<int:user_id>/toggle_active', methods=['POST'])
@login_required
@superadmin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id and user.role == 'superadmin': # Süper admin kendini pasif yapamasın
        flash("Süper admin kendi hesabını pasif yapamaz.", "warning")
        return redirect(url_for('admin.list_users'))
        
    try:
        user.is_active = not user.is_active
        db.session.commit()
        status_text = "aktif" if user.is_active else "pasif"
        flash(f"Kullanıcı '{user.ad} {user.soyad}' durumu {status_text} olarak güncellendi.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Kullanıcı aktif/pasif durumu değiştirilirken hata (ID: {user_id}): {str(e)}", exc_info=True)
        flash(f"Kullanıcı durumu güncellenirken bir hata oluştu: {str(e)}", "danger")
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id: # Süper admin kendini silemesin
        flash("Kendi hesabınızı silemezsiniz.", "danger")
        return redirect(url_for('admin.list_users'))
    
    # Opsiyonel: Bu kullanıcıya rapor veren diğer kullanıcıların reports_to_user_id'sini NULL yap
    User.query.filter_by(reports_to_user_id=user_id).update({'reports_to_user_id': None})
    
    # Opsiyonel: Bu kullanıcının ofis sahibi olduğu ofislerin owner_id'sini NULL yap (eğer Office modelinde owner ilişkisi varsa)
    # Office.query.filter_by(owner_id=user_id).update({'owner_id': None})
    
    # Opsiyonel: Bu kullanıcının oluşturduğu analiz, crm kaydı vb. ne olacak?
    # Bunlar ya silinecek (cascade ile) ya da başka bir kullanıcıya atanacak ya da sahipsiz kalacak.
    # Modeldeki ondelete ayarlarına bağlı.

    try:
        username = f"{user_to_delete.ad} {user_to_delete.soyad}"
        User.query.filter_by(reports_to_user_id=user_id).update({'reports_to_user_id': None})

        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"Kullanıcı '{username}' başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Kullanıcı silinirken hata (ID: {user_id}): {str(e)}", exc_info=True)
        flash(f"Kullanıcı silinirken bir hata oluştu: {str(e)}", "danger")
    return redirect(url_for('admin.list_users'))

# --- KULLANICI YÖNETİMİ (Genel) ---
@admin_bp.route('/users')
@login_required
@superadmin_required
def list_users():
    # Rol ve ofise göre filtreleme eklenebilir
    page = request.args.get('page', 1, type=int)
    per_page = 15
    role_filter = request.args.get('role', None)
    office_filter = request.args.get('office_id', None, type=int)

    query = User.query
    if role_filter:
        query = query.filter(User.role == role_filter)
    if office_filter:
        query = query.filter(User.office_id == office_filter)
    
    users = query.order_by(User.registered_on.desc()).paginate(page=page, per_page=per_page, error_out=False)
    offices = Office.query.order_by(Office.name).all() # Filtreleme için
    roles = ['superadmin', 'broker', 'danisman', 'calisan'] # Filtreleme için

    return render_template('list_users.html', users_pagination=users, offices=offices, roles=roles, 
                           current_role_filter=role_filter, current_office_filter=office_filter)

# allowed_file fonksiyonunu buraya da ekleyelim veya global bir utils.py'den import edelim
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS