from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # ...config settings...
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Tabloları oluştur
        
    return app