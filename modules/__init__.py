from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()  # SQLAlchemy nesnesini burada tanımla

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sizin_gizli_anahtariniz') # SECRET_KEY ekle
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mssql+pyodbc:///?odbc_connect=DRIVER={SQL Server};SERVER=46.221.49.106;DATABASE=arsa_db;UID=altan;PWD=Yxrkt2bb7q8.;')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  # SQLAlchemy nesnesini uygulamaya bağla

    with app.app_context():
        db.create_all()

    return app

def create_app():
    app = Flask(__name__)
    # ...config settings...
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Tabloları oluştur
        
    return app