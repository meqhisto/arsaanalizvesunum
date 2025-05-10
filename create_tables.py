from flask import Flask
from models.db import db
import os

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mssql+pyodbc://altan:Yxrkt2bb7q8.@46.221.49.106/arsa_db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "future": True,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": 5,
    }
    return app

def create_tables():
    app = create_app()
    db.init_app(app)
    
    with app.app_context():
        # Import all models that need tables
        from models.customer import Customer
        from models.portfolio import Portfolio, PortfolioGroup, PortfolioTag, PortfolioPerformance
        
        print("Creating all database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    create_tables()
