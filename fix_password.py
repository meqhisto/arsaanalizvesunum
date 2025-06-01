# fix_password.py
from app import create_app
from models import db
from models.user_models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(email="altanbariscomert@gmail.com").first()
    if user:
        # Yeni güçlü bir şifre atayın:
        user.set_password("123456")
        db.session.commit()
        print("Şifre başarıyla güncellendi.")
    else:
        print("Kullanıcı bulunamadı.")