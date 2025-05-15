# app.py
from flask import Flask, render_template # render_template error.html için
from flask_login import LoginManager, current_user # current_user Jinja'ya eklenebilir
from concurrent_log_handler import ConcurrentRotatingFileHandler
import logging
import os
from datetime import timedelta, datetime as dt_module # dt_module Jinja için
from flask_migrate import Migrate
from models import db as application_db # db'yi modellerden al
# Modelleri ve db nesnesini models paketinden import et
from models import init_db_models # init_app fonksiyonunu yeniden adlandırdık
from models.user_models import User # load_user için User modeline ihtiyaç var
from blueprints.admin_bp import admin_bp # admin_bp'yi import et

# Blueprint'leri import et
from blueprints.auth_bp import auth_bp
from blueprints.main_bp import main_bp
from blueprints.analysis_bp import analysis_bp
from blueprints.crm_bp import crm_bp
from blueprints.portfolio_bp import portfolio_bp # Import et


# Jinja filtreleri ve global'leri için
from markupsafe import Markup, escape

def nl2br_filter(value):
    if value is None: return ''
    escaped_value = escape(value)
    return Markup(escaped_value.replace('\n', '<br>\n'))

# Flask uygulamasını application olarak ayarlayın (bazı hosting platformları için)
application = None
migrate = Migrate() # Migrate nesnesini globalde (veya app factory dışında) oluştur


def create_app(config_name=None): # config_name opsiyonel, farklı config'ler için
    global application
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.template_folder = "templates"
    app.static_folder = "static" # Static dosyalar için
    app.static_url_path = "/static" # Static dosyaların URL yolu
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio') # Kaydet
    application = app # Elastic Beanstalk vb. için
    app.register_blueprint(admin_bp) # Eğer admin_bp.py içinde url_prefix='/admin' tanımlıysa

    # --- CONFIGURATION ---
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        os.environ.get("DATABASE_URL", "mssql+pyodbc://altan:Yxrkt2bb7q8.@46.221.49.106/arsa_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # SECRET_KEY'i daha güvenli bir yerden alın veya çok güçlü bir varsayılan kullanın
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "COK_GUCLU_VE_TAHMIN_EDILEMEZ_BIR_ANAHTAR_OLMALI_BURASI_dev_icin_degil!")
    
    # Medya yükleme ayarları
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    
    PRESENTATIONS_DIR = os.path.join(BASE_DIR, "static", "presentations")
    if not os.path.exists(PRESENTATIONS_DIR):
        os.makedirs(PRESENTATIONS_DIR)
    app.config["PRESENTATIONS_DIR"] = PRESENTATIONS_DIR # DocumentGenerator kullanabilsin diye

    # --- DATABASE INITIALIZATION ---
    init_db_models(app) # Modellerin bulunduğu paketteki init_app fonksiyonunu çağır
    migrate.init_app(app, application_db) # <-- BU SATIR ÇOK ÖNEMLİ

    # --- LOGIN MANAGER ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Blueprint adını kullan: auth.login
    login_manager.login_message = 'Lütfen önce giriş yapın'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        # User modelinin doğru import edildiğinden emin olun
        return User.query.get(int(user_id))

    # --- JINJA ENV SETUP ---
    app.template_folder = "templates" # Ana şablon klasörü
    app.jinja_env.globals.update(datetime=dt_module)
    app.jinja_env.globals.update(zip=zip)
    app.jinja_env.filters['nl2br'] = nl2br_filter
    # current_user'ı tüm şablonlara global olarak eklemek için (Flask-Login bunu zaten yapar ama explicit olabilir)
    @app.context_processor
    def inject_current_user():
        return dict(current_user=current_user, get_current_user=lambda: current_user)


    # --- LOGGING ---
    # Log dosyasının yolu, app.py'nin bulunduğu dizinde olacak şekilde ayarlandı.
    log_file_path = os.path.join(BASE_DIR, "app.log")
    handler = ConcurrentRotatingFileHandler(log_file_path, maxBytes=100000, backupCount=5, encoding='utf-8')
    handler.setLevel(logging.INFO)
    # Daha detaylı format: %(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    handler.setFormatter(formatter)
    
    if not app.logger.handlers: # Handler'ların tekrar tekrar eklenmesini önle
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO) # Flask'ın kendi logger'ının seviyesini de ayarla

    # --- ERROR HANDLER ---
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Hatanın tam traceback'ini logla
        import traceback
        tb_str = traceback.format_exc()
        app.logger.error(f"Sunucu hatası oluştu: {str(e)}\nTraceback:\n{tb_str}")
        # Kullanıcıya genel bir hata mesajı göster
        # Üretimde daha kullanıcı dostu bir hata sayfası göstermek daha iyi olur.
        # return render_template("error.html", error_message=str(e)), 500
        return f"Bir sunucu hatası oluştu: {str(e)}. Detaylar loglandı.", 500


    # --- BLUEPRINT REGISTRATION ---
    # Prefix'ler olmadan (root'a kayıt) veya prefix'lerle kaydedebilirsiniz.
    # Genellikle auth için /auth, crm için /crm gibi prefix'ler kullanılır.
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) # Prefix yok, kök URL'ler burada olacak (örn: /index)
    app.register_blueprint(analysis_bp, url_prefix='/analysis') # url_for('analysis.analizler')
    app.register_blueprint(crm_bp, url_prefix='/crm') # url_for('crm.crm_contacts_list')
    # portfolio_bp için de benzer bir kayıt yapabilirsiniz.

    # --- SESSION CONFIGURATION ---
    # app.permanent_session_lifetime = timedelta(days=30) # "Beni Hatırla" için
    # Flask-Login'in remember_me özelliği bunu zaten yönetir.
    # Eğer session.permanent = True yapıyorsanız, bu ayar kullanılır.

    app.logger.info("Flask uygulaması başarıyla oluşturuldu ve yapılandırıldı.")
    return app

# Bu kısım, doğrudan `python app.py` ile çalıştırıldığında uygulamayı başlatır.
# Üretimde bir WSGI sunucusu (Gunicorn, uWSGI) kullanılacaksa bu __main__ bloğu çalışmaz.
if __name__ == "__main__":
    app = create_app()
    # Veritabanı tabloları create_app içindeki init_db_models çağrısıyla oluşturuluyor.
    # init_db() fonksiyonunu eski app.py'den buraya taşımanıza gerek yok.
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e_run:
        # app.logger burada henüz tam aktif olmayabilir, print kullanalım
        print(f"Uygulama başlatılırken kritik bir hata oluştu: {str(e_run)}")
        import traceback
        traceback.print_exc()