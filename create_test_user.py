#!/usr/bin/env python3
"""
Test kullanıcısı oluşturma scripti
"""

from app import create_app
from models import db
from models.user_models import User
from models.office_models import Office
from datetime import datetime

def create_test_user():
    app = create_app()
    with app.app_context():
        try:
            # Önce mevcut kullanıcıları kontrol edelim
            existing_user = User.query.filter_by(email='test@example.com').first()
            if existing_user:
                print("Test kullanıcısı zaten mevcut!")
                print(f"Email: {existing_user.email}")
                print(f"Ad: {existing_user.ad} {existing_user.soyad}")
                print(f"Role: {existing_user.role}")
                return
            
            # Test ofisi oluştur
            test_office = Office.query.filter_by(name='Test Ofis').first()
            if not test_office:
                test_office = Office(
                    name='Test Ofis',
                    address='Test Adres',
                    phone='0555 123 4567',
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(test_office)
                db.session.flush()  # ID'yi almak için
                print("✓ Test ofisi oluşturuldu")
            
            # Test kullanıcısı oluştur
            test_user = User(
                email='test@example.com',
                ad='Test',
                soyad='Kullanıcı',
                telefon='0555 123 4567',
                firma='Test Ofis',
                unvan='Test Uzmanı',
                role='broker',
                office_id=test_office.id,
                timezone='Europe/Istanbul'
            )
            test_user.set_password('123456')
            
            db.session.add(test_user)
            db.session.commit()
            
            print("✅ Test kullanıcısı başarıyla oluşturuldu!")
            print(f"Email: test@example.com")
            print(f"Şifre: 123456")
            print(f"Role: broker")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Hata oluştu: {e}")
            raise

if __name__ == "__main__":
    create_test_user()