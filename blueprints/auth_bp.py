# blueprints/auth_bp.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, current_user # current_user'a burada genellikle ihtiyaç olmaz
from werkzeug.security import generate_password_hash, check_password_hash # Parola hashleme
from datetime import datetime, timedelta # Parola sıfırlama süresi için
import secrets # Parola sıfırlama token'ı için

# Modelleri ve db nesnesini models paketinden import et
from models.user_models import User
from models import db # SQLAlchemy db nesnesi

# Blueprint'i oluşturuyoruz.
# 'auth' blueprint'in adı (url_for içinde kullanılacak)
# __name__ modülün adını belirtir
# template_folder: Bu blueprint'e özel şablonlar varsa (örn: templates/auth/login.html)
# Eğer tüm şablonlar ana 'templates' klasöründeyse, template_folder belirtmeyebilir
# veya '../templates' olarak ayarlayıp render_template içinde 'auth/login.html' kullanabilirsiniz.
# Şimdilik, şablonların templates/auth/ altında olduğunu varsayalım.
auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth', static_folder='../static')
# Eğer static dosyalarınız (CSS, JS) ana static klasöründeyse, static_folder belirtmenize gerek yok.

# blueprints/auth_bp.py
# ... (importlar) ...

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'superadmin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'broker':
            return redirect(url_for('main.my_office')) # Broker'ın ofis yönetim/dashboard sayfası
        else: # danisman, calisan
            return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        user = User.query.filter_by(email=email).first()

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            user.failed_attempts = 0
            user.son_giris = datetime.utcnow()
            db.session.commit()
            flash('Başarıyla giriş yaptınız!', 'success')

            if user.role == 'superadmin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'broker':
                return redirect(url_for('main.my_office'))
            
            next_page = request.args.get('next')
            if next_page:
                # Güvenlik: next_page admin veya broker sayfasına gitmeye çalışıyorsa ve kullanıcı yetkili değilse engelle
                if (('/admin' in next_page or next_page.startswith('admin.')) and user.role != 'superadmin') or \
                   (('/my_office' in next_page or next_page.startswith('main.my_office')) and user.role != 'broker'):
                    flash('Bu sayfaya erişim yetkiniz yok.', 'warning')
                    return redirect(url_for('main.index'))
            return redirect(next_page or url_for('main.index'))
        else:
            # ... (hatalı giriş ve failed_attempts mantığı) ...
            flash('Geçersiz e-posta veya şifre ya da hesap aktif değil.', 'danger')
            if user:
                 user.failed_attempts = (user.failed_attempts or 0) + 1
                 db.session.commit()

    return render_template('login.html') # veya templates/auth/login.html
# @auth_bp.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('main.index'))

#     if request.method == 'POST':
#         try:
#             email = request.form.get('email')
#             password = request.form.get('password')
#             password_confirm = request.form.get('password_confirm')
#             ad = request.form.get('ad')
#             soyad = request.form.get('soyad')
#             # Diğer kayıt form alanları (telefon, firma, unvan, adres)
#             telefon = request.form.get('telefon')
#             firma = request.form.get('firma')
#             unvan = request.form.get('unvan')
#             adres = request.form.get('adres')

#             if password != password_confirm:
#                 flash('Şifreler eşleşmiyor!', 'danger')
#                 return redirect(url_for('auth.register'))

#             if len(password) < 6:
#                 flash('Şifre en az 6 karakter olmalıdır!', 'danger')
#                 return redirect(url_for('auth.register'))

#             if User.query.filter_by(email=email).first():
#                 flash('Bu e-posta adresi zaten kayıtlı!', 'danger')
#                 return redirect(url_for('auth.register'))

#             new_user = User(
#                 email=email,
#                 ad=ad,
#                 soyad=soyad,
#                 telefon=telefon,
#                 firma=firma,
#                 unvan=unvan,
#                 adres=adres,
#                 is_active=True # Yeni kullanıcılar varsayılan olarak aktif olsun
#             )
#             new_user.set_password(password)

#             db.session.add(new_user)
#             db.session.commit()

#             flash('Kayıt başarılı! Lütfen giriş yapın.', 'success')
#             return redirect(url_for('auth.login'))

#         except Exception as e:
#             db.session.rollback()
#             import logging
#             logging.getLogger(__name__).error(f"Registration error: {str(e)}", exc_info=True)
#             flash(f'Kayıt sırasında bir hata oluştu: {str(e)}', 'danger')
#             return redirect(url_for('auth.register'))

#     return render_template('register.html') # templates/auth/register.html

@auth_bp.route('/logout')
def logout():
    logout_user()
    # session.pop('user_id', None) # Flask-Login'den sonra gereksiz
    # session.pop('email', None)   # Flask-Login'den sonra gereksiz
    flash('Başarıyla çıkış yaptınız!', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            # E-posta gönderme işlemi burada olmalı.
            # Örnek: send_password_reset_email(user, token)
            # Şimdilik sadece loglayalım:
            import logging
            logging.getLogger(__name__).info(f"Password reset token for {email}: {token}. Reset URL: {url_for('auth.reset_password', token=token, _external=True)}")

            flash('Şifre sıfırlama bağlantısı e-posta adresinize gönderildi (Eğer e-posta gönderme ayarlıysa).', 'info')
        else:
            flash('Bu e-posta adresi ile kayıtlı bir hesap bulunamadı.', 'danger')

        return redirect(url_for('auth.login')) # Her durumda login'e yönlendir

    return render_template('forgot_password.html') # templates/auth/forgot_password.html

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expires < datetime.utcnow():
        flash('Geçersiz veya süresi dolmuş şifre sıfırlama bağlantısı.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır!', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        flash('Şifreniz başarıyla güncellendi. Lütfen yeni şifrenizle giriş yapın.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token) # templates/auth/reset_password.html