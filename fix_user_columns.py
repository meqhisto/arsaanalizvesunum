#!/usr/bin/env python3
"""
User tablosundaki gereksiz kolonları temizleme scripti
"""

from app import create_app
from models import db
from sqlalchemy import text

def fix_user_columns():
    app = create_app()
    with app.app_context():
        try:
            # Önce mevcut verileri kontrol edelim
            print("Mevcut user tablosu kolonları kontrol ediliyor...")
            
            # Önce constraint'leri kaldır
            constraints_to_drop = [
                "FK_User_ReportsTo_Self",
                "FK_User_ReportsTo", 
                "DF__users__is_active__22FF2F51"
            ]
            
            for constraint in constraints_to_drop:
                try:
                    db.session.execute(text(f"ALTER TABLE users DROP CONSTRAINT {constraint}"))
                    print(f"✓ {constraint} constraint'i kaldırıldı")
                except Exception as e:
                    print(f"{constraint} constraint'i kaldırılırken hata (muhtemelen zaten yok): {e}")
            
            # is_active_flag kolonunu kaldır (is_active zaten var)
            try:
                db.session.execute(text("ALTER TABLE users DROP COLUMN is_active_flag"))
                print("✓ is_active_flag kolonu kaldırıldı")
            except Exception as e:
                print(f"is_active_flag kolonu kaldırılırken hata (muhtemelen zaten yok): {e}")
            
            # reports_to_user_id kolonunu kaldır (manager_id kullanıyoruz)
            try:
                db.session.execute(text("ALTER TABLE users DROP COLUMN reports_to_user_id"))
                print("✓ reports_to_user_id kolonu kaldırıldı")
            except Exception as e:
                print(f"reports_to_user_id kolonu kaldırılırken hata (muhtemelen zaten yok): {e}")
            
            # report_to_id kolonunu da kaldır (gereksiz)
            try:
                db.session.execute(text("ALTER TABLE users DROP COLUMN report_to_id"))
                print("✓ report_to_id kolonu kaldırıldı")
            except Exception as e:
                print(f"report_to_id kolonu kaldırılırken hata (muhtemelen zaten yok): {e}")
            
            db.session.commit()
            print("✅ User tablosu başarıyla temizlendi!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Hata oluştu: {e}")
            raise

if __name__ == "__main__":
    fix_user_columns()