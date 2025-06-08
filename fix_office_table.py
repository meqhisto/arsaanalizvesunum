#!/usr/bin/env python3
"""
Office tablosuna eksik updated_at kolonunu ekleme scripti
"""

from app import create_app
from models import db
from sqlalchemy import text

def fix_office_table():
    app = create_app()
    with app.app_context():
        try:
            print("Office tablosuna updated_at kolonu ekleniyor...")
            
            # updated_at kolonunu ekle
            try:
                db.session.execute(text("ALTER TABLE offices ADD updated_at DATETIME DEFAULT GETDATE()"))
                print("✓ updated_at kolonu eklendi")
            except Exception as e:
                print(f"updated_at kolonu eklenirken hata (muhtemelen zaten var): {e}")
            
            db.session.commit()
            print("✅ Office tablosu başarıyla güncellendi!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Hata oluştu: {e}")
            raise

if __name__ == "__main__":
    fix_office_table()